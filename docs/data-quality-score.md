# Data Quality Score (DQS)

The DQS (0–100) is the single number that governs how sophisticated generated journeys may be. It is computed by `lifecycle-connect` and consumed by `lifecycle-journeys` for depth assignment. It is always reported as a component breakdown, never as a bare total.

## Components

| Component | Max | Scoring rubric |
|---|---|---:|
| **Event diversity** | 25 | Distinct *behaviorally meaningful* events (noise excluded: page_view, scroll, session_start counts as recency only). 0–2 events: 0–5 · 3–5: 6–12 · 6–10: 13–19 · 11+ across ≥ 4 stages: 20–25 |
| **Conversion events** | 25 | No true revenue event: 0 · 1 revenue event, missing params: 8–12 · 1 revenue event with `value`/`currency`/`items`: 13–18 · multiple conversion types (e.g. purchase + subscription) with params: 19–25 |
| **Funnel completeness** | 20 | Measured against the industry playbook's canonical funnel. Score = (tracked consecutive steps / total steps) × 20, rounded. Gaps in the middle hurt more than missing edges — a broken chain caps this at 12 |
| **User attributes / segments** | 15 | Anonymous only: 0 · identifiable users (user_id): 5–7 · + attributes usable for segmentation (plan, category affinity, consent state): 8–12 · + RFM-computable history: 13–15. **T2-aggregate inputs (pre-aggregated reports, no row-level data) cap at 0 here regardless of how rich the aggregate tables are** — there is no per-user identity to score. |
| **Volume sufficiency** | 15 | Monthly conversions: 0 (no data/T3) · < 100: 3–5 · 100–1k: 6–10 · ≥ 1k: 11–15. Volume gates *branch statistics*, not journey existence |

## Depth classes (what the score buys)

| DQS | Depth class | Journey shape |
|---|---|---|
| ≥ 70 | **branched** | 7–12 steps possible, behavioral branches (opened/clicked/converted), multi-channel orchestration, value-based gates |
| 40–69 | **standard** | 4–7 steps, one open/click branch, two channels |
| < 40 | **simple** | 3–5 steps, time-based waits, single channel + one support channel, playbook defaults |

Six hard rules regardless of score:

1. A journey may not claim a revenue KPI unless a true revenue event exists as its success exit (revenue-intent events don't qualify).
2. Informational patterns (back-in-stock, price-drop, anniversary) do not scale with DQS — they stay short by design.
3. **Activation flag — design sufficiency ≠ activation sufficiency.** The DQS is one number, and a score built on rich events + funnel + volume can clear the branched bar while the user-attributes component is **0** (the T2-aggregate hard cap). Such a portfolio can be *designed* but not *run*: with zero per-user identity, not one message can be sent to one person. Whenever user attributes score 0, the DQS carries `activation: blocked (no per-user identity)` alongside the number, and the portfolio header must state it. The score is not adjusted — the flag is a separate bit, so the design-quality signal stays honest in both directions.
4. **Volume is a gate on depth, not just an additive component.** The DQS is additive, so rich events + a complete funnel can clear the branched bar while monthly conversions are far too few to ever measure a branch (measurement.md's ~200-control-conversion rule). When the Volume component scores **≤ 5** (under ~100 conversions/month), the depth class is **capped at standard** regardless of the total — a 10-step branched journey on an unmeasurable audience is a designed failure. And in every case, the depth class is a **ceiling, not a quota**: the engine may always build shallower than the class allows when the pattern or audience calls for it.
5. **Freshness is a gate on depth, not just a footnote — and the threshold is sector-relative, not a fixed number.** The DQS is computed from up to 12 months of history, so rich event diversity, a complete funnel, and healthy volume can all score well while the tracked behavior itself is stale — the score describes what the data used to look like, not what it looks like now. A single universal cutoff doesn't work: a mobile app's real churn signal fires within a week, a leisure-travel company's customers may naturally return only once or twice a year. The freshness threshold is therefore the active industry playbook's own `churn_signal` window (`knowledge/industries/<sector>.md`) — 7 days for mobile-app, 45 for e-commerce, and so on; where a playbook's `churn_signal` is itself relative (a trailing-baseline percentage, or "compute from data" as travel.md states outright), the freshness check follows that same relative logic rather than forcing a fixed day count. **Fallback: 60 days** when no industry is set (T3) or `churn_signal` can't be parsed. When the most recent event in the pulled window is older than the threshold, the depth class is **capped at standard** regardless of the total. As with volume, this is a ceiling on the ceiling: fix the tracking gap and re-run `/lifecycle connect` to lift it, rather than trusting a score built on stale signal.
6. **Consistency is a gate on depth, not just a footnote — same sector-relative threshold as freshness.** A component score is only as trustworthy as the tracking that produced it: if the primary conversion event fired reliably for months, went silent for a stretch inside the pulled window (a broken pixel, a shipped bug, a removed tag), then resumed, the funnel and conversion components still score off the healthy months and hide the gap. The gap threshold is **one-third of the freshness threshold** from rule 5 (roughly 15 days for e-commerce, 2 for mobile-app) — **fallback: 14 days** under the same conditions as rule 5's fallback. When the primary conversion event shows a continuous silent gap past this threshold inside an otherwise-active window, the depth class is **capped at standard** regardless of the total, and the gap dates are reported alongside the DQS breakdown. This does not apply to normal seasonality — a slow stretch consistent with the sector's own rhythm is not a gap — only to an event that stops firing entirely and later resumes.

## Data Reliability Gate

The five components above answer "how much lifecycle capability does this data support?" — event diversity, conversion depth, funnel shape, identity richness, volume. They do **not** answer a different question: "can this specific pull be trusted?" A property can score well on all five while the underlying tracking is quietly broken — 30% duplicate `purchase` firing, a `value` param in the wrong currency, `user_id` populated for 27% of events, consent state stale by months. None of that moves the DQS number, because none of it is what the DQS measures.

The Reliability Gate is a **separate tag, not a sixth component** — it never changes the score, the same way the activation/freshness/consistency flags (hard rules 3, 5, 6 above) don't. It is reported alongside the score: `DQS 78 · activation ready · reliability: degraded`.

| Signal | What it checks | Triggers `degraded` when |
|---|---|---|
| Duplicate firing | Same event/identity/timestamp (or near-timestamp) appearing more than once | A meaningful share of a component's underlying events are duplicates — inflates event diversity, conversion counts, and volume simultaneously |
| Parameter completeness | Required params on conversion/key events are actually populated, not just present in the schema | A conversion event's core params (`value`, `currency`, `item_id`) are null/missing on a material share of firings — the same check `lifecycle-journeys` step 1 applies at eligibility time ("presence means usable, not just named"); this gate surfaces it earlier, at connect time |
| **Identity coverage ratio** | Not just whether `user_id` exists in the schema, but what share of active users/events actually carry it | `user_id` is populated on a low share of events/users — person-level segmentation and exclusions leak for the uncovered share even though the User Attributes component scores as if identity were solid |
| Timestamp integrity | Event timestamps are plausible and monotonic per identity where order matters | Clock skew, future-dated events, or out-of-order sequences that would break `LAG()`/window-based audience logic (`audience-sql.md`'s behavioral-sequence patterns) |
| Consent-state freshness | The consent/İYS property used for downstream filtering is itself being updated, not stale | Consent state hasn't changed for a population where real opt-outs are known to occur — a stale consent field can silently under- or over-suppress |
| Anomalous event ratios | A sudden shift in the ratio between related events (e.g. `add_to_cart` : `purchase`) inside the pulled window | A ratio moves far outside its own recent baseline — usually a firing bug (a tag added/removed, a step skipped) rather than real behavior change |

Any triggered signal sets `reliability: degraded`; more than one, or one severe enough to compromise a hard-gated component (identity coverage feeding the activation flag, timestamp integrity feeding a branch condition), sets `reliability: unreliable` and the affected component(s) are named. No trigger → `reliability: healthy`, stated explicitly (same "a clean report is a claim, not a default" logic as the other tags). This is a report-time check on the pulled sample, not a new data pull — it requires no instrumentation the source doesn't already provide.

## Worked example

E-commerce store, GA4 connected: 9 meaningful events across 4 stages (**18**), `purchase` with full params but no second conversion type (**16**), funnel tracked view_item → purchase except `add_payment_info` (6/7 consecutive → **17**), user_id + consent state but no RFM history (**9**), ~800 conversions/month (**9**). **DQS = 69 → standard** (one point short of branched — the report should say exactly that, and what would tip it).

## Re-scoring

DQS is recomputed whenever the user implements tracking-plan items and re-runs `/lifecycle connect`. The tracking plan template requires a "projected DQS if implemented" figure so the user can see what the work buys.

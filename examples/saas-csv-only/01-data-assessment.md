# Data Assessment Report — Kanbanly

*Output of `/lifecycle connect` on a Mixpanel CSV export · synthetic showcase data*

## 1. Source & tier

| Field | Value |
|---|---|
| Source | `kanbanly-mixpanel-export.csv` (Mixpanel, monthly event counts) — kept in local `output/`, not committed |
| Tier | **T2** (static export, no live connection) |
| Date range | Jan–Jun 2026 (6 monthly columns; figures below are monthly averages) |
| Industry playbook | [saas](../../knowledge/industries/saas.md) |
| Identity | `user_id` + email columns present; no other user attributes in the export |

## 2. DQS breakdown

Scored per [docs/data-quality-score.md](../../docs/data-quality-score.md), against the SaaS playbook's event expectations. Uncertain components scored conservatively and flagged.

| Component | Score | Max | Reasoning |
|---|---:|---:|---|
| Event diversity | 15 | 25 | 7 meaningful events (6–10 band: 13–19) across 4 stages (activation, engagement, revenue, payment-protection). Mid-band: clean naming, but no engagement depth beyond `login`/`project_created`. |
| Conversion events | 10 | 25 | `subscription_start` exists but the CSV carries **counts only — no `plan`/`value`/`currency` params visible** → "1 revenue event, missing params" band (8–12). |
| Funnel completeness | 16 | 20 | SaaS canonical funnel has 5 steps; tracked: `sign_up` → `trial_start` → `feature_used` (via the `project_created` alias — assumption, user-confirmed) → `subscription_start` = 4/5 consecutive. Missing edge is `session_start` (edge gaps hurt less than middle gaps). 4/5 × 20 = 16. |
| User attributes / segments | 7 | 15 | Identifiable users (`user_id` + email) — top of the 5–7 band. No plan, seat count, consent state, or usage attributes in the export. |
| Volume sufficiency | 4 | 15 | 96 conversions/month (`subscription_start`) — just under 100, so the < 100 band (3–5). Enough for journey KPIs against a holdout, not for per-branch statistics. |
| **Total** | **52** | **100** | |

**Depth class: standard (40–69).** 4–7 steps, one open/click branch, two channels. What would tip the class to branched: params on `subscription_start` (+~6), a `feature` param on `feature_used` (+diversity and branch unlocks), and any segmentation attributes (+~5) — see the tracking summary in [02-portfolio.md](02-portfolio.md).

## 3. Event inventory (monthly averages, Jan–Jun 2026)

| Event | Monthly count | Conversion? | Mapped stage |
|---|---:|:---:|---|
| `sign_up` | 1,450 | — | *(filled by lifecycle-map)* |
| `trial_start` | 1,380 | — | |
| `login` | 38,400 | — | |
| `project_created` | 3,900 | — (aliased to `feature_used` — user-confirmed core action) | |
| `subscription_start` | 96 | ✓ (revenue; params not in export) | |
| `payment_succeeded` | 1,210 | — (includes renewals) | |
| `payment_failed` | 41 | — | |

## 4. Gaps

Against the playbook's must-haves (`sign_up`, `trial_start`, `feature_used`, `subscription_start`, `payment_failed`): **all present** (one via alias). Remaining gaps:

- **No `feature` param on `project_created`/`feature_used`** — blocks feature-adoption entirely and blocks the per-feature activation branches of trial-conversion.
- **No `failure_reason` on `payment_failed`** — dunning journey runs, but cannot tailor the message to the decline cause (data gap, not a blocker).
- **No `session_start` / activity events beyond `login`** — blocks upsell-cross-sell (health gate needs activity) and weakens churn detection to login frequency only.
- **No plan / seat / billing attributes** — blocks meaningful expansion segmentation; admins and members cannot be distinguished.
- **No funnel percentages or user-level rows** — volumes are journey estimates only; all conversion baselines must be measured after launch.

## 5. Next step

Proceed to `lifecycle-map` to confirm the `project_created` → `feature_used` alias and stage mapping, then `lifecycle-journeys`.

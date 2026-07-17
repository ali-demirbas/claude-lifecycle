---
name: lifecycle-results
description: Close the measurement loop. Ingest journey performance data from the CRM (holdout/lift results, opens, conversions), evaluate it against the incrementality doctrine, and recommend keep/promote/demote/kill per journey — plus maintain the failed-strategies log that stops the engine from re-proposing what didn't work. Use when the user says "sonuçları gir", "results", "performans verisi", "holdout sonuçları", "test sonuçları geldi", "journey performansı".
---

# Lifecycle Results — Closing the Loop

The engine generates journeys and KPIs; this skill reads what actually happened and feeds it back. It **recommends** — promotion, demotion, and deletion are always the user's call. Doctrine: `${CLAUDE_PLUGIN_ROOT}/knowledge/measurement.md` — every rule there binds this skill.

## Step 1 — Ingest

Accept results in any form the user has: CSV export, pasted table, or plain description. Per journey, collect what exists:
- entered / exposed / control counts, conversions per group, window covered
- per-step diagnostics (opens, clicks, unsubscribes) if available
- which copy variant ran (A/B) and its `strategy`/`hypothesis` labels from the copy output

Missing fields are recorded as missing — never interpolated.

## Step 2 — Validate before judging (the gate)

Apply measurement.md's honesty rules **before** any verdict:
1. **Sample size:** control group below ~200 conversions → verdict is capped at "insufficient data — extend window / reduce holdout / keep running", regardless of how bad the lift looks. Zero lift on an underpowered test means *unmeasured*, not *failed*.
2. **Window:** results read before the journey family's measurement window closed (recovery 1–7d, activation 7–14d, winback 30–90d) are provisional.
3. **Contamination check:** ask whether holdout users could have been reached by an overlapping journey (portfolio conflict review names the overlaps).
4. **External factors:** price changes, PR spikes, seasonal peak (playbook Seasonality section) — flag if the window overlaps one; attributed numbers inflate on elevated baselines.

## Step 3 — Verdict per journey

For journeys that pass the gate, compute lift and iROI per measurement.md and recommend exactly one of:

| Verdict | When | Consequence proposed |
|---|---|---|
| **keep** | positive lift, iROI ≥ 0 | none; next review date |
| **promote** | strong lift + blocked depth upgrades exist | raise priority / build the branched version |
| **demote** | measured (powered) zero-to-weak lift on a P0/P1 | drop one priority level in the *brand's* portfolio (playbook defaults stay untouched — they are sector knowledge, not this account's results) |
| **kill** | powered negative lift or guardrail breach (unsubscribe/complaint ceiling) | pause now, redesign or retire |
| **fix-copy** | journey lift fine, but one variant/step clearly underperforms its sibling | rewrite that step via `lifecycle-copy`, log the losing strategy |

Guardrail breaches (unsubscribe/complaint over ceiling) override everything — recommend pause even on positive lift.

**Before a demote/kill verdict on borderline or zero overall lift:** check whether lift holds in any major segment the data supports (RFM tier, acquisition channel, platform, **and trigger context — the journey's first-instance vs repeat-instance entrants behave differently**, and pooling them can hide a real win in one). A real win in one segment can cancel against a loss in another and read as "no difference" in aggregate. Segment-level groups are smaller than the overall test by definition, so the sample-size gate (Step 2, rule 1) applies per segment too — a segment split that's itself underpowered is a lead worth naming for a future test, not grounds to override an already-clear overall kill.

## Step 4 — Write the memory

Three files under `output/<brand>/` (gitignored; linked from the brand config):

1. **`results-log.md`** — append one row per verdict: date, journey id, window, exposed/control, lift, iROI, verdict, decision taken by user.
2. **`failed-strategies.md`** — append an entry for (a) **powered failures** (sample-size gate passed, lift negative/zero) or (b) **guardrail-class absolute signals** (complaint, suppression trigger, unsubscribe spike) which are exempt from the sample gate but must be labeled `guardrail-class` with the n stated honestly. Format: `segment | journey/pattern | strategy label (from copy metadata) | what failed | evidence class | status`. This is a **do-not-repropose list**: `lifecycle-journeys` and `copy-writer` must check it and not offer the same strategy to the same segment again. Entries carry evidence so a human can overrule; the log recommends, it doesn't legislate.
3. **`winning-strategies.md`** — the positive counterpart: append an entry when a hypothesis is **confirmed** (a `keep`/`promote` verdict where the copy metadata's hypothesis held, or a `fix-copy` verdict's surviving sibling variant clearly won). Same format as failed-strategies: `segment | journey/pattern | strategy label (from copy metadata) | what worked | evidence class | status`. This is a **prefer-this-precedent list**, not a do-only-this list — `copy-writer` treats a matching entry as a starting-point hint for one variant, never as a reason to stop testing genuinely different angles for the other.

## Step 5 — Feed forward

- Tell the user which blocked journeys/depth upgrades the results now justify prioritizing (tracking plan cross-reference).
- If a hypothesis from the copy metadata was confirmed/refuted, say so explicitly — that is the entire point of labeling variants with hypotheses.

## Never do

- Never auto-demote or auto-delete — recommend with evidence, the user decides.
- Never judge an underpowered test (gate rule 1) or edit sector playbooks/lexicons based on one account's results.
- Never prescribe a fix without naming the layer the diagnostics indict: strong clicks + weak conversions usually indicts the surface AFTER the message (landing page, checkout, form) — rewriting copy for a downstream funnel problem is the wrong surgery. Strong opens + weak clicks → content/CTA; weak opens → subject/timing/list.
- Never read a diagnostic (open rate) as a primary result — a great open rate on zero lift is a well-performing message inside a worthless journey.
- Never let the failed-strategies log silently veto without saying so — when the engine skips a strategy because of the log, it states which entry caused the skip.

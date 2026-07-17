# Lifecycle Journey Portfolio — Kanbanly

**Generated:** 2026-07-12 · **Industry:** saas · **Data tier:** T2 · **DQS:** 52/100
**Goal weighting:** revenue-first (trial conversion)

## 1. Executive summary

Kanbanly's CSV export covers all five SaaS must-have events (one via a user-confirmed alias), so every P0 pattern generates — but at **standard** depth (DQS 52): 4–7 steps, one open/click branch, no parameter-based gates. Six journeys were generated across activation, revenue, and retention; two are blocked on missing instrumentation (`feature` param, activity events + attributes). Trial conversion (`saas-trial-conversion-01`) launches first: with 1,380 trials and 96 conversions a month, it addresses the goal directly and every other journey inherits from it.

## 2. Portfolio table

| # | Journey | ID | Stage | Priority | Depth | Channels | Status |
|---|---------|----|----|----------|-------|----------|--------|
| 1 | Trial Conversion | `saas-trial-conversion-01` | Revenue | P0 | 6 steps, standard | email+in-app+push | ✅ generated |
| 2 | Welcome & First Project | `saas-welcome-onboarding-01` | Activation | P0 | 5 steps | email+in-app | ✅ generated |
| 3 | Activation Rescue | `saas-activation-01` | Activation | P0 | 4 steps | email+in-app | ✅ generated¹ |
| 4 | Payment Failure (Dunning) | `saas-payment-failure-01` | Revenue | P0 | 4 steps | email+in-app | ✅ generated² |
| 5 | Churn Prevention | `saas-churn-prevention-01` | Retention | P0 | 5 steps | email+in-app | ✅ generated³ |
| 6 | NPS & Follow-up | `saas-feedback-nps-01` | Retention | P1 | 3 steps | email+in-app | ✅ generated⁴ |
| 7 | Feature Adoption | `saas-feature-adoption-01` | Engagement | P1 | — | — | 🔒 blocked — missing `feature` param on `feature_used` |
| 8 | Expansion (Upsell) | `saas-upsell-cross-sell-01` | Revenue | P1 | — | — | 🔒 blocked — missing `session_start` + plan/seat attributes (health gate impossible) |

¹ Activation event = first `project_created` (user-confirmed "aha" action), standing in for the pattern's `tutorial_complete` role — flagged as an assumption from `lifecycle-map`.
² First two dunning notices are transactional (zero promotional content); only later steps count against marketing caps.
³ Decline detection limited to login frequency vs the account's own trailing baseline — no richer usage events exist in the CSV.
⁴ `survey_response` is emitted by the CRM's own survey block, not by product instrumentation — journey is CRM-native.

Winback is not listed as a row: defining a *lapsed subscriber* requires `subscription_cancel`, which is not tracked — it is grouped into the tracking plan with the churn items. Referral needs `invite_sent` (not tracked) and stays out of a revenue-first portfolio.

## 3. Lifecycle stage coverage

| Stage | Journeys | Coverage verdict |
|---|---|---|
| Acquisition | — | not applicable — engine works from `sign_up` onward |
| Activation | `saas-welcome-onboarding-01`, `saas-activation-01` | covered |
| Engagement | — | gap — feature-adoption is blocked on the `feature` param; referral is blocked on `invite_sent`. Unblocked by the P0 tracking-plan item. |
| Revenue | `saas-trial-conversion-01`, `saas-payment-failure-01` | covered (expansion blocked — see row 8) |
| Retention | `saas-churn-prevention-01`, `saas-feedback-nps-01` | covered |
| Winback | — | gap — no `subscription_cancel` event to define the lapsed audience; unblocked by tracking-plan item 3. |

## 4. Conflict & frequency review

**Shared triggers / audiences — who wins:**

- **Welcome vs Trial Conversion:** `sign_up` and `trial_start` fire at nearly the same moment, and both patterns open with a welcome touch. Resolution (a cut, not a note): Welcome **owns days 0–7** — Trial Conversion's opening step is merged away, and its sequence anchors to `trial_end` −7/−3/−1 days per the [pattern](../../knowledge/journey-patterns/trial-conversion.md).
- **Activation Rescue vs Welcome:** Rescue triggers on the *absence* of `project_created` after Welcome's window closes (day 7) — sequential by construction.
- **Churn Prevention / Dunning vs trial journeys:** paid-account audiences only; a user cannot be in both a trial journey and a paid-account journey.
- **NPS:** suppressed for users active in any P0 journey; detractors additionally suppress all marketing for a 14-day cooldown.

**Worst-case weekly message math** (caps per [consent-and-quiet-hours.md](../../knowledge/compliance/consent-and-quiet-hours.md): email 4/wk, push 5/wk, combined 8/wk):

| Scenario: one user, worst week | email | in-app | push | total |
|---|---:|---:|---:|---:|
| Trial week 1 (Welcome steps 1, 3, 5 + in-app step 2; Trial Conversion silent until mid-trial) | 3 | 1 | 0 | 4 |
| Trial week 2 (Trial Conversion: midpoint, −3d, −1d push, activation-split in-app) | 3 | 1 | 1 | 5 |
| Paid account, failing card (dunning marketing steps + churn-prevention deferred while dunning active) | 2 | 1 | 0 | 3 |
| **Worst case vs caps** | **3 / 4** | — | **1 / 5** | **5 / 8** |

All scenarios inside caps; churn-prevention defers while a dunning sequence is active on the same account (payment recovery outranks engagement recovery).

## 5. Launch roadmap

1. **Week 1 — `saas-trial-conversion-01`:** the stated goal; ~318 trials/week enter, measurable against a 10% holdout within one trial cycle.
2. **Week 1 — `saas-payment-failure-01`:** 41 failures/month is silent revenue loss; dunning is logistics, not persuasion — fastest win available.
3. **Month 1 — `saas-welcome-onboarding-01` + `saas-activation-01`:** the sign_up → first-project gap decides trial outcomes; launch as a pair (Welcome educates, Rescue catches the silent).
4. **Month 1 — `saas-churn-prevention-01`:** login-frequency decline detection on paid accounts; crude but better than none.
5. **Later — `saas-feedback-nps-01`:** after the P0 set is stable and there are enough paid accounts to survey.
6. **Tracking plan:** implement the `feature` param first — it upgrades Trial Conversion's branch quality and unblocks Feature Adoption.

## 6. Tracking plan summary

2 blocked journeys (+1 winback gap). Top 3 missing items by unlocked value:

1. **`feature` param on `project_created`/`feature_used`** (P0) — unblocks `saas-feature-adoption-01`; upgrades the trial-conversion activation split from "created any project" to per-feature depth.
2. **Params on `subscription_start`** (`plan`, `value`, `currency`) (P0) — conversion component 10 → ~16 on the DQS rubric; enables revenue KPIs per plan and expansion detection.
3. **`subscription_cancel`, `session_start` + plan/seat attributes** (P1) — unblocks winback and `saas-upsell-cross-sell-01` (health gate), sharpens churn detection.

**Projected DQS if implemented: ≈ 67** (diversity 15→17, conversion 10→16, funnel 16→20, attributes 7→10, volume unchanged at 4) — top of the standard class; the branched threshold (70) then hinges on conversion volume crossing 100/month.

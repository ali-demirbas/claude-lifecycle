---
name: churn-prevention
stage: retention
trigger_type: segment
required_events: [login, subscription_start]
optional_events: [feature_used, subscription_cancel, payment_failed, session_start, share]
required_attributes: []
optional_attributes: [usage_trend_30d, plan_type, renewal_date, seats_active, rfm_tier_change, champion_changed]
default_channels: [email, in-app]
base_steps: 4
depth_range: [3, 7]
applicable_industries: [saas, mobile-app, fintech, subscription-media, edtech, insurance]
mutually_exclusive_with: [winback]
---

# Churn Prevention

Intervene while a paying user is **declining but not yet gone** — falling usage, shrinking session frequency, or explicit cancel-intent signals. This is the pre-churn save window; winback is what's left when you miss it. The two are made mutually exclusive by the **watch buffer** (see Entry / exit): a failed intervention hands off to winback through a quiet observation state, never directly — so the same person is never messaged by both journeys in the same window.

Not every churn is this pattern's job. Route by churn type first: **voluntary with complaint** → negative-signal suppression plus human resolution (see [feedback-nps](feedback-nps.md) and [consent-and-quiet-hours](../compliance/consent-and-quiet-hours.md)); **involuntary** → the payment-failure/dunning pattern; **passive drift** → this pattern; **revenue churn** (still active but downgrading spend or plan) → an upsell/reinforcement problem, not a winback one.

## Required-event signature

| Event | Role |
|---|---|
| `login` | The engagement baseline. Declining login frequency vs the user's own prior period is the core trigger signal. Without it, decline cannot be detected — pattern is **blocked**. |
| `subscription_start` | Qualifies the audience (active paying relationship) and anchors `renewal_date` math. |
| `feature_used` *(optional)* | Much finer decline signal than logins — usage can hollow out while logins persist. Also powers "unused high-value feature" content. |
| `subscription_cancel` *(optional)* | For term subscriptions, a cancel today means churn at renewal — that gap is the save window for a dedicated cancel-intent branch. |
| `payment_failed` *(optional)* | Exclusion signal — involuntary churn belongs to the dunning journey (P0, transactional), never to this one. |
| `rfm_tier_change` *(optional attr)* | A tier downgrade is a trigger in its own right, even with zero behavioral red flags — value drift moves before behavioral drift, and for infrequent-purchase businesses where session data is sparse between purchases it is often the earliest available signal. Only meaningful boundary crossings count (e.g. champion → loyalist), not single-point fluctuations; direction matters (arrived falling → reinforcement, arrived rising → nurture). |
| `seats_active` / `champion_changed` *(optional attrs, B2B)* | Account-level signals: dropping seat utilization is fixed by nudging the admin to drive adoption, not by messaging inactive end-users; champion turnover is a strong B2B churn predictor visible only in account/role continuity. Renewal proximity without any expansion signal belongs on the same watch list. |

Beyond product events, the entry signature should also watch the softer early warnings: declining message engagement (opens/clicks falling before any product lapse), repeated help/self-service access on the same topic *without* resolution (one successful self-serve visit is a positive signal — the difference is repetition and resolution), recurring empty-state exposure, and widening gaps between key actions.

## Entry / exit

- **Entry:** active subscription, rolling 30-day usage (`login` or `feature_used` count) down materially versus the prior period — a starting definition of "materially" is ≥ 30% down, recalibrate per business once enough churned-vs-recovered history exists to check the number against outcomes — or a cancel-intent signal on an unexpired term — while the user is still occasionally active.
- **Exclude:** fully silent past the lapse threshold (winback owns them), accounts < 30 days old (activation owns them), `payment_failed` open (dunning owns them).
- **Success exit:** usage recovers to baseline (e.g. weekly-active for 2 consecutive weeks) or renewal completes · **Window:** 30 days · **Re-entry:** once per 60 days.
- **Failure exit (watch buffer):** when the intervention fails and risk keeps climbing, do **not** hand off to winback instantly — enter a quiet "watch" state: messaging near zero, observe for a defined window. Recovers → exit healthy; crosses the lapse threshold → hand off to [winback](winback.md). The buffer prevents over-messaging a softening user and is the mechanism that keeps churn-prevention and winback from messaging the same person in the same window.
- **Risk × value gating:** low-value at-risk users get a light touch or nothing — chasing every at-risk user regardless of value spends budget and channel goodwill on relationships that were never worth the cost of saving.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (3) | DQS < 40 or only required events | Value recap → workflow tip → check-in. Email only, decline detected on logins alone. |
| Standard (4–5) | DQS 40–69 | Adds in-app step and a `feature_used`-driven "unused feature" message; content matched to `plan_type`. |
| Branched (6–7) | DQS ≥ 70 + `subscription_cancel` or `usage_trend_30d` | Separate cancel-intent save track (approved offer, renewal-date-aware timing) vs quiet-decline track (value re-engagement). Where `rfm_tier_change` exists, a tier downgrade opens a value-drift entry lane that fires even with zero behavioral red flags. |

## Step blueprint (standard, 4 steps)

| # | Wait | Channel | Intent | Branch |
|---|------|---------|--------|--------|
| 1 | on entry | in-app | Surface one high-value feature they haven't used, in context on next session | — |
| 2 | +3d | email | Usage recap: what they've accomplished with the product to date — remind them of sunk value | — |
| 3 | +5d | email | Workflow tip or short case study matched to `plan_type` / use pattern | if usage not recovering |
| 4 | +7d | email | Human check-in: support, success call, or reply-to-this offer; cancel-intent users get the approved save offer here | cancel-intent → save branch |
| — | after step 4, if still declining | (quiet) | **Watch buffer:** suppress non-transactional messaging and observe for the remainder of the window. Recovery → healthy exit; lapse threshold crossed → hand off to winback | failure path |

Anomaly-entry framing: when entry was a sharp break in the user's own pattern (abrupt stop, often right after an error, a failed action, or a support-worthy event) rather than gradual drift, the first touch reads as **support, not marketing** — "did something go wrong? one tap to a human" — because a sudden stop is more often a broken experience than faded interest, and a promo landing on a frustration is how quiet decline becomes an angry cancel.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Engagement recovery rate | primary | entrants returning to baseline usage within window / entrants — measured against a holdout, since some decline self-heals |
| Churn rate at next renewal | secondary | the lagging confirmation of the primary |
| Unsubscribe + in-app dismiss rate | guardrail | declining users are one annoyance from cancelling; message pressure here is riskier than anywhere else |

## Common mistakes

- Waiting for silence before acting — once they stop opening anything, it's winback, and winback converts worse; the save window is while messages still get read.
- Sending everyone the discount save-offer — reserve incentives for confirmed cancel intent; quiet decliners need value restated, not price cut.
- Measuring opens and clicks instead of usage recovery — a churn-prevention email that gets opened but doesn't change product behavior did nothing.
- Feeding the churn model inputs that are only knowable after the user leaves — data leakage makes the model look great in backtests and predict nothing in production; every input must be observable *before* the churn event.
- Jumping straight from a failed intervention to full winback escalation without the watch buffer — the softening user gets double-messaged by two journeys at once.

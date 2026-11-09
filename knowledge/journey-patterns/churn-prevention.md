---
name: churn-prevention
stage: retention
trigger_type: segment
journey_class: marketing
required_events: [login, subscription_start]
optional_events: [feature_used, cancellation_intent, subscription_cancel, payment_failed, session_start, share, subscription_renewed, support_ticket_opened, usage_recovered, subscription_expired, consent_withdrawn]
required_attributes: []
optional_attributes: [usage_trend_30d, plan_type, renewal_date, seats_active, rfm_tier_change, champion_changed, risk_score]
default_channels: [email, in_app]
base_steps: 4
depth_range: [3, 7]
applicable_industries: [saas, mobile-app, fintech, subscription-media, edtech, insurance]
mutually_exclusive_with: [winback]
signal_sources: {login: behavioral, subscription_start: authoritative, feature_used: behavioral, session_start: behavioral, cancellation_intent: behavioral, subscription_cancel: authoritative, support_ticket_opened: authoritative, subscription_renewed: authoritative, payment_failed: authoritative, usage_trend_30d: behavioral, rfm_tier_change: inferred, risk_score: inferred, seats_active: authoritative, champion_changed: authoritative, usage_recovered: behavioral, subscription_expired: authoritative, consent_withdrawn: authoritative}
insufficient_alone:
  - a risk score whose drivers cannot be traced back to observed signals
  - high account value
  - one weak decline signal with no independent signal agreeing
  - falling email opens
  - a single help-center visit that resolved the question
  - a cancel-page visit or a started cancel flow, read as a confirmed cancellation
exit_before_each_send: [usage_recovered, subscription_renewed, subscription_cancel, payment_failed, subscription_expired, consent_withdrawn]
reentry: {policy: after_cooldown, cooldown: P60D, on_duplicate_trigger: ignore}
measurement_default: holdout
instance_key: subscription_id
---

# Churn Prevention

Intervene while a paying user is **declining but not yet gone**: falling usage, shrinking session frequency, or explicit cancel-intent signals. This is the pre-churn save window; winback is what's left when you miss it. The two are made mutually exclusive by the **watch buffer** (decision `d3` in the blueprint): a failed intervention hands off to winback only after a send-free observation window, never directly, so the same person is never messaged by both journeys in the same window.

Not every churn is this pattern's job. Route by churn type first: **voluntary with complaint** → negative-signal suppression plus human resolution (see [feedback-nps](feedback-nps.md) and [consent-and-quiet-hours](../compliance/consent-and-quiet-hours.md)); **involuntary** → the [payment-failure](payment-failure.md)/dunning pattern; **passive drift** → this pattern; **revenue churn** (still active but downgrading spend or plan) → an upsell/reinforcement problem, not a winback one.

## Required-event signature

| Event | Source | Role |
|---|---|---|
| `login` | behavioral | The engagement baseline. Declining login frequency vs the user's own prior period is the core trigger signal. Without it, decline cannot be detected: pattern is **blocked**. |
| `subscription_start` | authoritative | Qualifies the audience (active paying relationship) and anchors `renewal_date` math. |
| `feature_used` *(optional)* | behavioral | Much finer decline signal than logins: usage can hollow out while logins persist. Also powers "unused high-value feature" content. |
| `cancellation_intent` *(optional)* | behavioral | Cancel intent: a cancel-page visit or a cancel flow started and not completed. The only signal the save branch reacts to. Intent is not a decision; many people look and stay. |
| `subscription_cancel` *(optional)* | authoritative | A confirmed cancellation recorded by billing. It is not a save signal: it exits this journey for this subscription and hands off to [cancellation-winddown](cancellation-winddown.md) once, with queued sends suppressed. |
| `subscription_renewed` *(optional)* | authoritative | Success exit for renewal-bound plans. |
| `payment_failed` *(optional)* | authoritative | Exclusion and exit signal: involuntary churn belongs to the dunning journey (transactional), never to this one. |
| `rfm_tier_change` *(optional attr)* | inferred | A tier downgrade is a trigger in its own right, even with zero behavioral red flags: value drift moves before behavioral drift, and for infrequent-purchase businesses where session data is sparse between purchases it is often the earliest available signal. Only meaningful boundary crossings count (e.g. champion → loyalist), not single-point fluctuations; direction matters (arrived falling → reinforcement, arrived rising → nurture). |
| `risk_score` *(optional attr)* | inferred | Orders who is looked at first; never decides a tier on its own (see below). |
| `seats_active` / `champion_changed` *(optional attrs, B2B)* | authoritative | Account-level signals: dropping seat utilization is fixed by nudging the admin to drive adoption, not by messaging inactive end-users; champion turnover is a strong B2B churn predictor visible only in account/role continuity. Renewal proximity without any expansion signal belongs on the same watch list. |

`usage_recovered` is a derived event, not a tracked one: it fires when `login`/`feature_used` return to the user's own baseline (default: weekly-active for 2 consecutive weeks; configurable). It is computed from the usage events, never from a falling risk score.

Beyond product events, the entry signature should also watch the softer early warnings: declining message engagement read from bot-filtered clicks (not opens), repeated help/self-service access on the same topic *without* resolution (one successful self-serve visit is a positive signal; the difference is repetition and resolution), recurring empty-state exposure, and widening gaps between key actions.

### Not enough on its own

- **A risk score whose drivers cannot be traced back to observed signals.** A score is a ranking aid. If nobody can say which usage, login, payment or support fact moved it, it cannot justify contact, let alone escalation. A score dropping is not recovery either: recovery is re-read from the usage events.
- **High account value.** Value says how much is at stake, not how likely the loss is. A large, healthy account is not at risk because it is large; value decides how much effort a confirmed risk earns, not whether risk exists.
- **One weak decline signal with no independent signal agreeing.** A single soft signal earns at most the lightest touch (the in-app step). Moving up a tier (human check-in, save offer) needs a second signal from an independent source agreeing: usage decline plus unresolved support contact, say, not two views of the same login count.
- **Falling email opens.** Privacy proxies and image blocking make opens unreliable; message disengagement is read from bot-filtered clicks.
- **A single help-center visit that resolved the question.** That is the product working. Repeated visits on the same topic without resolution are the warning.
- **A cancel-page visit or a started cancel flow, read as a confirmed cancellation.** Intent and decision are different signals. Intent may open the save branch; only `subscription_cancel` from billing confirms a cancellation, and that ends the save path rather than feeding it.

## Entry / exit

- **Entry:** active subscription, rolling 30-day usage (`login` or `feature_used` count) down materially versus the prior period (a starting definition of "materially" is ≥ 30% down; recalibrate per business once enough churned-vs-recovered history exists to check the number against outcomes), or a `cancellation_intent` signal on an unexpired term, while the user is still occasionally active. One instance per `subscription_id` (the account's subscription for B2B).
- **Risk tiers escalate on corroboration only.** Tier 1 (light, in-app/value content) needs one qualifying signal. Tier 2 (human check-in) and tier 3 (approved save offer) each need independent signals agreeing, and each escalation re-reads the underlying usage, payment and support state rather than trusting the score that ordered the queue. No incentive appears before tier 3.
- **Exclude:** a confirmed `subscription_cancel` already recorded for this subscription ([cancellation-winddown](cancellation-winddown.md) owns it), fully silent past the lapse threshold ([winback](winback.md) owns them), accounts < 30 days old (activation owns them), `payment_failed` open (dunning owns them), users under the portfolio negative-signal override, and accounts with an open issue already owned by a person (that owner speaks for the brand).
- **Risk × value gating:** low-value at-risk users get a light touch or nothing. Chasing every at-risk user regardless of value spends budget and channel goodwill on relationships that were never worth the cost of saving. Value gates the spend; it never stands in for evidence of risk.
- **Success exit:** `usage_recovered` or `subscription_renewed` · **Window:** 30 days.
- **Checked before each send:** for this subscription (`same_instance`): `usage_recovered`, `subscription_renewed`, `subscription_cancel` (confirmed cancellation: exit the save path, hand off to cancellation-winddown), `payment_failed` (hand to dunning), `subscription_expired`. `consent_withdrawn` is channel-scoped: an email unsubscribe stops the email steps, and the in-app step still renders unless the user turned off in-product messages.
- **Re-entry:** after a 60-day cooldown. A repeated trigger while an instance is open is ignored (the same risk episode re-crossing the threshold is the same instance).
- **Failure exit (watch buffer):** when the intervention fails, the user does **not** go to winback instantly. After the last send, a send-free observation window runs to the end of the journey window (decision `d3`). Recovers → healthy exit; crosses the lapse threshold → handoff to [winback](winback.md) with queued sends from this journey suppressed. Neither → the instance expires quietly. The buffer prevents over-messaging a softening user and is the mechanism that keeps churn-prevention and winback from messaging the same person in the same window.
- **Handoffs:** `subscription_cancel` (confirmed) → [cancellation-winddown](cancellation-winddown.md), once per subscription, queued sends suppressed, including a scheduled save offer: after a confirmed cancellation nobody argues the decision again; `payment_failed` → [payment-failure](payment-failure.md) (suppress queued); lapse after the buffer → [winback](winback.md) (suppress queued).

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (3) | DQS < 40 or only required events | Value recap → workflow tip → check-in. Email only, decline detected on logins alone. |
| Standard (4–5) | DQS 40–69 | Adds in-app step and a `feature_used`-driven "unused feature" message; content matched to `plan_type`. |
| Branched (6–7) | DQS ≥ 70 + `cancellation_intent` or `usage_trend_30d` | Separate cancel-intent save track (approved offer, renewal-date-aware timing) vs quiet-decline track (value re-engagement). Where `rfm_tier_change` exists, a tier downgrade opens a value-drift entry lane that fires even with zero behavioral red flags. |

## Step blueprint (standard, 4 sends)

| Node | When | Channel | Intent | Route |
|---|---|---|---|---|
| s1 | entry +0h | in_app | Open the next useful action: one high-value feature they haven't used, or the last meaningful context they left, shown in place. Shown at the next session, expires after 3d; s2 is anchored to s1's scheduled time and never waits for the view | → s2 |
| s2 | s1 +3d | email | Usage recap: what they've accomplished with the product to date, a reminder of value already built | → d1 |
| d1 | s2 +5d | — | Decision on `usage_recovered` (behavioral, derived from `login` / `feature_used`) between entry and s2 +5d | occurred → exit (completed) · not_occurred → s3 · unmeasurable → s3 |
| s3 | d1 +0h | email | Workflow tip or short case study matched to `plan_type` / use pattern | → d2 |
| d2 | s3 +7d | — | Decision on all_of(`cancellation_intent` (behavioral), usage still below baseline via `usage_trend_30d` (behavioral)) between entry and s3 +7d. Intent plus a second, independent signal opens the offer tier; a confirmed `subscription_cancel` never reaches this decision because it exits the instance first | occurred → s4b · not_occurred → s4 · unmeasurable → s4 |
| s4 | d2 +0h | email | Human check-in: support, success call, or reply-to-this; asks what's wrong, offers nothing | → d3 |
| s4b | d2 +0h | email | Cancel-intent save: the approved offer, timed against `renewal_date`, plus the same human route. Re-checks `subscription_cancel` immediately before sending; if the cancellation was confirmed meanwhile, it is not sent | → d3 |
| d3 | entry +30d | — | Decision on `usage_recovered` (behavioral, derived) between d2 and entry +30d; the watch buffer, no sends in this window | occurred → exit (completed) · not_occurred → d4 · unmeasurable → exit (expired, neutral) |
| d4 | d3 +0h | — | Decision on any_of(`login` (behavioral), `session_start` (behavioral)) within the trailing lapse threshold ending at d3 | occurred → exit (expired, still present) · not_occurred → exit (handoff → winback, suppress queued) · unmeasurable → exit (expired) |

Anomaly-entry framing: when entry was a sharp break in the user's own pattern (abrupt stop, often right after an error, a failed action, or a support-worthy event) rather than gradual drift, the first touch reads as **support, not marketing** ("did something go wrong? one tap to a human"), because a sudden stop is more often a broken experience than faded interest, and a promo landing on a frustration is how quiet decline becomes an angry cancel.

## Timing and channel fit

- **In-app** fits s1: it reaches the user while they are still occasionally present, costs no inbox attention, and points at the next action in context. It has no quiet-hours constraint because it renders on the user's own session; it waits at most 3 days for that session, then is skipped.
- **Email** carries the recap, tip and check-in: content worth reading at the user's pace. Send in the user's daytime (avoid 00:00–06:00 user local); a human check-in that leads to a call follows the business clock and staffing, not the user's.
- **Save offer (s4b)** is anchored to the term: it must land before `renewal_date` with time to act (default `renewal_date -14d` or earlier; configurable), never after the cancellation has taken effect.
- **Fallback:** no in-app surface or no session in the window → s1 content folds into s2. No email consent → in-app only, and the human check-in goes through the account owner or support queue if one exists. Push is deliberately not a default: unprompted pushes to a softening user read as pressure.

## Frequency and overlap

- **Worst path:** 2 sends in any rolling 7 days (s1+s2, or s2 on day 3 with s3 on day 8). Declining users get *fewer* messages under the cap, not more (compliance file, cap-by-engagement rule).
- **Usually overlaps with:** [feature-adoption](feature-adoption.md), [upsell-cross-sell](upsell-cross-sell.md), [feedback-nps](feedback-nps.md), [payment-failure](payment-failure.md), [winback](winback.md) (mutually exclusive).
- **Precedence:** dunning, [cancellation-winddown](cancellation-winddown.md), [renewal-reminder](renewal-reminder.md)'s last 7 days and the negative-signal override outrank this journey (it defers, pauses or exits). While an instance is open, upsell and cross-sell sends to the same user are deferred; selling more to someone on the way out accelerates the exit. A feature-adoption message for the same feature as s1 is deduplicated (one of them, not both).

## Measurement

- **Primary outcome:** `usage_recovered` within 30 days; churn at next renewal is the lagging confirmation.
- **Design:** holdout (default 10%), assigned at user level (account level for B2B, so colleagues in one account share an arm). The control does not receive s1–s4b, including the save offer.
- **Routine communications both groups keep:** transactional billing and renewal notices, product release announcements sent to all users, and the in-product cancellation flow's own retention screen.
- **Contamination risks:** customer-success staff contacting held-out accounts by hand; feature-adoption or in-app tours delivering the same "unused feature" content; the cancellation flow's save offer reaching both arms.
- **Low volume:** some decline self-heals, so a raw recovery rate without a control flatters the journey. When the power calculation shows the control arm is too small, report recovery as unmeasured rather than as a lift; small B2B books usually can only show a pre/post comparison of churn-at-renewal, labeled as descriptive.

## When data is missing

- **No `feature_used`:** decline is read from logins alone (Simple depth), and the "unused feature" content falls back to the plan's documented core features.
- **No baseline yet** (account younger than the comparison period): not eligible; activation owns them.
- **Usage events delayed or missing for a user:** `d1`/`d3` route to their unmeasurable branches; the sequence continues or expires neutrally, and missing data never produces a lapse handoff.
- **No `cancellation_intent`:** no save branch; everyone reaching `d2` gets the check-in. `subscription_cancel` alone never substitutes for intent: it is a confirmed decision and exits the journey.
- **`usage_trend_30d` missing at `d2`:** the all_of is unmeasurable even when intent occurred, so the route is the check-in without an offer.
- **No computable lapse threshold:** `d4` uses the industry playbook's `churn_signal` default, recorded as an assumption.
- **Only a score is available:** the score orders the queue, but nobody escalates past tier 1 until a decomposable signal agrees.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Engagement recovery rate | primary | entrants returning to baseline usage within window / entrants, measured against a holdout, since some decline self-heals |
| Churn rate at next renewal | secondary | the lagging confirmation of the primary |
| Unsubscribe + in-app dismiss rate | guardrail | declining users are one annoyance from cancelling; message pressure here is riskier than anywhere else |

## Common mistakes

- Waiting for silence before acting: once they stop showing up in the product, it's winback, and winback converts worse. The save window is while they are still occasionally present.
- Sending everyone the discount save-offer: reserve incentives for cancel intent backed by a second signal; quiet decliners need value restated, not price cut.
- Sending a save offer after the cancellation is confirmed: that argues with a decision already made. A recorded cancellation exits to cancellation-winddown and suppresses the queued offer.
- Escalating on a model score alone, or treating a big account as an at-risk account: escalation needs independent signals that agree.
- Measuring opens and clicks instead of usage recovery: a churn-prevention email that gets clicked but doesn't change product behavior did nothing.
- Feeding the churn model inputs that are only knowable after the user leaves: data leakage makes the model look great in backtests and predict nothing in production; every input must be observable *before* the churn event.
- Jumping straight from a failed intervention to full winback escalation without the watch buffer: the softening user gets double-messaged by two journeys at once.

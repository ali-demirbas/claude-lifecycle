---
name: payment-failure
stage: revenue
trigger_type: event
journey_class: transactional
required_events: [payment_failed, payment_succeeded]
optional_events: [subscription_cancel, login, add_payment_info, payment_status_unknown, access_suspended, access_restored]
required_attributes: [failure_reason]
optional_attributes: [retry_schedule, plan_name, payment_method_type, charged_payment_method, grace_end_date]
default_channels: [email, sms, in-app]
base_steps: 4
depth_range: [3, 6]
applicable_industries: [saas, subscription-media, fintech, mobile-app, insurance, edtech]
mutually_exclusive_with: []
signal_sources: {payment_failed: authoritative, payment_succeeded: authoritative, failure_reason: authoritative, payment_status_unknown: authoritative, add_payment_info: authoritative, subscription_cancel: authoritative, access_suspended: authoritative, access_restored: authoritative, retry_schedule: authoritative, charged_payment_method: authoritative, grace_end_date: authoritative, login: behavioral}
insufficient_alone:
  - a payment status of unknown or timeout
  - a card update with no successful charge yet
  - a pending automatic retry
  - email opens
exit_before_each_send: [payment_succeeded, subscription_cancel]
reentry: {policy: each_trigger, on_duplicate_trigger: ignore}
measurement_default: none_service
---

# Payment Failure (Dunning)

Recover failed subscription payments before involuntary churn. This protects existing revenue rather than creating new revenue, and it is often the highest-ROI journey a subscription business never built.

**Journey class: transactional.** Each notice exists because a specific charge on the customer's own account failed; it reports the state of that transaction and what happens next, which is the compliance file's definition of a transactional message (see [consent-and-quiet-hours.md](../compliance/consent-and-quiet-hours.md)). It is not `service`, which this repo uses for relationship obligations not tied to one transaction (renewal notices, protective alerts). Two consequences follow: the notices are exempt from marketing consent and marketing frequency caps **only while they contain zero promotional content**, and the journey is **never held out**: withholding a customer's payment-failure notice to measure lift would cause involuntary churn on purpose. The moment a step upsells ("upgrade to annual and save"), that step is marketing, requires marketing consent, and counts against frequency caps.

## Required-event signature

| Event | Source | Role |
|---|---|---|
| `payment_failed` | authoritative | Trigger. Must be a definitive decline and carry `failure_reason` (card expired vs insufficient funds vs hard decline): the branch key. |
| `payment_succeeded` | authoritative | Success exit (a renewal `purchase` or billing-system webhook is an acceptable stand-in). Without it, recovery is unmeasurable: pattern is **blocked**. |
| `payment_status_unknown` *(optional)* | authoritative | Timeout or pending status from the processor. Holds entry until reconciliation; never a trigger. |
| `subscription_cancel` *(optional)* | authoritative | Hard exit; also separates voluntary from involuntary churn in reporting. |
| `add_payment_info` *(optional)* | authoritative | Intermediate signal: card updated but retry pending; suppresses further urgency. |
| `access_suspended` / `access_restored` *(optional)* | authoritative | Mark the end of grace and the return of access; restoration must be confirmed to the customer (see Entry / exit). |
| `charged_payment_method` *(optional attr)* | authoritative | Which method a successful charge actually used, so a backup-method charge can be named. |
| `retry_schedule` *(optional attr)* | authoritative | Aligns messages with the processor's automatic retries instead of fighting them. |

### Not enough on its own

- **A payment status of unknown or timeout.** A timeout means nobody knows yet whether money moved. Telling a customer their payment failed when it may have succeeded creates double charges and support tickets. The instance opens only on a definitive decline after reconciliation; a status that stays unknown goes to billing operations, not to the customer.
- **A card update with no successful charge yet.** `add_payment_info` calms the tone (no more "please update") but is not recovery; the journey continues until `payment_succeeded`.
- **A pending automatic retry.** It is a reason to time messages around the retry, not a reason for urgency.
- **Email opens.** Nothing in this journey branches on them.

## Entry / exit

- **Entry:** a definitive `payment_failed` on an active subscription, no `payment_succeeded` for the same invoice since. Transactional status means consent gating is minimal, but channel-level opt-outs for the account (an SMS stop request, for example) are honored.
- **Backup method charged:** when the primary method fails and a stored backup method is then charged successfully, no dunning instance opens. The customer gets one transactional notice that names the backup method that was charged (type and last digits as policy allows) and asks them to fix the primary if they want it used. Same rule mid-journey: a recovery through a backup method exits the journey, and the success notice names that method.
- **Exclude:** user already in this journey for the same invoice, subscription already cancelled, failure on a free-trial card authorization (different message entirely), status still unknown.
- **Success exit:** `payment_succeeded` for the failing invoice · **Window:** the grace period (typically 7–21 days, set by billing config; `grace_end_date`).
- **Checked before each send:** `payment_succeeded`, `subscription_cancel`. Marketing consent withdrawal does not stop these notices; it does stop the optional post-recovery marketing step.
- **Restriction is never a surprise:** if there was time to warn before access is restricted, the warning (s4) must have gone out first; a suspension without a prior final notice is a defect.
- **Restoration is confirmed explicitly:** when payment succeeds after `access_suspended`, the customer receives a transactional confirmation that access is back, triggered on `access_restored`. That confirmation sits outside this graph, because a send after the success event would be cancelled by the before-each-send check; the journey doc must name the message that does it, and QA treats its absence as a gap.
- **Re-entry:** per distinct failed invoice. A repeated `payment_failed` for the same invoice (a failed automatic retry) is ignored by the trigger; the open instance continues on its own timeline.
- **Handoffs:** none on success. If grace ends without payment and the subscription lapses, [winback](winback.md) may pick the person up later on its own lapse clock, after paid access has ended.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (3) | DQS < 40 or no `failure_reason` | Notice → reminder → final notice before suspension. Single channel, all transactional. |
| Standard (4–5) | DQS 40–69 | Branches on `failure_reason` (expired card gets "update card", insufficient funds gets retry-date framing) and on card update; adds second channel for the final notice. |
| Branched (6) | DQS ≥ 70 + `add_payment_info` + `retry_schedule` | Syncs with processor retries, suppresses on card update, adds a suspension notice on `access_suspended`, and may append one *marketing* step post-recovery (e.g. annual-plan offer), clearly flagged as consent-gated and capped. |

Depth is bounded by the grace period, not by DQS ambition: every step must land before suspension.

## Step blueprint (standard, 4 sends)

| Node | When | Channel | Intent | Route |
|---|---|---|---|---|
| s1 | entry +1h | email | Transactional notice: what failed, why (`failure_reason`), whether a backup method will be tried, one-click link to update payment. No promo content. | → d1 |
| d1 | s1 +3d | — | Decision on `add_payment_info` (authoritative) between entry and s1 +3d | occurred → s3 · not_occurred → s2 · unmeasurable → s2 |
| s2 | d1 +0h | email | Transactional reminder aligned to the next automatic retry date; reassure that service continues during grace | → s3 |
| s3 | s1 +6d | in-app | Persistent banner: payment issue, days remaining in grace (or "card updated, we'll retry on date" when d1 occurred) | → s4 |
| s4 | grace_end_date -2d at 10:00 user_local | sms | Final transactional notice: exact suspension date and what happens to data/access | → exit (expired) at grace_end_date |

Tone rule: this is a service conversation with a customer who *wants* to pay in most cases (expired cards dominate). No guilt, no urgency theater: clarity and a working update link do the work. A failure message answers three things, in this order: **what is safe/unchanged** ("your coverage continues through the grace period", "your data is intact"), **what is being done**, and **when the user will hear next** (a concrete time, honored). Fear of loss is the reader's default state in a payment failure; the message's job is to remove it, never to lean on it.

## Timing and channel fit

- **Email** carries the notice and reminder: it holds the update link and the details. Sent promptly (s1 within the hour), but never 00:00–06:00 user local.
- **In-app** reaches the customer where they already are, without adding inbox pressure; it stays visible until resolved.
- **SMS** is reserved for the one final notice. Transactional status exempts it from marketing caps, not from quiet hours: 20:00–10:00 user local, no Sundays by default.
- **Timing follows billing, not marketing:** s2 is placed before the next automatic retry so an updated card is in place when the retry runs; asking hours before a retry that would have succeeded anyway creates needless friction.
- **Fallback:** no SMS channel or an SMS opt-out → the final notice goes by email and in-app; no in-app surface → s3 is skipped.

## Frequency and overlap

- **Worst path:** 3 sends in the first rolling 7 days (s1, s2, s3), plus the final notice. These are transactional and do not count against marketing caps, but they are counted in the per-user view so marketing journeys back off.
- **Usually overlaps with:** [churn-prevention](churn-prevention.md) (excluded while `payment_failed` is open), [renewal-reminder](renewal-reminder.md) and [cancellation-winddown](cancellation-winddown.md) (both hand money problems to this journey), [upsell-cross-sell](upsell-cross-sell.md), any promotional campaign.
- **Precedence:** this journey owns the customer's money conversation while an invoice is open. Promotional sends that reference paid features or prices are suppressed for the duration; other marketing defers by at least 24h around each notice.

## Measurement

- **Primary outcome:** `payment_succeeded` within the grace window.
- **Design:** `none_service`, no holdout. Reason: withholding a payment-failure notice from a random group would knowingly cause involuntary churn and leaves customers uninformed about their own account.
- **Alternative:** pre/post recovery rate against the pre-launch baseline (processor retries alone), read over full billing cycles; and in-journey experiments where every arm receives a notice and only timing, channel or wording differs.
- **Routine communications:** the billing system's own receipts and failure emails keep going; if they duplicate s1, one of them is switched off, and the journey doc says which.
- **Contamination risks:** processor-side changes (card updater services, retry logic changes) during the pre/post window; seasonal card-expiry waves.
- **Low volume:** small books produce noisy monthly recovery rates; compare multi-month averages and report the result as descriptive, not causal.

## When data is missing

- **No `failure_reason`:** one generic, accurate notice per step (Simple depth); no reason-specific asks.
- **No `retry_schedule`:** s2 uses the fixed default offset; the journey doc flags that it may collide with retries.
- **No `add_payment_info`:** `d1` takes its unmeasurable route (the reminder goes out).
- **Status unknown/timeout:** no instance; billing operations reconciles first.
- **No `access_restored` event:** restoration confirmation is triggered on the first `payment_succeeded` after `access_suspended`, and the gap goes into the tracking plan.
- **No `charged_payment_method`:** the success notice says the payment went through without naming a method, rather than guessing.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Payment recovery rate | primary | `payment_succeeded` within grace / failures entered, read pre/post, not against a holdout |
| Involuntary churn rate | secondary | subscriptions suspended after full sequence: the number this journey exists to shrink |
| Complaint/opt-out rate on SMS step | guardrail | transactional SMS still burns trust if overused; one final notice, never a drip |

## Common mistakes

- Putting promotional content in the first notices: instantly reclassifies the message as marketing, voiding the consent exemption and creating İYS/GDPR exposure.
- Holding the journey out like a marketing campaign to "measure lift".
- Treating a timeout as a decline and telling the customer their payment failed.
- Ignoring the processor's retry schedule: asking users to "update your card" hours before an automatic retry would have succeeded creates needless friction and support tickets.
- One generic message for all `failure_reason` values: an expired card and a hard decline need different asks; treating them identically costs recovery.
- Restoring access silently after a suspension, leaving the customer unsure whether it worked.

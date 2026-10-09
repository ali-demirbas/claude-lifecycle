---
name: cancellation-winddown
stage: retention
trigger_type: event
required_events: [subscription_cancel, subscription_expired]
optional_events: [subscription_reactivated, subscription_pause, subscription_resumed, payment_failed, data_export, support_ticket_created, cancel_reason_submitted]
required_attributes: [access_end_date]
optional_attributes: [plan_name, cancel_reason, marketing_consent, resume_date, renewal_price, data_retention_days, outstanding_balance]
default_channels: [email, push, in_app]
base_steps: 3
depth_range: [2, 4]
applicable_industries: [saas, subscription-media, edtech, mobile-app, fintech, insurance]
mutually_exclusive_with: []
journey_class: service
signal_sources: {subscription_cancel: authoritative, subscription_expired: authoritative, access_end_date: authoritative, subscription_reactivated: authoritative, subscription_pause: authoritative, subscription_resumed: authoritative, resume_date: authoritative, payment_failed: authoritative, marketing_consent: authoritative, support_ticket_created: authoritative, data_export: behavioral, cancel_reason_submitted: behavioral, cancel_reason: behavioral}
insufficient_alone:
  - a click on the cancel button or a visit to the cancellation page
  - a cancel-reason survey answer
  - an access end date computed from the signup date plus the plan length
  - an app uninstall
  - the last send of this journey having gone out
exit_before_each_send: [subscription_reactivated, subscription_expired, subscription_resumed]
reentry: {policy: each_trigger, on_duplicate_trigger: ignore}
measurement_default: none_service
instance_key: subscription_id
---

# Cancellation Wind-down

Carry a customer from a confirmed cancellation to the moment paid access actually ends, so the end date is never a surprise and staying remains one plain step away until then. This journey does not try to change the decision. A save attempt belongs before the cancellation is confirmed (churn-prevention, a cancel-flow offer); once the billing system records it, arguing again reads as not listening and produces complaints, not saves. Win-back starts only after paid access has really ended, and in a different journey.

A **pause variant** runs on the same skeleton: the customer chose a break with a resume date, and the job is to confirm that date, remind them before billing restarts, and keep everything else quiet while the pause lasts.

**Journey class: service.** The confirmation is a direct response to the customer's own action (transactional in nature); the ending notice tells them what they paid for and when it stops. Neither carries an offer, a discount or a "we'll miss you" pitch, so neither needs marketing consent nor counts against marketing caps. The pattern deliberately has no marketing node: anything persuasive is win-back's job, after access ends, under win-back's consent check.

## Required-event signature

| Event | Source | Role |
|---|---|---|
| `subscription_cancel` | authoritative | Trigger. The billing or policy system's record of the cancellation, carrying the subscription id. Mobile store billing maps its cancellation notification. |
| `access_end_date` *(attr)* | authoritative | The effective end of paid access, read from billing and re-read before each send. Every send counts down to it. Without it the pattern is **blocked** for anything beyond the confirmation. |
| `subscription_expired` | authoritative | Access has actually ended (insurance `policy_lapsed` / cancellation effective). Gates the win-back handoff; without it the handoff can't be timed honestly. |
| `subscription_reactivated` *(optional)* | authoritative | The customer withdrew the cancellation before the end date. Exits at once; no further wind-down send. |
| `subscription_pause` / `subscription_resumed` + `resume_date` *(optional)* | authoritative | Pause variant trigger, its anchor and its success exit. |
| `payment_failed` *(optional)* | authoritative | Pause variant: the restart charge failed, so payment-failure takes over. Main path: an outstanding balance owned by payment recovery. |
| `marketing_consent` *(optional attr)* | authoritative | Consent state at the moment of cancellation, carried to win-back. A withdrawal recorded in the cancel flow is final. |
| `support_ticket_created` *(optional)* | authoritative | Measurement: surprise contacts about lost access around the end date. |
| `data_export`, `cancel_reason_submitted` *(optional)* | behavioral | Shape content (skip the export reminder for someone who already exported) and reporting. Never branch on the cancel reason to re-pitch. |

### Not enough on its own

- **A click on the cancel button or a visit to the cancellation page.** Starting a cancel flow is not a cancellation; many people look and stay. Confirming a cancellation that didn't happen is a serious error.
- **A cancel-reason survey answer.** It may arrive without a recorded cancellation (abandoned flow) and never carries the end date.
- **An access end date computed from the signup date plus the plan length.** Pro-rating, prepaid annual terms, trial extensions and refunds move the real date. Only the billing system's date appears in a message.
- **An app uninstall.** Uninstalling does not cancel billing, and a store-side cancellation arrives as a billing notification, not as an analytics event.
- **The last send of this journey having gone out.** The win-back handoff waits for `subscription_expired`, not for this journey to run out of steps.

## Entry / exit

- **Entry:** `subscription_cancel` recorded for an active paid subscription, with `access_end_date` in the future or today. Instance key: `subscription_id` (one wind-down per subscription and term). Cancel intent (a cancel page, a started flow) never enters this journey; that belongs to churn-prevention's save branch.
- **Time anchor:** the distance to `access_end_date` varies per customer (a monthly plan cancelled on its last day, an annual prepaid term cancelled in month two), so a generated journey declares it as a range relative to entry, `access_end_date: entry +0d … +366d` (narrowed to the product's longest prepaid term), and reads the real date from billing at every send. It is never computed from signup date plus plan length.
- **Arriving from churn-prevention:** a confirmed cancellation recorded while a churn-prevention instance is open for the same subscription exits that instance and starts this one exactly once; churn-prevention's queued sends (a scheduled save offer included) are suppressed. A second `subscription_cancel` for the same subscription while this instance runs is ignored.
- **Exclude:** cancellations that end access immediately with nothing left to wind down (only the confirmation is sent, then straight to the outcome decision); involuntary terminations after failed payments (payment-failure owns those); account deletions and data-erasure requests (the erasure flow owns contact, and it may forbid any further message); enterprise accounts with a named account owner.
- **Success exit:** `subscription_expired` with the customer informed (completed), or `subscription_reactivated` (completed, the customer stayed) · **Window:** entry to `access_end_date` + 1 day.
- **Exit checks before each send:** for this subscription only (`same_instance`; reactivating subscription A does not end subscription B's wind-down): `subscription_reactivated`, `subscription_expired`, `subscription_resumed`, plus a fresh read of `access_end_date`. A moved end date (refund with immediate termination, a goodwill extension) is restated explicitly in the next send; it never shifts silently.
- **Re-entry:** each cancellation of a distinct subscription or term is its own instance (`each_trigger`). A duplicate cancel event for the same subscription while an instance is active (webhook retry, a second click) is ignored.
- **Permission withdrawn at cancellation is final.** If the customer opted out of marketing in the cancel flow or during the wind-down, that state is carried to win-back as withdrawn, and no re-permission request is sent to recover it. Service sends here still go, on channels where service contact is allowed.
- **Handoffs:**
  - `subscription_expired` → [winback](winback.md), `suppress_queued: true`, carrying `access_end_date`, `cancel_reason`, plan, and the consent state at cancellation. Win-back applies its own lapse threshold from the expiry date, never from the cancel click.
  - Pause variant, failed restart charge → [payment-failure](payment-failure.md), `suppress_queued: true`.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (2) | DQS < 40, or no event for reactivation | Confirmation with the end date + one ending notice. Outcome decision and handoff only if `subscription_expired` exists. |
| Standard (3) | DQS 40–69, `access_end_date` and `subscription_expired` present | Confirmation, ending notice with what survives, short heads-up the day before, runway decision, outcome decision, win-back handoff. |
| Branched (4) | DQS ≥ 70 + `data_export` + `data_retention_days` | Adds a data-retention notice where data is deleted some time after access ends, skipped for customers who already exported; runs the pause variant when the product offers pauses. |

Depth is bounded by the runway between cancellation and access end, not by DQS: a cancellation two days before the end of a monthly term gets the confirmation and nothing else.

## Step blueprint (standard, 3 sends)

| Node | When | Channel | Intent | Route |
|---|---|---|---|---|
| s1 | entry +15m | email | Confirmation (transactional): cancellation received, the exact date and time access ends, that paid access is not cut short, no further charges, and the one-step route to undo it. No offer, no survey push. In a short runway (below), it also carries the ending-notice facts. | → d1 |
| d1 | entry +15m | — | Decision on `access_end_date` (authoritative), evaluated at the decision moment (from = to = entry +15m): is the end date at least the minimum runway away (default 5 days)? | occurred → s2 · not_occurred → d2 · unmeasurable → d2 |
| s2 | access_end_date -3d at 10:00 user_local | email | Ending notice (service): the date restated, what survives and what doesn't (data, history, downloads, saved work; insurance: cover stops at the stated time), how to export, any outstanding balance as a fact with a link. One quiet line on how to stay. Deadline: access_end_date -1d; quiet hours move it earlier, never later. | → s3 |
| s3 | access_end_date -1d at 10:00 user_local | push (in_app if push not permitted, shown at the next session and expiring at access_end_date; skipped otherwise) | Heads-up (service): access ends tomorrow, pointing back to the ending notice. Deadline: access_end_date; quiet hours delay it at most to the last allowed time before that. Skipped when s2 went out less than 48 hours earlier. | → d2 |
| d2 | access_end_date +1d | — | Decision on `subscription_expired` (authoritative) between entry and access_end_date +1d | occurred → x1 · not_occurred → x2 · unmeasurable → x2 |
| x1 | access_end_date +1d | — | Exit `handoff` → winback, `suppress_queued: true`, carrying end date, cancel reason, plan and consent state at cancellation. | — |
| x2 | access_end_date +1d | — | Exit `completed` (neutral): access has not ended or the end can't be confirmed (moved date, billing lag). Reconcile; no win-back handoff until expiry is recorded. | — |

**Short-runway compression.** The runway is `access_end_date` minus entry, re-read from billing. No step is ever pushed past the next one or past the end date.

| Runway at entry | Sends | What changes |
|---|---|---|
| 30 days | s1, s2 (end -3d), s3 (end -1d) | Full path. |
| 11 days | s1, s2 (entry +8d), s3 (entry +10d) | Full path; s2 and s3 are still 48 hours apart. |
| 2 days | s1 only | d1 routes to d2: s2's facts (what survives, export, balance) merge into s1; s3 is dropped because a heads-up one day after the confirmation repeats it. |
| under 15 minutes / immediate end | s1 only | Confirmation states that access has ended; straight to the outcome decision. |

`subscription_reactivated` before any send exits as `completed` (good) through the exit check; it needs no node. The branched data-retention notice sits at `access_end_date +1d at 10:00 user_local` (email, service), only where `data_retention_days` says data will be deleted later, and only for customers without a `data_export`.

### Pause variant (standard, 2 sends)

| Node | When | Channel | Intent | Route |
|---|---|---|---|---|
| p1 | entry +15m | email | Pause confirmation (transactional): pause start, the resume date, what restarts on that date (billing amount, payment method), how to resume early, extend or cancel. | → p2 |
| p2 | resume_date -3d at 10:00 user_local | email (push as an added heads-up where permitted) | Resume reminder (service): the date, the amount, the payment method on file, the same change routes. The lead is configurable and is raised to any notice period the terms require. Deadline: the notice period before resume_date. A pause shorter than the lead merges this reminder into p1. | → pd1 |
| pd1 | resume_date +1d | — | Decision on `subscription_resumed` (authoritative) between entry and resume_date +1d | occurred → px1 · not_occurred → pd2 · unmeasurable → px3 |
| pd2 | resume_date +1d | — | Decision on `payment_failed` (authoritative) between resume_date -1d and resume_date +1d | occurred → px2 · not_occurred → px3 · unmeasurable → px3 |
| px1 | resume_date +1d | — | Exit `completed` (good): the subscription is running again; the billing receipt is the only follow-up. | — |
| px2 | resume_date +1d | — | Exit `handoff` → payment-failure, `suppress_queued: true`. | — |
| px3 | resume_date +1d | — | Exit `completed` (neutral): state unclear (extended, cancelled or not yet recorded); reconcile before anyone is told anything. | — |

`resume_date` is declared as a range relative to entry (`resume_date: entry +1d … +` the product's longest pause, in days) and re-read from billing before p2.

During a pause, every marketing journey for that subscription is suppressed (usage nudges, feature adoption, upsell, renewal reminders, churn-prevention). The only exceptions are things the customer asked for while pausing, such as staying on a release newsletter they chose in the pause flow. A cancellation during the pause exits the pause instance and starts the main path.

## Timing and channel fit

- **Clock:** the confirmation goes immediately after the cancellation (it answers an action the customer just took, so service-message timing applies, still outside the 00:00–06:00 email window where possible). The countdown sends use `user_local`; unknown timezone falls back to the market timezone. A pre-end send blocked by quiet hours moves earlier, never past the end date.
- **Quiet hours** per [consent-and-quiet-hours.md](../compliance/consent-and-quiet-hours.md): push 22:00–09:00. No SMS or WhatsApp by default: a cancellation is not urgent enough to justify them, and they read as pressure. Quiet hours are not code-checked; the export must say they need configuring in the sending tool.
- **Channel fit:** email carries the confirmation and the ending notice, because both hold facts the customer keeps and returns to. Push or in-app carries only the one-day heads-up. In-app suits products the customer still opens during the wind-down (streaming, apps), where a banner with the end date does more than a message.
- **Fallback:** confirmation and ending notice fall back to whatever service channel is permitted. The heads-up has no further fallback; it is skipped rather than repeating the email.

## Frequency and overlap

- **Worst path in any rolling 7 days:** s1 + s2 + s3 = 3 service sends, only when the end date falls about five days after the cancellation. The 48-hour rule between s2 and s3 drops s3 in short runways, so the usual worst case is 2.
- **Overlap:** renewal-reminder (a cancellation outranks a renewal reminder on the same subscription; renewal-reminder exits with its queue suppressed), churn-prevention, upsell-cross-sell, feature-adoption, trial-conversion, payment-failure, winback.
- **Precedence on the same subscription:** payment-failure (open) keeps owning any money owed; this journey states a balance as a fact and never chases it. Above every marketing journey for that subscription: from `subscription_cancel` to `subscription_expired`, marketing sends about that subscription are suppressed, queued ones included. Win-back cannot start before expiry; that boundary is the point of this pattern. Account-level messages about other active products the customer holds are not suppressed, but they must not mention the cancelled one.

## Measurement

- **Primary outcome:** surprise contacts, meaning `support_ticket_created` about lost access, plus refund or chargeback requests citing it, in the window from `access_end_date` -1d to `access_end_date` +7d, per 100 cancellations. Lower is better. Reactivations before the end date are recorded as a secondary outcome and never used as the target: optimizing this journey for reactivation turns it back into the save attempt it must not be.
- **Design: `none_service`.** Withholding the confirmation or the end date from a control is not acceptable. Alternative: pre/post comparison of the surprise-contact rate over equal-length periods before and after launch, with pricing and policy changes noted. The s3 heads-up alone can carry a component holdout if volume supports it; the confirmation and ending notice cannot.
- **Routine communications both groups keep:** billing-system cancellation receipts, mobile-store cancellation notices, final invoices, statutory insurance cancellation documents.
- **Contamination risks:** cancel-flow changes shipped in the same period (the flow itself sets expectations), support macros updated alongside, price changes driving a cancellation wave with a different mix of reasons.
- **Low volume:** a pre/post read can show a large drop in surprise contacts; it cannot attribute small changes, and it cannot measure whether the wind-down affects later win-back rates (that needs a much longer window and win-back's own holdout).

## When data is missing

- **`access_end_date` missing:** send only the confirmation, pointing to where the date is shown in the account. Flag the gap as a P0 tracking item. No countdown sends, because a countdown to a guessed date is worse than none.
- **`subscription_expired` missing:** the outcome decision falls to its unmeasurable route (x2) and no win-back handoff is made from this journey; win-back has to qualify the customer from its own lapse rule. Say so in the journey doc's data gaps.
- **`subscription_reactivated` missing:** a customer who withdrew the cancellation could still get the ending notice. Use the fresh read of subscription status before each send as a stand-in; if that read is unavailable too, drop s3 and keep only the confirmation and the ending notice.
- **`marketing_consent` at cancellation missing:** hand off with consent marked unknown; win-back treats unknown as not granted in opt-in markets.
- **`resume_date` missing (pause):** confirm the pause and say the resume date is shown in the account. No resume reminder until the date exists.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Surprise-contact rate around access end | primary | tickets, refund or chargeback requests citing lost access, per 100 cancellations |
| Confirmation delivery time | secondary | share of confirmations delivered within the configured target after the cancellation |
| Reactivation before end date | secondary | reported, never targeted |
| Complaints and opt-outs on wind-down sends | guardrail | a rise means the copy reads as pressure, which this journey must never apply |
| Pause restart success | secondary (pause) | `subscription_resumed` on the resume date without a payment failure |

## Common mistakes

- Turning the confirmation into a retention offer: the customer already said no, and a discount in the confirmation teaches everyone to cancel in order to get one.
- Cutting access the moment the cancel button is pressed on a prepaid term: the customer paid to the end date, and losing access early creates refund claims.
- Starting win-back on the cancel event: "come back" messages while the customer still has access read as confusion about whether they are a customer.
- Treating a marketing opt-out made in the cancel flow as a gap to close later: it was a decision, and a re-permission request ignores it.
- Letting other journeys carry on during a pause: usage nudges and upgrade offers to someone who asked for a break undo the trust the pause was meant to keep.
- Counting down to a computed end date: refunds, pro-rating and goodwill extensions move it, and a wrong date in a wind-down message produces exactly the surprise contact this journey exists to prevent.

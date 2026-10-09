---
name: renewal-reminder
stage: retention
trigger_type: time
required_events: [subscription_renewed]
optional_events: [subscription_cancel, subscription_expired, plan_changed, payment_failed, payment_succeeded, renewal_quote_issued, renewal_page_click, login]
required_attributes: [renewal_date, auto_renew]
optional_attributes: [renewal_price, notice_period_days, grace_period_days, plan_name, payment_method_type, quote_valid_until, product_line, delivered_value_summary]
default_channels: [email, push, sms]
base_steps: 3
depth_range: [2, 5]
applicable_industries: [insurance, saas, subscription-media, edtech, fintech, mobile-app]
mutually_exclusive_with: []
journey_class: service
signal_sources: {renewal_date: authoritative, auto_renew: authoritative, subscription_renewed: authoritative, subscription_cancel: authoritative, subscription_expired: authoritative, plan_changed: authoritative, payment_failed: authoritative, payment_succeeded: authoritative, renewal_quote_issued: authoritative, renewal_price: authoritative, quote_valid_until: authoritative, renewal_page_click: engagement, login: behavioral, delivered_value_summary: authoritative}
insufficient_alone:
  - a click on the renewal link or a visit to the renewal page
  - a renewal date computed from the start date plus an assumed term length
  - a renewal quote having been issued
  - a pending or authorized charge without a confirmed renewal
  - a reminder from this journey having been sent
exit_before_each_send: [subscription_renewed, subscription_cancel, plan_changed, payment_failed, subscription_expired]
reentry: {policy: each_trigger, on_duplicate_trigger: ignore}
measurement_default: none_service
instance_key: subscription_id
---

# Renewal Reminder

Count down to the date a term actually ends and make sure the customer knows, in time to act, what happens on that date. The defining split is the renewal model: an **auto-renewing** customer needs to be told that a charge is coming, for how much, on which payment method, and how to change it; a **manual-renewal** customer needs to be told that access or cover stops unless they act, and how to act. Sending both groups the same journey misinforms one of them every time. The deadline is always the real one, read from the system of record; this pattern never invents a renewal date, a price or a notice period to fill a gap.

**Journey class: service.** The notice a customer is owed before a term renews or ends (the date, the price, the change or cancel route) is an obligation of the relationship and, for auto-renewals and many insurance lines, of regulation. It is never rationed by marketing caps and never put in a holdout. Anything that persuades or sells at renewal (a delivered-value recap, an upgrade, an add-on cover, an annual-plan switch) is a separate node with `purpose: marketing`: consent-gated, counted against caps, holdout-eligible, and never merged into the notice. A notice with an upsell paragraph is a marketing message and loses its service standing, the same rule [consent-and-quiet-hours.md](../compliance/consent-and-quiet-hours.md) applies to payment-failure notices.

## Required-event signature

| Event | Source | Role |
|---|---|---|
| `renewal_date` *(attr)* | authoritative | The anchor every send counts down to: the policy expiry date, the subscription's next billing date, the contract term end. Read from billing, policy admin or contract records, re-read before each send. Without it the pattern is **blocked**. |
| `auto_renew` *(attr)* | authoritative | The branch key. Values `true` / `false`; anything else, or missing, takes the neutral route. |
| `subscription_renewed` | authoritative | Success exit: the new term exists. Insurance maps `policy_renewed`; mobile store billing maps its renewal notification. A charge alone is not a renewal until the billing system records the new term. |
| `subscription_cancel` *(optional)* | authoritative | Exit. An auto-renewal turned off or a cancellation recorded ends this journey; [cancellation-winddown](cancellation-winddown.md) owns the customer from there. |
| `subscription_expired` *(optional)* | authoritative | Confirms the term ended without renewal (insurance `policy_lapsed`). Without it, lapse is inferred from `renewal_date` passing with no `subscription_renewed`, and the outcome decision says so. |
| `plan_changed` *(optional)* | authoritative | Exit. A plan change usually moves the renewal date and price; the new term gets its own cycle instead of reminders quoting the old one. |
| `payment_failed` / `payment_succeeded` *(optional)* | authoritative | An open payment-recovery instance suppresses this journey. `payment_failed` at the renewal charge routes the instance to [payment-failure](payment-failure.md). |
| `renewal_quote_issued`, `renewal_price`, `quote_valid_until` *(optional)* | authoritative | Insurance and quote-based renewals: the price the notice may state, and the date until which that price holds. |
| `renewal_page_click` *(optional)* | engagement | Branched depth only: bot-filtered click on the renewal link. Shapes help, never ends the journey. |
| `delivered_value_summary` *(optional attr)* | authoritative | Claims paid, assistance used, hours streamed, invoices processed in the term. Feeds the marketing recap only when computed from the account's own records. |

### Not enough on its own

- **A click on the renewal link or a visit to the renewal page.** Interest, not a renewal. Exiting on it drops the final reminder for exactly the people who started and stalled.
- **A renewal date computed from the start date plus an assumed term length.** Mid-term changes, pro-rating, grace periods and backdated policies all break the arithmetic. A computed date may help find candidates; it may not appear in a message.
- **A renewal quote having been issued.** A quote is an offer with its own validity date; the policy is not renewed until it is accepted and bound.
- **A pending or authorized charge without a confirmed renewal.** Authorizations get reversed and retries fail. Thank-you copy waits for `subscription_renewed`.
- **A reminder from this journey having been sent.** A send is a communication, not a decision by the customer; it never advances the renewal state.

## Entry / exit

- **Entry:** a continuing subscription, policy or contract whose `renewal_date` is inside the lead window. Default lead 30 days, configurable; raised to the contractual or regulatory notice period when that is longer, and to the insurance playbook's 45-day pre-renewal start for insurance lines. Instance key: `subscription_id` (the policy or contract id where that is the entity), one instance per renewal cycle.
- **Time anchor:** most customers enter at the start of the lead window, but not all: a subscription bought or changed inside the window, a reopened cycle after payment recovery, or a lead raised to a longer notice period all shift the distance. A generated journey therefore declares `renewal_date` as a range relative to entry, `renewal_date: entry +1d … +45d` (upper end = the longest configured lead), and reads the real date from the system of record at every send. A runway under 24 hours gets no journey; the billing system's own renewal notice is all that lands in time.
- **Exclude:** an open payment-recovery instance on the same subscription (payment recovery owns the relationship until it resolves; a routine renewal note to someone whose current term is already in question reads as careless); a cancellation already recorded (cancellation-winddown owns it); terms that don't define the renewal model, the price or the notice period (route to a data/ops owner; nothing is sent on undefined terms); an open claim or escalated complaint for the marketing node only (the service notice still goes).
- **Success exit:** `subscription_renewed` for this cycle · **Window:** entry to `renewal_date` + grace (default 2 days for billing lag; the product's real grace period where one exists).
- **Exit checks before each send:** for this subscription only (`same_instance`): `subscription_renewed`, `subscription_cancel` (a confirmed cancellation or auto-renew turned off in billing, not a visit to the cancel page), `plan_changed`, `payment_failed`, `subscription_expired`, plus a fresh read of `renewal_date` and `auto_renew`. A changed date is restated in the next message, never silently moved; a flipped `auto_renew` re-routes at the next decision rather than sending the wrong branch's copy. The marketing node additionally re-checks marketing consent for its own channel (channel-scoped: an email marketing opt-out stops m1, never the service notices).
- **Re-entry:** one instance per renewal cycle (`each_trigger`, keyed on the cycle). A repeated trigger for the same cycle while an instance is active is ignored. A cycle closed by a payment-recovery handoff may open once more if `payment_succeeded` lands with at least the minimum runway left before `renewal_date` (default 7 days, configurable).
- **Handoffs:**
  - `payment_failed` at any point, including the renewal charge itself → [payment-failure](payment-failure.md), `suppress_queued: true`. This journey stops talking about money the moment a payment actually failed.
  - Term ends with no renewal, confirmed by `subscription_expired` or by the outcome decision → [winback](winback.md), `suppress_queued: true`, carrying `renewal_date`, `auto_renew`, product line and consent state. Win-back sets its own first-send timing; it does not inherit this journey's countdown.
  - Cancellation recorded mid-instance → [cancellation-winddown](cancellation-winddown.md), `suppress_queued: true`.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (2) | DQS < 40, or `auto_renew` not available | Neutral term-end notice + one reminder near the date. No branch; copy is true for both renewal models (the date, where to check renewal settings). |
| Standard (3 per path) | DQS 40–69, `auto_renew` populated | The auto/manual split, the outcome decision, and both handoffs. All sends are service. |
| Branched (4–5 per path) | DQS ≥ 70 + `renewal_price` / quote data + `renewal_page_click` | Adds the consent-gated marketing recap (real delivered value only), a quote-validity reminder for insurance, and a click-shaped help step for stalled manual renewers. |

Depth is bounded by the lead window, not by DQS: a monthly plan with a 7-day notice period cannot carry a 30-day cascade, and the engine shrinks the cascade to the reminders that still land before the date.

## Step blueprint (standard, 3 sends on the longest path)

| Node | When | Channel | Intent | Route |
|---|---|---|---|---|
| d1 | entry +0h | — | Decision on `auto_renew` (authoritative), evaluated at the decision moment (from = to = entry +0h) and re-read before every send | `true` → s1 · `false` → s3 · default → s6 · unmeasurable → s6 |
| s1 | renewal_date -30d at 10:00 user_local (entry +0h when that has passed) | email | Auto-renewal notice (service): renewal date, next-term price, plan, payment method on file, and how to change or turn off renewal. No offer. Deadline: renewal_date minus the notice period. | → s2 |
| s2 | renewal_date -7d at 10:00 user_local | push (email if push not permitted) | Approaching notice (service): date and amount, link to renewal settings. | → d2 |
| s3 | renewal_date -30d at 10:00 user_local (entry +0h when that has passed) | email | Renewal notice (service): the date access or cover ends, what ends with it, the renewing price and terms (insurance: the renewal quote and the date it is valid until), one link to renew. Deadline: renewal_date minus the notice period. | → s4 |
| s4 | renewal_date -7d at 10:00 user_local | push (email if push not permitted) | Reminder (service): days left until the real end date, link to renew. | → s5 |
| s5 | renewal_date -1d at 11:00 user_local | sms (push, then email if SMS not permitted) | Final reminder (service): the date, plainly; what lapses (insurance: cover stops at the policy end time). Deadline: renewal_date; quiet hours move it earlier, at most to the last allowed time before the deadline. | → d2 |
| s6 | renewal_date -30d at 10:00 user_local (entry +0h when that has passed) | email | Neutral term-end notice (service): the date and where to see whether this plan renews automatically. No claim either way. | → s7 |
| s7 | renewal_date -3d at 10:00 user_local | email | Neutral reminder (service): the date restated, same link. Deadline: renewal_date. | → d2 |
| d2 | renewal_date +2d | — | Decision on `subscription_renewed` (authoritative) between entry and renewal_date +2d | occurred → x1 · not_occurred → d3 · unmeasurable → x4 |
| d3 | renewal_date +2d | — | Decision on `payment_failed` (authoritative) between renewal_date -3d and renewal_date +2d | occurred → x2 · not_occurred → x3 · unmeasurable → x4 |
| x1 | renewal_date +2d | — | Exit `converted` (good). The billing system's renewal receipt is the only follow-up; this journey adds nothing. | — |
| x2 | renewal_date +2d | — | Exit `handoff` → payment-failure, `suppress_queued: true`. | — |
| x3 | renewal_date +2d | — | Exit `handoff` → winback, `suppress_queued: true`, carrying lapse date, renewal model, product line and consent state. | — |
| x4 | renewal_date +2d | — | Exit `completed` (neutral): outcome unknown, reconcile with billing before anyone is told they lapsed. No win-back handoff on an unknown outcome. | — |

**Short-runway compression.** The first notice of each branch (s1, s3, s6) goes at the lead point or at entry, whichever is later. A step whose anchor has already passed at entry is dropped, never sent late, and no step moves past the next one or past `renewal_date`. When two sends would land less than 48 hours apart, the earlier discretionary one is dropped; the owed first notice is never dropped.

| Runway at entry | Sends (auto · manual · neutral) | Dropped or merged |
|---|---|---|
| 30 days | s1 -30d, s2 -7d · s3 -30d, s4 -7d, s5 -1d · s6 -30d, s7 -3d | nothing |
| 11 days | s1 at entry, s2 -7d · s3 at entry, s4 -7d, s5 -1d · s6 at entry, s7 -3d | first notices move to entry |
| 2 days | s1 at entry · s3 at entry · s6 at entry | s2, s4, s7 dropped (anchors passed); s5 would land within 48 hours of s3, so s3 carries the final-reminder wording and s5 is dropped |

Every `-30d` above stands for the configured lead window (default 30 days; the notice period where that is longer; 45 days for insurance per the playbook). The `+2d` outcome point stands for the grace period (default 2 days of billing lag; the product's real grace window where one exists). Both are read per instance, never hard-coded.

Branched additions, each with its own anchor in a generated journey:
- **m1** at `renewal_date -21d at 10:00 user_local`, email, `purpose: marketing`: delivered-value recap computed from the account's own records (claims paid, assistance used, content consumed). Skipped without marketing consent, without the data, or for an account with an open claim or complaint. Never estimated.
- **q1** for insurance quote-based renewals at `quote_valid_until -3d at 10:00 user_local`, email, service: the renewal price holds until this date; after it the premium may be re-quoted. Sent only when the quote expires before the policy does. The two dates are never merged into one deadline.
- **d4** after s3: Decision on `renewal_page_click` (engagement, bot-filtered) between s3 +0h and renewal_date -7d: occurred → in-app step at `d4 +0h` offering the saved quote and a help route (shown at the next session, expires after 5d or at renewal_date, whichever is first), then s4 · not_occurred → s4 · unmeasurable → s4. s4 keeps its own anchor and is never gated on the in-app view. A click never exits the journey and never counts as a renewal.

## Timing and channel fit

- **Clock:** sends count down on the user's local clock (`user_local`); unknown timezone falls back to the market timezone from intake. A deadline send that lands in quiet hours moves **earlier**, never later: a reminder delivered after the date has passed is not a reminder.
- **Quiet hours** per [consent-and-quiet-hours.md](../compliance/consent-and-quiet-hours.md): push 22:00–09:00, SMS/WhatsApp 20:00–10:00 and no Sundays (an `s5` that would fall on a Sunday goes on Saturday). Quiet hours are not code-checked; the export must state that the window has to be configured in the sending tool.
- **Channel fit:** email carries the notices with terms, prices and dates the customer needs to keep (s1, s3, s6, q1). Push carries the short pre-deadline reminders where push permission exists. SMS or WhatsApp carries only the final reminder, where the operator holds permission for service messages on that route; insurance markets where renewal conversations run on WhatsApp can swap s5 to it.
- **Fallback:** a service notice falls back to email when its preferred channel isn't permitted. The marketing node has no fallback: no consent on its channel, no send.

## Frequency and overlap

- **Worst path in any rolling 7 days:** manual branch, s4 + s5 = 2 sends (both service). Branched adds at most q1 in the same window (3 service sends). The marketing recap m1 sits outside the last week and counts against marketing caps.
- **Service sends are exempt from marketing caps** but are deduplicated against other service messages about the same subscription: if a billing or policy-document notice with the same date and price goes out within 24 hours, skip the discretionary reminder (s2, s4, s7), never the first notice.
- **Usual overlaps:** payment-failure, cancellation-winddown, churn-prevention (insurance repurposes it as pre-renewal retention against the same `renewal_date`), upsell-cross-sell, anniversary.
- **Precedence on the same subscription:** payment-failure (open) > cancellation-winddown > renewal-reminder > churn-prevention / upsell-cross-sell / anniversary. A lower journey defers its sends inside this journey's last 7 days; a higher one suppresses this journey's queued sends at handoff. Where churn-prevention runs as an insurance pre-renewal program, the owner chooses at portfolio level whether it supplies the marketing layer (and this pattern drops m1) or this pattern replaces it; both must not count down to the same date with their own copy.

## Measurement

- **Primary outcome:** `subscription_renewed` for the cycle, window entry to `renewal_date` + grace. Track the auto-renewal path (renewed vs turned off vs failed charge) and the manual path (renewed before the date vs lapsed) separately; their base rates are not comparable.
- **Design: `none_service`.** The owed notices (s1, s3, s6, and the final reminder where terms or regulation require it) are never withheld from a control. Alternative: a component holdout on the discretionary sends only (s2, s4, s7, m1), consistent by account; the control still receives the owed notices. Where volume can't support that, a pre/post read on manual-renewal rate by monthly cohort, with price changes at renewal recorded as a confounder.
- **Routine communications both groups keep:** billing-system receipts and invoices, statutory policy documents, store-issued renewal notices for mobile-store-billed subscriptions, agent or broker renewal calls.
- **Contamination risks:** agents, brokers and call centers working the same renewal list; price changes at renewal (a re-rated premium moves renewal rates more than any message); comparison-shopping seasons in insurance; another journey's offer landing in the same window.
- **Low volume:** annual terms make each month's cohort small. A discretionary-step holdout can detect only large differences in manual-renewal rate; it cannot show the effect of the owed notice (which has no control) or separate copy effects from price effects. Report it as directional.

## When data is missing

- **`renewal_date` missing or only computable:** the pattern is blocked for messaging. Hand the gap to tracking (P0 item); do not send a date the system of record doesn't hold.
- **`auto_renew` missing or unexpected value:** the neutral route (s6, s7). Its copy is true for both models. Flag the gap; it is the cheapest attribute to add and doubles the pattern's value.
- **Renewal price not yet issued** (common for insurance, where the renewal quote is generated close to expiry): s3 states the date and that the renewal offer will follow; the price-bearing notice waits for `renewal_quote_issued`, re-anchored to the quote, still before the date. Never state last term's price as next term's.
- **`subscription_renewed` delayed** (batch billing feeds): the outcome decision at `+2d` absorbs normal lag; when the feed is known to run later, widen the grace window rather than let d2 read a late renewal as a lapse.
- **Outcome unmeasurable:** x4, a neutral exit with reconciliation. Not a lapse, not a win-back audience, not a suppression.
- **`delivered_value_summary` missing:** m1 is skipped. No estimates, no "customers like you" substitutes.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Renewal rate by renewal model | primary | `subscription_renewed` within the window / cycles entered, auto and manual reported separately |
| Notice delivery coverage | secondary | share of cycles where the owed notice was delivered before the notice deadline; below 100% is a compliance gap, not a performance dip |
| Auto-renewal disputes and refund requests after the charge | guardrail | rising numbers mean the notice is unclear or late, not that customers are fickle |
| Complaints and opt-outs on the final reminder | guardrail | the SMS/WhatsApp step is the one that burns trust if overused |

## Common mistakes

- One journey for auto and manual renewers: auto-renewers are told to "renew now" and pay twice or ring support; manual renewers are told nothing will change and lapse.
- Counting down to a computed date: start date plus twelve months drifts after any mid-term change, and a reminder for the wrong date is worse than none.
- Putting an upgrade pitch in the renewal notice: the message becomes marketing, needs marketing consent, and the customers without it never receive the notice they were owed.
- Running the renewal cascade while a payment recovery is open: the customer gets "your plan renews on the 14th" next to "your payment failed" and trusts neither.
- Extending reminders past the date: once the term has ended, the conversation belongs to win-back, with its own timing and consent check, not to reminder number six.
- Conflating quote validity and policy expiry in insurance: they are two dates, and telling a customer their cover ends when only the quoted price does is a misstatement.

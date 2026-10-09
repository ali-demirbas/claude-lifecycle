---
name: winback
stage: winback
trigger_type: segment
journey_class: marketing
required_events: [purchase, session_start]
optional_events: [subscription_cancel, subscription_expired, refund, login, add_to_cart, link_click, hard_bounce]
required_attributes: []
optional_attributes: [median_interpurchase_gap, ltv_tier, last_category, consent_age, cancel_reason, access_end_date, incentive_ledger]
default_channels: [email]
base_steps: 4
depth_range: [3, 6]
applicable_industries: [ecommerce, marketplace, saas, subscription-media, travel, fintech, insurance, edtech, mobile-app]
mutually_exclusive_with: [churn-prevention]
signal_sources: {purchase: authoritative, session_start: behavioral, subscription_cancel: authoritative, subscription_expired: authoritative, refund: authoritative, link_click: engagement, hard_bounce: authoritative, cancel_reason: authoritative, access_end_date: authoritative, incentive_ledger: authoritative, median_interpurchase_gap: inferred, ltv_tier: inferred, consent_age: authoritative}
insufficient_alone:
  - days since last purchase against one fixed global number
  - a cancellation request while paid access is still running
  - email opens
  - a browsing session without a purchase
  - no click on a delivered email, as a reason to switch to SMS
exit_before_each_send: [purchase, consent_withdrawn, refund]
reentry: {policy: after_cooldown, cooldown: P90D, on_duplicate_trigger: ignore}
measurement_default: holdout
---

# Winback

Recover **lapsed customers**: users who generated revenue and have since gone quiet past a recency threshold. The threshold is not a fixed number of days: it is computed per business (ideally per category) from the median inter-purchase or inter-usage gap, so a weekly-grocery lapse and an annual-travel lapse are detected on their own clocks. Distinct from [reactivation](reactivation.md), which targets dormant users who never bought.

## Required-event signature

| Event | Source | Role |
|---|---|---|
| `purchase` | authoritative | Qualifies the audience (≥ 1 historical purchase) and is the success exit. History of timestamps also feeds the inter-purchase gap math. Without it, pattern is **blocked**. |
| `session_start` | behavioral | Recency source: distinguishes "lapsed but still visiting" (product problem) from fully silent (attention problem). |
| `subscription_cancel` / `subscription_expired` *(optional)* | authoritative | Marks deliberate leavers; they need a changed-value message, not a "we miss you". `subscription_expired` (or `access_end_date`) is the moment a subscriber becomes eligible. |
| `refund` *(optional)* | authoritative | Exclusion signal: refund-heavy lapsers are often lost for cause; win them back with service, not promos. |
| `cancel_reason` *(optional attr)* | authoritative | Sets the starting angle and enforces the do-not-contact reason list. |
| `incentive_ledger` *(optional attr)* | authoritative | Per-person record of every comeback incentive already issued. |
| `link_click` *(optional)* | engagement | Bot-filtered click; the only message-engagement signal the blueprint may branch on. |
| `median_interpurchase_gap` *(optional attr)* | inferred | Precomputed per user/category; enables per-user thresholds instead of one global clock. |

### Not enough on its own

- **Days since last purchase against one fixed global number.** A consumable and an annual purchase lapse on clocks an order of magnitude apart; a lapse is defined against the business's own gap distribution (see the threshold rules below).
- **A cancellation request while paid access is still running.** Until access actually ends, the person is still a customer: that period belongs to [cancellation-winddown](cancellation-winddown.md) (and, before the cancellation is confirmed, [churn-prevention](churn-prevention.md)'s cancel-intent save branch), not to a comeback campaign.
- **Email opens.** Privacy proxies and image blocking make them unreliable; nothing in this journey branches on them.
- **A browsing session without a purchase.** It shows the person is reachable and interested, which is useful for routing, but it is not a win and does not exit the journey.
- **No click on a delivered email, as a reason to switch to SMS.** Not reached is not not-engaged. A generic comeback message stays on email; SMS needs both evidence that email is not being delivered (`hard_bounce` or a delivery failure on this address) and a message the SMS suitability table in [sms.md](../channels/sms.md) accepts on its own merits, which a generic winback is not.

## Entry / exit

- **Entry:** ≥ 1 lifetime `purchase`, no `purchase` and no `session_start` for longer than the lapse threshold (default 2× median inter-purchase gap, floor 45 days; **T2-aggregate, where the median gap is uncomputable without per-user order history: use the playbook `churn_signal` default and mark it as an assumption in the journey doc**; this is the engine's rule, not a per-run judgment call), valid marketing consent. For subscriptions, entry starts only once paid access has actually ended (`subscription_expired` or `access_end_date` in the past), never at the cancel click. Entrants arrive via a handoff (the churn-prevention watch buffer, [cancellation-winddown](cancellation-winddown.md) or [renewal-reminder](renewal-reminder.md) on `subscription_expired`, each carrying the end date, cancel reason and consent state at cancellation) or via direct lapse detection; never run winback and churn-prevention on the same user in the same window.
  - **Threshold refinement, percentile over multiplier when the data supports it:** 2×-median is a reasonable single number, but inter-purchase-gap distributions are usually right-skewed, so one flat multiplier can misjudge both ends of the base: too early for a slower-but-loyal segment, too late for a fast-repeat one. Where a category has enough per-user history (a reasonable floor: ≥ 30 purchasers in the category), rank each user's current gap against that category's own observed gap distribution and use a percentile cutoff (e.g., the 75th–80th percentile) instead of a fixed multiplier. This adapts to the distribution's actual shape, not just its center (the same idea as RFM "dynamic quintile scoring" applied to one axis). Below that data floor, a percentile estimate is noise wearing a formula: fall back to 2×-median + the 45-day floor. This is what "per-user gap" means in the Branched depth row below; record which method computed the threshold in the journey doc's assumption notes.
- **Exclude:**
  - refund or dispute open;
  - consent older than ~2 years of silence: those users get a re-permission message first, not a promo blast (see [consent-and-quiet-hours.md](../compliance/consent-and-quiet-hours.md), journey-level rule 2);
  - cancellation reasons on the do-not-contact list. The list is configuration owned by the business; a sensible default covers business closed, bereavement and relocation out of the service area. A person who left for one of these reasons gets no comeback message at all;
  - anyone who withdrew marketing permission during cancellation. That withdrawal is final for this journey: no re-permission ask, no "one last offer";
  - users under the portfolio negative-signal override.
- **Success exit:** `purchase` (a resubscription counts) · **Window:** 30 days.
- **Checked before each send:** `purchase`, `refund`, `consent_withdrawn` (channel-scoped: an email opt-out stops the email steps and is never a reason to move the same message to another channel).
- **Re-entry:** after a 90-day cooldown, max 2 lifetime winback cycles; a repeated trigger while an instance is open is ignored. After the second cycle, the person moves to [unengaged-sunset](unengaged-sunset.md) rather than a third campaign.
- **Incentive ledger:** every comeback incentive is written to a per-person record when issued (type, value, date). An incentive already in the ledger is never re-issued in a later cycle; that cycle's s4 becomes a value message instead.
- **Handoffs:** a purchase hands the customer to [post-purchase](post-purchase.md); queued winback sends are suppressed.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (3) | DQS < 40 or only required events | What's-new email → value reminder → single approved incentive. Email only, global threshold. |
| Standard (4–5) | DQS 40–69 | Adds a second-angle email for people with no measurable return and `last_category` personalization; incentive gated on `ltv_tier`. |
| Branched (6) | DQS ≥ 70 + `subscription_cancel` or per-user gap | Splits deliberate cancellers (changed-value track) from passive lapsers (reminder track); per-user lapse clocks. |

In the branched shape, a known lapse reason sets the starting angle: where a cancellation-flow reason or a one-tap "why did you leave?" answer exists (and is not on the do-not-contact list), start the sequence at the matching angle: price objection → the (policy-approved) incentive/down-sell step; missing feature → what's-new focused on that feature; competitive loss → differentiation and social proof. No signal → default order.

## Step blueprint (standard, 4 sends)

| Node | When | Channel | Intent | Route |
|---|---|---|---|---|
| s1 | entry +0h at 10:00 user_local | email | "Here's what changed since you left": concrete product/catalog news, no discount | → s2 |
| s2 | s1 +5d | email | Personalized best-of tied to `last_category`; restate the original value proposition | → d1 |
| d1 | s2 +7d | — | Decision on any_of(`link_click` from s1/s2 (engagement, bot-filtered), `session_start` (behavioral)) between entry and s2 +7d | occurred → s4 · not_occurred → s3 · unmeasurable → s4 |
| s3 | d1 +0h | email | Short, direct value reminder from a different angle (the lapse reason where known, otherwise the strongest remembered benefit), one link | → s4 |
| s4 | s2 +17d | email | Incentive, gated on `ltv_tier` and margin, checked against the incentive ledger, flagged for user approval before launch; recorded in the ledger when sent | → exit (expired) at entry +30d |

`d1` replaces the old open-based condition: people who clicked or came back to browse skip the second-angle email; people with no measurable sign get it, still by email. Silence on a delivered email does not justify a costlier or more intrusive channel: the generic winback is an email journey, and [sms.md](../channels/sms.md) lists generic winback as unsuitable for SMS.

**SMS exception (narrow):** an SMS step is allowed only when both hold: there is evidence email is not delivered to this person (`hard_bounce` or repeated delivery failure on s1/s2, authoritative), and the message is genuinely time-sensitive and valuable by the SMS table's own test (for example a wishlisted item back in stock or a tracked price drop expiring today, usually owned by [back-in-stock](back-in-stock.md) or [price-drop](price-drop.md)). A value reminder or a comeback incentive does not qualify.

## Timing and channel fit

- **Email** carries the substance (what changed, best-of, incentive terms): content a lapsed customer reads at their own pace. Avoid 00:00–06:00 user local.
- **SMS** is not a winback channel by default. The narrow exception above needs non-delivery evidence plus a message the SMS table accepts, SMS marketing consent, and the SMS quiet hours (20:00–10:00 user local, no Sundays by default).
- **Fallback:** no email consent → WhatsApp versions of s1 and s4 where the person opted in there (the SMS table's alternative for this content); otherwise the person is not eligible. A generic winback is not moved to SMS because email consent is missing or email went unclicked.
- Subscription entrants: s1 never lands before `access_end_date`; the first message after access ends is about what is new, not a reminder of the cancellation.

## Frequency and overlap

- **Worst path:** 2 sends in any rolling 7 days (s1 + s2 in week one; s3 and s4 are 10 days apart).
- **Usually overlaps with:** [churn-prevention](churn-prevention.md) (mutually exclusive), [reactivation](reactivation.md) (audiences separated by lifetime purchase), [price-drop](price-drop.md), [back-in-stock](back-in-stock.md), general broadcast campaigns.
- **Precedence:** a triggered alert the person asked for (back-in-stock, price-drop) may go out and defers the next winback send by 2 days. Broadcast promotions are suppressed for winback entrants while an instance is open, so the incentive step is not undercut by a bigger generic code.

## Measurement

- **Primary outcome:** `purchase` within 30 days (extend to 60–90 days for long-cycle businesses, matched to the purchase cycle).
- **Design:** holdout (default 10%), user-level, consistent assignment across cycles. The control receives none of s1–s4, including the incentive.
- **Routine communications both groups keep:** transactional messages, account notices, and any general newsletter the lapsed base already received before the journey existed (state which).
- **Contamination risks:** paid retargeting audiences built from the same lapsed list; generic promo codes in broadcasts; incentive codes shared on coupon sites.
- **Low volume:** winback rates are low, so detecting a lift needs a large lapsed base. When the power calculation shows the control arm can't detect a plausible lift, report the winback rate as unmeasured lift and use pre/post on monthly reactivated-customer counts only as a description.

## When data is missing

- **No per-user order history:** global threshold from the playbook `churn_signal` default, marked as an assumption.
- **No `cancel_reason`:** no do-not-contact filtering is possible, so the pattern says so in the journey doc and the default angle order applies; recommend capturing the reason in the cancellation flow.
- **No `access_end_date`:** subscription entrants are held until the last billed period's end can be inferred from billing data; never entered on the cancel event.
- **No incentive ledger:** the incentive step becomes once-per-lifetime by policy and is approved manually each cycle.
- **Click tracking off or not bot-filtered:** `d1` reads `session_start` alone; if neither is measurable, the unmeasurable route skips the second-angle email and goes to s4.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Winback rate | primary | purchases within window / journeys entered, compared with the holdout |
| Revenue per re-activated customer | secondary | compare against pre-lapse run rate, not against zero |
| Hard bounce + spam-complaint rate | guardrail | stale lists damage domain reputation for every other journey; this guardrail protects the whole portfolio |

## Common mistakes

- Using one fixed threshold (e.g. "90 days inactive") for every product: consumables and annual-cycle purchases lapse on clocks an order of magnitude apart; compute from the median gap.
- Leading with the deepest discount: it trains lapse-for-coupon behavior and anchors returning customers at the discounted price.
- Re-issuing the same comeback incentive every cycle: without a per-person ledger, the incentive becomes a subscription price.
- Starting the campaign at the cancel click while the customer still has paid access.
- Messaging people whose cancellation reason was bereavement, closure or relocation.
- Blasting multi-year-silent contacts: deliverability and İYS/GDPR risk; long-dormant segments get a re-permission step, not a campaign.

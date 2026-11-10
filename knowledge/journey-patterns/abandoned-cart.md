---
name: abandoned-cart
stage: revenue
trigger_type: event
required_events: [add_to_cart, purchase]
optional_events: [begin_checkout, view_cart, payment_failed, consent_withdrawn, cart_cleared]
required_attributes: []
optional_attributes: [cart_value, cart_items, cart_id, item_availability]
default_channels: [email, push]
base_steps: 4
depth_range: [3, 8]
applicable_industries: [ecommerce, marketplace, travel, insurance, edtech]
mutually_exclusive_with: []
journey_class: marketing
signal_sources:
  add_to_cart: behavioral
  purchase: authoritative
  begin_checkout: behavioral
  view_cart: behavioral
  payment_failed: authoritative
  cart_value: authoritative
  item_availability: authoritative
  consent_withdrawn: authoritative
  cart_cleared: authoritative
  link_click: engagement
insufficient_alone:
  - add_to_cart from a session that never resolved to a contactable person
  - a click on a cart message
  - a client-side cart event that the server-side cart record contradicts
exit_before_each_send: [purchase, consent_withdrawn, cart_cleared, payment_failed]
reentry: {policy: after_cooldown, cooldown: P7D, on_duplicate_trigger: restart}
instance_key: cart_id
measurement_default: holdout
---

# Abandoned Cart

Recover people who put items in a cart and did not buy. Consistently the highest-ROI journey in commerce: intent is proven and the ask is small. One instance follows one cart; a newer cart takes over from an older one.

## Required-event signature

| Event | Source | Role |
|---|---|---|
| `add_to_cart` | behavioral (authoritative when read from a server-side cart record) | Trigger. The journey arms when the cart becomes non-empty. |
| `purchase` | authoritative | Success exit, re-checked before every send. Without it, recovery cannot be measured and the pattern is **blocked**. |
| `begin_checkout` *(optional)* | behavioral | Enables a higher-intent branch: checkout abandoners get a shorter, more direct sequence. |
| `view_cart` *(optional)* | behavioral | Return-to-cart signal for branching and better abandonment timing. |
| `payment_failed` *(optional)* | authoritative | A failed payment during checkout is not abandonment; it hands the instance to [payment-failure](payment-failure.md). |
| `cart_value` *(optional attr)* | authoritative | Enables value-based branching (a high-value cart may justify an incentive step). It never justifies a costlier channel on its own. |
| `item_availability` *(optional attr)* | authoritative | Read before each send: only items that can still be bought are shown. |

### Not enough on its own

- **`add_to_cart` from an unresolved session:** a cart with no identity behind it cannot be messaged and must not be guessed onto a profile by device or cookie alone.
- **A click on a cart message:** engagement evidence that the reminder was seen; it never stands in for a purchase or a checkout start, and it never moves the instance to a success state.
- **A client-side cart event the server-side cart contradicts:** analytics events fire on page loads and retries; where a cart record exists, it wins.

## Entry / exit

- **Entry:** `add_to_cart` fired, no `purchase` within the arming window (default 1h, configurable; shorten only with evidence that buyers who return later than that are rare), the person is messageable on ≥ 1 channel, at least one item in the cart can currently be bought.
- **Exclude:** purchased in the last 24h, currently in a P0 transactional flow, cart value below the minimum (if known), any open complaint or escalated ticket (portfolio-wide negative-signal override in [consent-and-quiet-hours.md](../compliance/consent-and-quiet-hours.md)).
- **Success exit:** `purchase` (any, identity-stitched across devices where possible) · **Window:** 7 days.
- **Checked before each send:** `purchase` (any order by this person ends the instance), `consent_withdrawn` scoped to that send's channel (an email unsubscribe stops the email steps; push steps continue where push is consented), `cart_cleared` and `payment_failed` **for this cart** (`instance_key: cart_id`), and the live state of the cart's items. Adding or removing items in the same cart is not a new trigger; it changes what the next send shows, because content is read at send time.
- **Re-entry:** after a 7-day cooldown. A new cart filled inside the cooldown after a finished or suppressed instance is tracked and sends nothing.
- **Repeated trigger while active:** a newer cart (a new cart id, or a cart refilled after being emptied) supersedes the open instance. The instance restarts on the new cart, and every send still queued against the old one is dropped rather than carried forward.
- **Handoffs:**
  - `payment_failed` on the checkout → [payment-failure](payment-failure.md); queued cart sends suppressed. Cart-recovery copy and payment-recovery copy never run at the same time for the same failed payment.
  - Every item in the cart unavailable at a send check → [back-in-stock](back-in-stock.md) for those items, one instance per item; queued cart sends suppressed. A reminder about a cart nothing in which can be bought is never sent.
  - From [browse-abandonment](browse-abandonment.md): an `add_to_cart` there hands the person here, and browse's queued sends are suppressed.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (3) | DQS < 40 or only required events | Reminder → value nudge → last call. Single channel, time-anchored waits, no decisions. |
| Standard (4–6) | DQS 40–69 | Adds a second channel and one or two decisions on return-to-cart or a bot-filtered click. |
| Branched (7–8) | DQS ≥ 70 + `begin_checkout` or `cart_value` | Splits checkout abandoners from cart abandoners; optional incentive branch gated on cart value and margin. |

## Step blueprint (standard, 4 sends)

| Node | When | Channel | Intent | Route |
|---|---|---|---|---|
| s1 | entry +1h | email | Reminder: cart contents as they stand now, zero pressure | → d1 |
| d1 | s1 +20h | — | Decision on any_of(`view_cart` for this cart (behavioral), link_click on s1 (engagement, bot-filtered)) between s1 and s1 +20h | occurred → s3 · not_occurred → s2 · unmeasurable → s2 |
| s2 | s1 +20h | push | Short nudge, deeplink straight into the cart | → s3 |
| s3 | s1 +44h | email | Objection handling: shipping, returns, payment options, trust | → d2 |
| d2 | s3 +24h | — | Decision on any_of(`view_cart` for this cart (behavioral), link_click on s3 (engagement, bot-filtered)) between s3 and s3 +24h | occurred → s4 · not_occurred → end · unmeasurable → end |
| s4 | s3 +24h | email | Social proof on the cart's items, for someone who came back and still didn't buy; name a real cart expiry only if the system holds one, never invented urgency | → end |

Longest path s1 → s2 → s3 → s4 lands on about day 3 of the 7-day window. There is no late push: [push.md](../channels/push.md) accepts a cart push only while the intent is recent (under 24h), and someone who hasn't come back by d2 isn't chased further on any channel. any_of reads as occurred when either member occurred, not_occurred only when both were measured and neither occurred, unmeasurable otherwise (for example click tracking off and no `view_cart`).

Incentive rule: never lead with a discount. If an incentive step exists at all, it is the **last** send, gated on cart value and margin, issued once per person and recorded, and flagged for the user to approve. Incentive choice follows the CLV-tied rule: above the account's CLV threshold prefer a value-add over a discount; below it, a capped modest discount (see intake incentive policy).

Send-time staleness rule: any message referencing a live price or stock value (cart contents, item price, availability) must either pull live data at send time via the CRM's live-content mechanism or re-verify the trigger condition at send. A design-time value baked into copy goes stale, and a wrong price or stock claim is a trust-killer. Nothing is claimed that the system does not hold: no reserved stock, no held price, no expiry.

Honest low-stock urgency: where a live `inventory_level` exists for a cart item, the last call may state real scarcity ("2 left") under the same rule as [back-in-stock](back-in-stock.md). Never claim scarcity without the data, and re-check the level at send time.

## Timing and channel fit

- **Clock:** user local time; unknown timezone falls back to the market timezone from intake. A push that would land in 22:00–09:00 is skipped when it would otherwise go out more than 24h after `add_to_cart` (push.md's recency test); when it still fits, it is released staggered inside 09:00–11:00, never as a 09:00 burst. Email avoids 00:00–06:00. If a send would land in quiet hours, the following sends keep their anchors to the actual send time of the node they reference, so spacing is preserved.
- **Channel fit:** email carries the cart's contents and survives until the person returns, so it holds the reminder and objection steps. Push is a short re-entry deeplink; its reason is [push.md](../channels/push.md)'s recency test for an abandoned cart, which s2 meets (about 21h after entry), not the missing click on s1. SMS is not used: [sms.md](../channels/sms.md)'s suitability table rejects abandoned cart, and a cart that went unclicked is not a reason to escalate (not reached is not not-engaged). WhatsApp may **replace** push as the carrier of s2 for a person who opted in to WhatsApp in a market where it is the highest-attention channel ([whatsapp.md](../channels/whatsapp.md), first row); it is chosen per person up front, never added after a missing click, and cart value alone does not qualify anyone.
- **Fallback:** a push step for someone without push consent or a valid token is skipped, not moved to SMS; an email step for someone without email consent moves to push only when push is consented. A channel that fails reachability is skipped and the skip is recorded.

## Frequency and overlap

- **Worst path, rolling 7 days:** 3 emails + 1 push = 4 marketing sends, within the default caps (email 4, push 5, all channels 8) on its own. Combined with an active welcome series it can breach the email cap; the portfolio conflict review must count both.
- **Overlaps:** browse-abandonment (cart wins), back-in-stock and price-drop on the same items (cart wins; their send for an item in the cart is folded into the cart's next send or skipped), welcome/onboarding for new sign-ups, payment-failure (payment-failure always wins).
- **Precedence:** payment-failure and any service/complaint path outrank this journey; this journey outranks browse-abandonment, back-in-stock, price-drop and replenishment for the same items. On a cap breach, cart sends defer (re-evaluated against current cart state when released), they are not queued blindly.

## Measurement

- **Primary outcome:** `purchase` within 7 days of entry (whole-week window per [measurement.md](../measurement.md)).
- **Design:** journey-level holdout, default 10%, randomized at entry and sticky per person for the measurement period. The control receives none of this journey's sends on any channel.
- **Routine communications both groups keep:** transactional order and payment messages, and any existing cart emails the platform sends outside this journey; list them so they're not mistaken for treatment.
- **Contamination:** a held-out cart that receives a browse-abandonment, back-in-stock or price-drop send about the same items is contaminated; those journeys must respect the holdout for the cart's items during the window.
- **Low volume:** when the power calculation shows a read can't detect a plausible lift, pool a longer window or accept the result as inconclusive. A small store can confirm the journey isn't harmful (unsubscribes, complaints) long before it can size the lift.

## When data is missing

- **No `begin_checkout`:** run the standard shape for everyone; no checkout-abandoner track.
- **No `view_cart` and no click tracking:** both decisions resolve as unmeasurable, which follows the not_occurred route; the path is longer but never treats missing data as disinterest.
- **No server-side cart or availability data:** content can't be checked live, so drop item-specific price/stock claims from copy and show only a link back to the cart; note the gap in the journey doc.
- **`purchase` delayed** (batch import, offline orders): delay sends by at least the known lag, or the journey will chase people who already bought.
- **No `payment_failed` signal:** the payment-failure handoff can't fire; flag it as a data gap, since recovery copy may land on someone fighting a declined card.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Incremental cart recovery rate | primary | purchases within window, exposed vs holdout |
| Revenue per entrant | secondary | |
| Unsubscribe rate per send | guardrail | ceiling from channel rules |

## Common mistakes

- Firing at +5 minutes; the person may still be shopping. Minimum arming window 30–60 min.
- Discounting in the first send; it trains cart-abandonment behavior.
- Not excluding purchasers across devices; require an identity-stitched `purchase` exit if available.
- Branching on an email open. Opens are inflated by privacy proxies and blocked by others; use return-to-cart or a bot-filtered click.
- Letting an old cart's queued reminders fire after the person built a new cart; the newer cart supersedes.
- Sending cart reminders while a payment is failing; that instance belongs to payment-failure.

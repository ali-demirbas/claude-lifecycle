---
name: price-drop
stage: revenue
trigger_type: event
required_events: [price_drop, view_item, purchase]
optional_events: [add_to_wishlist, add_to_cart, price_increase, consent_withdrawn]
required_attributes: [item_id, item_price]
optional_attributes: [previous_price, currency]
default_channels: [push, email]
base_steps: 2
depth_range: [1, 3]
applicable_industries: [ecommerce, marketplace, travel]
requires_feed: true          # needs a live feed (stock, price, purchase cycle or alerts); blocked at T3
mutually_exclusive_with: [back-in-stock]
journey_class: marketing
signal_sources:
  price_drop: authoritative
  view_item: behavioral
  purchase: authoritative
  add_to_wishlist: behavioral
  add_to_cart: behavioral
  item_price: authoritative
  previous_price: authoritative
  consent_withdrawn: authoritative
  link_click: engagement
insufficient_alone:
  - a price_drop below the minimum threshold
  - a single view_item older than the recency window
  - a previous_price that did not come from the price feed
exit_before_each_send: [purchase, consent_withdrawn, price_increase]
reentry: {policy: each_trigger, on_duplicate_trigger: ignore}
instance_key: item_id
measurement_default: holdout
---

# Price Drop

Tell people an item they showed interest in got cheaper. Same informational family as [back-in-stock](back-in-stock.md): one fact, short sequence, entirely data-gated. It needs a price feed emitting `price_drop` events per item *and* item-level interest events to know who cares; without either, the pattern is blocked. In travel, this is the fare-alert workhorse.

## Required-event signature

| Event | Source | Role |
|---|---|---|
| `price_drop` | authoritative (price feed) | Trigger, fired per item when the price falls past a threshold (default 5–10% or a person's own alert level; configurable, tune with complaint and conversion data). Without a price feed, the pattern is **blocked**. |
| `view_item` | behavioral | Minimum interest signal, recency-bounded (≤ 30 days). |
| `purchase` | authoritative | Success exit; must carry `items` and `value` to attribute the conversion to the discounted item. |
| `add_to_wishlist` / `add_to_cart` *(optional)* | behavioral | Stronger interest tiers; prioritize these audiences when a drop affects many people. |
| `price_increase` *(optional)* | authoritative | The price rose back; ends the instance. Without it, the send-time price check does the same job. |
| `previous_price` *(optional attr)* | authoritative | Enables the before/after framing that makes the message land; without it, show only the new price. |

### Not enough on its own

- **A drop below the threshold:** a 1% wiggle is noise to the person; it never triggers.
- **A stale view:** interest older than the recency window is not interest in today's price.
- **A "was" price not from the feed:** a struck-through price must be a real previous price the system recorded, never a number chosen for the copy.

## Entry / exit

- **Entry:** `price_drop` fired for an item with recorded interest (view/wishlist/cart) in the last 30 days, item not purchased, drop exceeds the minimum threshold, person messageable on ≥ 1 channel.
- **Exclude:** person purchased the item at the higher price in the last 14 days (this message reads as an insult; see Common mistakes), trivial drops below threshold, person currently in a P0 flow, portfolio-wide negative-signal override, item concurrently entering [back-in-stock](back-in-stock.md) for the same person (a restock that also reprices is one message, "back and cheaper", never two notifications about the same item in the same window).
- **Success exit:** `purchase` containing the item · **Window:** 72h or until the price rises again, whichever comes first.
- **Checked before each send:** for this instance's item only (`instance_key: item_id`; a purchase or price change of another item never stops it): `purchase` of the item, `price_increase` on the item, and the live price. `consent_withdrawn` is scoped to that send's channel: a push opt-out skips s1 and leaves a consented email in place. If the price is above the notified level, the send is suppressed and the instance ends.
- **Re-entry:** per item, once per distinct drop; at most 1 price-drop notification per person per day across items.
- **Repeated trigger while active:** a further drop on the same item while an instance is open is ignored as a trigger; the next send shows the live price, so the person still sees the lower number.
- **Handoffs:** an item already in an open cart → the drop is mentioned in [abandoned-cart](abandoned-cart.md)'s next send instead of here (the branched cart-interest step below covers carts with no active cart journey).

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (1) | Any DQS | Single notification: new price, deeplink. |
| Standard (2) | Second channel consented | Push for speed, email with the before/after price for someone who didn't respond, only while the price holds. |
| Branched (3) | `add_to_cart` tracked | Cart-interest people get an extra direct step ("the thing in your cart is cheaper now"), the highest-intent audience this pattern ever sees. |

Depth does **not** scale with DQS. A price is a fact with a shelf life; a third reminder about the same discount is noise. DQS improves eligibility precision (interest recency, purchase exclusion, threshold tuning), not sequence length.

## Step blueprint (standard, 2 sends)

| Node | When | Channel | Intent | Route |
|---|---|---|---|---|
| s1 | entry +1h | push | "{{product_name}} dropped to {{new_price}}" + deeplink | → d1 |
| d1 | s1 +24h | — | Decision on any_of(link_click on s1 (engagement, bot-filtered), `view_item` of this item (behavioral)) between s1 and s1 +24h | occurred → end · not_occurred → s2 · unmeasurable → s2 |
| s2 | s1 +24h | email | Before/after price, product image, honest note that prices can change back | → end |

Hard rule: verify the price at send time. If it rose back, suppress. Never show a struck-through "was" price unless `previous_price` comes from the feed, not from copywriting. More generally, any message referencing a live price or stock value must either pull live data at send time (the CRM's live-content mechanism) or re-verify the trigger condition at send; a design-time value baked into copy goes stale, and a wrong price claim is a trust-killer.

## Timing and channel fit

- **Clock:** user local time. Push queued through 22:00–09:00 is released staggered inside 09:00–11:00 (never a 09:00 burst), with the price re-checked at release. Email avoids 00:00–06:00.
- **Channel fit:** push for speed on a fact with a shelf life; email for the before/after framing and the image. SMS only for a person-set price alert that asked for SMS, with SMS consent.
- **Fallback:** no push consent → s2 becomes the only send at `entry +1h`, subject to email's quiet window.
- **Business clock:** if the feed reprices in batches (overnight jobs, fare refreshes), anchor `entry` to the time the new price is live on the site, not to the feed event, so the link never lands on the old price.

## Frequency and overlap

- **Worst path, rolling 7 days:** 1 push + 1 email per item. The 1-per-day cap across items allows up to 7 notifications a week in a volatile catalog, so the channel caps (push 5, email 4 per week) bind first; drops beyond them are skipped, not queued.
- **Overlaps:** back-in-stock (merge), abandoned-cart (cart wins for items in the cart), browse-abandonment (this pattern wins), seasonal sale campaigns (a site-wide sale makes item-level drop alerts redundant; suppress during declared sale windows).
- **Precedence:** abandoned-cart and payment-failure outrank this pattern; this pattern outranks browse-abandonment. A send that would breach a cap is skipped, because a deferred price alert is often a wrong one.

## Measurement

- **Primary outcome:** `purchase` of the item within the 72h window, read over a 7-day measurement window.
- **Design:** journey-level holdout, default 10%, randomized per person (not per item) and sticky. The control gets the lower price on the site but no notification. A person-set price alert is a promise; treat it like an explicit back-in-stock request (outside the holdout, pre/post comparison) unless the business accepts the trade-off.
- **Routine communications both groups keep:** sale campaigns and newsletters that happen to feature the item.
- **Contamination:** sale emails featuring the same item reach the control; record the overlap and read the lift as the alert's effect on top of them.
- **Margin honesty:** a lift in purchases at a lower price is not automatically a gain; report incremental margin next to incremental conversions.
- **Low volume:** drops are per item and irregular; expect long accumulation before a lift read is trustworthy.

## When data is missing

- **No `previous_price`:** show only the new price; no before/after framing.
- **No `price_increase` event:** rely on the send-time price check; if the CRM can't read a live price at send, keep the sequence to s1 only.
- **No click tracking:** d1 resolves as unmeasurable and the email goes out once while the price holds.
- **Purchase without `items`:** exclude anyone with any purchase since the trigger, and mark attribution as approximate.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Incremental notification-to-purchase rate | primary | purchases of the item within window, exposed vs holdout |
| Incremental margin per notification | secondary | a price-drop sale at lower margin isn't automatically a win; track it honestly |
| Notifications per person per week | guardrail | volatile catalogs can flood people; the per-day cap is the pattern's survival mechanism |

## Common mistakes

- Notifying recent full-price buyers about the drop; the single most trust-destroying send in commerce. An exclusion window on purchasers is mandatory, cross-device if identity allows.
- No drop threshold; a 1% price wiggle triggers a push. People learn the channel is noise and kill it at the OS level.
- Fake urgency ("price goes back up tonight!") without feed evidence; if the repricing schedule isn't known, say nothing about the future.

---
name: back-in-stock
stage: revenue
trigger_type: event
required_events: [item_back_in_stock, add_to_wishlist, purchase]
optional_events: [view_item, add_to_cart, remove_from_wishlist, stock_alert_unsubscribe, item_discontinued, consent_withdrawn]
required_attributes: [item_id]
optional_attributes: [inventory_level, item_price, catalog_status]
default_channels: [push, email]
base_steps: 2
depth_range: [1, 3]
applicable_industries: [ecommerce, marketplace]
mutually_exclusive_with: [price-drop]
journey_class: marketing
signal_sources:
  item_back_in_stock: authoritative
  add_to_wishlist: behavioral
  purchase: authoritative
  view_item: behavioral
  remove_from_wishlist: behavioral
  stock_alert_unsubscribe: authoritative
  inventory_level: authoritative
  catalog_status: authoritative
  consent_withdrawn: authoritative
  message_click: engagement
insufficient_alone:
  - a single view_item
  - a restock event without a live availability check at send time
  - interest in an item that was purchasable all along
  - interest in a category rather than one specific item
exit_before_each_send: [purchase, consent_withdrawn, remove_from_wishlist, stock_alert_unsubscribe, item_discontinued]
reentry: {policy: each_trigger, on_duplicate_trigger: ignore}
measurement_default: holdout
---

# Back in Stock

Tell people the moment an item they wanted becomes available again. This is an informational pattern: the fact *is* the message, demand already exists, and the only jobs are speed and relevance. It can't run without an inventory data feed: the trigger event `item_back_in_stock` must come from the catalog/inventory system, not from user behavior.

## Required-event signature

| Event | Source | Role |
|---|---|---|
| `item_back_in_stock` | authoritative (inventory feed) | Trigger, fired per item when stock goes from 0 to available. Without a live inventory feed, the pattern is **blocked**. |
| `add_to_wishlist` | behavioral | Interest registration: who gets notified about which item. An explicit "notify me" request on the product page counts here too. |
| `purchase` | authoritative | Success exit. Must carry `items` so the conversion can be matched to the restocked item. |
| `view_item` *(optional)* | behavioral | Fallback interest signal when wishlist adoption is low; only with a tight recency window (≤ 14 days) and repeated views. |
| `remove_from_wishlist` / `stock_alert_unsubscribe` *(optional)* | behavioral / authoritative | Withdrawn interest; ends the instance. |
| `catalog_status` *(optional attr)* | authoritative | Separates temporarily out of stock from withdrawn from the catalogue. |
| `inventory_level` *(optional attr)* | authoritative | Enables honest scarcity ("only a few left"); never claim scarcity without it. |

### Not enough on its own

- **A single `view_item`:** a glance is not a request to be told; notifying on it is how this pattern collects unsubscribes.
- **A restock event without a send-time check:** the event says stock arrived at some moment; it doesn't say the item is still there when the message goes out. Availability is re-read before every send.
- **Interest in an item that was purchasable all along:** that's ordinary interest (browse or wishlist territory), not unmet demand waiting on a restock.
- **Interest in a category:** a restock is about one item; a category-level interest gets no alert.

## Entry / exit

- **Entry:** `item_back_in_stock` fired for an item the person wishlisted or asked to be notified about (or viewed repeatedly, if the fallback is enabled) while it was unavailable, no `purchase` of that item since, the person is messageable on ≥ 1 channel.
- **Exclude:** item already purchased (identity-stitched), wishlist interest older than 90 days (configurable; lengthen only for slow-moving catalogs where old wishlists still convert), item withdrawn from the catalogue rather than temporarily out of stock (it never comes back, so no instance opens, and a pending alert request is closed rather than left waiting), person currently in a P0 transactional flow, portfolio-wide negative-signal override, item concurrently entering [price-drop](price-drop.md) for the same person (combine into one "back and cheaper" message rather than sending both).
- **Success exit:** `purchase` containing the restocked item · **Window:** 72h (stock may not last longer).
- **Checked before each send:** `purchase` of the item, `consent_withdrawn` for that send's channel, `remove_from_wishlist` or `stock_alert_unsubscribe` for the item, `item_discontinued`, and live availability. A withdrawn interest ends the instance; it is never treated as a quiet one. An item that sold out again in the gap means the send is skipped and the instance ends.
- **Re-entry:** per item, once per restock event. An item that sells out again after the alert doesn't reopen this instance; interest recorded during the next out-of-stock period is a new instance on its own clock.
- **Repeated trigger while active:** a second restock event or a second interest signal for the same item while an instance is open is ignored.
- **Handoffs:** received from [abandoned-cart](abandoned-cart.md) when every item in a cart became unavailable (one instance per item). An `add_to_cart` of the restocked item → [abandoned-cart](abandoned-cart.md), queued sends here suppressed.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (1) | Any DQS | Single notification: item is back, deeplink to the product page. |
| Standard (2) | Any DQS, second channel consented | Push first for speed, email follow-up for someone who didn't respond, only while still in stock. |
| Branched (3) | `inventory_level` available | Adds a genuine low-stock last call, gated on real inventory and sent once per stock event. |

Depth does **not** scale with DQS here. The message carries one fact; adding steps adds annoyance, not persuasion. Higher DQS improves *targeting* (better interest signals, cross-device purchase exclusion), never length.

## Step blueprint (standard, 2 sends)

| Node | When | Channel | Intent | Route |
|---|---|---|---|---|
| s1 | entry +15m | push | "{{product_name}} is back" + deeplink to the product page; nothing about how long it will last | → d1 |
| d1 | s1 +24h | — | Decision on a bot-filtered click on s1 (engagement) or a `view_item` of the restocked item (behavioral) between s1 and s1 +24h | occurred → end · not_occurred → s2 · unmeasurable → s2 |
| s2 | s1 +24h | email | Same fact with product image and current price; availability re-checked at send | → end |

The occurred route ends the sequence because the person has seen the fact; the purchase window keeps running for measurement. The unmeasurable route sends the email once, since repeating a fact the person asked for on a second channel costs little.

Branched shape: s3 at `s2 +24h` on push, only when `inventory_level` is at or below a configured low-stock threshold at send time, once per stock event, and never with invented scarcity.

Hard rule: re-check inventory before every send. Notifying about an item that sold out again in the gap is the fastest way to burn this channel's trust. More generally, any message referencing a live price or stock value must either pull live data at send time (the CRM's live-content mechanism) or re-verify the trigger condition at send; a design-time value baked into copy goes stale, and a wrong stock claim is a trust-killer. Nothing is claimed about reserved stock, held prices or how long availability will last.

## Timing and channel fit

- **Clock:** user local time. Push is queued through 22:00–09:00 and released at the window's opening, never dropped; re-check availability at release, since a popular restock can sell out overnight. Email avoids 00:00–06:00.
- **Channel fit:** push first because speed is the lever and the message is one line; email second because it carries the image and price. SMS only for an explicit "notify me by SMS" request with SMS consent.
- **Fallback:** no push consent or no valid token → s2 becomes the first and only send at `entry +15m`, subject to email's quiet window.

## Frequency and overlap

- **Worst path, rolling 7 days:** 1 push + 1 email per restocked item; branched adds one push. Several restocks in the same week can stack, so cap this pattern at 1 push per person per day across items and fold same-day restocks into one message.
- **Overlaps:** price-drop on the same item (merge into one message), abandoned-cart for an item already in the cart (cart wins), browse-abandonment (this pattern wins), replenishment.
- **Precedence:** abandoned-cart and payment-failure outrank this pattern for the same items; this pattern outranks browse-abandonment. Because the value decays in hours, a back-in-stock send that would breach a cap is skipped rather than deferred past the window.

## Measurement

- **Primary outcome:** `purchase` of the restocked item within the 72h window, read over a 7-day measurement window (whole weeks).
- **Design:** journey-level holdout, default 10%, for inferred interest (wishlist and repeat views). An explicit "notify me" request is a promise to the person: hold those requesters out only if the business accepts not keeping it for the control, otherwise run them outside the holdout and measure with a pre/post comparison of restock conversion.
- **Routine communications both groups keep:** product-page "back in stock" badges, newsletters featuring the item.
- **Contamination:** a held-out person who gets the item in a price-drop or newsletter send within the window is contaminated; merge rules must respect the holdout.
- **Low volume:** restocks are lumpy and per-item; a store with few restocks a month will read this as unmeasured for a long time. Report it so, not as "no effect".

## When data is missing

- **No inventory feed:** blocked; there's nothing honest to trigger on.
- **No `catalog_status`:** a discontinued item can't be told apart from a stockout; close interests older than the exclusion window and flag the gap.
- **No `remove_from_wishlist` or alert-unsubscribe signal:** withdrawn interest can't be honoured, so shorten the interest recency window and note the risk.
- **No click tracking:** d1 resolves as unmeasurable and the email goes out once.
- **`purchase` without `items`:** the success exit can't match the item; exclude anyone with any purchase since the trigger and mark attribution as approximate.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Incremental notification-to-purchase rate | primary | purchases of the restocked item within window, exposed vs holdout |
| Time to first click | secondary | speed is the lever; track send latency separately from user latency |
| Push opt-out rate per send | guardrail | this pattern earns high engagement; a rising opt-out means targeting rot |

## Common mistakes

- Treating a single `view_item` as interest; people get notified about items they glanced at once, and unsubscribe. Require wishlist/follow or repeated recent views.
- Batching sends daily; restocks of popular items sell out in hours, and batching turns a revenue journey into an apology.
- No restock verification at send time; the push/email must be suppressed if the item sold out between trigger and send.
- Waiting forever on a discontinued item, or alerting someone who removed the item from their wishlist.

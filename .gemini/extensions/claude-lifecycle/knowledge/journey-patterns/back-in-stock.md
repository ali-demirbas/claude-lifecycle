---
name: back-in-stock
stage: revenue
trigger_type: event
required_events: [item_back_in_stock, add_to_wishlist, purchase]
optional_events: [view_item, add_to_cart]
required_attributes: [item_id]
optional_attributes: [inventory_level, item_price]
default_channels: [push, email]
base_steps: 2
depth_range: [1, 3]
applicable_industries: [ecommerce, marketplace]
mutually_exclusive_with: [price-drop]
---

# Back in Stock

Notify users the moment an item they wanted becomes available again. This is an informational pattern: the fact *is* the message, demand already exists, and the only jobs are speed and relevance. It cannot run without an inventory data feed — the trigger event `item_back_in_stock` must be emitted by the catalog/inventory system, not by user behavior.

## Required-event signature

| Event | Role |
|---|---|
| `item_back_in_stock` | Trigger (custom, from inventory feed). Fired per item when stock transitions 0 → available. Without a live inventory feed, the pattern is **blocked**. |
| `add_to_wishlist` | Interest registration. Defines *who* gets notified for *which* item. `view_item` alone is too weak — see Common mistakes. |
| `purchase` | Success exit. Must carry `items` so the conversion can be matched to the restocked item. |
| `view_item` *(optional)* | Fallback interest signal when wishlist adoption is low; use only with a tight recency window (≤ 14 days) and repeated views. |
| `inventory_level` *(optional attr)* | Enables honest scarcity ("only a few left") — never claim scarcity without it. |

## Entry / exit

- **Entry:** `item_back_in_stock` fired for an item the user wishlisted (or repeatedly viewed, if the fallback is enabled), no `purchase` of that item since, user messageable on ≥ 1 channel.
- **Exclude:** item already purchased (identity-stitched), wishlist interest older than 90 days, user currently in a P0 transactional flow, item concurrently entering [price-drop](price-drop.md) for the same user (combine into one "back and cheaper" message rather than sending both).
- **Success exit:** `purchase` containing the restocked item · **Window:** 72h (stock may not last longer) · **Re-entry:** per item, once per restock event.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (1) | Any DQS | Single notification: item is back, deeplink to PDP. |
| Standard (2) | Any DQS, second channel consented | Push first (speed), email follow-up 24h later if no click and still in stock. |
| Branched (3) | `inventory_level` available | Adds a genuine low-stock last-call step, gated on real inventory. |

Depth does **not** scale with DQS here. The message carries one fact; adding steps adds annoyance, not persuasion. Higher DQS improves *targeting* (better interest signals, cross-device purchase exclusion), never length.

## Step blueprint (standard, 2 steps)

| # | Wait | Channel | Intent | Branch |
|---|------|---------|--------|--------|
| 1 | ≤ 15 min after restock (respect push quiet hours 22:00–09:00 — queue, don't drop) | push | "{{product_name}} is back" + deeplink to PDP | — |
| 2 | +24h | email | Same fact with product image and price; include stock-check note | if step 1 not clicked **and** item still in stock |

Hard rule: re-check inventory before every send. Notifying about an item that sold out again in the gap is the fastest way to burn this channel's trust. More generally, any message referencing a live price or stock value must either pull live data at send time (the CRM's live-content mechanism) or re-verify the trigger condition at send — a design-time value baked into copy goes stale, and a wrong stock claim is a trust-killer.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Notification-to-purchase rate | primary | purchases of the restocked item within window / notifications sent |
| Time to first click | secondary | speed is the lever — track send latency separately from user latency |
| Push opt-out rate per send | guardrail | this pattern earns high engagement; a rising opt-out means targeting rot |

## Common mistakes

- Treating a single `view_item` as interest — users get notified about items they glanced at once, and unsubscribe. Require wishlist/follow or repeated recent views.
- Batching sends daily — restocks of popular items sell out in hours; batching converts a revenue journey into an apology.
- No re-stock verification at send time — the email/push must be suppressed if the item sold out between trigger and send.

---
name: price-drop
stage: revenue
trigger_type: event
required_events: [price_drop, view_item, purchase]
optional_events: [add_to_wishlist, add_to_cart]
required_attributes: [item_id, item_price]
optional_attributes: [previous_price, currency]
default_channels: [push, email]
base_steps: 2
depth_range: [1, 3]
applicable_industries: [ecommerce, marketplace, travel]
mutually_exclusive_with: [back-in-stock]
---

# Price Drop

Tell users an item they showed interest in got cheaper. Same informational family as [back-in-stock](back-in-stock.md): one fact, short sequence, entirely data-gated. It requires a price feed emitting `price_drop` events per item *and* item-level interest events to know who cares — without either, the pattern is blocked. In travel, this is the fare-alert workhorse.

## Required-event signature

| Event | Role |
|---|---|
| `price_drop` | Trigger (custom, from price feed). Fired per item when price decreases past a threshold (recommend ≥ 5–10% or a user-set alert). Without a price feed, pattern is **blocked**. |
| `view_item` | Minimum interest signal, recency-bounded (≤ 30 days). |
| `purchase` | Success exit; must carry `items` and `value` to attribute the conversion to the discounted item. |
| `add_to_wishlist` / `add_to_cart` *(optional)* | Stronger interest tiers — prioritize these audiences when a drop affects many users. |
| `previous_price` *(optional attr)* | Enables the before/after framing that makes the message land; without it, show only the new price. |

## Entry / exit

- **Entry:** `price_drop` fired for an item with recorded user interest (view/wishlist/cart) in the last 30 days, item not purchased, drop exceeds the minimum threshold, user messageable on ≥ 1 channel.
- **Exclude:** user purchased the item at the higher price in the last 14 days (this message reads as an insult — see Common mistakes), trivial drops below threshold, user currently in a P0 flow, item concurrently entering [back-in-stock](back-in-stock.md) for the same user (a restock that also reprices is one message — "back and cheaper" — never two separate notifications about the same item within the same window).
- **Success exit:** `purchase` containing the item · **Window:** 72h or until price rises again, whichever first · **Re-entry:** per item, once per distinct drop; max 1 price-drop notification per user per day across items.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (1) | Any DQS | Single notification: new price, deeplink. |
| Standard (2) | Second channel consented | Push for speed, email at +24h with before/after price if not clicked and price still holds. |
| Branched (3) | `add_to_cart` tracked | Cart-interest users get an extra direct step ("the thing in your cart is cheaper now") — highest-intent audience this pattern ever sees. |

Depth does **not** scale with DQS. A price is a fact with a shelf life; a third reminder about the same discount is noise. DQS improves eligibility precision (interest recency, purchase exclusion, threshold tuning) — not sequence length.

## Step blueprint (standard, 2 steps)

| # | Wait | Channel | Intent | Branch |
|---|------|---------|--------|--------|
| 1 | ≤ 1h after drop (queue through push quiet hours 22:00–09:00) | push | "{{product_name}} dropped to {{new_price}}" + deeplink | — |
| 2 | +24h | email | Before/after price, product image, honest note that prices can change back | if step 1 not clicked **and** price still at or below notified level |

Hard rule: verify the price at send time. If it rose back, suppress. Never show a struck-through "was" price unless `previous_price` comes from the feed, not from copywriting. More generally, any message referencing a live price or stock value must either pull live data at send time (the CRM's live-content mechanism) or re-verify the trigger condition at send — a design-time value baked into copy goes stale, and a wrong price claim is a trust-killer.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Notification-to-purchase rate | primary | purchases of the item within window / notifications sent |
| Incremental margin per notification | secondary | a price-drop sale at lower margin isn't automatically a win — track it honestly |
| Notifications per user per week | guardrail | volatile catalogs can flood users; the per-day cap is the pattern's survival mechanism |

## Common mistakes

- Notifying recent full-price buyers about the drop — the single most trust-destroying send in commerce. Exclusion window on purchasers is mandatory, cross-device if identity allows.
- No drop threshold — a 1% price wiggle triggers a push. Users learn the channel is noise and kill it at the OS level.
- Fake urgency ("price goes back up tonight!") without feed evidence — if the repricing schedule isn't known, say nothing about the future.

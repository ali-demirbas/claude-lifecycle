---
name: replenishment
stage: revenue
trigger_type: time
required_events: [purchase]
optional_events: [add_to_cart, view_item, subscription_start]
required_attributes: [items]
optional_attributes: [consumption_cycle_days, package_size, last_item_id]
default_channels: [email, push]
base_steps: 3
depth_range: [2, 5]
applicable_industries: [ecommerce, marketplace]
---

# Replenishment

Remind buyers of consumables to reorder just before the product runs out. Timing is everything: the reminder must land inside the narrow window between "getting low" and "already bought elsewhere". Cycles are computed per item — from repeat-purchase interval distributions across buyers, or catalog metadata — never as one global number.

## Required-event signature

| Event | Role |
|---|---|
| `purchase` | Trigger source and success exit. |
| `items` *(required attr)* | The GA4 items array on `purchase`, with `item_id` and `quantity`. This pattern is **blocked** without item-level data — you cannot know what to replenish or when. |
| `consumption_cycle_days` *(optional attr)* | Per-item cycle, from catalog metadata or observed repeat intervals. Without it, cycles must be inferred from the buyer base's repeat-purchase distribution before launch. |
| `package_size` × `quantity` *(optional attrs)* | Scale the cycle: a 2-pack buyer's clock runs twice as long. |
| `subscription_start` *(optional)* | Auto-delivery signal — subscribers on an item exit its replenishment reminders permanently. |

## Entry / exit

- **Entry:** `purchase` containing a replenishable item (catalog-flagged, or inferred from a tight repeat-interval distribution), predicted depletion approaching (cycle minus reorder lead time), no repurchase yet.
- **Exclude:** item on auto-delivery subscription, item refunded/returned, user already in a replenishment journey for the same item.
- **Success exit:** `purchase` containing the same `item_id` (or its category) · **Window:** through 1.5× cycle · **Re-entry:** every cycle, per item — but portfolio caps decide if multiple items' reminders can coexist.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (2) | DQS < 40 or cycle inferred coarsely | One "running low?" email near end of cycle + one overdue follow-up. |
| Standard (3) | DQS 40–69 | Pre-empt at ~80% of cycle, due reminder, subscribe-and-save close. |
| Branched (4–5) | DQS ≥ 70 + `package_size`/`quantity` | Quantity-adjusted timing per user, multi-item bundling when several cycles align, dedicated subscribe-and-save branch for 3rd+ repurchase. |

## Step blueprint (standard, 3 steps)

| # | Wait | Channel | Intent | Branch |
|---|------|---------|--------|--------|
| 1 | at ~80% of cycle | email | "Running low?" — exact item, one-click reorder, last order recap | — |
| 2 | at 100% of cycle | push | Due-today deeplink to a prefilled cart | if step 1 not clicked |
| 3 | +5d past cycle | email | Reorder + subscribe-and-save option: convert the habit into a subscription | — |

## KPIs

| KPI | Type | Note |
|---|---|---|
| Repurchase rate within 1.5× cycle | primary | same item or category / journeys entered; compare against unprompted organic repurchase baseline |
| Auto-delivery conversion rate | secondary | replenishment's endgame is making itself unnecessary |
| Unsubscribe rate per send | guardrail | mistimed reminders ("I just bought this") are the top complaint driver here |

## Common mistakes

- One global cycle for every SKU — a razor-blade cycle and a vitamin-jar cycle differ severalfold; compute per item or don't launch the item.
- Ignoring `quantity` and `package_size` — the multi-pack buyer reminded on the single-pack clock gets messaged when half the supply remains.
- Continuing reminders after `subscription_start` on the item — reminding a subscriber to buy what already ships automatically is the fastest route to an unsubscribe.

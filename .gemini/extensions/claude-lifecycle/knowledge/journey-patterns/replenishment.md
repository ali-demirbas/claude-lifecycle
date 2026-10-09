---
name: replenishment
stage: revenue
trigger_type: time
required_events: [purchase]
optional_events: [add_to_cart, view_item, subscription_start, refund, consent_withdrawn]
required_attributes: [items]
optional_attributes: [consumption_cycle_days, package_size, last_item_id]
default_channels: [email, push]
base_steps: 3
depth_range: [2, 5]
applicable_industries: [ecommerce, marketplace]
journey_class: marketing
signal_sources:
  purchase: authoritative
  items: authoritative
  consumption_cycle_days: inferred
  subscription_start: authoritative
  refund: authoritative
  add_to_cart: behavioral
  view_item: behavioral
  consent_withdrawn: authoritative
  message_click: engagement
insufficient_alone:
  - a category-average cycle with no purchase by this person behind it
  - a predicted run-out date, which is an estimate
  - a click on a reminder
exit_before_each_send: [purchase, subscription_start, refund, consent_withdrawn]
reentry: {policy: each_trigger, on_duplicate_trigger: restart}
measurement_default: holdout
---

# Replenishment

Remind buyers of consumables to reorder just before the product runs out. Timing is everything: the reminder must land inside the narrow window between "getting low" and "already bought elsewhere". Cycles are computed per item, from repeat-purchase interval distributions across buyers or from catalog metadata, never as one global number. Whatever the method, the run-out date is a prediction, and the person is told it as one.

## Required-event signature

| Event | Source | Role |
|---|---|---|
| `purchase` | authoritative | Trigger source and success exit. |
| `items` *(required attr)* | authoritative | The item array on `purchase`, with `item_id` and `quantity`. The pattern is **blocked** without item-level data: you can't know what to replenish or when. |
| `consumption_cycle_days` *(optional attr)* | inferred | Per-item cycle, from catalog metadata or observed repeat intervals. Without it, cycles must be inferred from the buyer base's repeat-purchase distribution before launch. |
| `package_size` × `quantity` *(optional attrs)* | authoritative | Scale the cycle: a 2-pack buyer's clock runs twice as long. |
| `subscription_start` *(optional)* | authoritative | Auto-delivery signal: a subscriber on an item leaves its replenishment reminders permanently. |
| `refund` *(optional)* | authoritative | A returned item has nothing to run out of; ends the instance. |

### Not enough on its own

- **A category-average cycle with no purchase by this person behind it:** the clock starts from the person's own purchase; a category average only sets the cycle length, never the start.
- **A predicted run-out date:** an estimate from purchase history and package size. It times the reminder, and the copy says it is an estimate ("you may be running low"), never a fact about what the person has left.
- **A click on a reminder:** a branch signal only; the instance ends on a purchase or a subscription, not on engagement.

## Entry / exit

- **Entry:** `purchase` containing a replenishable item (catalog-flagged, or inferred from a tight repeat-interval distribution), a cycle reliable enough to act on, no repurchase yet. The instance opens at purchase and waits for the anchors below.
- **Exclude:** item on an auto-delivery subscription, item refunded or returned, person already in a replenishment instance for the same item, an item whose cycle estimate is too loose to time (no instance opens rather than a mistimed one), portfolio-wide negative-signal override.
- **Success exit:** `purchase` containing the same `item_id` (or its category) · **Window:** through 1.5× the cycle (configurable).
- **Checked before each send:** `purchase` of the item or its category, `subscription_start` for it, `refund` of it, `consent_withdrawn` for that send's channel.
- **Re-entry:** every cycle, per item; portfolio caps decide whether several items' reminders can coexist.
- **Repeated trigger while active:** a new purchase of the same item closes the open instance as replenished and restarts the clock from the new purchase.
- **Handoffs:** `subscription_start` → the subscription's own service messages; queued reminders suppressed.

Anchors (declared in the journey's `time_anchors`): `predicted_runout` = purchase + cycle × quantity × package factor; `reorder_point` = `predicted_runout` minus the reorder lead time (default 20% of the cycle, configurable to the delivery time the business can actually meet).

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (2) | DQS < 40 or cycle inferred coarsely | One "running low?" email near the end of the cycle + one overdue follow-up. |
| Standard (3) | DQS 40–69 | Pre-empt at the reorder point, due reminder, subscribe-and-save close. |
| Branched (4–5) | DQS ≥ 70 + `package_size`/`quantity` | Quantity-adjusted timing per person, multi-item bundling when several cycles align, dedicated subscribe-and-save branch for a 3rd+ repurchase. |

## Step blueprint (standard, 3 sends)

| Node | When | Channel | Intent | Route |
|---|---|---|---|---|
| s1 | reorder_point +0d | email | "You may be running low": exact item, the estimated run-out stated as an estimate, one-click reorder, last order recap | → d1 |
| d1 | predicted_runout +0d | — | Decision on a bot-filtered click on s1 (engagement) or an `add_to_cart`/`view_item` of the item (behavioral) between s1 and predicted_runout | occurred → s3 · not_occurred → s2 · unmeasurable → s2 |
| s2 | predicted_runout +0d at 10:00 user_local | push | Short reorder nudge, deeplink to a prefilled cart | → s3 |
| s3 | predicted_runout +5d | email | Reorder + subscribe-and-save option: turn the habit into a subscription | → end |

Someone who came back to the item after s1 but didn't buy skips the push and gets the subscription close; the push is for the person who hasn't reacted.

## Timing and channel fit

- **Clock:** user local time. The push is pinned to 10:00 local on the due date to stay inside push and SMS-safe hours; email avoids 00:00–06:00.
- **Channel fit:** email carries the item, the estimate and the reorder link; push is a one-tap reorder on the due date. SMS only for a reorder flow the person has used by SMS before, with SMS consent.
- **Fallback:** no push consent → s2 is skipped and s3 moves to `predicted_runout +3d`, keeping two sends.
- **Delivery lead time:** the reorder point must leave enough time to deliver before the run-out estimate; if delivery takes longer than the default lead time, move the reorder point earlier rather than promising arrival dates.

## Frequency and overlap

- **Worst path, rolling 7 days:** s1 sits ahead of the run-out estimate and s2/s3 fall within 5 days of it, so with the default lead time all 3 sends (2 emails + 1 push) can land in one week for a short cycle. Several items on aligned cycles stack; bundle items due within the same week into one reminder.
- **Overlaps:** post-purchase (the second-purchase bridge often targets the same item; replenishment owns consumables, post-purchase steps aside), back-in-stock, price-drop, browse-abandonment.
- **Precedence:** abandoned-cart outranks this pattern for the same item; this pattern outranks browse-abandonment and back-in-stock for the same person. On a cap breach, defer by at most 2 days and re-check purchases before sending; drop it if the deferral would push s1 past the run-out estimate.

## Measurement

- **Primary outcome:** repurchase of the same item or category within 1.5× the cycle.
- **Design:** journey-level holdout, default 10%, randomized at entry, sticky per person across items. The control receives none of this journey's reminders and reorders on its own; that organic repurchase rate is the baseline the lift is read against.
- **Routine communications both groups keep:** order and delivery messages, newsletters.
- **Contamination:** a post-purchase bridge or a promo featuring the same item reaching the control dilutes the lift; the portfolio conflict review must keep them off the control for that item.
- **Low volume:** cycles are long, so a single read can take months. Per-item reads are rarely powered; read at portfolio level across replenishable items and say per-item results are unmeasured.

## When data is missing

- **No `consumption_cycle_days`:** infer the cycle from repeat-purchase intervals; if the distribution is too wide, don't launch the item.
- **No `package_size` or `quantity`:** use the single-unit cycle and add a "may" framing; flag that multi-pack buyers will be reminded early.
- **No `subscription_start`:** subscribers can't be excluded; launch only for items with no subscription option, or exclude everyone who bought through the subscription flow.
- **No click or cart tracking:** d1 resolves as unmeasurable and the push goes out.
- **Purchases from other channels not stitched** (marketplaces, stores): expect "I just bought this" complaints; widen the lead time and keep copy conditional.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Incremental repurchase rate within 1.5× cycle | primary | same item or category, exposed vs holdout; the holdout is the organic repurchase baseline |
| Auto-delivery conversion rate | secondary | replenishment's endgame is making itself unnecessary |
| Unsubscribe rate per send | guardrail | mistimed reminders ("I just bought this") are the top complaint driver here |

## Common mistakes

- One global cycle for every SKU; a razor-blade cycle and a vitamin-jar cycle differ severalfold. Compute per item or don't launch the item.
- Ignoring `quantity` and `package_size`; the multi-pack buyer reminded on the single-pack clock gets messaged when half the supply remains.
- Continuing reminders after `subscription_start` on the item; reminding a subscriber to buy what already ships automatically is the fastest route to an unsubscribe.
- Writing the prediction as a fact ("you've run out"); the person knows their shelf better than the model does.

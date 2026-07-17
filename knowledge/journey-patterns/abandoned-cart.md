---
name: abandoned-cart
stage: revenue
trigger_type: event
required_events: [add_to_cart, purchase]
optional_events: [begin_checkout, view_cart, remove_from_cart]
required_attributes: []
optional_attributes: [cart_value, cart_items]
default_channels: [email, push]
base_steps: 5
depth_range: [3, 8]
applicable_industries: [ecommerce, marketplace, travel, insurance, edtech]
---

# Abandoned Cart

Recover users who added items to their cart but did not purchase. Consistently the highest-ROI journey in commerce: intent is proven, the ask is small.

## Required-event signature

| Event | Role |
|---|---|
| `add_to_cart` | Trigger. Journey arms when the cart becomes non-empty. |
| `purchase` | Success exit. Without it, recovery cannot be measured — pattern is **blocked**. |
| `begin_checkout` *(optional)* | Enables a higher-intent branch (checkout abandoners get a shorter, more direct sequence). |
| `view_cart` *(optional)* | Enables re-engagement branch and better abandonment timing. |
| `cart_value` *(optional attr)* | Enables value-based branching (high-value carts may justify an incentive step). |

## Entry / exit

- **Entry:** `add_to_cart` fired, no `purchase` within the arming window (default 1h), user messageable on ≥ 1 channel.
- **Exclude:** purchased in last 24h, currently in a P0 transactional flow, cart value below minimum (if known).
- **Success exit:** `purchase` (any) · **Window:** 7 days · **Re-entry:** once per 7 days.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (3) | DQS < 40 or only required events | Reminder → value nudge → last call. Single channel, time-based waits. |
| Standard (4–6) | DQS 40–69 | Adds second channel and one open/click branch. |
| Branched (7–8) | DQS ≥ 70 + `begin_checkout` or `cart_value` | Splits checkout-abandoners vs cart-abandoners; optional incentive branch gated on cart value. |

## Step blueprint (standard, 5 steps)

| # | Wait | Channel | Intent | Branch |
|---|------|---------|--------|--------|
| 1 | +1h after abandonment | email | Reminder: cart contents, zero pressure | — |
| 2 | +20h | push | Short nudge, deeplink to cart | if step 1 not opened |
| 3 | +24h | email | Objection handling: shipping/returns/trust | — |
| 4 | +48h | email | Social proof on cart items | if clicked but no purchase |
| 5 | +72h | push | Last call (no fake urgency; state real expiry only if true) | — |

Incentive rule: never lead with a discount. If an incentive step exists at all, it is the **last** step, gated on cart value and margin, and flagged for the user to approve. Incentive choice follows the CLV-tied rule: above the account's CLV threshold prefer a value-add over a discount; below it, a capped modest discount (see intake incentive policy).

Send-time staleness rule: any message referencing a live price or stock value (cart contents, item price, availability) must either pull live data at send time via the CRM's live-content mechanism or re-verify the trigger condition at send — a design-time value baked into copy goes stale, and a wrong price or stock claim is a trust-killer.

Honest low-stock urgency: where a live `inventory_level` exists for a cart item, the last-call step may state real scarcity ("2 left") under the same rule as [back-in-stock](back-in-stock.md) — never claim scarcity without the data, and re-check the level at send time per the staleness rule above.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Cart recovery rate | primary | purchases within window / journeys entered |
| Revenue per entrant | secondary | |
| Unsubscribe rate per send | guardrail | ceiling from channel rules |

## Common mistakes

- Firing at +5 minutes — user may still be shopping; minimum arming window 30–60 min.
- Discounting in step 1 — trains cart-abandonment behavior.
- Not excluding purchasers across devices — require identity-stitched `purchase` exit if available.

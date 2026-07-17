---
name: post-purchase
stage: retention
trigger_type: event
required_events: [purchase]
optional_events: [refund, review_submitted, view_item, add_to_cart]
required_attributes: []
optional_attributes: [delivery_date, order_category, is_first_purchase, is_guest_checkout, support_ticket_open]
default_channels: [email, push]
base_steps: 4
depth_range: [3, 7]
applicable_industries: [ecommerce, marketplace, travel]
---

# Post-Purchase

Turn one purchase into a relationship: onboarding onto the product bought, a well-timed review/UGC ask, and a bridge to the second purchase. Sits **on top of, never inside** the transactional layer — order and shipping confirmations are consent-exempt only while they carry zero promotional content (see [consent-and-quiet-hours.md](../compliance/consent-and-quiet-hours.md)); everything in this pattern is marketing and requires marketing consent.

## Required-event signature

| Event | Role |
|---|---|
| `purchase` | Trigger and (for the second order) success exit. Must carry `items` for category-aware content. |
| `refund` *(optional)* | Kill switch — a refund mid-journey must halt cross-sell and review asks immediately. |
| `review_submitted` *(optional, custom)* | No GA4 standard exists; track it to measure the review step and stop re-asking. |
| `delivery_date` *(optional attr)* | The single highest-value attribute here: every step anchors to delivery, not checkout. Without it, fall back to purchase date + conservative offsets. |
| `is_first_purchase` *(optional attr)* | First-time buyers get the trust-building track; repeat buyers skip straight to the bridge. |
| `support_ticket_open` *(optional attr)* | Kill switch alongside `refund` — an open ticket on the order must halt cross-sell and review asks the same way a refund does. Without this attribute, the exclude/branch rules below cannot actually be evaluated; treat it as a required signal from the support system, not a nice-to-have. |

## Entry / exit

- **Entry:** `purchase` fired, marketing consent on ≥ 1 channel (transactional confirmations happen regardless, outside this journey).
- **Exclude:** refund initiated, open support ticket on the order, user already in a post-purchase journey for a recent order (newest order wins, older instance exits).
- **Success exit:** second `purchase` · **Window:** 45 days · **Re-entry:** per purchase, subject to portfolio frequency caps.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (3) | DQS < 40 or only `purchase` | Care/usage tips → review ask → generic second-purchase nudge. Purchase-date offsets. |
| Standard (4–5) | DQS 40–69 | Delivery-anchored timing, `order_category` cross-sell, refund kill switch. |
| Branched (6–7) | DQS ≥ 70 + `is_first_purchase` and `review_submitted` | First-buyer trust track vs repeat-buyer bridge track; reviewers skip the ask and get a UGC/referral step instead. |

## Step blueprint (standard, 4 steps)

| # | Wait | Channel | Intent | Branch |
|---|------|---------|--------|--------|
| 1 | +2d after `delivery_date` (fallback: +7d after purchase) | email | Usage / care / getting-the-most tips for the item bought — pure value, no sell | — |
| 2 | +5d | email | Review/UGC ask: one item, one click, honest framing | skip if `refund` |
| 3 | +10d | email | Cross-sell complements to `order_category`, framed as completing the purchase | skip if `refund` or support ticket open |
| 4 | +20d | push | Second-purchase bridge: replenish, next step in the category, or new-arrivals deeplink | — |

For guest checkout (`is_guest_checkout`): fold one account-creation nudge into step 1 or 2, framed on real value the account unlocks (order tracking, saved details for a faster next checkout, backdated loyalty points if a program exists) — never a bare "register now." Ask once; if declined, drop it, a second guest purchase in the same 90-day window doesn't get asked again.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Repeat purchase rate within 90 days | primary | second purchase / journeys entered; compare first-buyer vs repeat-buyer cohorts |
| Review submission rate | secondary | requires `review_submitted` tracking |
| Unsubscribe rate per send | guardrail | post-purchase lists are your best; burning them costs every future journey |

## Common mistakes

- Asking for a review before the item arrives — anchor on `delivery_date`; a checkout-date offset regularly lands the ask mid-shipping and earns 1-star logistics reviews.
- Slipping promos into the order-confirmation email to dodge consent — it converts the message to marketing and forfeits transactional status for the sender.
- Cross-selling to a user with an open refund or support ticket — the kill-switch check must run before each send, not only at entry.
- Treating every return as a lost relationship — the kill switch stops *selling*, not caring. A smoothly resolved return (`refund` completed without dispute) is a legitimate service-recovery moment: one no-sell "did the resolution work for you?" touch after resolution keeps the relationship alive, and a well-handled return is a known driver of the second purchase in return-heavy categories (fashion especially).

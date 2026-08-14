---
name: ecommerce
display_name: E-commerce (D2C / online retail)
funnel: [session_start, view_item_list, view_item, add_to_cart, begin_checkout, add_payment_info, purchase]
conversion_events: [purchase]
activation_definition: First purchase completed within 30 days of first session.
churn_signal: No session for 45 days after at least one purchase.
pattern_priorities:
  abandoned-cart: P0
  browse-abandonment: P0
  post-purchase: P0
  winback: P0
  welcome-onboarding: P1
  replenishment: P1
  back-in-stock: P1
  price-drop: P1
  upsell-cross-sell: P1
  progressive-profiling: P2
  loyalty: P2
  reactivation: P2
  referral: P2
  feedback-nps: P2
  anniversary: P2
  channel-opt-in: P2
  gamified-rewards: P2
typical_channels: [email, push, sms, whatsapp]
---

# E-commerce Playbook

High purchase frequency, short decision cycles (minutes to days), and a funnel that is almost fully observable in GA4's standard ecommerce events. Lifecycle value concentrates in three places: recovering proven intent (cart/browse abandonment), turning first purchase into second purchase (post-purchase), and reviving lapsed buyers (winback). Email is the workhorse; push and SMS earn their place on time-sensitive triggers only.

## Canonical funnel

| Step | Expected event | Notes |
|---|---|---|
| Visit | `session_start` | |
| Browse category | `view_item_list` | |
| View product | `view_item` | Biggest volume; feeds browse-abandonment |
| Add to cart | `add_to_cart` | Typical largest drop-off is between here and checkout |
| Start checkout | `begin_checkout` | |
| Payment | `add_payment_info` | |
| Purchase | `purchase` | Must carry `value` and `items` params |

## Event expectations

**Must-have** (missing any of these blocks P0 journeys): `view_item`, `add_to_cart`, `purchase`.
**Nice-to-have** (unlocks depth/branches): `begin_checkout`, `add_to_wishlist`, `remove_from_cart`, `refund`, `add_payment_info`, item-level params (`item_id`, `price`, `item_category`), `cart_value`.

## Pattern priorities — rationale

- **abandoned-cart P0** — proven intent, highest ROI per message in the sector.
- **browse-abandonment P0** — 5–10× the volume of cart abandonment; needs `view_item` with item params.
- **post-purchase P0** — second purchase is the strongest LTV lever; also carries review/UGC asks.
- **winback P0** — repeat-purchase businesses lose most revenue silently here.
- **replenishment P1** — only for consumable categories; promote to P0 if the catalog is consumables.
- **channel-opt-in P2** — SMS/WhatsApp consent is the İYS-gated bottleneck for the highest-urgency sends; ask at the order moment (shipping updates), per the pattern's value-first rule.
- **gamified-rewards P2** — occasion-bounded only (seasonal peak, anniversary); the prize table is bounded by the brand incentive cap, and it never substitutes for the core revenue patterns above.
- **trial-conversion, payment-failure, feature-adoption — not applicable** (subscription/SaaS mechanics).

## Sector-specific timing & cadence

- Cart abandonment first touch: 1–4 hours (not minutes).
- Browse abandonment first touch: same day, 4–24 hours.
- Post-purchase: order/shipping messages are transactional; first marketing touch after delivery, not before.
- Winback threshold: 1.5–2× the median inter-purchase gap (compute from data on T1; ask on T3). **T2 where the gap is uncomputable** (aggregate data, no per-user order history): fall back to the `churn_signal` default and mark it as an assumption in the journey doc — never present the fallback as a computed value.

## Seasonality

- The retail calendar dominates: Black Friday / Nov–Dec peak, sale seasons, and market-specific occasions (TR: bayram, back-to-school) are the year's intent concentrations.
- Peak-season inbox competition is brutal — consider **stricter frequency caps in Nov–Dec**, not looser ones; every send competes with every other retailer's.
- Seasonal windows modify existing journeys (abandonment timing tightens, incentive policy may shift, framing goes seasonal) — they are not a separate journey type.
- Brand-fit filter before adopting a calendar moment: a luxury brand doing aggressive Black Friday countdowns damages positioning.
- Attributed revenue inflates during peaks because baseline demand is elevated — holdouts are the only honest read (see [measurement](../measurement.md)).

## Segmentation attributes that matter

RFM (recency, frequency, monetary), first vs repeat buyer, discount affinity (bought only on promo?), category affinity, average order value, channel consent set.

## Intake questions (sector-specific)

1. Are your products consumable/replenishable (supplements, cosmetics, food) or durable?
2. What is your rough repeat-purchase rate or median time between orders?
3. Do you run discounts, and what is the maximum incentive a journey may offer?
4. Is inventory data (stock levels, price changes) available to the CRM tool?
5. Which channels do you have consented audiences on today (email/push/SMS/WhatsApp), roughly how many each?

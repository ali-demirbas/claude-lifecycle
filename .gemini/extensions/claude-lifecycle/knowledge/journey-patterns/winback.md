---
name: winback
stage: winback
trigger_type: segment
required_events: [purchase, session_start]
optional_events: [subscription_cancel, refund, login, add_to_cart]
required_attributes: []
optional_attributes: [median_interpurchase_gap, ltv_tier, last_category, consent_age]
default_channels: [email, sms]
base_steps: 4
depth_range: [3, 6]
applicable_industries: [ecommerce, marketplace, saas, subscription-media, travel, fintech, insurance, edtech, mobile-app]
mutually_exclusive_with: [churn-prevention]
---

# Winback

Recover **lapsed customers** — users who generated revenue and have since gone quiet past a recency threshold. The threshold is not a fixed number of days: it is computed per business (ideally per category) from the median inter-purchase or inter-usage gap, so a weekly-grocery lapse and an annual-travel lapse are detected on their own clocks. Distinct from reactivation, which targets dormant users who never bought.

## Required-event signature

| Event | Role |
|---|---|
| `purchase` | Qualifies the audience (≥ 1 historical purchase) and is the success exit. History of timestamps also feeds the inter-purchase gap math. Without it, pattern is **blocked**. |
| `session_start` | Recency source — distinguishes "lapsed but still visiting" (product problem) from fully silent (attention problem). |
| `subscription_cancel` *(optional)* | Marks deliberate leavers; they need a changed-value message, not a "we miss you". |
| `refund` *(optional)* | Exclusion signal — refund-heavy lapsers are often lost for cause; win them back with service, not promos. |
| `median_interpurchase_gap` *(optional attr)* | Precomputed per user/category; enables per-user thresholds instead of one global clock. |

## Entry / exit

- **Entry:** ≥ 1 lifetime `purchase`, no `purchase` and no `session_start` for longer than the lapse threshold (default 2× median inter-purchase gap, floor 45 days; **T2-aggregate, where the median gap is uncomputable without per-user order history: use the playbook `churn_signal` default and mark it as an assumption in the journey doc** — the engine's rule, not a per-run judgment call), valid marketing consent. Entrants arrive either via the churn-prevention watch buffer (preferred — see [churn-prevention](churn-prevention.md)) or via direct lapse detection; never run winback and churn-prevention on the same user in the same window.
  - **Threshold refinement — percentile over multiplier, when the data supports it:** 2×-median is a reasonable single number, but inter-purchase-gap distributions are usually right-skewed, so one flat multiplier can misjudge both ends of the base — too early for a slower-but-loyal segment, too late for a fast-repeat one. Where a category has enough per-user history (a reasonable floor: ≥ 30 purchasers in the category), rank each user's current gap against that category's own observed gap distribution and use a percentile cutoff (e.g., the 75th–80th percentile) instead of a fixed multiplier — this adapts to the distribution's actual shape, not just its center (the same idea as RFM "dynamic quintile scoring" applied to one axis). Below that data floor, a percentile estimate is noise wearing a formula — fall back to 2×-median + the 45-day floor. This is what "per-user gap" means in the Branched depth row below; record which method computed the threshold in the journey doc's assumption notes.
- **Exclude:** refund or dispute open, consent older than ~2 years of silence — those users get a re-permission message first, not a promo blast (see [consent-and-quiet-hours.md](../compliance/consent-and-quiet-hours.md), journey-level rule 2).
- **Success exit:** `purchase` · **Window:** 30 days · **Re-entry:** once per 90 days, max 2 lifetime winback cycles — after that, sunset to list hygiene.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (3) | DQS < 40 or only required events | What's-new email → value reminder → single approved incentive. Email only, global threshold. |
| Standard (4–5) | DQS 40–69 | Adds SMS touch and `last_category` personalization; incentive gated on `ltv_tier`. |
| Branched (6) | DQS ≥ 70 + `subscription_cancel` or per-user gap | Splits deliberate cancellers (changed-value track) from passive lapsers (reminder track); per-user lapse clocks. |

In the branched shape, a known lapse reason sets the starting angle: where a cancellation-flow reason or a one-tap "why did you leave?" answer exists, start the sequence at the matching angle — price objection → the (policy-approved) incentive/down-sell step; missing feature → what's-new focused on that feature; competitive loss → differentiation and social proof. No signal → default order.

## Step blueprint (standard, 4 steps)

| # | Wait | Channel | Intent | Branch |
|---|------|---------|--------|--------|
| 1 | on entry | email | "Here's what changed since you left" — concrete product/catalog news, no discount | — |
| 2 | +5d | email | Personalized best-of tied to `last_category`; restate the original value proposition | — |
| 3 | +7d | sms | Short, direct value reminder with one link (respect 20:00–10:00 quiet hours, no Sundays) | if steps 1–2 not opened |
| 4 | +10d | email | Incentive, gated on `ltv_tier` and margin, flagged for user approval before launch | — |

## KPIs

| KPI | Type | Note |
|---|---|---|
| Winback rate | primary | purchases within window / journeys entered |
| Revenue per re-activated customer | secondary | compare against pre-lapse run rate, not against zero |
| Hard bounce + spam-complaint rate | guardrail | stale lists damage domain reputation for every other journey — this guardrail protects the whole portfolio |

## Common mistakes

- Using one fixed threshold (e.g. "90 days inactive") for every product — consumables and annual-cycle purchases lapse on clocks an order of magnitude apart; compute from the median gap.
- Leading with the deepest discount — it trains lapse-for-coupon behavior and anchors returning customers at the discounted price.
- Blasting multi-year-silent contacts — deliverability and İYS/GDPR risk; long-dormant segments get a re-permission step, not a campaign.

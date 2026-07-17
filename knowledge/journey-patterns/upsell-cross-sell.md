---
name: upsell-cross-sell
stage: revenue
trigger_type: segment
required_events: [purchase, session_start]
optional_events: [subscription_start, feature_used, view_item, add_to_wishlist, trial_end, login]
required_attributes: []
optional_attributes: [plan_type, ltv_tier, category_history, engagement_score, seat_utilization]
default_channels: [email, in-app]
base_steps: 3
depth_range: [3, 6]
applicable_industries: [ecommerce, saas, fintech, marketplace, subscription-media, edtech, insurance, mobile-app, travel]
---

# Upsell / Cross-Sell

Expansion revenue from **healthy** existing customers: plan or tier upgrades (SaaS, fintech, media) and adjacent-category purchases (commerce). The defining rule is the health gate — an at-risk or declining account never receives an upsell; it routes to churn-prevention instead. Upsell pressure on a shaky account accelerates exactly the churn it should be funding against.

## Required-event signature

| Event | Role |
|---|---|
| `purchase` | Qualifies the audience (existing revenue relationship) and is the success exit. In pure subscription businesses, `subscription_start` plays this role. |
| `session_start` | Feeds the engagement-health gate — the pattern is **blocked** without a recency/frequency signal, because the gate is mandatory, not advisory. |
| `feature_used` / `seat_utilization` *(optional)* | The best upsell triggers: usage approaching a plan limit is a concrete, honest reason to upgrade. |
| `view_item` / `add_to_wishlist` *(optional)* | Commerce affinity signals for cross-sell candidate selection. |
| `category_history` / `ltv_tier` *(optional attrs)* | Rank expansion candidates; high-LTV users may warrant a human touch instead of automation. |

## Entry / exit

- **Entry:** active revenue relationship, engagement health at or above the user's own baseline, and a **concrete expansion candidate** (usage near plan limit, high seat utilization, strong category affinity). No candidate → no entry; generic "upgrade!" sends are excluded by design.
- **Exclude:** declining usage (churn-prevention owns), open support ticket or refund, `payment_failed` unresolved, upsell message received in the last 30 days.
- **Success exit:** expansion `purchase` / plan upgrade · **Window:** 21 days · **Re-entry:** once per 90 days, and only with a new expansion candidate.

## Candidate selection

- **Life-event triggers from record changes:** where the business holds structured customer records (insurance policies, account profiles), a record CHANGE is a cross-sell signal behavioral data can't see — an address change implies a home/contents need, a new dependent implies health/life lines. These are among the few life events a company actually observes first-party; use them as entry candidates where they exist, and never infer life events from outside data.
- Choose cross-sell candidates by **lift over chance, not raw co-occurrence** — the strongest associations are not always top-sellers paired together. Rank candidates by lift × revenue impact.
- Fire only the top 1–2 affinities per user per purchase and park the rest; a queue of "also-boughts" is noise, not personalization.
- State the evidence tier of every affinity claim: computed-from-data > stated hypothesis > sector default.
- Where no transaction-level data exists, GA4 Path exploration + Segment overlap are the native fallback for surfacing affinities.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (3) | DQS < 40 or only required events | Email-only: candidate pitch → value case → proof. Health gate on session recency alone. |
| Standard (4–5) | DQS 40–69 | Adds in-app contextual step at the trigger moment; candidates ranked by `category_history`/`plan_type`. |
| Branched (6) | DQS ≥ 70 + `feature_used` or `seat_utilization` | Limit-driven upgrade track (usage math in the copy) vs affinity cross-sell track; high-`ltv_tier` accounts diverted to a human/sales touch. |

## Step blueprint (standard, 3 steps)

| # | Wait | Channel | Intent | Branch |
|---|------|---------|--------|--------|
| 1 | at trigger moment | in-app | Contextual: "you're at N% of your plan's X" or "completes what you bought" — shown where the limit/affinity is felt | — |
| 2 | +3d | email | The value case for that specific expansion, framed in the user's own usage numbers | if step 1 not acted on |
| 3 | +7d | email | Proof: case study, reviews of the target product/plan, plus trial or sample of the upgrade if one exists | — |

Incentive choice follows the CLV-tied rule: above the account's CLV threshold prefer a value-add (extended trial of one feature, priority support, early access) over a discount; below it, a capped modest discount (see intake incentive policy).

## KPIs

| KPI | Type | Note |
|---|---|---|
| Expansion conversion rate | primary | upgrades or cross-sell purchases within window / journeys entered |
| Expansion revenue per entrant | secondary | |
| Unsubscribe + downgrade rate of contacted users | guardrail | the failure mode of upsell isn't non-conversion, it's resentment — watch downgrades vs a holdout |
| Return rate on cross-sold items | guardrail | a spike means a wrong pairing, not a channel problem — fix the affinity, not the copy |

## Common mistakes

- Upselling declining accounts — the health gate exists because upsell pressure on an at-risk user is a churn trigger, not a revenue play.
- Pitching a generic upgrade instead of the specific trigger — "you hit 90% of your storage" converts; "unlock premium features" is noise.
- Running upsell in parallel with a save offer — a user simultaneously told "pay more" and "please don't leave, here's a discount" loses trust in both messages.

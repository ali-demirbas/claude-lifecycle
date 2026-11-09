---
name: upsell-cross-sell
stage: revenue
trigger_type: segment
required_events: [purchase, session_start]
optional_events: [subscription_start, plan_upgraded, order_delivered, feature_used, view_item, add_to_wishlist, trial_end, login, refund, support_ticket_opened, payment_failed, consent_withdrawn]
required_attributes: []
optional_attributes: [plan_type, ltv_tier, category_history, engagement_score, seat_utilization, usage_vs_limit, limit_reset_date, renewal_date, time_to_first_use]
default_channels: [email, in_app]
base_steps: 3
depth_range: [3, 6]
applicable_industries: [ecommerce, saas, fintech, marketplace, subscription-media, edtech, insurance, mobile-app, travel]
mutually_exclusive_with: []
journey_class: marketing
signal_sources: {purchase: authoritative, plan_upgraded: authoritative, subscription_start: authoritative, order_delivered: authoritative, session_start: behavioral, feature_used: behavioral, view_item: behavioral, add_to_wishlist: behavioral, seat_utilization: authoritative, usage_vs_limit: authoritative, limit_reset_date: authoritative, renewal_date: authoritative, engagement_score: inferred, refund: authoritative, support_ticket_opened: authoritative, payment_failed: authoritative, consent_withdrawn: authoritative}
insufficient_alone:
  - a purchase that hasn't plausibly been received and used yet
  - a co-purchase pair below the configured data-sufficiency thresholds
  - a single product view
  - a usage figure from client-side analytics rather than the metering system
exit_before_each_send: [purchase, plan_upgraded, refund, support_ticket_opened, payment_failed, consent_withdrawn]
reentry: {policy: after_cooldown, cooldown: P90D, on_duplicate_trigger: ignore}
measurement_default: holdout
instance_key: candidate_id
---

# Upsell / Cross-Sell

Expansion revenue from **healthy** existing customers: plan or tier upgrades (SaaS, fintech, media) and adjacent-category purchases (commerce). The defining rule is the health gate: an at-risk or declining account never receives an upsell; it routes to churn-prevention instead. Upsell pressure on a shaky account accelerates exactly the churn it should be funding against.

Three honesty rules sit next to the health gate. **Wait for use**: a complement is offered only once the first product has plausibly been received and used, never on the order confirmation's heels. **Name the free path**: when the need can be met without paying (the allowance resets, a free tier covers it, an included feature does the job), the message says so alongside the paid option. **Dates come from the system**: a limit-reset or renewal date appears in copy only when the billing or metering system supplies it; it is never estimated.

## Required-event signature

| Event | Source | Role |
|---|---|---|
| `purchase` | authoritative (order system) | Qualifies the audience (existing revenue relationship) and is the success exit. In pure subscription businesses, `subscription_start` / `plan_upgraded` play this role. |
| `session_start` | behavioral | Feeds the engagement-health gate: the pattern is **blocked** without a recency/frequency signal, because the gate is mandatory, not advisory. |
| `order_delivered` *(optional)* | authoritative (fulfillment system) | Starts the use clock for complement cross-sell. |
| `feature_used` / `seat_utilization` / `usage_vs_limit` *(optional)* | behavioral / authoritative / authoritative | The best upsell triggers: usage approaching a plan limit is a concrete, honest reason to upgrade. The figure quoted in copy comes from the metering system. |
| `limit_reset_date` / `renewal_date` *(optional attrs)* | authoritative (billing / metering system) | The only source for "your allowance resets on…" and renewal timing. |
| `view_item` / `add_to_wishlist` *(optional)* | behavioral | Commerce affinity signals for cross-sell candidate selection. |
| `category_history` / `ltv_tier` *(optional attrs)* | authoritative | Rank expansion candidates; high-LTV users may warrant a human touch instead of automation. |
| `refund` / `support_ticket_opened` / `payment_failed` *(optional)* | authoritative | Exclusions, re-checked before each send: a problem with what they already have comes before selling them more. |

### Not enough on its own

- **A purchase that hasn't plausibly been received and used yet:** offering the case before the phone arrives, or the refill before the first pack is opened, sells to an imagined user. Cross-sell waits for delivery plus a use period.
- **A co-purchase pair below the configured data-sufficiency thresholds:** two items bought together a handful of times is coincidence, not affinity. Below threshold, the recommendation falls back and is labelled (see Candidate selection).
- **A single product view:** one view is curiosity; affinity needs repeated views, a wishlist add, or purchase history.
- **A usage figure from client-side analytics rather than the metering system:** "you're at 92% of your plan" must be the number the bill will use.

## Entry / exit

- **Entry:** active revenue relationship, engagement health at or above the user's own baseline, and a **concrete expansion candidate**, read as any_of(`usage_vs_limit` near the plan limit (authoritative, metering system), `seat_utilization` high (authoritative), a complement to something already bought after `order_delivered` (authoritative) plus its use period). Unmeasurable is no candidate. For complements, the first product's `order_delivered` plus its use period (`time_to_first_use` per category, default 7 days, configurable) must have elapsed. No candidate → no entry; generic "upgrade!" sends are excluded by design.
- **Exclude:** declining usage (churn-prevention owns), open support ticket or refund on the first product, `payment_failed` unresolved, upsell message received in the last 30 days, negative-signal suppression per [consent-and-quiet-hours.md](../compliance/consent-and-quiet-hours.md) rule 4.
- **Success exit:** expansion `purchase` / `plan_upgraded` · **Window:** 21 days.
- **Instance key:** `candidate_id`, the expansion candidate (the plan being outgrown, or the anchor order a complement is paired with).
- **Checked before each send:** the success events for this candidate (`same_instance`; buying an unrelated item does not end a plan-upgrade instance), `refund` of the anchor order (`same_instance`), `support_ticket_opened` and `payment_failed` on the account (journey scope: any open ticket or failed payment stops every upsell instance), `consent_withdrawn` (channel-scoped: an email opt-out stops s2 and s3; the in-app step still renders unless in-product messages were turned off). A refund, ticket or payment failure ends the instance: the account is no longer healthy enough to sell to.
- **Re-entry:** once per 90 days, and only with a new expansion candidate. A repeated trigger for the same candidate while an instance is active is ignored.
- **Handoffs:** declining health mid-journey → [churn-prevention](churn-prevention.md), queued upsell sends cancelled; high-`ltv_tier` accounts → a human/sales touch instead of automated sends.

## Candidate selection

- **Life-event triggers from record changes:** where the business holds structured customer records (insurance policies, account profiles), a record CHANGE is a cross-sell signal behavioral data can't see: an address change implies a home/contents need, a new dependent implies health/life lines. These are among the few life events a company actually observes first-party; use them as entry candidates where they exist, and never infer life events from outside data.
- Choose cross-sell candidates by **lift over chance, not raw co-occurrence**: the strongest associations are not always top-sellers paired together. Rank candidates by lift × revenue impact.
- **Data sufficiency is configured, not assumed.** The computed ranking runs only after the brand sets `recommendation_thresholds` in its config, for these four measures:
  - `observation_period`: how much order history counts; usually at least one full seasonal cycle, shorter only for catalogues that turn over fast.
  - `min_sample_orders`: orders containing the anchor item in that period.
  - `min_pair_support`: orders containing both items.
  - `min_lift`: the minimum lift over chance, where lift is used to rank.
  There is no universal minimum. The right numbers depend on catalogue size, order volume and how noisy the pairs are. A practical way to set them: pick the smallest support at which the top pairs stay the same when the period is split in two halves, and keep a pair only if it holds in both. Until the brand sets them, the engine treats every computed pairing as unvalidated, uses the fallback below, and lists the thresholds as an open item.
- **When data is insufficient**, the candidate falls back, in this order: a curated pairing the merchandising team has approved, then the category's bestsellers. The journey records which method produced each recommendation (`computed`, `curated`, `bestseller`), and copy never claims "customers who bought this also bought" for a curated or bestseller pick.
- Fire only the top 1–2 affinities per user per purchase and park the rest; a queue of "also-boughts" is noise, not personalization.
- State the evidence tier of every affinity claim: computed-from-data > stated hypothesis > sector default.
- Where no transaction-level data exists, GA4 Path exploration + Segment overlap are the native fallback for surfacing affinities, labelled as hypotheses.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (3) | DQS < 40 or only required events | Email-only: candidate pitch → value case → proof. Health gate on session recency alone; candidates from the curated/bestseller fallback. |
| Standard (4–5) | DQS 40–69 | Adds in-app contextual step at the trigger moment; candidates ranked by `category_history`/`plan_type`, computed where the thresholds are met. |
| Branched (6) | DQS ≥ 70 + `feature_used` or `seat_utilization` | Limit-driven upgrade track (metered usage in the copy, free path named) vs complement cross-sell track (delivery + use clock); high-`ltv_tier` accounts diverted to a human/sales touch. |

## Step blueprint (standard, 3 sends)

| Node | When | Channel | Intent | Route |
|---|---|---|---|---|
| s1 | entry +0h | in_app | Contextual: "you're at N% of your plan's X" or "completes what you bought", shown where the limit or the first product is used. If a free path exists, it is named next to the paid one. Shown at the next session after the candidate qualifies, expires after 3d; s2 is anchored to s1's scheduled time and is never gated on the view | → s2 |
| s2 | s1 +3d | email | The value case for that specific expansion, framed in the user's own usage numbers from the metering system. A reset or renewal date appears only if the system supplies it | → s3 |
| s3 | s2 +7d | email | Proof: case study, reviews of the target product/plan, plus a trial or sample of the upgrade if one exists | → exit (completed) |

The success, refund, ticket and payment checks run before s2 and s3, so a user who upgraded, returned the first product or raised a ticket hears nothing more. For complements, `entry` is the moment the use period after delivery elapsed, not the purchase.

Incentive choice follows the CLV-tied rule: above the account's CLV threshold prefer a value-add (extended trial of one feature, priority support, early access) over a discount; below it, a capped modest discount (see intake incentive policy).

## Timing and channel fit

- In-app first because the reason to expand is felt in the product; email follows on the user's clock, in daytime, quiet hours per [consent-and-quiet-hours.md](../compliance/consent-and-quiet-hours.md).
- Limit-driven sends react to usage within a day; a "you're near your limit" message after the limit already reset is wrong twice.
- Complement sends wait for delivery + use; when no delivery event exists, see When data is missing.
- No email consent → s2 and s3 drop; the in-app step alone is a valid shallow version.

## Frequency and overlap

- **Worst path:** 3 sends in 10 days, 2 of them marketing email in a rolling 7 days.
- **Overlaps:** post-purchase (same trigger family), [churn-prevention](churn-prevention.md) and save offers, [trial-conversion](trial-conversion.md), [loyalty](loyalty.md).
- **Precedence:** never in parallel with a save offer: a user simultaneously told "pay more" and "please don't leave, here's a discount" loses trust in both messages, so churn-prevention wins and upsell is cancelled. Post-purchase service messages (delivery, setup help) go first; the complement waits for them.

## Measurement

- **Primary outcome:** expansion conversion (upgrade or complement purchase) within 21 days, vs holdout.
- **Design:** user/account-level holdout (default 10%). The control does not receive s1–s3; organic upgrade paths in the product stay available to both.
- **Routine communications both groups keep:** billing, usage-limit notices required by the product (a hard-limit warning is service), order and delivery messages.
- **Contamination risks:** in-product upgrade banners and on-site recommendation widgets reach the control; sales outreach to high-LTV accounts.
- **Low volume:** expansion is a minority outcome; small bases can measure whether the journey moves upgrades at all, not which track or pairing did. Recommendation-method comparisons (computed vs curated) need their own test.

## When data is missing

- **No `order_delivered`:** use purchase date + the category's typical delivery time + `time_to_first_use`, labelled as an estimate in the journey doc.
- **Thresholds not met:** curated pairing, then category bestsellers, labelled as such; never relaxed silently to make a computed claim.
- **No metered usage:** the limit-driven track doesn't run; usage numbers are never estimated from analytics.
- **No `limit_reset_date` / `renewal_date`:** copy names the free path without a date ("your allowance resets with your plan's cycle") only if that rule is documented; otherwise it omits timing entirely.
- **Health signal unmeasurable:** no entry. The health gate fails closed: an account that can't be shown healthy isn't sold to.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Expansion conversion rate | primary | upgrades or cross-sell purchases within window / journeys entered, vs holdout |
| Expansion revenue per entrant | secondary | split by recommendation method (computed / curated / bestseller) |
| Unsubscribe + downgrade rate of contacted users | guardrail | the failure mode of upsell isn't non-conversion, it's resentment: watch downgrades vs a holdout |
| Return rate on cross-sold items | guardrail | a spike means a wrong pairing, not a channel problem: fix the affinity, not the copy |

## Common mistakes

- Upselling declining accounts: the health gate exists because upsell pressure on an at-risk user is a churn trigger, not a revenue play.
- Pitching a generic upgrade instead of the specific trigger: "you hit 90% of your storage" converts; "unlock premium features" is noise.
- Offering the complement before the first product has arrived: it reads as a sales script, not a recommendation.
- Hiding the free path: a user who later finds out the limit would have reset next week for free remembers the upsell as a trick.
- Inventing a reset or renewal date to create urgency.
- Ranking pairs on a handful of co-purchases and presenting them as "customers also bought".
- Running upsell in parallel with a save offer.

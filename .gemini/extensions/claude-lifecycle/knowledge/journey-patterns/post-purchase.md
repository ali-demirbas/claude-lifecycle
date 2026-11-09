---
name: post-purchase
stage: retention
trigger_type: event
required_events: [purchase]
optional_events: [refund, order_cancelled, review_submitted, low_rating_submitted, support_ticket_opened, view_item, add_to_cart, consent_withdrawn]
required_attributes: []
optional_attributes: [delivery_date, order_category, repurchase_period_days, is_first_purchase, is_guest_checkout, support_ticket_open]
default_channels: [email, push]
base_steps: 4
depth_range: [3, 7]
applicable_industries: [ecommerce, marketplace, travel]
mutually_exclusive_with: []
journey_class: marketing
signal_sources:
  purchase: authoritative
  delivery_date: authoritative
  refund: authoritative
  order_cancelled: authoritative
  review_submitted: authoritative
  low_rating_submitted: authoritative
  support_ticket_opened: authoritative
  repurchase_period_days: inferred
  consent_withdrawn: authoritative
  link_click: engagement
insufficient_alone:
  - a carrier delivery estimate not confirmed by the system of record
  - an order placed but not yet accepted or paid
  - a category-average repurchase period with no evidence for this category
exit_before_each_send: [purchase, order_cancelled, refund, support_ticket_opened, consent_withdrawn]
reentry: {policy: each_trigger, on_duplicate_trigger: restart}
instance_key: order_id
measurement_default: holdout
---

# Post-Purchase

Turn one purchase into a relationship: onboarding onto the product bought, a well-timed review/UGC ask, and a bridge to the second purchase. Sits **on top of, never inside** the transactional layer: order and shipping confirmations stay consent-exempt only while they carry zero promotional content (see [consent-and-quiet-hours.md](../compliance/consent-and-quiet-hours.md)); everything in this pattern is marketing and requires marketing consent.

## Required-event signature

| Event | Source | Role |
|---|---|---|
| `purchase` | authoritative | Trigger (the order accepted by the system of record) and, for the second order, success exit. Must carry `items` for category-aware content. |
| `order_cancelled` / `refund` *(optional)* | authoritative | Kill switch. A cancelled or fully reversed first purchase ends the instance; any refund stops review and sell asks at once. |
| `review_submitted` *(optional, custom)* | authoritative | No analytics standard exists; track it to measure the review step and stop re-asking. |
| `low_rating_submitted` *(optional, custom)* | authoritative | A review or rating at or below a configurable threshold (default 2 of 5), from any source: review form, in-app rating, CSAT. Routes to service recovery. |
| `support_ticket_opened` / `support_ticket_open` *(optional)* | authoritative | Kill switch alongside refund: an open ticket on the order halts sell and review asks the same way. Without it, the exclude rule below can't be evaluated; treat it as a required signal from the support system, not a nice-to-have. |
| `delivery_date` *(optional attr)* | authoritative | The single highest-value attribute here: every early step anchors to delivery, not checkout. Read it from the system of record's delivery confirmation, not a carrier estimate. Without it, fall back to purchase date + conservative offsets. |
| `repurchase_period_days` *(optional attr)* | inferred | The product's natural repurchase period per category; anchors the second-purchase bridge. |
| `is_first_purchase` *(optional attr)* | authoritative | First-time buyers get the trust-building track; repeat buyers skip straight to the bridge. |

### Not enough on its own

- **A carrier estimate:** an expected delivery date or an "out for delivery" scan is not delivery. Tips and review asks timed to it land before the item does.
- **An order placed but not yet accepted:** payment can still fail and stock can still be short; the instance opens on the accepted order.
- **A category-average repurchase period with no evidence:** a guessed period mistimes the bridge for the whole category; default to the fallback below and mark it as an assumption.

## Entry / exit

- **Entry:** `purchase` accepted by the system of record, marketing consent on ≥ 1 channel (transactional confirmations happen regardless, outside this journey).
- **Exclude:** refund initiated, open support ticket on the order, any open complaint (portfolio-wide negative-signal override).
- **Success exit:** second `purchase` · **Window:** `repurchase_due` +14d (default 44 days from purchase when no repurchase period is known: 30-day default period + 14; configurable).
- **Checked before each send:** a later `purchase` (success; it also restarts the journey on the new order), and, for this instance's order only (`instance_key: order_id`): `order_cancelled`, `refund`, `support_ticket_opened` on the order. A refund or ticket on an older order doesn't stop this one (an open complaint still applies through the portfolio-wide override). `consent_withdrawn` is scoped to that send's channel: an email unsubscribe stops s1–s3, and s4 still goes by push where push is consented. A low rating is handled by d1/d2 before each sell, not as a journey-wide exit, so it can't silently filter who gets the review request. A first purchase cancelled or fully reversed ends the instance without a further touch.
- **Re-entry:** per purchase, subject to portfolio frequency caps.
- **Repeated trigger while active:** a newer order restarts the instance on that order; the older instance exits and its queued sends are dropped (newest order wins).
- **Handoffs:**
  - `low_rating_submitted` or `support_ticket_opened` → service recovery (the support/human resolution path; [feedback-nps](feedback-nps.md)'s detractor route where that journey runs); queued sell sends suppressed. A low rating is never followed by a sell, and it is never used to decide who gets the review request (no review gating).
  - `refund` resolved without dispute → one no-sell "did the resolution work for you?" touch belongs to the service path, not to this journey.

Anchor (declared in `time_anchors`): `repurchase_due` = purchase + `repurchase_period_days` (default 30 days when unknown), never earlier than `s3 +7d`.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (3) | DQS < 40 or only `purchase` | Care/usage tips → review ask → generic second-purchase nudge. Purchase-date anchors. |
| Standard (4–5) | DQS 40–69 | Delivery-anchored early steps, `order_category` cross-sell, refund and ticket kill switches, low-rating route. |
| Branched (6–7) | DQS ≥ 70 + `is_first_purchase` and `review_submitted` | First-buyer trust track vs repeat-buyer bridge track; reviewers skip the ask and get a UGC/referral step instead. |

## Step blueprint (standard, 4 sends)

**Time anchors.** `delivery_date: entry +1d … +14d` (configurable per category), read from the system of record's delivery confirmation at send time; `repurchase_due` as declared above.

| Node | When | Channel | Intent | Route |
|---|---|---|---|---|
| s1 | delivery_date +2d | email | Usage / care / getting-the-most tips for the item bought; pure value, no sell | → s2 |
| s2 | s1 +5d | email | Review/UGC ask: one item, one click, honest framing | → d1 |
| d1 | s2 +5d | — | Decision on `low_rating_submitted` for this order (authoritative review/rating record) between entry and s2 +5d | occurred → handoff service recovery · not_occurred → s3 · unmeasurable → s3 |
| s3 | s2 +5d | email | Cross-sell complements to `order_category`, framed as completing the purchase | → d2 |
| d2 | repurchase_due -1d | — | Decision on `low_rating_submitted` for this order (authoritative review/rating record) between s2 +5d and repurchase_due -1d | occurred → handoff service recovery · not_occurred → s4 · unmeasurable → s4 |
| s4 | repurchase_due +0d | email (push only for users opted into product-update pushes; a 30-day-old purchase is not a recent trigger under push.md) | Second-purchase bridge: replenish, the next step in the category, or new-arrivals deeplink | → end |

s1 is skipped when nothing useful is recorded for the item (no setup, care or usage content); a tips email with no substance is a promotion in disguise. A low rating stops every **sell** step (d1 before s3, d2 before s4) and hands the user to service recovery. It never decides who receives the review request: s2 goes to every eligible buyer whatever their earlier private rating, because asking only the people expected to be positive (review gating) breaks most review platforms' terms and consumer-protection rules in several markets. Eligibility for s2 rests on operational facts only (delivery confirmed, no refund, cancellation or open ticket on the order); confirm the platform's own rules for those too. Neither decision reads a click: a click on s2's review link is not a submitted review, and `review_submitted` comes from the review system.

For guest checkout (`is_guest_checkout`): fold one account-creation nudge into s1 or s2, framed on real value the account unlocks (order tracking, saved details for a faster next checkout, backdated loyalty points if a program exists), never a bare "register now." Ask once; if declined, drop it, and a second guest purchase in the same 90-day window doesn't get asked again.

## Timing and channel fit

- **Clock:** user local time; email avoids 00:00–06:00, push holds through 22:00–09:00.
- **Anchors:** s1 waits for confirmed delivery; s4 waits for the product's natural repurchase period, set per category (consumables weeks, durables months) and changed only with repeat-purchase interval evidence. When the period is shorter than the early steps, s4 waits until `s3 +7d`.
- **Channel fit:** email for tips, the review ask and the cross-sell, which need room; push for the bridge, a short deeplink. No SMS by default; post-purchase lists are a business's best and the least worth burning.
- **Fallback:** no push consent → s4 goes by email at the same anchor.

## Frequency and overlap

- **Worst path, rolling 7 days:** s1 and s2 are 5 days apart, and s3 follows s2 by 5 days, so any 7-day window holds at most 2 emails; s4 lands later. Low load on its own, but it runs right after checkout, when order and shipping messages are already arriving.
- **Overlaps:** replenishment (owns consumables' reorder; the bridge steps aside for an item replenishment covers), feedback-nps (a survey on the same order replaces the review ask), welcome/onboarding for first-time buyers who also just signed up, loyalty.
- **Precedence:** service recovery and support paths outrank everything here; transactional messages are never delayed by it. On a cap breach, defer the cross-sell and the bridge (re-checked against refunds and tickets when released); the tips email may go first.

## Measurement

- **Primary outcome:** second `purchase` within the success window.
- **Design:** journey-level holdout, default 10%, randomized at entry and sticky per person across orders. The control receives none of this journey's marketing sends; it still gets every transactional order, shipping and delivery message.
- **Routine communications both groups keep:** transactional order messages, newsletters, any review-request system the platform runs on its own (list it; if it runs, the review-ask lift is measured against it).
- **Contamination:** a replenishment or winback send reaching the control in the window; an external review platform's automatic request.
- **Low volume:** second purchases are slow; a small store may need a full quarter of entrants. A short read that shows nothing is unmeasured, not a failure.

## When data is missing

- **No `delivery_date`:** anchor s1 at purchase +7d (longer for slow-shipping categories) and mark it as an assumption.
- **No `repurchase_period_days`:** use the 30-day default for s4, mark it as an assumption, and list the per-category interval analysis as an open item.
- **No `low_rating_submitted` or ticket signal:** d1 resolves as unmeasurable and the path continues, but the portfolio must carry the warning that low raters will still receive sells; add the signal to the tracking plan as P0.
- **No `refund` or `order_cancelled`:** the kill switch can't fire; restrict cross-sell to orders past the return window, or don't run s3.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Incremental second-purchase rate | primary | second purchase within window, exposed vs holdout; compare first-buyer vs repeat-buyer cohorts |
| Review submission rate | secondary | requires `review_submitted` tracking |
| Repeat purchase within 90 days | secondary | long-horizon view beyond the success window |
| Unsubscribe rate per send | guardrail | post-purchase lists are your best; burning them costs every future journey |

## Common mistakes

- Asking for a review before the item arrives; anchor on confirmed delivery. A checkout-date offset regularly lands the ask mid-shipping and earns 1-star logistics reviews.
- Slipping promos into the order-confirmation email to dodge consent; it turns the message into marketing and forfeits its transactional status.
- Cross-selling to someone with an open refund or support ticket; the kill-switch check must run before each send, not only at entry.
- Answering a low rating with a cross-sell; it goes to service recovery.
- Review gating: sending the public review request only to people with a positive private rating, or holding it back from people with a negative one. The request goes to every eligible buyer or to none.
- Timing the bridge on one fixed day count for every category; a consumable and a durable repurchase on very different clocks.
- Treating every return as a lost relationship. The kill switch stops *selling*, not caring: a smoothly resolved return is a legitimate service-recovery moment, and a well-handled return is a known driver of the second purchase in return-heavy categories (fashion especially). That touch runs on the service path, no sell attached.

---
name: ga4-recommended-events
purpose: Map GA4 recommended/standard events to lifecycle stages for lifecycle-map
stages: [acquisition, activation, engagement, revenue, retention, winback]
---

# GA4 Recommended Events → Lifecycle Stage Map

`lifecycle-map` looks events up here first. Stage meanings: **acquisition** (getting in), **activation** (first value moment), **engagement** (ongoing use), **revenue** (money or hard conversion intent), **retention** (signals of coming back), **winback** (only ever assigned by absence — no event maps here directly).

## Universal / cross-vertical

| GA4 event | Stage | Intent weight | Notes |
|---|---|---|---|
| `first_visit` | acquisition | low | |
| `session_start` | acquisition | low | Recency source for winback math |
| `sign_up` | activation | high | Primary activation event when no vertical event exists |
| `login` | engagement | medium | Frequency feeds engagement scoring |
| `search` | engagement | medium | Query param unlocks interest segments |
| `share` | engagement | high | Referral journey signal |
| `select_content` / `select_item` | engagement | low | |
| `view_item` | engagement | medium | Promotes to revenue-intent in commerce contexts |
| `generate_lead` | acquisition | high | Lead capture — the entry of [lead-nurture](../journey-patterns/lead-nurture.md); revenue comes later |
| `purchase` | revenue | high | Canonical conversion; must carry `value`, `currency`, `items` |
| `refund` | revenue | high (negative) | Excludes users from post-purchase marketing |
| `join_group` | retention | medium | Community signal |
| `app_remove` (Android) | winback-adjacent | high (negative) | Only reachable via email/SMS afterwards |

## Commerce funnel

| GA4 event | Stage | Intent weight |
|---|---|---|
| `view_item_list` | engagement | low |
| `view_promotion` / `select_promotion` | engagement | low |
| `add_to_wishlist` | revenue-intent | medium |
| `add_to_cart` | revenue-intent | high |
| `view_cart` | revenue-intent | medium |
| `remove_from_cart` | revenue-intent | medium (negative) |
| `begin_checkout` | revenue-intent | very high |
| `add_shipping_info` | revenue-intent | very high |
| `add_payment_info` | revenue-intent | very high |

## Games / app verticals

| GA4 event | Stage | Intent weight |
|---|---|---|
| `tutorial_begin` | activation | medium |
| `tutorial_complete` | activation | high |
| `level_up` / `unlock_achievement` | engagement | medium |
| `earn_virtual_currency` | engagement | low |
| `spend_virtual_currency` | revenue-intent | medium |
| `post_score` | engagement | medium |

## SaaS / subscription (common custom conventions — not GA4-official but widely used)

| Event (convention) | Stage | Intent weight |
|---|---|---|
| `trial_start` | activation | high |
| `trial_end` | revenue-intent | very high |
| `subscription_start` / `subscribe` | revenue | high |
| `subscription_cancel` | winback-adjacent | high (negative) |
| `payment_failed` | revenue (protect) | very high |
| `feature_used` (with `feature` param) | engagement | medium |
| `invite_sent` / `invite_accepted` | engagement | high |

`revenue-intent` counts toward the revenue stage for coverage, but a journey may not claim a revenue KPI unless a true revenue event (`purchase`, `subscription_start`) exists as its success exit. Exception: in lead-gen business models where revenue closes offline, `generate_lead` may stand in as the measurable conversion — while still anchoring the **acquisition** stage, not revenue coverage.

## Fintech (banking, trading, payments — common custom conventions, matches `knowledge/industries/fintech.md`'s funnel)

| Event (convention) | Stage | Intent weight | Notes |
|---|---|---|---|
| `kyc_start` | activation | medium | Identity-verification funnel entry |
| `kyc_complete` | activation | high | Primary activation event — fintech.md: activation = `kyc_complete` within 7 days of `sign_up` |
| `kyc_rejected` | winback-adjacent | high (negative) | Hard block — an unverified user cannot transact |
| `first_deposit` | revenue | high | Canonical conversion; carries `value`, `currency` — first of fintech.md's two funnel conversion events |
| `first_transaction` | revenue | high | Second canonical conversion event in fintech.md's funnel |
| `payment_failed` | revenue (protect) | very high | Same protect-family treatment as SaaS's `payment_failed` |
| `withdrawal` | engagement | medium | A **full-balance** withdrawal is fintech.md's own hard churn signal — treat as winback-adjacent (negative) when the amount equals the account balance; a partial withdrawal is ordinary account activity |
| `card_activated` | activation | medium | Card-issuing fintechs' equivalent of first product use |
| `loan_applied` / `trade_executed` | revenue-intent | high | Lending/investing sub-verticals' core pre-conversion action — not itself a true revenue event |

## Mobile subscription platforms (RevenueCat / App Store Server Notifications — not GA4-official, real webhook/event names)

Mobile subscription apps rarely emit GA4's convention events natively; the subscription state machine lives in RevenueCat or the platform's own server-to-server notifications. Map these to the same stage vocabulary above before scoring DQS or arming journeys — don't assume `trial_start`/`subscription_start` exist verbatim just because the app is a subscription business.

| Real event (RevenueCat webhook) | Maps to | Stage |
|---|---|---|
| `INITIAL_PURCHASE` (trial) | `trial_start` | activation |
| `INITIAL_PURCHASE` (paid) / `NON_RENEWING_PURCHASE` | `subscription_start` | revenue |
| `RENEWAL` | repeat `subscription_start`-class success exit for renewal-cadence journeys | retention |
| `CANCELLATION` | `subscription_cancel` | winback-adjacent |
| `UNCANCELLATION` | reverses a pending cancellation within the grace window — the save-offer success exit for churn-prevention, not a new subscription | revenue (recovered) |
| `BILLING_ISSUE` | `payment_failed` | revenue (protect) |
| `EXPIRATION` | trial or subscription lapsed with no recovery | winback-adjacent |
| `PRODUCT_CHANGE` | plan/tier change | engagement |

App Store Server Notifications V2 (when RevenueCat isn't in the stack) use their own `notificationType` vocabulary instead (`SUBSCRIBED`, `DID_RENEW`, `EXPIRED`, `DID_FAIL_TO_RENEW`, `GRACE_PERIOD_EXPIRED`, `REFUND`, `REVOKE`) — same mapping logic applies, confirm the exact source (RevenueCat vs. direct App Store/Play Billing notifications) before assuming either vocabulary.

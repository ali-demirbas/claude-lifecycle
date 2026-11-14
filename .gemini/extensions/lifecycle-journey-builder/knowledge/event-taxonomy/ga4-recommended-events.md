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

## Lifecycle control signals (custom conventions used by the journey patterns)

| Event (convention) | Stage | Intent weight |
|---|---|---|
| `consent_withdrawn` (per channel: email unsubscribe, push opt-out, SMS/İYS revocation) | control (stops sends) | very high (negative) |
| `order_cancelled` | revenue (negative) | high |
| `low_rating_submitted` (rating at or below a configurable threshold) | retention (risk) | high (negative) |
| `item_discontinued` (withdrawn from the catalogue, not out of stock) | control | medium |
| `stock_alert_unsubscribe` | control | medium (negative) |
| `price_increase` | control | medium |
| `lead_qualified` (sales-ready, from the CRM of record) | acquisition → handoff | high |
| `support_ticket_opened` / `support_case_opened` (same signal; use whichever the support system emits) | control (pauses marketing) | high (negative) |
| `cancellation_intent` (cancel flow started, not completed) | retention (risk) | very high (negative) |
| `csm_owner_assigned` | control (human owner takes over) | medium |
| `continue_later_selected` / `help_declined` | control | medium |
| `feature_opened` (product event, not a message click) | engagement | medium |
| `in_app_shown` / `profile_question_dismissed` | control | low |
| `usage_recovered` (derived: usage back above the account's own baseline, computed, never a falling risk score) | retention | high |
| `coverage_ended` (insurance: the policy's cover actually stopped) | winback-adjacent | high (negative) |
| `email_delivered` (ESP delivery record; the base for "silence" in unengaged-sunset) | control | low |
| `access_restored` (after a payment-related suspension) | revenue (protect) | high |

`incentive_ledger` and `sender_suppression` are records, not events: a per-person log of comeback incentives already issued, and the sender-side suppression list. A sender-side suppression is not a consent withdrawal and never stops transactional or service messages.

`activation_event` and `account_activated` in pattern files are placeholders for the sector's own activation event (`knowledge/industries/<sector>.md` `activation_definition`); map them per account, never emit them literally.

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

## App events (GA4 for Firebase: automatically collected and recommended app events)

`noise` means the event says the app ran or a message arrived, not that the user did anything worth a journey decision: it is excluded from event diversity and never used as a trigger or a success exit.

| GA4 event | Stage | Intent weight | Notes |
|---|---|---|---|
| `first_open` | acquisition | low | App install-to-first-launch; the app counterpart of `first_visit` and the clock start for mobile activation windows |
| `app_update` | — | noise | Version change; useful only for release diagnostics |
| `screen_view` | — | noise | App counterpart of `page_view` |
| `user_engagement` | — | noise | Foreground-time heartbeat; recency at most, never a behavior |
| `notification_receive` / `notification_open` | — | message metric | Delivery and open records of a push: they measure the message, not product behavior. Usable for message-engagement reporting (channel-opt-in's post-grant health, unengaged-sunset's push measurability), never as a product signal; excluded from event diversity |
| `in_app_purchase` | revenue | high | Store purchase (automatically collected on Android and iOS); carries `value`, `currency`, `product_id`; a true revenue event |
| `app_store_subscription_convert` | revenue | high | Trial converted to paid through the store; maps to `subscription_start` |
| `app_store_subscription_renew` | retention | high | Store renewal; the success exit for renewal-cadence journeys |
| `app_store_subscription_cancel` | retention | high (negative) | Store-side cancellation; maps to `subscription_cancel` (winback-adjacent, stage `retention` + `"negative": true`) |
| `ad_impression` | — | low | Ad shown in an ad-funded app; monetization reporting (ad revenue), not a user intent signal and never a journey trigger |

## Games / app verticals

| GA4 event | Stage | Intent weight |
|---|---|---|
| `tutorial_begin` | activation | medium |
| `tutorial_complete` | activation | high |
| `level_start` | engagement | low |
| `level_end` (with `success`) | engagement | medium |
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
| `subscription_renewed` | retention | high |
| `subscription_expired` (paid access actually ended) | winback-adjacent | high (negative) |
| `subscription_reactivated` | retention | high |
| `subscription_pause` / `subscription_resumed` | retention | medium |
| `plan_changed` (with `from_plan`/`to_plan`) | revenue / retention | medium |
| `renewal_quote_issued` (insurance, contracts) | retention | high |
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

## Insurance (common custom conventions, matches `knowledge/industries/insurance.md`'s funnels)

| Event (convention) | Stage | Intent weight | Notes |
|---|---|---|---|
| `quote_started` | revenue-intent | high | Quote funnel entry; a completed, priced quote with no purchase is the quote-abandonment trigger |
| `policy_purchased` | revenue | high | Canonical conversion; carries `value` (premium), `currency`, `product_line`, `payment_plan` |
| `app_activated` / `portal_registered` | activation | high | insurance.md's activation event (within 14 days of `policy_purchased`) |
| `claim_filed` | retention | high | Service moment; pauses marketing to that policyholder while the claim is open |
| `claim_resolved` (with `outcome`) | retention | high | `outcome` (paid / partial / rejected) sets every post-claim message; a rejected claim is a negative signal |
| `premium_payment_failed` | revenue (protect) | very high | Same protect-family treatment as `payment_failed` |
| `premium_payment_succeeded` | revenue (protect) | high | Recovery / success exit for premium dunning |
| `policy_renewal_due` (attribute `renewal_date`) | retention | high | Time-based cohort entry for renewal-reminder, not a behavior |
| `policy_renewed` | revenue | high | The annual conversion event (`conversion_events`); the renewal success exit |
| `policy_lapsed` | retention | high (negative) | Winback-adjacent (stage `retention` + `"negative": true`); the sector's core churn definition |
| `coverage_ended` | retention | high (negative) | See the control signals above; cover actually stopped |

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

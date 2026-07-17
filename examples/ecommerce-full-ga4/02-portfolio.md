# Lifecycle Journey Portfolio — Moda Nova

**Generated:** 2026-07-12 · **Industry:** ecommerce · **Data tier:** T1 · **DQS:** 74/100
**Goal weighting:** revenue-first (from intake)

## 1. Executive summary

Moda Nova's GA4 property carries the full ecommerce funnel (11 meaningful events, DQS 74 → **branched** class), so all four P0 patterns generate at full depth with behavioral branches. Nine journeys were generated across five lifecycle stages; two patterns are blocked on missing data (item-level CRM params, inventory feed) and go to the tracking plan. Cart recovery (`ecom-abandoned-cart-01`) is the launch-first journey: proven intent, ≈ 650 messageable entrants/week, and the shortest path to measurable revenue.

## 2. Portfolio table

| # | Journey | ID | Stage | Priority | Depth | Channels | Status |
|---|---------|----|----|----------|-------|----------|--------|
| 1 | Cart Recovery | `ecom-abandoned-cart-01` | Revenue | P0 | 8 steps, branched | email+push | ✅ generated → [doc](03-journey-cart-recovery.md) |
| 2 | Browse Abandonment | `ecom-browse-abandonment-01` | Revenue | P0 | 4 steps | email+push | ✅ generated |
| 3 | Post-Purchase Care | `ecom-post-purchase-01` | Retention | P0 | 7 steps, branched | email+push | ✅ generated |
| 4 | Winback — Lapsed Buyers | `ecom-winback-01` | Winback | P0 | 5 steps | email | ✅ generated |
| 5 | Welcome & First Purchase | `ecom-welcome-onboarding-01` | Activation | P1 | 6 steps | email | ✅ generated |
| 6 | Cross-Sell — Adjacent Category | `ecom-upsell-cross-sell-01` | Revenue | P1 | 4 steps | email | ✅ generated |
| 7 | NPS & Service Recovery | `ecom-feedback-nps-01` | Retention | P2 | 3 steps | email | ✅ generated¹ |
| 8 | 3rd-Purchase Milestone | `ecom-milestone-01` | Retention | P2 | 2 steps | email | ✅ generated² |
| 9 | Signup Anniversary | `ecom-anniversary-01` | Retention | P2 | 1 step | email | ✅ generated |
| 10 | Replenishment — Basics line | `ecom-replenishment-01` | Revenue | P1 | — | — | 🔒 blocked — missing `items` params in CRM sync |
| 11 | Back in Stock | `ecom-back-in-stock-01` | Revenue | P1 | — | — | 🔒 blocked — missing `item_back_in_stock` (no inventory feed) |

¹ `survey_response` is not in GA4; the CRM's own survey block emits it — flagged as an assumption, journey is CRM-native.
² `milestone_reached` is computed by CRM counting logic over synced `purchase` events (3rd purchase); no new instrumentation needed.

Price-drop shares the inventory/price-feed dependency and is folded into the back-in-stock tracking-plan item rather than listed separately. Winback runs email-only because no SMS audience is consented. Referral and loyalty are not in scope: no `invite_sent` / `earn_virtual_currency` events and no loyalty program exists (intake).

## 3. Lifecycle stage coverage

| Stage | Journeys | Coverage verdict |
|---|---|---|
| Acquisition | — | not applicable — the engine works from identified users onward; acquisition is owned by paid/organic channels |
| Activation | `ecom-welcome-onboarding-01` | covered |
| Engagement | — | gap — engagement events exist (`view_item`, `add_to_wishlist`) but the wishlist-consuming journeys (back-in-stock, price-drop) are feed-blocked; browse-abandonment covers the highest-value engagement→revenue path from the Revenue row. Unblocked by the inventory/price feed. |
| Revenue | `ecom-abandoned-cart-01`, `ecom-browse-abandonment-01`, `ecom-upsell-cross-sell-01` | covered |
| Retention | `ecom-post-purchase-01`, `ecom-feedback-nps-01`, `ecom-milestone-01`, `ecom-anniversary-01` | covered |
| Winback | `ecom-winback-01` | covered |

## 4. Conflict & frequency review

**Shared triggers / audiences — who wins:**

- **Cart Recovery vs Browse Abandonment:** overlapping audience (viewers who add to cart). Cart Recovery wins; Browse Abandonment excludes users with a non-empty cart or active in `ecom-abandoned-cart-01`.
- **Cart Recovery vs Welcome:** a new signup who abandons a cart would be in both. Revenue P0 wins — Welcome pauses its marketing steps while the cart journey is active and resumes after exit.
- **Any revenue journey vs Post-Purchase:** `purchase` is the success exit of all revenue journeys and the entry of Post-Purchase — sequential by construction, no overlap.
- **Winback:** excludes anyone with a session in the last 60 days — cannot co-occur with the browse/cart journeys.
- **P2 garnish journeys (NPS, Milestone, Anniversary):** engine rule — their sends are **deferred while the user is in an active P0 revenue journey**, released after exit. This is a cut, not a note (see math below).

**Worst-case weekly message math** (caps per [consent-and-quiet-hours.md](../../knowledge/compliance/consent-and-quiet-hours.md): email 4/wk, push 1/day & 5/wk, combined 8/wk):

| Scenario: one user, worst week | email | push | total |
|---|---:|---:|---:|
| Cart Recovery worst path (steps 1, 4, 5 *or* 6, 8 + one of 2/3, 7) | 4 | 2 | 6 |
| + P2 garnish (deferred while cart journey active) | +0 | +0 | 6 |
| **Worst case vs caps** | **4 / 4** | **2 / 5** | **6 / 8** |

Email lands exactly at cap with zero headroom — therefore any future email journey must exclude users active in Cart Recovery, and the deferred-P2 rule above is mandatory, not advisory. Without that rule the worst case would be 5 emails/week (breach).

## 5. Launch roadmap

1. **Week 1 — `ecom-abandoned-cart-01`:** highest ROI per message, copy already reviewed, 10% holdout from day one.
2. **Week 1 — `ecom-post-purchase-01`:** protects the ≈ 722 purchases/month already happening; no conflict with cart recovery.
3. **Month 1 — `ecom-browse-abandonment-01`:** launch after cart-recovery cap behavior is observed for 2 weeks (it shares the message budget and has 6–7× the audience).
4. **Month 1 — `ecom-welcome-onboarding-01`:** 5,830 signups/90d deserve a first-purchase bridge; pauses for cart journey by rule.
5. **Month 1 — `ecom-winback-01`:** threshold computed from purchase timestamps (median inter-purchase gap × 1.5–2).
6. **Later — `ecom-upsell-cross-sell-01`:** needs 4 weeks of CRM-side category history before the health gate is meaningful.
7. **Later — NPS, Milestone, Anniversary:** garnish after the core is stable.
8. **Tracking plan — replenishment + inventory feed:** unblocks journeys 10–11 (and price-drop).

## 6. Tracking plan summary

2 blocked journeys. Top missing items by unlocked value:

1. **`items` params in the CRM sync** (P0 in plan) — unblocks `ecom-replenishment-01` for the basics line and per-item winback depth.
2. **Inventory/price feed → `item_back_in_stock`, `price_drop`** (P1) — unblocks `ecom-back-in-stock-01` and price-drop against 18,750 wishlist adds/90d.
3. **RFM attributes in CRM** (P1) — no journey blocked, but upgrades winback/cross-sell segmentation and adds up to +6 DQS (attributes component 9 → 13–15).

---
name: marketplace
display_name: Marketplace (two-sided — classifieds, services, resale)
funnel: [session_start, search, view_item, add_to_wishlist, generate_lead, purchase]
conversion_events: [purchase, generate_lead]
activation_definition: First completed transaction or first seller contact (generate_lead) within 14 days of first session.
churn_signal: No session for 30 days after at least one search or listing view; for sellers, no active listing for 30 days.
pattern_priorities:
  abandoned-cart: P0
  browse-abandonment: P0
  post-purchase: P0
  winback: P0
  welcome-onboarding: P1
  price-drop: P1
  back-in-stock: P1
  feedback-nps: P1
  reactivation: P1
  progressive-profiling: P2
  referral: P2
  loyalty: P2
  upsell-cross-sell: P2
  milestone: P2
  anniversary: P2
  channel-opt-in: P2
  gamified-rewards: P2
typical_channels: [email, push, whatsapp, sms]
---

# Marketplace Playbook

Two-sided by construction: the product is liquidity, and every lifecycle message either helps a buyer find supply or helps a seller find demand. Buyer purchase frequency and decision cycle vary wildly by vertical (minutes for services, weeks for cars or apartments), but the shared mechanics are search-driven intent, saved listings as the cart analog, and a trust loop — reviews and ratings — that *is* the platform's conversion asset, which makes post-transaction review collection a P0 revenue journey rather than a courtesy. Inventory is unique and perishable (a listed item sells once and disappears), so timing beats persuasion: the right listing surfaced hours late is a lost transaction. This playbook covers the buyer side primarily; seller-side differences are summarized below and warrant their own journey set on two-sided engagements.

## Canonical funnel

| Step | Expected event | Notes |
|---|---|---|
| Visit | `session_start` | |
| Search | `search` | Query params unlock intent segments and saved-search alerts |
| View listing | `view_item` | Highest volume; feeds browse-abandonment |
| Save listing | `add_to_wishlist` | The marketplace "cart" — saved listings are the strongest recoverable intent |
| Contact seller | `generate_lead` | Conversion event for classifieds/services verticals with off-platform closing |
| Transaction | `purchase` | Conversion event where checkout is on-platform; biggest drop-off is save/contact → transaction |
| Review | `feedback` / review event | Closes the trust loop; treat as part of the funnel, not an afterthought |

Verticals differ: classifieds convert at `generate_lead`, managed marketplaces at `purchase`. Establish which applies at intake — it changes every journey's success exit.

## Event expectations

**Must-have** (missing any of these blocks P0 journeys): `view_item` (with item params), `add_to_wishlist` (or saved-listing equivalent), and at least one of `purchase` / `generate_lead`.
**Nice-to-have** (unlocks depth/branches): `search` with query params, listing-status data (sold, expired, price changed — powers price-drop and back-in-stock analogs), review-submitted event, seller-response signals, `share`, category and location attributes, view-count per listing (for factual social proof), seller-side events (listing created, listing expired).

## Pattern priorities — rationale

- **abandoned-cart P0** — as saved-listing follow-up: `add_to_wishlist` without a transaction is proven intent on unique inventory; the follow-up must carry listing status (still available, price changed) because the item can vanish.
- **browse-abandonment P0** — repeat views of the same listing or category without saving is the volume intent signal; saved-search alert mechanics make this the marketplace's biggest re-engagement surface.
- **post-purchase P0** — the review ask is CRITICAL: reviews are the trust infrastructure both sides transact on, so review collection compounds platform-wide conversion. Also carries transaction follow-through (meetup/delivery confirmation, dispute avoidance).
- **winback P0** — marketplace usage is episodic (people return when a need arises); winback keyed to past category interest ("looking for a car again?") re-captures demand that would otherwise restart at a competitor.
- **welcome-onboarding P1** — getting the first search and first saved listing in session one; light-touch, since intent usually arrives with the user.
- **price-drop P1** — on saved listings, a real price change is the highest-converting message the platform can send; requires listing-status data. Promote to P0 when that data exists.
- **back-in-stock P1** — the analog is "new listings matching your saved search / a listing like the one you missed"; unique inventory means literal restock is rare but similar-supply alerts convert well.
- **feedback-nps P1** — distinct from the review ask: platform-level satisfaction, both sides.
- **trial-conversion — not applicable** (no trial mechanics on the buyer side).
- **payment-failure — not applicable buyer-side** in most verticals; applies on the seller side where sellers pay for subscriptions or promoted listings.
- **replenishment — not applicable** (unique, non-consumable inventory).
- **feature-adoption — not scored buyer-side**; relevant to seller tooling (promoted listings, analytics) within the seller journey set.

### Seller-side differences (summary)

Sellers have their own funnel — `sign_up` → first listing created → first inquiry received → first sale → relist/repeat — and different P0s: **welcome-onboarding** (first listing quality: photos, price guidance), **activation** (time-to-first-inquiry; an inquiry-less first listing churns the seller), **churn-prevention** (listing expiry without renewal), and **upsell-cross-sell** (promoted placement, seller subscriptions — where payment-failure becomes applicable). Seller messaging is supply-side liquidity work: "3 people saved your listing", "listings with 5+ photos get more replies". Run sellers as a separate audience with separate journeys; never mix buyer and seller messaging in one program.

## Sector-specific timing & cadence

- Saved-listing follow-up: within 4–24 hours, and always re-check availability at send time — pushing a sold listing destroys trust.
- Browse abandonment / saved-search alerts: new-match alerts near-real-time to daily digest depending on vertical velocity; high-velocity categories (rentals, jobs) justify instant push.
- Review ask: 1–3 days after the transaction completes (delivery/meetup), not at payment; one reminder at most.
- Winback: keyed to the vertical's natural repurchase cycle — weeks for goods, months-to-years for cars/property; use category-level recency, not global.
- Respect episodic usage: a user who just completed their need (bought the car) should be moved to long-cycle winback, not hit with more car listings.

## Seasonality

- Seasonality is **category-dependent**: rentals peak with moving seasons and academic calendars, vehicles with model-year and tax timing, jobs with new-year and post-summer waves, second-hand goods with gifting seasons — read it per dominant category, not platform-wide.
- **Supply has its own seasonality**: listing volume surges (spring cleaning, post-holiday resale) are seller-side moments; demand-side messaging works best when supply is fresh, so buyer alerts and digests earn more during supply peaks.
- Seasonal windows modify existing journeys (saved-search alert cadence, winback timing keyed to the category's season) — they are not a separate journey type.
- Peak-season attributed transactions inflate with the baseline; holdouts matter more (see [measurement](../measurement.md)).

## Segmentation attributes that matter

Side (buyer / seller / both — "both" users are the most valuable and need combined suppression rules), category and location interest, intent stage (searcher / saver / contacter), transaction count and recency per category, review-leaving propensity, saved-search ownership, seller tier (casual vs professional).

## Intake questions (sector-specific)

1. Where does the transaction close — on-platform checkout (`purchase`) or off-platform after contact (`generate_lead`)? This sets the success exit for every buyer journey.
2. Do you have listing-status data (sold, expired, price changes) available in real time to the messaging tool?
3. What share of users are buyers, sellers, or both — and do you currently message the two sides separately?
4. How does the review flow work today (who is asked, when, response rate roughly), and is the review event tracked?
5. What is the natural repurchase cycle in your dominant categories (goods vs services vs vehicles/property)?

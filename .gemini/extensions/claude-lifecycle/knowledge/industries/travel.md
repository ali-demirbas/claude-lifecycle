---
name: travel
display_name: Travel (OTA / airlines / hotels)
funnel: [session_start, search, view_search_results, view_item, begin_checkout, add_payment_info, purchase]
conversion_events: [purchase]
activation_definition: First completed booking (purchase); pre-booking, a completed search with dates + destination counts as activated intent.
churn_signal: No search or session for a period exceeding the customer's booking rhythm (leisure travelers may naturally return only 1–2× per year — compute from data before declaring churn).
pattern_priorities:
  abandoned-cart: P0
  browse-abandonment: P0
  post-purchase: P0
  price-drop: P0
  welcome-onboarding: P1
  upsell-cross-sell: P1
  winback: P1
  loyalty: P1
  feedback-nps: P1
  progressive-profiling: P2
  reactivation: P2
  referral: P2
  anniversary: P2
  channel-opt-in: P2
  gamified-rewards: P2
  lead-nurture: P2
  care-alert: P2
typical_channels: [email, push, whatsapp, sms, in-app]
---

# Travel Playbook

Long consideration cycles (days to months of research for a single high-value booking), extreme seasonality, and a purchase that is the *start* of the customer experience, not the end. Search events are the intent goldmine: a user searching `IST→BCN, 12–19 Aug, 2 adults` has handed you a complete brief. Lifecycle value concentrates in four places: recovering abandoned bookings, converting abandoned searches with fare intelligence, monetizing the pre-trip window (ancillaries: seats, bags, hotels, transfers, insurance), and price/fare alerts that turn watchers into buyers. The booking-to-trip gap makes **post-purchase a full journey in its own right**, not a receipt.

## Canonical funnel

| Step | Expected event | Notes |
|---|---|---|
| Visit | `session_start` | Traffic spikes with seasonality and fare-sale news |
| Search | `search` (with origin/destination/dates params; often custom `search_flight`/`search_hotel`) | The highest-signal event in the sector |
| View results | `view_search_results` / `view_item_list` | Fare/rate comparison happens here, across tabs and competitors |
| View offer | `view_item` | A specific flight/room/package |
| Start booking | `begin_checkout` | Biggest drop-off typically sits between results and here — price sensitivity + comparison shopping |
| Payment | `add_payment_info` | Abandonment here often means payment friction, not lost intent |
| Book | `purchase` | Must carry `value`, destination, and travel dates as params |

## Event expectations

**Must-have** (missing any of these blocks P0 journeys): `search` (or `search_flight`/`search_hotel`) with destination + date params, `view_item`, `begin_checkout`, `purchase` with travel-date params.
**Nice-to-have** (unlocks depth/branches): fare/price as an item param (enables price-drop), `add_to_wishlist`/saved trips, `refund`/cancellation events, ancillary purchase events, loyalty-tier user property, app vs web surface, trip-completion signal (enables post-trip timing).

## Pattern priorities — rationale

- **abandoned-cart P0** — booking abandonment: a user who reached `begin_checkout` on a ₺15.000 booking is the highest-value recoverable intent in any sector; recovery must quote the exact itinerary back.
- **browse-abandonment P0** — search abandonment: many times the volume of checkout abandonment, and the search params (route, dates, party size) make the follow-up almost self-writing. Requires `search` with params.
- **post-purchase P0** — the pre-trip journey: between booking and departure sits a window of high attention and real needs (check-in, seats, bags, hotel, transfer, destination info). It is simultaneously the ancillary-revenue engine and the CX moat. In-trip and post-trip phases extend it (support info → review/NPS ask).
- **price-drop P0** — fare alerts: travel demand is watch-and-wait by nature; a real fare drop on a searched route is the single most welcome marketing message in the sector. Requires fare data availability — verify at intake.
- **upsell-cross-sell P1** — ancillaries; folded partly into post-purchase but earns standalone journeys for flight+hotel cross-sell.
- **winback / loyalty P1** — repeat-booking economics for OTAs and airlines; loyalty is table stakes for airlines/hotels with programs.
- **feedback-nps P1** — post-trip reviews feed the product (hotel reviews are inventory); ask after return, never mid-trip.
- **welcome-onboarding P1** — app install/sign-up to first search; lighter than in subscription sectors.
- **anniversary P2** — "a year since Rome" re-inspiration; works only with tasteful, data-real framing.
- **trial-conversion, payment-failure, feature-adoption, replenishment, back-in-stock, churn-prevention, milestone — not applicable**: no subscription mechanics (payment-failure only matters for pay-later/installment products — ask at intake); "back in stock" is expressible as availability alerts but is covered by price-drop/fare-alert tooling here; churn-prevention has no heartbeat to monitor given naturally long purchase gaps — winback/reactivation cover the lapse cases.

- **care-alert P2** — flight/route disruption heads-ups to travelers holding affected bookings; requires a carrier-status feed, zero-sell inside the alert.

## Sector-specific timing & cadence

- Booking abandonment first touch: fast — within 1–4 hours; fares and rates genuinely change, and the message can say so honestly.
- Search abandonment: same day to 24h, then a slower cadence tracking the research cycle (leisure users search weeks ahead; the journey should breathe over days, not hours).
- Urgency claims (seats left, price valid until) **only from live inventory/fare data** — fabricated scarcity in travel is both a trust killer and, in some markets, a regulatory issue. See lexicon.
- Pre-trip journey: anchor to departure date — booking confirmation (transactional), ancillary offers in the mid-window, check-in/logistics near departure (transactional).
- Post-trip: review/NPS ask within days of return; winback re-inspiration aligned to next seasonal booking window, not fixed intervals.
- Seasonality dominates: schedule portfolio-level sends around booking seasons for the market (e.g. TR: summer-holiday booking waves, bayram windows) — compute from the account's own seasonality on T1 data.

## Seasonality

- Travel intent runs on **booking-season lead times**: people book summer holidays weeks-to-months ahead, so the marketing window opens well before the travel window — re-inspiration and winback sends belong at the *booking* season, not the travel season.
- Market-specific waves (TR: summer-holiday booking waves, bayram windows, school holidays) set the portfolio rhythm; business travel is far flatter than leisure.
- Seasonal windows modify existing journeys — search-abandonment cadence, price-alert sensitivity, and winback timing all shift with the booking season; they are not a separate journey type.
- Peak booking seasons inflate attributed conversions because baseline intent is elevated — holdouts matter more (see [measurement](../measurement.md)).

## Segmentation attributes that matter

Searched-but-not-booked routes/destinations (with dates and party size), trip purpose signals (business vs leisure: trip length, weekend pattern, booking lead time), booking lead-time profile, home airport/city, loyalty tier, price sensitivity (fare-class and filter behavior), days-to-departure for booked customers.

## Intake questions (sector-specific)

1. Which verticals do you sell — flights, hotels, packages, other — and which drives most revenue?
2. Do search events carry structured params (origin, destination, dates, party size), and are they available to the CRM tool?
3. Is live fare/rate and availability data accessible for messaging (enables price-drop and honest urgency)? 
4. What ancillaries can be purchased after booking, and up to when (enables the pre-trip revenue journey)?
5. What is your market's booking seasonality, and do you have a loyalty program?

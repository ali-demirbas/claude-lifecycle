---
name: subscription-media
display_name: Subscription Media (streaming / news / content subscriptions)
funnel: [first_visit, sign_up, trial_start, content_play, subscription_start]
conversion_events: [subscription_start]
activation_definition: First meaningful content session (content_play / content_read reaching a completion threshold) within 48 hours of sign_up or trial_start.
churn_signal: Consumption drop — content_play/content_read frequency falls to zero for 7+ days for a subscriber whose baseline was regular use; cancellation follows consumption collapse, it doesn't precede it.
pattern_priorities:
  welcome-onboarding: P0
  trial-conversion: P0
  churn-prevention: P0
  payment-failure: P0
  activation: P1
  feature-adoption: P1
  winback: P1
  upsell-cross-sell: P1
  progressive-profiling: P2
  reactivation: P2
  milestone: P2
  referral: P2
  feedback-nps: P2
  anniversary: P2
  channel-opt-in: P2
  gamified-rewards: P2
typical_channels: [email, push, in-app, whatsapp]
---

# Subscription Media Playbook

Revenue is a recurring decision the user re-makes every billing cycle, and the vote is cast with consumption: people don't cancel subscriptions they actively use. The entire lifecycle program therefore optimizes one proxy metric — regular content consumption — and the highest-leverage messaging is **content recommendation framed as service, not promotion** ("yeni bölüm yayında", "the next chapter in your series"). Decision cycles are short at trial start and invisible at churn: by the time `subscription_cancel` fires, the user checked out weeks earlier. Email and push carry recommendations; in-app carries plan moments; payment-failure recovery is the quietest, highest-ROI journey in the sector.

## Canonical funnel

| Step | Expected event | Notes |
|---|---|---|
| Visit | `first_visit` / `session_start` | Content marketing / SEO heavy acquisition |
| Register | `sign_up` | Often free tier or metered access first |
| Trial | `trial_start` | Biggest drop-off is typically between trial start and first real content session |
| Consume | `content_play` / `content_read` (custom; `select_content` as fallback) | The engagement heartbeat; must carry content id/category params |
| Convert | `subscription_start` | Must carry plan and `value` params |

Post-conversion the funnel loops: consumption → renewal, and the loop breaking is the churn signal.

## Event expectations

**Must-have** (missing any of these blocks P0 journeys): `sign_up`, `trial_start`, a consumption event (`content_play`/`content_read`/`video_start` with a content identifier), `subscription_start`.
**Nice-to-have** (unlocks depth/branches): consumption completion events (`video_complete`, percent-read), `subscription_cancel`, `payment_failed`, content taxonomy params (`content_category`, `series_id`), `search`, `add_to_watchlist`/save events, plan/tier as user property.

## Pattern priorities — rationale

- **welcome-onboarding P0** — the trial clock starts at sign-up; users who never reach a first satisfying content session are lost before any conversion journey can touch them. Onboarding here means "get them watching/reading something they love", not a product tour.
- **trial-conversion P0** — the sector's canonical revenue journey: consumption-aware messaging through the trial, plan decision framing near expiry.
- **churn-prevention P0** — churn is driven by consumption drop, and the drop is measurable weeks before cancellation. Re-engagement via personalized recommendations ("new episode of the series you watch") is the intervention — not discounts first.
- **payment-failure P0** — involuntary churn from failed cards is silent, sizable in any recurring-billing business, and the recovery messaging is transactional (no consent friction). Cheapest churn to fix.
- **activation P1** — largely covered by welcome-onboarding here; keep as a separate journey only if there's a distinct free tier before trial.
- **feature-adoption P1** — profile setup, watchlists, downloads, newsletters: each adopted feature is a retention hook.
- **upsell-cross-sell P1** — tier upgrades (ad-free, 4K, family plan) triggered by usage signals (device count, hitting tier limits).
- **winback P1** — cancelled subscribers with known taste profiles are the warmest cold audience there is; "what you missed" framing.
- **abandoned-cart, browse-abandonment, replenishment, back-in-stock, price-drop, post-purchase, loyalty — not applicable**: there is no cart, catalog stock, or discrete-purchase mechanics; "post-purchase" is subsumed by onboarding/engagement, and loyalty is the subscription itself.

## Sector-specific timing & cadence

- Welcome/first-recommendation touch: within hours of sign-up, while intent is hottest; first 48h decide activation.
- Trial-conversion sequence: consumption-adaptive — heavy users get a plan nudge near expiry only; non-consumers get recommendation rescue mid-trial, not price messaging.
- Churn-prevention trigger: consumption silence at roughly 7 days for a previously regular user (tune to the product's natural cadence — daily news vs weekly episodes differ).
- Content-drop triggers (new episode/issue in a followed series) beat calendar sends; prefer event-triggered over scheduled.
- Payment failure: retry-aligned notices immediately, then day-by-day until grace period ends; keep strictly transactional in tone.

## Seasonality

- Seasonality here is **content-release-driven** more than calendar-driven: a new season of a flagship series is a bigger intent window than any holiday — plan winback and trial pushes around the release slate, and let content-drop triggers do the work in between.
- **Holiday bingeing** windows (year-end breaks, long weekends) lift consumption and make "what to watch/read next" recommendations land harder; they are also natural trial-start moments.
- Post-flagship churn is predictable: subscribers who joined for one title lapse when it ends — bridge them to adjacent content *before* the finale, not after the cancel.
- Seasonal and release windows modify existing journeys (recommendation cadence, trial timing, winback framing) — they are not a separate journey type. Release-window attributed engagement inflates with the baseline; holdouts matter more (see [measurement](../measurement.md)).

## Segmentation attributes that matter

Consumption frequency vs personal baseline (the churn predictor), content/genre affinity, trial vs paying vs churned status, plan tier, device mix (TV/mobile/web — drives feature adoption targets), tenure.

## Intake questions (sector-specific)

1. Is there a free trial, a free/metered tier, or both — and how long is the trial?
2. What consumption events are tracked (play/read/complete), and do they carry content IDs and categories?
3. How is content released — continuous catalog, weekly episodes, daily editions? (Determines trigger vs calendar cadence.)
4. Can the CRM tool access per-user content history for recommendation personalization, or only aggregate segments?
5. What is the billing setup — app-store subscriptions, direct card billing, or mixed? (Determines how much of payment-failure recovery you control.)

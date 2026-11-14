---
name: segmentation
purpose: How to choose and validate audience segments — referenced when journey-architect writes a journey's §3 Audience and when a pattern's entry conditions are being scoped.
---

# Segmentation

Segmentation exists to avoid the failure mode Seth Godin names in *This Is Marketing*: trying to please everyone produces messaging that's flat, generic, and mediocre — it ends up pleasing no one. A journey's audience definition isn't a formality; it's what makes the copy specific enough to work.

## Six lenses — consider each, don't force all six

- **Demographic** — age, location, income, job role. Cheapest to get; works even at T3 (industry-playbook assumption) or T2 (a CSV field).
- **Behavioral** — what they do, how often, why (purchase history, feature usage, session frequency). Needs T1/T2 event data; most journey-pattern entry conditions already live here.
- **Psychographic** — values, attitudes, motivations. Rarely directly measurable; infer from behavior (e.g. `share`/`invite_sent` as an advocacy-mindset proxy in referral.md), never assert as a standalone fabricated claim.
- **Engagement level** — frequent / occasional / lapsed. Already load-bearing across the engine (`compliance/consent-and-quiet-hours.md`'s "declining engagement gets fewer messages, not more"; every winback/reactivation/churn-prevention pattern).
- **Lifecycle-stage / journey position** — where they sit relative to a specific outcome (trial, onboarding, post-purchase). This is what `stage:` in every pattern's frontmatter already encodes at the portfolio level.
- **Platform/device** — iOS vs Android vs web. Affects channel mechanics (`knowledge/channels/push.md`), not message content, unless a pattern says otherwise. App-version/OS-age is also a legitimate care segment: an outdated-app nudge framed as looking out for the user ("update to keep getting X") is a relationship touch, distinct from any marketing ask.

Most journeys need one or two lenses combined, not all six. Reaching for every lens on every journey is the over-segmentation failure mode below, not thoroughness.

## The four-question test before a segment becomes an entry condition

1. **Actionable** — if this group gets a distinct message, is the message actually different from what everyone else gets? A segment that doesn't change the copy or the offer isn't a segment, it's a label.
2. **Distinguishable** — separable from adjacent segments with the data you actually have, not data you wish you had.
3. **Sizable** — enough volume for the message to matter, and (per `measurement.md`) enough volume to ever measure it. A segment of a dozen people doesn't justify a dedicated branch.
4. **Reachable** — you know how to find and message this group on a consented channel with the attributes available.

A segment failing any one of these is a `templates/tracking-plan.md` data-gap candidate, not a journey branch to build anyway.

## Over-segmentation is a real failure mode, not just inefficiency

Splitting "holiday shoppers in the region" into "customers who buy at Christmas, pay with one specific card, and live in one city" doesn't produce better copy — it produces unmeasurable noise and upkeep cost. Segment granularity should scale with DQS the same way journey depth does (see each pattern's Depth scaling table): a T3 account gets one or two broad, defensible segments from the industry playbook; only a T1 account with real behavioral and engagement data earns finer cuts. Proposing fine-grained segmentation on T2/T3 data is the same honesty violation as proposing branched journey depth without the data to support it.

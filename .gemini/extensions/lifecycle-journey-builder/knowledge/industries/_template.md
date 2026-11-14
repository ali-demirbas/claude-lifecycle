---
name: <sector-slug>            # must match a file in knowledge/lexicons/
display_name: <Sector Name>
funnel: [<ordered list of the sector's canonical funnel steps as event slugs>]
conversion_events: [<the events that count as "revenue" here>]
activation_definition: <one line — what makes a new user "activated" in this sector>
churn_signal: <one line — the earliest measurable churn signal>
pattern_priorities:
  # Every applicable pattern from knowledge/journey-patterns/, scored P0/P1/P2 for this sector.
  <pattern-slug>: P0
  <pattern-slug>: P1
typical_channels: [<channels this sector actually uses, in preference order>]
---

# <Sector Name> Playbook

One paragraph: what lifecycle marketing looks like in this sector — purchase frequency, decision cycle, relationship length, dominant channels.

## Canonical funnel

Ordered funnel with the expected GA4-style event at each step and the typical biggest drop-off point. Table format:

| Step | Expected event | Notes |
|---|---|---|

## Event expectations

Events a well-instrumented company in this sector should have, split into **must-have** (blocks P0 journeys if missing) and **nice-to-have** (unlocks depth/branches). This is what `lifecycle-connect` checks the user's events against.

## Pattern priorities — rationale

For each P0 pattern in frontmatter, 1–2 sentences on why it is P0 *in this sector specifically*. Mention any pattern that is explicitly NOT applicable and why.

## Sector-specific timing & cadence

Concrete guidance: how fast the first touch should be, sensible journey windows, seasonal effects. Ranges, not fake-precise numbers.

## Seasonality

Every business has predictable intent windows — the retail calendar, fiscal/budget cycles, planning and resolution moments, or per-customer renewal/anniversary clustering. Name this sector's windows here, qualitatively (no invented percentages). Keep three rules in view:

- Seasonal windows **modify existing journeys** — trigger timing, framing, incentive level — they are not a separate journey type.
- Apply a **brand-fit filter** before adopting a calendar moment; not every occasion belongs to every brand.
- During seasonal peaks, attributed numbers inflate because the baseline itself is elevated — holdouts matter more. See [knowledge/measurement.md](../measurement.md).

## Segmentation attributes that matter

The 3–6 user attributes with the most leverage in this sector (e.g. RFM for commerce, plan/seat count for SaaS).

## Intake questions (sector-specific)

3–5 questions `lifecycle-intake` should add for this sector when data is thin.

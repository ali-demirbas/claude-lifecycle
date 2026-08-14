---
name: care-alert
stage: retention
trigger_type: event
required_events: [external_alert]
optional_events: [session_start, claim_filed, purchase]
required_attributes: [alert_type, affected_region]
optional_attributes: [product_line, travel_date, severity]
default_channels: [push, sms]
base_steps: 1
depth_range: [1, 2]
applicable_industries: [insurance, travel]
---

# Care Alert

A protective heads-up triggered by the **outside world**, not by user behavior: a hail warning to motor policyholders in the affected province, a flight disruption to travelers holding tomorrow's booking. Every other trigger in this engine comes from what the user did; this one comes from what's about to happen *to* them — which is why it builds more trust per message than anything else the portfolio sends, and why abusing it costs more too. Same structural precedent as [back-in-stock](back-in-stock.md): the trigger is a **data feed**, and without the feed the pattern is blocked, not simulated.

## The care contract (all hold, or the journey doesn't run)

1. **Official sources only.** The `external_alert` feed comes from an authoritative origin (meteorological authority, carrier status API) — never a model's guess about the weather, never a scraped rumor. The alert's claim must be as traceable as any copy claim (CLAUDE.md rule 3, applied to the physical world).
2. **Zero-sell, with a cool-down.** No cross-sell, no promo, no "by the way" inside the alert — and none within **72h after** it. Care converts to trust; monetizing the same moment converts it to cynicism, visibly.
3. **Affected users only.** `affected_region` (and `product_line`/`travel_date` where present) gates the audience hard. A storm warning to the whole country is spam wearing a safety vest.
4. **Consent classified honestly.** A protective notice tied to an active policy/booking is arguably service communication, but that classification varies by market and product — default to requiring marketing consent, and treat a service classification as something counsel approves, never something growth assumes (strictest-wins).

## Required-event signature

| Event | Role |
|---|---|
| `external_alert` | Trigger (custom, from the feed integration, with `alert_type` + `affected_region` params). No feed → pattern is **blocked** — see the tracking plan, not a workaround. |
| `affected_region` (required attr) | The audience gate. Region-matching against the user's stored address/booking is what makes this care instead of broadcast. |
| `claim_filed` *(optional)* | Powers the after-event check-in's one-tap claim path. |
| `severity` *(optional attr)* | Real severity from the source feed may be stated plainly; the engine never escalates wording beyond it. |

## Entry / exit

- **Entry:** `external_alert` fired, user's region/booking matches, relevant product held (kasko for hail, the disrupted flight for travel), consent per the care contract.
- **Exclude:** users already in an open claim for the same peril (they need claim comms, not warnings), negative-signal suppressed users **only if** the message is classified marketing — a genuinely protective service notice goes to everyone affected.
- **Success exit:** none — protective touch · **Window:** the event's own duration · **Re-entry:** per distinct alert event, deduped per region+peril (three severity updates of one storm = one journey, not three).

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (1) | Any DQS | The alert: what's coming, one concrete protective action, where to reach help. |
| Standard (2) | `claim_filed` instrumented | Adds the after-event check-in: "did everything come through okay? one tap to report damage" — care completing into claims-readiness. |
| Branched | — | Not applicable. An emergency heads-up with marketing-style branching has misread the moment. |

## Step blueprint (standard, 2 steps)

| # | Wait | Channel | Intent | Branch |
|---|------|---------|--------|--------|
| 1 | ≤ 30 min after `external_alert` (quiet hours yield ONLY if the event allows — an overnight storm warning sends; see note) | push (sms where push unconsented) | The warning + one concrete action ("aracınızı kapalı alana alın") + source of the alert | — |
| 2 | +24h after the event window closes | push | Check-in: "hasar oldu mu? tek dokunuşla bildirin" — claim path, zero paperwork framing | if step 1 delivered |

Quiet-hours note: a genuinely imminent, high-severity protective alert is the one legitimate quiet-hours exception in the portfolio — and it's an exception the **user's own safety** justifies, taken only when the source feed's timing forces it, documented per send. A morning-safe warning waits for morning.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Delivery + engagement on affected segment | primary | goodwill class (like anniversary) — the touch landing IS the outcome; long-run value shows in renewal cohorts, not this week's clicks |
| Post-event claim-filing ease (step 2 tap-through) | secondary | care completing into the product's core promise |
| Opt-out rate per alert | guardrail | should be near zero; elevation means bad region-matching or a sell that leaked in |

## Common mistakes

- Selling in the alert — the single fastest way to burn the most trusted message type the brand will ever send.
- Broadcasting beyond the affected region because segmentation was hard — precision is the pattern.
- Escalating severity language beyond the source feed's own wording to juice engagement — fabricated urgency about the physical world is the worst possible instance of rule 3.
- Firing per feed-update instead of per event — dedupe or become the boy who cried storm.

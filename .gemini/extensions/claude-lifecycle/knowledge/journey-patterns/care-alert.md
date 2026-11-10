---
name: care-alert
stage: retention
trigger_type: event
journey_class: service
required_events: [external_alert]
optional_events: [claim_filed, alert_cancelled, coverage_ended, consent_withdrawn]
required_attributes: [alert_type, affected_region]
optional_attributes: [product_line, travel_date, severity, alert_end]
default_channels: [push, sms]
base_steps: 2
depth_range: [1, 2]
applicable_industries: [insurance, travel]
requires_feed: true          # needs a live feed (stock, price, purchase cycle or alerts); blocked at T3
mutually_exclusive_with: []
signal_sources: {external_alert: authoritative, alert_type: authoritative, affected_region: authoritative, severity: authoritative, alert_end: authoritative, alert_cancelled: authoritative, claim_filed: authoritative, coverage_ended: authoritative, product_line: authoritative, travel_date: authoritative, consent_withdrawn: authoritative}
insufficient_alone:
  - a forecast or model output that is not the official feed
  - a region match without a held product or booking exposed to the peril
  - a severity update to an alert already sent
exit_before_each_send: [alert_cancelled, claim_filed, coverage_ended, consent_withdrawn]
reentry: {policy: each_trigger, on_duplicate_trigger: ignore}
measurement_default: none_service
instance_key: alert_event_id
---

# Care Alert

A protective heads-up triggered by the **outside world**, not by user behavior: a hail warning to motor policyholders in the affected province, a flight disruption to travelers holding tomorrow's booking. Every other trigger in this engine comes from what the user did; this one comes from what's about to happen *to* them, which is why it builds more trust per message than anything else the portfolio sends, and why abusing it costs more too. Same structural precedent as [back-in-stock](back-in-stock.md): the trigger is a **data feed**, and without the feed the pattern is blocked, not simulated.

**Journey class: service.** The message protects a customer's held policy or booking from a specific outside event; it sells nothing and is not tied to a transaction the customer made, so it is `service`, not `transactional` or `marketing`. That class exempts it from marketing frequency caps and from a holdout (withholding a safety warning from a random group to measure it is not acceptable). It does **not** settle the consent question; see contract rule 4.

## The care contract (all hold, or the journey doesn't run)

1. **Official sources only.** The `external_alert` feed comes from an authoritative origin (meteorological authority, carrier status API), never a model's guess about the weather, never a scraped rumor. The alert's claim must be as traceable as any copy claim (CLAUDE.md rule 3, applied to the physical world).
2. **Zero-sell, with a cool-down.** No cross-sell, no promo, no "by the way" inside the alert, and none within **72h after** it. Care converts to trust; monetizing the same moment converts it to cynicism, visibly.
3. **Affected users only.** `affected_region` (and `product_line`/`travel_date` where present) gates the audience hard. A storm warning to the whole country is spam wearing a safety vest.
4. **Consent classified honestly.** A protective notice tied to an active policy/booking is arguably service communication, but that classification varies by market and product: default to requiring marketing consent on each channel, and treat a service-consent classification as something counsel approves, never something growth assumes (strictest-wins). `journey_class: service` governs caps and measurement; it is not a consent ruling.

## Required-event signature

| Event | Source | Role |
|---|---|---|
| `external_alert` | authoritative | Trigger (custom, from the feed integration, with `alert_type` + `affected_region` params). No feed → pattern is **blocked**; see the tracking plan, not a workaround. |
| `affected_region` (required attr) | authoritative | The audience gate. Region-matching against the user's stored address/booking is what makes this care instead of broadcast. |
| `alert_end` / `alert_cancelled` *(optional)* | authoritative | When the event window closes, or the source withdraws the alert; anchors the check-in and stops queued sends. |
| `claim_filed` *(optional)* | authoritative | Powers the after-event check-in's one-tap claim path; once filed, claim communications take over. |
| `severity` *(optional attr)* | authoritative | Real severity from the source feed may be stated plainly; the engine never escalates wording beyond it. |

### Not enough on its own

- **A forecast or model output that is not the official feed.** However accurate it looks, it is not a source the brand can stand behind in a safety message.
- **A region match without a held product or booking exposed to the peril.** Living in the hail zone without motor cover, or being in the city of a disrupted airport without a booking, does not make the alert relevant.
- **A severity update to an alert already sent.** Updates of one event fold into the open instance; only a change the source itself marks as material (e.g. a higher official warning level) justifies a new message, and still inside the same instance.

## Entry / exit

- **Entry:** `external_alert` fired from the official feed, user's region/booking matches, relevant product held (motor cover for hail, the disrupted flight for travel), consent per the care contract.
- **Exclude:** users already in an open claim for the same peril (they need claim comms, not warnings); negative-signal suppressed users **only if** the message is classified marketing: a genuinely protective service notice goes to everyone affected.
- **Success exit:** none (protective touch); the instance completes when the window closes · **Window:** the event's own duration plus the check-in day.
- **Checked before each send:** `alert_cancelled` for this alert (`same_instance`: the source withdrew it), `claim_filed` for this event's peril and the exposed policy or booking (claims communications own the person now; a claim about something else does not stop the warning), `coverage_ended` for the exposed product (no longer a policyholder or booking holder), `consent_withdrawn` (while the default marketing-consent classification applies; channel-scoped: a withdrawn SMS consent stops SMS, not push).
- **Time anchor:** `alert_end` comes from the feed and its distance from entry varies by peril (a hailstorm closes in hours, a flood warning can run for days), so a generated journey declares it as a range relative to entry (`alert_end: entry +1h … +7d`, widened for perils the feed issues for longer) and re-reads it from the feed before d1. A moved end time moves d1 and s2 with it.
- **Re-entry:** per distinct alert event (`alert_event_id`), deduped per region+peril: three severity updates of one storm = one journey, not three. A duplicate trigger while an instance is open is ignored.
- **Handoffs:** `claim_filed` → claims communications (outside this repo's patterns), with queued care-alert sends suppressed.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (1) | Any DQS | The alert: what's coming, one concrete protective action, where to reach help. |
| Standard (2) | `claim_filed` instrumented | Adds the after-event check-in ("did everything come through okay? one tap to report damage"): care completing into claims-readiness. |
| Branched | — | Not applicable. An emergency heads-up with marketing-style branching has misread the moment. |

## Step blueprint (standard, 2 sends)

| Node | When | Channel | Intent | Route |
|---|---|---|---|---|
| s1 | entry +0m (deliver within 30 min of the feed event) | push (sms where push is unconsented) | The warning + one concrete protective action (e.g. "move the car under cover") + the official source of the alert. Deadline: the peril's onset time from the feed; a warning that would only arrive after onset is not sent as a warning | → d1 |
| d1 | alert_end +24h | — | Decision on `claim_filed` (authoritative) between entry and alert_end +24h | occurred → exit (completed; claims own it) · not_occurred → s2 · unmeasurable → s2 |
| s2 | d1 +0h at 10:00 user_local | push | Check-in: "was there any damage? report it in one tap", claim path with a zero-paperwork framing | → exit (completed) |

s2 is worded so it reads correctly even if s1 never arrived (it names the event, not "our warning"). Where the platform reports delivery receipts, an undelivered s1 may also skip s2; that is a delivery signal, not an open.

## Timing and channel fit

- **Quiet hours:** a genuinely imminent, high-severity protective alert is the one legitimate quiet-hours exception in the portfolio, an exception the **user's own safety** justifies, taken only when the source feed's timing forces it, and documented per send. The same exception covers the SMS no-Sundays rule: an imminent alert goes on a Sunday too. A morning-safe warning waits for morning (push 09:00, SMS 10:00 user local); a morning-safe SMS that would land on a Sunday goes by push at 09:00 where push is reachable, otherwise moves to Monday 10:00, and is dropped if the peril's onset comes before that. The check-in (s2) never uses the exception.
- **Push** fits: it is immediate and lands on the device the traveler or driver carries. **SMS** is the fallback where push is unconsented or the token is dead, and for travelers who may be offline from the app. Email is too slow for s1 and is not used.
- **Fallback:** neither push nor SMS reachable → the person is not alerted by this journey; the journey doc reports the gap rather than switching to email for an imminent event.

## Frequency and overlap

- **Worst path:** 2 sends per alert event; several distinct perils in one week can stack, so the dedupe per region+peril is mandatory and the journey doc states the expected worst case for the season. Exempt from marketing caps as a service journey, but counted in the per-user view.
- **Usually overlaps with:** every marketing journey (they defer), [renewal-reminder](renewal-reminder.md), [anniversary](anniversary.md), claims communications.
- **Precedence:** care-alert outranks all marketing. From s1 until 72h after it, marketing sends to affected users are deferred (the zero-sell cool-down). Claims communications outrank s2.

## Measurement

- **Primary outcome:** share of affected holders reached by s1 before the event window opens (delivered within 30 minutes of the feed event).
- **Design:** `none_service`, no holdout. Reason: a random control group would mean knowingly not warning people about a physical risk.
- **Alternative:** delivery coverage and latency per alert, opt-out rate per alert, and check-in claim tap-through; long-run renewal of alerted cohorts compared descriptively with earlier seasons, never as a causal lift.
- **Contamination risks:** public warnings from authorities and media reach everyone, so any "behavior change" comparison is confounded by the event itself.
- **Low volume:** alert events are rare and lumpy; read results per season, not per week.

## When data is missing

- **No feed:** pattern blocked.
- **No region or booking data on the person:** not eligible; broadcasting instead is the failure this pattern exists to prevent.
- **No `claim_filed`:** Simple depth only (s1), since the check-in can't route to claims or stop when a claim exists.
- **No `alert_end`:** s2 anchors to the feed's own expected end time; if none is given, s2 is not sent.
- **No `severity`:** wording uses the source's alert text as-is, with no severity framing added.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Delivery + engagement on affected segment | primary | goodwill class (like anniversary): the touch landing IS the outcome; long-run value shows in renewal cohorts, not this week's clicks |
| Post-event claim-filing ease (step 2 tap-through) | secondary | care completing into the product's core promise |
| Opt-out rate per alert | guardrail | should be near zero; elevation means bad region-matching or a sell that leaked in |

## Common mistakes

- Selling in the alert: the single fastest way to burn the most trusted message type the brand will ever send.
- Broadcasting beyond the affected region because segmentation was hard: precision is the pattern.
- Escalating severity language beyond the source feed's own wording to juice engagement: fabricated urgency about the physical world is the worst possible instance of rule 3.
- Firing per feed-update instead of per event: dedupe or become the boy who cried storm.
- Reading `journey_class: service` as permission to skip the consent check.

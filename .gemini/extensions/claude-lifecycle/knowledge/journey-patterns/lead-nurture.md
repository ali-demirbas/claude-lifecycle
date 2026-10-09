---
name: lead-nurture
stage: acquisition
trigger_type: event
required_events: [generate_lead, sign_up]
optional_events: [trial_start, purchase, file_download, session_start, view_item, link_click, lead_qualified]
required_attributes: []
optional_attributes: [lead_source, lead_score, content_topic, lead_status, marketing_consent]
default_channels: [email]
base_steps: 4
depth_range: [3, 6]
applicable_industries: [saas, edtech, travel, fintech, insurance]
mutually_exclusive_with: []
journey_class: marketing
signal_sources: {generate_lead: authoritative, sign_up: authoritative, marketing_consent: authoritative, lead_status: authoritative, lead_qualified: authoritative, lead_score: inferred, file_download: behavioral, session_start: behavioral, link_click: engagement, consent_withdrawn: authoritative}
insufficient_alone:
  - a form submission without a separate marketing opt-in
  - message clicks
  - lead_score without sales acceptance
exit_before_each_send: [sign_up, consent_withdrawn, lead_qualified]
reentry: {policy: after_cooldown, cooldown: P90D, on_duplicate_trigger: ignore}
measurement_default: holdout
---

# Lead Nurture

Move a captured lead to the product's front door. Every other pattern in this engine starts at `sign_up` or later; in high-consideration sectors (B2B SaaS, edtech, travel, insurance, fintech) the relationship starts weeks earlier: someone downloads a guide, joins a webinar or fills a pricing form (`generate_lead`) and then researches for a long time before creating an account. This pattern owns that gap. Its job is **problem/solution education and trust**, never product onboarding: there is no product usage to onboard yet, which is exactly why [welcome-onboarding](welcome-onboarding.md) cannot absorb this audience.

The window is bounded at entry and closes on time whether or not nurture worked.

## Required-event signature

| Event | Source | Role |
|---|---|---|
| `generate_lead` | authoritative | Trigger (form submit, gated download, webinar registration) and entry anchor. Without lead capture there is no audience; pattern is **blocked**. |
| `sign_up` | authoritative | Stands in for the sector's destination event and is the success exit: `trial_start` (SaaS), `quote_started` (insurance), first `purchase` or booking (travel) play the same role per playbook. Untracked destination = unmeasurable journey; pattern is **blocked**. |
| `marketing_consent` (attr) | authoritative | Captured with the lead, unbundled from the asset request. Without it only s1 (the requested asset) is sent. |
| `lead_status` / `lead_qualified` *(optional)* | authoritative | Sales-ready status from the system of record. Sales-ready at entry skips nurture; becoming sales-ready during the window ends it (hand-off). |
| `file_download` / `session_start` *(optional)* | behavioral | Engagement depth for d1: a lead consuming more content is warming. |
| `link_click` *(optional)* | engagement | Bot-filtered clicks on s2; the second input to d1. |
| `lead_source` / `content_topic` *(optional attrs)* | authoritative | The reason they entered decides what to send: a pricing-page lead and a beginner-guide lead are at different stages of the same question. |
| `lead_score` *(optional attr)* | inferred | Where a scoring model exists, proposes leads for the sales route in the branched shape. |

### Not enough on its own

- **A form submission without a separate marketing opt-in.** The capture is not the consent; see the consent note.
- **Message clicks.** Engagement inside the window is not progress toward the destination. Clicks route d1 (bot-filtered); they never extend the window, never count as conversion, and never qualify a lead for sales.
- **`lead_score` without sales acceptance.** A score can propose a lead for the sales route; only a recorded sales-ready status (`lead_qualified`) moves it there.

## Entry / exit

- **Entry:** `generate_lead` fired, no active account (`sign_up` never fired for this identity), lead not already sales-ready. A lead whose recorded status is already sales-ready skips nurture and is handed straight to sales: nurturing someone ready to talk only delays them.
- **Exclude:** existing customers and trial users (onboarding and trial patterns own them); leads from purchased or rented lists (no first-party consent, never enter); anyone under negative-signal suppression or a standing sender-side marketing suppression.
- **Success exit:** the destination event (`sign_up` or sector equivalent), handed to [welcome-onboarding](welcome-onboarding.md) immediately. · **Window:** configurable, default 60–90 days matched to the sector's research cycle (evidence to change it: the median lead-to-destination time of converted leads). Engagement inside the window never extends it.
- **Checked before every send:** `sign_up`, `consent_withdrawn` (email marketing consent; since the journey is email-only it stops every marketing send, while the s1 delivery of a requested asset is transactional), `lead_qualified` as recorded in the CRM (a click on a pricing link is not a qualification). The lead's state is re-read from the system of record before each send; a recorded progression ends the window instead of spending the next touch on it.
- **Re-entry:** a new `generate_lead` with a new reason may open a new instance after the cooldown (configurable, default 90 days). A second download inside an active window is ignored: it neither restarts nor extends the window.
- **Sunset:** a lead that reaches the window's end without converting moves to the low-frequency newsletter list (if they opted in to it), not to a re-entry loop. Nurture pressure on a cold lead produces complaints, not conversions.
- **Hand-offs:** `sign_up` → welcome-onboarding; `lead_qualified` → sales owner. Both suppress every queued send of this journey.

## Consent note (this pattern's sharpest legal edge)

A filled form is **not** marketing consent by itself. TR (İYS) and EU (GDPR) require an explicit, unbundled opt-in captured at the form: "download the guide" and "send me marketing" are two different checkboxes. Where only the delivery of the requested asset was consented, the journey sends the asset (s1) and nothing else. This is the strictest-wins compliance chain, not a growth judgment call.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (3) | DQS < 40 or T3 | Deliver the promised asset → one related insight → one soft destination ask. Entry-anchored, email only, no decision. |
| Standard (4–5) | DQS 40–69 | Adds the engagement decision: content consumers get the next-depth piece, silent leads get one re-angle. `content_topic` steers which content track runs. |
| Branched (6) | DQS ≥ 70 + `lead_score` or rich engagement events | Warm/cold tracks; leads accepted as sales-ready route to a human touch instead of more automation; topic-matched sequences. |

## Step blueprint (standard, 4 sends)

| Node | When | Channel | Intent | Route |
|---|---|---|---|---|
| s1 | entry +15m | email | Deliver exactly what was promised (the asset or confirmation), nothing else; this send is the trust foundation | → s2 (only with marketing consent) |
| s2 | s1 +3d | email | One useful insight adjacent to the reason they entered: education, zero product pitch | → d1 |
| d1 | s1 +10d | — | Decision on content engagement: any_of(`link_click` on s2 (engagement, bot-filtered), `file_download` (behavioral), `session_start` (behavioral)) between s1 and s1 +10d | occurred → s3a · not_occurred → s3b · unmeasurable → s3a |
| s3a | s1 +10d | email | Next-depth proof: a case study or named-source finding on their problem (real source, per persuasion-principles) | → s4 |
| s3b | s1 +10d | email | Re-angle: the same question from a different entry point (cost of the problem, a short checklist), still no pitch | → s4 |
| s4 | s1 +24d | email | The soft destination ask: trial, demo or quote framed as the natural next step of what they have been reading | end |

After s4 the instance waits silently until the window closes, then sunsets. Engagement during that wait does not trigger extra sends.

Cadence discipline: this audience asked for content, not a campaign. Roughly one send per week is the ceiling, and every send must pass the "worth reading even if they never buy" test. Product-feature tours belong after `sign_up`, not here.

## Timing and channel fit

- Email only by default: the lead asked for content, and content must be readable later. Business-hours sends in the lead's timezone for B2B, avoiding 00:00–06:00 for everyone (see [consent-and-quiet-hours](../compliance/consent-and-quiet-hours.md)).
- s1 goes within 15 minutes at any hour: it fulfils a request, and its delivery is transactional.
- No SMS or push: phone numbers on lead forms are rarely consented for marketing. No marketing consent → s1 only, then exit.

## Frequency and overlap

- Worst path in a rolling 7 days: 2 emails (s1, s2).
- **Usual overlaps:** newsletter sends to the same address, event or webinar reminders, sales sequences.
- **Precedence:** a sales sequence always wins: `lead_qualified` exits this journey before the next send. Newsletter sends count toward the same 4/week email cap; when both would go in one day, the nurture send moves by a day. Webinar reminders the lead registered for are transactional and never deferred.

## Measurement

- **Primary outcome:** destination event within the window, incremental vs holdout.
- **Design:** 10% random holdout at `generate_lead`; the control receives s1 (they asked for it) and none of s2–s4.
- **Routine communications both groups keep:** asset delivery (s1), webinar reminders, the newsletter for leads who opted in to it.
- **Contamination:** sales outreach to control leads; retargeting ads running on both groups.
- **Low volume:** B2B lead counts and 60–90-day windows make most lifts undetectable in one quarter. Below the sample-size floor, fall back to `none_low_volume` with a pre/post comparison of lead-to-destination rate, labeled directional.

## When data is missing

- **Destination event not tracked:** blocked; nothing tells you whether nurture worked.
- **No unbundled consent field:** treat every lead as asset-only (s1) until the form is fixed.
- **Click data missing or unfiltered, no product events:** d1 takes the unmeasurable route to s3a. Missing engagement data is not a cold lead.
- **No `lead_status` sync from the sales system:** the skip and hand-off rules cannot fire; warn that sales-ready leads will be nurtured in parallel with sales.
- **`content_topic` / `lead_source` missing:** one general track, and the gap goes into the tracking plan.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Lead-to-destination conversion rate | primary | destination events within window / leads entered, incremental vs holdout |
| Content engagement rate | secondary | bot-filtered clicks and content consumption as leading indicators; opens are too inflated to read; never a substitute for the primary |
| Unsubscribe + spam-complaint rate | guardrail | the earliest sign nurture has become pestering; the sunset rule exists because this number only degrades past the window |

## Common mistakes

- Pitching product features to someone who hasn't signed up. The audience is researching a problem, not evaluating your UI.
- Treating the newsletter list as a nurture audience. A newsletter subscriber wanted ongoing content; a lead wanted one asset and is being *moved* somewhere. Different intent, consent and cadence.
- Nurturing forever, or letting each click push the end date out. The window is fixed at entry.
- Nurturing a lead sales already accepted, so the lead hears from automation and a person at the same time.
- Assuming the form's existence equals marketing consent; see the consent note.

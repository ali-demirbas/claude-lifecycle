---
name: lead-nurture
stage: acquisition
trigger_type: event
required_events: [generate_lead, sign_up]
optional_events: [trial_start, purchase, file_download, session_start, view_item]
required_attributes: []
optional_attributes: [lead_source, lead_score, content_topic]
default_channels: [email]
base_steps: 4
depth_range: [3, 6]
applicable_industries: [saas, edtech, travel, fintech, insurance]
---

# Lead Nurture

Move a captured lead to the product's front door. Every other pattern in this engine starts at `sign_up` or later; in high-consideration sectors (B2B SaaS, edtech, travel, insurance, fintech) the relationship starts weeks earlier — someone downloads a guide, joins a webinar, or fills a pricing form (`generate_lead`) and then researches for a long time before ever creating an account. This pattern owns that gap. Its job is **problem/solution education and trust**, never product onboarding: there is no product usage to onboard yet, which is exactly why [welcome-onboarding](welcome-onboarding.md) cannot absorb this audience.

## Required-event signature

| Event | Role |
|---|---|
| `generate_lead` | Trigger (GA4 recommended event — form submit, gated download, webinar registration). Without lead capture there is no audience — pattern is **blocked**. |
| `sign_up` | Stands in for the sector's destination event and is the success exit — `trial_start` (SaaS), `quote_started` (insurance), first `purchase`/booking (travel) play the same role per the playbook. Untracked destination = unmeasurable journey — pattern is **blocked**. |
| `file_download` / `session_start` *(optional)* | Engagement depth: a lead consuming more content is warming; long silence is cooling. |
| `lead_source` / `content_topic` *(optional attrs)* | What they came for decides what to send — a pricing-page lead and a beginner-guide lead are at different stages of the same question. |
| `lead_score` *(optional attr)* | Where a scoring model exists, gates the hand-to-sales branch in the branched shape. |

## Entry / exit

- **Entry:** `generate_lead` fired, **explicit marketing consent captured with it** (see the consent note below), no active account (`sign_up` never fired for this identity).
- **Exclude:** existing customers and trial users (they belong to onboarding/trial patterns), leads from purchased/rented lists (no first-party consent — never enter), anyone under negative-signal suppression.
- **Success exit:** the destination event (`sign_up` / sector equivalent) — hand off to [welcome-onboarding](welcome-onboarding.md) immediately · **Window:** 60–90 days, matched to the sector's research cycle · **Sunset:** a lead that reaches the window's end without converting moves to the low-frequency newsletter list, not to a re-entry loop — nurture pressure on a cold lead produces spam complaints, not conversions.

## Consent note (this pattern's sharpest legal edge)

A filled form is **not** marketing consent by itself. TR (İYS) and EU (GDPR) require an explicit, unbundled opt-in captured at the form — "download the guide" and "send me marketing" are two different checkboxes. Where only the transactional delivery of the requested asset was consented, the journey may deliver the asset and nothing else. This is the strictest-wins compliance chain, not a growth judgment call.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (3) | DQS < 40 or T3 | Deliver the promised asset → one related insight → one soft destination ask. Time-based, email only. |
| Standard (4–5) | DQS 40–69 | Adds engagement branching: content consumers get the next-depth piece, silent leads get one re-angle before sunset. `content_topic` steers which content track runs. |
| Branched (6) | DQS ≥ 70 + `lead_score` or rich engagement events | Warm/cold tracks; high-score leads route to a human/sales touch instead of more automation; topic-matched content sequences. |

## Step blueprint (standard, 4 steps)

| # | Wait | Channel | Intent | Branch |
|---|------|---------|--------|--------|
| 1 | ≤ 15 min after `generate_lead` | email | Deliver exactly what was promised (the asset/confirmation), nothing else — this send is the trust foundation | — |
| 2 | +3d | email | One genuinely useful insight adjacent to what they downloaded — education, zero product pitch | — |
| 3 | +7d | email | Proof: a case study or named-source industry finding relevant to their problem (social proof with a real source, per persuasion-principles) | if step 2 engaged → deeper content; else re-angle |
| 4 | +14d | email | The soft destination ask: trial/demo/quote framed as the natural next step of what they've been reading | — |

Cadence discipline: this audience asked for content, not a campaign — roughly one send per week is the ceiling, and every send must survive the "would this be worth reading even if they never buy" test. Product-feature tours belong after `sign_up`, not here.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Lead-to-destination conversion rate | primary | destination events within window / leads entered — measured vs holdout like every journey |
| Content engagement rate | secondary | opens/clicks are legitimate *leading* indicators here (the audience pre-converted nothing else), but never substitute for the primary |
| Unsubscribe + spam-complaint rate | guardrail | the earliest sign nurture has become pestering; the sunset rule exists because this number only degrades past the window |

## Common mistakes

- Pitching product features to someone who hasn't signed up — the audience is researching a problem, not evaluating your UI; feature tours before `sign_up` read as premature selling.
- Treating the newsletter list as a nurture audience — a newsletter subscriber wanted ongoing content; a lead wanted one asset and is being *moved* somewhere. Different intent, different consent, different cadence.
- Nurturing forever — a 6-month-old unconverted lead is not "still warming"; the sunset rule protects deliverability and the brand.
- Assuming the form's existence equals marketing consent — see the consent note; this is the pattern most likely to inherit a compliance defect from how the form was built.

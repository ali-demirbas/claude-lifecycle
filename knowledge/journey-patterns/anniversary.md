---
name: anniversary
stage: retention
trigger_type: time
required_events: []
optional_events: [purchase, login, session_start]
required_attributes: [anniversary_date]
optional_attributes: [first_purchase_date, birthdate, tenure_years]
default_channels: [email, push]
base_steps: 1
depth_range: [1, 2]
applicable_industries: [ecommerce, saas, mobile-app, fintech, marketplace, subscription-media, travel, edtech]
---

# Anniversary

A once-a-year relationship touch on the signup anniversary, first-purchase anniversary, or birthday. Honest framing: this is a **P2 pattern in every industry** — it never anchors a lifecycle program, it garnishes one. Its value is a low-cost goodwill moment with reliably decent engagement because the message is genuinely about the user. Build it after the P0/P1 journeys exist, never instead of them. The only hard requirement is the date attribute; without a stored `anniversary_date` (or `birthdate`), there is nothing to schedule and the pattern is blocked.

## Required-event signature

| Event | Role |
|---|---|
| `anniversary_date` (required attr) | The scheduler key — signup date, first-purchase date, or birthdate. This pattern is attribute-driven, not event-driven. |
| `purchase` *(optional)* | Success measurement if an offer is attached; also sources `first_purchase_date`. |
| `login` / `session_start` *(optional)* | Cheap engagement exits — proof the touch landed as more than an open. |
| `tenure_years` *(optional attr)* | Lets copy say "3 years together" instead of a generic greeting — the difference between charming and templated. |

## Entry / exit

- **Entry:** scheduled on the anniversary/birthday date (send in user-local daytime), user has valid consent on the channel, date attribute passes sanity checks (no placeholder 01-01 dates, tenure ≥ 1 year).
- **Exclude:** churned/dormant users (a "happy anniversary" from a product someone abandoned reads as unaware — dormant users belong to winback), users in dunning or service recovery, birthday sends where `birthdate` was not explicitly and lawfully collected.
- **Success exit:** none required — goodwill touch. If an offer is attached, `purchase` within window · **Window:** 7 days · **Re-entry:** once per year per date type.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (1) | Any DQS | One message on the date. This is the correct default at every tier. |
| Standard (2) | Offer attached and purchase tracking exists | Adds one expiry reminder for an unredeemed offer near its real end date. |
| Branched | — | Not applicable. |

Depth does **not** scale with DQS. An anniversary is one calendar moment; a sequence hung off it stops being a gesture and becomes a campaign wearing a bow. Higher DQS improves personalization inside the single message (tenure, year-in-review numbers pulled from real events) — never step count.

## Step blueprint (standard, 1 step)

| # | Wait | Channel | Intent | Branch |
|---|------|---------|--------|--------|
| 1 | on the date, user-local daytime | email | Warm, specific note ("{{tenure_years}} years since your first order") — with real personal stats if events allow; small thank-you perk only if the business wants one | — |

**Year-in-review variant:** where real per-user event history exists, the message opens with a delivered-value recap ("this year: {{order_count}} orders, {{assist_count}} times we helped") — the strongest form of this pattern, and bound by the same rule as insurance's pre-renewal recap: **real account data only; a single number that can't be computed means the recap is skipped, never estimated** (CLAUDE.md rule 3).

If a perk is attached, add step 2: push reminder 48h before the perk's true expiry, only if unredeemed.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Engagement rate (open/click) | primary | goodwill touch — engagement *is* the outcome; expect it to run above regular campaigns |
| Perk redemption rate | secondary | only when an offer is attached |
| Unsubscribe rate per send | guardrail | should be near zero; anything elevated means bad dates or dormant targeting |

## Common mistakes

- Sending to dormant users — the strongest possible signal the brand doesn't actually know them; dormant belongs to winback, not celebration.
- Trusting dirty date data — placeholder birthdays (01-01) and imported garbage dates produce absurd sends; validate before scheduling.
- Over-investing because it's easy — this is P2 everywhere; a team polishing anniversary copy before abandoned-cart or trial-conversion exists has its priorities inverted.

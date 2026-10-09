---
name: anniversary
stage: retention
trigger_type: time
required_events: []
optional_events: [purchase, login, session_start, coupon_redeemed]
required_attributes: [anniversary_date]
optional_attributes: [first_purchase_date, birthdate, tenure_years, perk_expiry_date]
default_channels: [email, push]
base_steps: 1
depth_range: [1, 2]
applicable_industries: [ecommerce, saas, mobile-app, fintech, marketplace, subscription-media, travel, edtech]
journey_class: marketing
signal_sources: {anniversary_date: authoritative, birthdate: authoritative, first_purchase_date: authoritative, tenure_years: authoritative, perk_expiry_date: authoritative, purchase: authoritative, coupon_redeemed: authoritative, login: behavioral, session_start: behavioral, consent_withdrawn: authoritative}
insufficient_alone:
  - a placeholder or imported default date
  - a birthdate collected without a stated purpose
  - a year-in-review figure that can't be computed for this user
exit_before_each_send: [coupon_redeemed, consent_withdrawn]
reentry: {policy: after_cooldown, cooldown: P1Y, on_duplicate_trigger: ignore}
measurement_default: holdout
---

# Anniversary

A once-a-year relationship touch on the signup anniversary, first-purchase anniversary, or birthday. Honest framing: this is a **P2 pattern in every industry**. It never anchors a lifecycle program, it garnishes one. Its value is a low-cost goodwill moment with reliably decent engagement because the message is genuinely about the user. Build it after the P0/P1 journeys exist, never instead of them. The only hard requirement is the date attribute; without a stored `anniversary_date` (or `birthdate`), there is nothing to schedule and the pattern is blocked.

Two scheduling rules hold at every depth. **A date that passed without a message is closed**: if the send moment slipped by (the attribute arrived late, consent was granted after the date, a platform outage), the year's message is skipped, never sent days late. **One date per window**: when a birthday and an anniversary fall in the same window, the birthday wins and only one message goes out.

## Required-event signature

| Event | Source | Role |
|---|---|---|
| `anniversary_date` (required attr) | authoritative (account or order record) | The scheduler key: signup date, first-purchase date, or birthdate. This pattern is attribute-driven, not event-driven. |
| `birthdate` *(optional attr)* | authoritative (user-declared, lawfully collected) | The birthday variant's key; also the tie-breaker when it collides with another date. |
| `purchase` / `coupon_redeemed` *(optional)* | authoritative (order / promotion system) | Success measurement when a perk is attached; `purchase` also sources `first_purchase_date`. |
| `login` / `session_start` *(optional)* | behavioral | Cheap return signals: proof the touch landed as more than a glance. |
| `tenure_years` *(optional attr)* | authoritative (computed from the date) | Lets copy say "3 years together" instead of a generic greeting: the difference between charming and templated. |
| `perk_expiry_date` *(optional attr)* | authoritative (promotion record) | The only perk deadline copy may state. |

### Not enough on its own

- **A placeholder or imported default date:** 01-01 birthdays, a migration date stamped on every account, a signup date equal to the import day. These produce absurd sends; validate before scheduling and skip anything that fails.
- **A birthdate collected without a stated purpose:** a date of birth captured for age verification or KYC isn't consent to celebrate it. The birthday variant runs only on a birthdate collected for that use.
- **A year-in-review figure that can't be computed for this user:** one missing number means the recap is skipped, never estimated (CLAUDE.md rule 3).

## Entry / exit

- **Entry:** the instance is created the day before the date and scheduled for the date itself in user-local daytime. Requires valid consent on the channel and a date that passes sanity checks (no placeholder dates, tenure ≥ 1 year for anniversaries).
- **Exclude:** churned/dormant users (a "happy anniversary" from a product someone abandoned reads as unaware; dormant users belong to [winback](winback.md)), users in dunning or service recovery, negative-signal suppression per [consent-and-quiet-hours.md](../compliance/consent-and-quiet-hours.md) rule 4, birthday sends where `birthdate` was not explicitly and lawfully collected for this use.
- **Date collision:** when a birthday and an anniversary (signup or first purchase) fall within the same window (default 7 days, configurable in brand config), the birthday instance wins and the anniversary instance for that year is closed unsent. Two anniversaries of different types in one window → the older relationship date wins. Never two date messages in one window.
- **Missed moment:** if the scheduled send time has passed when the instance would act (late attribute, consent granted after the date, outage), the instance closes as expired. The message is not sent late and not rolled to next week.
- **Success exit:** none required; goodwill touch. If a perk is attached, `coupon_redeemed` (or a `purchase` using it) · **Window:** 7 days, or the perk's recorded validity if shorter.
- **Checked before each send:** `coupon_redeemed`, `consent_withdrawn`, and the exclusion states above (a user who entered dunning since the instance was created gets nothing).
- **Re-entry:** once per year per date type. A repeated trigger for the same date in the same year (a re-imported attribute, an edited date) is ignored.
- **Handoffs:** none. A user who turns out to be dormant is left to winback; the anniversary send is cancelled, not converted into a winback message.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (1) | Any DQS | One message on the date. This is the correct default at every tier. |
| Standard (2) | Perk attached and redemption tracking exists | Adds one reminder for an unredeemed perk near its recorded end date. |
| Branched | — | Not applicable. |

Depth does **not** scale with DQS. An anniversary is one calendar moment; a sequence hung off it stops being a gesture and becomes a campaign wearing a bow. Higher DQS improves personalization inside the single message (tenure, year-in-review numbers pulled from real events), never step count.

## Step blueprint (simple, 1 send)

| Node | When | Channel | Intent | Route |
|---|---|---|---|---|
| s1 | anniversary_date +0d at 10:00 user_local | email | Warm, specific note ("{{tenure_years}} years since your first order"), with real personal stats if events allow; a small thank-you perk only if the business wants one. Closed unsent if the moment has passed or a birthday in the same window took precedence | → exit (completed) |

**Year-in-review variant:** where real per-user event history exists, the message leads with a delivered-value recap ("this year: {{order_count}} orders, {{assist_count}} times we helped"), the strongest form of this pattern, and bound by the same rule as insurance's pre-renewal recap: **real account data only; a single number that can't be computed means the recap is skipped, never estimated** (CLAUDE.md rule 3).

**Perk reminder (standard, second send):** if a perk is attached and the promotion record holds its expiry, one push at `perk_expiry_date -2d at 10:00 user_local`, only if unredeemed (redemption is re-checked before the send). If that reminder moment has already passed, it is dropped. A perk with no recorded expiry gets no reminder and no deadline in copy.

## Timing and channel fit

- Calendar time on the user's clock: 10:00 user_local on the date, market timezone when the user's is unknown. A birthday greeting at 03:00 because the scheduler ran in UTC is the classic failure.
- Email for the note (room for personal stats), push for the one perk reminder. No email consent → push carries a shortened note; no consent on either → no send (in-app on the date is acceptable if the user happens to visit).
- Quiet hours per [consent-and-quiet-hours.md](../compliance/consent-and-quiet-hours.md); a send that can't fit the allowed window on the date is closed, not moved to the next day.

## Frequency and overlap

- **Worst path:** 1 send on the date + 1 perk reminder within the week. One date message per window per user, by the collision rule above.
- **Overlaps:** [milestone](milestone.md), [loyalty](loyalty.md), [gamified-rewards](gamified-rewards.md) (anniversary is a common occasion for a game), seasonal campaigns.
- **Precedence:** service and transactional first; the date message wins over a milestone celebration or a game invite on the same day (they move to the next day); birthday wins over anniversary.

## Measurement

- **Primary outcome:** return within 7 days of the date (`session_start`/`login`, or `purchase` where commerce), vs holdout.
- **Design:** user-level holdout (default 10%), assigned once and kept across years so the same user isn't in and out. The control receives no date message and no perk.
- **Routine communications both groups keep:** newsletters and service messages; any in-product birthday banner the product shows to everyone.
- **Contamination risks:** an in-product greeting or a birthday perk granted by the loyalty program reaches both groups.
- **Low volume:** entrants are spread evenly over the year, so daily volume is small even for large bases. Read results quarterly; a per-month reading is noise.

## When data is missing

- **Date fails sanity checks:** no instance for that user; the bad date goes to the data-quality list, not the send queue.
- **No `tenure_years`:** compute it from the date; if the date's year is unknown (birthday without a year), copy omits the count.
- **Year-in-review figure missing:** recap skipped, the warm note stands alone.
- **User timezone unknown:** market timezone from intake; multiple markets → the strictest window per the compliance file.
- **No perk expiry recorded:** no reminder, no deadline in copy.

## KPIs

| KPI | Type | Note |
|---|---|---|
| 7-day return rate | primary | session/login/purchase within 7 days of the date, vs holdout |
| Click rate (bot-filtered) and perk redemption rate | secondary | clicks show the note landed; redemption only when a perk is attached |
| Unsubscribe rate per send | guardrail | should be near zero; anything elevated means bad dates or dormant targeting |

## Common mistakes

- Sending to dormant users: the strongest possible signal the brand doesn't actually know them; dormant belongs to winback, not celebration.
- Trusting dirty date data: placeholder birthdays (01-01) and imported garbage dates produce absurd sends; validate before scheduling.
- Sending a missed date late: "happy birthday" four days after the fact tells the user they're a row in a batch job. A missed moment is closed.
- Sending both a birthday and an anniversary message in the same week: the second one cancels the warmth of the first. Birthday wins.
- Over-investing because it's easy: this is P2 everywhere; a team polishing anniversary copy before abandoned-cart or trial-conversion exists has its priorities inverted.

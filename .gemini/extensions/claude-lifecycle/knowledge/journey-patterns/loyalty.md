---
name: loyalty
stage: retention
trigger_type: event
required_events: [purchase, earn_virtual_currency]
optional_events: [spend_virtual_currency, loyalty_enrolled, tier_changed, reward_issued, sign_up, join_group, refund]
required_attributes: []
optional_attributes: [points_balance, tier, points_to_next_tier, tier_expiry_date, points_expiry_date, tier_benefits]
default_channels: [email, push]
base_steps: 4
depth_range: [3, 7]
applicable_industries: [ecommerce, travel, marketplace, fintech, insurance, mobile-app]
mutually_exclusive_with: [milestone]
journey_class: marketing
signal_sources: {purchase: authoritative, earn_virtual_currency: authoritative, spend_virtual_currency: authoritative, reward_issued: authoritative, tier_changed: authoritative, loyalty_enrolled: authoritative, points_to_next_tier: authoritative, tier_expiry_date: authoritative, refund: authoritative, consent_withdrawn: authoritative}
insufficient_alone:
  - a client-side analytics points hit with no ledger entry behind it
  - a click on a reward link
  - a points balance with no ledger-dated expiry
  - a replayed reward or tier event carrying a record id already handled
exit_before_each_send: [spend_virtual_currency, purchase, refund, consent_withdrawn]
reentry: {policy: after_cooldown, cooldown: P7D, on_duplicate_trigger: ignore}
measurement_default: holdout
---

# Loyalty

Points, tiers, and VIP mechanics for members of a loyalty program: the enrolment welcome, reward confirmations, tier changes in both directions, milestone celebrations, redemption nudges, tier-progress framing, and expiry warnings. Hard prerequisite: an actual loyalty program (or purchase frequency high enough to justify launching one). **P2 in most sectors**: build this after the core revenue and retention patterns are live, because it only compounds behavior those patterns create.

The pattern carries four kinds of message, and when they collide the order is fixed: **reward confirmation > tier change > enrolment welcome > nurture**. A confirmation is owed to the member; a tier change alters what they have; a welcome explains the program once; nurture is optional by nature and always yields.

## Required-event signature

| Event | Source | Role |
|---|---|---|
| `purchase` | authoritative (order system) | The behavior loyalty exists to reinforce; a qualifying purchase is a success exit. |
| `earn_virtual_currency` | authoritative (loyalty ledger) | Points accrual; opens the nurture path when a points milestone is crossed. GA4's event of the same name is only a stand-in: it must mirror a ledger entry. Without an observable accrual, no loyalty state exists and the pattern is **blocked**. |
| `spend_virtual_currency` *(optional, near-essential)* | authoritative (loyalty ledger) | Redemption: the primary KPI and a success exit. Launching loyalty messaging without it means flying blind on the one metric that matters. |
| `reward_issued` *(optional)* | authoritative (loyalty ledger) | A reward record was created (with a `reward_id`). Opens the confirmation send, exactly one per record. |
| `tier_changed` *(optional)* | authoritative (loyalty ledger) | Carries `from_tier`, `to_tier` and direction. Opens the upgrade or the downgrade send. |
| `loyalty_enrolled` *(optional)* | authoritative (membership record) | Opens the enrolment welcome. `sign_up` / `join_group` can stand in only where the program enrols on signup. |
| `tier` / `points_to_next_tier` / `tier_benefits` *(optional attrs)* | authoritative (loyalty ledger) | Enable tier-progress framing ("one more order to Gold"), the strongest message in the pattern, and the benefit diff an upgrade needs. |
| `tier_expiry_date` / `points_expiry_date` *(optional attrs)* | authoritative (loyalty ledger) | Enable expiry warnings. Only ledger dates, never manufactured urgency. |
| `refund` *(optional)* | authoritative (order system) | A refund can reverse the points that triggered a send; checked before each send. |

### Not enough on its own

- **A client-side analytics points hit with no ledger entry behind it:** analytics events can fire on a page view of a points banner, double-fire, or be dropped. A balance or credit is only stated in copy when the ledger holds it.
- **A click on a reward link:** browsing the catalogue is interest, not redemption. Only `spend_virtual_currency` exits the journey as redeemed.
- **A points balance with no ledger-dated expiry:** without a real expiry date there is no expiry warning; "use them before they're gone" with no date is invented urgency.
- **A replayed reward or tier event carrying a record id already handled:** event pipelines retry. A second `reward_issued` with the same `reward_id` is the same reward, not a second one, and gets no second confirmation.

## Entry / exit

- **Entry (by moment):**
  - *Reward confirmation*: `reward_issued` with a `reward_id` not yet confirmed.
  - *Tier change*: `tier_changed`, upgrade or downgrade, from the ledger.
  - *Enrolment welcome*: `loyalty_enrolled`, once per membership.
  - *Nurture*: a points milestone crossed in the ledger, or a ledger expiry date approaching.
  - Every moment requires an enrolled member; marketing moments (welcome, nurture) also require marketing consent on the channel used.
- **Exclude:** a pending refund that would reverse the triggering points; for nurture, a member already messaged by this journey's nurture path in the last 7 days (milestones cluster; collapse them into the latest). This pattern owns every points/tier crossing; [milestone](milestone.md) explicitly excludes them so the same crossing isn't tracked as two event types and celebrated twice. Don't also emit a generic `milestone_reached` for a tier change this pattern already covers. Every negative-signal suppression in [consent-and-quiet-hours.md](../compliance/consent-and-quiet-hours.md) rule 4 applies to the marketing moments.
- **Success exit:** `spend_virtual_currency` (redemption) or a qualifying `purchase` · **Window:** 30 days.
- **Checked before each send:** `spend_virtual_currency`, `purchase`, `refund` (if it reverses the triggering points, the send is dropped), `consent_withdrawn` (marketing moments only; reward confirmations and service notices still go out, without promotional content).
- **Re-entry:** nurture re-enters per milestone after a 7-day cooldown. Reward confirmations are keyed on `reward_id` and tier changes on the ledger's change id: each record gets one send, ever. **A repeated trigger while an instance is active, or a replayed event for a record already handled, is ignored.**
- **Handoffs:** a tier change or reward confirmation arriving mid-nurture runs first; the nurture send it collides with is deferred one day, or dropped if the new message makes it stale (a tier-progress nudge after the upgrade it was nudging toward). A member who stops purchasing entirely leaves for [winback](winback.md); queued nurture sends are cancelled.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (3) | DQS < 40 or only required events | Milestone announcement → nearest-reward nudge → generic redemption reminder. Email only. Reward confirmation and welcome still run if their events exist. |
| Standard (4–5) | DQS 40–69 | Adds push and tier-progress framing from `points_to_next_tier`; reward suggestions matched to purchase history; upgrade/downgrade sends from `tier_changed`. |
| Branched (6–7) | DQS ≥ 70 + `tier_expiry_date` and `spend_virtual_currency` | Separate tracks: near-tier climbers (progress framing), sitting-on-points hoarders (redemption value), expiring members (real-deadline warnings), plus downgrade recovery. |

## Step blueprint (standard, 4 sends)

Each instance runs one path, chosen by the moment that started it. The nurture path is the longest and sets the step count.

| Node | When | Channel | Intent | Route |
|---|---|---|---|---|
| r1 | reward_issued +0h | email (push mirror where consented) | Reward confirmation, transactional: what was credited, its value, how to use it, and its expiry only if the ledger holds one. One per `reward_id`; zero promotional content | → exit (completed) |
| t1 | tier_changed +1h | email | Upgrade: name only the benefits that are new at this tier (the new tier's benefit set minus the previous tier's), when they start, and how long the tier holds if the ledger says | → exit (completed) |
| t2 | tier_changed +1h | email | Downgrade, sent as a service notice: what changed, the rule that caused it, the effective date, what the member keeps, and the concrete way back. No upsell, no blame | → exit (completed) |
| w1 | loyalty_enrolled +1h | email | Enrolment welcome: how points are earned here, the current balance, and the first reward actually within reach from the live catalogue | → exit (completed) |
| n1 | entry +1h | email | Nurture starts on a ledger milestone: balance update and what it concretely unlocks ("your 1.200 points = free shipping ×3") | → n2 |
| n2 | n1 +3d | push | Nearest attainable reward, deeplinked | → d1 |
| d1 | n2 +4d | — | Decision on `points_to_next_tier` (authoritative, ledger) between entry and n2 +4d | within one typical order of the next tier → n3 · default → d2 · unmeasurable → d2 |
| n3 | d1 +0h at 10:00 user_local | email | Tier-progress framing: the concrete gap to the next tier and what that tier adds over the current one | → d2 |
| d2 | d1 +1d | — | Decision on `tier_expiry_date` or `points_expiry_date` (authoritative, ledger) between d1 and entry +30d | date falls inside the window → n4 · default → exit (completed) · unmeasurable → exit (completed) |
| n4 | tier_expiry_date -14d at 10:00 user_local | email | Expiry warning with the ledger date and the simplest action that preserves status. Skipped if that moment has already passed | → exit (completed) |

The success exit (redemption or qualifying purchase) is re-checked before n2, n3 and n4, which is how "only if not redeemed yet" works; no node needs its own redemption decision. An expiry that falls outside the nurture window gets its own instance later, entered on the expiry approach and sending n4 alone.

## Timing and channel fit

- Reward confirmations go immediately; they are service messages and are not held for a marketing send window, but push respects 22:00–09:00 quiet hours (email carries it overnight, push follows in the morning).
- Tier and welcome sends allow an hour of settling time so a reversed transaction can cancel them first.
- Nurture runs on the user's clock: push inside quiet hours per [consent-and-quiet-hours.md](../compliance/consent-and-quiet-hours.md); calendar sends at 10:00 user_local, falling back to the market timezone.
- Email carries anything with numbers, terms or dates; push carries one short nudge with a deeplink. No push consent → n2 moves to email at the same anchor; no marketing consent on any channel → only r1 and t2 run.

## Frequency and overlap

- **Worst path:** 4 nurture sends over ~30 days plus up to one confirmation and one tier change in the same week: at most 3 marketing sends in a rolling 7 days, inside the default caps. Confirmations and downgrade notices are service sends and don't count against marketing caps.
- **Overlaps:** post-purchase receipts (which often show points), [milestone](milestone.md) (mutually exclusive on points/tier crossings), [gamified-rewards](gamified-rewards.md) (a won prize can land as a loyalty reward), winback.
- **Precedence:** reward confirmation > tier change > enrolment welcome > nurture. Same 24h: the higher one sends, the lower one defers a day or drops if it is now stale. One confirmation per reward record, even when the event arrives twice.

## Measurement

- **Primary outcome:** redemption (`spend_virtual_currency`) within 30 days of entry; repeat purchase rate as the behavioral test.
- **Design:** member-level holdout (default 10%), assigned once and kept. The control does not receive the enrolment welcome or the nurture sends (n1–n4).
- **Routine communications both groups keep:** reward confirmations, tier-change notices (both directions), and any expiry notice the program terms require. Withholding what the member is owed is not a test condition.
- **Contamination risks:** points shown in order receipts and account pages reach both groups; a program-wide promotion (double points week) lifts both groups and must not be credited to the journey.
- **Low volume:** redemption lags; a small program can usually show whether nurture moves redemption at all, not which nurture step did. Below the measurement doctrine's ~200 control conversions, report "unmeasured", not "no effect".

## When data is missing

- **No `reward_issued`:** no confirmation send; never infer a reward from a points total crossing a catalogue price.
- **No `tier_changed` but a `tier` attribute:** compare the attribute between daily snapshots only if the ledger is the attribute's source; otherwise skip tier sends rather than guess a change.
- **No `tier_benefits`:** the upgrade send names the new tier and links to its benefits page; it does not list benefits from memory.
- **`points_to_next_tier` unavailable:** d1 routes to d2 (unmeasurable), so the member skips the progress framing; that is not a disengagement signal.
- **No expiry date in the ledger:** no expiry warning, ever.
- **Ledger events delayed:** confirmation waits for the record; it never goes out from a client-side hit alone.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Redemption rate | primary | `spend_virtual_currency` within window / entrants, vs holdout. Unredeemed points are a liability, not engagement |
| Repeat purchase rate, members vs comparable non-members | secondary | the honest test of whether the program changes behavior rather than rewarding it |
| Duplicate confirmation rate | guardrail | confirmations sent / distinct reward records; anything above 1.0 means replayed events are leaking through |
| Unsubscribe rate per send | guardrail | milestone triggers can fire often; the 7-day nurture cooldown keeps this in bounds |

## Common mistakes

- Launching without redemption tracking: if `spend_virtual_currency` isn't instrumented, the primary KPI is unmeasurable and the program's cost is invisible.
- Manufacturing expiry urgency: "your points expire soon!" without a real ledger date is a compliance and trust failure.
- Classifying points-balance emails as transactional to skip consent: balance updates wrapped around purchase prompts are marketing, full stop. Only the bare confirmation of a credited reward is a service message.
- Confirming the same reward twice because the event was replayed: key confirmations on the reward record, not on event arrival.
- An upgrade email that lists every benefit of the new tier, including ones the member already had: it reads as padding and hides what is actually new.
- Treating a downgrade like an upgrade with the sign flipped: it needs the rule, the date and the way back, not a celebration template or an upsell.
- Skipping the welcome: members who are never told how earning works don't earn deliberately.

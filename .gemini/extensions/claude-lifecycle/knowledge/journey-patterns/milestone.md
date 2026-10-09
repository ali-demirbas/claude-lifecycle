---
name: milestone
stage: retention
trigger_type: event
required_events: [milestone_reached]
optional_events: [purchase, level_up, unlock_achievement, feature_used, login, session_start, reward_redeemed]
required_attributes: [milestone_type, milestone_value]
optional_attributes: [first_purchase_date, streak_length, reward_id, reward_expiry_date]
default_channels: [email, in-app]
base_steps: 2
depth_range: [1, 3]
applicable_industries: [ecommerce, saas, mobile-app, fintech, edtech, subscription-media, insurance, marketplace]
mutually_exclusive_with: [loyalty]
journey_class: marketing
signal_sources: {milestone_reached: authoritative, milestone_type: authoritative, milestone_value: authoritative, purchase: authoritative, level_up: behavioral, unlock_achievement: behavioral, feature_used: behavioral, login: behavioral, session_start: behavioral, reward_redeemed: authoritative, reward_expiry_date: authoritative, consent_withdrawn: authoritative}
insufficient_alone:
  - a milestone counted from client-side analytics hits alone
  - a counter that went up and came back down (refund, reversal, broken streak)
  - an expiry date that is not on the reward record
exit_before_each_send: [reward_redeemed, consent_withdrawn]
reentry: {policy: each_trigger, on_duplicate_trigger: ignore}
measurement_default: holdout
---

# Milestone

Celebrate a user achievement: Nth purchase, usage streak, `level_up`, savings goal hit, or a curated badge/task from a gamification system. The pattern converts accumulated behavior into a moment of recognition, which reinforces the habit that produced it. It requires *countable* events: a `milestone_reached` trigger emitted by counting logic over engagement or revenue events. If nothing is countable (no purchase history, no usage events), there is no milestone to celebrate and the pattern is blocked.

## Required-event signature

| Event | Source | Role |
|---|---|---|
| `milestone_reached` | authoritative (counting logic over the system of record) | Trigger, with `milestone_type` + `milestone_value` params, e.g. `purchase_count=10`, `streak_days=30`, `savings_goal=met`. The counter runs over orders, ledgers or server-side usage, so the number in the copy is the real number. |
| `milestone_type` / `milestone_value` (required attrs) | authoritative | Determine copy and whether a reward is attached; the value is quoted in the message. |
| `purchase` *(optional)* | authoritative (order system) | Countable source for commerce milestones. |
| `level_up` / `unlock_achievement` *(optional)* | behavioral | GA4-native milestone events for app/game verticals; may serve as the trigger directly where the game server confirms them. |
| `feature_used` / `login` / `session_start` *(optional)* | behavioral | Streak and usage-count sources for SaaS/fintech/edtech; `login`/`session_start` also tell the in-app step whether the user came back. |
| `reward_redeemed` / `reward_expiry_date` *(optional)* | authoritative (reward record) | Only when a milestone carries a perk: the redemption exit, and the only expiry the copy may state. |

### Not enough on its own

- **A milestone counted from client-side analytics hits alone:** client hits double-fire and drop. "Your 10th order" sent on the 9th real order is worse than no message; the count comes from the record.
- **A counter that went up and came back down:** a refund un-does an Nth purchase, a missed day breaks a streak. Re-check the count before the send, not only at trigger.
- **An expiry date that is not on the reward record:** a perk's deadline is stated only when the reward record holds it. No record date, no deadline in copy and no reminder.

## Entry / exit

- **Entry:** `milestone_reached` fired, milestone is on the celebrated list (curated, not every counter tick), user messageable on ≥ 1 channel.
- **Exclude:** same milestone already celebrated (once per milestone per lifetime), user in a service-recovery or dunning flow (celebration next to a failed payment reads as tone-deaf), account flagged for refund/abuse, negative-signal suppression per [consent-and-quiet-hours.md](../compliance/consent-and-quiet-hours.md) rule 4, **loyalty-program points/tier crossings when [loyalty](loyalty.md) is active for this portfolio**. Tier and points milestones are that pattern's job (it owns points_balance/tier framing end to end); this pattern owns non-program achievements (Nth purchase, streaks, native `level_up`/badges) so the same real-world crossing isn't tracked as two event types and celebrated twice.
- **Success exit:** none required; this is a relationship touch. If a reward is attached, its redemption (`reward_redeemed`, or `purchase` with the reward's code) is the measured exit · **Window:** 14 days for reward redemption, or the reward record's own validity if shorter.
- **Checked before each send:** `reward_redeemed` (drops the reminder), `consent_withdrawn`, and the milestone count itself (a reversed milestone cancels the remaining sends).
- **Re-entry:** per distinct milestone only. A repeated trigger for a milestone already celebrated (a replayed event, a counter that dipped and crossed again) is ignored.
- **Handoffs:** an accepted share prompt feeds [referral](referral.md)'s `share` signal; it does not start a second journey here.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (1) | DQS < 40 or only the trigger exists | One congratulation message, no reward mechanics. |
| Standard (2) | DQS 40–69 | Celebration + a "what's next" nudge toward the next milestone (progress framing). |
| Branched (3) | DQS ≥ 70 + revenue events | Adds reward branch: high-value milestones (Nth purchase, big streak) or curated badges carry a perk; one redemption reminder if unused, only against a recorded expiry. For badge systems, treat "earned the badge" and "the badge unlocks a new reward" as two different things: badge-only recognition still gets the full celebration; a badge that also unlocks something gets one combined message, not two. |

Depth stays short at every tier by design: a celebration that turns into a sequence stops feeling like a celebration. DQS mainly unlocks *which* milestones can be counted reliably and whether a reward can be attributed.

## Step blueprint (standard, 2 sends)

| Node | When | Channel | Intent | Route |
|---|---|---|---|---|
| s1 | entry +2h | email | Congratulate with the specific number ("your 10th order", "30-day streak"); specificity is the whole trick. Sent in daytime; this is not urgent | → d1 |
| d1 | s1 +7d | — | Decision on `login` or `session_start` (behavioral) between s1 +2d and s1 +7d | occurred → s2 · not_occurred → exit (completed) · unmeasurable → exit (completed) |
| s2 | d1 +0h | in-app | Progress framing toward the next milestone, shown at the user's next session in that window: show the counter, or for task/badge systems suggest one specific next task | → exit (completed) |

The in-app step only exists where the user returns; someone who doesn't come back within the week isn't chased by a second celebration. For curated task/badge systems, "try X next" beats "2 more to go" when there's no natural running total to show. An optional same-session in-app share prompt can follow a badge-tier celebration directly (not a separate send): offer it, don't force it.

**Branched reward reminder (third send):** when the milestone carries a perk, one reminder at `reward_expiry_date -2d at 10:00 user_local`, only if the reward record holds that date and it is unredeemed. If the reminder moment has already passed when the journey reaches it, it is dropped, not sent late. Copy states the recorded expiry and nothing else about time.

Rule: only celebrate milestones the user would plausibly brag about. "You've read 5 of our emails" is surveillance, not celebration.

## Timing and channel fit

- Daytime on the user's clock; never inside push quiet hours per [consent-and-quiet-hours.md](../compliance/consent-and-quiet-hours.md). A celebration that arrives a few hours late loses nothing; one at 02:00 loses a lot.
- Email carries the specific number and any perk terms; in-app carries progress because it appears where the next action happens. Push is only a fallback for s1 when email isn't consented.
- No consent on any marketing channel → in-app only (it needs no channel consent but still respects the user's in-app message settings).

## Frequency and overlap

- **Worst path:** 2 sends in 7 days (3 with the branched reward reminder, spread over the reward's validity). Milestones cluster (a big order can cross a count and a streak at once): collapse simultaneous milestones into one message about the most meaningful one.
- **Overlaps:** [loyalty](loyalty.md) (mutually exclusive on points/tier crossings), [anniversary](anniversary.md), post-purchase.
- **Precedence:** service and transactional messages first; an anniversary or birthday message on the same day wins and the milestone celebration moves to the next day.

## Measurement

- **Primary outcome:** repeat of the counted action within 30 days of entry.
- **Design:** user-level holdout (default 10%). The control does not receive s1, s2 or the reward reminder; if the milestone carries a perk, the control still receives the perk through the product (otherwise the test measures the perk, not the message) unless the test is explicitly about the perk.
- **Routine communications both groups keep:** order/service messages and any in-product badge display the product shows regardless of messaging.
- **Contamination risks:** in-product badge screens and loyalty statements also celebrate the milestone; both groups see them.
- **Low volume:** large milestones (100th order) are rare; measure across the milestone family, not per milestone, and report per-milestone results as directional only.

## When data is missing

- **Counter source is client-side only:** the pattern runs only on milestones the record can confirm; the rest wait for server-side counting in the tracking plan.
- **No session signal for d1:** unmeasurable → the journey ends after s1 (completed). Missing tracking is not a sign the user lost interest.
- **No reward expiry on record:** no deadline in copy and no reminder.
- **`milestone_value` missing:** no send. A celebration without its number is a generic message wearing a party hat.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Repeat action rate post-milestone | primary | share of celebrated users performing the counted action again within 30 days, vs holdout |
| Reward redemption rate | secondary | only when a reward branch exists |
| Unsubscribe rate per send | guardrail | tone-deaf or trivial milestones show up here first |

## Common mistakes

- Celebrating trivial or creepy counters: milestone choice is an editorial decision; count things users are proud of, not things you merely measured.
- Attaching a discount to every milestone: turns recognition into a coupon program and trains users to wait for it.
- Firing celebrations into dunning or complaint contexts: always exclude users in payment-failure or service-recovery flows.
- Celebrating a count that the record later reverses: re-check the count before sending.
- Inventing a perk deadline to create urgency: the only deadline is the one on the reward record.

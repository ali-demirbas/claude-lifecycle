---
name: milestone
stage: retention
trigger_type: event
required_events: [milestone_reached]
optional_events: [purchase, level_up, unlock_achievement, feature_used, login]
required_attributes: [milestone_type, milestone_value]
optional_attributes: [first_purchase_date, streak_length]
default_channels: [email, in-app]
base_steps: 2
depth_range: [1, 3]
applicable_industries: [ecommerce, saas, mobile-app, fintech, edtech, subscription-media, insurance, marketplace]
mutually_exclusive_with: [loyalty]
---

# Milestone

Celebrate a user achievement: Nth purchase, usage streak, `level_up`, savings goal hit, or a curated badge/task from a gamification system. The pattern converts accumulated behavior into a moment of recognition, which reinforces the habit that produced it. It requires *countable* events — a `milestone_reached` trigger emitted by counting logic over engagement or revenue events. If nothing is countable (no purchase history, no usage events), there is no milestone to celebrate and the pattern is blocked.

## Required-event signature

| Event | Role |
|---|---|
| `milestone_reached` | Trigger (custom, emitted by counting logic with `milestone_type` + `milestone_value` params, e.g. `purchase_count=10`, `streak_days=30`, `savings_goal=met`). |
| `purchase` *(optional)* | Countable source for commerce milestones and the natural success exit for reward-bearing milestones. |
| `level_up` / `unlock_achievement` *(optional)* | GA4-native milestone events for app/game verticals — may serve as the trigger directly. |
| `feature_used` / `login` *(optional)* | Streak and usage-count sources for SaaS/fintech/edtech. |
| `milestone_type` (required attr) | Determines copy and whether a reward is attached. |

## Entry / exit

- **Entry:** `milestone_reached` fired, milestone is on the celebrated list (curated — not every counter tick), user messageable on ≥ 1 channel.
- **Exclude:** same milestone already celebrated (once per milestone per lifetime), user in a service-recovery or dunning flow (celebration next to a failed payment reads as tone-deaf), account flagged for refund/abuse, **loyalty-program points/tier crossings when [loyalty](loyalty.md) is active for this portfolio** — tier and points milestones are that pattern's job (it already owns points_balance/tier framing end to end); this pattern owns non-program achievements (Nth purchase, streaks, native `level_up`/badges) so the same real-world crossing isn't tracked as two different event types and celebrated twice.
- **Success exit:** none required — this is a relationship touch. If a reward is attached, its redemption event (e.g. `purchase` with coupon) is the measured exit · **Window:** 14 days for reward redemption · **Re-entry:** per distinct milestone only.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (1) | DQS < 40 or only the trigger exists | One congratulation message, no reward mechanics. |
| Standard (2) | DQS 40–69 | Celebration + a "what's next" nudge toward the next milestone (progress framing). |
| Branched (3) | DQS ≥ 70 + revenue events | Adds reward branch: high-value milestones (Nth purchase, big streak) or curated badges carry a perk; redemption reminder if unused. For badge systems, treat "earned the badge" and "the badge unlocks a new reward" as two different things — badge-only recognition still gets the full celebration; a badge that also unlocks something gets one combined message, not two. |

Depth stays short at every tier by design — a celebration that turns into a sequence stops feeling like a celebration. DQS mainly unlocks *which* milestones can be counted reliably and whether a reward can be attributed.

## Step blueprint (standard, 2 steps)

| # | Wait | Channel | Intent | Branch |
|---|------|---------|--------|--------|
| 1 | ≤ 24h after milestone (send in daytime; this is not urgent) | email | Congratulate with the specific number ("your 10th order", "30-day streak") — specificity is the whole trick | — |
| 2 | +48h | in-app | Progress framing toward the next milestone; show the counter | if step 1 opened |

For curated task/badge systems, step 2 can suggest a specific next task instead of a numeric counter — "try X next" beats "2 more to go" when there's no natural running total to show. An optional same-session in-app share prompt can follow a badge-tier celebration directly (not a separate send): offer it, don't force it. If accepted, it's an organic advocacy signal — feed it to [referral](referral.md)'s `share` event rather than building a second journey around it.

Rule: only celebrate milestones the user would plausibly brag about. "You've opened 5 emails" is surveillance, not celebration.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Repeat action rate post-milestone | primary | share of celebrated users performing the counted action again within 30 days (compare against holdout) |
| Reward redemption rate | secondary | only when a reward branch exists |
| Unsubscribe rate per send | guardrail | tone-deaf or trivial milestones show up here first |

## Common mistakes

- Celebrating trivial or creepy counters — milestone choice is an editorial decision; count things users are proud of, not things you merely measured.
- Attaching a discount to every milestone — turns recognition into a coupon program and trains users to wait for it.
- Firing celebrations into dunning or complaint contexts — always exclude users in payment-failure or service-recovery flows.

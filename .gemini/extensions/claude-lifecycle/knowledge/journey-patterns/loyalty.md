---
name: loyalty
stage: retention
trigger_type: event
required_events: [purchase, earn_virtual_currency]
optional_events: [spend_virtual_currency, sign_up, join_group, refund]
required_attributes: []
optional_attributes: [points_balance, tier, points_to_next_tier, tier_expiry_date]
default_channels: [email, push]
base_steps: 4
depth_range: [3, 7]
applicable_industries: [ecommerce, travel, marketplace, fintech, insurance, mobile-app]
mutually_exclusive_with: [milestone]
---

# Loyalty

Points, tiers, and VIP mechanics for members of a loyalty program: milestone celebrations, redemption nudges, tier-progress framing, and expiry warnings. Hard prerequisite: an actual loyalty program (or purchase frequency high enough to justify launching one). **P2 in most sectors** — build this after the core revenue and retention patterns are live, because it only compounds behavior those patterns create.

## Required-event signature

| Event | Role |
|---|---|
| `purchase` | The behavior loyalty exists to reinforce; qualifying purchases are a success exit. |
| `earn_virtual_currency` | GA4 stand-in for points accrual. Triggers milestone and tier-progress steps. Without it, no loyalty state is observable — pattern is **blocked**. |
| `spend_virtual_currency` *(optional but near-essential)* | Redemption. It is the primary KPI; launching loyalty messaging without it means flying blind on the one metric that matters. |
| `tier` / `points_to_next_tier` *(optional attrs)* | Enable tier-progress framing ("one more order to Gold") — the strongest message in the pattern. |
| `tier_expiry_date` *(optional attr)* | Enables expiry warnings; only real dates, never manufactured urgency. |

## Entry / exit

- **Entry:** enrolled member with marketing consent, on a triggering moment: points milestone crossed, tier change, or points/tier expiry approaching.
- **Exclude:** pending refund that would reverse the triggering points, member already messaged by this journey within 7 days (milestones can cluster; collapse them). This pattern owns every points/tier crossing; [milestone](milestone.md) explicitly excludes them so the same crossing isn't tracked as two event types and celebrated twice — don't also emit a generic `milestone_reached` for a tier change this pattern already covers.
- **Success exit:** `spend_virtual_currency` (redemption) or qualifying `purchase` · **Window:** 30 days · **Re-entry:** per milestone, within the 7-day internal cap and portfolio frequency caps.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (3) | DQS < 40 or only required events | Milestone announcement → nearest-reward nudge → generic redemption reminder. Email only. |
| Standard (4–5) | DQS 40–69 | Adds push and tier-progress framing from `points_to_next_tier`; reward suggestions matched to purchase history. |
| Branched (6–7) | DQS ≥ 70 + `tier_expiry_date` and `spend_virtual_currency` | Separate tracks: near-tier climbers (progress framing), sitting-on-points hoarders (redemption value), expiring members (real-deadline warnings). |

## Step blueprint (standard, 4 steps)

| # | Wait | Channel | Intent | Branch |
|---|------|---------|--------|--------|
| 1 | on milestone | email | Balance update + what it concretely unlocks ("your 1.200 points = free shipping ×3") | — |
| 2 | +3d | push | Nearest attainable reward, deeplinked | if no redemption yet |
| 3 | +7d | email | Tier-progress framing: the concrete gap to the next tier and what the tier is worth | if `points_to_next_tier` known |
| 4 | timed to `tier_expiry_date` − 14d | email | Expiry warning with the real date and the simplest action that preserves status | only if expiry is real |

## KPIs

| KPI | Type | Note |
|---|---|---|
| Redemption rate | primary | `spend_virtual_currency` within window / entrants — unredeemed points are a liability, not engagement |
| Repeat purchase rate, members vs comparable non-members | secondary | the honest test of whether the program changes behavior rather than rewarding it |
| Unsubscribe rate per send | guardrail | milestone triggers can fire often; the 7-day internal cap keeps this in bounds |

## Common mistakes

- Launching without redemption tracking — if `spend_virtual_currency` isn't instrumented, the primary KPI is unmeasurable and the program's cost is invisible.
- Manufacturing expiry urgency — "your points expire soon!" without a real `tier_expiry_date` is a compliance and trust failure.
- Classifying points-balance emails as transactional to skip consent — balance updates wrapped around purchase prompts are marketing, full stop.

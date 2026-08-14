---
name: referral
stage: engagement
trigger_type: segment
required_events: [invite_sent]
optional_events: [invite_accepted, share, survey_response, purchase, login]
required_attributes: []
optional_attributes: [nps_score, engagement_score, referral_reward]
default_channels: [in-app, email]
base_steps: 2
depth_range: [2, 4]
applicable_industries: [saas, mobile-app, fintech, ecommerce, marketplace, edtech, subscription-media, insurance, travel]
---

# Referral

Ask satisfied, engaged users to invite others. The pattern's entire economics rest on the gate: referral asks sent to unhappy or barely-active users produce no invites and damage the relationship, so entry is a **segment** (engagement-health or NPS-positive), not a behavioral trigger. `share` and `invite_sent` are the engagement signals that both qualify users and measure the outcome. This is an engagement-stage journey — the acquisition value of accepted invites is downstream and attributed separately.

## Required-event signature

| Event | Role |
|---|---|
| `invite_sent` | Primary success exit and the mechanic's core instrumentation. If invites can't be tracked, the loop can't be measured — pattern is **blocked**. |
| `invite_accepted` *(optional)* | Closes the loop; enables reward fulfillment and true referral-value reporting. |
| `share` *(optional)* | Organic advocacy signal — users who already `share` are the warmest referral audience. |
| `survey_response` *(optional, with score param)* | NPS gate: promoters (9–10) enter; feeds directly from [feedback-nps](feedback-nps.md). |
| `engagement_score` *(optional attr)* | Fallback gate when no NPS exists: sustained active use over a qualifying window. |

## Entry / exit

- **Entry (segment):** user qualifies as satisfied — NPS promoter, or organic `share` in the last 30 days, or engagement score above the healthy threshold for a sustained period — and has been active long enough to have an opinion (e.g. ≥ 30 days tenure).
- **Exclude:** detractors and anyone in a service-recovery cooldown (see feedback-nps), users in dunning, users who received a referral ask in the last 60 days.
- **Success exit:** `invite_sent` · **Window:** 14 days · **Re-entry:** once per 60–90 days, and stop permanently after repeated ignored asks (2–3 cycles).

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (2) | DQS < 40 or gate is tenure-only | In-app prompt at a natural high point + one email with the referral link. Blunt gate, soft ask. |
| Standard (2–3) | DQS 40–69, engagement scoring works | Same, plus a reminder to users who opened but didn't send; gate is real engagement health. |
| Branched (4) | DQS ≥ 70 + `survey_response` or `share` | NPS-promoter fast path (ask lands right after a 9–10 response), organic-sharer path, and a reward-status follow-up once `invite_accepted` fires. |

Depth stays modest at every tier: a referral is a favor, and favors aren't extracted by drip sequence. Extra DQS goes into sharper gating and better *timing* (asking at a moment of success), not more asks.

## Step blueprint (standard, 3 steps)

| # | Wait | Channel | Intent | Branch |
|---|------|---------|--------|--------|
| 1 | at next session after qualifying (in a success moment, not on error screens) | in-app | The ask: one line on why they might share, prefilled invite flow, reward terms if any | — |
| 2 | +3d | email | Referral link for forwarding; restate mutual reward plainly | if step 1 seen but no `invite_sent` |
| 3 | +7d after `invite_accepted` | email | Reward confirmation / thank-you — closes the loop and primes the next cycle. Fires only after the fraud/abuse check clears | only if an invite was accepted |

Fraud/abuse gate: verify the referral is genuine **before** granting any reward to either party — self-referral, disposable emails, and reward farming are standard attacks, and referral programs are a common abuse target, so this check is not optional. Unchecked rewarding is expensive and hard to reverse.

Reward rule: state the terms exactly and fulfill fast. A delayed or fine-print referral reward converts an advocate into a detractor with an audience.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Invite send rate | primary | qualified users sending ≥ 1 invite within window / journeys entered |
| Invite acceptance rate | secondary | `invite_accepted` / `invite_sent` — measures ask quality reaching the *invitee* |
| Repeat-ask fatigue (opt-out or prompt-dismiss rate) | guardrail | rising dismissals mean the gate is too loose or the cycle too frequent |

## Common mistakes

- Asking everyone — an ungated referral blast to the whole base yields near-zero invites and teaches users to ignore in-app prompts generally.
- Asking at the wrong moment — the prompt after a crash, a failed payment, or a support complaint is the canonical own-goal; tie the ask to success moments.
- Leading with the reward instead of the product — mercenary framing attracts low-quality invitees and can trip incentive-disclosure rules in regulated verticals (fintech especially).
- Granting rewards before verifying the referral is genuine — self-referrals, disposable emails, and reward farming go unchecked, and clawing back a granted reward is far harder than gating it up front.

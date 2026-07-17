---
name: feedback-nps
stage: retention
trigger_type: event
required_events: [survey_response]
optional_events: [purchase, feature_used, trial_end, login, share, invite_sent]
required_attributes: [survey_score]
optional_attributes: [survey_comment, experience_type]
default_channels: [email, in-app]
base_steps: 3
depth_range: [2, 5]
applicable_industries: [ecommerce, saas, mobile-app, fintech, marketplace, subscription-media, travel, edtech, insurance]
---

# Feedback / NPS

Collect post-experience feedback and *act on the answer* — the acting is the pattern. The ask fires after a meaningful experience completes (delivered order, trial end, core feature milestone, completed trip/course — sector-dependent), and the branch on `survey_score` does the retention work: promoters are routed to a referral or review ask while goodwill is hot; detractors get service recovery and a **suppression from marketing sends for a cooldown period**, because promoting to someone who just told you they're unhappy converts feedback into churn.

## Required-event signature

| Event | Role |
|---|---|
| `survey_response` | The branch point (custom, with `survey_score` param, 0–10 for NPS or 1–5 for CSAT). Without response capture, there is nothing to branch on — pattern is **blocked**. |
| `purchase` / `feature_used` / `trial_end` *(optional)* | Qualifying-experience triggers; the sector's industry file picks which one arms the ask. |
| `share` / `invite_sent` *(optional)* | Promoter-path handoff signals into [referral](referral.md). |
| `survey_comment` *(optional attr)* | Verbatims turn a score into a routable support case for the detractor path. |

## Entry / exit

- **Entry:** qualifying experience event completed (e.g. order delivered, not merely placed), no survey received in the last 90 days, user messageable on ≥ 1 channel.
- **Exclude:** open support ticket (they've already given feedback — route around the survey), user in dunning, surveyed within the fatigue window regardless of channel.
- **Success exit:** `survey_response` received — the branch then runs to completion · **Window:** 7 days for the ask; branch actions within 72h of response · **Re-entry:** once per 90 days maximum.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (2) | DQS < 40 | Ask + one reminder. Responses logged; branching handled manually. Honest but low-leverage. |
| Standard (3) | DQS 40–69 | Full branch: promoters → referral/review ask, detractors → recovery + marketing suppression, passives → thank-you only. |
| Branched (4–5) | DQS ≥ 70 + `survey_comment` / support integration | Detractor path opens a tracked recovery loop (human follow-up, resolution check-in); promoter path picks referral vs public-review ask based on prior `share` behavior. |

## Step blueprint (standard, 3 steps)

| # | Wait | Channel | Intent | Branch |
|---|------|---------|--------|--------|
| 1 | +24–72h after qualifying experience (long enough to have an opinion) | email | The ask: one question, tap-to-score in the email body, nothing else | — |
| 2a | +24h after response | email | Promoters (9–10): thank + referral or public-review ask — hand off to the referral pattern | if `survey_score` ≥ 9 |
| 2b | ≤ 24h after response | email | Detractors (0–6): acknowledge, apologize where warranted, route to human/service recovery; apply marketing suppression for a 14–30 day cooldown | if `survey_score` ≤ 6 |

Passives (7–8) get a short thank-you and no further steps. Non-responders get at most one reminder at +4d, then exit silently.

Public-review mechanics (promoter path, app products): gate the store-review prompt on a genuine success moment **and** minimum tenure — both, not either. Ask a soft in-app sentiment question first; positive → the native store rating flow, neutral/negative → a private feedback form, never the public store. Two separate cooldowns, not one: a shorter cooldown (~14 days) since the soft prompt was last *shown*, gating re-asking even when it never reached a native prompt, and a longer cooldown (60–90 days) after the native prompt actually *fires*, since that's the scarcer, quota-limited resource. Platform quotas make every native prompt precious: iOS's SKStoreReviewController allows at most 3 prompts per user per 365 days, and Android's In-App Review API enforces its own platform-managed quota — a wasted prompt cannot be re-fired.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Response rate | primary | responses / asks sent — everything downstream depends on it |
| Detractor recovery rate | secondary | detractors with a resolved follow-up who remain active after 60 days |
| Survey fatigue (asks per user per quarter) | guardrail | the 90-day re-entry cap is the floor, not a target; over-surveying depresses scores by itself |

## Common mistakes

- Collecting scores and doing nothing — an unanswered detractor response is worse than never asking, because the user now has evidence you don't listen.
- Skipping the marketing suppression — a promo email landing the day after a 2/10 response is how detractors become public detractors.
- Gaming the sample — asking only after visibly good experiences produces a flattering, useless number and hides the churn signal the pattern exists to catch.

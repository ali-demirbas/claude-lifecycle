---
name: welcome-onboarding
stage: activation
trigger_type: event
required_events: [sign_up]
optional_events: [login, tutorial_begin, tutorial_complete, feature_used, purchase, subscription_start]
required_attributes: []
optional_attributes: [signup_source, plan_type, onboarding_goal, account_id, user_role]
default_channels: [email, in-app]
base_steps: 5
depth_range: [4, 10]
applicable_industries: [ecommerce, saas, mobile-app, fintech, marketplace, subscription-media, travel, edtech, insurance]
mutually_exclusive_with: [account-onboarding]
---

# Welcome / Onboarding

Guide brand-new users from `sign_up` to their first value moment. The first 7 days set open-rate expectations for every journey that follows — this is the one sequence nearly every user reads, so it carries the education load and hands activated users off to engagement patterns quickly.

## Required-event signature

| Event | Role |
|---|---|
| `sign_up` | Trigger. Step 1 fires immediately — a welcome message is expected within minutes, not hours. |
| `tutorial_complete` / `feature_used` / first `purchase` *(optional)* | Sector's activation event (per industry playbook). When tracked, it becomes the success exit; without it the journey can only exit on completion and activation cannot be measured. |
| `login` *(optional)* | Enables a "returned but didn't activate" branch distinct from "never came back". |
| `signup_source` *(optional attr)* | Enables intent-matched content (ad-signup vs referral vs organic warrant different first messages). |
| `plan_type` / `onboarding_goal` *(optional attrs)* | Enable use-case-specific tracks in the branched shape. |
| `account_id` / `user_role` *(optional attrs)* | Not used by this pattern's own steps — exist solely so the exclude rule below (handing off to `account-onboarding` for multi-seat B2B accounts) can actually be evaluated against real data instead of a signal this file never declares. |

## Entry / exit

- **Entry:** `sign_up` fired, consent on ≥ 1 channel. In-app steps require no consent but only reach returning users.
- **Exclude:** migrated/imported accounts (no real signup moment), users who activated within the first session (skip educational steps, send welcome step 1 only), multi-seat B2B accounts with `account_id` + `user_role` set when [account-onboarding](account-onboarding.md) is also active for this portfolio (→ that pattern instead; this file has no reciprocal awareness of it otherwise, since each pattern is designed in isolation — without that pattern active, this one remains the correct fallback regardless of seat count).
- **Success exit:** sector activation event (see signature) · **Window:** 14 days · **Re-entry:** once ever.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (4) | DQS < 40 or only `sign_up` tracked | Linear: welcome → core value → single how-to → nudge. Email only, time-based waits. |
| Standard (5–7) | DQS 40–69 | Adds in-app channel and one activated-vs-not branch mid-sequence; activated users get a shortened congratulatory tail. |
| Branched (8–10) | DQS ≥ 70 + `feature_used` or `signup_source` | Splits by signup source or stated goal into parallel tracks; behavior-triggered tips replace fixed timing for steps 3+. |

Off-path entrants misfire sequence-gated logic: deep-link, ad-landing, and paywall-first flows put users past (or before) the steps the sequence assumes — check real first-event data before trusting the assumed order. Cold-monetization entries (first screen = paywall, zero product experience) route to a value-preview before any purchase ask.

Pace is a segmentation axis in its own right: fast progressors get a lighter track with already-done nudges skipped (exception checks before every step make this automatic); stallers get support and obstacle-removal, not repeats of the same nudge.

## Step blueprint (standard, 5 steps)

| # | Wait | Channel | Intent | Branch |
|---|------|---------|--------|--------|
| 1 | immediate | email | Welcome: confirm what they signed up for, one CTA to the single first-value action | — |
| 2 | +1d | in-app | Contextual pointer to the core action, shown on next session | if not yet activated |
| 3 | +2d | email | How-to targeting the most common activation blocker, with proof it's worth it | if not yet activated |
| 4 | +3d | email | Use-case story matched to `signup_source` when known, generic best-case otherwise | — |
| 5 | +5d | email | Direct activation nudge + offer of human help / support channel | if still not activated |

Activated users exit immediately at any point; do not keep sending them "how to get started" content.

For app products adding push: the OS push-permission prompt is never fired cold — show an in-app explanation of the specific value first, then the system prompt (full rule in [push.md](../channels/push.md)).

## KPIs

| KPI | Type | Note |
|---|---|---|
| Activation rate within 14 days | primary | activation events / journeys entered |
| Time-to-first-value | secondary | median hours from `sign_up` to activation event |
| Unsubscribe rate per send | guardrail | this list is your freshest — early unsubscribes are the most expensive |

## Common mistakes

- Delaying step 1 to batch sends — the welcome email is expected immediately; a 6-hour delay reads as neglect.
- Cramming every feature into email 1 — one first-value action per message; feature tours belong in later steps or in-app.
- Keeping activated users in the educational track — the branch check must run before every step, not just once.

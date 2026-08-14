---
name: activation
stage: activation
trigger_type: absence
required_events: [sign_up, tutorial_complete]
optional_events: [login, feature_used, session_start, first_open]
required_attributes: []
optional_attributes: [signup_source, days_since_signup, blocked_step]
default_channels: [email, push]
base_steps: 4
depth_range: [3, 6]
applicable_industries: [saas, mobile-app, fintech, edtech, marketplace, subscription-media]
---

# Activation Rescue

Rescue users who signed up but never reached the activation event within N days. Distinct from welcome-onboarding: welcome is triggered by `sign_up` and educates everyone; this pattern is triggered by the **absence** of activation after the welcome window closes, and its job is diagnosing and removing the specific blocker.

## Required-event signature

| Event | Role |
|---|---|
| `sign_up` | Cohort anchor. Absence window counts from here. |
| `tutorial_complete` | Stands in for the sector's designated activation event (`feature_used`, first `purchase`, first booking — per industry playbook). Both the trigger (its absence) and the success exit. Without it, the pattern is **blocked** — you cannot detect who needs rescuing. |
| `login` / `session_start` *(optional)* | Splits "returned but stuck" (product friction) from "never came back" (motivation) — the two need different messages. |
| `blocked_step` *(optional attr)* | Last onboarding step reached; enables blocker-specific how-tos instead of generic nudges. |

## Entry / exit

- **Entry:** `sign_up` ≥ N days ago (default 7; tune N to the observed median time-to-activation), activation event never fired, welcome-onboarding completed or exited.
- **Exclude:** activated users, accounts younger than N days (still welcome-onboarding's job), users who unsubscribed during welcome.
- **Success exit:** activation event fires · **Window:** 14 days · **Re-entry:** once ever — after that the user moves to a low-frequency digest, not another rescue.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (3) | DQS < 40 or only required events | Friction-removal email → direct deeplink push → help offer. Time-based, linear. |
| Standard (4–5) | DQS 40–69 | Adds returned-vs-never-returned branch: stuck users get how-tos, absent users get motivation/value content. |
| Branched (6) | DQS ≥ 70 + `blocked_step` | Blocker-specific tracks (e.g. stalled at data import vs stalled at invite step), each with its own fix content. |

## Step blueprint (standard, 4 steps)

| # | Wait | Channel | Intent | Branch |
|---|------|---------|--------|--------|
| 1 | on entry | email | "What got in the way?" — name the likely friction, one-click path back to the activation action | — |
| 2 | +2d | push | Deeplink directly into the activation action, zero preamble | if step 1 not clicked |
| 3 | +3d | email | Single-blocker how-to (matched to `blocked_step` if known, else the most common blocker) | if returned but not activated |
| 4 | +4d | email | Human help: support channel, onboarding call, or reply-to-this-email offer | — |

Resumption framing: when the blocker is a half-finished flow (a started-but-abandoned import, form, or filing), the message offers the **completed path back** — deep-link into the half-done state, "continue with one tap" — not an offer of assistance. "We made it easier, pick up where you left off" lifts the mental load; "can we help?" hands it back.

For a blocker that's tedious rather than confusing (importing a list, connecting an integration), step 4 can go further than offering help: a concierge move where a human completes the blocked step *for* the user within a stated SLA (e.g. 24–48h), then follows up explaining how, so the user can self-serve next time. This turns a support cost into an activation-rescue tactic, but it's a real operational commitment, not a copy choice — only propose it if the business has the staffing to honor the SLA, and reserve it for the single highest-value blocker, not every step.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Rescued activation rate | primary | activation events within window / journeys entered |
| Support-contact / reply rate | secondary | rescue sequences legitimately convert to human help — count it as a win path |
| Unsubscribe rate per send | guardrail | never-activated users churn off the list fastest; watch this closely |

## Common mistakes

- Re-sending welcome content with a new subject line — they already ignored it; the angle must change from education to friction removal.
- Triggering while welcome-onboarding is still running — the two must be sequenced, or the user gets two activation pitches per day.
- Setting N by gut feel — derive it from the median time-to-activation of users who did activate; a fixed 7 days is wrong for both same-day products and slow-burn ones.

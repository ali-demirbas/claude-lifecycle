---
name: welcome-onboarding
stage: activation
trigger_type: event
required_events: [sign_up]
optional_events: [login, tutorial_begin, tutorial_complete, feature_used, purchase, activation_event, consent_withdrawn]
required_attributes: []
optional_attributes: [signup_source, plan_type, onboarding_goal, account_id, user_role, last_completed_step]
default_channels: [email, in_app]
base_steps: 5
depth_range: [4, 10]
applicable_industries: [ecommerce, saas, mobile-app, fintech, marketplace, subscription-media, travel, edtech, insurance]
mutually_exclusive_with: [account-onboarding]
journey_class: marketing
signal_sources: {sign_up: authoritative, activation_event: behavioral, login: behavioral, tutorial_begin: behavioral, signup_source: authoritative, onboarding_goal: authoritative, consent_withdrawn: authoritative}
insufficient_alone:
  - a login without the activation event
  - tutorial_begin without tutorial_complete
  - a click on an onboarding message
exit_before_each_send: [activation_event, consent_withdrawn]
reentry: {policy: once, on_duplicate_trigger: ignore}
measurement_default: holdout
---

# Welcome / Onboarding

Guide brand-new users from `sign_up` to their first value moment. The first 7 days set the engagement baseline for every journey that follows: this is the one sequence nearly every user sees, so it carries the education load and hands activated users off to engagement patterns quickly.

`activation_event` below stands for the sector's designated activation event (`tutorial_complete`, a core `feature_used`, first `purchase`, first booking), named per industry playbook.

## Required-event signature

| Event | Source | Role |
|---|---|---|
| `sign_up` | authoritative | Trigger and the entry anchor. s1 fires within minutes: a welcome is expected immediately, not hours later. |
| `activation_event` *(optional, strongly advised)* | behavioral | Success exit, re-checked before every send. Without it the journey can only time out, and activation cannot be measured. |
| `login` *(optional)* | behavioral | Feeds d1: "returned but didn't activate" (friction) vs "never came back" (motivation). |
| `last_completed_step` *(optional attr)* | behavioral | Lets the returned-but-stuck branch deep-link to the exact unfinished step. |
| `signup_source` *(optional attr)* | authoritative | Intent-matched content: ad signup vs referral vs organic warrant different first messages. |
| `plan_type` / `onboarding_goal` *(optional attrs)* | authoritative | Use-case-specific tracks in the branched shape. |
| `account_id` / `user_role` *(optional attrs)* | authoritative | Not read by this pattern's own steps. They exist so the hand-off rule to `account-onboarding` (Entry / exit) can be evaluated on real data. |
| `consent_withdrawn` | authoritative | Channel opt-out, re-checked before every send. |

### Not enough on its own

- **A login without the activation event.** Returning proves interest, not value. It routes d1; it never counts as success.
- **`tutorial_begin` without `tutorial_complete`.** Starting the tour is the most common stall point, not progress.
- **A click on an onboarding message.** A click (bot-filtered) is a diagnostic. It does not mark the user as activated and does not by itself route anyone.

## Entry / exit

- **Entry:** `sign_up` fired, consent on ≥ 1 messaging channel. In-app steps need no marketing consent but only reach users who return.
- **Exclude:** migrated or imported accounts (no real signup moment); users who reached `activation_event` within the first session (send s1 only); multi-seat B2B accounts with `account_id` + `user_role` set **when [account-onboarding](account-onboarding.md) is active in this portfolio**. That pattern supersedes this one for those accounts. When it is not active, this pattern stays the correct fallback regardless of seat count.
- **Success exit:** `activation_event` · **Window:** 14 days from entry.
- **Checked before every send:** `activation_event` (activated users leave immediately; do not keep sending "how to get started"), `consent_withdrawn` scoped to that channel (an email unsubscribe stops the emails; the in-app pointer, which needs no marketing consent, still shows).
- **Re-entry:** once ever. A repeated `sign_up` for the same identity while an instance is active is ignored (no restart).
- **Inbound from:** [lead-nurture](lead-nurture.md) (on `sign_up`, carrying the lead source and consent state) and [reactivation](reactivation.md) (a returning dormant non-customer who never entered this journey, carrying `reactivation_reason`); the sender's queued sends are suppressed.
- **Hand-offs:** activated users go to the engagement patterns (`feature-adoption`, `milestone`); users who time out unactivated go to [activation](activation.md), which only starts after this window closes. Any queued sends of this journey are dropped at hand-off.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (4) | DQS < 40 or only `sign_up` tracked | Linear: welcome → core value → single how-to → nudge. Email only, entry-anchored waits, no decision. |
| Standard (5–7) | DQS 40–69 | Adds the in-app pointer and one returned-vs-never-returned decision mid-sequence. |
| Branched (8–10) | DQS ≥ 70 + `activation_event` and `signup_source` or `onboarding_goal` | Parallel tracks by signup source or stated goal; behavior-triggered tips replace fixed timing from s3 on. |

Activation itself always exits; any congratulation or next-step message belongs to the receiving engagement pattern, not to a tail of this one.

Off-path entrants misfire sequence-gated logic: deep-link, ad-landing and paywall-first flows put users past (or before) the steps the sequence assumes. Check real first-event data before trusting the assumed order. Cold-monetization entries (first screen is a paywall, zero product experience) route to a value preview before any purchase ask.

Pace is a segmentation axis in its own right: fast progressors get a lighter track because the before-each-send checks skip already-done nudges; stallers get obstacle removal, not repeats of the same nudge.

## Step blueprint (standard, 5 sends)

| Node | When | Channel | Intent | Route |
|---|---|---|---|---|
| s1 | entry +5m | email | Welcome: confirm what they signed up for, one CTA to the single first-value action | → s2 |
| s2 | s1 +1d (shown at next session, expires after 5d) | in_app | Contextual pointer to the core action, shown at the next session on or after this time; skipped if no session comes within 5 days. s3 keeps its own anchor (`s1 +3d`) whether or not s2 was seen | → s3 |
| s3 | s1 +3d | email | How-to aimed at the most common activation blocker, with proof the result is worth it | → d1 |
| d1 | s1 +6d | — | Decision on `login` (behavioral) between s1 +1d and s1 +6d (the window opens a day after the welcome, so the signup session's own login never counts as a return) | occurred → s4a · not_occurred → s4b · unmeasurable → s4b |
| s4a | s1 +6d | email | Returned but stuck: deep link back to the exact unfinished step (`last_completed_step`), not to the start of onboarding | → s5 |
| s4b | s1 +6d | email | Use-case story matched to `signup_source` when known, generic best case otherwise | → s5 |
| s5 | s1 +11d | email | Direct activation nudge plus an offer of human help or the support channel | end |

One next step per message: no send asks for more than one onboarding task, and the sequence ends the moment first value is reached. A user who comes back mid-way resumes where they stopped; restarting them at step one reads as the product forgetting them.

For app products adding push: the OS push-permission prompt is never fired cold. Show an in-app explanation of the specific value first, then the system prompt (full rule in [push.md](../channels/push.md)).

## Timing and channel fit

- s1 goes immediately, including overnight: the welcome is the one send users actively wait for. Later emails avoid 00:00–06:00 user local; push (when added) respects 22:00–09:00 (see [consent-and-quiet-hours](../compliance/consent-and-quiet-hours.md)). Unknown timezone → market timezone from intake.
- Email carries the welcome and durable how-tos; in-app carries contextual pointers because the user is already where the action happens. In-app is session-bound: s2 waits for the next session for at most 5 days, then is skipped; no email waits on it being seen.
- No email consent → s2 in-app only, plus the product's own transactional account confirmation (which must stay free of promotion). No consent and no return visit → nothing to send; the instance times out and is counted in the measurement as unreached, not as failed.

## Frequency and overlap

- Worst path in the first rolling 7 days: s1 + s3 + s4 = 3 marketing emails + 1 in-app, inside the 4/week email cap.
- **Usual overlaps:** `trial-conversion` (signup and trial start often coincide), `lead-nurture` (hands off into this journey on `sign_up`), `progressive-profiling`, `channel-opt-in`.
- **Precedence:** when a trial starts at signup, run one of the two: `trial-conversion` carries the onboarding content inside the trial clock and this journey sends s1 at most. `lead-nurture` exits on `sign_up` before this journey's s1, so the two never send in parallel. `progressive-profiling` never asks in the first session. If a send would breach the cap, defer the lower-priority marketing journey's send, never s1.

## Measurement

- **Primary outcome:** `activation_event` within 14 days of entry, incremental vs holdout. Secondary: time to first value.
- **Design:** 10% random holdout assigned at `sign_up`. The control receives s1 (every signup expects a welcome; withholding it measures a broken product, not the journey) and none of s2–s5.
- **Routine communications both groups keep:** s1, account confirmation, password and security emails, the product's own default in-app onboarding UI.
- **Contamination:** `trial-conversion` content reaching control users who also started a trial; in-app pointers that the product team ships to everyone outside this journey.
- **Low volume:** with few signups per month the 14-day window detects only large lifts. Fall back to `none_low_volume` with a cohort pre/post comparison of activation rate and time to first value, labeled directional.

## When data is missing

- **No `activation_event` tracked:** run the simple shape, exit on time-out only, report activation as unmeasured and put the event into the tracking plan as a P0 gap.
- **`login` missing or late:** d1 takes the unmeasurable route to s4b (generic story). Missing data is never read as "never came back".
- **`last_completed_step` missing:** s4a links to the core action instead of the exact step.
- **`signup_source` / `onboarding_goal` missing:** generic best-case content; the gap becomes a `progressive-profiling` target.
- **Activation event arrives in daily batches:** the before-each-send check can miss same-day activations. Flag the latency and keep s2–s5 at least 24h apart.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Activation rate within 14 days | primary | activation events / journeys entered, incremental vs holdout |
| Time to first value | secondary | median hours from `sign_up` to `activation_event` |
| Unsubscribe rate per send | guardrail | this list is your freshest; early unsubscribes are the most expensive |

## Common mistakes

- Delaying s1 to batch sends. The welcome is expected immediately; a 6-hour delay reads as neglect.
- Cramming every feature into s1. One first-value action per message; feature tours belong later or in-app.
- Keeping activated users in the educational track. The exit check runs before every send, not once at entry.
- Branching on whether the welcome email was opened. Opens are inflated by privacy proxies and security scanners; use `login` or a product event.
- Sending the returned-but-stuck user back to the beginning of onboarding instead of the step they left.

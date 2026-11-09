---
name: activation
stage: activation
trigger_type: absence
required_events: [sign_up, tutorial_complete]
optional_events: [login, feature_used, session_start, first_open, link_click, error_shown, help_page_view, step_retry, support_case_opened, continue_later_selected, help_declined, consent_withdrawn]
required_attributes: []
optional_attributes: [signup_source, days_since_signup, blocked_step, open_support_case]
default_channels: [email, push, in_app]
base_steps: 4
depth_range: [3, 6]
applicable_industries: [saas, mobile-app, fintech, edtech, marketplace, subscription-media]
mutually_exclusive_with: []
journey_class: marketing
signal_sources: {sign_up: authoritative, tutorial_complete: behavioral, session_start: behavioral, login: behavioral, blocked_step: behavioral, error_shown: behavioral, help_page_view: behavioral, step_retry: behavioral, link_click: engagement, support_case_opened: authoritative, continue_later_selected: behavioral, help_declined: behavioral, consent_withdrawn: authoritative}
insufficient_alone:
  - a single struggle signal
  - high activity that is making progress
  - a click on a rescue message
  - a login without the activation event
exit_before_each_send: [tutorial_complete, consent_withdrawn, support_case_opened, continue_later_selected, help_declined]
reentry: {policy: once, on_duplicate_trigger: ignore}
measurement_default: holdout
---

# Activation Rescue

Rescue users who signed up but never reached the activation event within N days. Distinct from welcome-onboarding: welcome is triggered by `sign_up` and educates everyone; this pattern is triggered by the **absence** of activation after the welcome window closes, and its job is diagnosing and removing the specific blocker. A second, event-triggered variant (in-flow struggle, below) catches users who are visibly trying and not getting anywhere while they are still inside the flow.

`tutorial_complete` stands in for the sector's designated activation event (`feature_used`, first `purchase`, first booking), named per industry playbook.

## Required-event signature

| Event | Source | Role |
|---|---|---|
| `sign_up` | authoritative | Cohort anchor. The absence window counts from here. |
| `tutorial_complete` | behavioral | Both the trigger (its absence since `sign_up`) and the success exit. Without it the pattern is **blocked**: you cannot detect who needs rescuing. |
| `login` / `session_start` *(optional)* | behavioral | Feeds d2: "returned but stuck" (product friction) vs "never came back" (motivation). The two need different messages. |
| `blocked_step` *(optional attr)* | behavioral | Last onboarding step reached; enables blocker-specific how-tos and deep links into the half-done state. |
| `link_click` *(optional)* | engagement | Bot-filtered click on s1; feeds d1. |
| `error_shown` / `step_retry` / `help_page_view` *(optional)* | behavioral | Struggle signals for the in-flow variant. Only count in combination. |
| `support_case_opened` *(optional)* | authoritative | An open case for the same issue suppresses both variants entirely. |
| `continue_later_selected` / `help_declined` *(optional)* | behavioral | The user's own answer to a help offer; both end the instance. |

### Not enough on its own

- **A single struggle signal.** One error, one long dwell, one help-page visit or one retry happens to people who are doing fine. The in-flow variant needs two or more corroborating signals on the same step with no progress behind them.
- **High activity that is making progress.** Someone doing a lot and getting somewhere is the last person to interrupt. Effort without progress is the signal; activity is not.
- **A click on a rescue message.** It routes d1 (bot-filtered) but never counts as activation.
- **A login without the activation event.** It routes d2; it is not success.

## Entry / exit

- **Entry (rescue):** `sign_up` ≥ N days ago, no `tutorial_complete` since `sign_up`, welcome-onboarding completed or exited. N is configurable: default 7 days, tuned to the observed median time-to-activation of users who did activate (evidence to change it: that median, from at least one full cohort).
- **Entry (in-flow struggle variant):** inside an open, unactivated onboarding or trial instance, two or more struggle signals (repeating the same step, a long dwell on one screen, an error message, going back and forth between steps, abandoning a form partway, re-editing a critical field, repeated help-page visits) on the same step, with no step completion since the first of them.
- **Exclude:** activated users; accounts younger than N days (still welcome-onboarding's job, rescue variant only); users who unsubscribed during welcome; anyone with an open support case for the same issue (both variants; the automated offer is the one that does not know the current state).
- **Success exit:** `tutorial_complete` · **Window:** 14 days from entry (rescue); until the stuck step completes or the cascade ends (struggle variant).
- **Checked before every send:** `tutorial_complete`, `consent_withdrawn` scoped to that channel (an email unsubscribe stops the emails, not a consented push or the in-app tier), `support_case_opened`, `continue_later_selected`, `help_declined`. "Continue later" and a decline are exits, not pauses: the offer is not repeated in the same terms afterwards.
- **Re-entry:** rescue runs once ever; afterwards the user moves to a low-frequency digest, not another rescue. The struggle variant may re-enter after a configurable cooldown (default 7 days) for a later struggle inside the same open, unactivated instance. A repeated trigger while an instance is active is ignored.
- **Hand-offs:** a user who opens a support case goes to support, and every queued send is dropped. A rescued user goes to the engagement patterns.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (3) | DQS < 40 or only required events | Friction-removal email → value reminder email → help offer. Entry-anchored, no decision; no push, because without a decision nothing shows the push would pass [push.md](../channels/push.md)'s recency test. |
| Standard (4–5) | DQS 40–69 | Adds the click and returned-vs-never-returned decisions: stuck users get how-tos, absent users get motivation and value content. |
| Branched (6) | DQS ≥ 70 + `blocked_step` | Blocker-specific tracks (stalled at data import vs stalled at the invite step), each with its own fix content. The in-flow struggle variant runs alongside when struggle signals are instrumented. |

## Step blueprint (standard, 4 sends)

| Node | When | Channel | Intent | Route |
|---|---|---|---|---|
| s1 | entry +0h | email | "What got in the way?": name the likely friction, one-click path back to the activation action | → d1 |
| d1 | s1 +20h | — | Decision on any_of(`link_click` on s1 (engagement, bot-filtered), `session_start` (behavioral)) between s1 and s1 +20h | occurred → s2 · not_occurred → d2 · unmeasurable → d2 |
| s2 | d1 +0h | push | Came back (or clicked) and still not activated: deep link straight into the half-done activation step, zero preamble | → d2 |
| d2 | s1 +5d | — | Decision on `session_start` (behavioral) between entry and s1 +5d | occurred → s3a · not_occurred → s3b · unmeasurable → s3a |
| s3a | s1 +5d | email | Returned but stuck: single-blocker how-to matched to `blocked_step`, else the most common blocker | → s4 |
| s3b | s1 +5d | email | Never came back: the value they signed up for, one concrete outcome, one path back | → s4 |
| s4 | s1 +9d | email | Human help: support channel, onboarding call, or reply-to-this-email offer | end |

**Why the push follows a reaction, not its absence.** A user who didn't click s1 may simply not have been reached; that is not a reason for a more intrusive channel. s2 goes to someone whose own action (a click or a session) is under 24h old, which is the reason [push.md](../channels/push.md)'s relevance test accepts. If quiet hours would release s2 more than 24h after that action, s2 is skipped, not delayed. Non-reactors continue by email through d2 (s3a or s3b).

Resumption framing: when the blocker is a half-finished flow (a started import, form or filing), the message offers the **completed path back** (a deep link into the half-done state, "continue with one tap"), not an offer of assistance. "Pick up where you left off" lifts the mental load; "can we help?" hands it back.

For a blocker that is tedious rather than confusing (importing a list, connecting an integration), s4 can go further: a concierge move where a human completes the blocked step *for* the user within a stated service time, then explains how, so the user can self-serve next time. It is a real operational commitment, not a copy choice: propose it only when the business can staff it, and only for the single highest-value blocker.

### In-flow struggle variant (3 touches)

| Node | When | Channel | Intent | Route |
|---|---|---|---|---|
| v1 | entry +0m (in the current session; expires when the session ends) | in_app | Help beside the stuck step: the tip or guide for the likely cause (form error, technical error, doesn't know how, unclear), with three choices: get live help, see the guide, continue later | → vd1 |
| vd1 | v1 +4h | — | Decision on completion of the stuck step (behavioral) between v1 and v1 +4h | occurred → exit · not_occurred → v2 · unmeasurable → v2 |
| v2 | v1 +4h | push | Short nudge back to exactly where they left off, deep link into the step (the struggle is the user's own action under 24h old, which push.md's recency test accepts) | → vd2 |
| vd2 | v1 +1d | — | Decision on completion of the stuck step (behavioral) between v1 and v1 +1d | occurred → exit · not_occurred → v3 · unmeasurable → v3 |
| v3 | v1 +1d | email | Durable summary of the unfinished step with guide and FAQ links, sent together with a live-help offer (chat, ticket, or a time slot) | end |

The cascade stops at the first answer: the step completed, live help requested, "continue later" chosen, or help declined. Each tier exists only because the previous one drew no answer. The help content is free of promotion.

## Timing and channel fit

- Email avoids 00:00–06:00 user local; push respects 22:00–09:00 (see [consent-and-quiet-hours](../compliance/consent-and-quiet-hours.md)). A struggle-variant push that falls in quiet hours waits for 09:00 and is dropped if the step completed meanwhile.
- In-app belongs to the moment of struggle because the user is still on the step. Push is the short way back into the app. Email carries anything that must survive until the user returns: how-tos, the live-help offer.
- No push consent or no token → s2 / v2 is skipped and the path continues on schedule; no email consent → s1, s3, s4 are skipped, and the rescue variant reduces to s2 for users who come back on their own (state this in the journey doc). The struggle variant's in-app tier needs no marketing consent.

## Frequency and overlap

- Worst path in a rolling 7 days: s1, s3a/s3b = 2 emails + 1 push (s4 lands on day 9). Struggle variant: 1 email + 1 push + 1 in-app in 24 hours.
- **Usual overlaps:** `welcome-onboarding` (strictly sequenced: rescue starts only after it ends), `trial-conversion` (an unactivated trialist), `progressive-profiling`.
- **Precedence:** for trialists, `trial-conversion`'s not-activated track owns the rescue content; this pattern does not run in parallel. The struggle variant outranks marketing sends in the same 24 hours: queued marketing touches from other journeys defer until it ends. A negative signal (complaint, escalated ticket) suppresses both variants.

## Measurement

- **Primary outcome:** `tutorial_complete` within 14 days of entry, incremental vs holdout. Secondary: support-contact or reply rate.
- **Design:** 10% random holdout at entry for the rescue variant; the control receives none of s1–s4. For the struggle variant, withholding help from someone visibly stuck is a product decision, not a measurement default: use a holdout only if the brand accepts that; otherwise `pre_post` on stuck-step completion rate, labeled directional.
- **Routine communications both groups keep:** transactional account emails, support replies, the product's own inline error messages and help links.
- **Contamination:** `trial-conversion` help content reaching control trialists; support agents proactively reaching out to stuck users.
- **Low volume:** never-activated cohorts are often small; below the sample-size floor in [measurement.md](../measurement.md), extend the window or report the result as unmeasured rather than as "no effect".

## When data is missing

- **`tutorial_complete` (or the sector's activation event) not tracked:** the pattern is blocked; no rescue without knowing who needs it.
- **`session_start` / `login` missing or late:** d2 takes the unmeasurable route to s3a (the most common blocker), which helps either group. Missing data is not "never came back".
- **Click data missing or not bot-filtered:** an unfiltered click is treated as unmeasurable, not as occurred; d1 still reads `session_start`, and when neither is measurable it takes the unmeasurable route to d2 (no push without a recent own action).
- **Struggle signals instrumented singly or not at all:** do not run the in-flow variant; one signal alone is noise.
- **No support-case feed:** the open-case suppression cannot fire. Record a portfolio-level warning and put the feed into the tracking plan.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Rescued activation rate | primary | activation events within window / journeys entered, incremental vs holdout |
| Support-contact / reply rate | secondary | rescue sequences legitimately convert to human help; count it as a win path |
| Stuck-step completion within 24h (struggle variant) | secondary | completion after v1 / struggle instances opened |
| Unsubscribe rate per send | guardrail | never-activated users leave the list fastest |

## Common mistakes

- Re-sending welcome content with a new subject line. They already ignored it; the angle must change from education to friction removal.
- Triggering while welcome-onboarding is still running. The two are sequenced, or the user gets two activation pitches a day.
- Setting N by gut feel. Derive it from the median time-to-activation of users who did activate; a fixed 7 days is wrong for both same-day products and slow-burn ones.
- Firing the struggle offer on raw activity or on one error. Busy, progressing users are interrupted and stuck ones are not told apart.
- Sending automated help while a support case for the same issue is open, or repeating an offer the user already declined or postponed.

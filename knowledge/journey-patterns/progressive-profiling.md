---
name: progressive-profiling
stage: engagement
trigger_type: segment
required_events: []
optional_events: [purchase, session_start, feature_used, in_app_shown, profile_question_dismissed]
required_attributes: [profile_gap]
optional_attributes: [last_updated_at]
default_channels: [in_app, email]
base_steps: 2
depth_range: [1, 3]
applicable_industries: [ecommerce, saas, mobile-app, fintech, marketplace, subscription-media, travel, edtech, insurance]
mutually_exclusive_with: []
journey_class: marketing
signal_sources: {profile_gap: authoritative, profile_attribute_written: authoritative, last_updated_at: authoritative, session_start: behavioral, feature_used: behavioral, purchase: authoritative, in_app_shown: behavioral, profile_question_dismissed: behavioral, consent_withdrawn: authoritative}
insufficient_alone:
  - a missing attribute with no consuming journey
  - an inferred value for the same attribute
  - a session_start in the first session
exit_before_each_send: [profile_attribute_written, consent_withdrawn, profile_question_dismissed]
reentry: {policy: after_cooldown, cooldown: P14D, on_duplicate_trigger: ignore}
instance_key: profile_gap
measurement_default: pre_post
---

# Progressive Profiling

Collect zero-party data, one lightweight question at a time, to close a **named segmentation gap** that another journey is currently guessing at. This is a support pattern: its output is a profile attribute, not revenue. It exists because a stated answer beats an inferred guess, and because asking five questions at signup loses the user while asking one at the right moment doesn't.

## Required-event signature

| Input | Source | Role |
|---|---|---|
| `profile_gap` (attr) | authoritative | The target. Every run names the missing attribute and the journey that needs it ("category affinity, feeds browse-abandonment branching"). No named gap → do not run. |
| `profile_attribute_written` | authoritative | Success exit: the answer is stored with `last_updated_at`. Re-checked before every send. |
| `session_start` / `feature_used` / `purchase` *(optional)* | behavioral / authoritative | Define the engaged moment: post-purchase, a natural pause, the task the field serves. Never the first thing a new user sees. |
| `in_app_shown` *(optional)* | behavioral | Whether the in-app question was actually displayed; feeds d1. |
| `profile_question_dismissed` *(optional)* | behavioral | The user saw the question and closed it. A dismissal is an answer: the instance ends. |
| `last_updated_at` *(optional attr)* | authoritative | Enables the staleness (TTL) logic below. |

### Not enough on its own

- **A missing attribute with no consuming journey.** Collecting fields nothing branches on is questionnaire theater; entry needs a named consumer.
- **An inferred value for the same attribute.** An inference may justify asking (to confirm it); it never replaces the answer or suppresses the ask by itself.
- **A `session_start` in the first session.** Activity is not an engaged moment; new users are excluded until their first session ends.

## Entry / exit

- **Entry:** user is at an engaged moment, the named attribute is missing **or past its TTL**, and no profiling question was asked within the cooldown.
- **Ask because the task needs it:** the best moment is when the user's current task depends on the field (a delivery preference while ordering, a role while setting up a workspace). The question says why the field is needed and what changes once it is answered. Never request personal data unrelated to the named gap, and never ask to raise a profile-completion percentage.
- **Exclude:** users in their first session, users in an active recovery or dunning journey, users under negative-signal suppression.
- **Success exit:** `profile_attribute_written`. · **Window:** 7 days from entry.
- **Checked before every send:** `profile_attribute_written` and `profile_question_dismissed` for this instance's attribute (`instance_key: profile_gap`; answering a different question doesn't end this one), `consent_withdrawn` scoped to email (it stops the email fallback only; the in-app ask needs no marketing consent). The answer is read from the profile store that records it, never inferred from a click on the email.
- **Re-entry:** next gap or next TTL expiry, after the cooldown (configurable, default 14 days between any two profiling asks). A repeated qualification while an instance is active is ignored.
- **Hand-offs:** the written attribute is handed to the consuming journey named in `profile_gap`.

## TTL / staleness

Volatile fields (sector, role, life stage, current goal) get a TTL, a configurable default of 3–6 months depending on volatility, and a field past its TTL counts as *missing* and is re-asked. Stable fields (birthday, language) get no TTL. Without this, the profile silently rots and journeys branch on a life stage the user left two years ago.

## Depth scaling

Depth does **not** scale with DQS. One question per interaction is the point of the pattern; better data never justifies a longer questionnaire. One in-app question is the norm; a second send is an email fallback for users who never surfaced in-app; a third at most (one reminder, then stop).

## Step blueprint (standard, 2 sends)

| Node | When | Channel | Intent | Route |
|---|---|---|---|---|
| s1 | entry +0h (shown at next session, expires after 7d) | in_app | One question, one tap to answer, shown at the engaged moment, with the reason and the immediate benefit visible ("answer and recommendations change now") | → d1 |
| d1 | s1 +7d | — | Decision on `in_app_shown` for this question (behavioral) between s1 and s1 +7d | occurred → exit · not_occurred → s2 · unmeasurable → s2 |
| s2 | s1 +7d | email | Same single question with the same reason, only for users the in-app ask never reached | end |

A user who saw the question and left it unanswered has answered; the occurred route ends the instance without chasing over another channel. s2 never waits on the in-app ask: it is scheduled at `s1 +7d` whether or not s1 was shown, and the view can only cancel it. A click on s2's link is not an answer; only `profile_attribute_written` is.

Rules: never gate product access behind answering; the answer must visibly change something for the user (recommendations, defaults, content), or the next ask earns silence.

## Timing and channel fit

- In-app first: the question belongs inside the moment it serves, and it needs no marketing consent. Email avoids 00:00–06:00 user local and is sent only with email marketing consent (see [consent-and-quiet-hours](../compliance/consent-and-quiet-hours.md)).
- No push or SMS: a profiling question is never worth an interruption.
- No email consent → s2 is skipped and the instance ends at d1; the gap waits for the next engaged moment after the cooldown.

## Frequency and overlap

- Worst path in a rolling 7 days: 1 in-app; the email falls on day 7, so at most 1 in-app + 1 email.
- **Usual overlaps:** `welcome-onboarding` and `account-onboarding` (both feed it gaps), `post-purchase`, `feedback-nps`.
- **Precedence:** this pattern always yields. It does not ask in the first session, during an onboarding sequence's active send day, while a survey from `feedback-nps` is open, or in the same session as any other in-app prompt. Deferred asks keep their entry and are re-evaluated at the next engaged moment within the window.

## Measurement

- **Primary outcome:** answer rate (attributes written / asks) within 7 days. This pattern is measured on data, not revenue.
- **Design:** `pre_post`. A holdout would only show that people who are not asked do not answer. The value shows up in the consuming journey: compare its branch accuracy or conversion before and after the gap was filled, using that journey's own holdout when it has one.
- **Routine communications both groups keep:** not applicable without a holdout; account settings pages where users can edit their profile at any time stay available to everyone.
- **Contamination:** the same field collected elsewhere (checkout, settings) during the period; record those writes separately by source.
- **Low volume:** answer rate is readable at small volumes; downstream lift usually is not, and is reported as directional.

## When data is missing

- **No named gap or consumer:** do not run.
- **`in_app_shown` not tracked:** d1 takes the unmeasurable route to s2. A user who may never have seen the question is not treated as having declined it.
- **`last_updated_at` missing:** TTL cannot apply; treat volatile fields as fresh for one TTL from the first observed value and record the assumption.
- **`profile_question_dismissed` not tracked:** a dismissal looks like silence; the email fallback may reach someone who already said no. Note the risk and prefer adding the event.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Answer rate (attribute fill) | primary | answers / asks; this pattern is measured on data, not revenue |
| Downstream targeting lift | secondary | did the consuming journey's branch accuracy improve |
| Dismiss/ignore rate | guardrail | rising dismissals mean the wrong moment or too-frequent asks |

## Common mistakes

- Asking without a named consumer. Collecting attributes no journey branches on is questionnaire theater.
- Batching questions ("just three quick things"). One question per interaction is the pattern's entire mechanism.
- Treating every answer as permanent. Volatile fields without TTL make the profile confidently wrong, which is worse than missing.
- Asking without saying why. A field requested with no visible reason reads as data harvesting; the reason and the benefit belong in the question.
- Chasing a dismissed question over email.

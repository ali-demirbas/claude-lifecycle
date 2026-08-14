---
name: progressive-profiling
stage: engagement
trigger_type: segment
required_events: []
optional_events: [purchase, session_start, feature_used]
required_attributes: [profile_gap]
optional_attributes: [last_updated_at]
default_channels: [in-app, email]
base_steps: 2
depth_range: [1, 3]
applicable_industries: [ecommerce, saas, mobile-app, fintech, marketplace, subscription-media, travel, edtech, insurance]
---

# Progressive Profiling

Collect zero-party data — one lightweight question at a time — to close a **named segmentation gap** that another journey is currently guessing at. This is a support pattern: its output is a profile attribute, not revenue. It exists because a stated answer beats an inferred guess, and because asking five questions at signup loses the user while asking one question at the right moment doesn't.

## Required-event signature

| Input | Role |
|---|---|
| `profile_gap` (attr) | The target. Every run of this pattern names the missing attribute and the journey that needs it ("category affinity — feeds browse-abandonment branching"). No named gap → do not run. |
| `session_start` / `feature_used` / `purchase` *(optional)* | Timing anchors: the question is asked at an engaged moment (post-purchase, natural pause), never as the first thing a new user sees. |
| `last_updated_at` *(optional attr)* | Enables the staleness/TTL logic below. |

## Entry / exit

- **Entry:** user is in an engaged moment, has the named attribute missing **or past its TTL**, and hasn't been asked any profiling question within the cooldown (default 14 days).
- **Exclude:** users in their first session, users in an active recovery/dunning journey, users under negative-signal suppression.
- **Success exit:** the attribute is written to the profile (with `last_updated_at`). · **Re-entry:** next gap or next TTL expiry, cooldown respected.

## TTL / staleness

Volatile fields (sector, role, life stage, current goal) get a TTL — a reasonable default is 3–6 months depending on volatility — and a field past its TTL counts as *missing* and gets re-asked. Stable fields (birthday, language) get no TTL. Without this, the profile silently rots and journeys branch on a life stage the user left two years ago.

## Depth scaling

Depth does **not** scale with DQS. One question per interaction is the point of the pattern; more data quality never justifies a longer questionnaire. 1 step (in-app question) is the norm; step 2 is an email fallback for users who don't surface in-app; step 3 at most (one reminder, then stop).

## Step blueprint (standard, 2 steps)

| # | Wait | Channel | Intent | Branch |
|---|------|---------|--------|--------|
| 1 | at next engaged moment | in-app | One question, one tap to answer, with the immediate benefit visible ("answer → better recommendations now") | — |
| 2 | +7d | email | Same single question, only if unanswered and email-appropriate | if step 1 not answered |

Rules: never gate product access behind answering; the answer must visibly change something for the user (recommendations, defaults, content), or the next ask earns silence.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Answer rate (attribute fill) | primary | answers / asks — this pattern is measured on data, not revenue |
| Downstream targeting lift | secondary | did the consuming journey's branch accuracy improve |
| Dismiss/ignore rate | guardrail | rising dismissals = wrong moment or too-frequent asks |

## Common mistakes

- Asking without a named consumer — collecting attributes no journey branches on is questionnaire theater.
- Batching questions ("just three quick things") — one question per interaction is the pattern's entire mechanism.
- Treating every answer as permanent — volatile fields without TTL make the profile confidently wrong, which is worse than missing.

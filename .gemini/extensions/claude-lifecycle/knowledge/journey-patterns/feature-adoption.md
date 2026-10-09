---
name: feature-adoption
stage: engagement
trigger_type: segment
required_events: [feature_used]
optional_events: [login, session_start, search, tutorial_complete, subscription_start, feature_opened, cancellation_intent]
required_attributes: [target_feature]
optional_attributes: [plan_name, engagement_score, feature_eligibility, usage_rhythm_days, risk_case_open]
default_channels: [in_app, email, push]
base_steps: 3
depth_range: [2, 5]
applicable_industries: [saas, mobile-app, fintech, edtech, subscription-media, insurance]
mutually_exclusive_with: []
journey_class: marketing
signal_sources: {feature_used: behavioral, feature_opened: behavioral, session_start: behavioral, search: behavioral, feature_eligibility: authoritative, risk_case_open: authoritative, cancellation_intent: behavioral, engagement_score: inferred, consent_withdrawn: authoritative}
insufficient_alone:
  - general activity without the benefit signal
  - engagement_score
  - opening the feature without using it
exit_before_each_send: [feature_used, consent_withdrawn]
reentry: {policy: after_cooldown, cooldown: P90D, on_duplicate_trigger: ignore}
instance_key: target_feature
measurement_default: holdout
---

# Feature Adoption

Drive usage of one specific undiscovered feature among users whose behavior indicates they would benefit from it. The pattern is deliberately narrow: one feature per journey, one benefit signal defining the audience, success measured as `feature_used` with `feature = target_feature`. It is not a product-updates newsletter: the entry segment must encode *why this user, this feature* (users who repeatedly do by hand what the feature automates). Requires `feature_used` instrumented with a `feature` parameter on both the target feature (success) and adjacent features (audience signal); without the parameter, adoption cannot be detected and the pattern is blocked.

## Required-event signature

| Event | Source | Role |
|---|---|---|
| `feature_used` (with `feature` param) | behavioral | Dual role: success exit when `feature = target_feature` (re-checked before every send), and audience signal when adjacent features show the user would benefit. Without the `feature` param the pattern is **blocked**. |
| `feature_opened` *(optional)* | behavioral | Opened the target feature's screen without completing a use; feeds d1. |
| `login` / `session_start` *(optional)* | behavioral | Confirms the user is active enough for an in-app step; inactive users belong to re-engagement, not adoption. |
| `search` *(optional, with query param)* | behavioral | High-precision benefit signal: users searching for what the feature does are the warmest audience. |
| `tutorial_complete` *(optional)* | behavioral | Distinguishes "never onboarded" from "onboarded but missed this feature"; different copy. |
| `feature_eligibility` *(optional attr)* | authoritative | Plan or permission gate: never promote a feature the user's plan can't reach without labeling it as an upgrade path. |
| `risk_case_open` / `cancellation_intent` *(optional)* | authoritative / behavioral | A live churn-risk case or a declared intent to cancel defers every send (Frequency and overlap). |
| `usage_rhythm_days` *(optional attr)* | behavioral | The product's typical interval between uses; sets the observation window. |

### Not enough on its own

- **General activity without the benefit signal.** "Active and hasn't used X" describes most of the base; it turns a precision pattern into a broadcast.
- **`engagement_score`.** A score can rank the qualified audience; it cannot say that this user would benefit from this feature.
- **Opening the feature without using it.** It routes d1; it is not adoption and does not exit the journey.

## Entry / exit

- **Entry (segment):** active user (recent sessions), never fired `feature_used` for `target_feature`, shows the benefit signal defined for this feature (adjacent-feature usage, relevant `search` queries, or the workflow the feature improves), and the feature is reachable on their plan.
- **Exclude:** users who tried the feature and stopped (a re-adoption problem with different copy); users in trial-conversion (it owns the onboarding narrative); users in dunning; users in an active onboarding journey.
- **Success exit:** `feature_used` with `feature = target_feature`. First use exits; sustained adoption is measured, not messaged.
- **Observation window:** configurable, scaled to the product's usage rhythm. Default: the longer of 21 days or three typical usage intervals (`usage_rhythm_days`, from the median gap between sessions of active users in the segment). A weekly product and a twice-a-year product cannot share one window; a fixed one reports every slow-cycle user as a failure. Evidence to change it: the median time from first exposure to first use among users who adopted on their own. Engagement inside the window does not extend it.
- **Checked before every send:** `feature_used` for this instance's feature only (`instance_key: target_feature`; using another feature never ends it), `consent_withdrawn` scoped to that channel (an email unsubscribe skips s2; in-app steps continue).
- **Re-entry:** once per feature per 90 days (configurable); at most one concurrent adoption journey per user. A repeated qualification while an instance is active is ignored.
- **Hand-offs:** none; adopters return to the normal engagement program.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (2) | DQS < 40 or `feature` param unreliable | In-app pointer + one email explaining the benefit. Coarse audience (all active non-users), no decision. |
| Standard (3) | DQS 40–69 | Adds the behavior-based audience (benefit signal) and a decision on whether the feature was opened but abandoned vs never opened. |
| Branched (4–5) | DQS ≥ 70 + `search` or rich adjacent-feature data | Signal-specific entry copy ("you searched for X"), a contextual in-app trigger at the exact workflow moment, and a post-first-use reinforcement step to turn one use into a habit. |

## Step blueprint (standard, 3 sends)

| Node | When | Channel | Intent | Route |
|---|---|---|---|---|
| s1 | entry +0h (shown at next session, expires after 7d) | in_app | Contextual pointer at the workflow moment the feature improves, shown at the first such moment on or after this time: show, don't announce. Skipped if no such session comes within 7 days; s2 keeps its anchor either way | → s2 |
| s2 | s1 +3d | email | The benefit in the user's own terms: what their current behavior costs, what the feature saves; deep link into the feature | → d1 |
| d1 | s2 +5d | — | Decision on `feature_opened` (behavioral) between entry and s2 +5d | occurred → s3a · not_occurred → s3b · unmeasurable → s3b |
| s3a | s2 +5d (shown at next session, expires after 7d) | in_app | Opened but abandoned: a short how-to for the step where they stopped, shown at the next session | end |
| s3b | s2 +5d (in-app: shown at next session, expires after 7d) | in_app or push | One short reminder with the single-sentence value claim; last touch. In-app by default; push only for a user who opted in to product-tip notifications | end |

After the last send the instance waits out the observation window silently; no further nudge is sent.

Copy rule: name the user's observed behavior, not the feature's marketing name. "You export this report every week; schedule it instead" beats any feature announcement.

## Timing and channel fit

- In-app is the primary channel because the pointer must land at the moment the feature would help. Email carries the explanation with a deep link; push carries only the one-line reminder and respects 22:00–09:00 user local. Email avoids 00:00–06:00 (see [consent-and-quiet-hours](../compliance/consent-and-quiet-hours.md)).
- Send s2 at a time the user is typically active in the product (their own usage hours), not at a fixed broadcast hour.
- s3b is not an escalation for a feature left unopened: a user who didn't open it may not have been reached. In-app is the channel [in-app.md](../channels/in-app.md) names for feature adoption, so s3b goes there by default; push carries it only where the user opted in to product tips, which is the reason [push.md](../channels/push.md)'s relevance test accepts. No push consent or no such opt-in → in-app at the next session. No email consent → s2 is skipped and d1 still runs on schedule.

## Frequency and overlap

- Worst path in a rolling 7 days: 1 email + 2 in-app, or 1 email + 1 in-app + 1 push for a user with a product-tips opt-in.
- **Usual overlaps:** other feature-adoption instances (capped at one concurrent per user), `upsell-cross-sell`, `milestone`, `churn-prevention`, `trial-conversion`.
- **Precedence and defer:** a live churn-risk case, an open issue under human ownership, or a declared cancellation intent on the same user or account means adoption is not the subject. Queued sends defer and are re-evaluated against the current state at their next scheduled time; if the condition is still open when the observation window closes, the instance ends without sending. `trial-conversion` and onboarding journeys exclude entry outright. When the weekly cap would be breached, this journey's send is the one deferred.

## Measurement

- **Primary outcome:** first `feature_used` (target) within the observation window, incremental vs holdout. Secondary: repeat use within a second window of the same length.
- **Design:** 10% random holdout of qualified users at entry; the control receives none of s1–s3.
- **Routine communications both groups keep:** release notes, product-update newsletters, the product's own feature-discovery UI (tooltips, empty states).
- **Contamination:** a general announcement of the same feature reaching the control; in-app UI changes shipped during the window.
- **Low volume:** narrow benefit segments are often small. Below the sample-size floor, pool several features' instances into one holdout comparison, or report the result as unmeasured.

## When data is missing

- **`feature` param missing on `feature_used`:** blocked; the success exit cannot be read.
- **`feature_opened` not tracked:** d1 takes the unmeasurable route to s3b (the generic reminder).
- **`usage_rhythm_days` unknown:** use the 21-day default and state it as an assumption in the journey doc.
- **No risk-case or cancellation-intent feed:** the defer rule cannot fire; record that adoption sends may reach users in a cancellation flow.
- **`feature_eligibility` missing:** promote only features available on every plan, or label the upgrade path explicitly.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Feature adoption rate | primary | first `feature_used` (target) within the observation window / journeys entered, vs a holdout of qualified non-messaged users |
| Repeat usage | secondary | second+ use among adopters within one further window; one forced click is not adoption |
| In-app prompt dismiss rate | guardrail | high dismissals mean the benefit signal or the moment is wrong; fix targeting before copy |

## Common mistakes

- Broadcasting to all users instead of the benefit segment. It turns a precision pattern into a product newsletter and wears out the in-app channel for every future journey.
- Declaring victory on first click. Measure repeat usage; one curiosity click and no habit changed nothing.
- Promoting plan-gated features without the upgrade framing. A user who taps through to an unexpected paywall files it under bait, not discovery.
- One fixed window for every product. A twice-a-year workflow judged on a three-week clock always looks like a failed adoption.
- Pushing a new feature at someone who is in the middle of cancelling.

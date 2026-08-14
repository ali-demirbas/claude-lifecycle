---
name: feature-adoption
stage: engagement
trigger_type: segment
required_events: [feature_used]
optional_events: [login, session_start, search, tutorial_complete, subscription_start]
required_attributes: [target_feature]
optional_attributes: [plan_name, engagement_score, feature_eligibility]
default_channels: [in-app, email, push]
base_steps: 3
depth_range: [2, 5]
applicable_industries: [saas, mobile-app, fintech, edtech, subscription-media, insurance]
---

# Feature Adoption

Drive usage of one specific undiscovered feature among users whose behavior indicates they would benefit from it. The pattern is deliberately narrow: one feature per journey, one benefit-signal defining the audience, success measured as `feature_used` with the target `feature` param. It is not a product-updates newsletter — the entry segment must encode *why this user, this feature* (e.g. users who repeatedly do manually what the feature automates). Requires `feature_used` instrumented with a `feature` parameter on both the target feature (success) and adjacent features (audience signal); without the param, adoption cannot be detected and the pattern is blocked.

## Required-event signature

| Event | Role |
|---|---|
| `feature_used` (with `feature` param) | Dual role: success exit when `feature = target_feature`, and audience signal when adjacent features indicate the user would benefit. Without the `feature` param, pattern is **blocked**. |
| `login` / `session_start` *(optional)* | Confirms the user is active enough to receive an in-app step; inactive users belong to re-engagement, not adoption. |
| `search` *(optional, with query param)* | High-precision benefit signal — users searching for what the feature does are the warmest audience. |
| `tutorial_complete` *(optional)* | Distinguishes "never onboarded" from "onboarded but missed this feature" — different copy. |
| `feature_eligibility` *(optional attr)* | Plan/permission gate: never promote a feature the user's plan can't access without labeling it as an upgrade path. |

## Entry / exit

- **Entry (segment):** active user (recent sessions), has never fired `feature_used` for `target_feature`, and shows the benefit signal defined per feature (adjacent-feature usage, relevant `search` queries, or workflow pattern the feature improves), feature accessible on their plan.
- **Exclude:** users who tried the feature and stopped (that is a re-adoption problem with different copy), users in trial-conversion (it owns the onboarding narrative), users in dunning.
- **Success exit:** `feature_used` with `feature = target_feature` — first use exits; sustained adoption is measured, not messaged · **Window:** 21 days · **Re-entry:** once per feature per 90 days; cap concurrent adoption journeys per user at one.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (2) | DQS < 40 or `feature` param unreliable | In-app pointer + one email explaining the benefit. Audience is coarse (all active non-users). |
| Standard (3) | DQS 40–69 | Adds behavior-based audience (benefit signal) and a follow-up branch on whether the feature was opened but abandoned vs never opened. |
| Branched (4–5) | DQS ≥ 70 + `search` or rich adjacent-feature data | Signal-specific entry copy ("you searched for X"), contextual in-app trigger at the exact workflow moment, and a post-first-use reinforcement step to convert trial into habit. |

## Step blueprint (standard, 3 steps)

| # | Wait | Channel | Intent | Branch |
|---|------|---------|--------|--------|
| 1 | at next session after qualifying | in-app | Contextual pointer at the workflow moment the feature improves — show, don't announce | — |
| 2 | +3d | email | The benefit in the user's own terms: what their current behavior costs, what the feature saves; deeplink into the feature | if no `feature_used` for target |
| 3 | +5d | push | One short reminder with the single-sentence value claim; last touch | if step 2 clicked but feature still unused |

Copy rule: name the user's observed behavior, not the feature's marketing name. "You export this report every week — schedule it instead" beats any feature announcement.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Feature adoption rate | primary | first `feature_used` (target) within window / journeys entered, vs a holdout of qualified non-messaged users |
| 30-day repeat usage | secondary | second+ use among adopters — one forced click is not adoption |
| In-app prompt dismiss rate | guardrail | high dismissals mean the benefit signal is wrong or the moment is wrong; fix targeting before copy |

## Common mistakes

- Broadcasting to all users instead of the benefit segment — turns a precision pattern into a product newsletter and burns the in-app channel for every future journey.
- Declaring victory on first click — measure repeat usage; a journey that produces one curiosity click and no habit changed nothing.
- Promoting plan-gated features without the upgrade framing — a user who taps through to a paywall they didn't expect files that under bait, not discovery.

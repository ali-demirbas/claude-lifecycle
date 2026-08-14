---
name: trial-conversion
stage: revenue
trigger_type: event
required_events: [trial_start, subscription_start]
optional_events: [feature_used, trial_end, login, tutorial_complete, add_payment_info, paywall_view, quota_limit_reached]
required_attributes: [trial_length]
optional_attributes: [plan_name, trial_end_date, activation_score]
default_channels: [email, in-app, push]
base_steps: 6
depth_range: [4, 10]
applicable_industries: [saas, subscription-media, mobile-app, fintech, edtech]
---

# Trial Conversion

Convert trial users into paying subscribers before the trial expires. The P0 journey for any subscription business: the entire monetizable audience passes through it, and it is strictly time-boxed — every step must land inside `trial_length`, so the sequence compresses or stretches with the trial, not with marketing appetite. The core mechanic is branching on **activation depth**: users who reached value (`feature_used` on core features) get a confident conversion ask; users who never activated get help, because selling to someone who hasn't experienced the product converts poorly and churns fast.

## Required-event signature

| Event | Role |
|---|---|
| `trial_start` | Trigger. Journey arms immediately; `trial_length` (attr) sets the clock. |
| `subscription_start` | Success exit. Without it, conversion cannot be measured — pattern is **blocked**. |
| `feature_used` *(optional)* | The activation-depth branch. With a `feature` param, splits activated vs non-activated paths — the single highest-leverage optional event. |
| `trial_end` *(optional)* | Enables a precise post-expiry grace step instead of guessing from `trial_start + trial_length`. |
| `add_payment_info` *(optional)* | Very-high-intent signal; users with card on file get a lighter sequence. |
| `login` / `tutorial_complete` *(optional)* | Cheap activation proxies when `feature_used` isn't instrumented. |
| `paywall_view` *(optional, with dwell param)* | Powers the in-session hesitation pivot in the branched shape — dwell time at the paywall with no action is a readable objection signal. |
| `quota_limit_reached` *(optional, freemium daily-cap apps)* | Alternate, softer entry point alongside `trial_start` — see the Freemium daily-limit entry note below. |

## Entry / exit

- **Entry:** `trial_start` fired, no active subscription, user messageable on ≥ 1 channel (email consent typically collected at signup). **Freemium daily-limit variant:** for apps with a hard daily usage cap on the free tier, `quota_limit_reached` (hitting that cap) is a second, softer entry point — offer a bounded trial invitation at the exact moment of felt friction, rather than waiting for the user to discover and start a trial unprompted. Treat this as an alternate arming event on the same journey, not a separate pattern; a user already mid-trial from this path does not re-enter on the next quota hit. **This does not create a second timing clock:** `quota_limit_reached` only ever fires the trial-invitation offer itself (functionally step 1, sent immediately); every wait in the step blueprint below stays anchored to `trial_start`, which fires only once the user actually accepts the invitation — not at the moment of `quota_limit_reached`, which may be earlier by an unknown, user-controlled delay. A user who never accepts never arms the rest of the sequence.
- **Exclude:** already subscribed on another account/plan (identity-stitched), enterprise/sales-led trials with a human owner, second trial within 90 days (different message needed — returning trialist).
- **Success exit:** `subscription_start` — user leaves immediately · **Window:** trial length + 7-day grace · **Re-entry:** once per distinct trial.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (4) | DQS < 40 or no usage events | Time-based only: welcome → value recap mid-trial → expiry warning → last call. No branching; honest but blunt. |
| Standard (5–7) | DQS 40–69, `login` or `feature_used` present | Adds the activation split mid-trial: activated users get the conversion track, silent users get an obstacle-removal track. |
| Branched (8–10) | DQS ≥ 70 + `feature_used` with `feature` param | Full depth: per-feature activation nudges, `add_payment_info` fast lane, post-`trial_end` grace/win-attempt step, optional human-touch escalation for high-fit silent accounts. With `paywall_view`, adds the in-session hesitation pivot (see blueprint note). |

All depths are bounded by the trial clock: a 7-day trial cannot carry 10 steps without violating frequency caps (email ≤ 4/user/week) — the engine must down-shift depth for short trials regardless of DQS.

## Step blueprint (standard, 6 steps)

| # | Wait | Channel | Intent | Branch |
|---|------|---------|--------|--------|
| 1 | +1h after `trial_start` | email | Welcome: the one action that predicts success in this product ("do X first") | — |
| 2 | +2d | in-app | Nudge toward the core feature; contextual, shown on next session | if no `feature_used` yet |
| 3 | +2d | email | Activated: use-case deepening. Not activated: "what's blocking you?" + help/docs/support offer | split on `feature_used` |
| 4 | at trial midpoint | email | Progress recap: what they've done, what stays behind on free/expiry | — |
| 5 | 72h before trial end | email | Expiry notice: date, price, what happens to their data. Plain and factual. | — |
| 6 | 24h before trial end | push | Last call, deeplink to upgrade. State the real deadline only. | if step 5 not clicked |

Hesitation pivot (branched shape): a user who reaches the paywall and hesitates — a dwell-time threshold with no action, tuned per product — is signalling that the ask arrived before the value case was made. Pivot in-session to a bounded, clearly-labeled unlock of *one* pro feature (e.g. 24h), then return to the ask. Strictly one-time per trial, never a repeatable offer; a decliner re-enters the standard sequence where they left off.

Discount rule: no discount inside the standard flow. If the business allows one, it belongs in a *post-expiry* winback step for activated non-converters only — discounting mid-trial teaches everyone to wait. Incentive choice follows the CLV-tied rule: above the account's CLV threshold prefer a value-add (extended trial of one feature, priority support, early access) over a discount; below it, a capped modest discount (see intake incentive policy).

## KPIs

| KPI | Type | Note |
|---|---|---|
| Trial-to-paid conversion rate | primary | `subscription_start` within window / trials entered |
| Activation rate mid-trial | secondary | share reaching `feature_used` on a core feature — the leading indicator the journey actually moves |
| Unsubscribe rate per send | guardrail | short trials concentrate sends; watch this harder than in any other pattern |

## Common mistakes

- Same sequence for activated and silent users — the conversion ask lands on people who never saw value, and the help content lands on people ready to buy.
- Ignoring the trial clock when scaling depth — an 8-step sequence in a 7-day trial breaches weekly frequency caps by design.
- Hiding the expiry — burying the end date to "reduce churn risk" produces refund requests and chargebacks instead of conversions; state date and price plainly.
- Repeating the same paywall ask harder at a hesitating user instead of changing the move — hesitation means the value case is missing, not that the volume was too low.

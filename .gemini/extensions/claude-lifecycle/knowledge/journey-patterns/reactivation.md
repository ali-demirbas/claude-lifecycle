---
name: reactivation
stage: engagement
trigger_type: segment
required_events: [session_start]
optional_events: [sign_up, first_open, login, purchase, app_remove]
required_attributes: []
optional_attributes: [days_dormant, acquisition_source, last_screen, push_token_valid]
default_channels: [push, email]
base_steps: 3
depth_range: [3, 6]
applicable_industries: [mobile-app, saas, marketplace, subscription-media, edtech, ecommerce, fintech, travel]
---

# Reactivation

Bring back dormant **non-customers**: users who signed up or installed, never converted to revenue, and have gone quiet. Distinct from winback on both audience and goal — winback targets lapsed *customers* and exits on purchase; reactivation targets never-converted users and exits on a **return session**, handing returners to activation or revenue patterns. Mixing the two audiences wastes winback economics on users who never had any.

## Required-event signature

| Event | Role |
|---|---|
| `session_start` | Both sides of the pattern: its absence defines dormancy, its return is the success exit. Without it, pattern is **blocked**. |
| `purchase` *(optional but important)* | Exclusion signal — any lifetime purchase routes the user to winback instead. Untracked, the two audiences cannot be separated and this journey silently absorbs lapsed customers. |
| `app_remove` *(optional, Android)* | Uninstallers are unreachable by push; they get the email-only branch automatically. |
| `acquisition_source` *(optional attr)* | The original promise that acquired them is the best reactivation hook; match content to it. |
| `push_token_valid` *(optional attr)* | Channel routing: dead tokens waste the journey's strongest channel on silence. |

## Entry / exit

- **Entry:** last `session_start` older than the dormancy threshold (default 21–30 days; tune to the product's natural usage cadence), zero lifetime `purchase`, valid consent or push token on ≥ 1 channel.
- **Exclude:** any past purchaser (winback owns them), users currently in activation-rescue (dormancy inside the first weeks is activation's problem), consent silent > 2 years (re-permission first).
- **Success exit:** `session_start` or `login` — revenue is explicitly *not* this journey's exit; returners hand off to activation/revenue patterns · **Window:** 14 days · **Re-entry:** once per 60 days, max 3 lifetime cycles, then sunset for list hygiene.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (3) | DQS < 40 or only `session_start` | What's-new push → value email → sunset ask. Fixed dormancy threshold. |
| Standard (4–5) | DQS 40–69 | Adds `acquisition_source`-matched content and `app_remove`/token-aware channel routing. |
| Branched (6) | DQS ≥ 70 + `last_screen` or `acquisition_source` | Splits by last-seen context (resume where they left off) vs long-dormant (fresh-start framing); uninstallers on a dedicated email track. |

## Step blueprint (standard, 3 steps)

| # | Wait | Channel | Intent | Branch |
|---|------|---------|--------|--------|
| 1 | on entry | push | What's genuinely new since their last visit, deeplinked to the freshest relevant content (22:00–09:00 quiet hours) | email instead if `app_remove` or dead token |
| 2 | +3d | email | The concrete value they never tried, matched to `acquisition_source` when known | if no return session |
| 3 | +7d | email | Honest last touch: "should we stop?" — preference center or snooze, doubling as the sunset mechanism | — |

## KPIs

| KPI | Type | Note |
|---|---|---|
| Return session rate | primary | `session_start` within window / journeys entered |
| Downstream activation rate of returners | secondary | a return that bounces in 10 seconds is not a win; measure what returners do next |
| Push opt-out + uninstall rate after send | guardrail | reactivation push is the top driver of opt-outs; a spike here costs the channel for every journey |

## Common mistakes

- Letting past customers into the audience — they belong in winback, with revenue exits and offer economics this journey deliberately lacks.
- Sending "we miss you" with nothing behind it — dormant users left for a reason; the message must state a concrete change, new content, or untried value.
- Cycling dormant users forever — without the lifetime cap and sunset step, this journey degrades deliverability and push opt-in rates portfolio-wide.

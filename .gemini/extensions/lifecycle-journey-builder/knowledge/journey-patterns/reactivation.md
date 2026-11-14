---
name: reactivation
stage: engagement
trigger_type: segment
journey_class: marketing
required_events: [session_start]
optional_events: [login, purchase, app_remove, preference_updated, consent_withdrawn]
required_attributes: []
optional_attributes: [days_dormant, acquisition_source, last_screen, push_token_valid, reactivation_reason]
default_channels: [push, email]
base_steps: 3
depth_range: [3, 6]
applicable_industries: [mobile-app, saas, marketplace, subscription-media, edtech, ecommerce, fintech, travel]
mutually_exclusive_with: []
signal_sources: {session_start: behavioral, login: behavioral, purchase: authoritative, app_remove: behavioral, preference_updated: authoritative, push_token_valid: authoritative, acquisition_source: behavioral, last_screen: behavioral, days_dormant: behavioral, consent_withdrawn: authoritative}
insufficient_alone:
  - no session on one surface while another surface is active
  - another inactive period with nothing new to say
  - email opens
  - an uninstall without checking the other surfaces
exit_before_each_send: [session_start, login, purchase, consent_withdrawn]
reentry: {policy: after_cooldown, cooldown: P60D, on_duplicate_trigger: ignore}
measurement_default: holdout
---

# Reactivation

Bring back dormant **non-customers**: users who signed up or installed, never converted to revenue, and have gone quiet. Distinct from [winback](winback.md) on both audience and goal: winback targets lapsed *customers* and exits on purchase; reactivation targets never-converted users and exits on a **return session**, handing returners to activation or revenue patterns. Mixing the two audiences wastes winback economics on users who never had any.

## Required-event signature

| Event | Source | Role |
|---|---|---|
| `session_start` | behavioral | Both sides of the pattern: its absence defines dormancy, its return is the success exit. Without it, pattern is **blocked**. |
| `login` *(optional)* | behavioral | Second return signal, and the one that joins web and app activity to the same person. |
| `purchase` *(optional but important)* | authoritative | Exclusion signal: any lifetime purchase routes the user to winback instead. Untracked, the two audiences cannot be separated and this journey silently absorbs lapsed customers. |
| `app_remove` *(optional, Android)* | behavioral | Uninstallers are unreachable by push; they get the email-only branch automatically. |
| `acquisition_source` *(optional attr)* | behavioral | The original promise that acquired them is the best reactivation hook; match content to it. |
| `push_token_valid` *(optional attr)* | authoritative | Channel routing: dead tokens waste the journey's strongest channel on silence. |
| `reactivation_reason` *(optional attr)* | authoritative | What is new or untried that justifies this attempt (see Entry); recorded per cycle. |

### Not enough on its own

- **No session on one surface while another surface is active.** Someone who stopped opening the app but still uses the website, or who is active in a sibling product under the same account, is not dormant. Dormancy is measured across every surface where the identity is joined.
- **Another inactive period with nothing new to say.** Going quiet again does not by itself earn another campaign. Each attempt needs its own reason: a real product change, new content matched to their interest, or value they demonstrably never tried.
- **Email opens.** Unreliable under privacy proxies; nothing here branches on them.
- **An uninstall without checking the other surfaces.** `app_remove` changes the channel, not the dormancy verdict; a web-active uninstaller is not dormant.

## Entry / exit

- **Entry:** last `session_start` (across all joined surfaces) older than the dormancy threshold (default 21–30 days; tune to the product's natural usage cadence; where the industry playbook's `churn_signal` sets a dormancy clock and states a sector override, as [mobile-app](../industries/mobile-app.md) does, that clock is the threshold), zero lifetime `purchase`, valid consent or push token on ≥ 1 channel, and a recorded `reactivation_reason` for this attempt.
- **Exclude:** any past purchaser (winback owns them), users currently in activation-rescue (dormancy inside the first weeks is activation's problem), users active on another surface or product, consent silent > 2 years (re-permission first), users under the portfolio negative-signal override.
- **Success exit:** `session_start` or `login`. Revenue is explicitly *not* this journey's exit; returners hand off to activation/revenue patterns · **Window:** 14 days.
- **Checked before each send:** `session_start`, `login`, `purchase` (hand off; the person is now a customer), `consent_withdrawn` (channel-scoped: an email unsubscribe stops the email steps, a revoked push permission or invalid token stops push; neither moves the message to another channel on its own).
- **Re-entry:** after a 60-day cooldown, max 3 lifetime cycles, and only with a new `reactivation_reason` each time; a repeated trigger while an instance is open is ignored. Without a new reason, or after the third cycle, the person goes to [unengaged-sunset](unengaged-sunset.md) instead of another campaign.
- **Handoffs:** return session → [welcome-onboarding](welcome-onboarding.md) or [activation](activation.md), only a journey the person has **never entered** (both run `reentry: once`, so a handoff to one already entered would silently go nowhere); if the person already entered both, → [feature-adoption](feature-adoption.md) where it applies, otherwise no handoff (the return session is the success). `purchase` → [post-purchase](post-purchase.md). Queued reactivation sends are suppressed in both cases. Inbound from [trial-conversion](trial-conversion.md): non-converting trialists arrive here after the trial's grace step (they never qualify for winback, which needs a past purchase).

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (3) | DQS < 40 or only `session_start` | What's-new push → value email → preference ask. Fixed dormancy threshold. |
| Standard (4–5) | DQS 40–69 | Adds `acquisition_source`-matched content and `app_remove`/token-aware channel routing. |
| Branched (6) | DQS ≥ 70 + `last_screen` or `acquisition_source` | Splits by last-seen context (resume where they left off) vs long-dormant (fresh-start framing); uninstallers on a dedicated email track. |

## Step blueprint (standard, 3 sends)

| Node | When | Channel | Intent | Route |
|---|---|---|---|---|
| s1 | entry +0h, delivered at the next 18:00 user_local | push (email if `app_remove` or invalid token) | What's genuinely new since their last visit, deeplinked to the freshest relevant content | → s2 |
| s2 | s1 +3d | email | The concrete value they never tried, matched to `acquisition_source` when known | → s3 |
| s3 | s1 +10d | email | Honest last touch: "should we stop?" with a link to the preference center for snooze, fewer messages or stop. The choice applies only once the preference system records it as `preference_updated` with its value; a click on the link is not a choice | → exit (expired) at entry +14d |

No decision rows: the only branch the old blueprint had ("if no return session") is enforced by the before-each-send exit check, and channel routing is a fallback on token state, not a behavioral branch. One reachable channel per step, not every channel at once.

## Timing and channel fit

- **Push** fits s1 when the token is valid: the deeplink takes the user straight into the new content. Push quiet hours 22:00–09:00 user local are mandatory.
- **Email** carries the longer value explanation and the preference choice. Avoid 00:00–06:00 user local.
- **Fallback:** uninstalled or invalid token → s1 goes by email; no email consent → s2/s3 are dropped and the journey is a single push. No reachable channel → not eligible.
- SMS is deliberately absent: the cost and intrusiveness don't fit people who never bought.

## Frequency and overlap

- **Worst path:** 2 sends in the first rolling 7 days (s1, s2), then 1.
- **Usually overlaps with:** [activation](activation.md), [welcome-onboarding](welcome-onboarding.md), [lead-nurture](lead-nurture.md), [channel-opt-in](channel-opt-in.md), [unengaged-sunset](unengaged-sunset.md).
- **Precedence:** activation-rescue owns users in their first weeks; this journey does not start for them. A lead-nurture instance already running for the same person wins and this journey is skipped for the cycle. Unengaged-sunset outranks it once the person is in sunset.

## Measurement

- **Primary outcome:** `session_start` within 14 days.
- **Design:** holdout (default 10%), user-level. The control does not receive s1–s3.
- **Routine communications both groups keep:** transactional/account messages and any product announcement sent to the whole user base.
- **Contamination risks:** paid re-engagement campaigns targeting the same dormant audience; app-store or OS-level re-engagement prompts; notifications from a sibling product.
- **Low volume:** returns happen without messages too, so a raw return rate overstates the journey. When the power calculation shows the control arm can't detect a plausible lift, report it as unmeasured; downstream activation of returners can still be described per arm.

## When data is missing

- **No `purchase` tracking:** the pattern cannot separate never-bought from lapsed; it runs only with that caveat in the journey doc, and winback is not run alongside it.
- **Web and app identities not joined:** dormancy is computed per surface, and the journey doc flags that some "dormant" users may be active elsewhere; recommend login-based joining.
- **No `acquisition_source`:** generic value content in s2.
- **Token state unknown:** push is attempted once; an undeliverable result moves the remaining steps to email.
- **No `reactivation_reason`:** the attempt is not started; "they went quiet" is not a reason.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Return session rate | primary | `session_start` within window / journeys entered, compared with the holdout |
| Downstream activation rate of returners | secondary | a return that bounces in 10 seconds is not a win; measure what returners do next |
| Push opt-out + uninstall rate after send | guardrail | reactivation push is the top driver of opt-outs; a spike here costs the channel for every journey |

## Common mistakes

- Letting past customers into the audience: they belong in winback, with revenue exits and offer economics this journey deliberately lacks.
- Treating an app-quiet but web-active user as dormant.
- Sending "we miss you" with nothing behind it: dormant users left for a reason; the message must state a concrete change, new content, or untried value.
- Cycling dormant users forever: without the lifetime cap, the per-attempt reason and the handoff to unengaged-sunset, this journey degrades deliverability and push opt-in rates portfolio-wide.

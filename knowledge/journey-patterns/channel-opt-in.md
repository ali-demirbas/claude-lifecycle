---
name: channel-opt-in
stage: engagement
trigger_type: segment
required_events: [consent_updated]
optional_events: [add_to_wishlist, purchase, session_start, notification_open, consent_ask_dismissed, consent_withdrawn]
required_attributes: [channel_consent_status]
optional_attributes: [push_permission_status, consent_ask_history, engagement_score]
default_channels: [in_app, email]
base_steps: 2
depth_range: [1, 3]
applicable_industries: [ecommerce, saas, mobile-app, fintech, marketplace, subscription-media, travel, edtech, insurance]
mutually_exclusive_with: []
journey_class: marketing
signal_sources: {consent_updated: authoritative, channel_consent_status: authoritative, consent_withdrawn: authoritative, push_permission_status: authoritative, consent_ask_history: authoritative, consent_ask_dismissed: behavioral, add_to_wishlist: behavioral, purchase: authoritative, session_start: behavioral, notification_open: engagement, engagement_score: inferred}
insufficient_alone:
  - an open asking channel
  - a tapped yes with no record in the consent system
  - time passed since an opt-out or a withdrawal
  - an OS push permission with no stated purpose behind it
exit_before_each_send: [consent_updated, consent_withdrawn]
reentry: {policy: after_cooldown, cooldown: P60D, on_duplicate_trigger: ignore}
measurement_default: holdout
instance_key: target_channel
---

# Channel Opt-In

Win consent on a channel the user doesn't have yet, by asking through one they already do. Every other pattern in this engine assumes the channel is open; this is the pattern that opens it. The asymmetry that makes it work: **in-app is the only zero-consent channel** (see [in-app.md](../channels/in-app.md)): anyone with a live session is askable, so in-app is the default asking surface, falling back to whichever consented channel exists (in-app > push > email > SMS by cost and intrusiveness). The ask itself is a marketing message and must respect the asking channel's own consent, caps, and quiet hours: you cannot ask for SMS consent via SMS.

The core rule: **the ask is value-first and moment-tied, never a bare "enable notifications."** Ask for push right after `add_to_wishlist` ("we'll tell you the moment it's back"), for SMS right after `purchase` ("instant shipping updates"), for email at a moment its content has obvious value. The stated value must match what will actually be sent: winning SMS consent with "shipping updates" and then sending promo blasts is consent bait-and-switch and a compliance liability, not a growth win.

Two boundaries frame everything below. **An open channel carries this one request and nothing else**: being reachable on email to ask about SMS doesn't license bundling a promotion, a second request, or a follow-up campaign into that ask, and a grant won for a stated purpose covers that purpose only. **A closed channel stays closed until the user reopens it**: this journey never targets a channel the user turned off or withdrew, never re-asks for it on a schedule, and never reactivates it automatically. Re-permission is something the user does (a preference centre, account settings, a "notify me" they tap themselves), recorded by an authoritative consent event; it is not a journey step.

## Required-event signature

| Event | Source | Role |
|---|---|---|
| `consent_updated` | authoritative (consent system, with `channel` + `status` + `purpose`) | Success exit and the measurement backbone. If consent changes can't be recorded per channel, the journey can't be measured **and** the grant can't be legally evidenced (İYS/TCPA/GDPR require provable opt-in): pattern is **blocked**. |
| `channel_consent_status` (required attr) | authoritative (consent system) | The per-channel reachability map that defines entry: open on ≥ 1 channel, never-granted on the target channel. It must distinguish never-granted from withdrawn. |
| `consent_withdrawn` *(optional)* | authoritative (consent system) | A withdrawal on the asking channel ends the journey; a withdrawal on the target channel excludes the user from this pattern for that channel. |
| `add_to_wishlist` / `purchase` *(optional)* | behavioral / authoritative | The value moments that arm a contextual ask: a wishlist add is the natural push-permission moment, an order is the natural SMS moment. |
| `push_permission_status` *(optional attr)* | authoritative (OS permission state, read on device each session) | The platform's own permission state (see push mechanics below for the iOS and Android states). Device-level permission to display notifications; it is not marketing consent. |
| `consent_ask_dismissed` *(optional)* | behavioral | An explicit "no thanks" on the soft ask; ends this instance and counts toward the permanent stop. |
| `notification_open` *(optional)* | engagement | Post-grant health signal only: consent that is never engaged is the leading indicator of a future opt-out. Never a branch. |

### Not enough on its own

- **An open asking channel:** reachability on one channel is permission to send what that channel was granted for, plus this single, promotion-free request. It is not permission for anything else on that channel.
- **A tapped yes with no record in the consent system:** a button tap that isn't evidenced in the consent system is a journey "success" a regulator reads as unconsented sending. Only `consent_updated` from the consent system counts.
- **Time passed since an opt-out or a withdrawal:** consents don't come back by aging. A user who turned a channel off two years ago is as closed today as the day they did it.
- **An OS push permission with no stated purpose behind it:** the OS dialog says nothing about what will be sent, and an OS permission is not marketing consent. The purpose stated in the soft ask, recorded as `consent_updated` with that purpose where the market's regime requires consent for marketing push, is what the grant covers.

## Entry / exit

- **Entry (segment):** user messageable on ≥ 1 consented channel, target channel **never granted** (not withdrawn), no opt-in ask for that channel in the last 60 days, and, where a contextual trigger is configured, the value moment just fired.
- **Exclude:** users who opted *out* of, withdrew, or turned off the target channel (a past opt-out is a decision, not a gap; there is no automatic route back, see the boundary above), push users whose OS permission is denied, detractors and anyone under negative-signal suppression ([consent-and-quiet-hours.md](../compliance/consent-and-quiet-hours.md) rule 4), users in dunning.
- **Success exit:** `consent_updated` grant for the target channel · **Window:** 14 days.
- **Instance key:** `target_channel`, one instance per channel being asked for.
- **Checked before each send:** `consent_updated` for the target channel (`same_instance`; a grant ends the journey, including one the user made on their own elsewhere; a grant on a different channel does not), `consent_withdrawn` on the asking channel (channel-scoped: it stops the asks sent on that channel; nothing switches to another channel to continue asking). A withdrawal on the target channel excludes the user from this pattern for that channel.
- **Re-entry:** per target channel, once per 60 days (configurable up to 90), and stop permanently after 2–3 ignored asks or one explicit "no": the same restraint rule as [referral](referral.md). Reachability is a favor the user grants, not a metric to be extracted. A repeated value moment while an instance is active is ignored.
- **Handoffs:** a grant unlocks journeys and depth upgrades in the tracking plan; the newly opened channel is used only for the purpose stated in the ask.

## Push mechanics (platform constraint, not a style choice)

The two platforms behave differently, so the journey reads `push_permission_status` per platform instead of assuming one rule. Behavior also shifts between OS versions; confirm against the current platform documentation for the app's target versions before launch.

**iOS.** States: *not determined* (the app has never shown the system prompt), *authorized*, *provisional* (quiet delivery granted without a prompt, where the app requested it), *denied*. The system prompt can be shown once, while the state is not determined; after the user answers, the app cannot show it again, and only the device Settings can change the state. Provisional is permission to deliver quietly, not a yes to prominent alerts.

**Android.** The state depends on the OS version and the app's target SDK:
- *Below Android 13:* notifications are allowed at install with no runtime dialog; the user can turn them off in Settings, per app or per notification channel. Read the state (enabled, or blocked in Settings); there is nothing to ask for.
- *Android 13+ with an app targeting 13+:* notification permission is a runtime permission and the app decides when the dialog appears, so the soft-ask sequencing below applies. States: *not requested*, *granted*, *denied (can ask again)*, *denied and blocked*: after repeated denials (two, on current versions) the system stops showing the dialog and only Settings can grant it.
- *Android 13+ with an app targeting 12L or lower:* the system shows the dialog itself when the app creates its first notification channel, so the app does not control the timing and cannot place a soft ask before it. Raising the target SDK is the fix; until then this journey does not sequence the Android prompt.
- Devices upgraded to 13 may carry a granted state for apps that already had notifications enabled. Read the state; never infer it from the OS version.

**Common to both.** The OS permission is not marketing consent. It lets the app display notifications; whether a marketing push may be sent is decided by the consent record and the purpose stated in the soft ask. So the pattern never spends the system prompt cold:

1. **Soft ask first** (in-app, skippable): state the concrete value, then ask "enable?". A "not now" here costs nothing and preserves the system prompt for a later, better moment.
2. **System prompt only on soft-ask yes**, fired immediately while intent is hot, and only where the app controls its timing (iOS not determined; Android 13+ targeting 13+, not requested or denied-but-askable).
3. **Denied with no prompt left** (iOS denied; Android denied and blocked, or turned off in Settings): the journey does not ask again. If the user later starts something that only works with push (taps "notify me when it's back"), the product itself explains that notifications are off and how to turn them on in Settings. That is the user's own action in the moment, not a scheduled re-ask, and it is never pretended to be a re-prompt.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (1) | DQS < 40 or no contextual events | One value-framed ask on the best open channel, timed to session activity. |
| Standard (2) | DQS 40–69 | Soft-ask → native-prompt sequencing for push; one restatement on a second open channel if the first ask was ignored (not declined). |
| Branched (3) | DQS ≥ 70 + `push_permission_status` and contextual events | Moment-tied asks per target channel (wishlist→push, order→SMS), never-asked vs denied split (denied is excluded from asks; the in-product Settings explanation handles user-initiated cases), plus a confirmation after a grant stating exactly what the channel will be used for. |

Depth stays shallow at every tier by design: an opt-in ask is one question. Extra DQS buys better *moments* and honest *state-awareness*, never more asks.

## Step blueprint (standard, 2 sends)

| Node | When | Channel | Intent | Route |
|---|---|---|---|---|
| a1 | entry +0h | in_app (fallback: best consented channel) | The value-first ask at the value moment: one concrete benefit tied to what the user just did, then the opt-in action (soft ask for push). No promotion bundled in. In-app: shown in the value-moment session or the next one, expires after 5d; d1 and a2 use a1's scheduled time, never the view | → d1 |
| d1 | a1 +5d | — | Decision on `consent_ask_dismissed` (behavioral) between a1 and a1 +5d | occurred → exit (completed; a no is respected) · not_occurred → a2 · unmeasurable → a2 |
| a2 | d1 +0h at 10:00 user_local | email (only with marketing consent on email) | One restatement of the same benefit with the opt-in link; nothing new, no pressure, no other content | → exit (completed) |

A grant at any point ends the instance before the next send. Branched depth adds one confirmation after a grant (`consent_updated +0h`, on the newly granted channel): what will be sent there, how often, and how to turn it off. It is the first message on that channel and sets the purpose the grant covers.

Consent capture rule: the grant must be recorded the way the target channel's regime requires (İYS registration for TR SMS/email, prior express written consent for US SMS, explicit opt-in for GDPR). Never pre-check boxes, never bundle channels into one yes.

The payoff is downstream: every grant unlocks blocked journeys and depth upgrades in the tracking plan (push unlocks [back-in-stock](back-in-stock.md)'s speed, SMS unlocks [payment-failure](payment-failure.md)'s urgency tier). The portfolio should name what each opt-in unlocks: that's also the honest way to prioritize which channel to ask for first.

## Timing and channel fit

- In-app asks happen inside the session at the value moment; they have no clock beyond that.
- An email restatement goes in daytime on the user's clock; push and SMS asks (asking for email via push, for example) respect their quiet hours per [consent-and-quiet-hours.md](../compliance/consent-and-quiet-hours.md).
- The asking channel needs its own marketing consent; a channel open only for service messages (order updates) does not carry the ask. No marketing-consented channel and no session → no ask.

## Frequency and overlap

- **Worst path:** 2 asks in 5 days for one target channel; one target channel per instance, never a wall of requests for several channels at once.
- **Overlaps:** [referral](referral.md) (also a favor ask), [welcome-onboarding](welcome-onboarding.md) (often carries a first opt-in moment), [back-in-stock](back-in-stock.md) (the wishlist moment).
- **Precedence:** service messages first; an opt-in ask and a referral ask never land in the same week (the later one defers); onboarding's own opt-in moment wins over this journey during the first week.

## Measurement

- **Primary outcome:** grant rate per target channel within 14 days, split never-asked vs previously-ignored.
- **Design:** user-level holdout (default 10%). The control receives no ask from this journey; organic grants (settings, checkout checkbox) remain available to both and form the baseline.
- **Routine communications both groups keep:** service messages, any opt-in checkbox the product shows in its own flows (checkout, signup).
- **Contamination risks:** onboarding or checkout flows that ask for the same channel; app-version changes that move the native prompt.
- **Low volume:** grant rates on a small base are noisy; measure per channel over a full month and report counts with rates. Post-grant retention (still opted in 90 days later) needs longer windows.

## When data is missing

- **`channel_consent_status` can't distinguish never-granted from withdrawn:** the journey does not run for that channel. Asking a withdrawn user because the data can't tell is exactly the reactivation this pattern forbids.
- **No `push_permission_status`:** treat as not determined only on fresh installs; for everyone else, the soft ask runs but the system prompt fires only on its yes, and only on a platform and target SDK where the app controls the prompt's timing.
- **No `consent_ask_dismissed`:** d1 is unmeasurable and a2 goes once; the ignored-ask cap still stops repeats.
- **No `consent_ask_history`:** default to the strictest reading: assume an ask happened within the cooldown and wait.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Opt-in rate per target channel | primary | grants within window / asks delivered, vs holdout, split never-asked vs previously-ignored |
| Native-prompt acceptance rate (push) | secondary | accepts / native prompts fired: measures soft-ask gating quality; a low rate means the soft ask is qualifying badly |
| Ask dismiss/ignore rate + asking-channel opt-out | guardrail | rising dismissals mean the moment or the value framing is wrong; an unsubscribe from the *asking* channel is the worst outcome this pattern can produce |

## Common mistakes

- Firing the system push prompt cold at first open: the most common way apps lose their highest-reach channel; always soft-ask first where the app controls the prompt's timing.
- Treating an OS push permission as marketing consent, or describing both platforms as one-shot: iOS and Android keep different states, and neither state says what the user agreed to receive.
- A bare "turn on notifications" with no concrete value: the user is being asked to pay attention forward; the ask must say what they get.
- Asking for every closed channel at once: one target channel per journey instance; a consent wall reads as a shakedown.
- Re-asking on a timer regardless of declines: 2–3 ignored asks or one explicit no is the permanent stop; a declined ask is data, not a retry queue.
- Treating an old opt-out as an opt-in gap, or "reactivating" a withdrawn channel because enough time passed: a closed channel reopens only when the user reopens it, recorded in the consent system (see the consent-age rule in [consent-and-quiet-hours.md](../compliance/consent-and-quiet-hours.md) for long-silent but never-withdrawn contacts).
- Bundling a promotion into the ask because the channel is open anyway.
- Promising one kind of content to win the grant and sending another: the fastest route from opt-in to spam complaint.

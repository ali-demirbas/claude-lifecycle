---
name: channel-opt-in
stage: engagement
trigger_type: segment
required_events: [consent_updated]
optional_events: [add_to_wishlist, purchase, session_start, notification_open]
required_attributes: [channel_consent_status]
optional_attributes: [push_permission_status, consent_ask_history, engagement_score]
default_channels: [in-app, email]
base_steps: 2
depth_range: [1, 3]
applicable_industries: [ecommerce, saas, mobile-app, fintech, marketplace, subscription-media, travel, edtech, insurance]
---

# Channel Opt-In

Win consent on a channel the user doesn't have yet, by asking through one they already do. Every other pattern in this engine assumes the channel is open; this is the pattern that opens it. The asymmetry that makes it work: **in-app is the only zero-consent channel** (see [in-app.md](../channels/in-app.md)) — anyone with a live session is askable, so in-app is the default asking surface, falling back to whichever consented channel exists (in-app > push > email > SMS by cost and intrusiveness). The ask itself is a marketing message and must respect the asking channel's own consent, caps, and quiet hours — you cannot ask for SMS consent via SMS.

The core rule: **the ask is value-first and moment-tied, never a bare "enable notifications."** Ask for push right after `add_to_wishlist` ("we'll tell you the moment it's back"), for SMS right after `purchase` ("instant shipping updates"), for email at a moment its content has obvious value. The stated value must match what will actually be sent — winning SMS consent with "shipping updates" and then sending promo blasts is consent bait-and-switch and a compliance liability, not a growth win.

## Required-event signature

| Event | Role |
|---|---|
| `consent_updated` | Success exit and the measurement backbone (custom, with `channel` + `status` params). If consent changes can't be recorded per channel, the journey can't be measured **and** the grant can't be legally evidenced (İYS/TCPA/GDPR require provable opt-in) — pattern is **blocked**. |
| `channel_consent_status` (required attr) | The per-channel reachability map that defines entry: who is open on ≥ 1 channel and closed on the target channel. |
| `add_to_wishlist` / `purchase` *(optional)* | The value moments that arm a contextual ask — a wishlist add is the natural push-permission moment, an order is the natural SMS moment. |
| `push_permission_status` *(optional attr)* | Splits never-asked from asked-and-declined on push — the two need entirely different treatment (see push mechanics below). |
| `notification_open` *(optional)* | Post-grant health signal: consent that is never engaged is the leading indicator of a future opt-out. |

## Entry / exit

- **Entry (segment):** user messageable on ≥ 1 consented channel, target channel closed, no opt-in ask for that channel in the last 60 days, and — where a contextual trigger is configured — the value moment just fired.
- **Exclude:** users who explicitly opted *out* of the target channel (a past unsubscribe is a decision, not a gap — re-permission belongs to winback's re-permission step, not here), detractors and anyone under negative-signal suppression, users in dunning.
- **Success exit:** `consent_updated` grant for the target channel · **Window:** 14 days · **Re-entry:** per target channel, once per 60–90 days, and stop permanently after 2–3 ignored or declined asks — the same restraint rule as [referral](referral.md): reachability is a favor the user grants, not a metric to be extracted.

## Push mechanics (platform constraint, not a style choice)

On iOS (and Android 13+), the OS permission dialog is a one-shot resource: once a user declines the native prompt, it cannot be programmatically re-triggered — the only remaining path is a Settings deep-link. So the pattern never spends the native prompt cold:

1. **Soft ask first** (in-app, skippable): state the concrete value, then ask "enable?" — a decline here costs nothing and preserves the native prompt for a later, better moment.
2. **Native prompt only on soft-ask yes**, fired immediately while intent is hot.
3. **Already declined natively** (`push_permission_status` = denied): the message changes entirely — restate the value and deep-link to Settings; never pretend a re-prompt is possible.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (1) | DQS < 40 or no contextual events | One value-framed ask on the best open channel, timed to session activity. |
| Standard (2) | DQS 40–69 | Soft-ask → native-prompt sequencing for push; one follow-up on a second open channel if the first was seen but not actioned. |
| Branched (3) | DQS ≥ 70 + `push_permission_status` and contextual events | Moment-tied asks per target channel (wishlist→push, order→SMS), never-asked vs declined split, Settings-deep-link track for natively-declined push. |

Depth stays shallow at every tier by design: an opt-in ask is one question. Extra DQS buys better *moments* and honest *state-awareness*, never more asks.

## Step blueprint (standard, 2 steps)

| # | Wait | Channel | Intent | Branch |
|---|------|---------|--------|--------|
| 1 | at the value moment (or next session if none configured) | in-app (fallback: best open channel) | The value-first ask: one concrete benefit tied to what the user just did, then the opt-in action (soft ask for push) | — |
| 2 | +5d | email (if open) | One restatement of the same benefit with the opt-in link; nothing new, no pressure | if step 1 seen but not actioned |

Consent capture rule: the grant must be recorded the way the target channel's regime requires (İYS registration for TR SMS/email, prior express written consent for US SMS, explicit opt-in for GDPR) — a tapped button that isn't evidenced in the consent system is a journey "success" that a regulator reads as unconsented sending. Never pre-check boxes, never bundle channels into one yes.

The payoff is downstream: every grant unlocks blocked journeys and depth upgrades in the tracking plan (push unlocks [back-in-stock](back-in-stock.md)'s speed, SMS unlocks [payment-failure](payment-failure.md)'s urgency tier). The portfolio should name what each opt-in unlocks — that's also the honest way to prioritize which channel to ask for first.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Opt-in rate per target channel | primary | grants within window / asks delivered, split never-asked vs declined |
| Native-prompt acceptance rate (push) | secondary | accepts / native prompts fired — measures soft-ask gating quality; a low rate means the soft ask is qualifying badly |
| Ask dismiss/ignore rate + asking-channel opt-out | guardrail | rising dismissals mean the moment or the value framing is wrong; an unsubscribe from the *asking* channel is the worst outcome this pattern can produce |

## Common mistakes

- Firing the native push prompt cold at first open — the single most common way apps permanently lose their highest-reach channel; always soft-ask first.
- A bare "turn on notifications" with no concrete value — the user is being asked to pay attention forward; the ask must say what they get.
- Asking for every closed channel at once — one target channel per journey instance; a consent wall reads as a shakedown.
- Re-asking on a timer regardless of declines — 2–3 ignored asks is the permanent stop; a declined ask is data, not a retry queue.
- Treating an old unsubscribe as an opt-in gap — re-permissioning a past opt-out has its own rules (see the consent-age rule in [consent-and-quiet-hours.md](../compliance/consent-and-quiet-hours.md)) and never enters this journey.
- Promising one kind of content to win the grant and sending another — the fastest route from opt-in to spam complaint.

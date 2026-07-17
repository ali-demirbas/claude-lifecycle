---
name: in-app
consent_required: none — rendered inside the product to a live session; the only zero-consent-risk channel
frequency_cap: 1 marketing in-app message / user / session (default; user-adjustable)
quiet_hours: not applicable — the message only appears when the user is already present
limits:
  title: {max: 60, unit: chars}
  body_modal: {max: 140, unit: chars}
  body_banner: {max: 90, unit: chars}
  cta: {max: 20, unit: chars}
  ctas: {max: 2, note: "one primary action + one dismiss; never two competing primaries"}
---

# In-App — Channel Rules

Shown only to users who are actively inside the product, which makes it the zero-consent-risk channel: no İYS, no TCPA, no OS permission to lose. The cost is paid in attention instead — a badly timed modal interrupts the very session you were trying to deepen. In-app excels at feature adoption, plan upsell, and contextual nudges; it is **structurally useless for winback**, because the user must already be present to see it — a churned user never will. Never plan an in-app step in a winback or reactivation journey.

## Hard rules (copy fails review if violated)

1. Title ≤ 60 chars; body ≤ 140 chars (modal) or ≤ 90 chars (banner) — counted per format.
2. Max **2 CTAs**, each ≤ 20 chars: one primary action + one dismiss ("Daha sonra" / "Not now"). The dismiss must be honest — no "No thanks, I hate saving money" confirm-shaming.
3. **Never block a core task flow.** No modal during checkout, content playback, an active lesson, or any funnel step with revenue intent. Interrupting `begin_checkout` to upsell is copy *and* targeting failure.
4. Frequency: **1 marketing in-app message per session.** Transactional/system notices (errors, consent, service status) don't count against this.
5. Targeting must use **live session context** — current screen, feature just used, plan state, cart contents — not stale batch segments. An in-app message that ignores what the user is doing right now reads as an ad, not a nudge.
6. Dismissal is a signal: a dismissed message must not reappear in the same session, and repeated dismissals (2–3) should suppress that campaign for the user entirely.
7. Deeplink/CTA lands on the exact screen the message describes — one tap from message to value.

## Format selection

| Format | Use when | Body limit |
|---|---|---|
| Banner / tooltip | Low-stakes nudge, feature hint, non-blocking | 90 chars |
| Modal | Decision moment the user benefits from now (trial expiring, plan limit hit) | 140 chars |
| Full-screen | Onboarding and major announcements only — never routine marketing | 140 chars |

Default to the least intrusive format that carries the message. If it works as a banner, it is not a modal.

## Store review flows: platform quotas

If an in-app step routes to a native store rating flow, platform quotas apply and cannot be worked around:

- **iOS**: `SKStoreReviewController` allows at most **3 prompts per user per 365 days**; the OS decides whether the sheet actually appears, and requesting it does not guarantee display.
- **Android**: the In-App Review API enforces its own **platform-managed quota** (not publicly specified); over-calling it silently shows nothing.

Because the prompts are scarce, never spend one blind: run a **sentiment pre-check** first — a soft in-app question ("Enjoying the app?" / a thumbs or star quick-poll) — and route only positive responders to the store flow. Negative responders go to a feedback form instead, which both saves the quota and captures the complaint privately.

## When to prefer in-app over other channels

| Situation | Verdict |
|---|---|
| Feature adoption / plan upsell tied to what the user just did | ✅ in-app is the best channel that exists |
| User hit a plan limit or trial boundary mid-session | ✅ modal, right now, beats any email |
| No consent on any outbound channel | ✅ in-app is the only compliant option |
| Winback / reactivation / anything targeting absent users | ❌ structurally impossible — use email/SMS/WhatsApp |
| Time-critical info for users not currently in-app | ❌ push |


## Dwell-help mechanic (generalized from trial-conversion's hesitation pivot)

Long dwell on a **complex, consequential page** (policy detail, claim form, plan comparison) with no action is a readable confusion signal — the same signal trial-conversion reads at the paywall. A contextual, dismissible "need a hand?" offer (help article, human chat) at a tuned dwell threshold is support, not marketing: it carries no promotion, doesn't count against marketing frequency caps, and is never shown twice in one session after a dismiss. Threshold is tuned per page from real dwell distributions — a guessed "30 seconds" flags readers, not stuck users.

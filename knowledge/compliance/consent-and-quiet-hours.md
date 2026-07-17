---
name: consent-and-quiet-hours
purpose: Consent, frequency, and quiet-hour rules every journey must respect
disclaimer: Practical guidance for journey design, not legal advice. Confirm with counsel per market.
---

# Consent, Frequency & Quiet Hours

Journeys are generated **assuming consent is checked per channel per step** — a user in a journey may be reachable on email but not push. The journey engine must include the consent requirement in every journey's section 7.

## Consent baseline by regime

| Regime | Applies to | Email | SMS/WhatsApp | Push |
|---|---|---|---|---|
| KVKK + Turkish Commercial Electronic Message law (İYS) | Türkiye | Prior opt-in, İYS-registered | Prior opt-in, İYS-registered | OS opt-in |
| GDPR + ePrivacy | EU/EEA | Opt-in (soft opt-in for existing customers in some states) | Opt-in | OS opt-in |
| CAN-SPAM | US email | Opt-out model, but honor unsubscribes ≤ 10 days | — | — |
| TCPA | US SMS | — | Prior express written consent; calls/texts additionally restricted to 08:00–21:00 recipient local time ("quiet hours" — this repo's SMS/WhatsApp default below already sits inside that window) | — |
| CASL | Canada | Opt-in (express or implied) + sender identification info + working unsubscribe honored ≤ 10 business days | Same three requirements as Email | OS opt-in |

Design consequence: **never assume US-style opt-out for TR/EU/Canada audiences.** When market is unknown, default to the strictest (opt-in everywhere) and note it. This table is not exhaustive — UK (PECR/UK GDPR, materially similar to the EU row post-Brexit), Brazil (LGPD), Australia (Spam Act 2003) and others aren't separately listed. The opt-in-everywhere default covers the *consent* question for an unlisted market but not regime-specific *procedural* mandates (CASL's identification requirement, for example, isn't satisfied by consent alone) — treat any `markets:` value not in this table as a signal to flag "confirm with counsel," not as silently covered.

## Transactional vs marketing

Order confirmations, delivery updates, password resets and payment-failure notices are transactional: exempt from marketing consent but must contain **zero promotional content** to keep that status. The payment-failure journey pattern is transactional for its first notices and becomes marketing the moment it upsells.

## Default frequency caps (user-adjustable, engine defaults)

| Scope | Cap |
|---|---|
| Email marketing | 4 / user / week |
| Push marketing | 1 / user / day, 5 / week |
| SMS marketing | 2 / user / week |
| WhatsApp marketing | 2 / user / week |
| All channels combined | 8 marketing messages / user / week |

The portfolio's conflict review (portfolio template §4) must compute the worst case against these caps.

Refinements to how caps are applied:

- **Transactional messages are protected from caps** — order confirmations, delivery updates, dunning notices always get through; caps govern marketing sends only.
- **Cap by engagement segment:** a user showing declining engagement gets *fewer* messages under the cap, not more — piling volume onto someone already softening accelerates the drift.
- **Rising unsubscribes/opt-outs are read as a volume signal first**, a content signal second. Audit frequency before rewriting copy.

## Quiet hours

| Channel | Default quiet hours (user local) |
|---|---|
| Push | 22:00–09:00 (mandatory) |
| SMS / WhatsApp | 20:00–10:00 + no Sundays (TR İYS practice: avoid 24:00–08:00 at minimum; stricter default chosen deliberately) |
| Email | none, but avoid 00:00–06:00 sends for engagement reasons |

Quiet hours are evaluated in the **user's timezone when known**. Unknown user timezone → the market timezone from intake (`markets:`). Multiple markets with unknown user timezones → the strictest interpretation: a send must be inside allowed hours in **every** target market's local time, which narrows the window rather than widening it.

## Enforcement: what's code-checked vs. what isn't

`scripts/validate_output.py` enforces two of the rules above as hard failures before any deliverable reaches the user: **channel consent** (a step's channel must be in the journey's `constraints.allowed_channels`) and **frequency caps** (portfolio-wide weekly math, parsed live from the table above by `load_default_caps()` — never hand-copied, so the check can't silently drift from this file). Both are fully computable from journey/portfolio JSON alone.

**Quiet hours are not code-checked, and can't be from journey JSON alone.** A step's `wait` (`templates/journey.schema.json`) is a relative ISO 8601 duration from the previous step or trigger — the schema carries no absolute clock time or timezone, because the real trigger instant is only known once the journey is live in a CRM. Quiet-hours compliance today rests entirely on `journey-architect`'s design-time judgment (schedule around the window) and `copy-reviewer`'s content check (no "right now" timing promises) — there is no code backstop, and none is possible at this layer.

That makes quiet-hours enforcement an **export-time responsibility, not a journey-authoring-time one**: every CRM this repo maps to (`docs/crm-export-mapping.md`) has its own send-time-window feature operating on the real trigger timestamp (Braze Intelligent Timing, Klaviyo Smart Send Time, Iterable send-time optimization, Insider's send windows). `lifecycle-export` must wire each push/SMS/WhatsApp step to that feature — or, where the target platform lacks one, state the gap explicitly rather than let the journey ship silently unprotected. As of this review, `docs/crm-export-mapping.md` does not yet mention quiet hours, timezones, or consent at all; closing that is a `lifecycle-export`-scoped follow-up, not a change made here.

## Journey-level rules

1. Unsubscribe/opt-out from a channel exits the user from that channel's steps immediately, not from the whole journey (unless it was single-channel).
2. Winback journeys targeting long-dormant users must check consent age — İYS/GDPR consents don't expire automatically, but a > 2-year-silent list warrants a re-permission step instead of a promo blast.
3. Minors and sensitive categories (health, finance, gambling): the lexicon/industry file may add stricter rules; strictest wins.
4. **Negative-signal override (portfolio-wide):** an explicit complaint, a detractor NPS/CSAT response, or an escalated support ticket suppresses the user from **every** standard marketing journey — queued and future sends alike, not just the journey that triggered the signal — and routes them to a human/support resolution path. Suppression holds until the signal is resolved (ticket closed, sentiment recovered), not on a fixed timer. This is broader than any single journey's internal cooldown (e.g. feedback-nps's detractor branch); every pattern's audience Exclude line inherits it.
   - **When no signal source exists in the mapped events** (no `survey_response`, no complaint/ticket integration — the normal state of a stock GA4 setup), inheriting the rule on paper changes nothing in practice. The portfolio itself must then carry a **portfolio-level warning**: "no suppression signal source — every journey will run without this protection", and the missing signal goes into the tracking plan as a P0 item. Marking each journey "compliant" while the mechanism cannot fire is exactly the false comfort this rule exists to prevent.

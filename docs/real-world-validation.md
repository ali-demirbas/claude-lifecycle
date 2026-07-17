# Real-World Validation

Most of this repo's evidence comes from the eval suite (`evals/`, 40 scenario-based decision tests) and synthetic sample data in `examples/`. Those prove the engine's *decision logic* is consistent. This page tracks the separate, rarer kind of evidence: what happened when someone actually ran it against a real product.

## Run 1: an iOS freemium subscription app (AI photo/video editing)

An early user connected the engine to a real GA4 property for a consumer iOS app — a freemium AI photo-editing tool (enhance, colorize, object removal, background removal, short AI video) with a daily free-usage cap and a paid subscription tier. GA4 was live-connected (T1). The engine produced a 7-journey portfolio: payment-failure, trial-conversion, welcome-onboarding, a late-activation follow-up, churn-prevention, reactivation, and feature-adoption.

No company name, product name, or account-specific numbers are reproduced here — only what the run demonstrated about the engine's own behavior.

### What it confirmed

- **Reactivation and winback stayed correctly separated.** The generated reactivation journey gated entry on "never paid before" versus "paid before" exactly as `knowledge/journey-patterns/reactivation.md` specifies — past payers were correctly excluded and left for churn-prevention/winback instead of being pulled into a reactivation flow designed for a different audience.
- **Discount-last discipline held.** Every discount offer across the portfolio (trial-conversion, churn-prevention) appeared only as the final, optional step of its sequence — never as an opening move.
- **Journey hand-off logic worked.** Welcome-onboarding explicitly deferred to a late-activation journey once a user passed the activation window, with messaging stopping on one side when the other took over — no double-messaging.
- **Caveats stayed embedded, not bolted on.** Data-tier notes and targeting-confidence caveats appeared inline on the relevant node, not as a separate summary section — consistent with this repo's own output-authoring rule.
- **Copy traceability held.** Every message step referenced its exact copy-doc anchor (file + step id), matching the journey-doc template's requirement.

### What it surfaced (since folded back into the engine)

Real usage found gaps this repo's own synthetic eval data hadn't exercised:

- `quota_limit_reached` added to `trial-conversion` as an alternate, softer entry trigger for freemium apps with a hard daily usage cap — hitting the cap is a natural trial-invitation moment distinct from an unprompted `trial_start`.
- A new "Mobile subscription platforms" reference in `knowledge/event-taxonomy/ga4-recommended-events.md` — RevenueCat and App Store Server Notification event names rarely match GA4-recommended-event conventions natively, and this repo had no mapping for that before.
- A labeling fix in `CLAUDE.md`'s conventions: don't reuse one field label ("Kontrol" in Turkish output) for two different concepts — a statistical control/holdout group and an operational guardrail are not the same thing, even when a shorter shared word would fit both.

### Status and limits

This is one external data point, not a validated sample. It doesn't cover: a live plugin install through Claude Code's actual `/lifecycle` commands (still open, see below), other verticals (ecommerce, B2B SaaS, fintech), or T2/T3 tiers. Treat it as directional evidence the engine holds up outside synthetic test data, not proof it's fully battle-tested.

**Still unverified:** an end-to-end run through the actual installed plugin (`/plugin install` → `/lifecycle connect` in a live Claude Code session) has not happened yet — every eval case and this run were exercised by an agent reading the skill files directly, not through the packaged plugin mechanism itself.

If you've run this engine against your own product, a report here (anonymized, no fabricated numbers, same format as above) is a genuinely useful contribution — see [CONTRIBUTING.md](../CONTRIBUTING.md).

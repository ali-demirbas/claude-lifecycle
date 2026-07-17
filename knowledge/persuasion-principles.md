# Persuasion Principles for Lifecycle Copy

Cognitive levers `copy-writer` draws on when picking a variant's persuasion angle (`agents/copy-writer.md` step 2). These are levers, not licenses: every principle below sits under the same rule as urgency (CLAUDE.md rule 3, copy-writer's Rules section) — never fabricated, only used when a real data variable or a true, statable fact backs it.

Source: Robert Cialdini's principles of influence (*Influence*, 1984) and Kahneman & Tversky's behavioral-economics research on loss aversion and framing (prospect theory, 1979). Established, decades-old, publicly documented psychology, not house theory, so it's fine to name it as such in annotations rather than pass it off as a proprietary insight.

## Reciprocity

People feel obliged to return value they've received. Lead with something genuinely useful (a tip, a resource, early access) before the ask.

- **Applies to:** welcome-onboarding, feedback-nps ("here's what changed from your last review, and one more thing").
- **Guardrail:** the value given must be real and delivered in the same message, not promised for later.

## Social proof

People infer correctness from what others similar to them do. This deepens the existing **Social-proof-led** angle in `copy-writer.md`.

- **Applies to:** trial-conversion, upsell-cross-sell.
- **Guardrail:** already enforced by copy-writer's data-variable rule. Similarity beats volume when both are available: "people in your industry" outperforms a bigger but generic headline number (the social-identity mechanism — Tajfel & Turner's work on in-group influence).

## Anchoring

The first number shown shapes how every later number is judged.

- **Applies to:** any incentive-bearing step (payment-failure recovery offer, winback discount, upsell pricing). Show the real original price or value before the discounted one.
- **Guardrail:** the anchor must be the actual original price, never a reference number inflated for contrast.

## Loss aversion / framing

Losing something already held feels roughly twice as painful as an equivalent gain feels good. For churn-adjacent journeys, "keep what you have" tends to outperform "get something new."

- **Applies to:** churn-prevention, cart-recovery, winback, payment-failure — frame around the account, progress, or cart already invested in, not a generic comeback pitch.
- **Guardrail:** the thing framed as at risk must actually be at risk (real expiry date, real cart contents). Same honesty bar as urgency, applied to loss framing instead of deadlines.

## Mental accounting (pricing frame)

The same price feels different depending on how it's divided. "$1/day" reads cheaper than "$30/month" even though it's identical.

- **Applies to:** subscription upsell, trial-conversion pricing steps.
- **Guardrail:** the per-unit math must be exact, never rounded in the favorable direction.

## Pricing & incentive wording

How an already-approved incentive is *phrased*. The incentive's existence, value, and eligibility are set by `knowledge/brands/<brand>.md`'s incentive policy and the compliance layer — this section is wording only, never a source of what discount to offer.

- **Rule of 100** — below roughly 100 units of the local currency, a percentage reads larger ("20% off"); above it, an absolute amount reads larger ("$50 off" / "500 TL indirim"). Pick whichever framing of the *same, real* discount reads larger.
- **Charm pricing** — a price just under a round number reads cheaper than the round number. Irrelevant if the brand's actual price list uses round numbers; don't introduce a charm ending the product doesn't have.

## Effort justification (the IKEA effect)

People value what they helped build (Norton, Mochon & Ariely's 2012 experiments named it the IKEA effect). A small, real choice made during setup — "which matters more to you: roadside assistance or a replacement vehicle?" — increases attachment to the resulting configuration, and doubles as progressive-profiling data.

- **Applies to:** onboarding micro-choices, progressive-profiling question design (the question itself creates investment, not just data).
- **Guardrail:** the friction must be a REAL choice the product honors. Manufactured busywork dressed as choice ("pick your favorite color" that changes nothing) is the dishonest twin and burns trust when discovered.

## Lower priority for single-message copy

**Commitment & consistency** and foot-in-the-door sequencing (small ask, then a bigger one) shape journey *structure* — which step asks what, in what order — more than any single message's wording. Relevant to journey design (`skills/lifecycle-journeys/`), not to a single copy-writer pass.

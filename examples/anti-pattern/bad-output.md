# Anti-Example — What a Bad Output Looks Like

> **This file is wrong on purpose.** "BrewTrack" is a fictional coffee-subscription app invented only for this page; every number below is made up to demonstrate eight real failure modes. Each excerpt reads like a normal engine output — right headers, plausible numbers, nothing that jumps out on a skim — which is exactly why each one is annotated. Do not copy any format from this file; see the [other three examples](../) for what a real output looks like.

## Excerpt 1 — Data Assessment (fragment)

> **Source & tier:** T1, GA4 property, 90-day pull.
>
> **DQS: 61/100** ❌¹
>
> | Component | Score |
> |---|---|
> | Event diversity | 22/25 |
> | Conversion events | 18/25 |
> | Funnel completeness | 14/20 |
> | User attributes | 5/15 |
> | Volume sufficiency | 2/15 |
>
> Event diversity counted 22 distinct events tracked across the funnel: `subscription_start`, `page_view`, `scroll_50`, `scroll_90`, `session_start`, `screen_view`, `add_to_cart`, `first_visit`... ❌²

## Excerpt 2 — Portfolio (fragment)

> | # | Journey | Stage | Depth | Status |
> |---|---|---|---|---|
> | 1 | Abandoned Cart | Revenue | 6 steps, standard | ✅ |
> | 2 | Browse Abandonment | Revenue | 6 steps, standard | ✅ |
> | 3 | Winback | Retention | 6 steps, standard | ✅ |
> | 4 | Churn Prevention | Retention | 6 steps, standard | ✅ |
>
> ❌³ ❌⁴
>
> **Conflict review:** sends are staggered across the four journeys and stay well within frequency limits. ❌⁵
>
> Based on industry benchmarks for subscription coffee brands, this portfolio is expected to lift 90-day retention by approximately 23%. ❌⁶

## Excerpt 3 — Copy Sample, Abandoned Cart step 1 (fragment)

> **Variant A:** "Sepetin seni bekliyor! Kaldığın yerden devam et."
> **Variant B:** "Sepetindeki ürünler hâlâ orada! Kaldığın yerden devam et." ❌⁷
>
> **CTA (both variants):** "Kaçırma, hemen tamamla!" ❌⁸

## Why each one fails

| # | What's wrong | Breaks | Corrected version |
|---|---|---|---|
| 1 | DQS given as a bare number, no gate flags | [lifecycle-connect pitfall 1](../../skills/lifecycle-connect/SKILL.md#common-pitfalls); DQS hard rule 3 | With volume sufficiency at 2/15 this is almost certainly an activation- or volume-limited portfolio — the score line must carry whichever tag actually triggers, e.g. `DQS 61/100 · activation: blocked (no per-user identity)` |
| 2 | `page_view`, `scroll_*`, `session_start`, `screen_view`, `first_visit` counted as "diversity" | [lifecycle-connect pitfall 2](../../skills/lifecycle-connect/SKILL.md#common-pitfalls) | Filter to behaviorally meaningful events per the industry playbook before counting — this inventory likely scores closer to 8-10/25 once page-mechanics events are dropped |
| 3 | Every journey is a recovery pattern — nothing grows an already-healthy stage | [lifecycle-journeys pitfall 2](../../skills/lifecycle-journeys/SKILL.md#common-pitfalls); CLAUDE.md rule 2 | Pair recovery (abandoned-cart, winback) with growth (post-purchase, loyalty, replenishment for a subscription product) — check the stage-coverage table before finalizing |
| 4 | Every journey is "6 steps, standard" regardless of pattern or DQS | [lifecycle-journeys pitfall 1](../../skills/lifecycle-journeys/SKILL.md#common-pitfalls) | Recompute depth per journey — DQS 61 with volume sufficiency at 2/15 should cap most of these at **standard at best**, and the informational ones shorter still, not a uniform 6 |
| 5 | "well within frequency limits" with no number | [lifecycle-journeys pitfall 3](../../skills/lifecycle-journeys/SKILL.md#common-pitfalls) | State the actual worst case per audience group and overlap combo against the caps, e.g. `5/8 combined vs cap` — a sentence with no number attached is a missing step, not a finished one |
| 6 | "~23% lift" sourced to "industry benchmarks" | CLAUDE.md rule 3 | `baseline after 4 weeks` — no invented percentage, cited source or not; ranges from `knowledge/` files may be cited as ranges, a specific lift number may never be fabricated |
| 7 | Variant B is Variant A with synonyms swapped ("ürünler" for nothing, same structure, same lever) | [lifecycle-copy pitfall 1](../../skills/lifecycle-copy/SKILL.md#common-pitfalls) | Give B a genuinely different lever — e.g. social proof: *"Bu hafta 1.200 kişi bu karışımı seçti — sepetin hâlâ hazır"* |
| 8 | "Kaçırma, hemen tamamla" implies urgency with no variable behind it | [lifecycle-copy pitfall 2](../../skills/lifecycle-copy/SKILL.md#common-pitfalls); word choice discipline rule | Either attach a real variable (`{{cart_reserved_until}}`) or drop the pressure framing entirely — "Sepetini tamamla" states the action without inventing a deadline |

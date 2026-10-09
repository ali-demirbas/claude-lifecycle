---
name: measurement
purpose: Incrementality doctrine every journey's KPI section and the audit skill apply
---

# Measurement — Incrementality Doctrine

Attribution and incrementality are different things: a winback email to a user who was going to return anyway still shows an attributed conversion. For marketing journeys measured with a holdout, the **primary KPI is incremental lift against that holdout**; attributed numbers are diagnostics. Not every journey is measured that way: the journey's `measurement.design` (holdout, none_service, pre_post, none_low_volume, other) decides how it is read — see "Evaluate by measurement design" below.

## Holdout mechanics

- Random assignment **before** launch — never engaged-vs-not-engaged comparison groups.
- **The holdout is a measurement design, not a fixed number.** 10% is a common starting point, not a rule every journey gets. The share follows the volume (a smaller share needs more volume to detect the same lift) and the cost of withholding the message. Each journey's `measurement` block in the JSON names the design, the primary outcome and its window, and for a holdout: the assignment unit, that assignment is consistent (the same user always lands in the same group, e.g. a hash of the user id), and which new communications the control does not receive.
- **Routine communications** that already exist (an existing welcome email, order and account mails) are stated per group. Usually both groups keep receiving them; if the control is also cut off from a routine mail, the measured lift includes that mail's effect too.
- **Low volume:** when the expected volume can't support a holdout in a reasonable window, use design `none_low_volume`, say why, and name the alternative (a pre/post comparison read as directional, a longer pooled window, a program-level control group). Never call a result statistically reliable just because a holdout exists; the volume note says what the numbers can and cannot show.
- **Service and transactional journeys** (payment failure, a contractual renewal notice, a cancellation confirmation) are not held out like marketing. Withholding them can harm the user or break an obligation; measure them with operational outcomes instead (recovery rate, time to resolution, complaints).
- Holdout users are strictly suppressed from the journey for the full measurement window. Contamination compresses measured lift toward zero.
- **The holdout is journey-level and spans every channel the journey uses.** A user held out of the email steps but reached by the same journey's push steps is contaminated — suppression means the whole journey, not one channel of it.
- **Universal Control Group (optional, program-level):** a small slice (3–5%) suppressed from ALL marketing journeys for a quarter measures what the entire program adds — the only honest answer to "is all this messaging worth anything." Per-journey holdouts can't answer that; they each measure one journey against a world where the others still run.

## Lift and the go/no-go number

```
p_T, p_C                 = conversion rate in treatment and in control (same outcome, same window)
absolute lift            = p_T − p_C
relative lift %          = (p_T − p_C) ÷ p_C × 100        (undefined when p_C = 0; never "infinite")
incremental_conversions  = N_treatment × (p_T − p_C)
incremental_contribution = incremental_conversions × contribution_per_conversion
iROI                     = (incremental_contribution − incremental_cost) ÷ incremental_cost
```

- `contribution_per_conversion` is **contribution margin**, not revenue or revenue LTV, over the **same time horizon** as the outcome window (or a stated longer horizon applied consistently), and net of the incentive, channel and operational costs a conversion carries.
- `incremental_cost` is what the journey added (sends, incentives redeemed, ops time); when it is 0, iROI is **undefined** — report incremental contribution instead.
- Worked check: N_treatment = 10,000, p_T − p_C = 0.01, contribution 500 per conversion, incremental cost 10,000 → 100 incremental conversions, 50,000 incremental contribution, iROI = (50,000 − 10,000) ÷ 10,000 = 4.
- A rollout estimate ("if we send to everyone") uses its own N (the population it would reach) and is labelled a **projection**, never reported as the measured result.

Report both relative and absolute lift; **decide on absolute** (a huge relative lift on a tiny base can still be worthless). For a holdout-measured marketing journey, iROI is the go/no-go number.

## Sample-size honesty

There is no universal conversion count that makes a lift "significant". Power and the minimum detectable effect (MDE) depend on the baseline rate, the expected effect, the sample size of **both** arms, the allocation between them, and the analysis method. Compute it before launch (or use the experiment platform's calculation) and record what the planned volume can detect in the journey's `volume_note`. When it can't be computed, report the uncertainty (a confidence interval or the plain statement that the difference is within noise) instead of a verdict.

- Report **participants and conversions separately** for each arm; a rate without its denominator can't be judged.
- **Low volume remedies:** a longer window, pooling comparable cohorts or periods, a more balanced allocation, or a different design (pre/post read as directional, a program-level control). Shrinking the control arm is **not** a power fix — it raises the uncertainty on the control side. A business may still choose a small holdout to limit the cost of withholding the message; that is a cost decision, and the volume note must say what it can no longer detect.
- An underpowered result is "unmeasured", **not** "doesn't work". Say which one applies.

Low power produces false negatives (Type II error): reading "no lift" as proof a journey doesn't work, when the test simply lacked power to detect a real but smaller effect. A borderline "no difference" on a small sample is closer to *inconclusive* than *kill* (see lifecycle-results Step 3).

## Evaluate by measurement design

Pick the evaluator from the journey's `measurement.design`, never one rule for all:

| Design | How it is read |
|---|---|
| `holdout` | **Intent-to-treat** on the randomized eligible population: everyone assigned to treatment counts in treatment, including people the message never reached (no consent, bounced, capped). Dropping undelivered people from treatment but not from control biases the lift. |
| `none_service` (service / transactional) | Operational outcomes and SLA (recovery rate, time to resolution, completion) plus harm guardrails (complaints, opt-outs, errors). "No holdout" is the design, not a failure. |
| `pre_post` | Directional only; name the confounders (season, price, product or traffic changes) that the comparison can't separate from the journey. |
| `none_low_volume` / `other` | The stated alternative in the journey's `alternative` field, read with its own limits. |

Across all designs: read an outcome only after its window has matured for the whole cohort; zero control conversions make relative lift undefined (report the absolute difference and counts); segment-level reads are exploratory leads for a future test, never declared winners.

## Why you don't stop early

Calling a test the moment it crosses a significance threshold inflates false positives — a well-known effect in A/B testing literature (repeated significance testing / "peeking"): in A/A tests (two identical variants, no real difference between them), a large share of runs cross a nominal significance threshold at some point purely from noise, and the share climbs the more often you peek. Treat any specific percentage here as an estimate, not a documented constant — the exact rate depends on the peeking cadence and the test's own parameters. Checking a holdout comparison daily and stopping on the first good-looking day is the same mistake.

Early results also regress to the mean and are prone to the novelty effect (a change gets more attention just for being new; the lift fades as it stops being new). Don't read or verdict a window before it closes (lifecycle-results Step 2, gate rule 2), even if the interim numbers look decisive either way.

## Measurement window by trigger latency

| Journey family | Window |
|---|---|
| Cart / browse recovery | 1–7 days |
| Activation / engagement | 7–14 days |
| Winback, renewal, considered purchase | 30–90 days, matched to the product's cycle |

Round up to whole weeks, not just the trigger-latency minimum above — day-of-week traffic and behavior patterns vary enough that a 5-day window and a 7-day window of the same journey can read differently for reasons that have nothing to do with the journey.

## Two-tier metrics (enforced in journey-doc §6)

- **Per-step diagnostics** — opens, clicks, step conversion: attributed, cheap, good for fixing individual messages.
- **Per-journey primary** — the outcome its measurement design names: incremental lift vs holdout for a held-out marketing journey, operational outcomes for a service journey, the stated alternative otherwise.

A high open rate on a message that would have converted the same users anyway is a well-performing message inside a worthless journey. Never promote a diagnostic to primary.

## Test discipline

- **One variable per test.** A winning variant that differed in angle AND timing AND channel proves nothing attributable — the copy metadata's `strategy` field IS the variable; everything else stays constant. Timing tests and copy tests are separate experiments.
- **Prioritize the queue, don't run the brainstorm.** When multiple test candidates exist, rank by expected business impact × ease of implementation × confidence, and run from the top — test ideas that don't make the cut go to a backlog, not to production.
- **Concurrency is bounded by audience power.** Every simultaneous test splits the same users; more concurrent tests than the volume supports means every one of them finishes underpowered (see sample-size honesty). Fewer, conclusive tests beat many inconclusive ones.
- **Launch variants simultaneously, into stable windows.** Arms starting on different days measure different weeks, not different variants; and a test straddling a declared campaign window or seasonal peak inherits the seasonality caution at design time — delay it or extend it past the window, don't launch into it.
- **Assignment is sticky.** A user stays in the arm they were randomized into for the whole test — someone who switches arms mid-test contaminates both measurements.
- **Power the test properly.** The working convention is ~80% statistical power (an 80% chance of detecting a real effect of the planned size), computed from the inputs in the sample-size section; below that, "no difference" results are mostly noise. Variance-reduction techniques that use pre-period behavior exist and can reach significance with smaller samples — they are a capability to ask your experimentation platform about, never something to hand-roll.

## Waits are test subjects too

A/B testing defaults to copy variants, but a step's WAIT is often the higher-leverage variable — the same message at +1h vs +24h after the trigger can differ more than any two subject lines. Timing cohorts follow every rule in this file (holdout, power, full windows); the copy output's variant metadata convention applies the same way: a timing test carries its own falsifiable hypothesis.

## Seasonality caution

Seasonal windows inflate attributed numbers because the baseline itself is elevated — holdouts matter more during peaks than at any other time. Separate "the season did this anyway" from "the journey did this" before crediting the journey. (Sector-specific seasonal windows live in each industry playbook's Seasonality section.)

## Common mistakes

- Underpowered test read as a real result (see sample-size honesty).
- Treatment counted per-delivered while control is counted per-assigned (breaks intent-to-treat).
- Contaminated control (holdout users reached via another journey sharing the audience — the portfolio conflict review must check this).
- Mismatched cohorts (holdout drawn from a different segment than exposed).
- Stopping early on a good week; external factors (price change, PR spike) credited to the journey.

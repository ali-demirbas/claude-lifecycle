---
name: measurement
purpose: Incrementality doctrine every journey's KPI section and the audit skill apply
---

# Measurement — Incrementality Doctrine

Attribution and incrementality are different things: a winback email to a user who was going to return anyway still shows an attributed conversion. Every journey's **primary KPI is incremental lift against a holdout**; attributed numbers are diagnostics.

## Holdout mechanics

- Random assignment **before** launch — never engaged-vs-not-engaged comparison groups.
- 10% holdout is the default starting split (journey-doc §6 requires it for T1/T2).
- Holdout users are strictly suppressed from the journey for the full measurement window. Contamination compresses measured lift toward zero.
- **The holdout is journey-level and spans every channel the journey uses.** A user held out of the email steps but reached by the same journey's push steps is contaminated — suppression means the whole journey, not one channel of it.
- **Universal Control Group (optional, program-level):** a small slice (3–5%) suppressed from ALL marketing journeys for a quarter measures what the entire program adds — the only honest answer to "is all this messaging worth anything." Per-journey holdouts can't answer that; they each measure one journey against a world where the others still run.

## Lift and the go/no-go number

```
Lift % = ((exposed conversion − control conversion) ÷ control conversion) × 100
iROI   = (absolute lift × LTV − journey cost) ÷ journey cost
```

Report both relative and absolute lift; **decide on absolute** (a huge relative lift on a tiny base can still be worthless). iROI is the only go/no-go number.

## Sample-size honesty

Rule of thumb: aim for **at least ~200 conversions in the control group** before trusting a lift number (roughly the p < 0.05 territory for typical effect sizes). Below that: extend the window, reduce the holdout %, or accept the journey can't be measured precisely yet — which means "unmeasured", **not** "doesn't work". Say which one applies.

The ~200-conversion rule guards against false positives (Type I error). It doesn't guard against false negatives (Type II error): reading "no lift" as proof a journey doesn't work, when the test simply lacked power to detect a real but smaller effect. A borderline "no difference" on a small control group is closer to *inconclusive* than *kill* (see lifecycle-results Step 3).

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
- **Per-journey primary** — incremental lift vs holdout: the only tier that justifies the journey's existence.

A high open rate on a message that would have converted the same users anyway is a well-performing message inside a worthless journey. Never promote a diagnostic to primary.

## Test discipline

- **One variable per test.** A winning variant that differed in angle AND timing AND channel proves nothing attributable — the copy metadata's `strategy` field IS the variable; everything else stays constant. Timing tests and copy tests are separate experiments.
- **Prioritize the queue, don't run the brainstorm.** When multiple test candidates exist, rank by expected business impact × ease of implementation × confidence, and run from the top — test ideas that don't make the cut go to a backlog, not to production.
- **Concurrency is bounded by audience power.** Every simultaneous test splits the same users; more concurrent tests than the volume supports means every one of them finishes underpowered (see the sample-size rule). Fewer, conclusive tests beat many inconclusive ones.
- **Launch variants simultaneously, into stable windows.** Arms starting on different days measure different weeks, not different variants; and a test straddling a declared campaign window or seasonal peak inherits the seasonality caution at design time — delay it or extend it past the window, don't launch into it.
- **Assignment is sticky.** A user stays in the arm they were randomized into for the whole test — someone who switches arms mid-test contaminates both measurements.
- **Power the test properly.** The working convention is ~80% statistical power (an 80% chance of detecting a real effect of the planned size); below that, "no difference" results are mostly noise. Variance-reduction techniques that use pre-period behavior exist and can reach significance with smaller samples — they are a capability to ask your experimentation platform about, never something to hand-roll.

## Waits are test subjects too

A/B testing defaults to copy variants, but a step's WAIT is often the higher-leverage variable — the same message at +1h vs +24h after the trigger can differ more than any two subject lines. Timing cohorts follow every rule in this file (holdout, power, full windows); the copy output's variant metadata convention applies the same way: a timing test carries its own falsifiable hypothesis.

## Seasonality caution

Seasonal windows inflate attributed numbers because the baseline itself is elevated — holdouts matter more during peaks than at any other time. Separate "the season did this anyway" from "the journey did this" before crediting the journey. (Sector-specific seasonal windows live in each industry playbook's Seasonality section.)

## Common mistakes

- Underpowered test read as a real result (see sample-size rule).
- Contaminated control (holdout users reached via another journey sharing the audience — the portfolio conflict review must check this).
- Mismatched cohorts (holdout drawn from a different segment than exposed).
- Stopping early on a good week; external factors (price change, PR spike) credited to the journey.

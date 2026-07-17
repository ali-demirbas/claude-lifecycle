# Example — Fintech with no data (Tier 3, industry-only)

What the engine produces when **nothing is connected**: playbook-driven simple journeys, an intake round to replace the missing data, and a tracking plan that shows exactly what instrumentation would buy.

> All data in this example is **synthetic**. "Parapuan" is a fictional app; every figure below is a user-declared estimate, never a measurement.

## Scenario

**Parapuan** — a fictional Turkish savings app (automatic round-up savings + recurring deposits, e-money licensed).

| Fact | Value |
|---|---|
| Sector | Fintech (savings / e-money app) |
| Data source | **none** — user explicitly chose Tier 3 (industry-only) |
| Industry playbook | [fintech](../../knowledge/industries/fintech.md) |
| DQS | 0/100 — all components score on connected data, and none exists |
| Copy language | Turkish |

## Commands run

```
/lifecycle connect            → user declares "no data yet, industry: fintech" → Tier 3 recorded
/lifecycle intake             → Q&A below (sector questions from the fintech playbook)
/lifecycle journeys           → 01-portfolio.md  (4 simple journeys + blocked list)
                              → 02-tracking-plan.md (what to instrument, in what order, and why)
```

## The intake Q&A that replaced the data

`lifecycle-intake` asked one round (grouped, defaults offered). Answers used by the portfolio:

**Standard intake**

| # | Question (default) | Answer |
|---|---|---|
| 1 | Primary goal? *(default: retention-first)* | **activation-first** — get signups through KYC to a first deposit |
| 2 | Channel inventory + rough sizes? | email ≈ 8k, push ≈ 5k, SMS ≈ 3k (İYS-registered) — *user estimates* |
| 3 | Existing automations? | none — only transactional OTP/security messages via the provider |
| 4 | Brand tone + formality? | calm, trust-building, plain; **sen**-form (young-saver audience) |
| 5 | Incentive policy? | **no financial incentives** — deposit bonuses not yet cleared by compliance |
| 6 | Copy language(s)? | Turkish |
| 7 | Legal market(s)? | Türkiye (KVKK + İYS) |

**Fintech sector questions** (from the [playbook's intake section](../../knowledge/industries/fintech.md)):

| # | Question | Answer |
|---|---|---|
| 1 | Which regulator(s)/marketing rules apply; does compliance review copy? | BDDK/TCMB e-money regime; **compliance reviews every lifecycle message before send** |
| 2 | Where do users stall in KYC; per-step events? | No per-step events yet. Support tickets point to document upload and selfie match, plus manual-review waits |
| 3 | What is the core "first transaction"; instrumented with value? | `first_deposit` (bank transfer or card top-up) — **not instrumented yet** |
| 4 | Are financial incentives permitted? | Not until legal sign-off — journeys carry none |
| 5 | Which message categories are transactional-only? | OTP, security alerts, transaction confirmations, statements, regulatory notices — journeys never touch or imitate them |

## Files in this example

| File | What it shows |
|---|---|
| [01-portfolio.md](01-portfolio.md) | 4 simple journeys (3–5 steps, time-based waits) with full journey docs, honest limitations |
| [02-tracking-plan.md](02-tracking-plan.md) | The instrumentation plan: which events unlock which journeys/depths, projected DQS |

## What Tier 3 means in practice

DQS 0 puts everything in the **simple** class (< 40, see [data-quality-score.md](../../docs/data-quality-score.md)): 3–5 steps, time-based waits, single channel plus one support channel, playbook defaults for all timing. No journey may claim a revenue KPI until a true revenue event (`first_deposit`) is instrumented as its success exit. Volumes and baselines are all "estimate after launch". The value of running the engine anyway: the portfolio launches something defensible now, and the tracking plan converts every limitation into a ranked instrumentation task.

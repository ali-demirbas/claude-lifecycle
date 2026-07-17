# Example — SaaS with CSV export only (Tier 2)

What the engine produces from a **static export** instead of a live analytics connection: enough for a standard-depth portfolio, honest about what the CSV cannot support.

> All data in this example is **synthetic**. "Kanbanly" is a fictional product; the event counts are invented for demonstration and internally consistent across files.

## Scenario

**Kanbanly** — a fictional B2B SaaS project-management tool with a 14-day opt-in free trial.

| Fact | Value |
|---|---|
| Sector | SaaS (B2B, self-serve) |
| Data source | CSV export from Mixpanel: 7 events with monthly counts, Jan–Jun 2026 |
| What the CSV lacks | funnel percentages, event parameters, user attributes (only `user_id` + email columns) |
| Trial model | 14-day opt-in trial, no credit card required |
| Channels (consented) | email 11k · in-app (all logged-in users) · push 2.1k (desktop/mobile app) |
| Goal (from intake) | revenue-first (trial conversion) |
| "Aha" action (from intake) | first `project_created` — accepted as the core activation event |

## Commands run

```
/lifecycle connect kanbanly-mixpanel-export.csv  → 01-data-assessment.md  (DQS 52 → standard class)
/lifecycle map                                   → project_created aliased to feature_used (user-confirmed)
/lifecycle journeys                              → 02-portfolio.md (6 generated, 2 blocked, tracking summary)
```

The CSV itself is **not** in the repo — user analytics exports never get committed (CLAUDE.md rule 4); it lived in the local gitignored `output/` directory during the run.

## Files in this example

| File | What it shows |
|---|---|
| [01-data-assessment.md](01-data-assessment.md) | T2 assessment: what a bare CSV earns on the DQS rubric and why |
| [02-portfolio.md](02-portfolio.md) | 6 standard-depth journeys, 2 blocked, coverage, conflict math, roadmap, tracking summary |

Individual journey docs and copy are not included here — see [ecommerce-full-ga4](../ecommerce-full-ga4/README.md) for those artifact types.

## What Tier 2 means in practice

DQS 52 lands in the **standard** class (40–69, see [data-quality-score.md](../../docs/data-quality-score.md)): journeys get 4–7 steps, at most one open/click branch, two channels. No value gates, no behavioral multi-branching — the CSV has no parameters to branch on. The [tracking summary](02-portfolio.md#6-tracking-plan-summary) shows exactly which instrumentation buys the branched class.

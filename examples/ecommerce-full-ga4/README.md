# Example — E-commerce with full GA4 (Tier 1)

The flagship end-to-end example: what the engine produces when a **real analytics source is connected** and the data is good enough for branched journeys.

> All data in this example is **synthetic**. "Moda Nova" is a fictional store; the event counts are plausible, internally consistent, and invented for demonstration.

## Scenario

**Moda Nova** — a fictional Turkish D2C fashion store.

| Fact | Value |
|---|---|
| Sector | E-commerce (fashion; mostly durable, small replenishable "basics" line) |
| Traffic | ~40k monthly active users (~118k users / 90 days) |
| Data source | GA4 property via MCP (`ga4` tools), 90-day window |
| Meaningful events | 11 (full ecommerce funnel + wishlist, refund, sign_up) |
| Channels (consented) | email 28k · push 9k · SMS none · WhatsApp none |
| Cart behavior | guest carts persist 7 days, then purge (real expiry — usable in copy) |
| Incentive policy | max 10% discount, last-step only, requires human approval |
| Goal (from intake) | revenue-first |
| Copy language | Turkish (sen-form per [ecommerce lexicon](../../knowledge/lexicons/ecommerce.md)) |

## Commands run

```
/lifecycle connect        → 01-data-assessment.md   (DQS 74 → branched class)
/lifecycle map            → (stage map consumed internally; all 11 events mapped by lookup)
/lifecycle journeys       → 02-portfolio.md          (9 generated, 2 blocked, tracking notes)
                          → 03-journey-cart-recovery.md (P0 journey doc, 8 steps, branched)
/lifecycle copy tr        → 04-copy-cart-recovery.md (steps 1–3, TR, reviewed ✅)
/lifecycle export json    → 05-journey-cart-recovery.json (validates against journey.schema.json)
```

## Files in this example

| File | What it shows |
|---|---|
| [01-data-assessment.md](01-data-assessment.md) | `lifecycle-connect` output: source, DQS component breakdown, event inventory, gaps |
| [02-portfolio.md](02-portfolio.md) | Full journey portfolio: 9 generated + 2 blocked, coverage, conflict math, roadmap |
| [03-journey-cart-recovery.md](03-journey-cart-recovery.md) | One complete P0 journey doc (`ecom-abandoned-cart-01`, branched, 8 steps) |
| [04-copy-cart-recovery.md](04-copy-cart-recovery.md) | Copy for the first 3 steps, Turkish, real character counts, review passed |
| [05-journey-cart-recovery.json](05-journey-cart-recovery.json) | The same journey as machine-readable JSON per [journey.schema.json](../../templates/journey.schema.json) |

The other eight journey docs and their copy are omitted from the repo for brevity — `ecom-abandoned-cart-01` is the representative deep dive. In a real run, every generated journey gets its own doc in `output/<project>/`.

## Why this example matters

DQS 74 crosses the **branched** threshold (≥ 70, see [data-quality-score.md](../../docs/data-quality-score.md)): journeys may use behavioral branches (opened / clicked / checkout-started), value-based gates (`cart_value`), and multi-channel orchestration. Compare with [saas-csv-only](../saas-csv-only/README.md) (standard) and [fintech-industry-only](../fintech-industry-only/README.md) (simple) to see what each tier buys.

# claude-lifecycle

**Journeys are a function of your data — most tools pretend otherwise.** A store tracking `add_to_cart` → `purchase` can run a branched 8-step cart recovery; a startup with three tracked events cannot. claude-lifecycle is a [Claude Code](https://claude.com/claude-code) plugin that scores what your data actually supports first, then generates a portfolio of customer journeys — and rule-checked, sector-aware CRM copy for every step — sized to that reality, not a template.

![validate](https://github.com/ali-demirbas/claude-lifecycle/actions/workflows/validate.yml/badge.svg)
![license](https://img.shields.io/badge/license-MIT-blue)
![claude-code](https://img.shields.io/badge/Claude_Code-plugin-d97706)
![patterns](https://img.shields.io/badge/journey_patterns-26-8b5cf6)
![industries](https://img.shields.io/badge/industries-9-10b981)

---

## Why this exists

Every lifecycle tool ships the same five template flows, regardless of what data backs them. Handing a startup with three tracked events the same branching journey as a mature e-commerce store produces automations that can neither trigger nor be measured. This engine makes that constraint explicit instead of hiding it:

- **Data quality is scored, not assumed.** A 0–100 [Data Quality Score](docs/data-quality-score.md) decides whether you get 3-step time-based flows or 10+ step behavioral branching.
- **Journeys are a portfolio, not a listicle.** Eligibility is computed per pattern from required-event signatures; what your data can't support becomes a [tracking plan](templates/tracking-plan.md) telling you exactly which events unlock which journeys.
- **Copy is an engineered artifact.** Channel files carry hard limits and banned words; sector lexicons decide vocabulary; a reviewer agent adversarially checks every message before you see it.

## How it works

![claude-lifecycle pipeline: data input tiers feed a Connect stage that scores a 0-100 Data Quality Score, then Map turns events into a stage map, a gap check routes to a short Intake or straight to the Journeys portfolio engine, which produces both Copy and a Tracking Plan, converging on Export](docs/pipeline-diagram.svg)

Full walkthrough with design decisions: [docs/architecture.md](docs/architecture.md)

**Zero-install demo:** the two HTML deliverables, rendered with sample data — [journey canvas](https://ali-demirbas.github.io/claude-lifecycle/demo/journey-canvas.html) · [channel copy canvas](https://ali-demirbas.github.io/claude-lifecycle/demo/iletisim-metinleri.html)

## Quickstart

```bash
# as a Claude Code plugin (marketplace or local)
/plugin install claude-lifecycle

# or clone and use as a project
git clone https://github.com/ali-demirbas/claude-lifecycle && cd claude-lifecycle && claude
```

Then, inside Claude Code:

```
/lifecycle connect          # score your data (GA4 via MCP, or point at a CSV)
/lifecycle journeys         # generate the portfolio
/lifecycle copy             # channel copy for the generated journeys
```

No data at all? `"/lifecycle journeys, my sector is fintech, no data"` works too: you get the sector playbook's priority journeys in their simple form, plus the tracking plan that upgrades them.

## The three tiers

| Tier | You have | You get |
|---|---|---|
| **T1** | GA4 connected (MCP) | Behavioral triggers, multi-branch journeys (7–12 steps where data supports it), volume-aware conflict review |
| **T2** | CSV / analytics export | Behavioral triggers, limited branching (4–7 steps) |
| **T3** | Just your industry | Playbook-driven starter portfolio (3–5 step flows) + a tracking plan to graduate to T1 |

## What's inside

| | |
|---|---|
| [`skills/`](skills/) | 11 skills: `lifecycle` routes; connect → map → intake → **journeys** → copy → export, plus audit, **results** (the measurement loop), **audience** (BigQuery SQL / CDP traits from journey audiences), and **qa** (trigger test payloads, positive and negative) |
| [`agents/`](agents/) | 4 subagents: event-analyst, journey-architect, and the copy-writer / copy-reviewer adversarial pair |
| [`knowledge/journey-patterns/`](knowledge/journey-patterns/) | 26 patterns (lead-nurture, care-alert, abandoned-cart, trial-conversion, churn-prevention, winback, channel-opt-in, gamified-rewards, …) each with a required-event signature and DQS-tied depth scaling |
| [`knowledge/industries/`](knowledge/industries/) | 9 sector playbooks: funnel, event expectations, pattern priorities, timing. [Add yours](docs/adding-an-industry.md): it's a content PR, not code |
| [`knowledge/lexicons/`](knowledge/lexicons/) | Sector word choice: use/avoid tables, urgency rules, banned lists, regulated-context flag, plus [`locales/`](knowledge/lexicons/locales/) language overlays (per-language voice, emotion calibration, market red lines) |
| [`knowledge/brands/`](knowledge/brands/) | Company config layer: per-brand tone, incentive policy, channels; rules inherit Company → Sector → Global, strictest compliance wins |
| [`knowledge/channels/`](knowledge/channels/) | Hard rules for email, push, SMS, in-app, WhatsApp: limits, spam lists, consent, quiet hours |
| [`templates/`](templates/) | Mandatory output formats + [`journey.schema.json`](templates/journey.schema.json) for CRM-agnostic export ([Braze/Klaviyo/Iterable/Insider mapping](docs/crm-export-mapping.md)) |
| [`examples/`](examples/) | Full end-to-end outputs for each tier |

## Example output (excerpt)

A T1 e-commerce run produces a portfolio like:

| # | Journey | Stage | Priority | Depth | Status |
|---|---------|-------|----------|-------|--------|
| 1 | Cart recovery | Revenue | P0 | 8 steps, branched | ✅ generated |
| 2 | Browse abandonment | Revenue | P0 | 4 steps | ✅ generated |
| 3 | Post-purchase → 2nd order | Retention | P0 | 6 steps | ✅ generated |
| 4 | Winback (lapsed buyers) | Winback | P0 | 5 steps | ✅ generated |
| 5 | Replenishment | Revenue | P1 | n/a | 🔒 blocked (missing item-level `items` params) |

…where every ✅ is a full [journey doc](templates/journey-doc.md) (trigger, audience, exit criteria, step table, KPIs + holdout, Mermaid diagram) and every 🔒 lands in the tracking plan with the event that unlocks it. See [examples/ecommerce-full-ga4/](examples/ecommerce-full-ga4/).

## Design principles

1. **One engine, data-driven sectors.** No `if industry == "fintech"` in skills; sector behavior lives in playbook/lexicon files, so extending the engine is a content contribution.
2. **Deterministic where it matters.** Eligibility, prioritization, and depth follow written rules ([DQS rubric](docs/data-quality-score.md)); the model's creativity goes into copy and sequencing, not into deciding whether a journey is possible.
3. **Honest by construction.** No fabricated benchmarks, no fake urgency, no journeys pretending untracked events exist. The never-do lists in every skill are load-bearing.

## Real-world validation

Beyond the eval suite, see [docs/real-world-validation.md](docs/real-world-validation.md) for what happened when someone ran this against a real product: what held up, and what gaps it surfaced that got folded back into the engine.

## Contributing

New industries, patterns, and sharper channel rules are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/adding-an-industry.md](docs/adding-an-industry.md). Run `bash scripts/validate.sh` before opening a PR.

## License

[MIT](LICENSE)

# Adapters

Deterministic bridges from the engine's CRM-agnostic outputs to specific tools. The contract: an adapter **reads** the canonical artifacts (`journey.schema.json`-valid JSON, copy docs with `{{snake_case}}` variables) and **emits** something a specific tool ingests — it never changes the canonical files, and it never invents an API shape that isn't documented in [docs/crm-export-mapping.md](../docs/crm-export-mapping.md).

| Adapter | Does | Status |
|---|---|---|
| `variables.py` | `{{snake_case}}` → Braze Liquid / Klaviyo / Iterable Handlebars / Insider syntax | ✅ |
| `durations.py` | ISO 8601 `steps[].wait` (e.g. `P3DT12H`) → integer + unit delay input | ✅ |

## Contributing an adapter

The most valuable PR this repo can receive: an adapter for your CRM. Ground rules (they mirror CONTRIBUTING.md):

1. Input is always the canonical schema/copy format — never a bespoke intermediate.
2. Every field mapping you implement must exist as a row in `docs/crm-export-mapping.md` (add it in the same PR) — the doc is the spec, the adapter is the spec made executable.
3. No fabricated API payloads: implement only what the tool's public docs define, and link them in your PR.
4. Add at least one fixture + an `expect` line in `scripts/tests/run_tests.sh`.

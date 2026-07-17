---
name: lifecycle-export
description: Export generated journeys as CRM-agnostic JSON (journey.schema.json), Mermaid diagrams, or CSV step lists — mappable to Braze, Klaviyo, Iterable, Insider. Use when the user says "export", "JSON ver", "Braze'e aktar", "Klaviyo formatı", "dışa aktar".
---

# Lifecycle Export — Structured Output

Convert generated journey docs into machine-consumable formats. Exports are derived from journey docs — never hand-author an export that diverges from its doc.

## Formats

| Format | What | Notes |
|---|---|---|
| **HTML canvas** (THE default deliverable — user-approved format) | Journey tabs + meta card (SEGMENT/AMAÇ/PRIMARY METRIC) + vertical tree canvas: entry/decision/message/exit node cards, Evet/Hayır branch pills, SVG connectors, tooltips, DETAYLAR toggles, print view, HTML/PDF download hints | Reproduce `${CLAUDE_PLUGIN_ROOT}/templates/canvas.html` EXACTLY — replace only the `JOURNEYS` data array, eyebrow/h1/lede texts, and `HOLDOUT_TIP`/`DATA_NOTE` constants with real data. Never redesign it, never add extra views |
| HTML report (optional, on request) | Single page: DQS breakdown, urgent findings, portfolio table, roadmap | `${CLAUDE_PLUGIN_ROOT}/templates/report.html` — offer only when the user asks for an assessment summary beyond the canvas |
| JSON | One file per journey, validating against `${CLAUDE_PLUGIN_ROOT}/templates/journey.schema.json` | The canonical machine export. Waits use ISO 8601 durations (`PT1H`, `P1D`) |
| Mermaid | `flowchart TD` per journey (already in each doc §8) | Bundled into one .md on request |
| CSV | Flat step list: journey_id, step, wait, channel, intent, branch_condition | For spreadsheet review with non-technical stakeholders |

HTML rules: fully self-contained (inline CSS/JS, no CDN), both themes token-based, no em dashes in customer-visible copy embedded in them, all numbers from real data — the reference templates' demo values never leak into a real export.

## Procedure

1. Ask which journeys (default: whole portfolio) and which format (default: JSON).
2. Transform each journey doc section-by-section into the schema fields. Field mapping guidance for specific CRMs: `${CLAUDE_PLUGIN_ROOT}/docs/crm-export-mapping.md` — when the user names their CRM, include that tool's mapping table in the output and rename nothing in the JSON itself (the JSON stays CRM-agnostic; the mapping table is the bridge). **Additionally, for the four documented tools (Braze, Klaviyo, Iterable, Insider): convert the copy files' `{{snake_case}}` variables to the tool's native syntax** using `python3 adapters/variables.py <tool> <file>` (deterministic, backed by the mapping table's syntax row) and write the converted copy alongside the agnostic one as `exports/copy-<tool>.md`. **Also convert each step's `wait` (ISO 8601) to the tool's integer+unit delay input** using `python3 adapters/durations.py <tool> <wait>` — same rationale as the variable-syntax adapter, arithmetic rounding a table lookup gets right every time. Undocumented tools get the existing prose-mapping treatment, never invented syntax.
3. Validate every JSON with `python3 scripts/validate_output.py journey <files>` before presenting — schema, `version` (SemVer, bump on change), embedded `constraints` (allowed channels, discount cap), KPI shape. Copy docs go through `python3 scripts/validate_output.py copy <files> --max-discount <brand's incentive_policy.max_discount_pct>` — **the flag is required, not optional**: without it the discount-ceiling check silently no-ops (it only runs when a numeric cap is passed), so a discount over the brand cap would pass validation unchecked. Character counts are recounted in code, not trusted. A violation is a hard stop, not a silent fix.
4. Write files to `output/<project>/exports/` (gitignored) and show one full example inline, summarizing the rest.

## Never do

- Never emit JSON that violates the schema (wrong enum, missing required field, malformed id pattern `<sector>-<pattern>-<nn>`).
- Never invent CRM-specific field names in the JSON — CRM specificity lives only in the mapping table.
- Never export copy that hasn't passed copy review; export copy refs (`step-1`) instead and say copy is pending.

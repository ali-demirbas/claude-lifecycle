---
name: lifecycle-export
argument-hint: "[json|mermaid|csv|report]"
description: Export generated journeys as CRM-agnostic JSON (journey.schema.json), Mermaid diagrams, or CSV step lists. Use when the user says "export", "JSON ver", "dışa aktar", "şema çıktısı", "CSV ver".
metadata:
  version: 0.1.0
  category: export
  updated: 2026-08-14
---

# Lifecycle Export — Structured Output

Convert generated journey docs into machine-consumable formats. Exports are derived from journey docs — never hand-author an export that diverges from its doc.

## When NOT to use this

- **No journeys exist yet** — there's nothing to convert; run `lifecycle-journeys` first.
- **The ask is just the normal user-facing deliverable for a fresh run** — the HTML canvas is already produced by `lifecycle-journeys`/`lifecycle-copy`'s own Output steps; this skill is for the *additional* formats (JSON, Mermaid, CSV, the standalone report) or a re-export on request, not the default path.
- **Copy hasn't finished its review loop yet** — export refuses to ship unreviewed copy regardless; the fix is finishing `lifecycle-copy`'s write → review → fix cycle, not forcing an export around it.

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
2. Transform each journey doc section-by-section into the schema fields. The JSON stays CRM-agnostic: `{{snake_case}}` variables, ISO 8601 waits, the schema's own channel and trigger vocabulary. **Never translate any of it into a specific tool's syntax.** Whoever imports it knows their own tool's variable syntax, delay input and step types; this engine does not, and a mapping written from memory is a fabrication (CLAUDE.md rule 3) that fails silently at import — the wrong Liquid filter or an off-by-one delay unit ships as a working-looking journey. When the user asks for their tool's format, say plainly that the export is the agnostic schema and the import mapping is theirs to apply.
3. Validate every JSON with `python3 scripts/validate_output.py journey <files>` before presenting — schema, `version` (SemVer, bump on change), embedded `constraints` (allowed channels, discount cap), KPI shape. Copy docs go through `python3 scripts/validate_output.py copy <files> --max-discount <brand's incentive_policy.max_discount_pct>` — **the flag is required, not optional**: without it the discount-ceiling check silently no-ops (it only runs when a numeric cap is passed), so a discount over the brand cap would pass validation unchecked. Character counts are recounted in code, not trusted. A violation is a hard stop, not a silent fix.
4. Write files to `output/<project>/exports/` (gitignored) and show one full example inline, summarizing the rest.

## Never do

- Never emit JSON that violates the schema (wrong enum, missing required field, malformed id pattern `<sector>-<pattern>-<nn>`).
- Never invent CRM-specific field names, variable syntax, or delay units, in the JSON or alongside it. The export stops at the agnostic schema; the import mapping belongs to whoever owns the tool.
- Never export copy that hasn't passed copy review; export copy refs (`step-1`) instead and say copy is pending.

---
name: lifecycle-audience
description: Turn journey audience definitions into executable artifacts — BigQuery SQL against the standard GA4 export schema, or a CDP-agnostic trait definition — so the data team receives a query, not a ticket. Use when the user says "audience SQL", "kitle sorgusu", "BigQuery sorgusu", "segmenti SQL'e çevir", "trait üret".
---

# Lifecycle Audience — From Definition to Query

A journey doc's §3 says "users with ≥ 2 `view_item` in 30 days and no `purchase`" — and then a human translates that into a data-team ticket. The engine already knows the events, the params, and the windows; this skill writes the query itself. It is the bridge over the "designed but not activatable" gap: the portfolio's audiences become artifacts a data engineer can run today.

## Inputs (gate)

1. `portfolio.json` + journey docs (the audience include/exclude definitions).
2. **Data substrate — this decides everything:**
   - **GA4 BigQuery export available** → generate BigQuery SQL against the standard `events_*` export schema (public, documented, stable). This is the primary mode.
   - **Composable / warehouse-native CDP (reads audiences directly from the same BigQuery project via reverse-ETL)** → this is not a third format, it's BigQuery mode: the audience is already one SQL model away from activation, and a reverse-ETL sync consumes a query result directly, so a separate trait translation would just be a redundant hop. Emit the same labeled SQL as the primary mode, and note which sync key it's meant to feed (e.g. "model query, sync key = user_pseudo_id").
   - **CDP (Segment-class, ingests its own copy of the data)** → generate a tool-agnostic trait definition (JSON: conditions, windows, event references) plus prose mapping notes — never a specific vendor's API body without documentation in hand.
   - **Neither** → this skill is **blocked**; say so and point at the tracking plan's identity item. No substrate, no query — pretending otherwise is the exact dishonesty the engine exists to prevent.

## BigQuery mode (primary)

Schema knowledge lives in `${CLAUDE_PLUGIN_ROOT}/knowledge/audience-sql.md` — read it before writing a line of SQL. Non-negotiables:

- One labeled query per journey: `-- journey: <id> · audience: include` with the exclude conditions as `AND NOT EXISTS` blocks, not a separate query someone forgets to apply.
- Identity: prefer `user_id` when the reporting identity is set; fall back to `user_pseudo_id` **and say so in a comment** (device-scoped, not person-scoped — cross-device exclusions will leak).
- Time windows via `_TABLE_SUFFIX` bounds, never full-table scans; window lengths come from the journey doc, not invented.
- Event params through the documented `UNNEST(event_params)` pattern; only params the mapped inventory confirms exist.
- Every query ends with a `-- validates:` comment naming the journey-doc line it implements — the decision-trace rule applied to SQL.

## Output

`output/<project>/audiences.sql` (BigQuery mode) or `audiences-traits.json` (CDP mode) — machine-facing artifacts (CLAUDE.md rule 2). Present to the user: one full example inline + a one-line summary per remaining audience, **plus the estimated audience size for each** — a dry-run row count where one can be run, otherwise an explicit "run `bq query --dry_run` before executing" instruction. A number the user can sanity-check against their own sense of the segment (near-zero or near-total is a logic bug, not a result to accept) beats a query they have to run blind to find out.

## Never do

- Never generate SQL against a guessed schema — custom/renamed tables → ask for one `INFORMATION_SCHEMA` listing or a sample row, then adapt.
- Never fold marketing-consent filtering silently into the query — consent lives in the CRM/İYS layer; the SQL selects the *behavioral* audience and a comment says consent filtering happens downstream.
- Never emit a query for an audience whose defining event is in the tracking plan's missing list — blocked is blocked, in SQL too.
- Never ship an audience query without a size signal (dry-run estimate, or an explicit instruction to get one before running) — an unvalidated query is exactly how an audience leak (accidentally targeting everyone, or no one) reaches a live send.
- Never return an identity-only audience when the journey's copy needs item/product/discount personalization — select those fields alongside identity (`knowledge/audience-sql.md` rule 6).

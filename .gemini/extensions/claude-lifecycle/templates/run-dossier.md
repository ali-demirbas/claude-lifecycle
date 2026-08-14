# Run Dossier Template

The single human-readable record of a full engine run: what went in, what came out, what stays open. Produced at the end of every run (after copy when copy ran) as `output/<project>/dossier.md`, **written in the user's language**. Together with the two canvases this is the user-facing deliverable set — JSON artifacts are machine-facing and are not presented (CLAUDE.md rule 2).

Keep it to roughly one page: this is the document a stakeholder reads instead of the raw outputs, not a second copy of them.

---

# <Company / Project> — Lifecycle Run Dossier

**Date:** <date> · **Run ID:** `<YYYYMMDD-HHmm>` *(local time, minute precision — the file's own audit-trail key; see §1a)* · **Sector:** <sector> · **Tier:** T1 | T2 | T3 · **DQS:** <n>/100 <· activation flag when set>

## 1. Input profile

- **Source:** <what data existed: events, attributes, exports, or "industry-only">
- **Channels:** <channels + consent state>
- **Goal priority:** <from intake>
- **Blocked signals:** <missing events blocking P0 patterns, one line>
- **Learning history consulted:** <e.g. "failed-strategies.md: 1 entry, avoided repeating the discount-led winback angle for this segment" / "results log: 3 prior journeys scored" — or "first run for this brand, no history yet". Never silently skip this line: a stakeholder can't tell "we knew and chose differently" from "we didn't know" unless it's stated.

## 1a. Versus previous run *(omit entirely on a brand's first-ever run — never show an empty section)*

<When `output/<project>/dossier.md` already existed before this run overwrote it (see the archiving rule in `skills/lifecycle-journeys/SKILL.md`): reference the archived prior run by its Run ID, e.g. "vs run `20260610-0930`: DQS 45→69 (tracking-plan items E-02, E-04 implemented), 2 new journeys unlocked (churn-prevention, upsell-cross-sell), 1 journey retired (replenishment — pattern no longer eligible)." 2-3 lines, facts only, no re-litigating why the old run's choices were made — that's what the archived dossier itself is for.>

## 2. Portfolio produced

| # | Journey | Pattern | Priority | Trigger | Steps | Status |
|---|---------|---------|----------|---------|-------|--------|

Per journey, 2–4 lines below the table: trigger → step chain in one line → exit rule. Blocked patterns do NOT appear here — they live in §5.

## 3. Conflict review

Precedence and entry-gate decisions, plus worst-case weekly load vs caps (including declared overlaps). 3–5 lines.

## 4. Copy summary *(only when the copy stage ran)*

Which rule sets bound the copy (lexicon, regulated flags), the review result (n blocks, violations, legal flags), and at most 1–2 sample blocks — the full set lives in the copy canvas.

## 5. Open items

- Tracking plan top items (priority + which journey each unlocks)
- Questions only the user's team can answer
- Legal/sign-off flags awaiting approval

## 6. File map

| File | For |
|---|---|
| `canvas.html` | user — journey flows |
| `iletisim-metinleri.html` *(name follows the user's language; EN: `message-copy.html`)* | user — channel copy |
| `dossier.md` | user — this document |
| `runs/dossier-<old-run-id>.md` *(when a previous run existed)* | audit trail — the prior run's dossier, archived rather than overwritten; referenced from §1a |
| `portfolio.json`, `<journey>.json` | machine — validator & CRM export; shown only when export is explicitly requested |
| `audiences.sql` / `audiences-traits.json`, `qa-payloads.json` *(when requested)* | machine — data team & CRM QA |

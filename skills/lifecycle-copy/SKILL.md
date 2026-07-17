---
name: lifecycle-copy
description: Write CRM channel copy (email, push, SMS, in-app, WhatsApp) for journey steps — rule-checked against channel limits and sector lexicons, with A/B variants and character counts. Use when the user says "copy yaz", "metin yaz", "email metni", "push metni", "CRM copy", "write the messages".
---

# Lifecycle Copy — Channel Copywriting

Produce send-ready copy for journey steps. Copy here is an engineering artifact: it has hard constraints (limits, banned words, consent text) and is **reviewed before it is shown**. The mandatory format is `${CLAUDE_PLUGIN_ROOT}/templates/copy-output.md`.

## Inputs (gate)

1. A journey doc (from `lifecycle-journeys`) OR a user-supplied step description (channel + intent minimum).
2. The rule chain, loaded in inheritance order (CLAUDE.md rule 8 — most specific wins, bans/compliance strictest wins):
   - `${CLAUDE_PLUGIN_ROOT}/knowledge/brands/<brand>.md` if it exists — tone/formality override; `extra_banned_words` extend all ban lists; `brand_vocabulary` is authoritative for product/feature names.
   - `${CLAUDE_PLUGIN_ROOT}/knowledge/lexicons/locales/<lang>.md` per target language — voice, emotion calibration, market red lines.
   - `${CLAUDE_PLUGIN_ROOT}/knowledge/lexicons/<sector>.md`. No lexicon for the sector → use the closest and say so.
3. Tone + formality + language(s) from the brand file or Intake Summary. Missing → trigger `lifecycle-intake` (tone questions only).
4. **Persona context:** the journey doc's §3 audience definition (segment, lifecycle stage, RFM tier where known) is passed to the writer — copy addresses that persona, never a generic user.
5. **Failed-strategies check:** if `output/<brand>/failed-strategies.md` exists, a logged powered failure is not re-proposed to the same segment; when a strategy is skipped because of the log, say which entry caused it.
6. **Winning-strategies check:** if `output/<brand>/winning-strategies.md` exists and has a confirmed entry for this segment/journey stage, pass it to the writer as a precedent — it informs one variant's starting angle, never both; the other variant still explores a genuinely different, less-tested angle. A precedent narrows a starting point, it doesn't replace the two-distinct-angles rule.

## Procedure — write → review → fix (mandatory loop)

### 1. Load the rules

For every channel used, load `${CLAUDE_PLUGIN_ROOT}/knowledge/channels/<channel>.md` — its frontmatter `limits` and "Hard rules" are the review contract. Load the lexicon's use/avoid table, urgency rules, and banned list.

### 2. Write

When multiple journeys need copy, spawn one `copy-writer` per journey **concurrently in a single message** (the agent is designed for exactly this parallelization). For each journey step (its **intent line is the brief** — don't drift from it):
- A **target tone** per step, drawn from the lexicon's stage-calibration table and adjusted by the locale overlay's emotion calibration — goes in the template's Target tone field and binds the writer.
- Variant A and Variant B with genuinely different angles (e.g. utility vs social proof) — not synonym swaps. Each variant carries the template's `strategy` + `hypothesis` JSON metadata (one falsifiable sentence — `lifecycle-results` scores these later).
- One short Fallback with no personalization variables.
- Real character counts per field (count characters, do not estimate; for SMS respect the GSM-7 vs Unicode distinction in the channel file — Turkish characters change the limit).

### 3. Review (adversarial)

Delegate to the `copy-reviewer` agent (or, if subagents are unavailable, perform the same checklist yourself in a separate explicit pass):
- limits per field · banned/spam words (channel + lexicon) · single-CTA rule · urgency claims backed by real data variables · variable fallbacks exist · consent/opt-out text where required · tone matches lexicon calibration for the journey stage.
- Verdict per block: PASS / FIX (with the exact violation).

### 4. Fix and re-check

FIX blocks are rewritten and re-checked. Nothing labeled FIX may reach the user. If a rule cannot be satisfied (e.g. intent impossible in 120 push chars), change the step's channel recommendation and tell the user why.

**Legal-review path:** when the sector lexicon has `regulated: true` and a block carries a borderline money/health/outcome claim that is not outright banned, the block ships stamped `⚖️ legal review required` (with the exact claim quoted) instead of ✅ — it goes to manual sign-off, not into the send queue.

### 5. Deliver

**Mandatory format: `${CLAUDE_PLUGIN_ROOT}/templates/copy-canvas.html`, reproduced verbatim — by copying the template file and editing only the swappable parts in place, never by retyping the boilerplate** (same convention as `templates/canvas.html` for journeys — copy only the `JOURNEYS` data array, the `<title>`, and the header eyebrow/h1/lede text, never redesign the page). The artifact's user-facing name and header follow the **user's language**, and never use the word "copy" toward Turkish users (it reads as "kopya/duplicate"): TR → "İletişim Metinleri", EN → "Message Copy". **This covers the generated FILE NAME too:** write the output to `output/<project>/iletisim-metinleri.html` (TR) / `message-copy.html` (EN) — and the markdown source-of-truth alongside it with the same base name — never `copy-canvas.html`/`copy-*.md`; only the repo template keeps its English name. One journey per tab, one card per step, review-status badge per card (✅ / ⚠️ with note / ⚖️ legal). The plain `templates/copy-output.md` structure is still the underlying content model each step's fields/variants/fallback follow — the HTML canvas is how it reaches the user, per this repo's output-authoring rule (CLAUDE.md rule 2). Multi-language requests: write each language natively per the lexicon's TR/EN notes — never translate literally.

## Word choice discipline

- The lexicon decides vocabulary; if a lexicon rule and a "nicer sounding" line conflict, the lexicon wins.
- Concrete beats clever: product names, real numbers (as `{{variables}}`), stated policies.
- Urgency/scarcity only when backed by a data variable that exists (`{{stock_count}}`, `{{sale_end_date}}`). No data → no urgency. Ever.

## Never do

- Never show unreviewed copy or skip the review pass "because it's short".
- Never output copy without character counts, or with estimated counts.
- Never use a personalization variable that the user's data cannot fill (check the event/attribute inventory).
- Never write identical copy across variants or across channels (each channel has its own shape, not a resize).
- Never use an em dash or en dash in customer-facing copy — commas, periods, parentheses, conjunctions.
- Never ASCII-fold diacritics (ç, ğ, ı, İ, ö, ş, ü …) in any channel; the only exception is deliberate, user-approved GSM-7 folding for SMS cost (see `knowledge/channels/sms.md`).

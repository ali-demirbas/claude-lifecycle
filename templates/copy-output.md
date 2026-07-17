# Copy Output Template

Every piece of CRM copy produced by `lifecycle-copy` MUST use this structure — one block per journey step.
Character counts are mandatory and must be actual counts, not estimates. Variants A/B differ in angle, not just wording.

---

# Copy — <Journey name> (`<journey-id>`)

**Language:** <e.g. TR> · **Locale overlay:** [<lang>](../knowledge/lexicons/locales/<lang>.md) · **Lexicon:** [<sector>](../knowledge/lexicons/<sector>.md) · **Brand:** <brand-slug or —> · **Tone:** <from brand → lexicon chain>
**Audience/persona:** <from journey doc §3 — e.g. "lapsed high-RFM buyers", "trial users, not yet activated">
**Review status:** ✅ passed copy-reviewer | ⚠️ passed with notes | ⚖️ legal review required

## Step <n> — <channel> (`step-<n>`)

**Intent:** <one line, copied from the journey step table> · **Target tone:** <from the lexicon's stage calibration, e.g. "helpful reminder, zero guilt">

### Variant A — <angle, e.g. "direct-utility">

```json
{"strategy": "<e.g. loss-aversion>", "hypothesis": "<what this variant tests vs the other — e.g. product benefit beats discount emphasis for this segment>"}
```

| Field | Content | Chars | Limit |
|---|---|---|---|
| Subject / Title | <text with `{{vars}}`> | 34 | ≤ 50 |
| Preheader / Body | <text> | 82 | ≤ 90 |
| CTA | <verb-first, single CTA> | 12 | ≤ 20 |

### Variant B — <different angle, e.g. "social proof">

```json
{"strategy": "<different strategy>", "hypothesis": "<the competing hypothesis>"}
```

| Field | Content | Chars | Limit |
|---|---|---|---|
| … | | | |

### Fallback (short)

One minimal-personalization version safe to send when variables are missing (no `{{vars}}` except system-safe ones). **System-safe** means supplied by the same trigger event that fires the message itself, so it cannot be independently absent (an invoice number on a `payment_failed` step, an item name on a `back_in_stock` step) — never a user-profile attribute (`{{first_name}}`, `{{plan_name}}`) that can be null for reasons unrelated to the trigger firing. If a fallback still contains a non-system-safe variable, it is not a fallback — it is the same failure mode with an extra heading (`scripts/validate_output.py` checks the Fallback section's own content, not just that the heading exists).

**Personalization variables used:** `{{first_name}}`, `{{product_name}}`, … (CRM-agnostic; mapping table in [crm-export-mapping.md](../docs/crm-export-mapping.md))
**Reviewer notes:** <only if ⚠️ — what was flagged and why it is acceptable; if ⚖️ — the exact claim needing legal sign-off and which lexicon/locale rule triggered it>

Variant metadata rules: `strategy` is a short slug (loss-aversion, social-proof, utility, progress, reciprocity); `hypothesis` is one falsifiable sentence — `lifecycle-results` reads these labels when scoring test outcomes, and confirmed/refuted hypotheses feed the brand's results log.

---

Table rules (enforced by `scripts/validate_output.py`):
- **Chars and Limit columns are always characters** — body budgets included (e.g. email body ≤ 350 chars, never a word count); the validator recounts every cell.
- The Limit column may be **stricter** than the channel file's ceiling, never looser — inflating your own limit column is a named violation (Limit Inflation).

Field sets per channel (use the applicable rows only):

| Channel | Fields |
|---|---|
| email | Subject, Preheader, Body (markdown ok), CTA |
| push | Title, Body, CTA (deeplink label), Image (optional, see below) |
| sms | Body (single field, opt-out text included in count) |
| in-app | Title, Body, Primary CTA, Secondary CTA (optional) |
| whatsapp | Template category, Header, Body, Button(s) |

**Push Image (optional):** not a chars-counted table row — a URL has no meaningful character ceiling the way a title/body does. Written as its own line right after the table: `**Image:** <https URL or —> · **Alt text:** <short description>`. The validator checks the line is well-formed (HTTPS URL, non-empty alt text if an image is present) — it cannot verify the actual downloaded file size or that the URL resolves, since that would require a network fetch this offline validator deliberately doesn't do; see `knowledge/channels/push.md`'s Rich media section for the ≤1MB guidance to apply by hand.

# Adding an Industry

Adding a sector to claude-lifecycle is a content contribution, not a code change. Two files, one optional pattern, and a validation run.

## 1. Create the playbook

Copy [`knowledge/industries/_template.md`](../knowledge/industries/_template.md) to `knowledge/industries/<sector-slug>.md` and fill every section. The rules that matter most:

- **`name`** must equal the filename slug and the lexicon's `name` — the engine joins on it.
- **`funnel`** is an ordered list of event slugs; prefer GA4 recommended names from [`ga4-recommended-events.md`](../knowledge/event-taxonomy/ga4-recommended-events.md), invent `snake_case` only when nothing standard exists.
- **`pattern_priorities`** keys must be existing files in `knowledge/journey-patterns/` (validation fails otherwise). Score 10–15 patterns honestly: not everything is P0, and explicitly listing not-applicable patterns in the rationale section is required — it is what stops the engine from generating nonsense.
- **Event expectations** must split must-have (blocks P0 journeys) from nice-to-have (unlocks depth). `lifecycle-connect` scores DQS against this section.
- **Intake questions** (3–5) should ask only what changes the output for this sector.

## 2. Create the lexicon

Mirror [`knowledge/lexicons/ecommerce.md`](../knowledge/lexicons/ecommerce.md): same frontmatter keys (`name`, `pairs_with`, `tone`, `formality`, `urgency_allowed`, `emoji_policy`) and same sections. The bar:

- The use/avoid table needs ≥ 6 rows with real TR + EN examples and a *why* per row.
- The "Banned outright" list must be sector-specific, not a copy of the spam list (channel files already cover generic spam).
- Regulated sectors (finance, health): state the regulatory posture explicitly, as `lexicons/fintech.md` does.

## 3. (Optional) Add a sector-specific pattern

If the sector has a journey shape no existing pattern covers, add `knowledge/journey-patterns/<slug>.md` following `abandoned-cart.md`'s frontmatter and section structure exactly, and add the slug to relevant playbooks' `pattern_priorities`.

## 4. Validate and test

```bash
scripts/validate.sh
```

Then dry-run the engine on your sector with no data (Tier 3):

```
/lifecycle journeys — sektörüm <sector>, verim yok
```

Check: intake asks your sector questions; the portfolio's P0s match your `pattern_priorities`; nothing references events your funnel doesn't define.

## Quality bar for PRs

- No fabricated statistics ("industry average is 23.4%") — ranges and qualitative claims only.
- Every table row informative; no filler rows to hit a count.
- Write like a senior lifecycle marketer explaining to a colleague, not like documentation boilerplate.

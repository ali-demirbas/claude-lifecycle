---
name: lifecycle
description: Lifecycle marketing engine router. Use when the user says "lifecycle", "/lifecycle", "customer journey", "journey oluştur", "CRM kampanya", "marketing automation", "GA4 bağla ve journey üret", or any /lifecycle subcommand. Routes to lifecycle-connect, lifecycle-map, lifecycle-intake, lifecycle-journeys, lifecycle-copy, lifecycle-audit, lifecycle-export, lifecycle-audience, lifecycle-qa, lifecycle-results.
---

# Lifecycle — Router

You are the entry point of the claude-lifecycle engine. Parse the user's intent and route to the right sub-skill. Read `${CLAUDE_PLUGIN_ROOT}/CLAUDE.md` rules before doing anything — they are binding.

## Routing table

| User intent / subcommand | Route to | Notes |
|---|---|---|
| `connect`, "GA4 bağla", "verimi analiz et", "data quality" | lifecycle-connect | Always the first step for new projects |
| `map`, "event'leri haritala", "funnel çıkar" | lifecycle-map | Requires connect output (or runs it first) |
| `journeys`, "journey üret", "kampanya kur", "otomasyonlar" | lifecycle-journeys | The main deliverable |
| `copy`, "metin yaz", "email metni", "push metni" | lifecycle-copy | Can run standalone for an existing journey |
| `audit`, "journey'lerimi denetle" | lifecycle-audit | For existing/imported journey portfolios |
| `results`, "sonuçları gir", "performans verisi", "holdout sonuçları" | lifecycle-results | Closes the loop; needs a launched journey + performance data |
| `export`, "JSON ver", "Braze'e aktar" | lifecycle-export | Needs generated journeys |
| `audience`, "kitle sorgusu", "BigQuery SQL" | lifecycle-audience | Needs generated journeys + a data substrate (BigQuery export or CDP) |
| `qa`, "test payload", "tetikleyiciyi test et" | lifecycle-qa | Needs generated journeys |
| `intake` (rarely called directly) | lifecycle-intake | Usually triggered by other skills |

## Ambiguous intent

If a request plausibly matches two or more rows above (e.g., "datamı incele" could mean lifecycle-connect's data-quality assessment or lifecycle-map's event mapping), do not silently pick one — state the two interpretations in one line and ask which one. Same principle as CLAUDE.md rule 7 (ask when event classification fails), applied here to intent classification. Once resolved, don't re-ask the same disambiguation again later in the same session — treat the user's answer as settled for that session.

Phrasing that turns out genuinely ambiguous more than once is worth contributing back as a routing-table example (see CONTRIBUTING.md) — the same content-not-code principle as adding an industry.

## Pipeline logic (when the user asks for the whole thing)

"Journey'lerimi oluştur" with no prior state means the full pipeline:

```
connect → map → (intake if needed) → journeys → copy → export (on request)
```

0. **Check for an existing brand config first:** if `${CLAUDE_PLUGIN_ROOT}/knowledge/brands/` has a file for this company, load it before asking anything — it pre-fills intake and carries the inheritance chain (CLAUDE.md rule 8).
1. **Determine the data tier before anything else.**
   - GA4 MCP tools available (`mcp__ga4__*` or similar)? → Tier 1. Confirm which property to use.
   - User has a CSV/export file? → Tier 2.
   - Neither? → Tier 3: ask for the industry (must match a file in `${CLAUDE_PLUGIN_ROOT}/knowledge/industries/`; if none matches, use the closest and say so, or offer `_template.md` for a custom playbook).
2. **Pre-generation gate — ask these BEFORE any stage runs, in one grouped message, unless the user (or a brand config) already answered them.** These are cheap questions that gate expensive fan-out; skipping them is what makes a run silently balloon in time and tokens. Do not proceed to `connect`/`map`/`journeys` until they are settled (or explicitly defaulted with the tradeoff stated):
   - **a) Scope:** journeys only, or journeys + copy (the full canvas pair)? State plainly that journeys + copy runs meaningfully longer and uses noticeably more tokens — the pipeline spawns one subagent per journey for the portfolio, then one writer + one reviewer per journey again for copy, each reading the sector/brand/channel rules independently. Journeys-only is the lighter, faster option; copy can always be added later as a separate `/lifecycle copy` step once the portfolio looks right. Silence or "hepsini/tümünü/full pipeline" defaults to journeys + copy (CLAUDE.md's "portfolio without copy is incomplete" rule) — but the cost/time tradeoff is stated before that default kicks in, never assumed silently.
   - **b) Channel inventory:** which channels the brand can actually send on (email / push / SMS / in-app / WhatsApp), and roughly the audience size per channel. **Never assume a default channel set** — a journey built on push when the brand has no push consent, or on SMS with no İYS registration, is unshippable. On T1 some of this is inferable from the data; still confirm rather than assume. A brand config file (`knowledge/brands/<brand>.md` `channels_live`) answers this and skips the question. This is the same slot `lifecycle-intake`'s whitelist marks "always ask on T2/T3", surfaced here up front so channels are settled before generation, not discovered mid-run.
3. Run the pipeline stages in order. Each stage's output feeds the next; summarize between stages in ≤ 3 sentences.
4. If the user asks for a single stage, run only that stage, but state which prerequisites are missing and offer to run them.

## Never do

- Never generate journeys without a DQS (CLAUDE.md rule 1).
- Never dump raw sub-skill mechanics on the user — they see results, not plumbing.
- Never run `lifecycle-copy` before journeys exist, unless the user provides their own journey/step description.
- **Never start generation without settling the step-2 pre-generation gate (scope + channels) first.** `copy` is still a standard stage of the pipeline — a journey portfolio without its copy is an incomplete deliverable for a "journeys'imi oluştur" request, so copy stays the default outcome. What the gate changes: the user hears the time/token tradeoff and can say "journeys only for now", and the brand's real channel set is confirmed, before the expensive fan-out starts instead of it running on silent assumptions.
- **Never assume the channel set.** Channels come from the user, the brand config's `channels_live`, or (T1) confirmed data — never a hardcoded email/push/in-app default. Generating on a channel the brand can't actually send produces an unshippable portfolio.
- Never invent a sub-skill; if the request fits nothing above (e.g. "run my campaign"), say what this plugin does and does not do (it designs; it does not send).

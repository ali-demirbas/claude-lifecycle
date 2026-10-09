---
name: lifecycle
argument-hint: "[connect|map|journeys|copy|audit|export|audience|qa|results]"
description: Lifecycle marketing engine router. Use when the user says "lifecycle", "/lifecycle", "customer journey", "journey oluştur", "CRM kampanya", "marketing automation", "GA4 bağla ve journey üret", or any /lifecycle subcommand — or when a request plausibly matches more than one lifecycle-* skill (the router disambiguates instead of guessing). Routes to lifecycle-connect, lifecycle-map, lifecycle-intake, lifecycle-journeys, lifecycle-copy, lifecycle-audit, lifecycle-export, lifecycle-audience, lifecycle-qa, lifecycle-results.
metadata:
  version: 0.2.0
  category: router
  updated: 2026-10-09
---

# Lifecycle — Router

You are the entry point of the claude-lifecycle engine. Parse the user's intent and route to the right sub-skill. Read `${CLAUDE_PLUGIN_ROOT}/CLAUDE.md` rules before doing anything — they are binding.

## When NOT to use this directly

- **The user already named an unambiguous subcommand or sub-skill** ("run lifecycle-audit on this", "/lifecycle copy") — go straight to that skill; running it through the router's disambiguation step first is overhead with nothing to resolve.
- **Mid-pipeline, moving to the next stage the current skill already named** (e.g. `lifecycle-connect` just finished and said "next: lifecycle-map") — continue directly; re-entering the router to re-derive a routing decision that was already made adds a step, not a check.
- **The request names something this plugin doesn't do at all** (sending a live campaign, managing a CRM account) — don't force it into the closest-sounding row of the table below; say plainly what the plugin does and doesn't do (see Never do).

## Routing table

| User intent / subcommand | Route to | Notes |
|---|---|---|
| `connect`, "GA4 bağla", "verimi analiz et", "data quality" | lifecycle-connect | Always the first step for new projects |
| `map`, "event'leri haritala", "funnel çıkar" | lifecycle-map | Requires connect output (or runs it first) |
| `journeys`, "journey üret", "kampanya kur", "otomasyonlar" | lifecycle-journeys | The main deliverable |
| `copy`, "metin yaz", "email metni", "push metni" | lifecycle-copy | Can run standalone for an existing journey |
| `audit`, "journey'lerimi denetle" | lifecycle-audit | For existing/imported journey portfolios |
| `results`, "sonuçları gir", "performans verisi", "holdout sonuçları" | lifecycle-results | Closes the loop; needs a launched journey + performance data |
| `export`, "JSON ver", "dışa aktar" | lifecycle-export | Needs generated journeys |
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
2. **One start message — ask everything the run needs before any stage runs, once.** Collect what isn't already known from the conversation, a brand config, or (T1) confirmed data; never re-ask something the user already answered, and never ask a later stage's question again mid-run (intake reads what was answered here). In that single message:
   - **Scope:** journeys only, or journeys + copy. Copy has two modes: **full** (every journey, writer + reviewer each) or **quick draft** (P0 journeys only, one review pass, labelled as a draft). State the tradeoff in one line: copy roughly doubles the run's agents. Silence or "hepsini/tümünü" means journeys + full copy, with the tradeoff stated first.
   - **Breadth:** P0 only / P0 + P1 / everything eligible (the eligible list comes after `connect`/`map`; offer P0 + P1 as the default and confirm the count once it's known, only if it's larger than the user expects).
   - **Facts that change correctness, never assumed:** which channels the brand can send on and for which ones users have consented or opted out; existing automations/journeys already running (name, audience, roughly how many messages a week; "unknown" is a valid answer, and then frequency is verified only inside the new portfolio); what key dates mean where the data has them (e.g. is `renewal_date` the policy end or the billing date).
   - **Safe, reversible preferences get defaults** instead of questions: tone (sector lexicon), quiet hours (compliance file), holdout design (per journey, from volume), language (the user's). Each default used is stated in the dossier, so it can be changed later.
   Missing correctness facts don't block design, they block readiness: journeys built without them are delivered as **drafts** with the open items listed, never as ready to implement.
2a. **Clean context:** a full run is long. If this conversation already carries a lot of unrelated work, recommend starting the run in a fresh session (or `/clear` first); the earlier history is re-read on every turn of the run and was the single largest cost in a measured past run.
2b. **Single-journey requests.** When the user names one journey ("sadece sepet terk journey'si", "just the winback"), take `lifecycle-journeys`' single-journey path. Connect and map still run (or reuse the cache), because the journey's own event sufficiency depends on them. The start message asks only what that journey needs: consent on its channels, existing communications that reach its audience, the meaning of any date it anchors on.
2c. **Non-interactive runs** (no one can answer, e.g. `claude -p`): apply defaults only to the safe, reversible preferences. Never assume consent, a real deadline, an event's existence or the load of existing communications. Unknowns become open items and the affected journeys are drafts; an unknown existing load is `external_journeys_status: unknown`, never zero.
3. Run the pipeline stages in order. Each stage's output feeds the next; summarize between stages in ≤ 3 sentences.
4. If the user asks for a single stage, run only that stage, but state which prerequisites are missing and offer to run them.

## Never do

- Never generate journeys without a DQS (CLAUDE.md rule 1).
- Never dump raw sub-skill mechanics on the user — they see results, not plumbing.
- Never run `lifecycle-copy` before journeys exist, unless the user provides their own journey/step description.
- **Never start generation without the step-2 start message settled** (scope, breadth, and the correctness facts — or an explicit "unknown" for each, which makes the affected journeys drafts). Copy stays the default outcome of a full run; the user hears the tradeoff first and can choose journeys only or a quick draft.
- **Never assume the channel set.** Channels come from the user, the brand config's `channels_live`, or (T1) confirmed data — never a hardcoded email/push/in-app default. Generating on a channel the brand can't actually send produces an unshippable portfolio.
- Never invent a sub-skill; if the request fits nothing above (e.g. "run my campaign"), say what this plugin does and does not do (it designs; it does not send).

---
name: lifecycle-intake
description: Structured questioning to fill information gaps before journey generation — goals, brand tone, channel inventory, existing automations, sector specifics. Usually triggered automatically by lifecycle-journeys or lifecycle-copy when data is insufficient; can be invoked directly with "intake", "bana soru sor", "eksik bilgileri al".
---

# Lifecycle Intake — Structured Gap Filling

Collect ONLY the information that changes the output. Maximum 2 rounds of questions; each round is one message with grouped, numbered questions and pre-filled defaults the user can accept with "defaults ok".

## What may be asked (the whitelist)

Ask a question only if its answer is (a) not derivable from connected data, and (b) actually consumed by a downstream step:

| Topic | Consumed by | Ask when |
|---|---|---|
| Primary goal (growth / retention / revenue / reactivation) | journey prioritization | Always, unless user already stated it |
| Product rhythm — how often a typical user engages/purchases (daily / weekly / occasional-seasonal, with the actual cadence) | every lapse window, dormancy threshold, and cadence | Always on T3 (it is the only way to set winback/reactivation clocks without data); on T1/T2 only if not computable from median gaps |
| Channel inventory + rough audience size per channel | step channel selection | Always on T2/T3; on T1 only if not inferable |
| Existing automations (what already runs) | dedupe — don't generate what exists | Always |
| Multi-vertical product lines — does the company run genuinely separate product lines, each with its own funnel and conversion event (not just several features sharing one funnel)? If yes: each vertical's name, its closest `knowledge/industries/` fit, and how its events are named (e.g. "do the wallet features' events all start with `wallet_`?") | brand config `verticals`; per-vertical DQS/funnel/pattern-priorities in connect/map/journeys | When the event inventory shows 2+ event-name clusters with no shared conversion event, or the user volunteers it |
| Brand tone (2–3 adjectives) + formality (sen/siz, formal/informal) | lexicon calibration | Before any copy |
| Incentive policy (may journeys offer discounts? max % + is there a CLV threshold above which value-adds replace discounts — priority support, early access, extended feature trial) | incentive-gated steps: above the CLV bar prefer a value-add (protects margin, doesn't train price expectations); below it a capped discount. Threshold comes from the account's real unit economics, never a guessed round number. **If the user doesn't know their CLV:** skip the value-add/discount split, default to capped-discount-only, and record the threshold as an open gap — never guess a number to fill it | If sector uses incentives |
| Sector-specific questions | industry playbook "Intake questions" section | On T3, or when playbook flags them |
| Known campaign calendar (dated peak/sale windows) | knowledge/calendar-rules.md — campaign-vs-evergreen conflict review | If the sector runs seasonal campaigns; silence = rules dormant, portfolio notes it |
| One-click unsubscribe implemented in the ESP (header pair, not just a footer link)? | knowledge/deliverability.md floor | If email volume is meaningful (bulk-sender territory) |
| Target language(s) for copy | lifecycle-copy | Before any copy |
| Legal market(s) | compliance defaults | If not obvious from GA4 geo/user context |

## Question format rules

- Group by topic, number the questions, ≤ 8 questions per round.
- Every question carries a stated default: "*(default: retention-first)*". Silence = default.
- Round 2 exists only for follow-ups created by round-1 answers. Never a round 3 — proceed with defaults and list assumptions.
- **Contextual slot carryover:** before drafting questions, scan the conversation so far — if the user already stated an answer informally (even outside a formal intake round), treat it as answered and don't ask it again. The whitelist's "not derivable from connected data" test also covers "not already stated in this conversation."

## Plausibility check

If a user's answer to a quantitative question (audience size, channel volume) differs from connected data (T1/T2) by an order of magnitude or more, surface the mismatch as one soft confirmation rather than silently trusting either source — *"50k email abonesi dedin ama bağlı GA4 verisi ~2k toplam kullanıcı gösteriyor; senin rakamını mı kullanayım, veriyi mi, yoksa bu ikisi farklı kapsamlar mı (ör. ayrı bir ESP listesi)?"* This is not a validation gate — CLAUDE.md rule 9's trust hierarchy still applies and the user's answer wins by default — it just makes a real discrepancy visible instead of resolving it silently.

## Output

An **Intake Summary** block that downstream skills read verbatim:

```
goal: retention-first
channels: email (45k), push (12k), sms (none)
existing_automations: [welcome email (Mailchimp)]
tone: sıcak, net, esprili-değil · formality: sen
incentive_policy: max 10%, only last-step, needs approval
languages: [tr]
markets: [TR]
sector_answers: {consumables: yes, repeat_cycle: ~40 days}
assumptions: [audience sizes are user estimates]
```

## Persistence (brand config)

After intake completes, offer to write/update `${CLAUDE_PLUGIN_ROOT}/knowledge/brands/<brand-slug>.md` (from `knowledge/brands/_template.md`) so the answers persist across sessions — every field the template defines: `languages`, `markets`, `tone`, `formality`, `channels_live`, `incentive_policy` (incl. `clv_threshold`), `extra_banned_words`, `brand_vocabulary`, `existing_automations`, `product_rhythm`, and `verticals` when the company has genuinely separate product lines. On later sessions an existing brand file **pre-fills the Intake Summary** — only genuine gaps and stale fields get asked.

**`goal` is the one whitelist answer that is never silently reused.** It persists to the brand file as `default_goal` and pre-fills the question, but — unlike tone or incentive policy — it is always re-surfaced for explicit confirmation ("*son seferki hedefiniz retention'dı, aynı mı?*"), never silently carried over: a brand's active priority can shift between engagements (this quarter's growth push vs. last quarter's retention focus) in a way the rest of the config shouldn't. Same pre-fills-but-never-silently-replaces principle as the website-research and brand-voice-ingestion paths below.

## Brand voice ingestion (samples beat adjectives)

Users struggle to answer "describe your tone in 2-3 adjectives" but happily paste their 3 best-performing past messages. When they do: analyze the samples and **propose** the brand config's `tone`, `formality`, and `brand_vocabulary` values from them — then show the proposal for confirmation before writing `knowledge/brands/<brand>.md`. Same principle as T3 website research: ingestion pre-fills, it never silently replaces the user's say. Banned-word candidates spotted in the samples (words the brand clearly avoids) are suggested, not assumed.

## Never do

- Never ask what the data already answers (e.g. asking "do you have purchase tracking?" when GA4 shows `purchase`).
- Never re-ask a question the brand config file already answers, unless the user says it changed.
- Never ask open-ended essay questions ("tell me about your business") — every question is specific and defaultable.
- Never exceed 2 rounds or re-ask a defaulted question later in the session.

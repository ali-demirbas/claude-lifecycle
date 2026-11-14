---
name: lifecycle-journeys
argument-hint: "[P0|P0+P1|all]"
description: The journey engine. Generates a prioritized portfolio of lifecycle journeys from the DQS, stage map, industry playbook, and user goals — from 3-step simple flows to 10+ step branched flows. Use when the user says "journey üret", "generate journeys", "kampanya kur", "otomasyon tasarla", "journeys".
metadata:
  version: 0.3.0
  category: design
  updated: "2026-11-10"
---

# Lifecycle Journeys — Portfolio Engine

Generate a **portfolio** of journeys, not one-off ideas. The algorithm below is deterministic — follow it in order; do not freestyle.

## When NOT to use this

- **No DQS exists yet** — hard-blocked by CLAUDE.md rule 1; run `lifecycle-connect` (and `lifecycle-map`) first.
- **A working journey already exists and the request is to review it, not replace it** — that's `lifecycle-audit`.
- **Only copy is needed for a journey that's already designed** — invoke `lifecycle-copy` directly against the existing journey doc; regenerating the journey to get its copy is unnecessary fan-out.

## Prerequisites (hard gate)

- DQS + event inventory from `lifecycle-connect` (or explicit T3 declaration with an industry chosen).
- Stage map from `lifecycle-map` (T1/T2 only).
- Intake Summary from `lifecycle-intake` — if goal, existing automations, or channel inventory are unknown, trigger intake NOW, before generating.
- Brand config `output/brands/<brand>.md` if it exists (inheritance chain, CLAUDE.md rule 8), plus this brand's `output/<project>/failed-strategies.md` and results log if they exist.

## Single-journey path

When the user explicitly asks for one journey, build that journey only: no portfolio, no sweep over the other patterns, no breadth gate. It is a scope choice, not a shortcut: every check that makes the one journey correct still runs.
- **Eligibility for that pattern only:** `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/eligibility.py" output/<project>/stage-map.json --pattern <pattern>`. `unknown` reasons go to the journey's open items (it is a draft). `blocked` stops the request: show the missing events and the tracking-plan item, and offer the closest eligible pattern; never build a blocked pattern; never treat an event name alone as sufficient.
- **Consent per channel and purpose**, **exit conditions re-checked before each send**, **timeline, branches and frequency on every reachable path**, **measurement design and ready/draft**: exactly as in the full path (steps 3–4).
- **Overlap with what already runs:** write `portfolio.json` with `scope: "single"`, this journey, and the existing welcome series, campaigns and other automations **as the user stated them**; the validator adds them to this journey's load. If the existing load is unknown, record `external_journeys_status: unknown` and an open item, never zero; the journey can't be `ready` on that point.
- **Run bookkeeping:** `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/finalize_run.py" start output/<project> --scope <id> --mode single` before writing, `... finish output/<project> --max-discount <n> --sector <sector>` after. The dossier and the portfolio doc say in one line that portfolio coverage and other journeys' eligibility were **not reviewed**, and list the other patterns only if the user asks.

## The algorithm

### 1. Eligibility pass

The mechanical part runs as a script: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/eligibility.py" output/<project>/stage-map.json` prints each pattern as eligible / blocked / unknown / playbook-recommended from the frontmatter signatures and the stage map's confirmed, usable events. `unknown` P0/P1 patterns are still designed, as `readiness: draft` with each reason as an open item (confirm the event's meaning or its parameters); `blocked` ones go to the tracking plan. When the data assessment says `activation: unverified` or `reliability: degraded|unreliable`, every journey that depends on it is a draft with that reason as an open item. Read its output instead of re-deriving it; the judgment below (special cases, existing automations, data feeds, multi-vertical runs) applies on top of it.

**Multi-vertical brands** (brand config has `verticals` set): run this whole algorithm **once per vertical** — a pattern is eligible only if `applicable_industries` includes that vertical's own industry, checked against that vertical's own mapped events from `lifecycle-map`. Steps 1–4 below all run per vertical; step 5's conflict review does not (see its note).

For every pattern in `${CLAUDE_PLUGIN_ROOT}/knowledge/journey-patterns/` whose `applicable_industries` includes the active sector (that vertical's sector, for multi-vertical brands):

Special case: `account-onboarding` supersedes `welcome-onboarding` for B2B accounts when `account_id` + `user_role` exist and seats > 1 — the two never both run for the same account.
- Compare its `required_events` (frontmatter) against the mapped event set (aliases already resolved by lifecycle-map).
- All present → **eligible**. Any missing → **blocked**: record the missing events for the tracking plan. **Presence means usable, not just named:** a required event whose required params are mostly null (a `purchase` with 90% missing `value`) does not satisfy the signature — the event-analyst's parameter-completeness finding gates here, and a hollow event goes to the tracking plan as "instrumented but unusable".
- `optional_events` / `optional_attributes` present → note which depth upgrades/branches they unlock.
- T3 has no events, so nothing here is data-confirmed — calling it "eligible" the same way T1/T2 do overstates what's actually known. Every pattern the playbook marks P0/P1 is **playbook-recommended** in its **simple** form (assumed feasible from sector defaults, not confirmed by data — distinct from T1/T2's data-confirmed `eligible`); patterns needing live data feeds (back-in-stock, price-drop, replenishment) are **blocked** with reason "requires data feed". The full state model across tiers: `eligible` (T1/T2, signature matched against real data) / `playbook-recommended` (T3, unconfirmed) / `blocked` (signature missing or feed required) / `unknown` (classification couldn't be completed, e.g. an unmapped event stage). Downstream (breadth gate, portfolio doc), T3 rows are labeled `playbook-recommended`, never bare `eligible` — collapsing these into one shared label is the same honesty gap the DQS activation flag and freshness/consistency caps exist to close elsewhere in this pipeline.

### 2. Prioritization

Start from the playbook's `pattern_priorities` (that vertical's own playbook, for multi-vertical brands) (P0/P1/P2), then adjust with the intake goal — promote/demote at most one level, and say why:
- goal=revenue → promote revenue-stage patterns; goal=retention → promote retention/churn-prevention; goal=reactivation → promote winback/reactivation; goal=growth → promote referral/onboarding.
- Any pattern with an **existing automation** named in intake is checked for **coverage overlap**, not auto-deferred on a name match alone — "we have a welcome email" doesn't mean the existing automation covers what this pattern would design (a single `signup → email` send is not the same journey as `signup → profile completion → activation → education → handoff`, even though both would be called "welcome onboarding"):

  | Overlap | What it means | Portfolio treatment |
  |---|---|---|
  | **Equivalent** | Existing automation covers the same steps, channels, and triggers this pattern would design | `⏸ deferred — already running` |
  | **Substantial** | Existing automation covers most of the pattern's intent (same trigger, most of the sequence) with minor gaps | `⏸ deferred — already running`, one line naming the gap for a later revisit |
  | **Partial** | Existing automation covers only the opening move (a single send where the pattern's depth class supports more) | **Not deferred** — flagged as a **redesign/extend candidate**: the pattern proceeds through prioritization, and its journey doc notes what already exists so the output extends rather than duplicates it |
  | **None** | Named automation doesn't actually address this pattern's trigger/audience | Proceeds normally — the "existing automation" note doesn't apply to this pattern |

  Ask when the overlap class isn't clear from what intake captured — a one-line description ("we have a welcome email") is rarely enough to classify past `partial` vs `equivalent` on its own.
- A journey/strategy with a **powered failure in the failed-strategies log** for this audience is not re-proposed as-is; state which log entry caused the change (the log recommends, the user can overrule).

### 2a. Breadth gate (ask before generating)

**Skip this gate when the router's start message already settled breadth** (`skills/lifecycle/SKILL.md` step 2: P0 only / P0 + P1 / everything eligible). Apply that choice to the prioritized set and state the resulting count in one line; re-ask only if the eligible count differs materially from what the user expected when they chose. The gate below is for runs that reach this skill without a settled breadth (called directly, or the start message left breadth open).

Prioritization tells you how many journeys are eligible and at which priority — the user hasn't seen that number yet, and it is the single biggest cost multiplier of the whole run (one subagent per journey at generation, and one writer + one reviewer per journey again if copy follows). So before any doc generation, present the prioritized set as one short list (id · pattern · priority) and ask how much of it to build now:

- **(A) P0 only** — the minimum honest portfolio (exactly the Never-do floor below); fastest and cheapest. **P0 + P1 is the default** (the router's start message offers it) unless the user picks otherwise.
- **(B) P0 + P1** — medium scope.
- **(C) Everything eligible** — most complete, longest run, most tokens.

Deferred journeys are not dropped: they appear in the portfolio doc as `⏸ deferred by user scope` with one line each on what they would add — this satisfies the stage-coverage table's "explained gap" clause, and lets the user say "add the P1s" later without re-running eligibility. Skip the question when breadth is already settled (the router's start message, or the user said "sadece P0'lar" / "hepsini üret") or when the eligible set is ≤ 3 journeys total (the choice would be meaningless).

### 3. Depth assignment (adım sayısı — deterministic)

For each eligible journey take the pattern's `base_steps`, then (DQS below means that vertical's own DQS breakdown, for multi-vertical brands):

| Condition | Effect |
|---|---|
| DQS ≥ 70 AND pattern has unlocked branch events | depth class **branched**: steps = base × 1.5–2, capped at pattern `depth_range` max; add branch conditions |
| DQS 40–69 | depth class **standard**: steps = base ± 1, one engagement or product-event branch max (never an email open) |
| DQS < 40 or T3 | depth class **simple**: steps = pattern `depth_range` min (3–5 typical), time-based waits only, single channel + one support channel |
| **Volume component ≤ 5** (under ~100 conversions/mo) | statistical branches (A/B splits, experiments) capped at **standard** regardless of total DQS — a split that can never reach measurement power is a designed failure (DQS hard rule 4); operational branches (a payment-failure reason, a delivery state) are not volume-gated |
| **Freshness gate triggered** (the relevant feed is staler than its own expected update cadence; the sector's `churn_signal` window, then 60d, only as fallbacks) | depth class capped at **standard** regardless of total DQS — journeys built on stale signal don't reflect current behavior (DQS hard rule 5) |
| **Consistency gate triggered** (primary conversion event has a silent gap past a third of the freshness threshold, or 14d fallback) | depth class capped at **standard** regardless of total DQS — component scores computed from an interrupted tracking period aren't trustworthy at face value (DQS hard rule 6) |
| Informational patterns (frontmatter shows depth does not scale) | keep 1–3 steps regardless of DQS |
| Only one consented channel exists | single-channel regardless of class; note the limitation |

Step counts mean **sends on the longest path** through the graph (mutually exclusive branches are not added together); the validator checks that number against the pattern's `depth_range`. The class is a **ceiling, not a quota**: build shallower whenever the pattern or audience calls for it — informational patterns already stay short by design, and nothing obliges a healthy post-purchase to inflate to its maximum.

The pattern file's "Depth scaling" section overrides this table where more specific.

### 4. Generate journey docs

For each journey (portfolio order), produce two artifacts from the same design decisions: `output/<project>/<id>.json` (schema 2.0, `templates/journey.schema.json`) and `output/<project>/<id>.md` (`templates/journey-doc.md`). The JSON is authoritative; the doc's §5 table and §8 diagram are generated from it with `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/journey_render.py" <id>.json`.

**Schema 2.0 in one paragraph.** The journey is a node graph (`start` + `nodes`): one `entry`, `message` sends, `decision` nodes, `exit` nodes, linked by id. Every send states **when** with an explicit anchor: journey entry, a named earlier node, or an event/attribute date (`trial_end`, `renewal_date`) whose relation to entry is declared in `time_anchors`; calendar times carry a timezone. A decision reads one signal (`event`, bot-filtered `click`, or `attribute`, with its source) inside a window and routes `occurred`, `not_occurred` and `unmeasurable` separately; an email open is never a branching signal. Exit conditions (the success event, consent withdrawal, pattern-specific stops) are re-checked **before each send**. `reentry` states the policy and what a repeated trigger does while an instance is active. `measurement` states the design (holdout or why not, plus the alternative). Since the external review, the schema also carries: `readiness` + `open_items` (a draft stays a draft when the file is reopened), `instance_key` with same-instance and channel-scoped exits, composite `any_of`/`all_of` signals, `delivery` (in-app at next session with an expiry; deadlines on hard-date notices), date `range`s in `time_anchors`, and non-negative elapsed durations. Use the pattern's blueprint as the skeleton: it is already written in these terms.

**Delegation.** Each journey is designed by one `journey-architect` agent; launch independent journeys **concurrently in a single message**. Give each agent a file to read, not pasted text:
1. Build its context bundle with a script (no model tokens): `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bundle_context.py" --pattern <pattern> --sector <sector> [--brand <brand>] --out output/<project>/_bundle/<id>.md`. It contains only what one journey needs (its pattern, the playbook, lexicon, brand config, consent/frequency rules, segmentation, measurement, the template, the schema), never the whole knowledge base.
2. The prompt carries the bundle path plus the resolved facts as short stated lines: id, DQS + depth class, confirmed channel inventory (and withdrawn channels), incentive policy (`max_discount_pct`, or "none stated": then no incentive step), `events_available` from the stage map, existing automations relevant to this journey, audience size and monthly conversions (unknown → `none_low_volume` with an open item, never a holdout sized on a guess), market timezone, any pause or precedence rule the conflict review already set for this journey's audience, the output paths.
3. The agent writes `<id>.json` and `<id>.md` itself, runs the validator on its own JSON, and returns a **receipt**, not the documents: paths, a two-line summary, the validator result line, and unresolved issues. Do not re-type or re-generate a returned document; read only the fields you need (e.g. the receipt's validation line, or a specific section when assembling the portfolio).
4. Fix loop limit: an agent fixes its own validation errors at most twice. If the same error survives, it stops and reports the diagnosis (which rule, which node, what it tried) instead of looping; record that in the dossier as unresolved. A journey that still fails is not presented as finished.

If a journey is written without delegation (a single small journey), the same rules hold: write both files, render §5/§8, validate before moving on.

### 5. Portfolio assembly & conflict review

**Multi-vertical brands:** stage coverage is per vertical (a blind stage in one product line isn't offset by coverage in another). Conflict review — worst-case weekly message count, precedence order, entry gate — is the opposite: computed **once, across the whole portfolio, all verticals combined**, against the same per-user compliance caps. A user eligible for journeys in two verticals at once is still one person receiving one inbox's worth of messages; vertical boundaries are an internal planning split, not an exemption from frequency caps. Declare cross-vertical audience overlaps in `audience_overlaps` exactly as any other overlap.

Fill `${CLAUDE_PLUGIN_ROOT}/templates/journey-portfolio.md`. The **contact policy** below (precedence order, concurrent-journey cap, entry gate, re-entry cooldown) is the portfolio's arbitration layer: when a user qualifies for several journeys, it decides who sends and who defers. Frequency numbers are never estimated by hand: the validator computes each journey's worst-path load per rolling 7 days from its node graph and sums the journeys a user can be in at once.
- Stage coverage table: every stage with events gets ≥ 1 journey or an explained gap. Blind stages from lifecycle-map are reported as gaps with their unblocking events.
- Conflict review: shared triggers/audiences, worst-case weekly message count vs the caps in `knowledge/compliance/consent-and-quiet-hours.md`. A breach the validator reports is a compliance stop (CLAUDE.md rule 12): report it with the numbers, propose the fix (merge or drop a step, a pause/precedence rule, `frequency_policy.on_breach`), and apply it only after the user agrees; in a non-interactive run, deliver the affected journeys as drafts with the breach as an open item. Never cut steps silently and present the result as passed.
- **Temporal dimension:** when intake/brand config declares campaign windows, apply `knowledge/calendar-rules.md` — each journey's in-window behavior class (never-pauses / incentive-suppressed / pauses / judgment) is stated in the portfolio, and campaign-week worst case includes the declared campaign sends against the same caps. No declared windows → one portfolio line says campaign behavior is undeclared.
- The worst case is computed per audience group **and per declared overlap combo** — a real user sits in several groups at once (a new signup who abandons a cart in the same week), and per-group sums alone silently approve that violation. Declare the overlapping combos in the registry's `audience_overlaps`; if the merged worst case breaches a cap, the fix is a pause/precedence rule (e.g. welcome pauses while cart recovery runs), written into both journeys' docs.
- **Contact Policy (arbitration layer):** the precedence order, concurrent-journey cap, and entry gate below together ARE the portfolio's contact policy. The answer to "a user qualifies for journeys A, B, and C in the same window — who actually sends?" is never "sum the theoretical worst case and hope it's under cap" — it's "apply this policy, admit the winner, defer/suppress the rest." State it that way when presenting conflict review, not as three separate rules a reader has to connect themselves.
- **Precedence order** — when one user qualifies for multiple journeys simultaneously, this default ranking decides who messages first (deviations are stated, never silent):
  1. Negative-signal suppression (compliance rule 4) beats everything.
  2. Transactional/protect flows (payment-failure dunning).
     Service notices owed to the customer (renewal-reminder's contractual notices, cancellation-winddown) sit with this tier: marketing defers to them, never the reverse. On one `renewal_date` (insurance), renewal-reminder owns the renewal clock; churn-prevention runs only as the save path for at-risk policies and defers to renewal-reminder (knowledge/industries/insurance.md).
  3. Short-window recovery (abandoned-cart, trial-conversion) — the shortest useful window of any journey; delayed entry loses the recoverable intent.
  4. Churn-prevention / winback (mutually exclusive with each other via the watch buffer).
  5. Welcome/activation for pre-activation users.
  6. Reinforcement asks: loyalty, milestone, referral, feedback.
  7. Progressive-profiling — never blocks anything, always lowest.
- **Concurrent-journey cap:** beyond message-volume caps, no more than 2 non-transactional journeys may be simultaneously active for one user (tier 2 of the precedence order above — transactional/protect flows — is exempt; those aren't discretionary marketing). This guards narrative coherence, not just inbox volume: a user technically under every frequency cap can still be getting pulled into 3-4 unrelated asks the same week. When a user would exceed the cap, the precedence order above decides which journey stays active and which defers — same ranking, applied to a new trigger.
- **Entry gate:** before admitting a user to a new journey, check whether a higher-priority journey messaged them within a lookback window (default 48h); if so, delay entry or open on a low-intrusion channel (in-app) instead of the normal opener. **Same-window tie:** when two or more journeys become eligible for the same user in the same cycle and *neither* has sent yet, there's no lookback signal to check — apply the precedence order directly instead: admit only the highest-ranked journey, defer the rest as if the higher one had already messaged. A cart-abandonment + price-drop + churn-prevention + campaign-audience overlap landing on the same day is this case, not the lookback case, and the two must not be conflated.
- **Re-entry cooldown** (distinct from the entry gate above — that one checks *other* journeys, this checks the *same* one): after a user exits a pattern, good or bad exit, that same pattern may not re-trigger for them until a cooldown passes — the pattern's own `reentry` (its cooldown, or `each_trigger` for per-instance patterns such as payment-failure, post-purchase or renewal, which are never delayed: a second failed invoice gets its own dunning), or 14 days minimum only when the pattern states no reentry at all. Without this, a user oscillating near a threshold (e.g. health score dipping in and out of the churn-prevention trigger) can be re-entered into the same journey repeatedly; each run is individually well-formed, but the user experiences it as relentless.
- **Incremental additions:** when adding journeys to an EXISTING portfolio, the full conflict review (precedence, entry gate, worst-case cap math) is recomputed over the whole portfolio — never just the new journey — and the portfolio doc is re-issued, not appended.
- **Channel economics within a sequence:** escalate by reachability and justification, not by a fixed order: in-app only for people who are active in the product, push only where push.md's suitability test passes, SMS only where sms.md's tests pass; never rotate channels because of opens (opens are not a signal). In branched journeys, never the same channel more than 2–3 consecutive steps.

### 6. Tracking plan

If anything was blocked or a depth upgrade was missed, instantiate `${CLAUDE_PLUGIN_ROOT}/templates/tracking-plan.md`, ranked by unlocked value (blocked P0 > blocked P1 > depth upgrades).

## Output order

Bookkeeping is code, not turns: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/finalize_run.py" start output/<project> --scope <ids> --mode portfolio|single` at the start (archives the previous run with its manifest, opens a new run id), and `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/finalize_run.py" finish output/<project> --max-discount <n> [--sector <s>]` at the end. `finish` renders the mechanical doc sections from each journey JSON, refreshes the registry's mechanical fields (keeping the audience groups, overlaps, existing journeys and breach policy you wrote), validates everything, builds the canvas only when nothing failed, and writes `run-manifest.json` with hashes. It never edits a journey's design. Present its status line: `passed`, `unverified` (drafts or unverifiable items, listed) or `failed` (no canvas; report and stop).

1. Portfolio doc → 2. journey docs (P0 first) → 3. tracking plan → 4. **HTML canvas (THE default deliverable):** write `output/<project>/_meta.json` first, in the user's language: `{"title", "eyebrow", "h1", "lede", "holdout_tip", "data_note", "lang"}`, all plain text (`lang`: `tr` or `en`; it sets the canvas interface language) (`holdout_tip` may also be `{"title": "…", "body": "…"}`); the lede states the journey count. Never leave the tooltips empty: they replace the template's sample text. `finalize_run.py finish` then builds `canvas.html` from the journey JSONs with `build_canvas.py` (template copied, only the swappable regions substituted, self-verified; branches and merges come from the schema-2.0 graph). Don't build the canvas by hand and don't run `build_canvas.py` separately unless `finish` is unavailable. **Canvas text rule:** the lede, segment/amaç/metric lines, and card texts are written in plain language a marketer reads in one pass — no DQS/holdout/"unmeasured"-style jargon in headline text; methodological caveats go into tooltips, phrased plainly. Copy is a separate deliverable: generate it when the start message settled the scope as "journeys + copy"; otherwise ask once ("run `/lifecycle copy` for these?"), and in a non-interactive run leave it out and say so.

Write everything to `output/<project>/` locally (gitignored) — including **`portfolio.json`**, the machine-readable registry, valid against `templates/portfolio.schema.json` (`schema_version: "2.0"`; `brand` or `project`; `allowed_channels`: the channels the brand can send on and users consented to; `frequency_policy: {window: "P7D", on_breach: defer|skip|priority}`; `events_available` from the stage map; existing journeys the user reported as `external_journeys_status: declared|none_reported|unknown` with `external_journeys: [{name, audience_groups, msgs: {channel: n} or null, window: "P7D"}]`, with the counts **exactly as the user stated them** — never invented, and never lowered to account for a pause or precedence rule (a pause doesn't stop both of a series' weekly messages from landing in the same rolling 7 days as the new journey's; if the combined load breaches a cap, that is a finding to resolve with `frequency_policy`, not a number to adjust); and per journey: id, `file` (its JSON, so load is computed from sends), pattern, stage, priority, channels, `audience_group`, `est_msgs_per_week` — **a per-CHANNEL dict, e.g. `{"email": 2, "push": 1}`, never a bare total** (validate_output.py checks each channel against its cap and rejects any other shape); plus top-level `audience_overlaps: [[groupA, groupB], ...]` naming every group combination one real user can occupy at once, and — when campaign windows are declared — top-level `campaign_msgs_per_week: {channel: n}` so the validator re-checks every group against the caps WITH the campaign load added (calendar-rules.md's math, enforced in code); plus top-level `blocked: [{pattern, reason}]` for every blocked pattern and `suppressed_accounts: []` for negative-signal suppression — the eval checker reads these) — and present the HTML canvas plus a short summary in the conversation. Keep `output/<project>/run-manifest.json` for the run: a unique run id (timestamp to the second plus a short random suffix, so two runs in the same minute can't collide), the journey ids in scope with each file's path, sha256, `readiness` and validator result, and the validator/schema versions. Downstream steps (copy merge, canvas, export) read the manifest, not whatever files sit in the folder. When a run is archived (below), its manifest and the files it lists move with the dossier, so an older run can be re-inspected as it was. Write `output/<project>/dossier.md` from `templates/run-dossier.md` before `finish` (see the validation gate; refresh it after copy when copy runs) — the dossier and canvases are the user-facing set; the JSONs are machine-facing and are never presented as deliverables (export is a separate, explicitly-requested stage). Archiving the previous run (its dossier, manifest, canvas and listed files, into `runs/<old-run-id>/`) is done by `finalize_run.py start`; the new dossier's §1a references the archived run id, and is omitted on a brand's first run.

**If the canvas can't be built** (build_canvas refuses an invalid journey, or the canvas check fails), the validated JSON and markdown remain the deliverable: present those, say the canvas failed and why, and don't call the canvas done. Don't spend a debugging loop on it inside the run.

**Validation gate (before presenting anything):** write `dossier.md` (from `templates/run-dossier.md`) **before** running `finalize_run.py finish`, so the dossier is code-validated and hashed into the manifest like every other delivered file; `finish` runs every validator mode on the run's files. **Always pass `--max-discount <brand's incentive_policy.max_discount_pct>` and `--sector <sector>`** to `finish`: without them the discount-ceiling and sector banned-word checks on copy silently don't run. After `finish`, paste its status line and validator summary into dossier §4a (the only post-finish edit; it changes no checked content). A compliance-class FAIL is a hard stop: report it and wait. Exit 3 (unverifiable items or drafts) is presented only with the list, labelled unverified.

## Common Pitfalls

Each of these was chosen because it passes every check above while still being wrong — the checklist confirms structure, not judgment. Read a finished portfolio against these before presenting it.

**Pitfall 1: Flat depth across the whole portfolio.**
Symptom: every journey lands at 5-7 steps, "standard," regardless of pattern or DQS.
Consequence: informational patterns bloat past their natural 1-3 steps, and thin-data journeys carry branches the volume/freshness/consistency gates should have capped.
Fix: re-run step 3's table per journey, not once for the portfolio — depth class is per-journey, not a portfolio default.

**Pitfall 2: A one-note portfolio.**
Symptom: everything eligible happens to be a recovery pattern — abandoned-cart, churn-prevention, winback — and the portfolio ships as-is.
Consequence: CLAUDE.md rule 2 calls this out directly as an incomplete deliverable; stopping at what's broken and never building on what's healthy leaves growth-stage value (post-purchase, referral, upsell) unclaimed for no data reason, only a framing one.
Fix: check the stage-coverage table before finalizing — a portfolio that is 100% leak-recovery with zero growth-stage journeys is a signal to look again at eligibility, not a valid result to ship.

**Pitfall 3: Conflict math asserted, not computed.**
Symptom: the portfolio doc says "channels are staggered to avoid overload" or "well within frequency limits" with no worst-case number attached.
Consequence: this is precisely the compliance-risk surface step 5 exists to close — an unverified sentence there is worse than an unverified sentence anywhere else in the doc, because it looks like the check ran.
Fix: every conflict-review claim traces to an actual number computed per audience group and per declared overlap combo, checked against `knowledge/compliance/consent-and-quiet-hours.md` — a claim with no number behind it is a missing step, not a finished one.

## Never do

- Never generate a journey whose pattern is blocked — no "we'll pretend the event exists".
- Never produce an ad-hoc journey format — the template is mandatory (CLAUDE.md rule 2).
- Never exceed frequency caps in aggregate and leave it as a "note".
- In a portfolio run, never generate fewer journeys than the eligible P0 set, or pad the portfolio with P2 filler the goal doesn't support. (The single-journey path is the explicit exception, and says so in its output.)
- Never invent event volumes or benchmark numbers for the KPI targets — "baseline after 4 weeks" is the honest default.
- Never assume the channel set. Every step's channel comes from the confirmed channel inventory (intake / brand config `channels_live` / confirmed T1 data), never a hardcoded default — if the inventory is unknown, trigger intake before generating, don't guess email/push/in-app.

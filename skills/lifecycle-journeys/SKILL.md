---
name: lifecycle-journeys
description: The journey engine. Generates a prioritized portfolio of lifecycle journeys from the DQS, stage map, industry playbook, and user goals — from 3-step simple flows to 10+ step branched flows. Use when the user says "journey üret", "generate journeys", "kampanya kur", "otomasyon tasarla", "journeys".
---

# Lifecycle Journeys — Portfolio Engine

Generate a **portfolio** of journeys, not one-off ideas. The algorithm below is deterministic — follow it in order; do not freestyle.

## Prerequisites (hard gate)

- DQS + event inventory from `lifecycle-connect` (or explicit T3 declaration with an industry chosen).
- Stage map from `lifecycle-map` (T1/T2 only).
- Intake Summary from `lifecycle-intake` — if goal, existing automations, or channel inventory are unknown, trigger intake NOW, before generating.
- Brand config `${CLAUDE_PLUGIN_ROOT}/knowledge/brands/<brand>.md` if it exists (inheritance chain, CLAUDE.md rule 8), plus this brand's `output/<brand>/failed-strategies.md` and results log if they exist.

## The algorithm

### 1. Eligibility pass

**Multi-vertical brands** (brand config has `verticals` set): run this whole algorithm **once per vertical** — a pattern is eligible only if `applicable_industries` includes that vertical's own industry, checked against that vertical's own mapped events from `lifecycle-map`. Steps 1–4 below all run per vertical; step 5's conflict review does not (see its note).

For every pattern in `${CLAUDE_PLUGIN_ROOT}/knowledge/journey-patterns/` whose `applicable_industries` includes the active sector (that vertical's sector, for multi-vertical brands):

Special case: `account-onboarding` supersedes `welcome-onboarding` for B2B accounts when `account_id` + `user_role` exist and seats > 1 — the two never both run for the same account.
- Compare its `required_events` (frontmatter) against the mapped event set (aliases already resolved by lifecycle-map).
- All present → **eligible**. Any missing → **blocked**: record the missing events for the tracking plan. **Presence means usable, not just named:** a required event whose required params are mostly null (a `purchase` with 90% missing `value`) does not satisfy the signature — the event-analyst's parameter-completeness finding gates here, and a hollow event goes to the tracking plan as "instrumented but unusable".
- `optional_events` / `optional_attributes` present → note which depth upgrades/branches they unlock.
- T3 has no events: every pattern the playbook marks P0/P1 is eligible in its **simple** form; patterns needing live data feeds (back-in-stock, price-drop, replenishment) are blocked with reason "requires data feed".

### 2. Prioritization

Start from the playbook's `pattern_priorities` (that vertical's own playbook, for multi-vertical brands) (P0/P1/P2), then adjust with the intake goal — promote/demote at most one level, and say why:
- goal=revenue → promote revenue-stage patterns; goal=retention → promote retention/churn-prevention; goal=reactivation → promote winback/reactivation; goal=growth → promote referral/onboarding.
- Any pattern matching an **existing automation** from intake is demoted to "⏸ deferred — already running" unless the user asked to redesign it.
- A journey/strategy with a **powered failure in the failed-strategies log** for this audience is not re-proposed as-is; state which log entry caused the change (the log recommends, the user can overrule).

### 2a. Breadth gate (ask before generating)

Prioritization tells you how many journeys are eligible and at which priority — the user hasn't seen that number yet, and it is the single biggest cost multiplier of the whole run (one subagent per journey at generation, and one writer + one reviewer per journey again if copy follows). So before any doc generation, present the prioritized set as one short list (id · pattern · priority) and ask how much of it to build now:

- **(A) P0 only** — the minimum honest portfolio (exactly the Never-do floor below); fastest and cheapest, recommended starting point.
- **(B) P0 + P1** — medium scope.
- **(C) Everything eligible** — most complete, longest run, most tokens.

Deferred journeys are not dropped: they appear in the portfolio doc as `⏸ deferred by user scope` with one line each on what they would add — this satisfies the stage-coverage table's "explained gap" clause, and lets the user say "add the P1s" later without re-running eligibility. Skip the question only when the user already stated breadth ("sadece P0'lar", "hepsini üret") or when the eligible set is ≤ 3 journeys total (the choice would be meaningless).

### 3. Depth assignment (adım sayısı — deterministic)

For each eligible journey take the pattern's `base_steps`, then (DQS below means that vertical's own DQS breakdown, for multi-vertical brands):

| Condition | Effect |
|---|---|
| DQS ≥ 70 AND pattern has unlocked branch events | depth class **branched**: steps = base × 1.5–2, capped at pattern `depth_range` max; add branch conditions |
| DQS 40–69 | depth class **standard**: steps = base ± 1, one open/click branch max |
| DQS < 40 or T3 | depth class **simple**: steps = pattern `depth_range` min (3–5 typical), time-based waits only, single channel + one support channel |
| **Volume component ≤ 5** (under ~100 conversions/mo) | depth class capped at **standard** regardless of total DQS — a branch that can never reach measurement power is a designed failure (DQS hard rule 4) |
| **Freshness gate triggered** (most recent event older than the sector's `churn_signal` window, or 60d fallback) | depth class capped at **standard** regardless of total DQS — journeys built on stale signal don't reflect current behavior (DQS hard rule 5) |
| **Consistency gate triggered** (primary conversion event has a silent gap past a third of the freshness threshold, or 14d fallback) | depth class capped at **standard** regardless of total DQS — component scores computed from an interrupted tracking period aren't trustworthy at face value (DQS hard rule 6) |
| Informational patterns (frontmatter shows depth does not scale) | keep 1–3 steps regardless of DQS |
| Only one consented channel exists | single-channel regardless of class; note the limitation |

The class is a **ceiling, not a quota**: build shallower whenever the pattern or audience calls for it — informational patterns already stay short by design, and nothing obliges a healthy post-purchase to inflate to its maximum.

The pattern file's "Depth scaling" section overrides this table where more specific.

### 4. Generate journey docs

For each journey (portfolio order), instantiate `${CLAUDE_PLUGIN_ROOT}/templates/journey-doc.md` — every required section. Use the pattern's step blueprint as the skeleton; adapt timing/channels to the playbook's "timing & cadence" section and intake's channel inventory. For deep dives on P0 journeys, optionally delegate to the `journey-architect` agent (one journey per agent) — and launch the agents for independent journeys **concurrently in a single message**, never one after another; journey docs don't depend on each other, and serializing them is the pipeline's second-largest time cost.

**The markdown doc is not the only artifact this step produces.** Emit the matching `<id>.json` (against `journey.schema.json`) from the *same* design decisions in the same pass — same steps (wait/channel/branch_condition), same kpis, same trigger/audience/exit, same `depth_class`, same `vertical` for multi-vertical brands — never author the JSON as an afterthought derived by re-reading the markdown later, and never let a markdown edit happen without the JSON edit alongside it. Run `python3 scripts/validate_output.py journey <id>.json` as soon as it's written, not batched to the end — a schema violation caught per-journey is a one-line fix; the same violation caught at the final all-mode gate (step 5) after every journey is written is a much larger rework. For multi-vertical brands, also carry each journey's `vertical` into its `portfolio.json` entry (step 5) — the registry has no other way to record it.

### 5. Portfolio assembly & conflict review

**Multi-vertical brands:** stage coverage is per vertical (a blind stage in one product line isn't offset by coverage in another). Conflict review — worst-case weekly message count, precedence order, entry gate — is the opposite: computed **once, across the whole portfolio, all verticals combined**, against the same per-user compliance caps. A user eligible for journeys in two verticals at once is still one person receiving one inbox's worth of messages; vertical boundaries are an internal planning split, not an exemption from frequency caps. Declare cross-vertical audience overlaps in `audience_overlaps` exactly as any other overlap.

Fill `${CLAUDE_PLUGIN_ROOT}/templates/journey-portfolio.md`:
- Stage coverage table: every stage with events gets ≥ 1 journey or an explained gap. Blind stages from lifecycle-map are reported as gaps with their unblocking events.
- Conflict review: shared triggers/audiences, worst-case weekly message count vs the caps in `knowledge/compliance/consent-and-quiet-hours.md`. If over cap, cut or merge steps — do not just flag.
- **Temporal dimension:** when intake/brand config declares campaign windows, apply `knowledge/calendar-rules.md` — each journey's in-window behavior class (never-pauses / incentive-suppressed / pauses / judgment) is stated in the portfolio, and campaign-week worst case includes the declared campaign sends against the same caps. No declared windows → one portfolio line says campaign behavior is undeclared.
- The worst case is computed per audience group **and per declared overlap combo** — a real user sits in several groups at once (a new signup who abandons a cart in the same week), and per-group sums alone silently approve that violation. Declare the overlapping combos in the registry's `audience_overlaps`; if the merged worst case breaches a cap, the fix is a pause/precedence rule (e.g. welcome pauses while cart recovery runs), written into both journeys' docs.
- **Precedence order** — when one user qualifies for multiple journeys simultaneously, this default ranking decides who messages first (deviations are stated, never silent):
  1. Negative-signal suppression (compliance rule 4) beats everything.
  2. Transactional/protect flows (payment-failure dunning).
  3. Short-window recovery (abandoned-cart, trial-conversion) — the shortest useful window of any journey; delayed entry loses the recoverable intent.
  4. Churn-prevention / winback (mutually exclusive with each other via the watch buffer).
  5. Welcome/activation for pre-activation users.
  6. Reinforcement asks: loyalty, milestone, referral, feedback.
  7. Progressive-profiling — never blocks anything, always lowest.
- **Concurrent-journey cap:** beyond message-volume caps, no more than 2 non-transactional journeys may be simultaneously active for one user (tier 2 of the precedence order above — transactional/protect flows — is exempt; those aren't discretionary marketing). This guards narrative coherence, not just inbox volume: a user technically under every frequency cap can still be getting pulled into 3-4 unrelated asks the same week. When a user would exceed the cap, the precedence order above decides which journey stays active and which defers — same ranking, applied to a new trigger.
- **Entry gate:** before admitting a user to a new journey, check whether a higher-priority journey messaged them within a lookback window (default 48h); if so, delay entry or open on a low-intrusion channel (in-app) instead of the normal opener.
- **Re-entry cooldown** (distinct from the entry gate above — that one checks *other* journeys, this checks the *same* one): after a user exits a pattern, good or bad exit, that same pattern may not re-trigger for them until a cooldown passes — the pattern's own typical duration, or 14 days minimum if the pattern has no stated duration. Without this, a user oscillating near a threshold (e.g. health score dipping in and out of the churn-prevention trigger) can be re-entered into the same journey repeatedly; each run is individually well-formed, but the user experiences it as relentless.
- **Incremental additions:** when adding journeys to an EXISTING portfolio, the full conflict review (precedence, entry gate, worst-case cap math) is recomputed over the whole portfolio — never just the new journey — and the portfolio doc is re-issued, not appended.
- **Channel economics within a sequence:** escalate cheap→expensive (in-app → push → email → SMS) as justification grows — opening a winback with SMS spends the most expensive channel before cheaper ones had a chance. In branched (7–12 step) journeys, never the same channel more than 2–3 consecutive steps; several consecutive no-opens on one channel → rotate the channel before rotating the message. Where per-user interaction-history exists, waits may calibrate to the user's own rhythm (a daily user tolerates faster escalation than a monthly one); otherwise use the pattern's static windows and say so.

### 6. Tracking plan

If anything was blocked or a depth upgrade was missed, instantiate `${CLAUDE_PLUGIN_ROOT}/templates/tracking-plan.md`, ranked by unlocked value (blocked P0 > blocked P1 > depth upgrades).

## Output order

1. Portfolio doc → 2. journey docs (P0 first) → 3. tracking plan → 4. **HTML canvas (THE default deliverable):** render the portfolio as `canvas.html` by **copying** `${CLAUDE_PLUGIN_ROOT}/templates/canvas.html` (file copy, then edit only the swappable parts in place — never retype the boilerplate) — only the `JOURNEYS` data array, header texts, and `HOLDOUT_TIP`/`DATA_NOTE` change; the design never does. This single file (tabs + meta + tree canvas + print view) is what the user reviews and shares; the markdown docs are the source of truth behind it. **Canvas text rule:** the lede, segment/amaç/metric lines, and card texts are written in plain language a marketer reads in one pass — no DQS/holdout/"unmeasured"-style jargon in headline text; methodological caveats go into tooltips, phrased plainly. Ask before generating copy ("run `/lifecycle copy` for these?") — copy is a separate deliverable.

Write everything to `output/<project>/` locally (gitignored) — including **`portfolio.json`**, the machine-readable registry (id, pattern, stage, priority, channels, `audience_group`, `est_msgs_per_week` per journey — **a per-CHANNEL dict, e.g. `{"email": 2, "push": 1}`, never a bare total** (validate_output.py checks each channel against its cap and rejects any other shape); plus top-level `audience_overlaps: [[groupA, groupB], ...]` naming every group combination one real user can occupy at once, and — when campaign windows are declared — top-level `campaign_msgs_per_week: {channel: n}` so the validator re-checks every group against the caps WITH the campaign load added (calendar-rules.md's math, enforced in code); plus top-level `blocked: [{pattern, reason}]` for every blocked pattern and `suppressed_accounts: []` for negative-signal suppression — eval and validator tooling reads these) — and present the HTML canvas plus a short summary in the conversation. End every run with `output/<project>/dossier.md` from `templates/run-dossier.md` (refresh it after copy when copy runs) — the dossier and canvases are the user-facing set; the JSONs are machine-facing and are never presented as deliverables (export is a separate, explicitly-requested stage). **Before writing the new dossier, check whether `output/<project>/dossier.md` already exists from a prior run.** If it does, read its Run ID and headline facts (DQS, journey count), move the file to `output/<project>/runs/dossier-<old-run-id>.md` (create the `runs/` folder if needed), then write the new dossier with a fresh Run ID and a filled-in §1a referencing the archived one. Never silently overwrite a prior dossier with no trace of it — that destroys the one audit trail a later root-cause question (why did journey X look like this three runs ago?) would need. If no prior dossier exists, this is the brand's first run: §1a is omitted entirely, not left as an empty section.

**Validation gate (before presenting anything):** run `python3 scripts/validate_output.py all output/<project>/ --max-discount <brand's incentive_policy.max_discount_pct>` — **always pass `--max-discount`**, even in `all` mode: omitting it silently disables the discount-ceiling check on every copy doc found. Journey JSONs are checked against the schema and their embedded `constraints`; the portfolio registry's frequency-cap math is recomputed in code. A compliance-class failure (unconsented channel, discount over cap, frequency breach) is a hard stop — report the violation and wait for the user; never silently fix and ship (CLAUDE.md rule 12).

## Never do

- Never generate a journey whose pattern is blocked — no "we'll pretend the event exists".
- Never produce an ad-hoc journey format — the template is mandatory (CLAUDE.md rule 2).
- Never exceed frequency caps in aggregate and leave it as a "note".
- Never generate fewer journeys than the eligible P0 set, or pad the portfolio with P2 filler the goal doesn't support.
- Never invent event volumes or benchmark numbers for the KPI targets — "baseline after 4 weeks" is the honest default.

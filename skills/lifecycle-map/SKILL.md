---
name: lifecycle-map
description: Map tracked events to lifecycle stages (acquisition/activation/engagement/revenue/retention/winback) and derive the funnel skeleton. Use after lifecycle-connect, or when the user says "map my events", "event haritala", "funnel çıkar", "hangi stage'ler eksik".
---

# Lifecycle Map — Event → Stage Mapping

Turn the event inventory from `lifecycle-connect` into a stage map and funnel skeleton. This is what makes journey eligibility computable.

## Procedure

0. **If `knowledge/brands/<brand>.md` has `verticals` set:** tag every event to a vertical via `event_prefix` match first — mechanical name-prefix matching, done before any stage classification. This determines which industry playbook's funnel table and "Event expectations" apply to that event in step 1. An event matching no vertical's prefix falls back to the primary industry, flagged `unclassified-vertical` — batch it into the same question as unmappable events (step 3).
1. **First, check for a prior pass:** if `output/<project>/event-analysis.json` exists (written when `lifecycle-connect` spawned `event-analyst` for a 50+ event inventory earlier in this same run), its Mapped/Assumed/Unmapped classification is a draft, not a discard-and-redo — confirm or override it below rather than reclassifying every event from zero. Two independent classification passes over the same event risk landing on two different stages for it — treating the first pass as the starting point removes that risk instead of hoping both agree. Absent the file (inventories under 50 events, classified inline by `lifecycle-connect` itself, or no prior connect run), load the mapping sources fresh, in lookup order:
   - `${CLAUDE_PLUGIN_ROOT}/knowledge/event-taxonomy/ga4-recommended-events.md` (exact + alias lookup)
   - the active industry playbook's funnel table (the event's own vertical's playbook, for multi-vertical brands)
   - `${CLAUDE_PLUGIN_ROOT}/knowledge/event-taxonomy/stage-mapping-rules.md` (heuristics for unknowns — apply its rules 1→5 in order)
2. Classify every event from the inventory. Track WHICH rule classified each one.
3. Batch unmappable events into a single question to the user (max 10, best-guess pre-filled). Continue with what is mapped; mark dependent outputs provisional.
4. Build the funnel skeleton: order the mapped events along the industry playbook's canonical funnel (one skeleton per vertical, for multi-vertical brands); note observed drop-off between steps if T1 volumes exist — and flag, don't silently build past, any step whose volume **exceeds** the previous step's. An inverted funnel means a mapping error or a data-integrity problem, not real user behavior; report it as a finding rather than presenting the funnel as if the numbers were trustworthy.

## Output (exactly the contract from stage-mapping-rules.md)

1. **Mapped table** — event | vertical (multi-vertical brands only) | stage | source rule | 90-day volume (if known).
2. **Assumed mappings** needing user confirmation (aliases + medium-confidence heuristics).
3. **Unmapped events** — asked or pending, including any `unclassified-vertical` events.
4. **Stage coverage summary** — six stages, events per stage, and the **blind stages** (zero events) called out explicitly. Blind stages are a first-class finding: they directly limit the journey portfolio. One summary per vertical for multi-vertical brands — a blind stage in one product line shouldn't be hidden by coverage in another.
5. **Funnel skeleton** — ordered steps with events, plus a Mermaid `flowchart LR` of the funnel. One funnel per vertical for multi-vertical brands.

## Never do

- Never silently guess a stage for an event that fails all rules (CLAUDE.md rule 7).
- Never map an event to `winback` — winback is defined by absence, not by an event.
- Never claim a revenue stage is covered on `revenue-intent` events alone; say "intent only — no true conversion event".

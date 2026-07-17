---
name: lifecycle-qa
description: Generate test event payloads for generated journeys — positive triggers, branch-condition cases, exits, and negative tests — so the CRM setup can be verified before launch. Use when the user says "test payload", "test eventi üret", "qa", "tetikleyiciyi test et", "sahte event".
---

# Lifecycle QA — Trigger Payload Simulator

The hardest part of wiring a designed journey into a CRM is proving the trigger works: someone hand-writes a fake `purchase` with the right params and posts it at the panel. The engine already knows every journey's entry conditions, branch conditions, and exits — so it writes those payloads itself, including the negative cases a hand-tester forgets.

## Inputs (gate)

1. Generated journey JSONs (from `lifecycle-journeys` / `lifecycle-export`) — the source of truth for triggers, entry conditions, branches, exits.
2. The mapped event inventory (which params each event actually carries — payloads must be **satisfiable by the real instrumentation**, never invent params the tracking plan says don't exist yet).
3. Optional but valuable: **a sample request from the user's CRM** (one real ingestion payload). With it, generated payloads follow the exact envelope (identifier fields, attribute nesting, timestamp format). Without it, payloads use a generic GA4-style shape and say so plainly — never guess a vendor's envelope from memory (same honesty rule as crm-export-mapping's snippet policy).

## What gets generated (per journey)

| Case class | What | Why |
|---|---|---|
| **Entry positive** | One payload satisfying the trigger + every entry condition | Proves the journey arms |
| **Entry negatives** | One payload per entry condition, each violating exactly that condition (wrong event, missing required param, below threshold, excluded segment) | Proves the journey does NOT arm when it shouldn't — the failure a hand-tester never writes |
| **Boundary pair** *(threshold conditions only)* | For a numeric/window condition ("≥ 2 view_item in 30 days"), the value just below the threshold alongside the value just at it (1 vs. 2; day 31 vs. day 30) — not one arbitrary satisfying value | Off-by-one and window-math bugs live at the edge; a single satisfying example can pass while the boundary is wrong |
| **Branch cases** | One payload per branch condition, both sides | Proves each split routes correctly |
| **Timeout / no-response branch** *(wait-gated conditions)* | The no-event side of a branch keyed off a step's `wait` elapsing, not an opposing event | Proves the "nobody responded" path — this can't be proven by posting a payload; the case says whether to advance the sandbox clock or temporarily shorten the wait for the test run |
| **Duplicate delivery** | The same trigger event (same id/params) posted twice | Proves the journey doesn't double-enter or double-fire a user on a retried/replayed delivery — the standard webhook-retry failure mode |
| **Degraded payload** | The entry-positive event with one real-but-optional param dropped or null, per the mapped inventory's own optionality (never an invented gap) | Proves the trigger config survives the partial data real instrumentation actually sends sometimes — a suite built from one idealized sample payload can still pass while realistic partial traffic silently fails to enter |
| **Exit / suppression** | The success-exit event mid-journey; the kill-switch event where the pattern has one (refund, complaint) | Proves exits fire and suppression works — the highest-stakes test in the set |
| **Cap probe** *(portfolio-level)* | The declared `audience_overlaps` scenario: one user triggering both journeys in the same week | Proves the pause/precedence rule actually holds in the tool, not just in the doc |

## Trigger-type awareness

A payload proves an `event`-type trigger fires. It does not prove the other two trigger types the journey schema allows the same way:

- **`time`** (a wait/schedule fires entry, e.g. "3 days after signup with no purchase") — there's no event to post; the test is a state precondition (the qualifying event backdated so the wait has already elapsed) plus an instruction to advance the sandbox clock or temporarily shorten the wait for the run. Say which one the tester should do — don't imply a payload alone proves a time trigger.
- **`segment_entry`** — the payload can prove the *underlying* behavior/attribute changed, but whether the journey actually fires also depends on the CRM's own segment-recomputation cadence (many tools refresh segments hourly or nightly, not on every event). A test that "passes" the instant after posting doesn't rule out a real refresh delay in production. Name the tool's refresh cadence if known; flag it as unverified if not.

## Output

`output/<project>/qa-payloads.json` — machine-facing (CLAUDE.md rule 2 artifact classification), one entry per case:

```json
{
  "journey": "ins-churn-prevention-01",
  "case": "entry-negative: policy_renewal already fired",
  "expect": "journey must NOT arm",
  "payload": { "...": "..." }
}
```

Every case carries an `expect` line — a payload without an expected outcome is not a test. Timestamps are relative placeholders (`<now>`, `<now-2d>`) the tester fills at run time, never baked dates.

**Coverage matrix (user-facing).** Alongside the JSON, present a small table — journeys as rows, case classes as columns, a mark per cell where a case exists — so a missing class (no duplicate-delivery case because the pattern carries no retry risk, no timeout branch because the journey has none) reads as a stated gap, not a silent omission. This is a coverage summary of what was generated, not a pass/fail report: lifecycle-qa doesn't execute against a live CRM, so whether a case actually passed is the tester's to report back once they've run the payloads.

## Never do

- Never invent a vendor's ingestion envelope — no sample request → generic shape + a clear "adapt the envelope" note.
- Never generate a payload the real instrumentation can't produce (params the tracking plan lists as missing) — that "passing" test would validate a journey the production data can never trigger.
- Never mark the set complete without the negative cases — positive-only QA is how silently-broken entry conditions reach production.
- Never let one golden-path sample payload stand in for the full range real instrumentation produces — an optional param that's sometimes missing or null in production is exactly what the degraded-payload case exists to catch; a set built only from the one idealized shape the user pasted is a contract test with a sample size of one.
- Never present a `segment_entry`/`time` case as equivalent proof to an `event` case — state plainly whether firing was proven directly or depends on a schedule/refresh cadence the payload doesn't control.

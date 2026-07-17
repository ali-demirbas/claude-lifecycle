---
name: lifecycle-audit
description: Audit an existing journey portfolio — user-described, imported from a CRM tool, or previously generated. Scores coverage, conflicts, depth-vs-data fit, and copy compliance. Use when the user says "journey'lerimi denetle", "audit my flows", "mevcut otomasyonları incele", "portfolio audit".
---

# Lifecycle Audit — Portfolio Review

Score an existing set of journeys against the same rules the engine uses to generate them. Output: an **Audit Report** with per-journey findings and a portfolio-level verdict.

## Inputs

Journeys as: prior engine output, user description ("we have a welcome email and a cart reminder"), or CRM exports/screenshots. Sparse descriptions are fine — audit what is known, list what could not be assessed. If available, also use the DQS + stage map; without them, stage-coverage **and depth-vs-data-fit** findings are marked "data-blind" — dimension 3 specifically cannot be judged without knowing what the data supports, so guessing "over-engineered" or "under-leveraged" from journey shape alone is a fabrication risk (CLAUDE.md rule 3), not a finding.

## Audit dimensions (score each 0–5, with evidence)

| # | Dimension | What is checked |
|---|---|---|
| 1 | Stage coverage | Each lifecycle stage with events has ≥ 1 journey; blind spots named (uses playbook `pattern_priorities` as the expectation) |
| 2 | Priority fit | Are the sector's P0 patterns running? A missing P0 (e.g. no abandoned-cart in e-commerce) is automatically a Critical finding |
| 3 | Depth-vs-data fit | Journey complexity matches what the data supports: 10-step branched flows on thin data = over-engineered; 2-step flows on rich data = under-leveraged |
| 4 | Trigger & exit hygiene | Event triggers vs blast schedules; success exits defined; re-entry policies exist |
| 5 | Frequency & conflict | Aggregate worst-case messages/user/week vs caps in `knowledge/compliance/consent-and-quiet-hours.md`; overlapping triggers |
| 6 | Measurement | Primary KPI + guardrail per journey; holdout existence; primary KPI defined as incremental lift vs holdout, not an attributed number (see `knowledge/measurement.md`) |
| 7 | Copy compliance *(if copy provided)* | Spot-check against channel hard rules + lexicon banned lists |
| 8 | Portfolio currency | Has the portfolio changed (journeys added/removed) since the last conflict review? A stale conflict review — cap math not covering the current journey set — is automatically a High finding |

**Dimension 4 also covers sector-benchmark fit.** When a running pattern has sector-specific timing guidance in `knowledge/industries/<sector>.md` ("Sector-specific timing & cadence"), compare the journey's actual/stated trigger timing and channel escalation order against that guidance and cite the specific range verbatim (e.g. "fires at 48h against the sector's 1–4h cart-abandonment window") — never an invented industry average (CLAUDE.md rule 3: ranges from knowledge files may be cited, nothing may be fabricated). A deviation is a finding scaled to its degree, not an automatic Critical — existing-but-slow still beats missing (dimension 2), and severity comes from revenue/compliance impact, not distance from the benchmark alone.

## Scoring posture (anti-inflation)

Score as an adversarial reviewer of someone else's work, not as the author: if you cannot name a concrete gap for a dimension, you have not looked hard enough to score it high. When torn between two adjacent scores, take the lower. Mostly-top scores on a first pass are a signal to re-examine the scoring, not evidence of quality. Never reverse-engineer scores from a desired overall verdict.

Two failure modes get confused under this posture and must be told apart: **no evidence provided** (the description simply didn't cover it — mark "not assessable," exclude it from the average, but count it in coverage) is not the same as **evidence of absence** (the journey was described and plainly has no exit criteria, no holdout, etc. — that scores low). Defaulting ambiguous cases to "not assessable" rather than a guessed-low score keeps the adversarial posture from tipping into fabrication.

When the verdict gates a real decision (budget, headcount, killing a program), treat one pass as provisional: a second independent pass (fresh session, or a different model) that disagrees by ≥ 2 points on any dimension is the same "two judgments to gate" discipline `evals/rubric.md` already applies to copy and journey judging — one adversarial pass catches more than no review, but it is still one reviewer's read.

## Report format

1. **Verdict** — one paragraph + overall score (avg of the *scored* dimensions, /5) + evidence coverage stated inline, the same way the DQS reports its flags in the score line itself rather than burying them — `6/8 dimensions scored, 2 not assessable (measurement, copy compliance — no config visibility)` — never a bare average silently computed over however many dimensions happened to be visible. A verdict built on fewer than half the dimensions says so in the paragraph itself, not just in the coverage tag.
2. **Findings table** — severity (Critical/High/Medium/Low) | journey | finding | fix. Critical = revenue leaking or compliance risk.
3. **Coverage map** — same stage table as the portfolio template §3.
4. **Recommended actions** — ordered; each one maps to a concrete next step (`run /lifecycle journeys for the missing P0s`, `re-run copy for flow X`, and when the user has performance data: `run /lifecycle results to score these against holdouts`).
5. **Audit trail** — when a brand config exists, check `output/<brand>/audit-history.md` (create it if absent, same convention as `results-log.md`): a Critical/High finding matching one from the prior run's log (same journey + same dimension) is flagged `repeat finding, open since <date>` instead of reported as new; a prior Critical/High that doesn't reappear gets one line `resolved since last audit`. Append this run's Critical/High findings before closing out. No brand config (ad hoc/anonymous audit) → skip this step and note once that findings aren't being tracked across runs.

## Never do

- Never score dimensions without stating the evidence ("no exit criteria mentioned for 3 of 5 journeys").
- Never fail a journey for missing information the user didn't provide — mark "not assessable" instead.
- Never rewrite the user's journeys inside the audit — the audit diagnoses; generation is a separate, offered step.

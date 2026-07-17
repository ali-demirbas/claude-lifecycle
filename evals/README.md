# Evals — Scenario-Based Decision Tests

The deterministic layer (`scripts/validate_*.py`) checks that outputs are *well-formed and compliant*. This suite checks that the engine's **decisions are correct**: what gets generated, what gets blocked, how deep, who is suppressed. Wording is never tested — decisions are.

## Case authoring rules (every case must satisfy all)

1. **Single purpose.** One case tests exactly one rule/decision. If a case fails, you must know which rule broke.
2. **Machine-checkable expectations.** Every assertion in `expected.yaml` is verifiable by `scripts/eval_check.py` — pattern lists, step counts, suppression lists, greps. "Output should make sense" is not an assertion here — graded qualities live in the **rubric layer** ([rubric.md](rubric.md)): anchored 1-5 dimensions for copy, journey design, and dossier quality, judged blind with quoted evidence.
3. **Rule reference required.** Every case names the written rule it tests (`rule_refs`). No rule, no case — write the rule first. Reverse lookup: when a rule changes, grep `rule_refs` to find the cases to update.
4. **Self-contained input.** `input.csv` (≤ 50 synthetic rows) + `intake.md` — nothing else. Data is deliberately constructed to trigger the tested condition.
5. **Negative twin.** Critical rules are tested in both directions ("generates when X" ↔ "blocks when not-X"), as separate cases.
6. **Bug → case.** Every caught engine mistake becomes a permanent case.
7. **Fictional companies only — hard rule.** No real company, brand, or product name may appear anywhere in a case (inputs, intake, expected strings). All names are invented; any resemblance is coincidental. A case containing a real brand name is rejected in review.

## Directory layout

```
evals/
  cases/<case-id>/
    input.csv        # synthetic source data (omit for T3 cases)
    intake.md        # user answers the pipeline would collect
    expected.yaml    # assertions + rule_refs (contract below)
  out/<case-id>/     # produced by a run; gitignored
```

## Running

Each case is executed by Claude running the normal pipeline (`connect → map → journeys` and, where `run.copy: true`, `copy`) with the case's input + intake, writing all artifacts to `evals/out/<case-id>/` — including `portfolio.json`. Then:

```bash
python3 scripts/eval_check.py evals/cases/<case-id>       # one case
python3 scripts/eval_check.py evals/cases                 # whole suite
```

Pass criteria: **binary — every assertion in every case must pass.** The report names each failed assertion with its rule reference. Run before releases and after skill/knowledge changes; the deterministic tests remain the per-PR CI gate.

## expected.yaml contract (consumed by eval_check.py)

```yaml
case: <case-id>
company: <fictional name>          # fictional only (rule 7)
sector: <industry slug or "unknown">
tier: T1 | T2 | T3
rule_refs:
  - <repo path + anchor of the rule under test>
run:
  copy: false                      # whether the copy stage runs for this case
assertions:
  must_generate: [<pattern>, ...]            # patterns present in portfolio.json
  must_not_generate: [<pattern>, ...]        # patterns absent from portfolio.json
  must_block:                                # entries in portfolio.json "blocked" list
    - pattern: <pattern>
      reason_contains: <substring>
  min_steps: {<pattern>: N}                  # from journey JSONs
  max_steps: {<pattern>: N, any: N}
  suppressed_accounts_include: [<id>, ...]   # portfolio.json "suppressed_accounts"
  audience_must_exclude: [<id>, ...]         # id may not appear in any journey audience.include
  required_anywhere: [<substring>, ...]      # grep across all out-files (case-insensitive)
  forbidden_anywhere: [<substring>, ...]
  copy:
    forbidden: [<substring>, ...]            # grep in copy *.md only
    required: [<substring>, ...]
    must_pass_validator: true
    max_discount: 0                          # passed to validate_output.py copy
```

All assertion keys are optional; at least one is required.

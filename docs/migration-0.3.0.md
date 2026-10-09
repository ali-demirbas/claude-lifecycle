# Migrating outputs to 0.3.0

0.3.0 changes the journey JSON from a flat step list to a node graph (`templates/journey.schema.json` 2.0). Old outputs still open, render and validate. The validator now tells you what it can't verify about them instead of passing them.

## What happens to an existing 1.x journey

- `validate_output.py journey old.json` exits **3** (no error found, but critical items unverifiable), or **1** if it finds a real defect. It reports both readings of the old waits: every wait counted from entry, and each wait counted from the previous step. The old format never said which one was meant. Real runs used both.
- A branch condition that reads an email open ("not opened", "açılmadıysa") is now an **error**.
- In a portfolio, a legacy journey's weekly load is computed as a lower bound (unconditioned steps, under both readings). A declared count below that bound fails.
- Old dossiers and canvases are left as they are. Don't rewrite them to make them pass: a dossier that said "passed" under 0.2.0 records what that validator checked at the time. Re-validate them, and keep the new result next to the old one.

## How to migrate a journey

1. **Timing.** For each step, decide what its wait was measured from, and write it as an anchor on a `message` node:
   - `{"from": "entry", "offset": "P4D"}` for "4 days after the user entered".
   - `{"from": "node", "node": "s2", "offset": "P2D"}` for "2 days after s2".
   - `{"from": "event", "event": "trial_end", "offset": "-P2D"}`, plus `time_anchors: {"trial_end": {"relative_to_entry": "P7D"}}`, for "2 days before the trial ends".
2. **Branches.** Replace each `branch_condition` with a `decision` node. A decision has:
   - a signal (event, bot-filtered click, or attribute) and its source;
   - a window;
   - routes for `occurred`, `not_occurred` and `unmeasurable`.

   Steps that were alternatives (for example standard vs VIP) become separate branches; they are no longer sequential steps. Replace open-based conditions with a click or a product event, or remove the branch.
3. **Exits.** List the success event, consent withdrawal and any pattern-specific stops in `exit.exit_conditions`, with `check: ["entry", "before_each_send"]`.
4. **Re-entry.** Turn `reentry_policy` text into `reentry: {policy, cooldown, on_duplicate_trigger}`.
5. **Measurement.** Replace `experiment` with a `measurement` block: a design, the primary outcome and its window, and either:
   - for a holdout: assignment unit, consistent assignment, and what the control doesn't receive;
   - for no holdout: the reason and the alternative measurement.

   Add `journey_class` (marketing, service or transactional).
6. **Inventory.** Add `events_available` from the stage map, and `schema_version: "2.0"`.
7. Validate, then render the doc's §5 and §8: `python3 scripts/validate_output.py journey new.json && python3 scripts/journey_render.py new.json`.

`examples/ecommerce-full-ga4/05-journey-cart-recovery.json` is a complete before/after: its 0.2.0 version listed steps 5 and 6 as sequential although they were alternatives, and branched step 3 on "step 1 not opened".

## Portfolio registry

A 2.0 portfolio (`schema_version: "2.0"`) needs:
- `file` for each journey, so that load is computed from its sends;
- `frequency_policy.on_breach` (defer, skip or priority);
- `external_journeys_status`, plus `external_journeys` when existing communications were declared.

`est_msgs_per_week` stays as a declaration the validator checks. It is no longer the source of truth.

## Exit codes

`0` passed · `1` errors · `2` usage error · `3` no errors, but critical items unverifiable. Scripts and CI that treated any non-zero exit as failure will now also stop on 3. That is intended for a final gate. Where you only want hard errors to stop you, accept 0 and 3, and present the UNVERIFIED list together with the output.

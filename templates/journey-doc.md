# Journey Doc Template

Every generated journey MUST use this exact structure. Replace `<...>` placeholders.
Sections marked **(required)** may never be omitted; sections marked *(if applicable)* may be dropped only when stated.

---

# Journey: <Human-readable name>

**ID:** `<sector>-<pattern>-<nn>` · **Version:** 1.0.0 *(bump on every change)* · **Pattern:** [<pattern-name>](../knowledge/journey-patterns/<pattern-name>.md) · **Priority:** P0 | P1 | P2
**Data tier:** T1 | T2 | T3 · **DQS at generation:** <n>/100 *(T3: n/a)* · **Depth class:** simple | standard | branched *(the send count comes from the pattern's `depth_range`; carry the class into the JSON's `depth_class`)* · **Class:** marketing | service | transactional
**Readiness:** ready to implement | draft *(draft = something that affects correctness is still unconfirmed: channel consent, an event's existence, an existing communication, or what a date means. List each open item in §9)*
**Validation:** `validate_output.py` <version> · schema 2.0 · <passed | incomplete: n unverified | failed>
**Vertical:** <vertical name> *(multi-vertical brands only — omit entirely for single-industry brands; carry this into the journey JSON's `vertical` field the same way as Depth class above)*

## 1. Objective (required)

One sentence: what business outcome this journey drives, and the single primary KPI.

## 2. Trigger & entry (required)

| Field | Value |
|---|---|
| Trigger type | event-based \| time-based \| segment-entry |
| Trigger | `<event_name>` or schedule |
| Entry conditions | <all conditions that must hold, incl. consent> |
| Re-entry policy | <once \| after cooldown (P90D) \| each trigger> · repeated trigger while active: <ignore \| restart \| new instance (only with a cooldown)> |
| Quiet hours | <per knowledge/compliance/consent-and-quiet-hours.md> |

## 3. Audience (required)

- **Who enters:** <segment definition in plain language>
- **Who is excluded:** <exclusions — e.g. purchased in last 24h, in another P0 journey>
- **Estimated volume:** <from data if T1/T2; write "unknown — estimate after launch" if T3>

## 4. Exit & success criteria (required)

- **Success (conversion) exit:** `<event>` · **Success window:** <ISO duration, e.g. P30D>
- **Checked before every send, not only at entry:** <success event>, <consent withdrawal / unsubscribe>, <pattern-specific stops, e.g. refund, cancellation reversed>. A pending message stops when any of these has happened.
- **Handoffs:** <exit → target journey, queued sends from this journey suppressed> *(if applicable)*
- **Other exits:** journey completed, entered a higher-priority journey (per the portfolio's contact policy).

## 5. Steps (required)

Generated, never hand-written: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/journey_render.py" <id>.json --section table` renders this table from the journey JSON's node graph.

| Node | When | Channel | Message intent | Reached via | Copy ref |
|------|------|---------|----------------|-------------|----------|
| s1 | +PT1H after entry | email | <one-line intent> | — | step-1 |
| s2 | +P1D after d1 | push | <intent> | d1=not_occurred | step-2 |

Rules behind the table (they live in the JSON):
- **When** always names its anchor: journey entry, a specific earlier node, or an event/attribute date (`trial_end -P2D`) whose relation to entry is declared in `time_anchors`. A calendar time (10:00 on the renewal date) states its timezone. There is no implicit "after the previous step".
- **Decisions** are their own nodes: the signal and where it comes from, the window it is read in, a route for `occurred`, `not_occurred` and **`unmeasurable`**. Not measurable is never treated as "did not happen", and never as disinterest. An email open is never a branching signal on its own.
- Mutually exclusive paths are separate branches of the graph, so their waits are never added together. A node reached from several branches (a merge) is anchored to something every one of those paths shares.
- **Copy ref** links each send to its block in the copy output ([copy-output.md](copy-output.md)).

## 6. Measurement (required)

| KPI | Type | Definition | Target |
|---|---|---|---|
| <e.g. cart recovery rate> | primary | <definition, measured as **incremental lift vs control** where a holdout exists> | <target or "baseline after 4 weeks"> |
| <e.g. unsubscribe rate> | guardrail | <definition> | <ceiling, e.g. < 0.3% per send> |

- **Design:** holdout | none (low volume) | none (service) | pre/post | other. Not every journey gets the same holdout share; the share follows the volume and the risk of withholding the message. Service and transactional journeys are not held out like marketing.
- **Primary outcome + window:** `<event>` within <ISO duration>.
- **Holdout** *(if used)*: <share>, assigned consistently per <user | account | household> (the same unit always lands in the same group); the control does not receive <which new communications>.
- **Routine communications:** <existing welcome email, transactional mails…> — sent to both groups / suppressed for control.
- **Contamination risks:** <overlapping journeys that also reach the control group>.
- **Volume note:** <what the expected volume can and cannot detect>. A holdout makes a result measurable; it does not make it statistically reliable.
- **No holdout?** State why and the alternative measurement used instead.
- Opens/clicks/step conversions are per-step diagnostics and never substitute for the primary outcome — see [measurement.md](../knowledge/measurement.md).
- **A/B plan:** <what is tested first + the hypothesis it decides>.

## 7. Frequency & compliance notes (required)

- Worst-path sends per rolling 7 days per channel (computed by the validator from the node graph, not estimated) and which journey wins on conflict under the portfolio's contact policy.
- Consent requirements per channel used (see [consent-and-quiet-hours.md](../knowledge/compliance/consent-and-quiet-hours.md)).

## 8. Flow diagram (required)

Generated: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/journey_render.py" <id>.json --section mermaid` (straight from the node graph, branches and merges included).

## 9. Open items and data gaps *(if applicable)*

- **Open items (make the journey a draft):** facts that affect correctness and are not confirmed yet: channel consent, whether an event exists, existing communications, what a date field means. Each line says who confirms it.
- **Data gaps:** events or attributes that would improve this journey but aren't tracked yet → cross-reference the [tracking plan](tracking-plan.md).

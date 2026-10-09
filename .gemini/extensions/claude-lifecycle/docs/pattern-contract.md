# Pattern file contract (schema 2.0)

Every file in `knowledge/journey-patterns/` follows this contract. Generated journeys are validated against `templates/journey.schema.json` 2.0; a pattern is what a journey is instantiated from, so the pattern must already speak the same language: explicit timing anchors, decisions with an evaluation window and an unmeasurable route, exit conditions re-checked before each send, a re-entry rule and a measurement approach. `scripts/validate.sh` section 2 checks the frontmatter keys and section headings below.

## Frontmatter

Existing keys stay: `name, stage, trigger_type, required_events, optional_events, required_attributes, optional_attributes, default_channels, base_steps, depth_range, applicable_industries, mutually_exclusive_with`. New keys:

| Key | Values | Meaning |
|---|---|---|
| `journey_class` | `marketing` \| `service` \| `transactional` | Service/transactional journeys are exempt from marketing frequency caps and are not forced into a marketing holdout |
| `signal_sources` | map event/attribute → `authoritative` \| `behavioral` \| `inferred` \| `engagement` | Where each required signal comes from. authoritative = system of record (orders, billing, consent); behavioral = product/web analytics; inferred = a score or model; engagement = message clicks |
| `insufficient_alone` | list of short strings | Signals that must not trigger or branch the journey on their own |
| `exit_before_each_send` | list of event names | Re-checked before every send, not just at entry. Always includes the success event; marketing patterns also include a consent-withdrawal event |
| `reentry` | flow map `{policy, cooldown, on_duplicate_trigger}` | Default for generated journeys. policy: once \| after_cooldown \| each_trigger; on_duplicate_trigger: ignore \| restart \| new_instance (new_instance only with a cooldown) |
| `measurement_default` | `holdout` \| `none_service` \| `pre_post` | Default design; generated journeys fall back to `none_low_volume` + an alternative when volume can't support a holdout |

List items are plain strings with no `: ` inside them (the frontmatter must parse as YAML).

## Body sections (exact headings, in this order)

1. `## Required-event signature`: table `| Event | Source | Role |`, then a `### Not enough on its own` list explaining each `insufficient_alone` entry.
2. `## Entry / exit`: entry conditions, exclusions, success exit + window, the exit conditions checked before each send, re-entry and what a repeated trigger does while an instance is active, and handoffs to other journeys (target + queued sends suppressed).
3. `## Depth scaling`: unchanged in meaning.
4. `## Step blueprint (<depth>, <n> sends)`: table `| Node | When | Channel | Intent | Route |`.
   - **When** always names its anchor: `entry +1h`, `s2 +3d`, `trial_end -2d`, `renewal_date -30d at 10:00 user_local`. Never a bare `+3d`.
   - Decision rows: Node `d1`, Channel `—`, Intent `Decision on <signal> (<source>) between <from> and <to>`, Route `occurred → s3 · not_occurred → s4 · unmeasurable → s4`.
   - No branch reads an email open, alone or as the deciding half of a condition. Use a click (bot-filtered) or a product/system event.
   - The unmeasurable route never leads to a disengaged/suppressed exit: missing data is not disinterest.
5. `## Timing and channel fit`: when sends are allowed (quiet hours, business vs user clock), which channels fit which step and why, and the fallback when a channel isn't consented.
6. `## Frequency and overlap`: sends per rolling 7 days on the worst path, which other patterns usually overlap with it, and the precedence/defer behavior when they do.
7. `## Measurement`: primary outcome + window, design (holdout and what the control does not receive; or why not and the alternative), routine communications both groups keep, contamination risks, what low volume can and cannot show.
8. `## When data is missing`: what the journey does when an optional signal is absent, a required one is delayed, or a branch signal can't be measured.
9. `## KPIs` and `## Common mistakes`: as before.

## Writing rules

- Rules from the author's own journey library may be adapted; write them fresh in this repo's voice, and record each adapted rule's source journey id in `docs/audit/0.3.0-pattern-provenance.md`. Never copy sentences, headlines or visuals verbatim.
- Thresholds that depend on the business (a lapse window, a recommendation's minimum support) are stated as configurable with a default and the evidence needed to change it, never as a universal number.
- Don't name third-party websites or vendors.

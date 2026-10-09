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
| `instance_key` *(optional)* | e.g. `invoice_id`, `subscription_id`, `cart_id`, `order_id` | The entity one instance is about. Patterns whose triggers and stops are per entity declare it, and their exit/decision events say "for this instance" |

List items are plain strings with no `: ` inside them (the frontmatter must parse as YAML).

Normalization (checked by `scripts/tests/instantiate_patterns.py`): channel names use the schema vocabulary (`email`, `push`, `sms`, `in_app`, `whatsapp`); `mutually_exclusive_with` is always present (`[]` when none); `reentry.cooldown` appears only with `policy: after_cooldown` and is a non-negative duration in days/weeks (no months or years: a yearly date recurs through its attribute anchor and `each_trigger`, not through a cooldown).

## Body sections (exact headings, in this order)

1. `## Required-event signature`: table `| Event | Source | Role |`, then a `### Not enough on its own` list explaining each `insufficient_alone` entry.
2. `## Entry / exit`: entry conditions, exclusions, success exit + window, the exit conditions checked before each send, re-entry and what a repeated trigger does while an instance is active, and handoffs to other journeys (target + queued sends suppressed).
3. `## Depth scaling`: unchanged in meaning.
4. `## Step blueprint (<depth>, <n> sends)`: table `| Node | When | Channel | Intent | Route |`.
   - **When** always names its anchor: `entry +1h`, `s2 +3d`, `trial_end -2d`, `renewal_date -30d at 10:00 user_local`. Never a bare `+3d`.
   - Decision rows: Node `d1`, Channel `—`, Intent `Decision on <signal> (<source>) between <from> and <to>`, Route `occurred → s3 · not_occurred → s4 · unmeasurable → s4`.
   - No branch reads an email open, alone or as the deciding half of a condition. Use a click (bot-filtered) or a product/system event.
   - A decision that reads several signals says so: `any_of(link_click (engagement, bot-filtered), session_start (behavioral))` or `all_of(...)`. any_of is occurred if any member occurred, not_occurred only if every member was measured and none occurred, unmeasurable otherwise. Never drop a signal or invent a combined event to fit one name.
   - A decision is taken at the end of its window. A check about a known future date ("does the points expiry fall within the next 30 days?") is evaluated at the decision moment, with `from` and `to` both at that moment, reading the date attribute; it never waits for the date itself.
   - In-app steps are shown at the user's next session: state how long they wait to be shown (`expires after 3d`) and that later anchors use the scheduled time. A required outbound notice is never gated on an in-app view.
   - A final notice tied to a hard date (suspension, renewal, expiry) states its deadline; quiet hours delay it at most to the last allowed time before that deadline.
   - When the runway before a date varies (trial length, grace period, time left to renewal at entry), state the compression rule for short runways: which steps are dropped or merged. Never push a step past the one after it or past the date.
   - Dates whose distance from entry varies per user are anchored to the date attribute, declared as a range relative to entry (`renewal_date: entry +2d … +45d`), and read from the system of record at send time.
   - The unmeasurable route never leads to a disengaged/suppressed exit: missing data is not disinterest.
5. `## Timing and channel fit`: when sends are allowed (quiet hours, business vs user clock), which channels fit which step and why, and the fallback when a channel isn't consented.
6. `## Frequency and overlap`: sends per rolling 7 days on the worst path, which other patterns usually overlap with it, and the precedence/defer behavior when they do.
7. `## Measurement`: primary outcome + window, design (holdout and what the control does not receive; or why not and the alternative), routine communications both groups keep, contamination risks, what low volume can and cannot show.
8. `## When data is missing`: what the journey does when an optional signal is absent, a required one is delayed, or a branch signal can't be measured.
9. `## KPIs` and `## Common mistakes`: as before.

## Rules that apply to every pattern

- **No review gating.** A public review or store-rating request never depends on a private satisfaction answer or rating. It goes to every eligible person (by operational criteria such as delivery confirmed, no open refund or ticket) or to none. A satisfaction answer may route service recovery and referral asks; it never decides who is asked for a public review.
- **Intent is not a decision.** Cancel intent (a cancel page visit, a cancel flow started) and a confirmed cancellation are different signals. Save offers react only to intent; a confirmed cancellation exits the save path and hands off to cancellation-winddown.
- **Not reached is not not-engaged.** No click on a delivered email doesn't justify escalating to a costlier or more intrusive channel on its own; escalation needs a reason the target channel's own suitability table accepts.
- **A click is not a recorded choice.** Preference changes, consents and choices are read from the system that records them (`preference_updated` with its value, `consent_granted`), never inferred from a link click.

## Writing rules

- Rules from the author's own journey library may be adapted; write them fresh in this repo's voice, and record each adapted rule's source journey id in `docs/audit/0.3.0-pattern-provenance.md`. Never copy sentences, headlines or visuals verbatim.
- Thresholds that depend on the business (a lapse window, a recommendation's minimum support) are stated as configurable with a default and the evidence needed to change it, never as a universal number.
- Don't name third-party websites or vendors.

---
name: trial-conversion
stage: revenue
trigger_type: event
required_events: [trial_start, subscription_start]
optional_events: [feature_used, trial_end, login, tutorial_complete, add_payment_info, paywall_view, quota_limit_reached, link_click]
required_attributes: [trial_length]
optional_attributes: [plan_name, trial_end_date, activation_score]
default_channels: [email, in_app, push]
base_steps: 6
depth_range: [1, 10]
applicable_industries: [saas, subscription-media, mobile-app, fintech, edtech]
mutually_exclusive_with: []
journey_class: marketing
signal_sources: {trial_start: authoritative, subscription_start: authoritative, trial_end: authoritative, trial_length: authoritative, feature_used: behavioral, login: behavioral, tutorial_complete: behavioral, add_payment_info: authoritative, paywall_view: behavioral, quota_limit_reached: behavioral, activation_score: inferred, consent_withdrawn: authoritative}
insufficient_alone:
  - a login or session without core feature use
  - a paywall view
  - add_payment_info without subscription_start
  - activation_score
exit_before_each_send: [subscription_start, consent_withdrawn]
reentry: {policy: after_cooldown, cooldown: P90D, on_duplicate_trigger: ignore}
instance_key: trial_id
measurement_default: holdout
---

# Trial Conversion

Convert trial users into paying subscribers before the trial expires. The P0 journey for any subscription business: the entire monetizable audience passes through it, and it is strictly time-boxed. Every send must land inside `trial_length`, so the sequence compresses or stretches with the trial, not with marketing appetite. The core mechanic is branching on **activation depth**: users who reached value (`feature_used` on core features) get a confident conversion ask; users who never activated get help, because selling to someone who hasn't experienced the product converts poorly and churns fast.

**Time anchors.** Early sends are anchored to `trial_start`; the closing sends are anchored to `trial_end`, declared as a range relative to entry that covers **only the runway band this journey JSON is built for** (`trial_end: entry +14d … +30d` for the standard shape, `entry +7d … +13d` for the 7–13-day shape; one JSON per band when trial lengths vary, because the graph can't express a node that exists only at some runways and a wider range is reported unverifiable at its short end) and **re-read from the billing system's `trial_end_date` at each send**, never computed once at entry. Only when billing holds no end date is it derived as `trial_start + trial_length`, and marked so. On the main path `trial_start` = entry.

## Required-event signature

| Event | Source | Role |
|---|---|---|
| `trial_start` | authoritative | Trigger and the anchor of the early sends. `trial_length` (attr) sets the clock. |
| `subscription_start` | authoritative | Success exit, re-checked before every send: a paying user leaves immediately. Without it conversion cannot be measured; pattern is **blocked**. |
| `trial_end` / `trial_end_date` *(optional)* | authoritative | Anchor of the closing sends and of the post-expiry grace step. Without it, computed from `trial_start + trial_length` and marked as derived. |
| `feature_used` *(optional)* | behavioral | The activation-depth decisions. With a `feature` param, splits activated vs not activated; the single highest-leverage optional event. |
| `add_payment_info` *(optional)* | authoritative | Very-high-intent signal; card on file gets a lighter sequence in the branched shape. |
| `login` / `tutorial_complete` *(optional)* | behavioral | Cheap activation proxies when `feature_used` isn't instrumented. |
| `paywall_view` *(optional, with dwell param)* | behavioral | Feeds d3 and the in-session hesitation pivot. |
| `quota_limit_reached` *(optional, freemium daily-cap apps)* | behavioral | Alternate, softer entry; see the Freemium daily-limit entry below. |

### Not enough on its own

- **A login or session without core feature use.** Showing up is not experiencing value; a login-only user gets the help track, not the confident ask. Use `login` as a proxy only when `feature_used` is missing, and label it a proxy.
- **A paywall view.** It shows the price was seen, not that the user decided; it routes d3, never a discount or an exit.
- **`add_payment_info` without `subscription_start`.** High intent, not conversion; the success exit stays `subscription_start`.
- **`activation_score`.** A model can order the help queue; it does not replace the activation decision.

## Entry / exit

- **Entry:** `trial_start` fired, no active subscription, user messageable on ≥ 1 channel (email consent is usually collected at signup).
- **Freemium daily-limit entry:** for apps with a hard daily cap on the free tier, `quota_limit_reached` is a second, softer entry. It sends one bounded trial invitation (q1) at the moment of felt friction. **It does not create a second clock:** every later send stays anchored to `trial_start` and `trial_end`, which exist only once the user accepts. A user who doesn't start a trial within the acceptance window (configurable, default 7 days) exits without further sends; a user already mid-trial is not re-entered by the next quota hit.
- **Exclude:** already subscribed on another account or plan (identity-stitched); enterprise or sales-led trials with a human owner; a second trial within 90 days (returning trialist, different message).
- **Success exit:** `subscription_start` · **Window:** `trial_end +7d` (trial plus a 7-day grace).
- **Checked before every send:** `subscription_start` on any plan for this account (a paying user leaves immediately), `consent_withdrawn` scoped to that channel: an email unsubscribe stops the emails, while push and in-app steps continue where consented, and a legally required expiry notice still goes transactionally (see Timing). One instance follows one trial (`instance_key: trial_id`).
- **Re-entry:** once per distinct trial (each new `trial_start` outside the 90-day exclusion opens a new instance); a duplicate `trial_start` for the same trial is ignored.
- **Hand-offs:** converters go to post-purchase / onboarding-for-paid; non-converters after the grace step go to `winback` or the low-frequency list, and nothing queued here survives the window.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (4) | DQS < 40 or no usage events | Time-based only: welcome → progress recap → expiry notice → last call. No decisions; honest but blunt. |
| Standard (5–7) | DQS 40–69, `login` or `feature_used` present | Adds the activation decisions: activated users get the conversion track, silent users get an obstacle-removal track. |
| Branched (8–10) | DQS ≥ 70 + `feature_used` with `feature` param | Per-feature activation nudges, `add_payment_info` fast lane, post-`trial_end` grace step, optional human touch for high-fit silent accounts, and the in-session hesitation pivot when `paywall_view` is tracked. |

All depths are bounded by the trial clock; the runway table under the blueprint says which nodes exist at each trial length.

## Step blueprint (standard, 6 sends)

Written for a 14-day trial; `trial_end -7d`, `-3d` and `-1d` cover the final week.

| Node | When | Channel | Intent | Route |
|---|---|---|---|---|
| q1 | entry +0m (in the current session; expires when it ends) | in_app | Freemium entry only: a bounded trial invitation at the moment the daily cap is hit | → s1 on `trial_start` |
| s1 | trial_start +1h | email | Welcome: the one action that predicts success in this product ("do X first") | → d1 |
| d1 | trial_start +2d | — | Decision on core `feature_used` (behavioral) between trial_start and trial_start +2d | occurred → s3a · not_occurred → s2 · unmeasurable → s2 |
| s2 | trial_start +2d (shown at next session, expires after 2d) | in_app | Nudge toward the core feature, shown at the next session; s3a/s3b keep their own anchor whether or not it was seen | → d2 |
| d2 | trial_start +4d | — | Decision on core `feature_used` (behavioral) between trial_start and trial_start +4d | occurred → s3a · not_occurred → s3b · unmeasurable → s3b |
| s3a | trial_start +4d | email | Activated: deepen the use case they already started | → s4 |
| s3b | trial_start +4d | email | Not activated: "what's blocking you?" plus help, docs or support | → s4 |
| s4 | trial_end -7d | email | Progress recap: what they have done, what stays and what goes when the trial ends | → s5 |
| s5 | trial_end -3d | email | Expiry notice: the date, the price, what happens to their data and access. Plain and factual | → d3 |
| d3 | trial_end -1d | — | Decision on `paywall_view` (behavioral) between s5 and trial_end -1d | occurred → s6a · not_occurred → s6b · unmeasurable → s6b |
| s6a | trial_end -1d (shown at next session, expires at trial_end) | in_app | Looked at the price and stopped: answer the question still open for them (what's kept, how to cancel, plan differences), no countdown | end |
| s6b | trial_end -1d | push | Last call with a deep link to upgrade; state the real deadline only | end |

Each closing send answers the next unresolved question for that user's state instead of repeating the countdown: what they have achieved (s4), what it costs and what happens next (s5), what still stops them (s6). The longest path (q1 aside) is s1, s2, s3b, s4, s5, s6.

### Runway: which nodes exist

The runway is `trial_end - trial_start`, with `trial_end` read from billing. Offsets in the blueprint are for 14 days or more; shorter runways compress as follows. A node whose time would fall at or before the node it follows, or after `trial_end`, is dropped, never stacked; the timelines below are already chronological.

| Runway | Nodes that exist (day = days after trial_start) |
|---|---|
| 14 days or more | Full standard shape. 14 days: s1 d0 · d1/s2 d2 · d2/s3a or s3b d4 · s4 d7 · s5 d11 · d3/s6a or s6b d13. 30 days: s1 d0 · s2 d2 · s3 d4 · s4 d23 · s5 d27 · s6 d29. |
| 7–13 days | s4 dropped; d1/s2 at `trial_start +1d`, d2/s3a or s3b at `trial_start +2d`; s5 at `trial_end -3d`, d3/s6 at `trial_end -1d`. For 7 days: s1 d0 · s2 d1 · s3 d2 · s5 d4 · s6 d6. |
| 4–6 days | Simple shape: no d1/d2/s3, no s4. s1 d0 · s2 (in-app nudge, no decision) at `trial_start +1d` · s5 at `trial_end -2d` · d3/s6 at `trial_end -1d`. For 4 days: s1 d0 · s2 d1 · s5 d2 · s6 d3. |
| 2–3 days | s5 merged into s1: the welcome states the end date, the price and what happens at the end. s2 at `trial_start +1d` only when it lands at least 12h before s6; s6b at `trial_end -1d`. For 3 days: s1 d0 · s2 d1 · s6b d2. |
| under 2 days | s1 only, carrying the date and price. |

The 2–3-day and under-2-day shapes have fewer sends than the standard one; `depth_range` starts at 1 for that reason, not as a target.

**Extended trial.** Because the closing anchors are re-read at send time, an extension moves s4, s5 and s6 to the new `trial_end` without restarting anything. Sent nodes are not repeated, except that s5 is re-sent at the new `trial_end -3d` if it had already gone out with the old date (a correction, stated as such). A node whose turn in the chain has passed is not revived: if s5 was sent before the extension, s4 is dropped rather than arriving after it. The runway band is recomputed from the new length for the nodes still to come. A shortened trial follows the same rule in reverse: nodes that would fall after the new `trial_end` are dropped, and s5 is never skipped while there is still a day before the end.

Hesitation pivot (branched shape): a user who reaches the paywall and hesitates (a dwell-time threshold with no action, tuned per product) is signalling that the ask arrived before the value case was made. Pivot in-session to a bounded, clearly labeled unlock of *one* pro feature (for example 24h), then return to the ask. Strictly once per trial, never repeatable; a decliner continues the standard sequence where they left off.

Post-expiry grace step (branched shape, `trial_end +2d`): one message within the grace window, built from what the user actually experienced. Activated non-converters hear about what they built and keep; non-activated users get a path to see the value, never a claim about value they never reached. One recovery window, then stop.

Discount rule: no discount inside the standard flow. If the business allows one, it belongs in the post-expiry step for activated non-converters only; discounting mid-trial teaches everyone to wait. Incentive choice follows the CLV-tied rule: above the account's CLV threshold prefer a value-add (extended trial of one feature, priority support, early access) over a discount; below it, a capped modest discount (see intake incentive policy).

## Timing and channel fit

- `trial_end`-anchored sends go at a fixed local time on their day (default 10:00 user local, market timezone when unknown) so "3 days before" is not read at 03:00. Push respects 22:00–09:00; email avoids 00:00–06:00 (see [consent-and-quiet-hours](../compliance/consent-and-quiet-hours.md)).
- Email carries anything with a date, a price or a policy: those must be findable later. In-app carries nudges and price-page follow-ups because the user is in the product. Push carries only the last call.
- No push consent → s6b goes by email. No email consent → s1, s3, s4 are skipped and s5 is shown in-app at the next session (expires at `trial_end`; the push s6b still goes where consented, since nothing waits on the in-app view); where a pre-expiry notice is legally required, it goes as a transactional notice, not through this journey.

## Frequency and overlap

- Worst path in a rolling 7 days, 14-day trial: s3b, s4, s5 = 3 emails + 1 push; compressed 7-day trial: s1, s3, s5 = 3 emails + 1 in-app + 1 push, inside the 4/week email cap; 3-day trial: 1 email + 1 in-app + 1 push.
- **Usual overlaps:** `welcome-onboarding` (signup and trial start coincide), `account-onboarding` (B2B trials), `activation`, `feature-adoption`, `payment-failure` (at conversion).
- **Precedence:** this journey owns the onboarding narrative for trialists: `welcome-onboarding` sends s1 at most, `activation` and `feature-adoption` do not run in parallel. With `account-onboarding`, deadline notices (s5, s6) never defer; that journey's digest moves instead.

## Measurement

- **Primary outcome:** `subscription_start` by `trial_end +7d`, incremental vs holdout. Secondary: share reaching core `feature_used` during the trial.
- **Design:** 10% random holdout at `trial_start`; the control receives none of s1–s6 (q1 too, when entry is freemium).
- **Routine communications both groups keep:** trial confirmation, billing receipts, and any legally required pre-renewal or expiry notice for auto-converting trials (sent transactionally to both groups, free of promotion).
- **Contamination:** in-product upgrade prompts and paywalls shown to everyone; sales outreach to trialists; app-store reminders outside your control.
- **Low volume:** with few trials per month, extend the read across several trial cohorts before deciding; below the sample-size floor, report "unmeasured", not "no effect".

## When data is missing

- **No `feature_used` or proxy:** run the simple shape with no decisions.
- **`feature_used` delayed or missing for a user:** d1/d2 take the unmeasurable route to the help track; help is wasted on few activated users, but the confident ask never reaches someone who saw no value.
- **`trial_end` not tracked:** compute it from `trial_start + trial_length` and mark the anchor as derived; extensions then cannot move the closing sends, so the journey doc flags that extended trials need the billing date before launch.
- **`paywall_view` missing:** d3 takes the unmeasurable route to s6b.
- **`subscription_start` arrives from the app store with a delay:** the before-each-send check can miss a fresh subscriber; state the latency and avoid sends within that delay after a purchase flow was opened.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Trial-to-paid conversion rate | primary | `subscription_start` within window / trials entered, incremental vs holdout |
| Activation rate during trial | secondary | share reaching core `feature_used`, the leading indicator the journey actually moves |
| Unsubscribe rate per send | guardrail | short trials concentrate sends; watch this harder than in any other pattern |

## Common mistakes

- Same sequence for activated and silent users. The conversion ask lands on people who never saw value, and the help content lands on people ready to buy.
- Ignoring the trial clock when scaling depth. An 8-step sequence in a 7-day trial breaches weekly caps by design.
- Timing by "trial midpoint" or by waits from the previous send. Anchor the closing sends to `trial_end`, or a trial extension leaves them landing on the wrong day.
- Hiding the expiry. Burying the end date produces refund requests and chargebacks instead of conversions; state date and price plainly.
- Repeating the countdown louder at a hesitating user instead of answering what is still unresolved for them.

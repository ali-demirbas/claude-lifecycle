---
name: gamified-rewards
stage: engagement
trigger_type: event
required_events: [game_played, reward_claimed]
optional_events: [purchase, game_impression, coupon_redeemed]
required_attributes: []
optional_attributes: [prize_id, reward_expiry_date, age_verified]
default_channels: [email, in_app, push]
base_steps: 2
depth_range: [1, 2]
applicable_industries: [ecommerce, marketplace, mobile-app, subscription-media, travel, edtech]
mutually_exclusive_with: []
journey_class: marketing
signal_sources: {game_played: behavioral, reward_claimed: authoritative, coupon_redeemed: authoritative, purchase: authoritative, reward_expiry_date: authoritative, age_verified: authoritative, game_impression: behavioral, consent_withdrawn: authoritative}
insufficient_alone:
  - a game_played hit without a reward record
  - an expiry date typed into a template rather than read from the reward record
  - a click on the play link
exit_before_each_send: [coupon_redeemed, purchase, consent_withdrawn]
reentry: {policy: once, on_duplicate_trigger: ignore}
measurement_default: holdout
instance_key: reward_id
---

# Gamified Rewards

A chance-based reward moment (spin-to-win, scratch card, pick-a-gift, mystery discount) run as a bounded campaign tied to a real occasion (seasonal peak, anniversary, a winback hook), never as a standing loop. The mechanic works because variable rewards are more compelling than fixed ones: experimentally shown (Shen, Fishbach & Hsee 2015, *Journal of Consumer Research*: uncertain rewards outperformed certain rewards of equal or higher value at motivating task completion). That is also exactly why this pattern carries harder guardrails than any other in the engine. Variable-ratio reinforcement is the same schedule that makes gambling habit-forming; the engine uses it sparingly and honestly or not at all.

**Not applicable to regulated sectors** (fintech, insurance, deliberately absent from `applicable_industries`): prize mechanics in regulated verticals attract both sector rules and promotional-lottery law simultaneously; the strictest-wins compliance chain resolves this to "don't."

## The honesty contract (all four hold, or the journey doesn't run)

1. **The draw is genuinely random over a real prize pool.** Predetermining the outcome per user or segment while displaying a spinning wheel is fabricated data in mechanic form (CLAUDE.md rule 3 applied to game mechanics). If every player receives the same reward, present it as a gift, not a game. If odds are stated anywhere, they are the actual odds.
2. **Every prize obeys the brand's incentive policy.** The prize table is checked against the discount cap and CLV-tied incentive rules from `knowledge/brands/<brand>.md` *before launch*. A wheel is not a loophole around the incentive ceiling, and a compliance-class breach here is a hard stop per CLAUDE.md rule 12.
3. **Legal review is assumed, not optional.** Promotional prize draws are regulated in many markets (free-entry requirements, disclosure rules, age limits, in some places outright licensing). The compliance file's standing disclaimer applies with extra force: confirm with counsel per market before launch. Copy for this pattern in any borderline case takes copy-reviewer's LEGAL verdict lane, and `age_verified` gating applies wherever minors could be in the audience.
4. **Won-reward deadlines are real and come from the record.** A claimed reward's `reward_expiry_date` is set at grant time in the reward record, and copy reads it from there. It may be stated plainly (honest urgency, the kind copy-reviewer's check 4 allows), but it is never typed into a template, estimated from "usual" validity, or shortened afterward to manufacture pressure. A reward with no expiry in its record gets no expiry sentence and no expiry reminder.

## Required-event signature

| Event | Source | Role |
|---|---|---|
| `game_played` | behavioral (product analytics, with `game_type`) | Opens the claim-nudge path when no claim follows; the campaign's engagement measure. |
| `reward_claimed` | authoritative (reward record, with `prize_id`) | Opens the reward path. Without claim tracking, prize cost and redemption are unmeasurable: pattern is **blocked**. |
| `purchase` / `coupon_redeemed` *(optional)* | authoritative (order / promotion system) | Redemption success exit: the only evidence the prize did revenue work rather than just costing margin. |
| `game_impression` *(optional)* | behavioral | Funnel diagnostics: invited → saw → played. |
| `reward_expiry_date` *(optional attr)* | authoritative (reward record) | Enables the one honest expiry reminder and the only expiry the copy may state. |
| `age_verified` *(optional attr)* | authoritative (account record) | Gate in markets that restrict prize mechanics by age. |

### Not enough on its own

- **A `game_played` hit without a reward record:** analytics shows a play, not a prize. Nothing about a won reward is said until the reward record exists.
- **An expiry date typed into a template rather than read from the reward record:** the date in copy must be the record's date for that user's reward; a campaign-wide "valid for 7 days" line is only true if the record says so.
- **A click on the play link:** interest, not participation. It doesn't count as a play and doesn't open any path.

## Entry / exit

- **Entry (by moment):**
  - *Invite*: campaign live, user in the campaign's target segment, marketing consent on ≥ 1 channel, `age_verified` where the market requires it, no gamified campaign participation in the current cap window.
  - *Reward path*: `reward_claimed` with a reward record.
  - *Claim nudge* (branched): `game_played` that produced a winnable prize with no `reward_claimed` within 24h.
- **Exclude:** minors and unverified-age users in gated markets, detractors and negative-signal-suppressed users ([consent-and-quiet-hours.md](../compliance/consent-and-quiet-hours.md) rule 4), users in dunning (a prize wheel next to a failed payment reads as mockery), sectors whose lexicon sets `regulated: true`.
- **Success exit:** `purchase`/`coupon_redeemed` containing the won reward · **Window:** the reward's real validity period from its record (default 14 days for measurement when the record has none).
- **Instance key:** `reward_id` on the reward path (the claim-nudge path uses the play's prize record). Redeeming another reward or another campaign's code does not stop this instance.
- **Checked before each send:** for this reward (`same_instance`): `coupon_redeemed`, `purchase` containing the reward; `consent_withdrawn` is channel-scoped (a push opt-out stops push steps, an email opt-out stops email steps). The won-reward message itself still goes out after a consent withdrawal only if the reward system treats it as the transactional delivery of the prize, with no promotional content.
- **Re-entry:** once per user per campaign, campaigns bounded (a few per year as a default posture, set in brand config), never a daily-spin cadence in CRM sends. A daily reward loop is a product-gamification decision with its own ethics review, not a lifecycle journey. A repeated trigger (second play, replayed claim event for the same reward) is ignored.
- **Handoffs:** a won reward that is a loyalty credit is confirmed by [loyalty](loyalty.md)'s reward confirmation, not twice; this pattern's won-reward send is then skipped.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (1) | DQS < 40 | Invite, then a single won-reward message with claim instructions. No expiry step without a real tracked expiry. |
| Standard (2) | DQS 40–69 | Reward path adds the one expiry reminder, gated on a recorded `reward_expiry_date`. |
| Branched (2) | DQS ≥ 70 + redemption events | Adds the played-not-claimed nudge path; splits claimed-and-redeemed (exits) from claimed-not-redeemed (expiry reminder); prize-tier-aware copy via `prize_id`. |

The step count is per path. Across one campaign a single user can receive at most the invite, a claim nudge or the won-reward message, and the expiry reminder.

## Step blueprint (standard, 2 sends)

| Node | When | Channel | Intent | Route |
|---|---|---|---|---|
| i1 | campaign_start +0d at 10:00 user_local | email or push | The invite: what the occasion is, what can be won, one deeplink to play. Odds and terms linked where law requires | → exit (completed); a play starts a later path |
| w1 | entry +1h | email | Reward path starts on `reward_claimed`: exactly what was won, how to use it, and its expiry only as stated in the reward record | → d1 |
| d1 | w1 +0h | — | Decision on `reward_expiry_date` (authoritative, reward record), evaluated at the decision moment (from = to = w1 +0h): is a recorded date at least 3 days ahead? It reads the date; it never waits for it | occurred → w2 · not_occurred → exit (completed) · unmeasurable → exit (completed) |
| w2 | reward_expiry_date -2d at 10:00 user_local | push or email | One expiry reminder: the recorded deadline, stated once. Deadline: reward_expiry_date -1d; quiet hours delay it at most to the last allowed time before that, and if the moment has already passed the reminder is dropped, not sent late | → exit (completed) |
| c0 | entry +24h | — | Claim-nudge path starts on `game_played`: decision on `reward_claimed` (authoritative) between entry and entry +24h | occurred → exit (completed; the reward path owns it) · not_occurred → c1 · unmeasurable → exit (completed) |
| c1 | c0 +0h | in_app (push where the product has no in-app surface) | One nudge that a won prize is waiting to be claimed, with the claim deeplink. In-app: shown at the next session, expires after 3d, then skipped. The channel is chosen at design time; no push is sent because the in-app view didn't happen | → exit (completed) |

Redemption is re-checked before w2, so "only if claimed but not redeemed" needs no separate decision.

## Timing and channel fit

- The invite goes at a calendar time on the user's clock, inside quiet hours per [consent-and-quiet-hours.md](../compliance/consent-and-quiet-hours.md); unknown timezone → market timezone.
- The won-reward message is near-immediate: the user is mid-experience and expects a record of what they won. Email carries it because it holds the code and terms.
- The expiry reminder fits push (short, one deadline) with email as fallback; it is calendar-anchored at 10:00 user_local two days before the recorded expiry.
- No consent on the chosen channel → the next consented channel in the order push > email; no marketing consent at all → no invite and no nudge (the won reward is still delivered in-product).

## Frequency and overlap

- **Worst case per campaign:** invite + won-reward + expiry reminder (3 sends, 2 of them in the same week). Inside default caps, but a campaign that coincides with a peak sale needs the portfolio review.
- **Overlaps:** seasonal campaigns, [loyalty](loyalty.md) (rewards credited as points), [winback](winback.md) (gamified hooks used as a winback opener), [anniversary](anniversary.md).
- **Precedence:** service and transactional sends first; an anniversary or birthday message that falls in the same week as the invite wins and the invite is deferred to the next send day. Never two prize mechanics in one week for one user.

## Measurement

- **Primary outcome:** incremental redemption (reward redeemed via `coupon_redeemed`/`purchase`) and net revenue within the reward's validity period.
- **Design:** user-level holdout (default 10%) assigned before the invite. The control receives no invite, no nudge and no reminder; it cannot play unless it finds the game organically, which is logged as contamination.
- **Routine communications both groups keep:** order and account service messages; regular newsletters continue for both.
- **Contamination risks:** the game promoted on-site or in social posts reaches the control; prizes shared between users.
- **Prize cost belongs in the iROI:** the prize pool is journey cost, and a campaign whose lift doesn't cover its prizes is a `kill` verdict in lifecycle-results regardless of how good the play rate looked.
- **Low volume:** a small campaign can show play rate and claim rate reliably; redemption lift needs enough control-arm volume for the expected effect (compute the power; see measurement.md), which bounded campaigns often don't reach. Report "unmeasured" rather than reading a small difference as success.

## When data is missing

- **No `reward_expiry_date` in the record:** no expiry sentence in any copy, no w2. Do not substitute a typical validity period.
- **No `prize_id`:** the won-reward message describes the prize from the reward record's own fields only; prize-tier copy is off.
- **`reward_claimed` delayed:** w1 waits for the record; it never goes out from the game's client-side result alone.
- **No `age_verified` in a market that requires it:** the user is not invited. Missing verification is an exclusion, not a pass.
- **No redemption events:** the journey can still run, but the primary KPI is unmeasurable; say so before launch.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Reward redemption rate | primary | redeemed within validity / rewards claimed, incremental vs holdout per [measurement.md](../measurement.md). An unredeemed prize is pure cost |
| Play rate | secondary | `game_played` / invites delivered: the engagement half of the funnel |
| Unsubscribe + complaint rate per send | guardrail | gimmick fatigue shows up here first; a complaint spike triggers the portfolio-wide negative-signal override |

## Common mistakes

- Rigged randomness: a predetermined outcome dressed as chance is the pattern's cardinal sin; it converts a marketing campaign into something a regulator and a journalist both recognize.
- Prizes exceeding the brand's incentive cap because "the wheel awarded it": the prize table is bounded by the same policy as every other incentive.
- Launching in a regulated market without counsel sign-off, or without a free-entry route where the law requires one.
- Running it as a standing daily/weekly loop in CRM sends: habituation is the failure mode, not the goal; occasion-bounded or not at all.
- Stating an expiry the record doesn't hold, or shortening a won reward's validity after grant to force redemption: manufactured urgency on top of a real grant poisons the pattern's one honest deadline.
- Sending a late expiry reminder after the reminder moment has passed: it arrives too close to the deadline to act on and reads as pressure.
- Measuring success by plays instead of incremental redemptions: plays are cheap fun; the journey exists only if redemption lift covers prize cost.

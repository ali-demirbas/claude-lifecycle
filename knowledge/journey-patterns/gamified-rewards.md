---
name: gamified-rewards
stage: engagement
trigger_type: event
required_events: [game_played, reward_claimed]
optional_events: [purchase, game_impression, coupon_redeemed]
required_attributes: []
optional_attributes: [prize_id, reward_expiry_date, age_verified]
default_channels: [email, in-app, push]
base_steps: 3
depth_range: [2, 4]
applicable_industries: [ecommerce, marketplace, mobile-app, subscription-media, travel, edtech]
---

# Gamified Rewards

A chance-based reward moment — spin-to-win, scratch card, pick-a-gift, mystery discount — run as a bounded campaign tied to a real occasion (seasonal peak, anniversary, a winback hook), never as a standing loop. The mechanic works because variable rewards are more compelling than fixed ones — experimentally shown (Shen, Fishbach & Hsee 2015, *Journal of Consumer Research*: uncertain rewards outperformed certain rewards of equal or higher value at motivating task completion); that is also exactly why this pattern carries harder guardrails than any other in the engine. Variable-ratio reinforcement is the same schedule that makes gambling habit-forming — the engine uses it sparingly and honestly or not at all.

**Not applicable to regulated sectors** (fintech, insurance — deliberately absent from `applicable_industries`): prize mechanics in regulated verticals attract both sector rules and promotional-lottery law simultaneously; the strictest-wins compliance chain resolves this to "don't."

## The honesty contract (all four hold, or the journey doesn't run)

1. **The draw is genuinely random over a real prize pool.** Predetermining the outcome per user or segment while displaying a spinning wheel is fabricated data in mechanic form (CLAUDE.md rule 3 applied to game mechanics). If every player receives the same reward, present it as a gift, not a game. If odds are stated anywhere, they are the actual odds.
2. **Every prize obeys the brand's incentive policy.** The prize table is checked against the discount cap and CLV-tied incentive rules from `knowledge/brands/<brand>.md` *before launch* — a wheel is not a loophole around the incentive ceiling, and a compliance-class breach here is a hard stop per CLAUDE.md rule 12.
3. **Legal review is assumed, not optional.** Promotional prize draws are regulated in many markets (free-entry requirements, disclosure rules, age limits, in some places outright licensing). The compliance file's standing disclaimer applies with extra force: confirm with counsel per market before launch. Copy for this pattern in any borderline case takes copy-reviewer's LEGAL verdict lane, and `age_verified` gating applies wherever minors could be in the audience.
4. **Won-reward deadlines are real.** A claimed reward's `reward_expiry_date` is a genuine deadline and may be stated plainly (that's honest urgency, the kind check 4 in copy-reviewer allows) — but the expiry is set at grant time and never shortened afterward to manufacture pressure.

## Required-event signature

| Event | Role |
|---|---|
| `game_played` | Trigger for the post-play sequence (custom, with `game_type` param). Also the campaign's engagement measure. |
| `reward_claimed` | The branch point (custom, with `prize_id` param). Without claim tracking, prize cost and redemption are unmeasurable — pattern is **blocked**. |
| `purchase` / `coupon_redeemed` *(optional)* | Redemption success exit — the only evidence the prize did revenue work rather than just costing margin. |
| `game_impression` *(optional)* | Funnel diagnostics: invited → saw → played. |
| `reward_expiry_date` *(optional attr)* | Enables the one honest expiry reminder. |

## Entry / exit

- **Entry:** campaign live, user in the campaign's target segment, marketing consent on ≥ 1 channel, `age_verified` where the market requires it, no gamified campaign participation in the current cap window.
- **Exclude:** minors and unverified-age users in gated markets, detractors and negative-signal-suppressed users, users in dunning (a prize wheel next to a failed payment reads as mockery), sectors whose lexicon sets `regulated: true`.
- **Success exit:** `purchase`/`coupon_redeemed` containing the won reward · **Window:** the reward's real validity period · **Re-entry:** hard habituation cap — once per user per campaign, campaigns bounded (a few per year as a default posture, set in brand config), never a daily-spin cadence in CRM sends. A daily reward loop is a product-gamification decision with its own ethics review, not a lifecycle journey.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (2) | DQS < 40 | Invite → play → reward message with claim instructions. No expiry step without a real tracked expiry. |
| Standard (3) | DQS 40–69 | Adds the one expiry reminder gated on `reward_expiry_date`, and a played-but-not-claimed nudge. |
| Branched (4) | DQS ≥ 70 + redemption events | Splits claimed-and-redeemed (thank-you, exits) from claimed-not-redeemed (expiry reminder) from played-not-claimed (claim nudge); prize-tier-aware copy via `prize_id`. |

## Step blueprint (standard, 3 steps)

| # | Wait | Channel | Intent | Branch |
|---|------|---------|--------|--------|
| 1 | at campaign start (or the occasion trigger) | email or push | The invite: what the occasion is, what can be won, one deeplink to play. Odds/terms linked where law requires | — |
| 2 | ≤ 1h after `reward_claimed` | email | The won reward: exactly what it is, how to use it, the real expiry date | if `reward_claimed` |
| 3 | at `reward_expiry_date` − 48h | push or email | One expiry reminder — real deadline, stated once | if claimed but not redeemed |

## KPIs

| KPI | Type | Note |
|---|---|---|
| Reward redemption rate | primary | redeemed within validity / rewards claimed — an unredeemed prize is pure cost; measure incrementally vs holdout per [measurement.md](../measurement.md) |
| Play rate | secondary | `game_played` / invites delivered — the engagement half of the funnel |
| Unsubscribe + complaint rate per send | guardrail | gimmick fatigue shows up here first; a complaint spike triggers the portfolio-wide negative-signal override |

Prize cost per incremental conversion belongs in the iROI calculation: the prize pool is journey cost, and a campaign whose lift doesn't cover its prizes is a `kill` verdict in lifecycle-results regardless of how good the play rate looked.

## Common mistakes

- Rigged randomness — a predetermined outcome dressed as chance is the pattern's cardinal sin; it converts a marketing campaign into something a regulator and a journalist both recognize.
- Prizes exceeding the brand's incentive cap because "the wheel awarded it" — the prize table is bounded by the same policy as every other incentive.
- Launching in a regulated market without counsel sign-off, or without a free-entry route where the law requires one.
- Running it as a standing daily/weekly loop in CRM sends — habituation is the failure mode, not the goal; occasion-bounded or not at all.
- Shortening a won reward's validity after grant to force redemption — manufactured urgency on top of a real grant poisons the pattern's one honest deadline.
- Measuring success by plays instead of incremental redemptions — plays are cheap fun; the journey exists only if redemption lift covers prize cost.

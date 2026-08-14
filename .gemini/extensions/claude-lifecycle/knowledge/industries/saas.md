---
name: saas
display_name: SaaS (B2B & B2C subscription software)
funnel: [session_start, sign_up, trial_start, feature_used, subscription_start]
conversion_events: [subscription_start]
activation_definition: Used a core feature (`feature_used` with the product's designated core `feature` param) at least once within 7 days of trial_start.
churn_signal: Login/usage frequency drops below 50% of the account's own trailing 30-day baseline, or no login for 14 days on a paid plan.
pattern_priorities:
  welcome-onboarding: P0
  trial-conversion: P0
  activation: P0
  payment-failure: P0
  churn-prevention: P0
  account-onboarding: P1
  feature-adoption: P1
  upsell-cross-sell: P1
  winback: P1
  feedback-nps: P1
  progressive-profiling: P1
  milestone: P2
  referral: P2
  reactivation: P2
  anniversary: P2
  channel-opt-in: P2
  lead-nurture: P1
typical_channels: [email, in_app, push]
---

# SaaS Playbook

Low purchase frequency, long relationship: one conversion decision (trial → paid) followed by months or years of retention economics. The decision cycle runs days to weeks for B2C and self-serve B2B, weeks to months when procurement is involved. Nearly all lifecycle value sits in two windows — the first 7 days of a trial (activation) and the recurring billing moment (payment failure, renewal) — plus expansion via seats and plan upgrades on accounts that are already succeeding. Email carries the sequences; in-app messages carry the product guidance; push is marginal outside mobile-first B2C tools.

## Canonical funnel

| Step | Expected event | Notes |
|---|---|---|
| Visit | `session_start` | |
| Account created | `sign_up` | Should carry signup source/plan-intent params |
| Trial begins | `trial_start` | Often same moment as sign_up; keep both events distinct |
| First value moment | `feature_used` (core feature) | Biggest drop-off is sign_up → first core action; this gap decides trial outcome |
| Paid conversion | `subscription_start` | Must carry `plan`, `value`, `currency`; recurring `purchase` acceptable alias |
| Expansion | `subscription_start` (plan change) or seat-count attribute change | Feeds upsell-cross-sell |

## Event expectations

**Must-have** (missing any of these blocks P0 journeys): `sign_up`, `trial_start`, `feature_used` (with `feature` param), `subscription_start`, `payment_failed`.
**Nice-to-have** (unlocks depth/branches): `trial_end`, `subscription_cancel`, `login`, `invite_sent`/`invite_accepted`, plan/seat-count attributes, `feature_used` per-feature breakdown, session frequency, `generate_lead` (sales-assisted motion).

## Pattern priorities — rationale

- **welcome-onboarding P0** — the sign_up → first-core-action gap is where most trials die; onboarding is the sector's abandoned cart.
- **trial-conversion P0** — the single revenue decision of the entire lifecycle; sequences keyed to trial_end are non-negotiable.
- **activation P0** — activated trials convert at a multiple of non-activated ones; every other journey inherits from whether this one worked.
- **payment-failure P0** — involuntary churn (expired/declined cards) is silent recurring-revenue loss that dunning recovers at low effort; no persuasion needed, just logistics.
- **churn-prevention P0** — usage decline is measurable weeks before cancel; catching it pre-cancel is far cheaper than winback. Downgrade to high P1 only if the product has annual-only contracts with sales-led renewals.
- **account-onboarding P1** — applies only to multi-seat B2B accounts with a usable role map (`account_id` + `user_role`); where it applies it supersedes person-level welcome-onboarding, and it promotes to P0 for sales-assisted B2B motions. See [account-onboarding](../journey-patterns/account-onboarding.md).
- **feature-adoption P1** — breadth of feature use correlates with retention; promote to P0 for multi-module products.
- **upsell-cross-sell P1** — seat and plan expansion; gate on health (never upsell a struggling account).
- **progressive-profiling P1 (promoted from the usual P2)** — the role map (economic buyer vs technical stakeholder vs end-user, see Multi-stakeholder accounts below) is a hard dependency for role-differentiated journeys, and it is rarely captured at signup; see [progressive-profiling](../journey-patterns/progressive-profiling.md).
- **abandoned-cart, browse-abandonment — not applicable** (no cart; the "abandonment" analog is an unfinished signup or stalled trial, which welcome-onboarding and trial-conversion own).
- **replenishment, back-in-stock, price-drop, post-purchase — not applicable** (no consumable inventory, no stock, no per-order lifecycle; post-conversion care is handled by welcome-onboarding on the paid plan and feature-adoption).

- **lead-nurture P1** — B2B buyers research for weeks before a trial; a captured lead (webinar, gated guide, pricing form) needs problem/solution education until `trial_start`, and welcome-onboarding cannot absorb them (no product usage exists yet to onboard).

## Sector-specific timing & cadence

- Welcome email: within minutes of `sign_up` (transactional-adjacent); first behavioral nudge at 24h if no core action.
- Activation window: days 1–7 of trial; front-load — a trial silent for its first 3 days rarely recovers.
- Trial-conversion sequence: anchor to `trial_end` minus 7/3/1 days, not to trial_start; one post-expiry grace touch.
- Payment failure: first retry notice within hours; dunning sequence over 7–14 days before access change.
- Churn-prevention: evaluate usage weekly; intervene within days of a sustained drop, not at renewal time.
- B2B rhythm: send Tue–Thu working hours in the account's timezone; avoid Mondays and weekends.

## Seasonality

- B2B buying follows **fiscal and budget cycles**: quarter-ends and fiscal-year boundaries concentrate both new purchase decisions and use-it-or-lose-it budget — time trial-conversion and expansion framing to the account's cycle where known, not the calendar year by default.
- **Renewals cluster per customer**, not per season: each account's renewal anniversary is its own high-stakes window; renewal-adjacent journeys anchor to contract dates, not campaign calendars.
- Summer and end-of-December are decision dead zones for many B2B markets — expect slower trial engagement and plan grace touches accordingly rather than escalating.
- Seasonal windows modify existing journeys (timing, framing) — they are not a separate journey type. During elevated-intent windows attributed numbers inflate with the baseline; holdouts matter more (see [measurement](../measurement.md)).

## Segmentation attributes that matter

Plan tier and billing period (monthly vs annual), seat count / team size, trial status (in trial, expired-unconverted, paid), activation state (core action done or not), usage trend vs own baseline, role (admin vs invited member — admins get billing and expansion messaging, members get feature guidance).

## Multi-stakeholder accounts

In B2B, one signup often represents several people with different jobs to do, and a single undifferentiated path serves none of them:

- **Economic buyer** — cares about ROI and rollout risk; gets lighter-touch, outcome-framed messaging, not feature tours.
- **Technical stakeholder** — their "aha" is a completed integration or setup working end-to-end, not the end-user workflow moment; onboarding for them is setup/integration confidence.
- **End-user** — the classic workflow aha; standard activation messaging applies.

Capture role at signup where possible, or infer it from invite type / seat assignment (the inviter is usually admin/buyer-side, invitees are usually end-users). A missing role map is a named data gap — make it a [progressive-profiling](../journey-patterns/progressive-profiling.md) target, not a silent assumption. The pattern implementing this role fan-out is [account-onboarding](../journey-patterns/account-onboarding.md).

Account-level churn signals that per-contact metrics cannot see:

- **Seat/license utilization dropping** — the fix is nudging the *admin* to drive adoption, not messaging inactive end-users directly.
- **Champion turnover** — the internal advocate leaves; visible only in account/role continuity, and the single most common silent killer of renewals.
- **Renewal proximity without an expansion signal** — flat usage approaching a renewal date is a risk state even when nothing "dropped".

Renewal-critical accounts that don't respond to digital reinforcement escalate to a **human** (a CSM task in the journey), not to a louder message.

## Intake questions (sector-specific)

1. What is your "aha" action — the one event that best predicts a trial converting — and is it instrumented as `feature_used` (or equivalent)?
2. Trial model: opt-in free trial, freemium, or credit-card-required trial? How long is the trial?
3. Self-serve, sales-assisted, or both? (Sales-assisted accounts need journey suppression when an owner is active.)
4. Is billing state (payment failed, card expiring, renewal date) available to the CRM tool as events or attributes?
5. Is expansion driven by seats, usage limits, or plan features — and which of those do you track per account?
6. Who is in the account besides the end-user — do you know each contact's role (buyer, technical, end-user, admin), and is seat/role structure available to the messaging tool?

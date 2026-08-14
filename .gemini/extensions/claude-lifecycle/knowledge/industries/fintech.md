---
name: fintech
display_name: Fintech (banking, trading, payments apps)
funnel: [session_start, sign_up, kyc_complete, first_deposit, first_transaction]
conversion_events: [first_deposit, first_transaction]
activation_definition: kyc_complete within 7 days of sign_up (a signed-up but unverified user cannot transact and is not yet a customer).
churn_signal: KYC started but not completed within 72 hours, or no session for 30 days after funding; a full balance withdrawal is a hard churn signal.
pattern_priorities:
  welcome-onboarding: P0
  activation: P0
  churn-prevention: P0
  payment-failure: P1
  reactivation: P1
  winback: P1
  feature-adoption: P1
  progressive-profiling: P2
  milestone: P2
  referral: P2
  feedback-nps: P2
  upsell-cross-sell: P2
  anniversary: P2
  loyalty: P2
  channel-opt-in: P2
  lead-nurture: P2
typical_channels: [email, push, sms]
---

# Fintech Playbook

Trust-critical and regulator-watched: the product holds people's money, so every lifecycle message is also a compliance artifact. The funnel has a hard gate no other sector has — KYC/identity verification — and most acquisition spend dies there: users sign up in minutes, then stall on document upload and never return. Lifecycle value therefore concentrates on getting users *through* KYC and to a first deposit or transaction within days of signup, then on keeping funded accounts active. Marketing and transactional messaging must stay strictly separated: security alerts, transaction confirmations, and regulatory notices are untouchable transactional traffic, and promotional copy must never impersonate them. Anything that could be read as investment advice or a promise of returns is off-limits by default (see the fintech lexicon).

## Canonical funnel

| Step | Expected event | Notes |
|---|---|---|
| Visit | `session_start` | |
| Account created | `sign_up` | Cheap and fast; not a customer yet |
| Identity verified | `kyc_complete` | Activation gate; biggest drop-off is sign_up → kyc_complete (document friction) |
| Account funded | `first_deposit` | First revenue event; should carry `value`, `currency` |
| First use | `first_transaction` | Trade, transfer, payment, or card use — the product's core action |
| Habitual use | recurring transaction / `feature_used` | Recurring deposits or standing orders are the strongest retention signal |

Instrument KYC as staged events where possible (`kyc_start`, document submitted, `kyc_complete`) — the rescue journey needs to know *where* the user stalled.

## Event expectations

**Must-have** (missing any of these blocks P0 journeys): `sign_up`, `kyc_complete`, `first_deposit` or `first_transaction` (at least one true revenue event).
**Nice-to-have** (unlocks depth/branches): `kyc_start` and per-step KYC events with failure reasons, `login`, transaction events with `value`, balance-tier attribute, recurring-deposit flag, `payment_failed` (card/top-up declines), withdrawal events, product-holding attributes (card, savings, investment module), `app_remove`.

## Pattern priorities — rationale

- **welcome-onboarding P0** — here this *is* KYC-completion rescue: a staged sequence that unblocks stalled verification (what document, why it failed, how to retry) recovers users who cost real acquisition money and are otherwise lost within days.
- **activation P0** — a verified-but-unfunded account earns nothing; the kyc_complete → first_deposit bridge is the sector's highest-leverage journey after KYC itself.
- **churn-prevention P0** — dormancy in a finance app is quiet and sticky (money parked, app forgotten); usage-decline detection on funded accounts protects the entire revenue base, and a balance withdrawal must trigger immediate (careful, non-desperate) attention.
- **payment-failure P1, contextually P0** — applies where recurring money movement exists: failed top-ups, failed recurring deposits, subscription-fee declines. Promote to P0 for any product with recurring billing or scheduled deposits; leave P1 for pure trading apps.
- **feature-adoption P1** — multi-product breadth (card + savings + investments) is fintech's retention moat; adoption messaging must stay educational, never advisory.
- **winback / reactivation P1** — lapsed funded users still hold trust (and often a balance); reactivation is high-value but must not lean on urgency or market-timing pressure.
- **referral P2** — powerful in fintech but usually incentive-driven and heavily compliance-reviewed; keep P2 until legal sign-off on the mechanic exists.
- **upsell-cross-sell P2** — cross-selling regulated products (credit, investments) carries suitability obligations in many jurisdictions; require explicit compliance approval before any journey ships.
- **trial-conversion — not applicable** (no trial model; account tiers are handled by feature-adoption/upsell).
- **abandoned-cart, browse-abandonment, replenishment, back-in-stock, price-drop, post-purchase — not applicable** (no cart, catalog, or inventory; and a "price-drop" analog on market assets would constitute investment prompting — explicitly forbidden).

## Sector-specific timing & cadence

- KYC rescue: first nudge within 2–24 hours of a stalled verification, while documents are still at hand; sequence over 3–7 days, then park.
- Verified → funded: first deposit prompt within 24 hours of `kyc_complete`; keep it about capability ("your account is ready"), never about market opportunity.
- Overall frequency: conservative — fewer, heavier messages than any other sector; a finance app that notifies like a game gets uninstalled *and* distrusted.
- Never send marketing adjacent in time to a security or transaction alert; give transactional messages clear air.
- No market-event-triggered promotional sends (volatility, price moves) — that is prompting investment behavior.
- Quiet hours strictly enforced; money messages at 2am read as fraud alerts.

## Seasonality

- **Salary cycles** set the monthly rhythm: deposits, savings top-ups, and bill payments cluster around payday — deposit and savings nudges timed to the user's own salary pattern land better than calendar blasts.
- **Tax season** is a legitimate, high-relevance service window (statements, deduction summaries, filing reminders) — service framing only, never a promo hook.
- **Market events are NOT a seasonal opportunity**: volatility, rallies, and crashes must never trigger promotional sends — that is prompting investment behavior (see timing rules above and the lexicon). This is the sector's hard exception to "seasonal moments modify journeys".
- New-year financial resolutions and fiscal-year boundaries are usable for savings/budgeting features, with the brand-fit and compliance filters applied first. Elevated-baseline windows inflate attributed numbers; holdouts matter more (see [measurement](../measurement.md)).

## Segmentation attributes that matter

KYC state (not-started / stalled-at-step / complete), funded vs unfunded, balance tier, product holdings (card, savings, investment, credit), transaction recency and frequency, recurring-deposit flag, risk/suitability classification where the product is regulated (gates which journeys a user may enter at all).

## Intake questions (sector-specific)

1. Which regulator(s) and marketing rules apply to you (e.g. SPK/BDDK in Turkey, or your market's equivalents), and does compliance review lifecycle copy before send?
2. Where exactly do users stall in KYC — do you have per-step events and failure reasons (blurry document, mismatch, manual review)?
3. What counts as your core "first transaction" — deposit, trade, transfer, card payment — and is it instrumented with value?
4. Are financial incentives (deposit bonuses, referral rewards, fee waivers) permitted for you, and under what conditions?
5. Which message categories are locked as transactional-only in your stack (security, statements, regulatory), so journeys never touch or imitate them?

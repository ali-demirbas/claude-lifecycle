---
name: insurance
display_name: Insurance (motor, health, home, travel, SME lines)
funnel: [quote_started, policy_purchased, app_activated, claim_filed, policy_renewed]
conversion_events: [policy_purchased, policy_renewed]
activation_definition: app_activated or portal_registered within 14 days of policy_purchased (a policyholder who never opens the app/portal has no claims-readiness and no cross-sell surface).
churn_signal: no re-engagement (app/portal login, email open) inside the 45 days before policy expiry, or a claim closed without a satisfaction follow-up.
pattern_priorities:
  welcome-onboarding: P0
  abandoned-cart: P0
  payment-failure: P0
  churn-prevention: P0
  winback: P1
  upsell-cross-sell: P1
  feedback-nps: P1
  loyalty: P2
  milestone: P2
  referral: P2
  progressive-profiling: P2
  feature-adoption: P2
  account-onboarding: P2
  channel-opt-in: P2
  lead-nurture: P2
  care-alert: P2
typical_channels: [email, sms, push, whatsapp]
---

# Insurance Playbook

A relationship built on two moments that matter far more than any other touchpoint: the **quote-to-purchase decision** (once a year or less, often price-driven and comparison-shopped) and the **claim** (rare, high-stakes, and the single biggest driver of renewal or defection — a well-handled claim converts a price-shopper into a loyal renewer; a badly-handled one loses them regardless of price next year). Between those two moments the relationship is mostly dormant: an annual policy generates almost no natural reason to open an email. Lifecycle marketing therefore concentrates on three windows — closing the purchase once a quote exists, keeping the policyholder claims-ready and premium-current during the term, and running a proactive multi-touch campaign ahead of the renewal date, which is this sector's single highest-value recurring journey (the closest analogue to a subscription business's entire retention program, compressed into a 4-6 week annual window). Cross-sell matters more here than in most sectors because a single household plausibly needs 3-6 distinct policies (motor, home, health, travel, contents, pet) and rarely holds them all with one insurer.

## Canonical funnel

| Step | Expected event | Notes |
|---|---|---|
| Quote started | `quote_started` | Comparison-shopping is the norm; price is compared across 3+ insurers in one sitting |
| Policy purchased | `policy_purchased` | True conversion event; should carry `value` (premium), `product_line`, `payment_plan` (peşin/taksit) |
| App/portal activated | `app_activated` or `portal_registered` | The claims-readiness and cross-sell gate; a policyholder who never registers is invisible to every journey after this one |
| Claim filed | `claim_filed` | The moment of truth; should carry `product_line`, `channel` (app/WhatsApp/call center) |
| Claim resolved | `claim_resolved` | Should carry `outcome` (paid/partial/rejected) — outcome drives the entire post-claim tone |
| Renewal due | `policy_renewal_due` (attribute: `renewal_date`) | Time-based, not behavioral; the funnel step every other sector lacks an equivalent of |
| Renewed / lapsed | `policy_renewed` / `policy_lapsed` | The annual conversion event; `policy_lapsed` without a new purchase elsewhere is the sector's core churn definition |

## Event expectations

**Must-have** (missing any of these blocks P0 journeys): `quote_started`, `policy_purchased` with `value`/`product_line`, `renewal_date` attribute.
**Nice-to-have** (unlocks depth/branches): `app_activated`/`portal_registered`, `claim_filed` + `claim_resolved` with `outcome`, `premium_payment_failed`/`premium_payment_succeeded` with `failure_reason` and `payment_plan`, `policy_renewed`/`policy_lapsed`, product-holding attributes (which lines a household already has — the cross-sell candidate list), `no_claims_years` (bonus/discount eligibility), NPS/CSAT response tied to a specific claim.

## Pattern priorities — rationale

- **welcome-onboarding P0** — here this is policy activation: confirm coverage, get the app/portal registered (must-have for every later journey), and teach "how to file a claim" *before* it's needed — a policyholder who has to search for this mid-emergency has a worse claims experience regardless of how the claim itself goes.
- **abandoned-cart P0** — repurposed as **quote abandonment**: a completed quote with no purchase is proven, priced intent (the user already knows the premium) — structurally identical to a commerce cart, and typically the single highest-ROI recoverable moment in the funnel, same as in commerce.
- **payment-failure P0** — installment premium plans (a near-universal product feature in this sector) create a real involuntary-churn risk: a failed card payment silently lapses coverage the policyholder believes is still active. This is transactional, urgent, and protects revenue already sold — promote to P0 for any insurer offering installment/taksitli payment plans (nearly all do).
- **churn-prevention P0** — repurposed as **pre-renewal retention**: annual policies do not "decline" the way a SaaS login trend does, so the trigger is `renewal_date` proximity (the pattern already lists `renewal_date` as an optional attribute for exactly this reason), not usage decay. This is the sector's single most important recurring revenue journey — treat it as the anchor of the whole program, not a garnish.
- **winback P1** — lapsed (non-renewed) policyholders remain a warm audience for 60-90 days; win them back before they've re-shopped and bought elsewhere for the year.
- **upsell-cross-sell P1** — a household holding one line (commonly mandatory traffic/motor) is a strong candidate for adjacent lines (home, health, travel, pet); the health gate matters doubly here — never cross-sell to a policyholder with an unresolved or rejected claim. Policy-record changes are the sector's strongest cross-sell triggers: an address change (home/contents), a new dependent on a health policy (life/education lines) — first-party, observed, and far more timely than behavioral signals.
- **feedback-nps P1, contextually P0** — promote to P0 immediately after any `claim_resolved` event; post-claim sentiment is the strongest available renewal predictor in the sector and a rejected-claim detractor needs human recovery before the next renewal touch, not a survey link.
- **loyalty P2** — no-claims-bonus/discount recognition and multi-year tenure acknowledgment; real goodwill value but never the anchor of the program.
- **milestone P2** — claim-free anniversaries, N years insured.
- **referral P2** — works well in insurance (trust transfers from someone you know) but keep P2 until an approved referral mechanic and compliance sign-off exist.
- **progressive-profiling P2** — household composition, vehicle/property details, and existing coverage elsewhere are exactly what improves cross-sell targeting over time.
- **feature-adoption P2** — app capabilities beyond the core claim flow (location-based services, digital assistant); useful but secondary to claims-readiness itself.
- **account-onboarding P2** — for corporate/SME lines (fleet, business package) where a company account has multiple seats/users; runs instead of welcome-onboarding for those accounts, same supersession rule as other sectors.
- **anniversary — folded into churn-prevention.** A generic "happy anniversary" goodwill touch is real but secondary; the renewal-date journey already owns the calendar moment that matters, so don't run both against the same date.
- **trial-conversion — not applicable** (no trial model; a quote is priced intent, not product trial).
- **browse-abandonment, back-in-stock, price-drop, replenishment — not applicable** (no catalog, inventory, or repeat-purchase-of-the-same-item concept; a "price-drop" analog on a live premium would also risk misrepresenting the actual underwriting quote).

- **care-alert P2** — weather-peril warnings to affected policyholders (hail → kasko holders in the province) are the sector's highest-trust message class; requires an official feed integration and the zero-sell contract, so P2 until the feed exists.

## Sector-specific timing & cadence

- Quote abandonment: first touch within 1-4 hours (the quoted premium is usually still valid), sequence over 3-5 days — a lapsed quote often needs re-quoting after that, which changes the message entirely.
- Pre-renewal: begin 45 days before `renewal_date`, escalate at 30/15/7/1 days; this is the one journey in the whole portfolio allowed a real, non-fake deadline (the policy genuinely expires on a fixed date). Open the sequence with a delivered-value recap computed from the account's real data — claims paid, assistance used, coverage period — before any renewal ask; if that data isn't available, skip the recap entirely rather than estimating it (CLAUDE.md rule 3).
- Post-claim NPS: send 3-5 days after `claim_resolved` — immediately reads as premature relief-seeking; too late loses the moment.
- Payment recovery: first notice within hours of `premium_payment_failed`, full sequence must complete before the grace period (typically 15-30 days per product/regulation) ends or coverage genuinely lapses.
- Overall frequency: sparse outside the renewal window — an annual-purchase relationship that emails weekly reads as spam, not engagement; concentrate volume into the windows above.
- Never send marketing adjacent to an open claim; a cross-sell email arriving while a claim is under review reads as tone-deaf at best.

## Seasonality

- **Renewal date is per-policyholder, not calendar-wide** — this sector's seasonality is a rolling, individual clock rather than a shared retail calendar; the pre-renewal journey's entry condition *is* the seasonal trigger.
- **Weather/disaster-adjacent moments** (earthquake anniversaries, flood/storm season, winter-tire season for motor) are legitimate service-relevant windows for home/DASK/motor content — framed as preparedness, never as fear-based urgency (see lexicon).
- **New-driver / new-homeowner life moments** are acquisition-adjacent, not lifecycle-adjacent, and out of scope for this engine's journeys.
- Elevated claim-filing periods (storm events, earthquake aftermath) inflate near-term engagement numbers for reasons unrelated to any journey's own performance — treat any metric read during such a window as contaminated and wait for a normal-period baseline.

## Segmentation attributes that matter

Product-line holdings (which of the household's plausible lines are already covered — the cross-sell map), payment plan (peşin/taksit — installment holders carry payment-failure risk that annual-paid holders don't), days-to-renewal, claims history (count, recency, outcome), no-claims-bonus tier, app/portal activation status, channel consent per product line (a household can hold multiple policies with different consent states).

## Intake questions (sector-specific)

1. Which product lines do you sell, and does a single household commonly hold more than one (the cross-sell map depends on this)?
2. What share of premiums are paid by installment vs in full, and does a failed installment payment reach the CRM as an event today, or only the payment processor?
3. Is claim outcome (paid/partial/rejected) captured anywhere accessible to marketing/CRM, or does it live only in the claims system?
4. What is your renewal grace period and lapse policy (does coverage end exactly on the renewal date, or is there a grace window)?
5. Which regulator's marketing/conduct rules apply (e.g. SEDDK in Türkiye), and does compliance/legal review lifecycle copy before send?

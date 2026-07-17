# Tracking Plan — Parapuan

**Generated:** 2026-07-12 · **Current DQS:** 0/100 · **Projected DQS if implemented:** ≈ 68 before volume is measured (P0 items alone ≈ 51); volume adds 3–15 more once real conversion counts exist — it cannot be projected honestly from zero data.

Naming follows GA4 recommended events where one exists ([ga4-recommended-events.md](../../knowledge/event-taxonomy/ga4-recommended-events.md)); otherwise `snake_case`, verb-first, ≤ 40 chars. Funnel per the [fintech playbook](../../knowledge/industries/fintech.md): `session_start` → `sign_up` → `kyc_complete` → `first_deposit` → `first_transaction`.

## 1. Missing events (required)

| Priority | Event to add | Suggested GA4 name | Parameters | Unlocks |
|---|---|---|---|---|
| P0 | Account created | `sign_up` | `method: string` | Trigger for `fin-welcome-onboarding-01` — without it the CRM cannot even start the P0 journey |
| P0 | KYC started | `kyc_start` | — | Stall detection: distinguishes "never started" from "stalled mid-flow" in KYC Rescue |
| P0 | KYC step completed / failed | `kyc_step_completed` | `step: string`, `failure_reason: string` | Upgrades KYC Rescue steps 3–4 from generic tips to stall-specific rescue (the playbook's headline recommendation); +funnel completeness |
| P0 | Identity verified | `kyc_complete` | — | Success exit of `fin-welcome-onboarding-01`; trigger of `fin-activation-01` |
| P0 | First deposit | `first_deposit` | `value: number`, `currency: string` | Success exit + revenue KPI of `fin-activation-01` (hard launch precondition); the conversion-events DQS component moves off zero |
| P0 | App session / login | `login` | — | Dormancy segments for `fin-churn-prevention-01` and `fin-reactivation-01`; recency signal for everything |
| P1 | First core transaction | `first_transaction` | `type: string`, `value: number`, `currency: string` | Second conversion type → conversion component toward the 19–25 band; completes the canonical funnel |
| P1 | Recurring deposit executed | `deposit` | `value: number`, `currency: string`, `recurring: boolean` | Retention's strongest signal (playbook); future milestone/habit journeys |
| P1 | Top-up / recurring payment failed | `payment_failed` | `failure_reason: string` | Unblocks `fin-payment-failure-01` — promoted to P0 the day this event exists (recurring deposits make dunning recovered revenue) |
| P1 | Withdrawal | `withdrawal` | `value: number`, `currency: string`, `full_balance: boolean` | Hard-churn exclusion in Dormancy Save actually fires; full-balance flag triggers careful attention per playbook |
| P2 | Feature used | `feature_used` | `feature: string` | Unblocks `fin-feature-adoption-01` (card/goals/round-up breadth — fintech's retention moat) |
| P2 | App removed | `app_remove` | — | Channel viability split in `fin-reactivation-01` (dead push token vs ignoring) |

## 2. Missing user attributes *(if applicable)*

| Priority | Attribute | Why | Unlocks |
|---|---|---|---|
| P0 | `kyc_state` (not-started / stalled-at-step / complete) | Segment entry conditions for the two activation journeys | Precise audiences instead of event-absence inference |
| P0 | `consent_state` per channel (İYS status) | Per-step consent checks are mandatory (KVKK/İYS) | Legally safe sends; attributes DQS component |
| P1 | `funded` flag + `balance_tier` (bucketed, not raw balance) | Dormancy Save audience; tone calibration | Value-aware retention without storing sensitive raw balances in the CRM |
| P1 | `recurring_deposit_active` flag | Strongest retention signal as a segmentable attribute | Habit-based journeys; churn-risk scoring |
| P2 | `product_holdings` (card / savings / goals) | Multi-product breadth segmentation | Feature-adoption targeting once unblocked |

## 3. Implementation notes (required)

- `sign_up`, `kyc_start`, `kyc_step_completed`, `kyc_complete`: fire **server-side** from the identity-verification service (client-side KYC events are unreliable and spoofable); include `failure_reason` from the verification vendor's response codes.
- `first_deposit`, `deposit`, `withdrawal`, `payment_failed`: fire server-side from the ledger/payments service — money events must come from the system of record, never the client.
- `login`: client-side on app foreground with a server-side session fallback.
- `feature_used`, `app_remove`: client-side (app); `app_remove` via push-token feedback.
- Consent implications: event collection itself falls under KVKK — confirm the analytics/CRM data-processing basis with compliance before enabling; `consent_state` must mirror İYS, not shadow it. Balance data enters the CRM only as bucketed tiers.

## 4. Re-run instruction (required)

After implementing any batch (P0 first), re-run `/lifecycle connect` — the DQS is re-scored, blocked journeys unlock, and the simple journeys above regenerate at higher depth automatically.

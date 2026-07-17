---
name: payment-failure
stage: revenue
trigger_type: event
required_events: [payment_failed, payment_succeeded]
optional_events: [subscription_cancel, login, add_payment_info]
required_attributes: [failure_reason]
optional_attributes: [retry_schedule, plan_name, payment_method_type]
default_channels: [email, sms, in-app]
base_steps: 4
depth_range: [3, 6]
applicable_industries: [saas, subscription-media, fintech, mobile-app, insurance, edtech]
---

# Payment Failure (Dunning)

Recover failed subscription payments before involuntary churn. This protects existing revenue rather than creating new revenue — often the highest-ROI journey a subscription business never built. Its defining constraint is regulatory: per [consent-and-quiet-hours.md](../compliance/consent-and-quiet-hours.md), payment-failure notices are **transactional** — exempt from marketing consent but only while they contain **zero promotional content**. The first notices must be pure service messages; the moment a step upsells ("upgrade to annual and save"), that step is marketing, requires marketing consent, and counts against frequency caps.

## Required-event signature

| Event | Role |
|---|---|
| `payment_failed` | Trigger. Must carry `failure_reason` (card expired vs insufficient funds vs hard decline) — the branch key. |
| `payment_succeeded` | Success exit (custom; a renewal `purchase` or billing-system webhook is an acceptable stand-in). Without it, recovery is unmeasurable — pattern is **blocked**. |
| `subscription_cancel` *(optional)* | Hard exit; also separates voluntary from involuntary churn in reporting. |
| `add_payment_info` *(optional)* | Intermediate success signal — card updated but retry pending; suppresses further urgency. |
| `retry_schedule` *(optional attr)* | Aligns messages with the processor's automatic retries instead of fighting them. |

## Entry / exit

- **Entry:** `payment_failed` fired on an active subscription, no `payment_succeeded` since. Transactional status means consent gating is minimal for early steps — but honor channel-level opt-outs for the account.
- **Exclude:** user already in this journey for the same invoice, subscription already cancelled, failure on a free-trial card authorization (different message entirely).
- **Success exit:** `payment_succeeded` for the failing subscription · **Window:** grace period length (typically 7–21 days, set by billing config) · **Re-entry:** per distinct failed invoice.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (3) | DQS < 40 or no `failure_reason` | Notice → reminder → final notice before suspension. Single channel, all transactional. |
| Standard (4–5) | DQS 40–69 | Branches on `failure_reason` (expired card gets "update card", insufficient funds gets retry-date framing); adds second channel for the final notice. |
| Branched (6) | DQS ≥ 70 + `add_payment_info` + `retry_schedule` | Syncs with processor retries, suppresses on card update, and may append one *marketing* step post-recovery (e.g. annual-plan offer) — clearly flagged as consent-gated. |

Depth is bounded by the grace period, not by DQS ambition: every step must land before suspension.

## Step blueprint (standard, 4 steps)

| # | Wait | Channel | Intent | Branch |
|---|------|---------|--------|--------|
| 1 | ≤ 1h after failure | email | Transactional notice: what failed, why (`failure_reason`), one-click link to update payment. No promo content. | — |
| 2 | +3d | email | Transactional reminder aligned to next auto-retry date; reassure service continues during grace | if not recovered and card not updated |
| 3 | +3d | in-app | Persistent banner: payment issue, days remaining in grace | if not recovered |
| 4 | 48h before suspension | sms | Final transactional notice: exact suspension date and what happens to data/access (respect SMS quiet hours 20:00–10:00, no Sundays) | if not recovered |

Tone rule: this is a service conversation with a customer who *wants* to pay in most cases (expired cards dominate). No guilt, no urgency theater — clarity and a working update link do the work. A failure message answers three things, in this order: **what is safe/unchanged** ("your coverage continues through the grace period", "your data is intact"), **what is being done**, and **when the user will hear next** (a concrete time, honored). Fear of loss is the reader's default state in a payment failure; the message's job is to remove it, never to lean on it.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Payment recovery rate | primary | `payment_succeeded` within grace / failures entered |
| Involuntary churn rate | secondary | subscriptions suspended after full sequence — the number this journey exists to shrink |
| Complaint/opt-out rate on SMS step | guardrail | transactional SMS still burns trust if overused; one final notice, never a drip |

## Common mistakes

- Putting promotional content in the first notices — instantly reclassifies the message as marketing, voiding the consent exemption and creating İYS/GDPR exposure.
- Ignoring the processor's retry schedule — asking users to "update your card" hours before an automatic retry would have succeeded creates needless friction and support tickets.
- One generic message for all `failure_reason` values — an expired card and a hard decline need different asks; treating them identically halves recovery.

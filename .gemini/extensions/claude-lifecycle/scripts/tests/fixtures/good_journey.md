# Journey: Trial Conversion

**ID:** `saas-trial-conversion-01` · **Version:** 1.0.0 · **Pattern:** trial-conversion · **Priority:** P0
**Data tier:** T2 · **DQS at generation:** 69/100 · **Depth class:** standard (4–7)

## 1. Objective (required)

Convert trial accounts to paid within the trial clock.

## 2. Trigger & entry (required)

| Field | Value |
|---|---|
| Trigger type | event-based |
| Trigger | `trial_start` |
| Entry conditions | no active subscription |
| Re-entry policy | once per trial |
| Quiet hours | per knowledge/compliance/consent-and-quiet-hours.md |

## 3. Audience (required)

- **Who enters:** trial account admins
- **Who is excluded:** suppressed accounts
- **Estimated volume:** 2

## 4. Exit & success criteria (required)

- **Success (conversion) exit:** `subscription_start` — user leaves the journey immediately.
- **Other exits:** unsubscribe.
- **Success window:** 21 days

## 5. Steps (required)

| # | Wait | Channel | Message intent | Branch condition | Copy ref |
|---|------|---------|----------------|------------------|----------|
| 1 | +1h after trigger | email | welcome + first value action | — | step-1 |
| 2 | +2d | in_app | obstacle removal | no feature_used by day 3 | step-2 |
| 3 | +2d | email | activation-split content | feature_used status | step-3 |
| 4 | +3d | push | expiry notice + last call | — | step-4 |

## 6. Measurement (required)

| KPI | Type | Definition | Target |
|---|---|---|---|
| trial to paid | primary | conversions vs entered | baseline after 4 weeks |
| unsubscribe rate | guardrail | per send | < 0.3% |

## 7. Frequency & compliance notes (required)

- Standard portfolio precedence applies.

## 8. Flow diagram (required)

```mermaid
flowchart TD
    T([Trigger: trial_start]) --> S1[Step 1: email — welcome]
    S1 --> S2[Step 2: in_app — obstacle removal]
    S2 --> S3[Step 3: email — activation-split content]
    S3 --> S4[Step 4: push — expiry notice]
```

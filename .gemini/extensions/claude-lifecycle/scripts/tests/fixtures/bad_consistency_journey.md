# Journey: Trial Conversion

**ID:** `saas-trial-conversion-01` · **Version:** 1.0.0 · **Pattern:** trial-conversion · **Priority:** P0
**Data tier:** T2 · **DQS at generation:** 69/100 · **Depth class:** standard (4–7)

## 1. Objective (required)

Convert trial accounts to paid within the trial clock.

## 5. Steps (required)

| # | Wait | Channel | Message intent | Branch condition | Copy ref |
|---|------|---------|----------------|------------------|----------|
| 1 | +1h after trigger | push | welcome + first value action | — | step-1 |
| 2 | +2d | in_app | obstacle removal | — | step-2 |
| 3 | +2d | email | activation-split content | feature_used status | step-3 |
| 4 | +3d | push | expiry notice + last call | — | step-4 |

## 6. Measurement (required)

| KPI | Type | Definition | Target |
|---|---|---|---|
| trial to paid | primary | conversions vs entered | baseline after 4 weeks |

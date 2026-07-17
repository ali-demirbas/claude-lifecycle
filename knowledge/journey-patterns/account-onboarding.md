---
name: account-onboarding
stage: activation
trigger_type: event
required_events: [sign_up]
optional_events: [invite_sent, invite_accepted, feature_used, tutorial_complete, subscription_start]
required_attributes: [account_id, user_role]
optional_attributes: [seats_total, seats_active, plan_name, champion_changed]
default_channels: [email, in-app]
base_steps: 6
depth_range: [4, 10]
applicable_industries: [saas, insurance]
mutually_exclusive_with: [welcome-onboarding]
---

# Account Onboarding

Onboard a **B2B account**, not a person. The unit of success is the account reaching activation (enough seats doing the core job) — and the same signup fans out into role-differentiated parallel tracks, because the economic buyer, the technical stakeholder, and the end-user each have a different "aha" and a different failure mode. Distinct from `welcome-onboarding` (person-level, self-serve); use this when `account_id` + `user_role` exist and seats > 1.

## Required-event signature

| Input | Role |
|---|---|
| `sign_up` (with `account_id`) | Trigger. Journey arms at account creation, not per user. |
| `user_role` (attr) | The fan-out key: economic buyer / technical stakeholder / end-user. Missing role map → run person-level `welcome-onboarding` instead and log the gap as a progressive-profiling target. |
| `invite_sent` / `invite_accepted` *(optional)* | Seat-expansion milestone; also the cheapest role-inference signal (inviter ≈ admin/champion). |
| `feature_used` *(optional)* | Per-role activation evidence; end-user track branches on it. |
| `seats_active` *(optional attr)* | Account activation metric: active seats / total seats. |

## Entry / exit

- **Entry:** account created, ≥ 1 messageable user, not a sales-led enterprise deal with a human onboarding owner (those follow the CSM's plan — the journey only fills gaps the CSM asks for).
- **Exclude:** accounts under negative-signal suppression; single-seat accounts (→ `welcome-onboarding`).
- **Success exit:** account activation definition from the playbook (e.g. ≥ 3 active seats using the core feature within 30 days). · **Window:** 30–45 days. · **Re-entry:** never; failures hand to `activation` (rescue) or CSM escalation.

## Role tracks (the core mechanic)

| Role | Their aha | Track focus | Failure mode to design against |
|---|---|---|---|
| Economic buyer | ROI evidence, team adoption visible | Lighter touch: setup progress digest, adoption summary at week 2–3 | Radio silence until renewal — then it's too late |
| Technical stakeholder | A completed integration | Setup/integration sequence: docs, API keys, sandbox, support fast-lane | Stuck at integration = the whole account stalls; escalate stuck-state fast |
| End-user | Core workflow completed once | Workflow-first product tour, first-task nudges | Tool fatigue: never market to them, only remove obstacles |

Champion identification happens here: the inviter/most-active admin gets tagged (feeds `churn-prevention`'s `champion_changed` watch later).

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (4) | DQS < 40 or no `user_role` reliability | Account-level sequence to the admin only: welcome → setup checklist → invite nudge → activation check |
| Standard (5–7) | DQS 40–69 | Admin track + one end-user track; seat-activation milestone at midpoint |
| Branched (8–10) | DQS ≥ 70 + `feature_used`/`invite_accepted` | Full three-role fan-out, stuck-state branches (no invites by day 5, integration not completed by day 7 → obstacle-removal or human escalation) |

## Step blueprint (standard, 6 steps)

| # | Wait | Channel | Intent | Branch |
|---|------|---------|--------|--------|
| 1 | +1h | email → admin | Welcome + the one setup action that predicts account success | — |
| 2 | +1d | in-app → admin | Invite-your-team nudge with visible seat value | if no `invite_sent` |
| 3 | +2d | email → technical | Integration/setup path, docs + support fast-lane | if role known |
| 4 | +3d | in-app → end-users | First core workflow, contextual | per accepted invite |
| 5 | +7d | email → admin | Adoption digest: who's active, what's stuck | — |
| 6 | +14d | email → admin | Activation checkpoint; stuck accounts → offer human help | if `seats_active` below bar |

## KPIs

| KPI | Type | Note |
|---|---|---|
| Account activation rate | primary | accounts hitting the playbook activation definition within window, incremental vs holdout |
| Seat activation ratio | secondary | `seats_active`/`seats_total` at day 30 — the leading indicator |
| Per-role unsubscribe rate | guardrail | end-user track especially; they never asked for email |

## Common mistakes

- Messaging every seat identically — the end-user track sending ROI content is how the whole account tunes out.
- Measuring person activation instead of account activation — five active seats in a 100-seat account is a failing account with great-looking user metrics.
- Letting a stuck technical stakeholder age silently — integration stall is an account-level emergency, not a drip-sequence data point; escalate to a human.

---
name: account-onboarding
stage: activation
trigger_type: event
required_events: [sign_up]
optional_events: [invite_sent, invite_accepted, feature_used, integration_completed, account_activated, consent_withdrawn, csm_owner_assigned]
required_attributes: [account_id, user_role]
optional_attributes: [seats_total, seats_active, plan_name, champion_changed, csm_owner]
default_channels: [email, in_app]
base_steps: 6
depth_range: [4, 10]
applicable_industries: [saas, insurance]
mutually_exclusive_with: [welcome-onboarding]
journey_class: marketing
signal_sources: {sign_up: authoritative, account_id: authoritative, user_role: authoritative, invite_sent: behavioral, invite_accepted: authoritative, feature_used: behavioral, seats_active: behavioral, account_activated: behavioral, csm_owner_assigned: authoritative, consent_withdrawn: authoritative}
insufficient_alone:
  - one highly active seat in a multi-seat account
  - invite_sent without invite_accepted
  - an inferred role with no confirmation
exit_before_each_send: [account_activated, consent_withdrawn, csm_owner_assigned]
reentry: {policy: once, on_duplicate_trigger: ignore}
instance_key: account_id
measurement_default: holdout
---

# Account Onboarding

Onboard a **B2B account**, not a person. The unit of success is the account reaching activation (enough seats doing the core job), and the same signup fans out into role-differentiated tracks, because the economic buyer, the technical stakeholder and the end-user each have a different "aha" and a different failure mode. Distinct from `welcome-onboarding` (person-level, self-serve); use this when `account_id` + `user_role` exist and seats > 1.

`account_activated` below is the account activation definition from the industry playbook, computed per account (a configurable default: ≥ 3 active seats using the core feature since entry; change it from the observed seat count of accounts that renewed).

## Required-event signature

| Event | Source | Role |
|---|---|---|
| `sign_up` (with `account_id`) | authoritative | Trigger. The journey arms once per account at account creation, not per user. |
| `user_role` (attr) | authoritative | The fan-out key: economic buyer / technical stakeholder / end-user. Missing role map → run person-level `welcome-onboarding` instead and log the gap as a progressive-profiling target. |
| `account_activated` | behavioral | Success exit, computed from `seats_active` and core `feature_used` since entry. Re-checked before every send. |
| `invite_sent` / `invite_accepted` *(optional)* | behavioral / authoritative | Seat-expansion milestone and the cheapest role-inference signal (the inviter is usually the admin or champion). Feeds d1. |
| `feature_used` *(optional)* | behavioral | Per-role activation evidence for the end-user track. |
| `integration_completed` *(optional)* | behavioral | Technical-track milestone; its absence is the stuck-state the branched shape escalates. |
| `seats_active` / `seats_total` *(optional attrs)* | behavioral | Account activation ratio, the leading indicator. |
| `csm_owner` *(optional attr)* | authoritative | A human onboarding owner. Assigning one mid-journey (`csm_owner_assigned`) stops automated sends. |

### Not enough on its own

- **One highly active seat in a multi-seat account.** Great person metrics inside a failing account; never counts toward `account_activated` alone.
- **`invite_sent` without `invite_accepted`.** The admin did their part; the account has not grown yet. d1 reads `invite_sent` only to decide whether to nudge the admin, never as seat activation.
- **An inferred role with no confirmation.** "Inviter ≈ admin" is a good guess for routing a setup email, not for sending ROI content to someone who may be an end-user.

## Entry / exit

- **Entry:** account created, ≥ 1 messageable user, `user_role` mapped for at least the admin, not a sales-led deal with a human onboarding owner (those follow the CSM's plan; the journey only fills gaps the CSM asks for).
- **Exclude:** accounts under negative-signal suppression; single-seat accounts (→ `welcome-onboarding`).
- **Supersede rule:** for multi-seat accounts this pattern supersedes `welcome-onboarding` whenever both are active in a portfolio; `welcome-onboarding` remains the fallback only when this pattern is not active.
- **Success exit:** `account_activated` · **Window:** 30–45 days from entry (configurable; match it to the time-to-activation of accounts that renewed).
- **Checked before every send:** `account_activated` and `csm_owner_assigned` **for this account** (`instance_key: account_id`; another account the same person belongs to doesn't count), and `consent_withdrawn` scoped to that recipient and channel (one admin's email unsubscribe stops that admin's emails, not the account's other recipients or the in-app tier).
- **Re-entry:** never. A new seat's `sign_up` with the same `account_id` while the instance is active does not open a second instance; it adds that person to their role track.
- **Hand-offs:** failures go to [activation](activation.md) (rescue) or CSM escalation; a CSM taking ownership suppresses every queued send of this journey. Champion identification happens here: the inviter or most active admin gets tagged, which later feeds `churn-prevention`'s `champion_changed` watch.

## Role tracks (the core mechanic)

| Role | Their aha | Track focus | Failure mode to design against |
|---|---|---|---|
| Economic buyer | ROI evidence, team adoption visible | Lighter touch: setup progress digest, adoption summary at week 2–3 | Radio silence until renewal, when it is too late |
| Technical stakeholder | A completed integration | Setup and integration: docs, API keys, sandbox, support fast lane | Stuck at integration stalls the whole account; escalate fast |
| End-user | Core workflow completed once | Workflow-first product tour, first-task nudges | Tool fatigue: never market to them, only remove obstacles |

Invited people are messaged by this journey only after they accept. Before that, their address came from a colleague, not from them, and the product's own invitation is the only message they should receive.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (4) | DQS < 40 or no reliable `user_role` | Account-level sequence to the admin only: welcome → setup checklist → invite nudge → activation check |
| Standard (5–7) | DQS 40–69 | Admin track + technical touch + one end-user track; seat-activation digest at day 7 |
| Branched (8–10) | DQS ≥ 70 + `feature_used`/`invite_accepted` | Full three-role fan-out with stuck-state decisions (no `invite_sent` by entry +5d, no `integration_completed` by entry +7d → obstacle removal or human escalation) |

## Step blueprint (standard, 6 sends)

| Node | When | Channel | Intent | Route |
|---|---|---|---|---|
| s1 | entry +1h | email → admin | Welcome plus the one setup action that best predicts account success | → d1 |
| d1 | s1 +1d | — | Decision on `invite_sent` (behavioral) between entry and s1 +1d | occurred → s3 · not_occurred → s2 · unmeasurable → s2 |
| s2 | s1 +1d (shown at next session, expires after 5d) | in_app → admin | Invite-your-team nudge with visible seat value, shown at the admin's next session; skipped if none comes within 5 days | → s3 |
| s3 | s1 +3d | email → technical | Integration and setup path, docs plus support fast lane; goes to the admin when no technical role is mapped | → s4 |
| s4 | s1 +6d (shown at next session, expires after 7d) | in_app → end-users | First core workflow, contextual; each accepted invitee sees it at their first session on or after this time (or after accepting, if later), for at most 7 days | → s5 |
| s5 | s1 +7d | email → admin | Adoption digest: who is active, what is stuck, one action to unblock | → s6 |
| s6 | s1 +14d | email → admin | Activation checkpoint with an offer of human help (only accounts below the bar reach it, because `account_activated` exits first) | end |

The sends above are per role, so no one person receives all six: the admin's longest path is s1, s2, s5, s6.

## Timing and channel fit

- Business clock: admin and technical emails go on the account's working days within business hours in the recipient's timezone (account timezone when the person's is unknown). In-app touches wait for the recipient's next session up to their stated expiry, then are skipped; later sends keep their scheduled anchors, and no email waits on an in-app view.
- Email suits the admin and technical tracks because setup instructions and digests must survive until someone acts on them. End-users get in-app only by default: they did not choose the tool and are the first to tune out email.
- Push and SMS are not default channels here. A recipient without email consent gets in-app only; when the admin has neither, the account falls back to the product's own transactional setup emails, and the gap goes to the CSM.

## Frequency and overlap

- Worst path per person in a rolling 7 days: admin at most 2 marketing emails + 1 in-app; technical 1 email; end-users 1 in-app. Caps apply per person, not per account.
- **Usual overlaps:** `trial-conversion` (B2B trials), `progressive-profiling`, `feature-adoption`.
- **Precedence:** `trial-conversion` owns expiry and pricing notices to the admin; this journey owns setup content. When both would put the admin above 4 emails in 7 days, defer the s5 digest by up to 2 days rather than dropping a trial deadline notice. `feature-adoption` waits until this journey exits.

## Measurement

- **Primary outcome:** `account_activated` within the window, incremental vs holdout. Secondary: `seats_active`/`seats_total` at day 30.
- **Design:** holdout assigned per **account**, never per user; seats in the same account split across arms contaminate each other through the shared product. The control receives none of s1–s6.
- **Routine communications both groups keep:** product invitations, account confirmation, security emails, billing notices, the product's own default setup checklist.
- **Contamination:** CSM or sales outreach to control accounts; admins forwarding digests to colleagues.
- **Low volume:** B2B account counts are usually too small for a 10% holdout to detect anything in one window. Default then to `none_low_volume` with a cohort pre/post of account activation rate, labeled directional, and say which lift size the volume could have shown.

## When data is missing

- **`user_role` missing for most seats:** run the simple shape to the admin only and add role capture to `progressive-profiling`.
- **`invite_sent` not tracked or delayed:** d1 takes the unmeasurable route to s2. An extra invite nudge costs little; skipping it on missing data costs the account.
- **`seats_active` unavailable:** `account_activated` cannot be computed; the journey exits only on time-out, and activation is reported as unmeasured, not as zero.
- **`csm_owner` not synced from the CRM:** state the risk that automated emails will reach CSM-owned accounts and ask for the field before launch.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Account activation rate | primary | accounts reaching `account_activated` within window, incremental vs account-level holdout |
| Seat activation ratio | secondary | `seats_active`/`seats_total` at day 30, the leading indicator |
| Per-role unsubscribe rate | guardrail | end-user track especially; they never asked for email |

## Common mistakes

- Messaging every seat identically. An end-user track sending ROI content is how the whole account tunes out.
- Measuring person activation instead of account activation. Five active seats in a 100-seat account is a failing account with great-looking user metrics.
- Letting a stuck technical stakeholder age silently. Integration stall is an account-level emergency, not a drip data point; escalate to a human.
- Randomizing the holdout per user, so half an account gets the journey and the other half watches them use it.
- Emailing invited people before they accept, using an address a colleague typed in.

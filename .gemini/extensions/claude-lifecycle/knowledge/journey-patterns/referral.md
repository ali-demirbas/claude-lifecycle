---
name: referral
stage: engagement
trigger_type: segment
required_events: [invite_sent]
optional_events: [invite_accepted, referral_reward_credited, share, survey_response, login, consent_withdrawn]
required_attributes: []
optional_attributes: [nps_score, engagement_score, referral_reward]
default_channels: [in_app, email]
base_steps: 4
depth_range: [2, 4]
applicable_industries: [saas, mobile-app, fintech, ecommerce, marketplace, edtech, subscription-media, insurance, travel]
mutually_exclusive_with: []
journey_class: marketing
signal_sources: {invite_sent: authoritative, invite_accepted: authoritative, referral_reward_credited: authoritative, share: behavioral, survey_response: authoritative, engagement_score: inferred, login: behavioral, consent_withdrawn: authoritative}
insufficient_alone:
  - a referral code issued, which is not a code used
  - a share-sheet open with no recorded invite
  - an accepted invite before the fraud and qualification check clears
  - an engagement score with no recent activity behind it
exit_before_each_send: [invite_sent, consent_withdrawn]
reentry: {policy: after_cooldown, cooldown: P60D, on_duplicate_trigger: ignore}
measurement_default: holdout
instance_key: referral_code
---

# Referral

Ask satisfied, engaged users to invite others. The pattern's entire economics rest on the gate: referral asks sent to unhappy or barely-active users produce no invites and damage the relationship, so entry is a **segment** (engagement-health or NPS-positive), not a behavioral trigger. `share` and `invite_sent` are the engagement signals that both qualify users and measure the outcome. This is an engagement-stage journey; the acquisition value of accepted invites is downstream and attributed separately.

The loop has a second half that is easy to get wrong: **a code issued is not a code used.** Once an invite goes out, what happens next depends on whether anyone used it. Used and credited → confirm the reward that was actually credited. Unused → one nudge to the referrer, then stop.

## Required-event signature

| Event | Source | Role |
|---|---|---|
| `invite_sent` | authoritative (referral system: an invite or code recorded as issued and shared) | Success exit of the ask and the core instrumentation. If invites can't be tracked, the loop can't be measured: pattern is **blocked**. |
| `invite_accepted` *(optional)* | authoritative (referral system: the code was used by a new account) | Splits used codes from unused ones; enables reward fulfillment and true referral-value reporting. |
| `referral_reward_credited` *(optional)* | authoritative (reward ledger) | The reward was granted after the fraud/qualification check. The only trigger for a reward confirmation. |
| `share` *(optional)* | behavioral | Organic advocacy signal: users who already `share` are the warmest referral audience. |
| `survey_response` *(optional, with score param)* | authoritative (survey system) | NPS gate: promoters (9–10) enter; feeds directly from [feedback-nps](feedback-nps.md). |
| `engagement_score` *(optional attr)* | inferred | Fallback gate when no NPS exists: sustained active use over a qualifying window. |

### Not enough on its own

- **A referral code issued, which is not a code used:** issuing (or even sharing) a code says nothing about whether anyone redeemed it. Copy never says "your friend joined" or "you've earned" on the strength of an issued code.
- **A share-sheet open with no recorded invite:** opening the native share sheet is intent; many are dismissed. Only the referral system's record counts as `invite_sent`.
- **An accepted invite before the fraud and qualification check clears:** self-referrals, disposable emails and reward farming produce accepted invites. Nothing is confirmed until `referral_reward_credited`.
- **An engagement score with no recent activity behind it:** a score computed months ago, or from a model with no fresh inputs, is not "satisfied right now". The gate needs recent activity too.

## Entry / exit

- **Entry (by moment):**
  - *Ask*: user qualifies as satisfied, read as any_of(a 9–10 `survey_response` (authoritative), an organic `share` in the last 30 days (behavioral), all_of(`engagement_score` above the healthy threshold for a sustained period (inferred), a `login` in the last 14 days (behavioral))), and has been active long enough to have an opinion (default ≥ 30 days tenure, configurable). Unmeasurable is not qualified: no ask on missing data.
  - *Code follow-up*: an `invite_sent` from this journey's ask or from the product's own referral screen.
  - *Reward confirmation*: `referral_reward_credited` for the referrer (and, separately, the invitee where they're also rewarded).
- **Exclude:** detractors and anyone in a service-recovery cooldown (see [feedback-nps](feedback-nps.md); also [consent-and-quiet-hours.md](../compliance/consent-and-quiet-hours.md) rule 4), users in dunning, users who received a referral ask in the last 60 days.
- **Success exit:** `invite_sent` for the ask · **Window:** 14 days.
- **Instance key:** `referral_code` for the code follow-up (one nudge per code), the reward record for confirmations; the ask is per user.
- **Checked before each send:** `invite_sent` (ends the ask), `consent_withdrawn` (channel-scoped: an email opt-out stops a2 and c1; the in-app ask still renders unless in-product messages were turned off). Before the code nudge, `invite_accepted` for this code (`same_instance`) is re-checked so a code used minutes earlier isn't nudged.
- **Re-entry:** the ask once per 60–90 days, and stop permanently after repeated ignored asks (2–3 cycles). The code nudge happens once per code, ever. Reward confirmations are keyed on the reward record: one per credited reward, and a replayed credit event is ignored.
- **Handoffs:** invitees enter the brand's welcome/onboarding journey, never this one. A promoter path arriving from feedback-nps enters the ask directly.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (1–2) | DQS < 40 or gate is tenure-only | In-app prompt at a natural high point + one email with the referral link. Blunt gate, soft ask. |
| Standard (2) | DQS 40–69, engagement scoring works | Same ask, gated on real engagement health; adds the used/unused code follow-up when `invite_accepted` exists. |
| Branched (2) | DQS ≥ 70 + `survey_response` or `share` | NPS-promoter fast path (ask lands right after a 9–10 response), organic-sharer path, and reward confirmation once `referral_reward_credited` fires. |

Depth stays modest at every tier: a referral is a favor, and favors aren't extracted by drip sequence. Extra DQS goes into sharper gating and better *timing* (asking at a moment of success), not more asks. Across one cycle a user receives at most the two asks, one code nudge and one reward confirmation.

## Step blueprint (standard, 2 sends)

| Node | When | Channel | Intent | Route |
|---|---|---|---|---|
| a1 | entry +0h | in_app | The ask, in a success moment (never on error screens): one line on why they might share, prefilled invite flow, reward terms if any. Shown at the next session after qualifying, expires after 7d; a2 is anchored to a1's scheduled time, not to the view | → a2 |
| a2 | a1 +3d | email | Referral link for forwarding; restate the mutual reward plainly | → exit (completed) |
| d1 | invite_sent +7d | — | Code follow-up path starts on `invite_sent` (declared as an event anchor in the journey's `time_anchors`, so an invite sent on day 6 still gets its full 7 days): decision on `invite_accepted` (authoritative, referral system) between invite_sent and invite_sent +7d | occurred → exit (completed; the credit, once granted, starts r1) · not_occurred → c1 · unmeasurable → exit (completed) |
| c1 | d1 +0h at 10:00 user_local | email | One nudge: the invite hasn't been used yet, here is the link again to share with someone who'd want it. Then the path stops for this code | → exit (completed) |
| r1 | referral_reward_credited +0h | email (in_app mirror at the next session, expires after 14d) | Reward confirmation, transactional: exactly what was credited, to whom, and where to see it; zero promotional content. One per credited reward record | → exit (completed) |

`invite_sent` is re-checked before a2, so the email only reaches people who haven't sent an invite yet. When the used/unused signal can't be read, there is no nudge: telling someone their code is unused when it may have been used is worse than silence.

Fraud/abuse gate: verify the referral is genuine **before** granting any reward to either party. Self-referral, disposable emails, and reward farming are standard attacks, and referral programs are a common abuse target, so this check is not optional. Unchecked rewarding is expensive and hard to reverse.

Reward rule: state the terms exactly and fulfill fast. A delayed or fine-print referral reward converts an advocate into a detractor with an audience.

## Timing and channel fit

- The in-app ask has no clock constraint beyond the session itself; it is timed to a success moment the product defines (task completed, order delivered, goal reached).
- Email asks and nudges go in daytime on the user's clock (10:00 user_local for the nudge); quiet hours per [consent-and-quiet-hours.md](../compliance/consent-and-quiet-hours.md).
- Reward confirmations go as soon as the credit lands; they are service messages.
- No email consent → a2 and c1 are skipped (no other channel substitutes for a favor ask); r1 still goes in-app and as a service email.

## Frequency and overlap

- **Worst case per cycle:** a1 + a2 within 3 days, c1 a week after the invite, r1 when credited: at most 2 marketing sends in any rolling 7 days.
- **Overlaps:** [feedback-nps](feedback-nps.md) (promoter path), [milestone](milestone.md) (share prompts after celebrations), [channel-opt-in](channel-opt-in.md) (both ask the user for a favor).
- **Precedence:** a service-recovery or detractor state cancels any queued ask; an opt-in ask and a referral ask never go in the same week (the later one defers); reward confirmations always go.

## Measurement

- **Primary outcome:** invite send rate within 14 days, and accepted-and-credited invites within 45 days as the business outcome.
- **Design:** user-level holdout (default 10%) among qualified users. The control receives no ask (a1, a2) and no code nudge; the product's own referral screen stays available to both.
- **Routine communications both groups keep:** reward confirmations for organic referrals, account and service messages.
- **Contamination risks:** an always-visible referral banner in the product, program-wide referral promotions, invitees who are themselves in the test.
- **Low volume:** invites are a small fraction of qualified users and credited referrals smaller still; most programs can measure invite rate but not credited-referral lift. Say which one was measured.

## When data is missing

- **No `invite_accepted`:** the code follow-up path doesn't run; the ask path still does.
- **No `referral_reward_credited`:** no reward confirmation from this journey; the referral system's own receipts carry it. Never confirm from `invite_accepted` alone.
- **No NPS:** fall back to the engagement-score gate; no score either → tenure + recent activity, labelled as the blunt gate.
- **Ask impression not tracked:** a2 still goes (gated on no `invite_sent`); nothing reads the missing impression as disinterest.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Invite send rate | primary | qualified users sending ≥ 1 invite within window / journeys entered, vs holdout |
| Invite use rate | secondary | `invite_accepted` / `invite_sent`: measures ask quality reaching the *invitee*; the gap between issued and used is the nudge's target |
| Repeat-ask fatigue (opt-out or prompt-dismiss rate) | guardrail | rising dismissals mean the gate is too loose or the cycle too frequent |

## Common mistakes

- Asking everyone: an ungated referral blast to the whole base yields near-zero invites and teaches users to ignore in-app prompts generally.
- Asking at the wrong moment: the prompt after a crash, a failed payment, or a support complaint is the canonical own-goal; tie the ask to success moments.
- Leading with the reward instead of the product: mercenary framing attracts low-quality invitees and can trip incentive-disclosure rules in regulated verticals (fintech especially).
- Granting rewards before verifying the referral is genuine: self-referrals, disposable emails, and reward farming go unchecked, and clawing back a granted reward is far harder than gating it up front.
- Treating an issued code as a success story: "you've referred a friend!" sent on `invite_sent` is a claim the data doesn't support.
- Nudging an unused code more than once: one reminder is help, a sequence is pressure on the referrer's relationships.

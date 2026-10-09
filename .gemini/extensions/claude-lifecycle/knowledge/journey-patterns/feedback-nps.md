---
name: feedback-nps
stage: retention
trigger_type: event
required_events: [survey_response]
optional_events: [purchase, feature_used, trial_end, login, share, invite_sent, support_ticket_opened, follow_up_completed, resolution_confirmed]
required_attributes: [survey_score]
optional_attributes: [survey_comment, experience_type, follow_up_sla]
default_channels: [email, in-app]
base_steps: 3
depth_range: [2, 3]
applicable_industries: [ecommerce, saas, mobile-app, fintech, marketplace, subscription-media, travel, edtech, insurance]
journey_class: service
signal_sources: {survey_response: authoritative, survey_score: authoritative, purchase: authoritative, trial_end: authoritative, feature_used: behavioral, login: behavioral, share: behavioral, invite_sent: authoritative, support_ticket_opened: authoritative, follow_up_completed: authoritative, resolution_confirmed: authoritative, consent_withdrawn: authoritative}
insufficient_alone:
  - no response to the survey
  - a support ticket marked closed
  - a tap-to-score click with no recorded response behind it
  - a follow-up marked scheduled
exit_before_each_send: [survey_response, support_ticket_opened, consent_withdrawn]
reentry: {policy: after_cooldown, cooldown: P90D, on_duplicate_trigger: ignore}
measurement_default: none_service
---

# Feedback / NPS

Collect post-experience feedback and *act on the answer*; the acting is the pattern. The ask fires after a meaningful experience completes (delivered order, trial end, core feature milestone, completed trip/course, sector-dependent), and the branch on `survey_score` does the retention work: promoters are routed to a referral or review ask while goodwill is hot; detractors get service recovery and a **suppression from marketing sends until the issue is resolved**, because promoting to someone who just told you they're unhappy converts feedback into churn.

Three rules keep the pattern honest. **Silence is not a score**: a non-responder is not a detractor and is never treated as one. **Closed is not resolved**: a ticket's status says the team stopped working on it, not that the customer's problem went away. **A promise has a clock**: when a message tells a detractor someone will follow up, that follow-up stays open until it actually happens, and escalates when its SLA passes.

## Required-event signature

| Event | Source | Role |
|---|---|---|
| `survey_response` | authoritative (survey system, with `survey_score`) | The branch point, 0–10 for NPS or 1–5 for CSAT. Without response capture, there is nothing to branch on: pattern is **blocked**. |
| `purchase` / `trial_end` / `feature_used` *(optional)* | authoritative / authoritative / behavioral | Qualifying-experience triggers; the sector's industry file picks which one arms the ask (delivered, not merely placed). |
| `support_ticket_opened` *(optional)* | authoritative (support system) | Excludes users already in a support conversation; re-checked before each send. |
| `follow_up_completed` *(optional)* | authoritative (support system: the follow-up happened, with a timestamp) | Measures the promised follow-up against its SLA. Without it, detractor acknowledgments must not promise a follow-up. |
| `resolution_confirmed` *(optional)* | authoritative (customer confirmation, or the remedy's own record such as a refund issued or replacement delivered) | The only evidence the issue is actually resolved; lifts the detractor's marketing suppression. |
| `share` / `invite_sent` *(optional)* | behavioral / authoritative | Promoter-path handoff signals into [referral](referral.md). |
| `survey_comment` *(optional attr)* | authoritative | Verbatims turn a score into a routable support case for the detractor path. |

### Not enough on its own

- **No response to the survey:** most people don't answer surveys. A non-responder gets at most one reminder, then exits as completed: no negative tag, no suppression, no "at risk" flag.
- **A support ticket marked closed:** closure is the team's status, not the customer's outcome. Suppression lifts on `resolution_confirmed`, and where only a closed status exists, the resolution check-in asks.
- **A tap-to-score click with no recorded response behind it:** email security scanners click every link in a message, including every score. A score counts only when the survey system records the response (a confirmed submission, bot-filtered).
- **A follow-up marked scheduled:** a callback booked is not a callback made. The SLA clock stops at `follow_up_completed`.

## Entry / exit

- **Entry (by moment):**
  - *Ask*: qualifying experience completed (e.g. order delivered, not merely placed), no survey received in the last 90 days, user reachable on ≥ 1 channel.
  - *Answer*: `survey_response` recorded.
- **Exclude:** open support ticket (they've already given feedback; route around the survey), user in dunning, surveyed within the fatigue window regardless of channel.
- **Success exit:** `survey_response` received for the ask; the answer path then runs to completion · **Window:** 7 days for the ask; detractor acknowledgment within 24h of response, promoter and passive actions within 72h.
- **Checked before each send:** `survey_response` (ends the ask path), `support_ticket_opened` (a new ticket during the ask cancels the survey), `consent_withdrawn` (for the promoter's referral/review ask, which is marketing; service messages to a detractor still go).
- **Re-entry:** once per 90 days maximum. A second response to the same survey (a re-submit, a replayed event) updates the score but does not restart the answer path.
- **Handoffs:** promoters → [referral](referral.md) ask or a review ask; detractors → human/service recovery and the portfolio-wide negative-signal override in [consent-and-quiet-hours.md](../compliance/consent-and-quiet-hours.md) rule 4 (every marketing journey's queued sends are suppressed until resolution, not on a timer).

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (2) | DQS < 40 | Ask + one reminder. Responses logged; branching handled manually. The detractor acknowledgment doesn't promise a follow-up the system can't track. |
| Standard (2–3) | DQS 40–69 | Full branch: promoters → referral/review ask, detractors → acknowledgment + recovery route + marketing suppression, passives → thank-you only. |
| Branched (3) | DQS ≥ 70 + `survey_comment` / support integration | Detractor path runs a tracked recovery loop (promised follow-up against an SLA, escalation, resolution check-in); promoter path picks referral vs public-review ask based on prior `share` behavior. |

## Step blueprint (standard, 3 sends)

Two paths: the ask (started by the qualifying experience) and the answer (started by the response). The detractor branch of the answer path is the longest.

| Node | When | Channel | Intent | Route |
|---|---|---|---|---|
| q1 | entry +2d | email | The ask, 24–72h after the qualifying experience (long enough to have an opinion): one question, score in the body, nothing else | → d1 |
| d1 | q1 +4d | — | Decision on `survey_response` (authoritative) between q1 and q1 +4d | occurred → exit (completed; the response starts the answer path) · not_occurred → q2 · unmeasurable → exit (completed) |
| q2 | d1 +0h at 10:00 user_local | email | One reminder, same question. Then the ask path ends whatever happens | → exit (completed) |
| d2 | entry +0h | — | Answer path starts on `survey_response`: decision on `survey_score` (authoritative) between entry and entry +0h | 9–10 → p1 · 0–6 → r1 · default (7–8) → t1 · unmeasurable → t1 |
| p1 | entry +24h | email | Promoters: thank, then one referral or public-review ask (marketing; needs marketing consent). Hand off to the referral pattern | → exit (completed) |
| t1 | entry +24h | email | Passives, or a response whose score didn't arrive: a short thank-you, no ask | → exit (completed) |
| r1 | entry +4h | email | Detractors: acknowledge, apologize where warranted, route to human/service recovery. Names a follow-up and its timeframe only if the support system will record it | → d3 |
| d3 | r1 +2d | — | Decision on `follow_up_completed` (authoritative, support system) between r1 and r1 + the follow-up SLA (default 2 business days, configurable) | occurred → d4 · not_occurred → e1 · unmeasurable → e1 |
| e1 | d3 +0h | email | SLA missed: the case is escalated to a team lead internally, and the customer gets an honest update that it is still unresolved and who now owns it | → d4 |
| d4 | d3 +7d | — | Decision on `resolution_confirmed` (authoritative) between r1 and d3 +7d | occurred → exit (completed) · not_occurred → v1 · unmeasurable → v1 |
| v1 | d4 +0h at 10:00 user_local | email | Resolution check-in: one question, "is this sorted?". A no reopens the case with the same owner; a yes lifts the marketing suppression | → exit (completed) |

The worst path for a detractor is r1 → e1 → v1: three service sends, each of which exists because something is still unresolved. When the follow-up signal can't be read, d3 escalates rather than assuming it happened.

Public-review mechanics (promoter path, app products): gate the store-review prompt on a genuine success moment **and** minimum tenure, both, not either. Ask a soft in-app sentiment question first; positive → the native store rating flow, neutral/negative → a private feedback form, never the public store. Two separate cooldowns, not one: a shorter cooldown (~14 days) since the soft prompt was last *shown*, gating re-asking even when it never reached a native prompt, and a longer cooldown (60–90 days) after the native prompt actually *fires*, since that's the scarcer, quota-limited resource. Platform quotas make every native prompt precious: iOS's SKStoreReviewController allows at most 3 prompts per user per 365 days, and Android's In-App Review API enforces its own platform-managed quota; a wasted prompt cannot be re-fired.

## Timing and channel fit

- The ask goes on the user's clock, in daytime; quiet hours per [consent-and-quiet-hours.md](../compliance/consent-and-quiet-hours.md). In-app works for products with frequent sessions (ask at the next session after the experience).
- Detractor acknowledgments are service messages: they go within business hours of the support team that will act on them, so the "someone will be in touch" is true by the time it's read.
- Email carries the survey and anything that needs a reply; push is not used for surveys. No email consent and no session → no ask.
- Whether a survey request needs marketing consent varies by market (some regimes treat it as direct marketing). Where unclear, apply the strictest reading and confirm with counsel. The promoter referral/review ask always needs marketing consent.

## Frequency and overlap

- **Worst path:** ask path 2 sends in 5 days; detractor path up to 3 service sends over ~10 days. Service sends don't count against marketing caps; the promoter ask does.
- **Overlaps:** post-purchase, [referral](referral.md) (promoter handoff), every marketing journey (the detractor override suppresses them all).
- **Precedence:** a detractor response suppresses every queued marketing send portfolio-wide until resolution. The survey yields to any open service conversation: never survey someone mid-ticket.

## Measurement

- **Primary outcome:** response rate within 7 days of the ask; detractor recovery (resolved and still active 60 days after response) for the answer path.
- **Design:** `none_service`. The answer path is service: withholding recovery from a control group to measure it is not acceptable. Alternative: compare detractor retention before and after the recovery loop launched (pre/post, same season), and track SLA attainment. The promoter referral/review ask may carry its own holdout, inherited from [referral](referral.md).
- **Routine communications both groups keep:** all support and service messages.
- **Contamination risks:** surveys sent by other teams or tools to the same users; support macros that already apologize and promise follow-ups.
- **Low volume:** detractor counts are often small; recovery rates on a few dozen cases are directional. Report counts alongside rates.

## When data is missing

- **No `follow_up_completed`:** r1 does not promise a follow-up or a timeframe; it routes to support and stops there. The SLA loop needs this signal.
- **No `resolution_confirmed`, only a ticket status:** the check-in (v1) asks the customer; closed status alone never lifts the suppression.
- **Score missing from a recorded response:** thank-you only (t1); never guess the bucket.
- **Response arrives late (after the reminder):** the answer path still runs; the late responder is not penalized.
- **No support integration at all:** portfolio-level warning per the compliance file: the negative-signal override cannot fire, and the missing signal goes into the tracking plan as P0.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Response rate | primary | responses / asks sent: everything downstream depends on it |
| Detractor recovery rate | secondary | detractors with a confirmed resolution who remain active after 60 days |
| Follow-up SLA attainment | guardrail | promised follow-ups completed within SLA / follow-ups promised; a broken promise to a detractor does more damage than no promise |
| Survey fatigue (asks per user per quarter) | guardrail | the 90-day re-entry cap is the floor, not a target; over-surveying depresses scores by itself |

## Common mistakes

- Collecting scores and doing nothing: an unanswered detractor response is worse than never asking, because the user now has evidence you don't listen.
- Skipping the marketing suppression: a promo email landing the day after a 2/10 response is how detractors become public detractors.
- Treating silence as dissatisfaction: tagging non-responders as at-risk inflates the "unhappy" segment with people who are simply busy.
- Lifting the suppression when the ticket closes: the customer decides whether it's fixed, not the ticket status.
- Promising "we'll be in touch within 24 hours" with nothing tracking whether anyone was.
- Gaming the sample: asking only after visibly good experiences produces a flattering, useless number and hides the churn signal the pattern exists to catch.

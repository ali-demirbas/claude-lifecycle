---
name: unengaged-sunset
stage: engagement
trigger_type: absence
journey_class: marketing
required_events: [email_delivered, link_click]
optional_events: [session_start, login, purchase, preference_updated, unsubscribe, spam_complaint, hard_bounce]
required_attributes: []
optional_attributes: [last_engaged_at, consent_date, click_tracking_reliable, marketing_streams, sender_suppression]
default_channels: [email]
base_steps: 3
depth_range: [2, 4]
applicable_industries: [ecommerce, marketplace, saas, subscription-media, travel, fintech, insurance, edtech, mobile-app]
mutually_exclusive_with: []
signal_sources: {email_delivered: authoritative, link_click: engagement, session_start: behavioral, login: behavioral, purchase: authoritative, preference_updated: authoritative, unsubscribe: authoritative, spam_complaint: authoritative, hard_bounce: authoritative, click_tracking_reliable: authoritative, sender_suppression: authoritative}
insufficient_alone:
  - no email opens
  - silence on a route where clicks are not measured
  - a quiet period shorter than the configured window
  - few deliveries in the window
  - quiet email while the person is active in the product
exit_before_each_send: [link_click, session_start, purchase, preference_updated, consent_withdrawn]
reentry: {policy: after_cooldown, cooldown: P180D, on_duplicate_trigger: ignore}
measurement_default: pre_post
---

# Unengaged Sunset

Reduce, then stop, non-essential marketing to people who have stopped responding to it, after offering them a clear choice first. This is the list-hygiene step that [winback](winback.md), [reactivation](reactivation.md) and [lead-nurture](lead-nurture.md) hand people to when their own cycles run out. Silence is a reason to lower pressure, never a reason to send more campaigns.

The journey ends in a **sender-side suppression**: the brand decides to stop sending marketing to this address. That is not a consent withdrawal. The person's consent record is untouched, they can come back by engaging, and transactional and service messages (receipts, payment notices, account and security messages, protective alerts) keep flowing.

## Required-event signature

| Event | Source | Role |
|---|---|---|
| `email_delivered` | authoritative | Proves the person was actually sent marketing in the window. Silence only counts when there was something to respond to. Without it, pattern is **blocked**. |
| `link_click` | engagement | The engagement signal, bot-filtered. Without click tracking (or without bot filtering), silence can't be told apart from a measurement gap: pattern is **blocked** for that route. |
| `session_start` / `login` / `purchase` *(optional)* | behavioral / authoritative | Activity anywhere in the product or store counts as engagement; a customer who buys but never clicks emails is not unengaged. |
| `preference_updated` *(optional)* | authoritative | The choice the journey offers (fewer, pause, stop, keep). A choice is a success, whatever it is. |
| `spam_complaint` / `hard_bounce` / `unsubscribe` *(optional)* | authoritative | Not handled here: complaints and hard bounces suppress immediately, unsubscribes are consent changes. Listed so the journey can exclude them. |
| `click_tracking_reliable` *(optional attr)* | authoritative | Per route or per mailbox: whether clicks are tracked and bot-filtered there. |

### Not enough on its own

- **No email opens.** Opens are inflated by privacy proxies and suppressed by image blocking; "never opened" says little about a person. Nothing in this journey reads them.
- **Silence on a route where clicks are not measured.** If links aren't tracked, or bot clicks aren't filtered, or the channel has no click concept, silence there is a measurement gap. Only routes with measurable engagement can make someone unengaged.
- **A quiet period shorter than the configured window.** The window is a business setting (default 180 days without a measurable engagement; shorten it for high-frequency senders, lengthen it for annual-cycle businesses, and change it only with evidence from the business's own re-engagement history).
- **Few deliveries in the window.** Someone sent two emails in six months has not been silent; they have barely been asked. Default minimum: 8 marketing deliveries in the window (configurable).
- **Quiet email while the person is active in the product.** A user who logs in weekly is engaged; their inbox habits are a channel preference, not disinterest.

## Entry / exit

- **Entry:** marketing consent valid; at least the minimum number of marketing deliveries in the window; no bot-filtered `link_click`, `session_start`, `login`, `purchase` or `preference_updated` in the window; the route's click tracking is reliable. Also entered by handoff when winback, reactivation or lead-nurture exhaust their lifetime cycles.
- **Exclude:** consent younger than the window (new subscribers are onboarding, not silent); open transactional or service flows are unaffected and need no exclusion; people already sender-suppressed; people already suppressed by a complaint or hard bounce (those are immediate, not sunset); people under the portfolio negative-signal override.
- **Success exit:** any of `link_click` (bot-filtered), `session_start`, `purchase`, `preference_updated` · **Window:** default 45 days (configurable, tied to the probation length in `d2`).
- **Checked before each send:** `link_click`, `session_start`, `purchase`, `preference_updated`, `consent_withdrawn`.
- **What the suppression does:** records `sender_suppression` (reason: unengaged; date; streams covered). Every marketing and lifecycle journey reads it as an exclusion. It never touches transactional or service journeys, and it never edits the consent record. Re-engagement (sign-in, purchase, click from a transactional message's account link, or a preference choice) lifts it.
- **Re-entry:** after a 180-day cooldown from the last instance; a duplicate trigger while open is ignored. A person who comes back after more than ~2 years of silence follows the compliance re-permission rule before any marketing resumes.
- **Handoffs:** none outbound. Inbound from [winback](winback.md), [reactivation](reactivation.md) and [lead-nurture](lead-nurture.md), with their queued sends suppressed.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (2) | DQS < 40 or no stream-level data | Preference choice → final notice → suppression. No reduced-cadence probation. |
| Standard (3) | DQS 40–69 | Preference choice → reduced cadence for a probation period → final notice → suppression. |
| Branched (4) | DQS ≥ 70 + `marketing_streams` with per-stream engagement | Evaluates each marketing stream separately: sunsets the streams the person ignores while keeping the one they still click, with one stream-specific notice. |

## Step blueprint (standard, 3 sends)

| Node | When | Channel | Intent | Route |
|---|---|---|---|---|
| s1 | entry +0h at 10:00 user_local | email | Preference choice, nothing to sell: keep everything, fewer (a periodic digest), pause for a while, or stop marketing; one click each | → d1 |
| d1 | s1 +7d | — | Decision on a bot-filtered `link_click` or `preference_updated` (engagement / authoritative) between s1 and s1 +7d | occurred → exit (completed; choice applied) · not_occurred → s2 · unmeasurable → s2 |
| s2 | d1 +0h | email | First reduced-cadence send: the person now gets only the digest; says so plainly, with one click to restore full cadence | → d2 |
| d2 | s2 +30d | — | Decision on bot-filtered `link_click`, `session_start` or `purchase` between s2 and s2 +30d (the probation period, configurable) | occurred → exit (completed) · not_occurred → s3 · unmeasurable → exit (expired; stays on reduced cadence, re-evaluated next cycle) |
| s3 | d2 +0h | email | Final notice: marketing email stops on a stated date; account and transaction messages continue; one click keeps them subscribed | → d3 |
| d3 | s3 +7d | — | Decision on bot-filtered `link_click` or `preference_updated` between s3 and s3 +7d | occurred → exit (completed) · not_occurred → exit (suppressed; record sender-side suppression) · unmeasurable → exit (expired; no suppression) |

Fewer before none: the reduced cadence (s2 onward) is the default outcome of silence; stopping is reached only after silence continues through it. No unmeasurable route leads to suppression.

## Timing and channel fit

- **Email only.** The journey corrects email pressure, so it speaks in email; pushing an unengaged email subscriber by SMS or push to ask about email adds pressure on a second channel.
- Send in the user's daytime (avoid 00:00–06:00 user local). No urgency language: the deadline in s3 is information, not a countdown.
- **Other channels:** push and SMS marketing can be sunset by the same rules only where their engagement is measurable (push open tracked by the app; SMS links tracked and bot-filtered). Where it isn't, those channels are not sunset on silence.
- **Fallback:** if the person's email is no longer deliverable (hard bounce), this journey does not run; the bounce suppression already applies.

## Frequency and overlap

- **Worst path:** 1 send in any rolling 7 days. While an instance is open, every other marketing email to the person is replaced by the reduced cadence; the journey lowers total volume, never adds to it.
- **Usually overlaps with:** [winback](winback.md), [reactivation](reactivation.md), [lead-nurture](lead-nurture.md) (all hand off here), broadcast newsletters and promotions.
- **Precedence:** once a person enters, other marketing journeys defer to it for email. Transactional and service journeys are never affected. A triggered alert the person explicitly requested (back-in-stock, price-drop) may still send and counts as a chance to engage.

## Measurement

- **Primary outcome:** spam-complaint rate of the marketing email stream, compared over 8 weeks before and after launch (with bounce rate and inbox placement alongside).
- **Design:** `pre_post`, no per-user holdout. Reason: the outcome is shared at the domain level; mailbox providers judge the sender as a whole, so a randomized control that keeps mailing unengaged people damages placement for both arms and cannot isolate the effect.
- **Alternative and counter-check:** revenue and conversions attributed to the sunset segment in the 6 months before suppression (expected near zero; if not, the window is wrong), and the re-engagement rate from s1/s2. Optionally, a randomized *delay* (half the eligible group starts 30 days later) measures what the suppression itself costs in revenue, without anyone being mailed indefinitely.
- **Routine communications:** transactional and service messages continue for everyone, in every phase.
- **Contamination risks:** other hygiene work at the same time (bounce pruning, authentication changes), seasonal volume spikes, and mailbox-provider policy changes all move the pre/post numbers.
- **Low volume:** small senders see complaint rates near zero either way; the honest reading is "no damage detected", alongside the volume reduction achieved.

## When data is missing

- **No click tracking, or no bot filtering:** that route is not eligible; the journey reports how many addresses could not be evaluated rather than treating them as silent.
- **No product activity data:** engagement is read from clicks alone, and the journey doc flags that product-active users may be included; recommend joining product activity before launch.
- **No `email_delivered`:** pattern blocked (silence without proof of sending means nothing).
- **No `preference_updated` support in the ESP:** s1 offers keep / stop only; the reduced-cadence step still applies by default.
- **No stream-level data:** Simple or Standard depth; all marketing streams are treated as one.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Spam-complaint rate, marketing stream | primary | pre/post; keep below the deliverability floor |
| Re-engagement rate from s1/s2 | secondary | people who chose a cadence or came back; every one is a person not lost |
| Revenue from the suppressed segment before suppression | guardrail | should be near zero; if not, the window or the engagement definition is wrong |

## Common mistakes

- Defining "unengaged" as "hasn't opened": it suppresses real readers whose mail client hides opens.
- Counting silence on routes where clicks aren't measured.
- Answering silence with more campaigns ("last chance", "we miss you" series) instead of less volume.
- Recording the sunset as an unsubscribe or consent withdrawal: it removes a lawful basis the person never gave up and makes coming back harder.
- Letting the suppression stop receipts, payment notices or security messages.

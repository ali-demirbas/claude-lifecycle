---
name: unengaged-sunset
stage: engagement
trigger_type: absence
journey_class: marketing
required_events: [email_delivered, link_click]
optional_events: [session_start, login, purchase, preference_updated, unsubscribe, spam_complaint, hard_bounce, consent_withdrawn]
required_attributes: []
optional_attributes: [last_engaged_at, consent_date, click_tracking_reliable, marketing_streams, sender_suppression]
default_channels: [email]
base_steps: 3
depth_range: [2, 4]
applicable_industries: [ecommerce, marketplace, saas, subscription-media, travel, fintech, insurance, edtech, mobile-app]
mutually_exclusive_with: []
signal_sources: {email_delivered: authoritative, link_click: engagement, session_start: behavioral, login: behavioral, purchase: authoritative, preference_updated: authoritative, unsubscribe: authoritative, spam_complaint: authoritative, hard_bounce: authoritative, click_tracking_reliable: authoritative, sender_suppression: authoritative, consent_withdrawn: authoritative}
insufficient_alone:
  - no email opens
  - silence on a route where clicks are not measured
  - a quiet period shorter than the configured window
  - few deliveries in the window
  - quiet email while the person is active in the product
  - a click on a preference, pause, stop or help link
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
| `preference_updated` *(optional)* | authoritative | The choice the journey offers, read from the preference system with its value: `keep`, `fewer` (digest), `pause` (with an end date) or `stop`, plus the streams it covers. A recorded choice is a success, whatever it is. A click on a choice link is not a choice until this record exists. |
| `spam_complaint` / `hard_bounce` / `unsubscribe` *(optional)* | authoritative | Not handled here: complaints and hard bounces suppress immediately, unsubscribes are consent changes. Listed so the journey can exclude them. |
| `click_tracking_reliable` *(optional attr)* | authoritative | Per route or per mailbox: whether clicks are tracked and bot-filtered there. |

### Not enough on its own

- **No email opens.** Opens are inflated by privacy proxies and suppressed by image blocking; "never opened" says little about a person. Nothing in this journey reads them.
- **Silence on a route where clicks are not measured.** If links aren't tracked, or bot clicks aren't filtered, or the channel has no click concept, silence there is a measurement gap. Only routes with measurable engagement can make someone unengaged.
- **A quiet period shorter than the configured window.** The window is a business setting (default 180 days without a measurable engagement; shorten it for high-frequency senders, lengthen it for annual-cycle businesses, and change it only with evidence from the business's own re-engagement history).
- **Few deliveries in the window.** Someone sent two emails in six months has not been silent; they have barely been asked. Default minimum: 8 marketing deliveries in the window (configurable).
- **Quiet email while the person is active in the product.** A user who logs in weekly is engaged; their inbox habits are a channel preference, not disinterest.
- **A click on a preference, pause, stop or help link.** A click is not a recorded preference, and it is not engagement either: a stop, pause, unsubscribe or help click is never read as "keep". Only the preference system's `preference_updated` record says what was chosen. Engagement clicks are bot-filtered clicks on content links.

## Entry / exit

- **Entry:** marketing consent valid; at least the minimum number of marketing deliveries in the window; no bot-filtered `link_click`, `session_start`, `login`, `purchase` or `preference_updated` in the window; the route's click tracking is reliable. Also entered by handoff when winback, reactivation or lead-nurture exhaust their lifetime cycles.
- **Exclude:** consent younger than the window (new subscribers are onboarding, not silent); open transactional or service flows are unaffected and need no exclusion; people already sender-suppressed; people already suppressed by a complaint or hard bounce (those are immediate, not sunset); people under the portfolio negative-signal override.
- **Success exit:** any of a content-link `link_click` (bot-filtered; preference, unsubscribe, help and this journey's choice links never count), `session_start`, `purchase`, or a recorded `preference_updated` applied as its value says · **Window:** default 44 days = 7 + 30 + 7 (configurable, tied to the probation length in `d2`).
- **Checked before each send:** content-link `link_click` (bot-filtered), `session_start`, `purchase`, `preference_updated` (any recorded value ends the instance and is applied as recorded), `consent_withdrawn` for marketing email (channel-scoped: a push or SMS opt-out does not end this email journey, and this journey never changes push or SMS consent).
- **How a choice is applied:** the s1 and s3 links open the preference center, which writes `preference_updated`. `keep` keeps full cadence; `fewer` moves the covered streams to the digest; `pause` stops the covered streams until the recorded end date (default 90 days, configurable; the date is stated on the confirmation page and in copy), after which they resume at the cadence held before the pause, and the paused time never counts as silence for a later sunset; `stop` is a consent change recorded in the consent system for the covered streams, not a sender suppression. Stream scope is part of the record: by default all marketing email, or only the stream the email belonged to when the preference center offers per-stream choices. If the preference write failed, the choice is not applied and not assumed from the click: the failure is logged for repair, and no further marketing email goes to the address while a stop or pause request is unresolved (the legal deadline for honoring an unsubscribe runs regardless of a technical failure).
- **What the suppression does:** records `sender_suppression` (reason: unengaged; date; streams covered). Every marketing and lifecycle journey reads it as an exclusion. It never touches transactional or service journeys, and it never edits the consent record. Re-engagement (sign-in, purchase, a bot-filtered content click from a transactional message's account link, or a recorded `preference_updated` of keep or fewer) lifts it. Lifting a sender-side suppression never lifts a consent withdrawal: a person who chose `stop`, or unsubscribed anywhere, stays withdrawn until they grant consent again through the consent system.
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
| s1 | entry +0h at 10:00 user_local | email | Preference choice, nothing to sell: keep everything, fewer (a periodic digest), pause until a stated date, or stop marketing; each link opens the preference center, which records the choice | → d1 |
| d1 | s1 +7d | — | Decision on `preference_updated` (authoritative, preference system, with its value) between s1 and s1 +7d. Clicks on s1's links are not read: only the recorded value counts | occurred → exit (completed; value applied as recorded: keep, fewer, pause with end date, or stop as a consent change) · not_occurred → s2 · unmeasurable → s2 |
| s2 | d1 +0h | email | First reduced-cadence send: the person now gets only the digest; says so plainly, with one link to the preference center to restore full cadence | → d2 |
| d2 | s2 +30d | — | Decision on any_of(content-link `link_click` (engagement, bot-filtered), `session_start` (behavioral), `purchase` (authoritative)) between s2 and s2 +30d (the probation period, configurable) | occurred → exit (completed) · not_occurred → s3 · unmeasurable → exit (expired; the pre-instance cadence is restored and the measurement gap is logged for repair; re-evaluated next cycle once engagement is measurable again) |
| s3 | d2 +0h | email | Final notice: marketing email stops on a stated date (s3 +7d, the moment of d3); account and transaction messages continue; one link to the preference center keeps them subscribed | → d3 |
| d3 | s3 +7d | — | Decision on any_of(`preference_updated` (authoritative, with its value), content-link `link_click` (engagement, bot-filtered), `session_start` (behavioral), `purchase` (authoritative)) between s3 and s3 +7d. A click on s3's own keep, stop or help link is not a member: the keep choice counts only once recorded | occurred → exit (completed; a recorded preference is applied as its value says) · not_occurred → exit (suppressed; record sender-side suppression) · unmeasurable → exit (expired; no suppression) |

Fewer before none: the reduced cadence (s2 onward) is the default outcome of silence; stopping is reached only after silence continues through it. No unmeasurable route leads to suppression or keeps the person on reduced cadence: missing data restores the cadence they had before the instance.

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
- **No `preference_updated` support in the sending tool:** s1 offers stop only, through the standard unsubscribe that writes the consent record; "keep" cannot be offered because a click cannot record it. The reduced-cadence step still applies by default.
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
- Reading a click on the choice email as "engaged, keep": the stop and help links get clicked too, and scanners click everything. Only the recorded preference value decides.
- Lifting a sender suppression and, with it, a consent withdrawal: the two live in different records and only the person can restore consent.

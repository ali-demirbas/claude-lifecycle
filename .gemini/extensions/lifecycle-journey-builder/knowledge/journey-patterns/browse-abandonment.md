---
name: browse-abandonment
stage: revenue
trigger_type: event
required_events: [view_item, purchase]
optional_events: [add_to_cart, view_item_list, search, add_to_wishlist, consent_withdrawn]
required_attributes: []
optional_attributes: [viewed_item, viewed_category, price, session_view_count, items_owned]
default_channels: [email, push]
base_steps: 3
depth_range: [2, 4]
applicable_industries: [ecommerce, marketplace, travel]
mutually_exclusive_with: []
journey_class: marketing
signal_sources:
  view_item: behavioral
  purchase: authoritative
  add_to_cart: behavioral
  search: behavioral
  add_to_wishlist: behavioral
  items_owned: authoritative
  consent_withdrawn: authoritative
  link_click: engagement
insufficient_alone:
  - a single view_item with no repeat or dwell
  - views from a bot or a session not attributed to a person
  - attention to an item or plan the person already owns or holds
  - a click on a browse message
exit_before_each_send: [purchase, add_to_cart, consent_withdrawn]
reentry: {policy: after_cooldown, cooldown: P14D, on_duplicate_trigger: ignore}
instance_key: interest_key
measurement_default: holdout
---

# Browse Abandonment

Re-engage people who looked at products but never added to cart. Intent is real but much weaker than cart abandonment, and volume is far higher, so this pattern carries the strictest frequency discipline of any revenue journey: it can quietly consume a person's whole weekly message budget if left uncapped. Most qualifying signals should end in no send at all; that is the design working, not failing.

## Required-event signature

| Event | Source | Role |
|---|---|---|
| `view_item` | behavioral | Trigger. Must carry an item id; arms only on repeated or dwelling views, never a single bounce. |
| `purchase` | authoritative | Success exit and exclusion signal. Without it, revenue can't be attributed and the pattern is **blocked**. |
| `add_to_cart` *(optional)* | behavioral | Handoff exit: the moment it fires, the person leaves this journey and [abandoned-cart](abandoned-cart.md) takes over. Untracked, the two patterns double-message. |
| `search` / `view_item_list` *(optional)* | behavioral | Separates directed shoppers (searched, then viewed) from casual browsers; directed intent justifies the push step. A **zero-result search** is the strongest directed signal of all, see the zero-result track below. |
| `items_owned` *(optional attr)* | authoritative | What the person already bought or holds (an item, an active plan, an existing booking). Used to drop attention that isn't purchase interest. |
| `price` *(optional attr)* | authoritative | Entry floor: suppress for low-ticket items where a send costs more goodwill than the sale is worth. |

### Not enough on its own

- **A single `view_item`:** a bounce is not intent. Repeat views or measurable dwell are required.
- **Bot or unattributed views:** crawler traffic, preview fetches and sessions that never resolved to a person don't qualify, however many views they rack up.
- **Attention to something already owned or held:** viewing an item the person already bought, a plan they already have, or a booking they already hold is usually support, comparison or re-reading, not purchase interest. It sends nothing.
- **A click on a browse message:** shows the message was seen; it is a branch signal, never a success.

## Entry / exit

- **Entry:** `view_item` on the same item or category ≥ 2 times (or one view with meaningful dwell, if measurable) within a session, attributed to a contactable person, no `add_to_cart` within 4h, no `purchase`, the item or category is currently available. The qualification rule (how many views, how recent) is configurable; change it only with evidence about which qualifying sessions actually convert.
- **Exclude:** entered browse-abandonment or abandoned-cart in the last 14 days, purchased in the last 7 days, item price below threshold (if known), the viewed item or plan is already owned or held, bot or unattributed sessions, portfolio-wide negative-signal override.
- **Success exit:** `add_to_cart` (hands off to abandoned-cart) or `purchase` · **Window:** 3 days.
- **Checked before each send:** `purchase` and `add_to_cart` (any item: either one ends the browse instance), `consent_withdrawn` scoped to that send's channel (an email unsubscribe stops s1/s3, not a consented push), and the item's current availability. An item that became unavailable isn't shown; if nothing in the subject is available, the send is skipped.
- **Re-entry:** after a 14-day cooldown, a hard floor that is deliberately stricter than abandoned-cart's 7.
- **Instance:** one instance follows one interest key (`instance_key: interest_key`, the viewed item, or the category when qualification was category-level).
- **Repeated trigger while active:** more views of the same item or category are the same interest and are ignored; they never extend the wait before the first send. A different interest key inside an active instance waits for the cooldown.
- **Handoffs:** `add_to_cart` → [abandoned-cart](abandoned-cart.md), queued browse sends suppressed. An `add_to_wishlist` on an unavailable item → [back-in-stock](back-in-stock.md), queued browse sends suppressed.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (2) | DQS < 40 or only required events | One email reminder + one final email. No push; low intent doesn't earn the interruptive channel. |
| Standard (3) | DQS 40–69 | Adds a push nudge between emails for someone who didn't come back. |
| Branched (4) | DQS ≥ 70 + `search` or `add_to_wishlist` | Splits directed shoppers (searched/wishlisted → item-specific track) from casual browsers (category track). |

## Step blueprint (standard, 3 sends)

| Node | When | Channel | Intent | Route |
|---|---|---|---|---|
| s1 | entry +4h | email | Viewed item + 2–3 close alternatives the catalog itself surfaces; helpful catalog tone, zero discount | → d1 |
| d1 | s1 +12h | — | Decision on any_of(`view_item` of this interest key (behavioral), link_click on s1 (engagement, bot-filtered)) between s1 and s1 +12h | occurred → s3 · not_occurred → s2 · unmeasurable → s3 |
| s2 | s1 +12h | push | Short deeplink back to the item | → s3 |
| s3 | s1 +44h | email | Category best-sellers and social proof, then exit; do not extend | → end |

The unmeasurable route skips the push rather than assuming the person went quiet: a low-intent journey only earns the interruptive channel on evidence. The push is not an escalation for a missing click: its reason is [push.md](../channels/push.md)'s recency test (a user-initiated action under 24h old). s2 lands about 20h after the qualifying view (4h arming + 4h + 12h); if quiet hours would release it more than 24h after that view, s2 is skipped, not delayed.

No incentive step at any depth: discounting on a product view trains window-shopping and undercuts the abandoned-cart journey's economics.

Zero-result search track (branched shape, where search events carry a result count): a person who searched and found nothing gets one help-framed follow-up within about 24h: the closest match, the right category, or an honest "we don't carry this, here's the nearest thing", never a generic promo. This is the one entry where a single event (not repeat views) justifies a send, because the intent is stated outright. If the searched term maps to nothing sellable, log it as a merchandising signal instead of messaging the person.

Booking and reservation variant (travel, appointments, any availability search over dates or slots): what the search showed was never held, so availability is re-read before every send and the copy never implies a hold. A slot in the exact range the person searched is offered as that slot; a nearby alternative is labelled plainly as a different date or time from the one searched; a waitlist place is described as reserving nothing, because someone who believes they hold a place plans around it. Same 3-send ceiling, same exits; a booking for the searched window is the success event.

## Timing and channel fit

- **Clock:** user local time; unknown timezone falls back to the market timezone. Push is held through 22:00–09:00 and released at the window's opening; email avoids 00:00–06:00.
- **Channel fit:** email carries the item and its alternatives; push only while the view is under 24h old (push.md's recency test) and only for someone who hasn't come back on their own, and in the branched shape only for directed shoppers. No SMS or WhatsApp at any depth; the intent doesn't justify the cost or the interruption.
- **Fallback:** no push consent → s2 is skipped, not replaced; no email consent → the journey runs push-only with s2 (push) as the single send, re-anchored to entry +4h (s1's slot, still inside push.md's recency test), or not at all for casual browsers.
- **First send:** the wait before s1 is bounded and is never pushed back by more browsing; a message that lands while the person is still choosing competes with what they are choosing.

## Frequency and overlap

- **Worst path, rolling 7 days:** 2 emails + 1 push = 3 marketing sends. With the 14-day cooldown this is the most a person can receive from this pattern in any week.
- **Overlaps:** abandoned-cart, back-in-stock, price-drop and replenishment on the same items or category; welcome/onboarding for new visitors who browse.
- **Precedence:** this pattern ranks lowest in the commerce-recovery group. Any of the patterns above holding the person suppresses browse sends (skipped, not deferred); a browse send that would breach a cap is dropped rather than queued.

## Measurement

- **Primary outcome:** `add_to_cart` or `purchase` of the viewed item or category within 7 days of entry (whole-week window).
- **Design:** journey-level holdout, default 10%, randomized at entry and sticky. The control receives none of this journey's sends.
- **Routine communications both groups keep:** newsletters and campaign sends outside this journey; note their volume so the comparison is read against it.
- **Contamination:** a held-out browser who adds to cart enters abandoned-cart, which is expected; the outcome is measured at `add_to_cart`, before that handoff. Other journeys must not send browse-style content about the same item to the control.
- **Low volume:** high entry volume usually supports a holdout. Low conversion per entrant is the constraint, so expect to need several weeks before a lift read is trustworthy.

## When data is missing

- **No dwell or session view count:** use the repeat-view rule only; never fall back to single views.
- **No click tracking and no repeat `view_item`:** d1 resolves as unmeasurable and the push is skipped.
- **No `add_to_cart`:** the handoff can't fire, so the pattern double-messages with abandoned-cart. Run it only for people with no open cart, and record the gap.
- **No `items_owned`:** the owned-item exclusion can't be applied; exclude at least recent purchasers of the item from order history, and note the residual risk.
- **No bot filtering on web analytics:** require an identified, logged-in or email-resolved session for entry.

## KPIs

| KPI | Type | Note |
|---|---|---|
| Incremental view-to-cart conversion | primary | `add_to_cart` within window, exposed vs holdout (purchase credit flows through abandoned-cart) |
| Revenue per entrant | secondary | attribute only purchases of the viewed item or category |
| Unsubscribe + spam-complaint rate per send | guardrail | tightest ceiling in the portfolio; high volume × low intent is the classic complaint generator |

## Common mistakes

- Triggering on a single fleeting view; a bounce is not intent. Require repeat views or dwell.
- Letting it stack with abandoned-cart; the cart always wins, and browse must stop the moment `add_to_cart` fires.
- Allowing weekly re-entry for heavy browsers; the same person can qualify daily, and without the 14-day floor this becomes a fatigue engine.
- Messaging people about what they already own, such as a customer reading their own plan's page.
- Counting bot traffic as interest; one crawler can create thousands of "qualified" browsers.
- Presenting an alternative date or a waitlist place as if it were the slot the person asked for.

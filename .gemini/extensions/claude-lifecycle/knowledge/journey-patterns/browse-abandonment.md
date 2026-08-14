---
name: browse-abandonment
stage: revenue
trigger_type: event
required_events: [view_item, purchase]
optional_events: [add_to_cart, view_item_list, search, add_to_wishlist]
required_attributes: []
optional_attributes: [viewed_item, viewed_category, price, session_view_count]
default_channels: [email, push]
base_steps: 3
depth_range: [2, 4]
applicable_industries: [ecommerce, marketplace, travel]
---

# Browse Abandonment

Re-engage users who viewed products but never added to cart. Intent is real but much weaker than cart abandonment — and volume is far higher, so this pattern carries the strictest frequency discipline of any revenue journey: it can quietly consume a user's entire weekly message budget if left uncapped.

## Required-event signature

| Event | Role |
|---|---|
| `view_item` | Trigger. Must carry item id; arm only on repeated or dwelling views, never a single bounce. |
| `purchase` | Success exit and exclusion signal. Without it, revenue cannot be attributed — pattern is **blocked**. |
| `add_to_cart` *(optional)* | Hand-off exit: the moment it fires, the user leaves this journey and abandoned-cart takes over. Untracked, the two patterns will double-message. |
| `search` / `view_item_list` *(optional)* | Distinguish directed shoppers (searched, then viewed) from casual browsers — directed intent justifies the push step. A **zero-result search** (`search` with no results, or `view_search_results` with a zero-count param) is the strongest directed signal of all: the user told you exactly what they wanted and left empty-handed — see the zero-result note below. |
| `price` *(optional attr)* | Entry floor: suppress for low-ticket items where a send costs more goodwill than the sale is worth. |

## Entry / exit

- **Entry:** `view_item` on the same item or category ≥ 2 times (or one view with meaningful dwell, if measurable) within a session, no `add_to_cart` within 4h, no `purchase`.
- **Exclude:** entered browse-abandonment or abandoned-cart in the last 14 days, purchased in the last 7 days, item price below threshold (if known).
- **Success exit:** `add_to_cart` (hands off to abandoned-cart) or `purchase` · **Window:** 3 days · **Re-entry:** once per 14 days, hard cap — this is deliberately stricter than abandoned-cart's 7.

## Depth scaling

| Depth class | When | Shape |
|---|---|---|
| Simple (2) | DQS < 40 or only required events | One email reminder + one final email. No push — low intent doesn't earn the interruptive channel. |
| Standard (3) | DQS 40–69 | Adds a push nudge between emails, gated on step-1 non-open. |
| Branched (4) | DQS ≥ 70 + `search` or `add_to_wishlist` | Splits directed shoppers (searched/wishlisted → item-specific track) from casual browsers (category track). |

## Step blueprint (standard, 3 steps)

| # | Wait | Channel | Intent | Branch |
|---|------|---------|--------|--------|
| 1 | +4h after last view | email | Viewed item + 2–3 close alternatives; helpful catalog tone, zero discount | — |
| 2 | +24h | push | Short deeplink back to the item | if step 1 not opened |
| 3 | +48h | email | Category best-sellers and social proof, then exit — do not extend | — |

No incentive step at any depth: discounting on a product view trains window-shopping and undercuts the abandoned-cart journey's economics.

Zero-result search track (branched shape, where search events carry a result count): a searched-and-found-nothing user gets one help-framed follow-up within ~24h — the closest match, the right category, or an honest "we don't carry this, here's the nearest thing" — never a generic promo. This is the one browse-abandonment entry where a single event (not repeat views) justifies a send, because the intent statement is explicit. If the searched term maps to nothing sellable, log it as merchandising signal instead of messaging the user.

## KPIs

| KPI | Type | Note |
|---|---|---|
| View-to-cart conversion | primary | `add_to_cart` within window / journeys entered (purchase credit flows through abandoned-cart) |
| Revenue per entrant | secondary | attribute only purchases of viewed item or category |
| Unsubscribe + spam-complaint rate per send | guardrail | tightest ceiling in the portfolio — high volume × low intent is the classic complaint generator |

## Common mistakes

- Triggering on a single fleeting view — a bounce is not intent; require repeat views or dwell.
- Letting it stack with abandoned-cart — cart always wins; browse must suppress the moment `add_to_cart` fires.
- Allowing weekly re-entry for heavy browsers — the same user can qualify daily; without the 14-day re-entry floor this becomes a fatigue engine.

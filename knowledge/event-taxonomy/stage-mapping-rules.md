---
name: stage-mapping-rules
purpose: Classify custom/unknown events into lifecycle stages when ga4-recommended-events.md has no entry
---

# Stage Mapping Rules for Unknown Events

Apply in order. Stop at the first rule that matches. If none matches, the event goes to the **ask-the-user list** — never guess silently (CLAUDE.md rule 7).

## Rule 1 — Exact/alias lookup

Check [ga4-recommended-events.md](ga4-recommended-events.md) including obvious aliases (`signup` = `sign_up`, `checkout_started` = `begin_checkout`, `order_completed` = `purchase`). An alias match must be reported to the user as an assumption: "treating `order_completed` as `purchase`".

## Rule 2 — Industry playbook lookup

The active industry playbook (`knowledge/industries/<sector>.md`) lists sector-specific expected events. If the event name matches one (exact or alias), take the stage from the playbook's funnel table.

## Rule 3 — Name-pattern heuristics

**Matching is token-based, not substring.** Split the event name on `_` and case boundaries (camelCase) into tokens first; a pattern must match a whole token, never match as a substring inside a longer token. `use` matches `use_feature` (token `use`) but **not** `user_deleted` or `user_invited` (token `user` — contains "use" as a substring, not a full-token match; `user_deleted` should never land in "engagement"). Patterns ending in `_` (like `first_`) are prefix matches against the token sequence, unchanged: `first_` still matches `first_open` and `first_purchase`.

**Within a whole-token match, tolerate the token's inflectional form** — plural, verb tense, gerund, or nominalization of the *same* action: `cancel` also matches `cancelled`/`cancelling`/`cancellation`; `delete` also matches `deleted`/`deletion`; `invite` also matches `invited`/`inviting`. This is still whole-token, not substring, and it never bridges two different words: `user` is a distinct noun from `use`, not an inflection of it, so `use` still does not match `user_deleted` — it correctly matches on `delete`'s family instead (the `deleted` token), landing in winback-adjacent. When it's genuinely unclear whether two tokens share a root or just look similar, treat them as different words — Rule 5's ask-the-user path is the safe default, not a rule to stretch.

| Pattern in event name | Stage | Confidence |
|---|---|---|
| `purchase`, `order`, `payment`, `subscribe`, `deposit`, `booking_confirm` | revenue | high |
| `cart`, `checkout`, `wishlist`, `quote`, `plan_view`, `pricing` | revenue-intent | high |
| `signup`, `register`, `onboard`, `tutorial`, `activate`, `first_` | activation | high |
| `login`, `view`, `search`, `play`, `read`, `use`, `click`, `open` | engagement | medium |
| `invite`, `share`, `refer` | engagement (referral signal) | medium |
| `cancel`, `churn`, `delete`, `delete_account`, `unsubscribe`, `remove` | winback-adjacent (negative) | high |
| `fail`, `error`, `declined` | protect (payment-failure family) | medium |

Medium-confidence matches are applied but listed in the output under "assumed mappings — please confirm". A medium-confidence match on one of the generic engagement tokens (`view`, `click`, `open` especially) still goes through the noise-exclusion judgment `event-analyst` step 4 already applies (page_view/scroll/session-style noise) before it counts toward anything — a technically-matched pattern that is noise doesn't get to skip that filter just because Rule 3 assigned it a stage.

## Rule 4 — Parameter-based promotion

An event classified as acquisition, activation, or engagement that carries monetary parameters (`value`, `price`, `revenue`, `currency`) is promoted to **revenue-intent** — the parameter is the stronger signal regardless of which stage the name alone suggested. A B2B `demo_scheduled` or `quote_requested` custom event carrying a deal `value` is exactly as much a revenue-intent signal as a commerce `view_item` carrying one; scoping this rule to engagement-only left the acquisition/activation cases silently unpromoted.

## Rule 5 — Everything else → ask

Batch the unmapped events into ONE question to the user (max 10 events per question, with your best guess pre-filled per event). Do not block the whole pipeline: continue with mapped events, mark dependent journeys as provisional.

## Output contract

`lifecycle-map` must always emit:
1. Mapped table: event → stage → source rule (lookup / playbook / heuristic / user).
2. Assumed mappings needing confirmation.
3. Unmapped events (asked or pending).
4. Stage coverage summary: which stages have zero **meaningful** events — noise excluded per `event-analyst` step 4 doesn't count as coverage just because Rule 3 matched it a stage. These zero-meaningful-event stages are the **blind stages** the portfolio report must call out.

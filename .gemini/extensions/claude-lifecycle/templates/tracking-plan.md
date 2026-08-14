# Tracking Plan Template

Output of the journey engine's gap analysis: events/attributes worth adding, ranked by the journeys they unlock.

---

# Tracking Plan — <Company / Project>

**Generated:** <date> · **Current DQS:** <n>/100 · **Projected DQS if implemented:** <n>/100

## 1. Missing events (required)

| ID | Priority | Event to add | Suggested GA4 name | Parameters | Unlocks |
|---|---|---|---|---|---|
| E-01 | P0 | <plain-language behavior> | `<snake_case_name>` | `value: number; currency: string; items: array` | <journey ids / depth upgrades> |
| … | | | | | |

Naming rules: follow GA4 recommended events where one exists ([ga4-recommended-events.md](../knowledge/event-taxonomy/ga4-recommended-events.md)); otherwise `snake_case`, verb-first, ≤ 40 chars.

Parameters rule: list **every** parameter the event needs, semicolon-separated `name: type` pairs — never just one illustrative example. A conversion/revenue event that ships with `value` but not `currency`+`items` is "tracked" by name only; `event-analyst`'s parameter-completeness check (and DQS's Conversion events component) score it as incomplete, so an under-specified Parameters cell here is exactly how a developer implements to the letter of the ticket and still misses the DQS points the event was meant to unlock. If an event genuinely takes no parameters, write `—`, not a blank cell — a blank reads as "not yet specified," not "specified as none."

ID rule: `E-nn` is stable across regenerations of this file for the *same* missing event — if a prior tracking plan already assigned `E-03` to `add_to_wishlist` and it's still missing, keep `E-03`, don't renumber. This is what makes a row referenceable from a ticket title or commit message without the reference going stale the next time `/lifecycle connect` regenerates the plan.

## 2. Missing user attributes *(if applicable)*

| ID | Priority | Attribute | Why | Unlocks |
|---|---|---|---|---|
| A-01 | | | | |

## 3. Implementation notes (required)

- Where each event should fire (page/screen/server), one line each.
- Consent implications, if any.
- Renamed/retired events silently break live journey triggers — every rename in this plan must be checked against the triggers in the active journey portfolio before it ships.

## 4. Re-run instruction (required)

One line telling the user to re-run `/lifecycle connect` after implementation to re-score and unlock blocked journeys.

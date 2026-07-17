---
name: <channel-slug>
consent_required: <the actual regime(s), named — OS-level opt-in, TCPA/İYS/GDPR opt-in, or "none" if the channel is genuinely zero-consent-risk (e.g. in-app, rendered only to a live session). Don't write "consent required" without saying which regime.>
frequency_cap: <n> marketing <messages/period-unit> / user / <period> (default; user-adjustable — see knowledge/compliance/consent-and-quiet-hours.md)
quiet_hours: <window in user local time>, or "not applicable" with the one-line reason (in-app: message only appears when the user is already present)
limits:
  <field_name>: {max: N, unit: chars, note: "optional context, e.g. platform truncation behavior"}
  # One line per character-limited field the channel actually has — field
  # names here become the canonical keys scripts/validate_output.py checks
  # copy-doc table rows against (see FIELD_ALIASES/LIMIT_KEY_ALIASES if the
  # copy-doc field name differs from this key, e.g. cta_label -> cta).
  # A non-length constraint (max BUTTON COUNT, not char count) omits
  # `unit: chars` entirely — load_channel_limits() only treats a `unit: chars`
  # entry as a character ceiling; anything else is documentation only, the
  # same convention in-app.md's `ctas: {max: 2, ...}` already uses.
---

# <Channel Name> — Channel Rules

One paragraph: this channel's cost and intrusiveness relative to the others already defined here, what it's structurally good at, and what it's structurally bad at (a channel that's excellent at one thing is often unusable for another — in-app can't reach an absent user, SMS is too expensive for routine content, email is too slow for a 2-hour relevance window). Name the failure mode explicitly; "use for important things" isn't a rule a reviewer can check.

## Hard rules (copy fails review if violated)

Numbered list. Every line is a real constraint (platform-enforced or regulatory), not a stylistic preference — `copy-reviewer`'s checklist treats each one as a FIX trigger, so state it as a fact with a threshold, not general advice. Cover, in whatever order makes sense for this channel: character/count limits (counted, not estimated), consent and its exemptions (transactional vs marketing), quiet hours, sender/identity requirements, personalization-variable fallback requirements, and anything platform-specific that silently breaks copy that "looks" fine (SMS's GSM-7/UCS-2 split, WhatsApp's template-category mismatch, push's OS truncation).

## <Structure guidance — name this section for what actually varies here: "Message anatomy" (SMS), "Format selection" (in-app), "Template design guidance" (WhatsApp), or just "Structure guidance">

How to actually write inside the limits: what goes first, what's load-bearing if the rest truncates, the channel's characteristic shape. Include a worked example if the anatomy is non-obvious (SMS's fixed field order is a good model).

## When to prefer <channel> over other channels

| Situation | Verdict |
|---|---|
| <the situation this channel is structurally best at> | ✅ |
| <a situation another channel handles better> | ❌ <which channel, in one line> |

This table is what `lifecycle-copy`/`lifecycle-journeys` actually consult when a step's channel choice is in question — make the ❌ rows name the better channel, not just reject this one.

---

**New file from this template vs. extending an existing channel's file:** a new file is for a genuinely new *delivery channel* — its own consent regime, its own platform enforcement, its own line in the portfolio's frequency-cap conflict review. A new *message type within* a channel that already has a file (rich media on a push notification, a new in-app widget shape, a WhatsApp interactive-list message) is not a new channel: extend the existing file's `limits:` block and add a row to its format-selection table, the way `in-app.md`'s own banner/modal/full-screen split already lives in one file, not three. The test: does this need its own consent tracking and its own frequency-cap line? If yes, new file from this template. If no, it's a section in the channel that already exists.

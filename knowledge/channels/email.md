---
name: email
consent_required: opt-in (KVKK/GDPR); implied consent varies by region — see compliance file
frequency_cap: 4 marketing emails / user / week (default; user-adjustable)
quiet_hours: none required, but respect send-time optimization — see knowledge/send-time.md
limits:
  subject: {min: 20, max: 50, unit: chars}
  preheader: {min: 40, max: 90, unit: chars}
  body: {max: 350, unit: chars, note: "lifecycle emails, not newsletters — chars, aligned with copy-output.md; a word count can't be recounted by validate_output.py"}
  cta_label: {max: 20, unit: chars}
---

# Email — Channel Rules

The default lifecycle channel: cheap, rich formatting, tolerant of longer waits. Everything here sits on the deliverability floor in [knowledge/deliverability.md](../deliverability.md) — spam-rate ceiling, authentication, one-click unsubscribe; a journey that violates that floor unsends every other journey on the domain. Weak at immediacy — never use email alone for time-critical triggers (flash price drops, OTP-adjacent flows).

## Hard rules (copy fails review if violated)

1. Subject 20–50 chars, sentence case, no trailing punctuation except `?`.
2. Preheader 40–90 chars and NOT a repeat of the subject — it extends it.
3. Exactly **one primary CTA**. A plain-text secondary link is allowed; a second button is not.
4. CTA label starts with a verb, ≤ 20 chars ("Sepeti tamamla", "See your plan" — never "Click here" / "Tıkla").
5. Personalization variables must have a fallback defined, or the copy block must include the no-var Fallback version.
6. Unsubscribe link is assumed present via ESP footer — copy must never say "reply to unsubscribe".
7. Max 1 emoji in subject, only if the lexicon's emoji policy allows it. None in CTA.

## Spam-trigger words (banned in subject/preheader)

free!!!, guaranteed, act now, winner, 100% free, no cost, ÜCRETSİZ (caps), KAZANDINIZ, "RE:"/"FWD:" fakery, currency symbols repeated (₺₺₺/$$$), all-caps words, > 1 exclamation mark.

## Structure guidance

- First line of body restates the trigger context in the user's terms ("Sepetinde 2 ürün seni bekliyor").
- One idea per email. If the intent line in the journey step needs "and", split the step.
- Plain, short paragraphs (≤ 3 lines rendered mobile). Bullets over prose for product lists.

## When to prefer email over other channels

| Situation | Verdict |
|---|---|
| Rich content (multiple products, education) | ✅ email |
| Time-critical (< 2h relevance window) | ❌ use push/SMS |
| No email consent but push consent exists | ❌ obvious, but check consent per step, not per journey |
| Winback of long-dormant users | ✅ email is usually the only surviving consent |

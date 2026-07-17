---
name: whatsapp
consent_required: explicit opt-in with clear channel disclosure (İYS-registered in TR, GDPR opt-in EU); Meta additionally requires per-template approval for business-initiated messages
frequency_cap: 2 marketing WhatsApp messages / user / week (default; user-adjustable — see compliance file)
quiet_hours: "20:00–10:00 user local time + no Sundays (per compliance baseline)"
limits:
  header: {max: 60, unit: chars, note: "text header; media headers have no text limit"}
  body: {max: 1024, unit: chars, note: "platform max — recommend ≤ 300 for marketing templates"}
  button_label: {max: 25, unit: chars}
---

# WhatsApp — Channel Rules

A conversational channel with platform-enforced quality policing: Meta scores every business number, and users who block you lower that rating until your sends get throttled or your templates rejected. Treat WhatsApp like a channel where every recipient holds a ban button — because they do. **TR-market note: WhatsApp is a primary messaging channel in Türkiye (as across LATAM), often with better reach than email for consumer audiences — in TR-focused portfolios it deserves consideration as a first-class lifecycle channel, not an afterthought.**

## Hard rules (copy fails review if violated)

1. Every business-initiated message uses a **pre-approved template** in one of three categories — `marketing`, `utility`, `authentication` — and the copy must match its declared category. Miscategorizing marketing as utility gets the template rejected or reclassified by Meta, and repeat offenses damage account standing.
2. Category choice matters twice: **pricing** (per-conversation rates differ by category; marketing is the most expensive) and **approval** (utility/authentication templates face stricter content review — any promotional wording forces marketing category).
3. **24-hour customer-service window:** after a user messages you, you may reply free-form (and cheaper) for 24 hours. Outside that window, only approved templates may initiate. Journeys must state which mode each step uses — a "reply within the window" step and a "template send" step are different animals in cost, content freedom, and compliance.
4. Opt-in is explicit and channel-specific: the user must have agreed to receive WhatsApp messages from this brand (İYS-registered in TR). Email consent does not transfer. No cold template blasts to imported phone lists — Meta bans for this independently of the regulator.
5. Structure limits, counted: header ≤ 60 chars (text), body ≤ 1024 chars, button labels ≤ 25 chars. For marketing templates, keep body ≤ 300 chars — WhatsApp is a chat surface; a wall of text reads as spam and invites blocks.
6. Buttons over links: use quick-reply or CTA buttons instead of raw URLs where possible. Max 1 URL button, on a branded domain.
7. Quiet hours 20:00–10:00 user local + no Sundays (compliance baseline), and cap 2 marketing messages/week — the frequency cap here protects quality rating as much as compliance.
8. Personalization variables ({{1}}, {{2}} in template syntax) must have fallbacks defined at send time; Meta rejects sends with missing variables.

## Quality-rating risk (why restraint is enforced, not optional)

Meta continuously rates each sending number from user feedback — blocks and "report spam" taps weigh heaviest. A falling rating triggers, in order: reduced messaging tier (daily send caps shrink), template pausing, and ultimately number suspension. One over-aggressive campaign can throttle *all* journeys on the number, including transactional ones. Design consequence: any journey step on WhatsApp must clear a higher relevance bar than the same step on email, and portfolio conflict review should treat WhatsApp sends as a shared, depletable resource.

## Template design guidance

- Open with the reason the user is getting this, in their terms — first line shows in the chat-list preview.
- One message = one intent = one primary button. Marketing templates with 3 CTA buttons underperform and look desperate.
- Media headers (image/product card) earn attention on commerce triggers; keep the body doing the work of a caption, not a brochure.
- Write like a person messaging, not a newsletter: short sentences, no ALL CAPS, no exclamation stacking.

## When to prefer WhatsApp over other channels

| Situation | Verdict |
|---|---|
| TR/LATAM consumer audience with WhatsApp opt-in | ✅ often the highest-attention channel available |
| Conversational follow-up inside the 24h service window | ✅ free-form, cheap, natural |
| Rich but urgent commerce trigger (order issue, booking change, back-in-stock with image) | ✅ template with media header |
| Long-form content, education, multi-product digests | ❌ email |
| Low-relevance batch promo | ❌ nowhere, but especially not here — quality rating pays the bill |

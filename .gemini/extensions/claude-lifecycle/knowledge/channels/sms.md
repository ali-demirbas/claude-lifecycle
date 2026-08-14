---
name: sms
consent_required: strictest of all channels — TCPA prior express written consent (US), İYS-registered opt-in (TR), GDPR opt-in (EU); never soft opt-in
frequency_cap: 2 marketing SMS / user / week (default; user-adjustable — see compliance file)
quiet_hours: "20:00–10:00 user local time + no Sundays (per compliance baseline; İYS practice)"
limits:
  body: {max: 160, unit: chars, note: "GSM-7 single segment; drops to 70 if any UCS-2 char — see encoding rules"}
  body_unicode: {max: 70, unit: chars, note: "single segment when Turkish chars force UCS-2"}
  opt_out: {note: "opt-out instruction counts against the limit — budget ~15–25 chars for it"}
  link: {note: "one link max, short branded domain only"}
---

# SMS — Channel Rules

The most expensive and most intrusive channel: it interrupts, it costs per segment, and one regulatory mistake (TCPA class action, İYS fine) costs more than a year of sends. SMS is reserved for messages that would justify a phone buzz — OTP-adjacent flows, time-critical windows, and high-value moments only. If a message would also work as an email tomorrow morning, it is not an SMS.

## Hard rules (copy fails review if violated)

1. Single segment by default: **160 chars GSM-7** or **70 chars UCS-2** — counted against the correct encoding, not estimated. Multi-segment SMS requires explicit user approval per journey step (concatenated segments count 153 GSM-7 / 67 UCS-2 each).
2. **Turkish encoding trap, called out explicitly:** `ş`, `ğ`, `ı`, `İ` are not in the GSM-7 default alphabet; national shift tables exist but carrier support is unreliable. `ç`/`ö`/`ü` alone survive GSM-7, but real Turkish copy almost always contains at least one of the former — so **any TR-language SMS must be counted at the 70-char UCS-2 limit** unless it is verified ASCII-only ("Sepetin seni bekliyor" is safe; "yaşadığınız şehir" is not).
3. The opt-out instruction ("Çıkış: IPTAL yaz" / "Reply STOP to opt out") is part of the message and **counts inside the character limit**. Budget it before writing the body.
4. Sender ID must be the registered alphanumeric brand sender (TR: İYS-registered başlık). Never a raw long number for marketing; never a sender the user won't recognize instantly.
5. Consent is the strictest tier: TCPA prior express *written* consent (US), İYS-registered opt-in (TR), GDPR opt-in (EU). Transactional exemption applies only to genuinely transactional content — one promotional word converts the message to marketing and voids the exemption.
6. Exactly one link, if any — **shortened on a branded domain** (e.g. `brnd.co/x1`), never a generic shortener (`bit.ly` links get carrier-filtered and erode trust).
7. **No emoji.** Beyond tone, a single emoji forces UCS-2 and halves the character budget.
8. Quiet hours 20:00–10:00 user local + no Sundays are mandatory (compliance baseline). Journeys must schedule around them, not queue into a 10:00 burst.
9. No personalization variable without a fallback; a broken `{{first_name}}` in 70 chars is a third of the message wasted.

## Message anatomy (single segment)

`[Sender context if not obvious] + [one fact] + [one action/link] + [opt-out]`

Example (GSM-7, 92 chars): `Acme: Sepetindeki urun icin stok az kaldi. Tamamla: brnd.co/x1 Cikis: IPTAL yaz`
Note the deliberate ASCII spelling — an accepted TR-SMS practice to stay in GSM-7; if the brand requires proper diacritics, count at 70. **Folding diacritics is a cost decision, not a default: it requires explicit user approval per brand, applies to SMS only, and is never carried into email/push/in-app copy. The approval must be RECORDED — brand config `sms_ascii_fold: approved` or the user's explicit yes in this run; absent that record, count at UCS-2/70 and ask, never assume.**

## When SMS is justified (cost + intrusiveness test)

Send SMS only when **all three** hold: the user cannot reasonably be reached in time on a cheaper channel, the information decays within hours, and the value to the *user* is concrete.

| Situation | Verdict |
|---|---|
| OTP-adjacent / security / delivery-today updates | ✅ (transactional) |
| Time-critical, high-value: price-drop on a tracked item expiring today, back-in-stock of a wishlisted item, payment failure about to cancel service | ✅ marketing SMS |
| Abandoned cart, generic promo, winback, newsletter-ish content | ❌ email (or WhatsApp if opted in) |
| "Journey needs a third touch" | ❌ never a justification |

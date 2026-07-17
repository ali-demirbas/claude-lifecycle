---
name: push
consent_required: OS-level opt-in (iOS explicit, Android 13+ explicit)
frequency_cap: 1 marketing push / user / day, 5 / week (default; user-adjustable)
quiet_hours: "22:00–09:00 user local time (default, mandatory unless user overrides); within the allowed window, see knowledge/send-time.md for optimization"
limits:
  title: {max: 40, unit: chars, note: "iOS truncates ~40; Android allows more (~65) but the ceiling here is the cross-platform floor, not a per-OS split — see body text below"}
  body: {max: 120, unit: chars, note: "visible without expanding on iOS; Android's collapsed view is looser (~150-240 depending on device/OS version)"}
  cta_label: {max: 20, unit: chars, note: "deeplink button label, where supported"}
  image: {max: 1, unit: MB, note: "cross-platform floor: FCM (Android) caps notification images at 1MB (Firebase's own doc); APNs (iOS) allows attachments up to 10MB via a Notification Service Extension, but the image is fetched from its URL at delivery time, not embedded in the ~4KB APNs payload itself — 1MB is the number that holds on both platforms, same 'tighter number wins' logic as the title/body ceilings above"}
---

# Push — Channel Rules

Highest immediacy, lowest tolerance. Every bad push costs OS-level permission that never comes back. Use for time-sensitive, high-relevance triggers only; never for "we miss you" filler.

## Hard rules (copy fails review if violated)

1. Title ≤ 40 chars, body ≤ 120 chars — counted, not estimated. This is the iOS-conservative floor, not a blended average: Android tolerates noticeably more (title ~65, body ~150-240 depending on device) before its own truncation kicks in, but this engine has no per-OS send-time targeting today, so one number has to hold for both — the tighter one, since writing to iOS's limit never breaks on Android, and the reverse isn't true.
2. Title and body must each make sense **alone** (either may be truncated by the OS).
3. Must deeplink to the exact relevant screen (cart, product, feature) — never to the app home.
4. No personalization variable in the title unless a fallback exists (an empty `{{first_name}}` in a push is unrecoverable).
5. Quiet hours are mandatory. Journeys must schedule around them, not just delay into a 09:00 burst (stagger 09:00–11:00).
6. Max 1 emoji total, never as the first character, none in TR finance/health contexts.
7. Never send the same intent on push and email within the same 4-hour window (cross-channel dedupe).

## Permission priming (hard rule)

**Never fire the OS push-permission dialog cold.** A denied OS prompt is nearly unrecoverable — the user must dig through system settings to reverse it — so a cold prompt gambles the channel for the duration of the relationship.

- Show an in-app priming message first that explains the **specific, concrete value** of enabling push ("order updates and price alerts on your saved items" — not "stay in the loop").
- Trigger the system prompt **only after an affirmative tap** on the priming message. A "not now" on the priming layer costs nothing and can be retried later; a "Don't Allow" on the OS layer cannot.
- Journeys for app products must place the priming moment at a **point of demonstrated value** (first order placed, first item saved, first goal set) — never at first launch, when the app has earned nothing yet.

## Rich media (image, optional)

- HTTPS URL only, and it must resolve before send — a broken image URL degrades silently to a text-only push on most OSes rather than erroring, the same "fails silent, not loud" risk `docs/crm-export-mapping.md`'s Trigger Health section already flags for triggers.
- ≤ 1MB (see `limits.image` above) — Android/FCM's own ceiling; iOS/APNs tolerates far more, but 1MB is the number that holds on both.
- Always pair with alt text describing the image. A meaningful share of devices and notification-center states never render the image at all, so title+body must already carry the full message alone (rule 2 above) — the image is an enhancement, never the payload, and the alt text is what a screen reader speaks in its place.
- Not every push needs one — reserve for triggers where a picture adds real information (price-drop with the product photo, back-in-stock item), not decoration for its own sake.

## What earns a push (relevance test)

A push is justified only if at least one is true:
- The trigger is user-initiated and recent (< 24h): abandoned cart/checkout, back in stock on wishlisted item.
- The information decays fast: price drop, delivery update, live event.
- The user explicitly opted into the topic (order updates, price alerts).

"Journey step needs a second channel" is NOT a justification by itself — downgrade to email or in-app.

## Structure guidance

- Lead with the payload, not the brand: "Sepetindeki ürünün fiyatı düştü" beats "Acme'de fırsat!".
- Numbers and product names outperform adjectives; use real data variables (`{{price}}`, `{{product_name}}`).
- The body's last 20 chars should not carry critical info (truncation risk on small screens).

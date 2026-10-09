# Copy — Cart Recovery (`ecom-abandoned-cart-01`)

**Language:** TR · **Locale overlay:** [tr](../../knowledge/lexicons/locales/tr.md) · **Lexicon:** [ecommerce](../../knowledge/lexicons/ecommerce.md) · **Brand:** — · **Tone:** warm, concrete, product-forward · sen-form
**Audience/persona:** identified shoppers with a non-empty cart 1 hour after their last `add_to_cart` and no purchase since
**Review status:** ✅ passed copy-reviewer · `validate_output.py` 2.0.0 recount passed · covers sends `s1`–`s3` only

Covers the first three sends (`s1`, `s2`, `s3`) of [03-journey-cart-recovery.md](03-journey-cart-recovery.md); `s4`–`s8` are produced the same way on request, so this file is not the journey's complete copy. Channel rules applied: [email](../../knowledge/channels/email.md) (subject 20–50, preheader 40–90, body ≤ 350, CTA ≤ 20), [push](../../knowledge/channels/push.md) (title ≤ 40, body ≤ 120). All counts are actual character counts of the literal text including `{{variables}}`.

## Step 1 — email (`step-1`)

**Intent:** Cart reminder: contents + free-shipping threshold, zero pressure · **Target tone:** helpful reminder, zero guilt

### Variant A — "helpful reminder"

```json
{"strategy": "utility", "hypothesis": "Stating the cart's practical facts (saved for 7 days, free shipping over 1500 TL, easy returns) recovers more carts than a convenience angle for first-time abandoners"}
```

| Field | Content | Chars | Limit |
|---|---|---:|---|
| Subject | Sepetin seni bekliyor: {{product_name}} | 39 | 20–50 |
| Preheader | Ayırdığın ürünler sepetinde duruyor. 1500 TL üzeri kargo bedava. | 64 | 40–90 |
| Body | Merhaba {{first_name}}, sepetine eklediğin {{product_name}} ve yanındaki ürünler sepetinde duruyor. Sepetin 7 gün boyunca saklanır, 1500 TL üzeri siparişlerde kargo bedava ve iade 30 gün içinde kolayca yapılır. | 210 | ≤ 350 |
| CTA | Sepeti tamamla | 14 | ≤ 20 |

### Variant B — "saved effort / convenience"

```json
{"strategy": "progress", "hypothesis": "Telling shoppers their size and colour choices are saved recovers more carts than restating shipping and returns terms, because the remaining effort feels smaller"}
```

| Field | Content | Chars | Limit |
|---|---|---:|---|
| Subject | {{product_name}} hâlâ sepetinde | 31 | 20–50 |
| Preheader | Beden ve renk seçimin kayıtlı. Kaldığın yerden tek adımda devam edebilirsin. | 76 | 40–90 |
| Body | Merhaba {{first_name}}, {{product_name}} için seçtiğin beden ve renk hâlâ sepetinde kayıtlı. Tekrar seçim yapmana gerek yok, kaldığın yerden tek adımda devam edebilirsin. Aklına takılan bir şey olursa bu e-postayı yanıtlaman yeterli. | 233 | ≤ 350 |
| CTA | Sepete dön | 10 | ≤ 20 |

### Fallback (short)

| Field | Content | Chars | Limit |
|---|---|---:|---|
| Subject | Sepetindeki ürünler seni bekliyor | 33 | 20–50 |
| Preheader | Seçtiğin ürünler sepetinde duruyor. Dilediğin zaman devam edebilirsin. | 70 | 40–90 |
| Body | Merhaba, sepetine eklediğin ürünler seni bekliyor. Dilediğin zaman alışverişine devam edebilirsin. | 98 | ≤ 350 |
| CTA | Sepete dön | 10 | ≤ 20 |

## Step 2 — push (`step-2`)

**Intent:** Checkout continuation: resume payment step, deeplink to checkout · **Target tone:** calm, practical
**Deeplink:** checkout screen (never app home). Sent on `d1` = occurred (`begin_checkout` seen in the first 5 hours). No variables in titles (push rule 4).

### Variant A — "one step left"

```json
{"strategy": "progress", "hypothesis": "Framing the order as one step from done converts checkout abandoners better than reminding them their details are saved"}
```

| Field | Content | Chars | Limit |
|---|---|---:|---|
| Title | Ödemeye bir adım kaldı | 22 | ≤ 40 |
| Body | Sepetin hazır, ödeme adımında bekliyor. Kaldığın yerden bir dakikada tamamlayabilirsin. | 87 | ≤ 120 |
| CTA | Ödemeyi tamamla | 15 | ≤ 20 |

### Variant B — "saved details"

```json
{"strategy": "utility", "hypothesis": "Reassuring that address and shipping choices are saved converts checkout abandoners better than a progress frame"}
```

| Field | Content | Chars | Limit |
|---|---|---:|---|
| Title | Sepetin ödeme adımında bekliyor | 31 | ≤ 40 |
| Body | Adres ve kargo seçimlerin kayıtlı. Siparişini tek adımda tamamlayabilirsin. | 75 | ≤ 120 |
| CTA | Siparişi tamamla | 16 | ≤ 20 |

### Fallback (short)

| Field | Content | Chars | Limit |
|---|---|---:|---|
| Title | Sepetin ödeme adımında | 22 | ≤ 40 |
| Body | Kaldığın yerden devam edebilirsin. Sepetin ödeme adımında bekliyor. | 67 | ≤ 120 |
| CTA | Devam et | 8 | ≤ 20 |

## Step 3 — push (`step-3`)

**Intent:** Short cart nudge, deeplink to cart · **Target tone:** light, no pressure
**Deeplink:** cart screen. Sent on `d1` = not_occurred or unmeasurable (no `begin_checkout` seen in the first 5 hours, or it couldn't be read); scheduled outside quiet hours.

### Variant A — "named product"

```json
{"strategy": "utility", "hypothesis": "Naming the product in the push body brings more shoppers back to the cart than a light question with no product named"}
```

| Field | Content | Chars | Limit |
|---|---|---:|---|
| Title | Ayırdıkların sepetinde duruyor | 30 | ≤ 40 |
| Body | {{product_name}} sepetinde seni bekliyor. Göz atmak için dokun. | 63 | ≤ 120 |
| CTA | Sepete git | 10 | ≤ 20 |

### Variant B — "light question"

```json
{"strategy": "curiosity", "hypothesis": "A light question title earns more cart returns than a statement for shoppers who left without starting checkout"}
```

| Field | Content | Chars | Limit |
|---|---|---:|---|
| Title | Sepetini mi unuttun? | 20 | ≤ 40 |
| Body | Seçtiğin ürünler sepetinde duruyor. İstediğin an devam edebilirsin. | 67 | ≤ 120 |
| CTA | Sepete git | 10 | ≤ 20 |

### Fallback (short)

| Field | Content | Chars | Limit |
|---|---|---:|---|
| Title | Sepetin seni bekliyor | 21 | ≤ 40 |
| Body | Ayırdığın ürünler sepetinde duruyor. Devam etmek için dokun. | 60 | ≤ 120 |
| CTA | Sepete git | 10 | ≤ 20 |

---

**Personalization variables used:** `{{first_name}}`, `{{product_name}}` (CRM-agnostic `{{snake_case}}`). Every variable has the no-var Fallback block above; `{{product_name}}` appears only in bodies/subjects, never in push titles.

**Reviewer checklist applied:** sen-form throughout · no banned words ("kaçırma", "SON ŞANS", all-caps, "tıkla" as bare CTA, "değerli müşterimiz") · zero exclamation marks · no emoji · no em dashes in customer-facing text · urgency only via real data (the 7-day cart lifetime in step 1 Variant A is the actual purge policy) · one primary CTA per message · preheaders extend, not repeat, subjects · push titles and bodies each stand alone · each variant carries a falsifiable strategy/hypothesis label.

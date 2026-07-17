# Copy — Cart Recovery (`ecom-abandoned-cart-01`)

**Language:** TR · **Lexicon:** [ecommerce](../../knowledge/lexicons/ecommerce.md) · **Tone:** warm, concrete, product-forward · sen-form
**Review status:** ✅ passed copy-reviewer

Covers steps 1–3 of [03-journey-cart-recovery.md](03-journey-cart-recovery.md). Steps 4–8 are produced the same way on request. Channel rules applied: [email](../../knowledge/channels/email.md) (subject 20–50, preheader 40–90, CTA ≤ 20), [push](../../knowledge/channels/push.md) (title ≤ 40, body ≤ 120). All counts are actual character counts of the literal text including `{{variables}}`.

## Step 1 — email (`step-1`)

**Intent:** Cart reminder: contents + free-shipping threshold, zero pressure

### Variant A — "helpful reminder"

| Field | Content | Chars | Limit |
|---|---|---:|---|
| Subject | Sepetin seni bekliyor: {{product_name}} | 39 | 20–50 |
| Preheader | Ayırdığın ürünler sepetinde duruyor. 1500 TL üzeri kargo bedava. | 64 | 40–90 |
| Body | Merhaba {{first_name}},<br><br>Sepetine eklediğin {{product_name}} ve yanındaki ürünler sepetinde duruyor.<br><br>• Sepetin 7 gün boyunca saklanır.<br>• 1500 TL üzeri siparişlerde kargo bedava.<br>• İade 30 gün içinde, kolay. | 35 words | ≤ 500 words |
| CTA | Sepeti tamamla | 14 | ≤ 20 |

### Variant B — "saved effort / convenience"

| Field | Content | Chars | Limit |
|---|---|---:|---|
| Subject | {{product_name}} hâlâ sepetinde | 31 | 20–50 |
| Preheader | Beden ve renk seçimin kayıtlı. Kaldığın yerden tek adımda devam edebilirsin. | 76 | 40–90 |
| Body | Merhaba {{first_name}},<br><br>{{product_name}} için seçtiğin beden ve renk hâlâ sepetinde kayıtlı. Tekrar seçim yapmana gerek yok — kaldığın yerden tek adımda devam edebilirsin.<br><br>Aklına takılan bir şey olursa bu e-postayı yanıtlaman yeterli. | 32 words | ≤ 500 words |
| CTA | Sepete dön | 10 | ≤ 20 |

### Fallback (short)

| Field | Content | Chars | Limit |
|---|---|---:|---|
| Subject | Sepetindeki ürünler seni bekliyor | 33 | 20–50 |
| Preheader | Seçtiğin ürünler sepetinde duruyor. Dilediğin zaman devam edebilirsin. | 70 | 40–90 |
| Body | Merhaba,<br><br>Sepetine eklediğin ürünler seni bekliyor. Dilediğin zaman alışverişine devam edebilirsin. | 11 words | ≤ 500 words |
| CTA | Sepete dön | 10 | ≤ 20 |

## Step 2 — push (`step-2`)

**Intent:** Checkout continuation: resume payment step, deeplink to checkout
**Deeplink:** checkout screen (never app home). No variables in titles (push rule 4).

### Variant A — "one step left"

| Field | Content | Chars | Limit |
|---|---|---:|---|
| Title | Ödemeye bir adım kaldı | 22 | ≤ 40 |
| Body | Sepetin hazır, ödeme adımında bekliyor. Kaldığın yerden bir dakikada tamamlayabilirsin. | 87 | ≤ 120 |
| CTA | Ödemeyi tamamla | 15 | ≤ 20 |

### Variant B — "saved details"

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

**Intent:** Short cart nudge, deeplink to cart
**Deeplink:** cart screen. Sent only if step 1 unopened and no `begin_checkout`; scheduled outside quiet hours (09:00–11:00 stagger).

### Variant A — "named product"

| Field | Content | Chars | Limit |
|---|---|---:|---|
| Title | Ayırdıkların sepetinde duruyor | 30 | ≤ 40 |
| Body | {{product_name}} sepetinde seni bekliyor. Göz atmak için dokun. | 63 | ≤ 120 |
| CTA | Sepete git | 10 | ≤ 20 |

### Variant B — "light question"

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

**Personalization variables used:** `{{first_name}}`, `{{product_name}}` (CRM-agnostic; mapping table in [crm-export-mapping.md](../../docs/crm-export-mapping.md)). Every variable has the no-var Fallback block above; `{{product_name}}` appears only in bodies/subjects, never in push titles.

**Reviewer checklist applied:** sen-form throughout · no banned words ("kaçırma", "SON ŞANS", all-caps, "tıkla" as bare CTA, "değerli müşterimiz") · zero exclamation marks · no emoji · urgency only via real data (the 7-day cart lifetime in step 1 Variant A is the actual purge policy) · one primary CTA per message · preheaders extend, not repeat, subjects · push titles and bodies each stand alone.

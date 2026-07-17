---
name: ecommerce
pairs_with: knowledge/industries/ecommerce.md
tone: warm, concrete, product-forward
formality: informal-you (TR: "sen"; EN: contractions ok)
urgency_allowed: true          # but only when factually true
regulated: false
emoji_policy: sparing — max 1 per subject/title, none in SMS
last_reviewed: 2026-07-16
---

# E-commerce Lexicon

Word choice for e-commerce CRM copy. The customer relationship is transactional and frequent; copy should feel like a helpful shop assistant, not a brand manifesto. Concrete nouns beat adjectives: name the product, show the price, state the benefit.

## Use / avoid

| Use | Avoid | Why |
|---|---|---|
| "sepetin", "ayırdıkların" / "your cart", "your picks" | "işleminiz", "siparişiniz tamamlanmadı" / "your transaction" | Possessive + casual beats bureaucratic |
| exact product names via `{{product_name}}` | "ürünler", "seçtikleriniz" (vague) | Specificity drives recall |
| "kargo bedava" / "free shipping" (if true) | "kaçırma!!", "SON ŞANS" in caps | Real value > manufactured panic |
| "stokta azaldı: {{stock_count}} adet" (if real data) | "tükenmek üzere" without data | Fake scarcity destroys trust and deliverability |
| "iade kolay: 30 gün" | "risk yok", "%100 memnuniyet garantisi" | Concrete policy > absolute claims |
| "sana özel" only with a real personalized item | "size özel fırsatlar dünyası" | Empty personalization reads as spam |

## Urgency rules

Urgency is allowed **only when literally true**: real stock counts, real sale end dates, real cart expiry. If the fact isn't available as data, the urgency line is cut — no exceptions. Never stack urgency devices (countdown + "last chance" + low stock in one message).

## Tone calibration by journey stage

| Journey type | Tone shift |
|---|---|
| Abandoned cart / browse | Helpful reminder; zero guilt ("hâlâ ilgileniyorsan" not "neden bıraktın?") |
| Post-purchase | Gratitude + utility (care tips, tracking) before any cross-sell |
| Winback | Honest and light ("bir süredir görüşemedik"); never passive-aggressive |
| Price drop / back in stock | Pure information, minimal decoration — the fact IS the message |

## TR / EN notes

- TR: "sen" throughout for D2C fashion/beauty/lifestyle; switch to "siz" only for luxury or 45+ audiences (ask via intake).
- TR: avoid direct translations like "kaçırmayın fırsatı" word orders; write native TR, not translated EN.
- EN: contractions on ("you're", "it's"); sentence-case subjects, never Title Case.
- Currency/date formats follow the audience locale, not the brand HQ.

## Banned outright (spam & trust killers)

"ÜCRETSİZ!!!" / "FREE!!!", "kazandınız" / "you've won" / "you're a winner", "tıklayın" / "click here" as a bare CTA, "fırsatlar kaçıyor" / "don't miss out", all-caps words, more than one exclamation mark per message, "değerli müşterimiz" / "valued customer" (says "we don't know you").

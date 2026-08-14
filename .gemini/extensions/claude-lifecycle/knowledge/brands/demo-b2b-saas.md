---
name: demo-b2b-saas
display_name: Kanbanly (demo)
industry: saas
languages: [tr]
markets: [TR]
default_goal: retention
product_rhythm: daily — takım liderleri panoyu iş günü boyunca birden çok kez kontrol ediyor
tone: sakin, net, yardımcı
formality: siz
channels_live: [email, in_app]
incentive_policy:
  max_discount_pct: 0
  clv_threshold: null
  value_adds: [öncelikli destek, ücretsiz onboarding oturumu, bir aylık ek koltuk]
extra_banned_words: ["kaçırmayın", "fırsat"]
brand_vocabulary: ["Kanbanly", "pano", "otomasyon akışı", "rapor dışa aktarma"]
existing_automations: []
---

# Kanbanly (demo) — Company Config

Demo brand for the B2B SaaS test dataset (40 accounts). Proje yönetimi aracı; kitle iş yerinde okuyan takım liderleri ve yöneticiler.

## Inheritance chain (how this file is used)

```
1. Company   this file — tone/formality override, extra bans, incentive policy
2. Sector    knowledge/industries/saas.md + knowledge/lexicons/saas.md
3. Global    CLAUDE.md + knowledge/channels/ + knowledge/compliance/ + knowledge/lexicons/locales/tr.md
```

- `max_discount_pct: 0` → **hiçbir journey'de indirim yok**; teşvik gerektiğinde value-add listesinden seçilir.
- `channels_live` yalnızca email + in_app → SMS/push/WhatsApp adımı üretilemez.
- Compliance yalnızca sıkılaşabilir: SaaS lexicon'unun "urgency yalnızca gerçek tarihlerde" kuralı aynen geçerli.

## Notes

Rakip adı anılmaz. "Verimlilik devrimi" tarzı büyük laflar marka sesine aykırı; Kanbanly somut sayıyla konuşur ("47 rapor", "12 otomasyon akışı"). UI dilinde "pano" kullanılır, "board" değil.

## Results memory

- `output/demo-b2b-saas/results-log.md`
- `output/demo-b2b-saas/failed-strategies.md`
- `output/demo-b2b-saas/winning-strategies.md`
- `output/demo-b2b-saas/audit-history.md`

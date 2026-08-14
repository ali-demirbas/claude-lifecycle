---
name: tr
display_name: Türkçe
default_formality: sen (D2C tüketici) / siz (finans, kurumsal, lüks, 45+ kitle)
last_reviewed: 2026-07-16
---

# Türkçe — Locale Overlay

Sektör lexicon'u ne söyleneceğine karar verir; bu dosya Türkçenin onu nasıl söylediğine. Türkçe copy natively yazılır — İngilizce kurgu Türkçe kelimelerle doldurulmaz.

## Voice & register

- "Sen" Türk D2C pazarlamasında varsayılandır ve samimi değil *normal* okunur; "siz" finans/sağlık/kurumsal ve lükste güven sinyalidir. Karışık kullanım (aynı mesajda sen+siz) her zaman hatadır.
- Kısa, yüklemi sonda net biten cümleler. İngilizceden devşirilmiş kurgu ("Hazır mısın keşfetmeye?") yerine doğal Türkçe sözdizimi.
- Emir kipi CTA'larda doğaldır ve kaba okunmaz: "Sepeti tamamla", "Planını gör". İngilizcedeki "please" yumuşatması Türkçeye taşınmaz — "lütfen" CTA'da zayıflık okur.

## Emotion calibration

- **Güven verici:** somut politika + sahiplenme diliyle kurulur ("30 gün iade, soru sorulmaz") — sıfat yığınıyla değil ("güvenilir, kaliteli hizmet" boş okur).
- **Sıcak:** küçültme/samimiyet ekleriyle değil, kullanıcının kendi verisiyle kurulur ("40 gündür süren serin" > "canım müşterimiz").
- **Acil (izinliyse):** Türkçede büyük harf + ünlem hızla spam okur; aciliyet veriyle taşınır ("son 3 adet"), tonlamayla değil.
- **Kutlayıcı:** abartı Türkçede hızlı devalüe olur; "Tebrikler, 10. siparişin" yeter — "MUHTEŞEMSİN!" yazmaz.

## Punctuation & typography

- Türkçe tırnak ve kesme kuralları; sayılarda binlik ayracı nokta, ondalık virgül (1.250,50 ₺); ₺ sembolü tutardan sonra boşluklu veya "TL" — marka tercihi, tutarlı olsun.
- Tarih GG.AA.YYYY veya "12 Temmuz"; saat 24 formatı.
- Başlıklar cümle düzeni (sentence case); Her Kelimesi Büyük başlık İngilizce alışkanlığıdır, kullanılmaz.
- İ/ı ayrımı hayatidir: büyük harfe çevirirken "i" → "İ" (INDIRIM değil İNDİRİM). Otomatik uppercase'e güvenme.

## Market red lines

- Karşılaştırmalı reklamda rakip adı anmak TR'de hukuken dar alandır — rakip adı geçen iddialar legal-review bayrağı alır.
- Fiyat/indirim iddiaları: "en ucuz", "piyasanın en iyisi" gibi doğrulanamayan üstünlük iddiaları Reklam Kurulu riskidir; veriye bağlanamıyorsa yazılmaz.
- Finansal ürünlerde getiri iması ve "garanti" kelimesi sektör lexicon'undan bağımsız yasak (SPK/BDDK hassasiyeti).
- Sağlık/tedavi etkisi iması (kozmetik dahil: "iyileştirir", "tedavi eder") yasak; "destekler/yardımcı olur" sınırında bile dikkat.

## Character set

ç, ğ, ı, İ, ö, ş, ü her kanalda varsayılan olarak korunur. SMS'te GSM-7 maliyet optimizasyonu için diakritik atma (ş→s) bilinçli ve kullanıcı onaylı bir karardır; e-posta/push/in-app'te hiçbir koşulda yapılmaz.

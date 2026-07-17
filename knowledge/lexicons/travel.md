---
name: travel
pairs_with: knowledge/industries/travel.md
tone: destination-evocative in imagery, strictly factual on prices, dates, and availability
formality: informal-you for OTA/leisure (TR: "sen"); "siz" for airlines, business travel, and premium hotel brands — resolve at intake
urgency_allowed: true          # only when backed by live fare/availability data; fabricated scarcity is banned
regulated: false
emoji_policy: sparing — max 1 in subject/push title (✈️-style topical only); none in booking, payment, or disruption messages
last_reviewed: 2026-07-16
---

# Travel Lexicon

Word choice for OTA/airline/hotel CRM copy. Travel copy gets to dream a little — a destination line may evoke ("Ege'de eylül sakinliği") — but every number must be brutally factual: prices, dates, seat counts, and availability come from live data or they don't appear. The sector's credibility problem is manufactured scarcity ("2 seats left!" on every fare, forever); a brand that only says "son 2 koltuk" when it is literally true owns a message competitors have burned. Quote itineraries back precisely ({{origin}}→{{destination}}, {{dates}}): specificity is respect for a high-stakes purchase.

## Use / avoid

| Use | Avoid | Why |
|---|---|---|
| "İstanbul→Barselona, 12–19 Ağustos araman hâlâ geçerli" / "your Istanbul→Barcelona search, 12–19 Aug, is still live" | "hayalindeki tatil seni bekliyor" / "your dream vacation awaits" | Quote the actual search; generic wanderlust is noise |
| "aradığın rota şu an ₺4.230'dan başlıyor" / "fares on your route now start at $189" (live data) | "inanılmaz fiyatlar!", "fiyatlar uçuyor" / "unbelievable prices!" | The number is the message; adjectives dilute it |
| "bu tarihte son 3 oda kaldı" (real inventory) / "3 rooms left for your dates" | "tükenmek üzere!" with no data / "selling fast!" | Real counts convert AND preserve trust; fake scarcity destroys both |
| "fiyat düştü: takip ettiğin uçuş şimdi ₺3.980" / "price drop: the flight you're watching is now €142" | "fırsatı kaçırma, hemen al" / "grab it before it's gone" | A fare drop needs no decoration — data IS the urgency |
| "yolculuğuna 5 gün kaldı — online check-in açıldı" / "5 days to your trip — check-in is open" | "unutmayın!", "önemli hatırlatma!!" | Countdown-to-departure framing is naturally engaging; alarm tone is for disruptions only |
| "Eylülde Ege: az kalabalık, hâlâ deniz" / "September on the Aegean: fewer crowds, warm sea" | "cennet gibi", "büyüleyici deneyim" / "paradise awaits", "magical experience" | Evocative = concrete sensory facts; brochure superlatives are wallpaper |
| "iptal koşulları: 48 saate kadar ücretsiz" / "free cancellation until 48h before" | "içiniz rahat olsun" / "book with total peace of mind" | The policy is the reassurance; state it |

## Urgency rules

Urgency is permitted **only on real fare/availability data**: an actual fare change on a searched route, actual remaining inventory for the user's dates, an actual sale end datetime. The data source must exist as a variable ({{current_fare}}, {{seats_left}}, {{sale_end}}); if the integration can't supply it, the urgency line is cut — no exceptions. Never stack devices (price + scarcity + countdown in one message: pick the strongest single fact). Never use urgency in disruption/change communications — those are service messages where calm is the brand. Post-booking, urgency language is banned entirely except for genuine deadlines (check-in closing, payment due on hold bookings).

## Tone calibration by journey stage

| Journey type | Tone shift |
|---|---|
| Search abandonment | Helpful research assistant: replay their search, add one useful fact (fare level, flexibility tip); zero pressure — they may book in 3 weeks and that's fine |
| Booking abandonment | Concrete and prompt: exact itinerary + current price + one-tap resume; honest note if fares are volatile |
| Price drop / fare alert | Pure signal: route, dates, old→new price, book link. The least decorated message in the portfolio |
| Pre-trip (post-purchase) | Warm concierge: anticipation + logistics; ancillary offers framed as trip improvements, not add-on sales |
| In-trip | Service-only, minimal, instantly useful (directions, support, check-out time); marketing silence |
| Post-trip / review ask | Grateful, brief, memory-forward ("Barselona nasıldı?"); one ask per message |
| Winback / re-inspiration | Seasonal + personal ("geçen eylül Ege'deydin — bu yıl nereye?"); inspiration allowed here more than anywhere |

## TR / EN notes

- TR: "sen" for leisure OTA audiences; "siz" for airlines, corporate travel, and upscale hotel brands — the price point sets the register.
- TR: destination names in Turkish exonyms where natural (Barselona, Atina); airport codes only for frequent-flyer segments.
- TR: currency always ₺ with thousands separator (₺4.230); date format "12–19 Ağustos" — never ISO dates in customer copy.
- EN: aviation jargon (layover, red-eye, carrier) is fine for flight products; hotel copy stays plainer. No "wanderlust"/"getaway" filler.
- Both: always name route/city/hotel — a travel message without a place name in the first line has failed.
- Both: disruption and change messages follow transactional rules: no promo content, no emoji, formal register.

## Banned outright

Fake scarcity in any form ("son koltuklar!", "selling fast!" without live data), "hayallerinizdeki tatil" / "dream vacation" as a hook, "kaçırılmayacak fırsat" / "once-in-a-lifetime deal", price claims without a data variable behind them, "%70'e varan indirim" framing when the median discount is far lower, countdown timers not tied to a real sale end, all-caps destination names, more than one exclamation mark per message, urgency of any kind in disruption/cancellation communications.

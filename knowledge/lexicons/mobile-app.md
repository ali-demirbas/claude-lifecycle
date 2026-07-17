---
name: mobile-app
pairs_with: knowledge/industries/mobile-app.md
tone: short, playful, energetic — a friend nudging, never a brand broadcasting
formality: informal throughout (TR: "sen"; EN: casual, contractions, fragments ok)
urgency_allowed: true          # only for real expiring things (streaks, timed events, limited content with actual end dates)
regulated: false
emoji_policy: welcome in push/in-app but max 1 per message (per push channel rules); none in transactional/billing copy
last_reviewed: 2026-07-16
---

# Mobile App Lexicon

Word choice for consumer app and game notifications. The reading context is a lock screen glanced at for under two seconds — every word must earn its place, and the message must reference something *real and personal* (their streak, their level, their unfinished thing) or it reads as spam and costs push permission. Personalization off actual behavior is the whole game: "your 12-day streak" beats any adjective. Playful is good; needy is fatal.

## Use / avoid

| Use | Avoid | Why |
|---|---|---|
| "12 günlük serin devam ediyor 🔥" / "your 12-day streak is alive 🔥" | "Seni özledik!" / "We miss you!" | Real user data > brand neediness; guilt doesn't reopen apps |
| "Kaldığın yerden: 3. bölüm seni bekliyor" / "Pick up where you left off — level 3 awaits" | "Uygulamamıza geri dön" / "Come back to our app" | Their progress is the hook, not your app |
| "{{friend_name}} skorunu geçti" / "{{friend_name}} just beat your score" | "Yeni bir bildirim var" / "You have a new notification" | Social + specific triggers action; vague meta-messages are noise |
| "2 dakikan var mı? Bugünkü bulmaca hazır" / "Got 2 minutes? Today's puzzle is ready" | "Harika içerikler seni bekliyor!" / "Amazing content awaits!" | Small concrete ask > empty superlatives |
| "Etkinlik pazar gece yarısı bitiyor" / "Event ends Sunday midnight" | "SON SAATLER!!! Kaçırma!!!" / "FINAL HOURS!!! Don't miss out!!!" | A real deadline stated once > shouting |
| "Yeni rozet: Hafta Savaşçısı — nasıl kazanılır?" / "New badge: Week Warrior — see how to earn it" | "Yenilikleri keşfet" / "Check out what's new" | Named reward + curiosity > generic explore prompt |
| "Serin bozulmak üzere — bugün 1 tur yeter" / "Your streak's about to break — one round today saves it" | "Neden bizi bıraktın?" / "Why did you leave us?" | Loss-framing on *their* asset works; guilt-tripping earns an uninstall |

## Urgency rules

Urgency must be anchored to a real, system-known expiry: a streak that breaks at midnight, a timed event with an end date, rotating content that actually rotates. State the deadline once, plainly, and let the loss speak for itself — no countdown spam, no "LAST CHANCE" caps, no urgency on evergreen content ever. A message may carry at most one urgency device. Fake scarcity in an app users open daily is discovered within a week and paid for in disabled notifications.

## Tone calibration by journey stage

| Journey type | Tone shift |
|---|---|
| Welcome / onboarding | Warm, zero-pressure, one tiny step at a time ("ilk adım 30 saniye sürer") |
| Activation (stalled tutorial) | Encouraging, effort-minimizing ("kaldığın yerden 1 dakikada bitir"); never point out that they quit |
| Churn prevention (fading) | Light, content-led — lead with what's new or unfinished, never with their absence |
| Reactivation / winback | Fresh-start energy: what changed, what's new since they left; no guilt, no "we noticed you've been away" |
| Milestone / streak | Celebrate loudly, this is the one place hype is allowed ("Rekor kırdın!") |
| Monetization (IAP/offer) | Matter-of-fact and tied to their moment ("bu seviyede işine yarar"); never desperate discounting |

## TR / EN notes

- TR: "sen" always — "siz" in a game push reads like a bank letter. Native, spoken-register TR; write how players actually talk ("hadi", "bir tur", "kaldığın yerden"), not translated marketing EN.
- TR: suffix personalization correctly ({{first_name}} + vocative works; avoid awkward possessive constructions with foreign names).
- EN: fragments welcome ("New puzzle. 2 minutes. Go."), sentence case, no Title Case Push Titles.
- Emoji: max 1, placed at the end of title or body, never as a substitute for a word; skip entirely in billing, account, or parental-context messages.
- Numerals over words in both languages ("3 gün", "level 7") — scannable at lock-screen speed.

## Banned outright

"Seni özledik" / "We miss you" as an opener, "Neredesin?", "geri dön" as a bare CTA, "Amazing/incredible content awaits", all-caps words, multiple exclamation marks, more than one emoji, "don't miss out", fake social proof ("everyone's playing!") without data, guilt framing of any kind ("bizi unuttun mu?"), "you have a new notification" (a notification announcing a notification), streak/expiry claims not backed by real system state.

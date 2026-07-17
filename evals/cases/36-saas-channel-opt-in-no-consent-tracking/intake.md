goal: engagement — kullanıcıların push kanalını da açmasını istiyoruz
sector: saas
company: Panovar (kurgusal — B2C rapor/analiz aracı)
channels: email (açık), push (kullanıcıların çoğunda kapalı)
existing_automations: []
tone: samimi ama net · formality: sen
incentive_policy: indirim yok
languages: [tr] · markets: [TR]

Not: Kanal bazlı consent durumu CRM'de statik bir alan olarak duruyor (email: açık, push: kapalı), ancak consent DEĞİŞİKLİKLERİ hiçbir yerde event olarak kaydedilmiyor — `consent_updated` benzeri bir event yok, bir kullanıcı push iznini açsa bile bunu ne ölçebiliyoruz ne de kanıtlayabiliyoruz. Ekip yine de "push izni kazanma" journey'si istiyor.

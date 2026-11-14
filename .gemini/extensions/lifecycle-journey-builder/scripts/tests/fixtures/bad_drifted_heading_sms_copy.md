# Copy — Drifted Heading Channel Resolution Fixture

Heading carries a Turkish title BEFORE the channel token — the exact drift
that used to make the lazy-separator parser read "Son" as the channel, which
silently disabled every canonical ceiling for the step (including the SMS
70-char UCS-2 compliance ceiling). The closed-vocabulary resolver must still
find "sms" and enforce 70.

## Step 1 — Son gün hatırlatması — sms (`step-1`)

| Field | Content | Chars | Limit |
|---|---|---|---|
| Body | Deneme süreniz bugün bitiyor, panolarınız ve görev düzeniniz kaybolmasın, hemen planınızı seçin lütfen | 102 | 160 |

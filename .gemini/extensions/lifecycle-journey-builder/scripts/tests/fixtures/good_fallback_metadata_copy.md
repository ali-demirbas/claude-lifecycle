# Copy — Fallback Followed By Metadata Fields Fixture

The template places `**Personalization variables used:**` (and per-step
reviewer notes) directly after the Fallback section with no heading between.
Those metadata lines legitimately mention `{{vars}}`; they are step
bookkeeping, not sendable fallback content. A heading-only bound used to
swallow them into the fallback body and false-positive the variable check —
this fixture must PASS.

## Step 1 — email (`step-1`)

### Variant A (utility)

```json
{"strategy": "direct-utility", "hypothesis": "Kurulum odaklı net mesaj ilk pano oluşturmayı artırır"}
```

| Field | Content | Chars | Limit |
|---|---|---|---|
| Subject | Panonuzu kurmak icin tek adim kaldi | 35 | 50 |
| CTA | Panonu kur | 10 | 20 |

### Fallback (short)

Hesabınız hazır, ilk panonuzu kurarak başlayabilirsiniz.

**Personalization variables used:** `{{first_name}}` (fallback: "ekibiniz")
**Reviewer notes (v1→v2):** draft claim cut; only {{seats_purchased}} is traceable per intake.

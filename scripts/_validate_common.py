#!/usr/bin/env python3
"""Shared helpers for validate_input.py, validate_output.py, and eval_check.py."""
import re

failures = []
warnings = []


def fail(msg):
    failures.append(msg)
    print(f"FAIL: {msg}")


def warn(msg):
    warnings.append(msg)
    print(f"  warn: {msg}")


def tr_fold(s):
    """Casefold that avoids Python str.lower()'s Unicode full-casefold
    expansion of Turkish 'İ' (U+0130) into 'i' + U+0307 COMBINING DOT ABOVE —
    that expansion breaks plain-ASCII token/string matching anywhere Turkish
    text with a capital dotted İ is compared (e.g. a header like 'TARİH' or
    a value like 'İptal' would otherwise never match its lowercase-ASCII
    counterpart)."""
    return s.replace("İ", "i").lower()


# Each entry is the ASCII-stripped form of a common Turkish word that has no
# plausible English collision (unlike e.g. "gun" -> "gün", which IS an English
# word and is deliberately excluded) — a whole-word hit is a strong signal that
# Turkish diacritics were accidentally dropped during generation, not that the
# text is legitimately English. This targets customer/canvas-facing text only
# (a journey JSON's flow.title/tag/rows[].html); the flat steps[].intent /
# objective / kpis fields are internal design language this repo's own
# production data already writes in English (see
# examples/ecommerce-full-ga4/05-journey-cart-recovery.json and
# output/anadolu-benchmark/ecom-welcome-onboarding-01.json), so checking those
# would false-positive — this list is deliberately not applied there.
TR_DIACRITIC_STRIPPED_WORDS = {
    "icin", "degil", "gunluk", "gunde", "goruntule", "goruntuleme", "gormek",
    "kullanici", "kullanicilar", "kullanicilara", "urun", "urunu", "urunler",
    "basari", "basarili", "basarisiz", "gercek", "gerceklesme", "gerceklesti",
    "musteri", "musteriler", "hicbir", "aninda", "yardimci", "cikis",
    "kontrolu", "sikayet", "sikayeti", "olayi", "kosul", "kosulu",
    "hatirlatma", "adim", "ayni",
}
# NOT re.IGNORECASE: Python's Unicode case-fold graph unions Turkish dotless
# 'ı' with ASCII 'I'/'i' (verified: 'ı'.upper() == 'I', 'I'.lower() == 'i'), so
# a re.IGNORECASE match of e.g. "adim" against "adım" — a CORRECTLY-accented
# word — returns True, exactly inverting this check's purpose. Matching is
# done case-sensitively against text already folded through tr_fold(), which
# is ASCII/İ-safe without touching 'ı' (confirmed: plain str.lower() leaves
# 'ı' as 'ı', only re.IGNORECASE's case-fold graph merges it with 'i').
_TR_STRIPPED_RE = re.compile(
    r"\b(" + "|".join(sorted(TR_DIACRITIC_STRIPPED_WORDS, key=len, reverse=True)) + r")\b"
)


def tr_diacritic_stripped_hits(text):
    """Whole-word hits of TR_DIACRITIC_STRIPPED_WORDS in `text` — flags Turkish
    text whose diacritics were accidentally dropped (ç/ğ/ı/ö/ş/ü -> ASCII).
    Returns the matched substrings (may repeat); empty list if none found."""
    return _TR_STRIPPED_RE.findall(tr_fold(text or ""))

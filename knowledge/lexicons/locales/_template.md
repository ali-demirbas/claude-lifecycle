---
name: <lang-code>          # ISO 639-1, e.g. tr, en, de
display_name: <Language>
default_formality: <language-appropriate default>
---

# <Language> — Locale Overlay

Language-level voice rules, layered **on top of** the sector lexicon at write time. The sector lexicon decides *what* to say (vocabulary, urgency policy, banned claims); this file decides *how that language says it*. Never a translation guide — copy is written natively per language.

## Voice & register

Default formality and when to deviate; sentence-length norms for this language; how directness reads (blunt vs rude vs trustworthy).

## Emotion calibration

How tone targets from the journey's step table land in this language — the same "reassuring" brief needs different surface forms per language (what reads warm in one language reads distant or over-familiar in another). 3–6 concrete calibration notes.

## Punctuation & typography

Language-specific marks, quotation style, number/currency/date formats, capitalization rules for headings/subjects.

## Market red lines

Legal/cultural no-gos for the markets where this language dominates — claims, comparisons, or framings that are acceptable elsewhere but risky here. `copy-reviewer` checks these in addition to the sector lexicon's bans.

## Character set

All diacritics of this language are preserved in every channel by default. Any ASCII-folding (e.g. SMS cost optimization) is a deliberate, user-approved decision — see the SMS channel file.

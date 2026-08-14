---
name: <brand-slug>
display_name: <Brand Name>
industry: <sector-slug>            # primary — must match a file in knowledge/industries/; drives tone/compliance/brand_vocabulary always, and drives DQS/funnel/pattern-priorities too when verticals (below) is empty
verticals: []                      # optional — leave empty unless the company runs genuinely distinct product lines with their own funnels and conversion events (single-industry companies are the common case). Each entry:
#   - name: <slug>                 #     short identifier, e.g. "vertical-a"
#     industry: <sector-slug>      #     must match a file in knowledge/industries/
#     event_prefix: [<prefix>]     #     events starting with any of these belong to this vertical
languages: [tr]                    # copy languages; first is default
markets: [TR]                      # legal markets → compliance regimes
default_goal: <growth | retention | revenue | reactivation | null>  # pre-fills lifecycle-intake's goal question; ALWAYS re-surfaced for confirmation, never silently assumed — a brand's active priority can shift between engagements even though everything else here is stable. null = not yet asked.
product_rhythm: <daily | weekly | occasional-seasonal — actual cadence, e.g. "~40 days between orders", or null if unknown>  # gates lapse windows, dormancy thresholds, and winback/reactivation clocks when not computable from connected data (lifecycle-intake's "Product rhythm" question)
tone: <2–3 adjectives>
formality: <sen | siz | per-language override in notes>
channels_live: [email, push]       # only channels with real consented audiences
incentive_policy:
  max_discount_pct: 10
  clv_threshold: null              # above this LTV → value-add instead of discount; null = unknown, ask
  value_adds: []                   # e.g. [priority support, early access]
extra_banned_words: []             # brand-specific additions to lexicon/channel bans
brand_vocabulary: []               # words/phrases the brand insists on (product names, feature names)
existing_automations: []           # what already runs — the engine won't regenerate these
---

# <Brand Name> — Company Config

The **company layer** of the rule inheritance chain. One file per client/brand; created or updated by `lifecycle-intake` so answers persist across sessions instead of being re-asked.

## Inheritance chain (how this file is used)

Before generating anything, skills merge three layers, most specific wins — **except compliance, where the strictest layer wins**:

```
1. Company   knowledge/brands/<brand>.md          (this file)
2. Sector    knowledge/industries/<industry>.md + knowledge/lexicons/<industry>.md
3. Global    CLAUDE.md + knowledge/channels/ + knowledge/compliance/ + locale overlays
```

- Tone/formality here override the lexicon's defaults.
- `extra_banned_words` are **added to** (never replace) the lexicon and channel ban lists.
- `incentive_policy` here overrides intake defaults; a journey may never exceed `max_discount_pct`.
- Frequency caps, quiet hours, and consent rules can only get **stricter** at this layer, never looser.

## Verticals (multi-product-line companies)

Most companies belong to one industry and never fill in `verticals` — the field stays empty and every downstream skill behaves exactly as if it didn't exist. Fill it in only when the company runs genuinely separate product lines, each with its own funnel and its own conversion event (not just several features under one funnel).

When `verticals` is non-empty:
- `industry` (primary) still drives tone, compliance baseline, and brand vocabulary for the whole company — those don't fork per vertical.
- `lifecycle-connect` scores **funnel completeness and volume separately per vertical**, against that vertical's own industry file — a blended funnel across unrelated product lines isn't a real funnel. Event diversity and user attributes stay company-wide (shared identity, overall behavioral richness benefit every vertical equally).
- `lifecycle-map` tags each event to a vertical via `event_prefix` match before stage classification. An event matching no prefix falls back to the primary industry, flagged `unclassified-vertical`.
- `lifecycle-journeys` evaluates pattern eligibility and depth per vertical, using that vertical's own DQS and pattern priorities — a portfolio spans verticals, it doesn't average them into one blended number.
- **Known scope boundary:** `tone`, `formality`, `incentive_policy`, and `channels_live` stay company-wide even across verticals — a company whose product lines genuinely need different tone or discount policy per vertical isn't representable today. This is a deliberate simplification for the common case, not an oversight; if it's ever needed, the extension point is an optional per-vertical override block under each `verticals[]` entry (mirroring `event_prefix`), not a parallel brand-config file per vertical.

## Notes

Free-form context that doesn't fit frontmatter: brand character, taboo topics, competitor names never to mention, seasonal no-go windows. Keep it short — this file is loaded into every copy/journey run.

## Results memory

Links to this brand's results log and strategy history (written by `lifecycle-results`), plus its audit trail (written by `lifecycle-audit`):
- `output/<brand>/results-log.md`
- `output/<brand>/failed-strategies.md`
- `output/<brand>/winning-strategies.md`
- `output/<brand>/audit-history.md`

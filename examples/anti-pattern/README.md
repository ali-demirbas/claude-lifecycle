# Example — What a bad output looks like

The other three examples in this folder ([saas-csv-only](../saas-csv-only/), [fintech-industry-only](../fintech-industry-only/), [ecommerce-full-ga4](../ecommerce-full-ga4/)) show the engine working correctly. This one shows the opposite on purpose: a fictional run ("BrewTrack") that hits eight real failure modes while still *looking* correct — right section headers, plausible numbers, nothing obviously broken on a skim.

That's the point of including it. A skill file can list rules all day; what actually calibrates a model fast is seeing a plausible-looking output and being told exactly which line is wrong and why — the same contrast-pair effect the "Common Pitfalls" sections in [lifecycle-connect](../../skills/lifecycle-connect/SKILL.md#common-pitfalls), [lifecycle-journeys](../../skills/lifecycle-journeys/SKILL.md#common-pitfalls), and [lifecycle-copy](../../skills/lifecycle-copy/SKILL.md#common-pitfalls) exist for, shown here as one worked example instead of eight separate abstract descriptions.

## Files

| File | What it shows |
|---|---|
| [bad-output.md](bad-output.md) | Three short excerpts (data assessment, portfolio, copy) with inline ❌ markers, followed by a table naming the exact rule or pitfall each one breaks and what the fix looks like |

**Nothing in `bad-output.md` should be copied as a template** — every excerpt in it is wrong by design. For a real output's shape and formatting, use the three examples linked above instead.

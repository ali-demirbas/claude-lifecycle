# Contributing

Contributions that make the engine smarter are welcome — new industries, new journey patterns, sharper channel rules, richer lexicons.

## What to contribute

| Contribution | How | Difficulty |
|---|---|---|
| New industry | Follow [docs/adding-an-industry.md](docs/adding-an-industry.md) — playbook + lexicon pair | Content-only |
| New journey pattern | Mirror `knowledge/journey-patterns/abandoned-cart.md` exactly; reference it from ≥ 1 playbook | Content-only |
| Channel rule improvements | Edit `knowledge/channels/<channel>.md` — cite the platform doc that motivates the change | Content-only |
| Lexicon depth | More use/avoid rows with real TR/EN examples and a *why* per row | Content-only |
| Skill improvements | Edit `skills/*/SKILL.md` — keep the never-do lists intact; behavior changes need an example transcript in the PR | Care required |
| Router disambiguation phrases | Hit a request the router misclassified or had to ask about? Add it to the right row (or as a new example) in `skills/lifecycle/SKILL.md`'s routing table — cite the request that was ambiguous | Content-only |

## Ground rules

1. **No fabricated statistics.** "Industry average open rate is 21.33%" does not get merged. Ranges and qualitative claims only, sourced if specific.
2. **Industry logic lives in data files.** PRs adding `if sector == X` style branching to skills will be asked to move it into a playbook/lexicon.
3. **English repo content**; lexicons carry TR/EN guidance and may include other languages.
4. **Frontmatter is API.** Keys are consumed by skills and `scripts/validate.sh`; never rename or drop keys without updating both.

## Before opening a PR

```bash
bash scripts/validate.sh          # repo consistency — must print ALL CHECKS PASSED
bash scripts/tests/run_tests.sh   # validation-layer regression tests — must print ALL TESTS PASSED
```

For new industries also run the Tier-3 dry test described in [docs/adding-an-industry.md](docs/adding-an-industry.md) and paste the resulting portfolio table into the PR description.

## PR checklist

- [ ] `scripts/validate.sh` passes locally
- [ ] New files follow their exemplar's frontmatter + section structure
- [ ] No fabricated statistics, no filler table rows
- [ ] Cross-references updated (playbook ↔ lexicon ↔ patterns)
- [ ] CHANGELOG.md entry added under Unreleased

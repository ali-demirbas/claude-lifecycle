# Directory submission package

Everything needed to submit Lifecycle Journey Builder to Anthropic's plugin directory, plus a pre-submission risk check and an assessment of installing the skills outside Claude Code.

Checked against the official docs on 2026-11-14: the `claude-plugins-official` README, the Claude Code plugin docs (plugins, plugins reference, marketplaces, publish) and the claude.com pages "Submit your plugin" and "Plugin pre-submission checklist". Fields marked **unconfirmed** could not be verified from those pages.

## How the directory reads a submission

- Submissions go through the developer portal at [claude.ai/directory/manage](https://claude.ai/directory/manage) (**Submit new → Plugin bundle**). Pull requests to `anthropics/claude-plugins-official` are not monitored, and its `marketplace.json` is being reduced to Anthropic's own plugins.
- A paid claude.ai plan is required (Pro, Max or Ultra from your own account; on Team and Enterprise, an Owner).
- The portal steps are: **Source** (repository, optional plugin path, optional branch or tag, then **Validate**), **Listing details**, **Data handling**, **Compliance** (contact email and four acknowledgements), **Review and submit**.
- **Listing details are read from `plugin.json` and the README**, not typed into a form. To change a listed field, edit the file, push, and validate again.
- The directory also reads `icon`, `documentationUrl`, `supportUrl`, `privacyPolicyUrl` and `termsOfServiceUrl` from `plugin.json` (only there, never in a marketplace entry). Claude Code ignores them at load time.
- Run `claude plugin validate . --strict` locally first; the portal applies extra rules the CLI does not check.

## Listing fields

| Field | Value | Source / status |
|---|---|---|
| Repository | `https://github.com/ali-demirbas/claude-lifecycle` (or `ali-demirbas/claude-lifecycle`) | confirmed |
| Plugin path | *(empty)*: `.claude-plugin/plugin.json` is at the repository root | confirmed |
| Branch or tag | `main` (or a release tag such as `v0.3.0` if each release should be reviewed deliberately) | choice |
| Plugin name (`name`) | `lifecycle-journey-builder` (renamed from `claude-lifecycle`, see [Plugin name](#plugin-name)) | `plugin.json` |
| Display name (`displayName`) | `Lifecycle Journey Builder` | `plugin.json` |
| Version | `0.4.0` | `plugin.json` |
| Author | `Ali Demirbaş` | `plugin.json` |
| License | MIT (`LICENSE` file and `license` field) | confirmed |
| Short description | `plugin.json` `description` (below) | confirmed |
| Long description | the README (below is a suggested opening) | confirmed |
| Category | Marketing *(suggested)* | **unconfirmed**: none of the checked pages lists a category field for plugin submissions or says where one is read from |
| Keywords | `plugin.json` `keywords` (below) | in manifest; whether the directory shows them is **unconfirmed** |
| Icon (`icon`) | not set; the repo has no logo file | to add before the first submission: a square PNG, 512 to 2048 px, under 2 MB, at `.claude-plugin/icon.png` (SVG and WebP are refused). The icon is taken only once, at the first save or submission, so choose it deliberately |
| Documentation URL | `https://ali-demirbas.github.io/claude-lifecycle/` | to add as `documentationUrl` |
| Support URL | `https://github.com/ali-demirbas/claude-lifecycle/issues` | to add as `supportUrl` |
| Privacy policy URL | `https://github.com/ali-demirbas/claude-lifecycle/blob/main/docs/directory-submission.md#privacy-statement` | to add as `privacyPolicyUrl` |
| Terms of service URL | none; MIT license applies | optional |
| Contact email | the submitter's own address | entered in the portal |

### Short description

> Data-adaptive lifecycle marketing engine for Claude Code. Connects GA4 or other data sources (or just an industry), scores data quality, and generates a prioritized portfolio of customer journeys with channel-ready CRM copy.

The listing follows the live version, so a later change ships with a new version.

### Long description (README opening)

> Journeys are a function of your data. Lifecycle Journey Builder scores what your analytics can actually support first (a 0 to 100 Data Quality Score from GA4, a CSV export, or just an industry), then generates a portfolio of customer journeys sized to that reality: onboarding and activation, retention, churn prevention and win-back. Journeys your data cannot support become a tracking plan instead of a template. Every step gets rule-checked, sector-aware copy for email, push, SMS, in-app and WhatsApp, reviewed against channel limits and banned words before you see it, and the result is delivered as an interactive journey canvas plus a channel copy canvas.

### Keywords

`lifecycle-marketing`, `crm`, `customer-journeys`, `ga4`, `marketing-automation`, `email-marketing`, `push-notifications`, `claude-code`, `claude-skills`

### Install command

- **After listing:** people add the plugin from the directory on claude.ai; Claude Code then loads it as `<name>@synced`.
- **Today (own marketplace):**

  ```
  /plugin marketplace add ali-demirbas/claude-lifecycle
  /plugin install lifecycle-journey-builder@lifecycle-journey-builder
  ```

### Screenshots and media

All under `docs/assets/` or `docs/`, served at `https://ali-demirbas.github.io/claude-lifecycle/`.

| File | What it shows |
|---|---|
| `docs/assets/demo.gif` | 58-second walkthrough: GA4 data in, Data Quality Score, journey portfolio, journey canvas, channel copy canvas (1280×800, 13 frames) |
| `docs/hero-screenshot.png` | the journey canvas, rendered from sample data |
| `docs/pipeline-diagram.svg` | the pipeline: Connect, Map, Intake, Journeys, Copy, Export |
| live demo | `demo/journey-canvas.html` and `demo/message-copy.html` |

Whether the portal accepts uploaded screenshots in addition to what the README shows is **unconfirmed**; the checked pages only say the listing is read from `plugin.json` and the README, and that bundled images belong in the README as Markdown images.

## Privacy statement

Lifecycle Journey Builder runs entirely inside the user's own Claude session and machine.

- **No data is sent anywhere by the plugin.** Its scripts and hooks make no network calls. It declares no MCP server and no remote endpoint.
- **It reads local files the user points it at**: analytics exports (CSV, JSON), the plugin's own knowledge and template files, and, when the user has connected their own analytics tools in Claude, the results those tools return in the session.
- **It writes only to the user's working folder**, by default `output/` (configurable through the `output_dir` setting): assessments, journey documents, the two HTML canvases and machine-readable JSON. Nothing is written inside the plugin's install folder.
- **It keeps no data of its own.** There is no account, telemetry, analytics or cache outside `output/`. Deleting that folder removes everything the plugin produced.
- **Hooks:** a start-of-session hook prints the plugin's rules; a post-write hook runs the local output validator on files the session just wrote. Both run locally with Python and read no credentials.
- The plugin is not intended for people under 18.

### Data handling answers for the portal

| Question | Answer |
|---|---|
| Reads or stores personal data? | It can read user-level analytics data the user supplies (for example user IDs in a CSV export). It processes them in the session and writes derived outputs to the user's own `output/` folder; it stores nothing elsewhere. |
| Sends data to services other than declared connectors? | No. |
| How long is data kept? | Only as long as the user keeps their `output/` folder. The plugin keeps nothing itself. |
| Intended for people under 18? | No. |

## Pre-submission risk check

Results against the pre-submission checklist, from the repository as of 2026-11-14, after the rename.

| Finding | Checklist result | Fix |
|---|---|---|
| `name` started with `claude-` | was **Blocks** (reserved prefix) | fixed: renamed to `lifecycle-journey-builder` |
| 802 tracked files in the plugin folder (limit 512); the `.gemini/` bundle alone is 307, `evals/` 129, `scripts/` 217 | Held for a reviewer | submit from a slimmer folder or tag, or move evals, tests and the Gemini bundle out of the plugin folder |
| Hooks run Python files (`hooks/session_orientation.py`, `hooks/validate_on_write.py`) | Held for a reviewer ("a program the validator can't read through") | accept the review, or move hook logic into plain shell scripts |
| A demo MP4 would be a non-image binary | Held for a reviewer | fixed: only `docs/assets/demo.gif` is in the repository; attach the MP4 to a GitHub release if wanted |
| `description`, `author`, `version` | set | none |
| README of 40+ words, `LICENSE` | present | none |
| `.DS_Store` files | present on disk but not tracked | keep them untracked |
| Files over 256 KiB that are not images | none tracked | none |
| Network calls, credentials, package launchers | none found in `scripts/` or `hooks/` | none |

## Plugin name

Names that start with `claude-`, `anthropic-`, `anthropics-` or `cc-plugin-` are reserved, and current CLIs refuse to load them, so the plugin was renamed from `claude-lifecycle` to `lifecycle-journey-builder` (display name "Lifecycle Journey Builder") in both manifests. The marketplace has the same name. The GitHub repository name is separate and stays.

- Skills are now namespaced `lifecycle-journey-builder:lifecycle`; docs, hooks, eval prompts and the install lines were updated with it.
- A `renames` map in `marketplace.json` would migrate old installs automatically, but CLI 2.1.117 rejects the key ("Unrecognized key") and would fail to read the whole marketplace, so it is left out. The README tells existing users to uninstall `claude-lifecycle` and install the new name.
- `claude plugin validate .` passes on 2.1.117 and 2.1.321; CI runs it as a blocking job.
- Once a plugin is published its `name` is fixed; this is the name to submit.

## Installing outside Claude Code

Every skill reaches its working files through `${CLAUDE_PLUGIN_ROOT}`: 42 references across the 11 skills, pointing at `scripts/` (23), `knowledge/` (10), `templates/` (8) and `docs/` (1). Claude Code sets that variable only for an installed plugin. The four agents and the two hooks are plugin components too.

### `npx skills add ali-demirbas/claude-lifecycle` (open skills CLI): does not work as-is

- **What happens:** the CLI discovers `skills/<name>/SKILL.md` (and skills declared in `.claude-plugin/plugin.json` or `marketplace.json`, which declare none here), then copies **only each skill folder** into the chosen agents' skill directories. Each of the 11 folders contains just `SKILL.md`.
- **Why it breaks:** `knowledge/`, `templates/`, `scripts/` and `docs/data-quality-score.md` are not copied, and `${CLAUDE_PLUGIN_ROOT}` is not set outside a plugin install. The first real step (`lifecycle-connect` running `scripts/validate_input.py`, then reading the DQS table) fails, and the template-only and validate-before-delivery rules cannot be followed. The skills would still load and route, which makes the failure look like a working install until the first run.
- **Also missing:** the copy-reviewer, copy-writer, journey-architect and event-analyst agents, and the hooks that inject the 12 rules and validate every written output.
- **What it would take:** a build step (like the existing `scripts/build_gemini.py`) that emits one self-contained skill folder, for example `dist/skills/lifecycle/` with the router `SKILL.md`, the sub-skills as reference files, and `knowledge/`, `templates/` and the non-test `scripts/` inside it (about 81 knowledge/template files and 24 scripts, roughly 2.5 MB before trimming), with every `${CLAUDE_PLUGIN_ROOT}/` rewritten to paths relative to the skill folder, the 12 rules inlined, and agent steps replaced by in-context passes. Then declare that folder in the manifest or a discovery path so the CLI installs it.

### AGENTS.md for other coding agents: partially

- **What works:** an agent that reads `AGENTS.md` and runs inside a clone of this repository can reach `knowledge/`, `templates/` and `scripts/` by relative path. A short `AGENTS.md` that says "`${CLAUDE_PLUGIN_ROOT}` means the repository root", lists the skills with their paths, and inlines the 12 rules would make the pipeline runnable, with Python 3.9+ and `pip install -r requirements.txt`.
- **What does not:** `AGENTS.md` is a single always-loaded instruction file, so there is no per-skill loading or slash-command routing; the subagent review passes run in-context or not at all; the post-write validation hook does not exist, so rule 12 depends on the agent remembering to run `scripts/validate_output.py`; and it only works from inside the clone, which mixes the user's `output/` with the plugin's source.
- **What it would take:** the same self-contained bundle as above, or an `AGENTS.md` written for clone mode with explicit validation steps. No `AGENTS.md` exists in the repository today.

### Gemini CLI: works through the existing bundle

`.gemini/extensions/lifecycle-journey-builder/` is already generated by `scripts/build_gemini.py`, which solves exactly these problems for that agent: it rewrites `${CLAUDE_PLUGIN_ROOT}` to the extension's install path, copies the referenced `knowledge/`, `templates/` and files, inlines the rules, and maps the agents' tool names. That script is the natural starting point for any further agent target.

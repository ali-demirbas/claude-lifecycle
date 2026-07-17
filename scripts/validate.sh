#!/usr/bin/env bash
# Repo consistency validation for claude-lifecycle.
# Checks skill/pattern/industry/lexicon frontmatter, cross-file references,
# JSON schema validity, example conformance, and internal markdown links.
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
FAIL=0

# Unique per-invocation, not a hardcoded shared path — two validate.sh runs
# in flight at once (two terminals, overlapping CI jobs) would otherwise race
# on the same /tmp filename, one run's subshell output silently clobbering
# the other's right before its own read-back. Cleaned up on exit either way.
TMP_CHECK="$(mktemp)"
trap 'rm -f "$TMP_CHECK"' EXIT

err() { echo "FAIL: $1"; FAIL=1; }
ok()  { echo "  ok: $1"; }

echo "== 1. Skills: frontmatter with name + description =="
for f in skills/*/SKILL.md; do
  head -1 "$f" | grep -q '^---$' || { err "$f: no frontmatter"; continue; }
  fm=$(awk '/^---$/{c++; next} c==1{print} c==2{exit}' "$f")
  echo "$fm" | grep -q '^name:' || err "$f: missing name"
  echo "$fm" | grep -q '^description:' || err "$f: missing description"
  dir=$(basename "$(dirname "$f")")
  nm=$(echo "$fm" | sed -n 's/^name:[[:space:]]*//p' | head -1)
  [ "$nm" = "$dir" ] || err "$f: name '$nm' != directory '$dir'"
done
ok "$(ls skills/*/SKILL.md | wc -l | tr -d ' ') skills checked"

echo "== 2. Journey patterns: required frontmatter keys =="
PATTERN_KEYS="name stage trigger_type required_events optional_events required_attributes optional_attributes default_channels base_steps depth_range applicable_industries"
for f in knowledge/journey-patterns/*.md; do
  fm=$(awk '/^---$/{c++; next} c==1{print} c==2{exit}' "$f")
  for k in $PATTERN_KEYS; do
    echo "$fm" | grep -q "^$k:" || err "$f: missing frontmatter key '$k'"
  done
  stage=$(echo "$fm" | sed -n 's/^stage:[[:space:]]*//p' | head -1)
  case "$stage" in
    acquisition|activation|engagement|revenue|retention|winback) ;;
    *) err "$f: invalid stage '$stage'" ;;
  esac
  tt=$(echo "$fm" | sed -n 's/^trigger_type:[[:space:]]*//p' | head -1)
  case "$tt" in
    event|time|segment|absence) ;;
    *) err "$f: invalid trigger_type '$tt'" ;;
  esac
done
ok "$(ls knowledge/journey-patterns/*.md | wc -l | tr -d ' ') patterns checked"

echo "== 3. Industries: keys, pattern refs, lexicon pairing =="
INDUSTRY_KEYS="name display_name funnel conversion_events activation_definition churn_signal pattern_priorities typical_channels"
for f in knowledge/industries/*.md; do
  base=$(basename "$f" .md)
  [ "$base" = "_template" ] && continue
  fm=$(awk '/^---$/{c++; next} c==1{print} c==2{exit}' "$f")
  for k in $INDUSTRY_KEYS; do
    echo "$fm" | grep -q "^$k:" || err "$f: missing frontmatter key '$k'"
  done
  # every pattern_priorities key must exist as a pattern file AND list this
  # industry in its applicable_industries — otherwise the priority is a dead
  # line the eligibility pass never evaluates
  # [a-z0-9_-]+, not [a-z-]+: a pattern key with a digit or underscore
  # (e.g. "trial_conversion", "care-alert-2") was silently dropped by the
  # narrower class, so its dead-priority-line check never ran at all.
  echo "$fm" | awk '/^pattern_priorities:/{flag=1; next} /^[a-z0-9_]+:/{flag=0} flag && /^[[:space:]]+[a-z0-9_-]+:/{print $1}' | tr -d ':' | while read -r p; do
    pf="knowledge/journey-patterns/$p.md"
    if [ ! -f "$pf" ]; then
      echo "FAIL: $f: pattern_priorities references missing pattern '$p'"
      continue
    fi
    grep "^applicable_industries:" "$pf" | cut -d: -f2 | tr -d '[] ' | tr ',' '\n' | grep -qx "$base" \
      || echo "FAIL: $f: '$p' is prioritized here but $pf applicable_industries lacks '$base' — dead priority line"
  done | tee "$TMP_CHECK"
  grep -q FAIL "$TMP_CHECK" && FAIL=1
  # paired lexicon must exist
  [ -f "knowledge/lexicons/$base.md" ] || err "$f: no paired lexicon knowledge/lexicons/$base.md"
done
ok "industries checked"

echo "== 4. Lexicons: keys and pairing =="
LEXICON_KEYS="name pairs_with tone formality urgency_allowed regulated emoji_policy"
for f in knowledge/lexicons/*.md; do
  base=$(basename "$f" .md)
  fm=$(awk '/^---$/{c++; next} c==1{print} c==2{exit}' "$f")
  for k in $LEXICON_KEYS; do
    echo "$fm" | grep -q "^$k:" || err "$f: missing frontmatter key '$k'"
  done
  [ -f "knowledge/industries/$base.md" ] || err "$f: no paired industry knowledge/industries/$base.md"
done
ok "lexicons checked"

echo "== 5. JSON: schema validity + example conformance =="
python3 - <<'PY' || FAIL=1
import json, sys, glob, re

with open('templates/journey.schema.json') as f:
    schema = json.load(f)
print("  ok: journey.schema.json parses")

try:
    import jsonschema
    validator = jsonschema.Draft202012Validator(schema)
    have_lib = True
except ImportError:
    have_lib = False
    print("  note: jsonschema lib not installed - falling back to structural checks")

failed = False
for path in glob.glob('examples/**/*.json', recursive=True):
    with open(path) as f:
        try:
            doc = json.load(f)
        except json.JSONDecodeError as e:
            print(f"FAIL: {path}: invalid JSON: {e}"); failed = True; continue
    if have_lib:
        errs = list(validator.iter_errors(doc))
        for e in errs[:5]:
            print(f"FAIL: {path}: {'/'.join(map(str, e.path))}: {e.message}")
        failed = failed or bool(errs)
    else:
        for k in schema['required']:
            if k not in doc:
                print(f"FAIL: {path}: missing required field '{k}'"); failed = True
        if 'id' in doc and not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*-[0-9]{2}$', doc['id']):
            print(f"FAIL: {path}: id '{doc['id']}' violates pattern"); failed = True
    if not failed:
        print(f"  ok: {path}")
sys.exit(1 if failed else 0)
PY

echo "== 6. Plugin manifest =="
python3 -c "import json; json.load(open('.claude-plugin/plugin.json'))" \
  && ok "plugin.json parses" || err "plugin.json invalid"

echo "== 7. Internal markdown links =="
python3 - <<'PY' || FAIL=1
import os, re, sys
failed = False
link_re = re.compile(r'\]\(([^)#]+\.(?:md|json))(?:#[^)]*)?\)')
for dirpath, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ('.git', 'node_modules', 'output')]
    for fn in files:
        if not fn.endswith('.md'):
            continue
        path = os.path.join(dirpath, fn)
        with open(path, encoding='utf-8') as f:
            text = f.read()
        for m in link_re.finditer(text):
            target = m.group(1)
            if target.startswith(('http://', 'https://', 'mailto:')):
                continue
            if '<' in target:  # template placeholder links like <pattern-name>.md
                continue
            resolved = os.path.normpath(os.path.join(dirpath, target))
            if not os.path.exists(resolved):
                print(f"FAIL: {path} -> {target} (broken)")
                failed = True
if failed:
    sys.exit(1)
print("  ok: internal links resolve")
PY

echo "== 8. Brands: frontmatter + cross-file references =="
BRAND_KEYS="name display_name industry languages markets default_goal product_rhythm tone formality channels_live incentive_policy extra_banned_words brand_vocabulary existing_automations"
for f in knowledge/brands/*.md; do
  base=$(basename "$f" .md)
  [ "$base" = "_template" ] && continue
  fm=$(awk '/^---$/{c++; next} c==1{print} c==2{exit}' "$f")
  for k in $BRAND_KEYS; do
    echo "$fm" | grep -q "^$k:" || err "$f: missing frontmatter key '$k'"
  done
  nm=$(echo "$fm" | sed -n 's/^name:[[:space:]]*//p' | head -1)
  [ "$nm" = "$base" ] || err "$f: name '$nm' != filename '$base'"
  ind=$(echo "$fm" | sed -n 's/^industry:[[:space:]]*//p' | head -1)
  [ -f "knowledge/industries/$ind.md" ] || err "$f: industry '$ind' has no knowledge/industries/$ind.md"
  # channels_live entries must each resolve to a real channel file; in_app aliases to
  # in-app.md (same alias validate_output.py's CHANNEL_ALIASES already applies).
  chans=$(echo "$fm" | sed -n 's/^channels_live:[[:space:]]*\[\(.*\)\]/\1/p' | tr ',' '\n' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
  for ch in $chans; do
    [ -z "$ch" ] && continue
    chfile="$ch"; [ "$ch" = "in_app" ] && chfile="in-app"
    [ -f "knowledge/channels/$chfile.md" ] || err "$f: channels_live entry '$ch' has no knowledge/channels/$chfile.md"
  done
  # each declared vertical's industry must also resolve (subshell-safe: tee + grep, same
  # workaround section 3's pattern_priorities check already needed for the same reason).
  echo "$fm" | awk '/^verticals:/{flag=1; next} /^[a-z_]+:/{flag=0} flag && /industry:[[:space:]]*[a-z-]+/{print}' | \
    sed -n 's/.*industry:[[:space:]]*\([a-z-]*\).*/\1/p' | while read -r vind; do
      [ -f "knowledge/industries/$vind.md" ] || echo "FAIL: $f: vertical industry '$vind' has no knowledge/industries/$vind.md"
    done | tee "$TMP_CHECK"
  grep -q FAIL "$TMP_CHECK" && FAIL=1
  # A leftover <placeholder> token anywhere in frontmatter means the template was copied
  # but never filled in — the exact failure mode that let '<2–3 adjectives>' ship as a
  # brand's real tone with nothing else in this validator catching it.
  echo "$fm" | grep -qE '<[a-zA-Z]' && err "$f: frontmatter still contains a <placeholder> token — template was not filled in"
done
ok "$(ls knowledge/brands/*.md | grep -v _template | wc -l | tr -d ' ') brand configs checked"

echo "== 9. Channels: frontmatter + parseable limits =="
CHANNEL_KEYS="name consent_required frequency_cap quiet_hours limits"
for f in knowledge/channels/*.md; do
  base=$(basename "$f" .md)
  [ "$base" = "_template" ] && continue
  fm=$(awk '/^---$/{c++; next} c==1{print} c==2{exit}' "$f")
  for k in $CHANNEL_KEYS; do
    echo "$fm" | grep -q "^$k:" || err "$f: missing frontmatter key '$k'"
  done
  nm=$(echo "$fm" | sed -n 's/^name:[[:space:]]*//p' | head -1)
  [ "$nm" = "$base" ] || err "$f: name '$nm' != filename '$base'"
  # limits: must actually declare at least one field with a real ceiling —
  # this is scripts/validate_output.py's load_channel_limits() source of
  # truth now, so an empty/malformed block silently zeroes out enforcement
  # for the whole channel instead of failing loudly here.
  echo "$fm" | awk '/^limits:/{flag=1; next} /^[a-z_]+:/{flag=0} flag && /max:[[:space:]]*[0-9]/{found=1} END{exit !found}' \
    || err "$f: 'limits:' block has no parseable 'max: N' entry"
done
ok "$(ls knowledge/channels/*.md | grep -v _template | wc -l | tr -d ' ') channel files checked"

echo "== 10. Journey patterns: mutually_exclusive_with reciprocity =="
# Optional field, not in PATTERN_KEYS (section 2) — only patterns whose audiences can
# genuinely collide declare it (the welcome-onboarding/account-onboarding bug was exactly
# a one-directional exclude: one file excluded the other's audience, the other didn't
# reciprocate). No associative arrays here — bash 3.2 (macOS system default) doesn't
# have them; a small function re-reading frontmatter on demand keeps this portable.
mutex_of() {
  local f="knowledge/journey-patterns/$1.md"
  [ -f "$f" ] || return
  awk '/^---$/{c++; next} c==1{print} c==2{exit}' "$f" \
    | sed -n 's/^mutually_exclusive_with:[[:space:]]*\[\(.*\)\][[:space:]]*$/\1/p' \
    | tr -d '[:space:]'
}
for f in knowledge/journey-patterns/*.md; do
  base=$(basename "$f" .md)
  mex="$(mutex_of "$base")"
  [ -z "$mex" ] && continue
  old_ifs="$IFS"
  IFS=','
  for p in $mex; do
    IFS="$old_ifs"
    [ -z "$p" ] && continue
    if [ ! -f "knowledge/journey-patterns/$p.md" ]; then
      err "$f: mutually_exclusive_with references unknown pattern '$p'"
      continue
    fi
    case ",$(mutex_of "$p")," in
      *",$base,"*) ;;
      *) err "$f: declares mutually_exclusive_with '$p', but $p.md does not reciprocate — asymmetric exclusion" ;;
    esac
    IFS=','
  done
  IFS="$old_ifs"
done
ok "mutually_exclusive_with reciprocity checked across $(ls knowledge/journey-patterns/*.md | wc -l | tr -d ' ') patterns"

echo "== 11. Lexicon locale overlays: frontmatter + required sections =="
# copy-writer/copy-reviewer both read these files for voice rules and the
# Market red lines legal check, but until now nothing verified a locale file
# actually has the sections locales/_template.md promises — a malformed or
# incomplete new-language file (e.g. missing 'Market red lines') would fail
# silently: copy-reviewer's check 11 would just find nothing to check against.
LOCALE_KEYS="name display_name default_formality"
LOCALE_HEADINGS="Voice & register|Emotion calibration|Punctuation & typography|Market red lines|Character set"
for f in knowledge/lexicons/locales/*.md; do
  base=$(basename "$f" .md)
  [ "$base" = "_template" ] && continue
  fm=$(awk '/^---$/{c++; next} c==1{print} c==2{exit}' "$f")
  for k in $LOCALE_KEYS; do
    echo "$fm" | grep -q "^$k:" || err "$f: missing frontmatter key '$k'"
  done
  nm=$(echo "$fm" | sed -n 's/^name:[[:space:]]*//p' | head -1)
  [ "$nm" = "$base" ] || err "$f: name '$nm' != filename '$base'"
  old_ifs="$IFS"
  IFS='|'
  for h in $LOCALE_HEADINGS; do
    IFS="$old_ifs"
    grep -qF "## $h" "$f" || err "$f: missing required section '## $h' (see locales/_template.md)"
    IFS='|'
  done
  IFS="$old_ifs"
done
ok "$(ls knowledge/lexicons/locales/*.md | grep -v _template | wc -l | tr -d ' ') locale files checked"

echo "== 12. Lexicon staleness: last_reviewed cadence =="
# Advisory only (WARN, never FAILs the build on a calendar fact alone) — a stale
# lexicon is worth a fresh pass, not a blocked pipeline. Cadence keys off the
# `regulated:` field every lexicon already carries: regulated sectors (fintech,
# insurance, edtech) ban vocabulary anchored in slow-moving legal wording; a
# non-regulated sector's spam/hype patterns drift faster with marketing fashion.
# Missing last_reviewed entirely IS a real FAIL — that's a structural regression
# in a field this repo now depends on, not a calendar question.
python3 - <<'PY' || FAIL=1
import glob, re, sys
from datetime import date

REGULATED_MONTHS, UNREGULATED_MONTHS = 12, 6
today = date.today()
hard_fail = False

for path in sorted(glob.glob("knowledge/lexicons/*.md")) + sorted(glob.glob("knowledge/lexicons/locales/*.md")):
    if path.endswith("_template.md"):
        continue
    text = open(path, encoding="utf-8").read()
    m = re.search(r"^last_reviewed:\s*(\d{4}-\d{2}-\d{2})", text, re.M)
    if not m:
        print(f"FAIL: {path}: missing last_reviewed frontmatter field")
        hard_fail = True
        continue
    reviewed = date.fromisoformat(m.group(1))
    months = (today.year - reviewed.year) * 12 + (today.month - reviewed.month)
    regulated = bool(re.search(r"^regulated:\s*true", text, re.M))
    threshold = REGULATED_MONTHS if regulated else UNREGULATED_MONTHS
    if months > threshold:
        print(f"WARN: {path}: last reviewed {months}mo ago (threshold {threshold}mo, "
              f"{'regulated' if regulated else 'unregulated'} sector) — spam/jargon patterns may have shifted")
    else:
        print(f"  ok: {path}: {months}mo since last_reviewed (threshold {threshold}mo)")

sys.exit(1 if hard_fail else 0)
PY
ok "lexicon staleness cadence checked"

echo "== 13. Channel vocabulary: knowledge files vs schema enum vs validator set =="
# knowledge/channels/*.md is the data layer (limits, tone rules); the channel
# VOCABULARY itself is still hardcoded in two more places for reasons that
# won't go away — templates/journey.schema.json's $defs/channel enum is a
# static, portable artifact meant to validate outside this repo/Python env
# (so it can't just "read the filesystem" at validation time), and
# scripts/validate_output.py's CHANNELS set predates load_channel_limits()'s
# live-parsing. Adding a channel today means touching data (one new .md) AND
# two literal lists — this section is the drift guard for the latter two,
# same class of fix as section 10's mutually_exclusive_with reciprocity check:
# it can't make the touchpoints disappear, but it stops one being forgotten.
python3 - <<'PY' || FAIL=1
import glob, json, os, re, sys

files = set()
for path in sorted(glob.glob("knowledge/channels/*.md")):
    base = os.path.splitext(os.path.basename(path))[0]
    if base == "_template":
        continue
    files.add("in_app" if base == "in-app" else base)

schema = json.load(open("templates/journey.schema.json", encoding="utf-8"))
schema_enum = set(schema["$defs"]["channel"]["enum"])

vo_text = open("scripts/validate_output.py", encoding="utf-8").read()
m = re.search(r'^CHANNELS = \{([^}]*)\}', vo_text, re.M)
vo_channels = set(re.findall(r'"([a-z_]+)"', m.group(1))) if m else set()

hard_fail = False
if files != schema_enum:
    print(f"FAIL: knowledge/channels/*.md {sorted(files)} != journey.schema.json's "
          f"$defs/channel enum {sorted(schema_enum)}")
    hard_fail = True
if files != vo_channels:
    print(f"FAIL: knowledge/channels/*.md {sorted(files)} != validate_output.py's "
          f"CHANNELS set {sorted(vo_channels)}")
    hard_fail = True
if not hard_fail:
    print(f"  ok: {len(files)} channels agree across knowledge files, schema enum, and validator set")

sys.exit(1 if hard_fail else 0)
PY

echo
if [ "$FAIL" = 1 ]; then
  echo "VALIDATION FAILED"; exit 1
else
  echo "ALL CHECKS PASSED"; exit 0
fi

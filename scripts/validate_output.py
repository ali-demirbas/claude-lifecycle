#!/usr/bin/env python3
"""Output validator for claude-lifecycle deliverables.

Checks generated artifacts against machine-enforceable business rules BEFORE
they reach the user. Compliance-class violations are hard failures (exit 1):
the engine must stop and report, never silently self-correct.

Usage:
  validate_output.py journey <file.json> [...]        journey JSON: schema + business rules
  validate_output.py copy <copy.md> [...] [--max-discount N] [--sector SLUG]
                                                      copy doc: recount chars, limits, em-dash,
                                                      discount ceiling, candidate banned/spam terms
                                                      (--sector enables the lexicon/spam-word check)
  validate_output.py portfolio <portfolio.json>       registry: unique ids + frequency-cap math
  validate_output.py consistency <journey.md> <journey.json>
                                                      cross-check id/depth_class/step-channels/
                                                      branch-presence/KPI-count+types agree
                                                      (never diffs intent text or wait-duration
                                                      equivalence — those stay a human read)
  validate_output.py all <output-dir> [--max-discount N]
                                                      also auto-pairs a journey-doc.md with its
                                                      journey JSON (by id) for the consistency check

Exit codes: 0 = pass (warnings allowed), 1 = violations found, 2 = usage error.
"""
import glob
import json
import os
import re
import sys

from _validate_common import fail, failures, tr_fold, warn, warnings

CHANNELS = {"email", "push", "sms", "in_app", "whatsapp"}
ISO_WAIT = re.compile(r"^P(?!$)(?:\d+W|(\d+D)?(T(?=\d)(\d+H)?(\d+M)?(\d+S)?)?)$")
ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*-[0-9]{2}$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
EMDASH = re.compile(r"[—–]")  # em dash, en dash
VARIANT_HEAD = re.compile(r"^### Variant\b.*$", re.M)
VARIANT_JSON_FENCE = re.compile(r"```json\s*\n(.*?)\n```", re.S)
REVIEW_STATUS_RE = re.compile(r"\*\*Review status:\*\*\s*(.+)$", re.M)
REVIEWER_NOTES_RE = re.compile(r"\*\*Reviewer notes:\*\*\s*(.*)$", re.M)
# push's optional rich-media line (templates/copy-output.md): not a chars-table
# row (a URL has no meaningful character ceiling), so it's parsed separately.
# Checks what's statically verifiable — well-formed HTTPS + non-empty alt text —
# never the actual downloaded file size, which needs a network fetch this
# offline validator deliberately doesn't do (see knowledge/channels/push.md's
# Rich media section for the ≤1MB ceiling to apply by hand).
IMAGE_LINE = re.compile(r"^\*\*Image:\*\*[ \t]*(\S+)[ \t]*·[ \t]*\*\*Alt text:\*\*[ \t]*(.*)$", re.M)
BANNED_HEADING = re.compile(r"^## Banned outright", re.M)
SPAM_HEADING = re.compile(r"^## Spam-trigger words", re.M)
QUOTED_TERM = re.compile(r'"([^"]+)"')
# "%40 indirim", "40% off", "%45.5 indirim" ... The negative lookbehind on the
# trailing-%% alternative stops "45.5%" from being mis-split (a bare \d{1,3}
# scan finds "5%" inside it and silently drops the "45." prefix).
DISCOUNT = re.compile(r"(?:%\s*(\d{1,3}(?:[.,]\d+)?)|(?<![\d.,])(\d{1,3}(?:[.,]\d+)?)\s*%)", re.U)
DISCOUNT_CTX = re.compile(r"indirim|discount|off\b|sale", re.I | re.U)

# Fallback only — used if the compliance file is missing or its table can't be
# parsed. The real source of truth is load_default_caps() below, which reads
# knowledge/compliance/consent-and-quiet-hours.md live. A hand-copied dict here
# with no live check is exactly the drift risk that already let WhatsApp's
# copy-limit ceilings go stale (see load_channel_limits' comment below) — this
# repo's own precedent for the fix is "parse the knowledge file, don't shadow it".
_FALLBACK_CAPS = {"email": 4, "push": 5, "sms": 2, "whatsapp": 2, "in_app": 99, "total": 8}
CAPS_HEADING = re.compile(r"^## Default frequency caps", re.M)
CAPS_ROW = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$", re.M)
CAPS_SCOPE_TO_CHANNEL = {
    "email marketing": "email", "push marketing": "push", "sms marketing": "sms",
    "whatsapp marketing": "whatsapp", "all channels combined": "total",
}

_default_caps_cache = None


def _parse_weekly_cap(cell):
    """A cap cell may carry more than one cadence, e.g. '1 / user / day, 5 / week'
    — check_portfolio works in weekly units only, so pull the figure paired with
    'week', not just the first number in the cell (which would silently grab the
    daily figure instead)."""
    for segment in cell.split(","):
        if "week" in segment:
            m = re.search(r"(\d+)", segment)
            if m:
                return int(m.group(1))
    return None


def load_default_caps():
    """{channel: weekly cap}, parsed live from consent-and-quiet-hours.md's
    'Default frequency caps' table so this script can never silently drift from
    the knowledge file it claims to enforce. in_app has no row in that table (an
    in-app message only shows while the user is already present, so it carries
    none of the annoyance-while-absent risk the cap exists to bound) — it keeps
    the fallback constant instead."""
    global _default_caps_cache
    if _default_caps_cache is not None:
        return _default_caps_cache
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "..", "knowledge", "compliance", "consent-and-quiet-hours.md")
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        warn(f"{path} not found — falling back to hardcoded default caps")
        _default_caps_cache = dict(_FALLBACK_CAPS)
        return _default_caps_cache
    m = CAPS_HEADING.search(text)
    if not m:
        warn(f"{path}: 'Default frequency caps' section not found — falling back to hardcoded default caps")
        _default_caps_cache = dict(_FALLBACK_CAPS)
        return _default_caps_cache
    rest = text[m.end():]
    nxt = re.search(r"^## ", rest, re.M)
    section = rest[: nxt.start()] if nxt else rest
    caps = {"in_app": _FALLBACK_CAPS["in_app"]}
    for row in CAPS_ROW.finditer(section):
        channel = CAPS_SCOPE_TO_CHANNEL.get(row.group(1).strip().lower())
        if not channel:
            continue  # header/separator row or a scope this parser doesn't map
        cap = _parse_weekly_cap(row.group(2))
        if cap is not None:
            caps[channel] = cap
    missing = set(_FALLBACK_CAPS) - set(caps)
    if missing:
        warn(f"{path}: table parse produced no value for {sorted(missing)} — using fallback for those")
        for k in missing:
            caps[k] = _FALLBACK_CAPS[k]
    _default_caps_cache = caps
    return caps


def ok(msg):
    print(f"  ok: {msg}")


# ---------------------------------------------------------------- journeys
def schema_path():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "..", "templates", "journey.schema.json")


_schema_cache = None


def load_schema():
    """Read+parse journey.schema.json once and reuse it — check_journey()
    runs once per journey file (e.g. 'all' mode over a whole output dir),
    and re-reading the same schema file from disk every time is pure waste."""
    global _schema_cache
    if _schema_cache is None:
        with open(schema_path(), encoding="utf-8") as f:
            _schema_cache = json.load(f)
    return _schema_cache


def check_journey(path):
    print(f"== journey: {path}")
    try:
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
    except Exception as e:  # noqa: BLE001
        fail(f"{path}: invalid JSON: {e}")
        return

    # 1. schema (jsonschema if available, structural otherwise)
    try:
        schema = load_schema()
        try:
            import jsonschema  # type: ignore

            errs = list(jsonschema.Draft202012Validator(schema).iter_errors(doc))
            for e in errs[:8]:
                fail(f"{path}: schema: {'/'.join(map(str, e.path))}: {e.message}")
            if len(errs) > 8:
                # A cap of 8 keeps a badly-malformed document's output readable, but
                # silently dropping the rest is a real false-negative: whoever fixes
                # the first 8 and re-runs would otherwise discover the 9th only on a
                # second pass, one violation at a time. Say so explicitly instead.
                fail(f"{path}: schema: ...and {len(errs) - 8} more schema violation(s) not shown (fix the above and re-run to see the rest)")
            if not errs:
                ok("schema valid")
        except (ImportError, AttributeError):
            # AttributeError: an old jsonschema without Draft202012Validator —
            # degrade to the structural check instead of crashing (see
            # requirements.txt for the recommended version)
            for k in schema["required"]:
                if k not in doc:
                    fail(f"{path}: missing required field '{k}'")
            ok("structural check done (jsonschema lib missing or too old)")
    except FileNotFoundError:
        warn("journey.schema.json not found; skipping schema check")

    # 2. id / version
    if "id" in doc and not ID_RE.match(str(doc["id"])):
        fail(f"{path}: id '{doc.get('id')}' violates <sector>-<pattern>-<nn>")
    if "version" not in doc:
        warn(f"{path}: no 'version' field — bump-on-change tracking impossible")
    elif not SEMVER.match(str(doc["version"])):
        fail(f"{path}: version '{doc['version']}' is not SemVer")

    # 2b. pattern must name a real file — JSON Schema can only check this is a
    # non-empty string, not that knowledge/journey-patterns/<pattern>.md exists;
    # the same class of cross-reference scripts/validate.sh already runs for
    # industries' pattern_priorities, applied here to the generated journey itself.
    # Once the file is known to exist, two more business-logic facts live only
    # there, not in this schema: the pattern's own canonical stage, and its
    # depth_range — "does this many steps make sense for this pattern" is a
    # question no static JSON Schema can answer, since the answer depends on
    # a *different* file's own frontmatter, not a fixed rule.
    pat = doc.get("pattern")
    if pat:
        here = os.path.dirname(os.path.abspath(__file__))
        pattern_path = os.path.join(here, "..", "knowledge", "journey-patterns", f"{pat}.md")
        if not os.path.isfile(pattern_path):
            fail(f"{path}: pattern '{pat}' has no knowledge/journey-patterns/{pat}.md — unknown pattern")
        else:
            try:
                pattern_fm = open(pattern_path, encoding="utf-8").read().split("---")[1]
            except (OSError, IndexError):
                pattern_fm = ""
            stage_m = re.search(r"^stage:\s*(\S+)", pattern_fm, re.M)
            if stage_m and doc.get("stage") and stage_m.group(1) != doc["stage"]:
                fail(
                    f"{path}: stage '{doc['stage']}' != {pat}.md's own stage "
                    f"'{stage_m.group(1)}' — a journey's stage should match the pattern it's built from"
                )
            range_m = re.search(r"^depth_range:\s*\[\s*(\d+)\s*,\s*(\d+)\s*\]", pattern_fm, re.M)
            n_steps = len(doc.get("steps", []))
            if range_m and n_steps:
                lo, hi = int(range_m.group(1)), int(range_m.group(2))
                if not (lo <= n_steps <= hi):
                    fail(
                        f"{path}: {n_steps} steps is outside {pat}.md's own depth_range [{lo}, {hi}] — "
                        f"either the depth class was miscomputed or this pattern isn't the right fit"
                    )

    # 3. constraints vs steps (compliance-class: hard fail)
    cons = doc.get("constraints") or {}
    allowed = set(cons.get("allowed_channels") or [])
    for step in doc.get("steps", []):
        ch = step.get("channel")
        if ch not in CHANNELS:
            fail(f"{path}: step {step.get('index')}: unknown channel '{ch}'")
        elif allowed and ch not in allowed:
            fail(
                f"{path}: step {step.get('index')}: channel '{ch}' not in "
                f"constraints.allowed_channels {sorted(allowed)} — Channel Consent Violation"
            )
        w = step.get("wait", "")
        if w and not ISO_WAIT.match(w):
            fail(f"{path}: step {step.get('index')}: wait '{w}' is not a supported ISO 8601 duration")

    # 4. KPIs: exactly-one primary, guardrail recommended
    kpis = doc.get("kpis", [])
    prim = [k for k in kpis if k.get("type") == "primary"]
    if len(prim) != 1:
        fail(f"{path}: expected exactly 1 primary KPI, found {len(prim)}")
    if not any(k.get("type") == "guardrail" for k in kpis):
        warn(f"{path}: no guardrail KPI")


# ------------------------------------------------------------------- copy
ROW = re.compile(r"^\|\s*([^|]+?)\s*\|\s*(.+?)\s*\|\s*(\d+)\s*\|\s*[≤<=]*\s*(\d+)\s*\|\s*$")
# "## Step 1 — email (`step-1`)" / "## Adım 1 · Email · +1sa" — channel is the
# first word after the separator; stop at the next non-word char (paren, ·,
# comma). Field ceilings are channel-specific (push != in-app != email), so
# every row's channel must be known before its limit can be checked.
STEP_HEAD = re.compile(r"^## (?:Step|Adım)\b.*?[—·-]\s*([A-Za-zçğıöşüÇĞİÖŞÜ][\w-]*)", re.M)
CHANNEL_ALIASES = {"in-app": "in_app", "inapp": "in_app", "app-push": "push"}

# Canonical per-field ceilings, one dict per channel — parsed LIVE from each
# knowledge/channels/<slug>.md's own frontmatter `limits:` block, never
# duplicated here by hand. A hand-maintained shadow copy is exactly the kind
# of drift that let WhatsApp's header/button-label ceilings go unenforced:
# whatsapp.md's own "Hard rules" already declared header <= 60 and
# button_label <= 25, but a second, separately-maintained dict here simply
# never got updated to match — so those two fields silently skipped the
# channel-ceiling check entirely (see canonical_limit's "unparsed" fallback).
# Keying by channel (not just field name) still matters: push's real
# title/body ceilings (40/120, push.md) are much tighter than in-app's
# (60/90-140, in-app.md) or email's (350, email.md) — a flat "title"/"body"
# table let push copy silently pass at the wrong channel's looser ceiling.
LIMITS_HEADING = re.compile(r"^limits:\s*$", re.M)
LIMIT_ENTRY = re.compile(r"^\s*([a-z_]+):\s*\{([^}]*)\}\s*$", re.M)
# Frontmatter key -> canonical (channel-agnostic) field name matched by the
# copy-doc table rows below; a key not listed here is already canonical.
LIMIT_KEY_ALIASES = {
    "cta_label": "cta", "body_modal": "body (modal)", "body_banner": "body (banner)",
    "button_label": "button",
}

_channel_limits_cache = None


def load_channel_limits():
    """{channel: {field: max_chars}}, parsed from every knowledge/channels/*.md's
    frontmatter `limits:` block. Only entries with `unit: chars` count as a
    character ceiling — in-app's `ctas: {max: 2, ...}` is a button COUNT, not a
    length, and has no `unit` key, which is what excludes it here. Cached: this
    runs once per validator invocation, not once per row checked."""
    global _channel_limits_cache
    if _channel_limits_cache is not None:
        return _channel_limits_cache
    here = os.path.dirname(os.path.abspath(__file__))
    limits = {}
    for path in sorted(glob.glob(os.path.join(here, "..", "knowledge", "channels", "*.md"))):
        base = os.path.splitext(os.path.basename(path))[0]
        if base == "_template":
            continue
        channel = "in_app" if base == "in-app" else base
        try:
            text = open(path, encoding="utf-8").read()
        except OSError:
            continue
        m = LIMITS_HEADING.search(text)
        if not m:
            continue
        rest = text[m.end():]
        fence = re.search(r"^---\s*$", rest, re.M)
        block = rest[: fence.start()] if fence else rest
        chan_limits = {}
        for entry in LIMIT_ENTRY.finditer(block):
            key, body = entry.group(1), entry.group(2)
            if not re.search(r"unit:\s*chars", body):
                continue
            mx = re.search(r"max:\s*(\d+)", body)
            if not mx:
                continue
            chan_limits[LIMIT_KEY_ALIASES.get(key, key)] = int(mx.group(1))
        limits[channel] = chan_limits
    _channel_limits_cache = limits
    return limits


# Turkish field names -> canonical (channel-agnostic) English field name.
FIELD_ALIASES = {
    "konu": "subject", "ön izleme": "preheader", "gövde": "body",
    "başlık": "title", "buton": "cta", "birincil buton": "primary cta",
    "ikincil buton": "secondary cta", "gövde (banner)": "body (banner)",
    "gövde (modal)": "body (modal)",
}
# knowledge/channels/sms.md rule 2: ş/ğ/ı/İ are NOT in the GSM-7 default
# alphabet and force UCS-2 (160 -> 70 chars/segment); ç/ö/ü alone survive
# GSM-7 and do not — don't over-match the whole Turkish diacritic set.
SMS_TR_CHARS = re.compile(r"[şğıİŞĞ]")


def canonical_limit(field, channel=None, content=""):
    f = FIELD_ALIASES.get(tr_fold(field).strip(), tr_fold(field).strip())
    ch = CHANNEL_ALIASES.get(tr_fold(channel).strip(), tr_fold(channel).strip()) if channel else None
    limits = load_channel_limits()
    if ch == "sms" and f == "body":
        # sms.md declares both ceilings by name (body=160 GSM-7, body_unicode=70
        # UCS-2); the choice between them is the one genuinely dynamic bit
        # (depends on the content itself), so it stays code, not frontmatter.
        sms = limits.get("sms", {})
        return sms.get("body_unicode", 70) if SMS_TR_CHARS.search(content) else sms.get("body", 160)
    if ch and ch in limits:
        chan_limits = limits[ch]
        if f in chan_limits:
            return chan_limits[f]
        # "primary cta"/"secondary cta" (templates/copy-output.md's in-app field
        # set: Title, Body, Primary CTA, Secondary CTA) are the same ceiling as
        # plain "cta" wherever a channel file declares only one cta_label limit
        # for both button slots, which is every channel today.
        if f in ("primary cta", "secondary cta"):
            return chan_limits.get("cta")
        return None
    # Channel unparsed/unknown: don't guess by scanning every channel's
    # dict — that's exactly the cross-channel mismatch this function exists
    # to prevent (push matching in-app's looser ceiling, etc).
    return None


_banned_terms_cache = {}


def _banned_match_fold(s):
    """Casefold for banned-term matching only. tr_fold() fixes İ's Unicode
    over-expansion, but a caps-lock banned word ("KAZANDINIZ") uses plain ASCII
    I for what should fold to dotless ı, and Python's locale-blind .lower()
    takes it to dotted i instead — silently missing the match against a lexicon
    entry stored dotless (verified: tr_fold('KAZANDINIZ') != tr_fold('kazandınız')).
    Collapsing i/ı (already merged with İ/I by tr_fold) to one symbol sidesteps
    the ambiguity for this narrow use. tr_fold itself is left untouched — its
    other callers (field/channel alias lookup) don't hit this ambiguity."""
    return tr_fold(s).replace("ı", "i")


def _quoted_terms_in_section(file_path, heading_re):
    """Pull the double-quoted literal phrases out of a knowledge file's banned/spam
    section. These are the unambiguous exact-match terms; the same section's
    unquoted prose (all-caps words, more than one exclamation mark, "tıklayın" as
    a bare CTA) is a rule needing judgment, not a literal string — it stays a
    reviewer call, this function makes no claim to check it."""
    if file_path in _banned_terms_cache:
        return _banned_terms_cache[file_path]
    try:
        text = open(file_path, encoding="utf-8").read()
    except OSError:
        _banned_terms_cache[file_path] = None
        return None
    m = heading_re.search(text)
    if not m:
        _banned_terms_cache[file_path] = []
        return []
    rest = text[m.end():]
    nxt = re.search(r"^## ", rest, re.M)
    section = rest[: nxt.start()] if nxt else rest
    terms = [_banned_match_fold(t) for t in QUOTED_TERM.findall(section)]
    _banned_terms_cache[file_path] = terms
    return terms


def banned_terms_for(sector, channel):
    """Quoted banned/spam terms applicable to one copy block: the sector lexicon's
    'Banned outright' list always applies; email additionally carries its own
    'Spam-trigger words' (a deliverability concept tied to email's spam-folder
    mechanics — no other channel file has an equivalent section)."""
    here = os.path.dirname(os.path.abspath(__file__))
    terms = []
    if sector:
        found = _quoted_terms_in_section(
            os.path.join(here, "..", "knowledge", "lexicons", f"{sector}.md"), BANNED_HEADING
        )
        if found is None:
            warn(f"no lexicon file found for sector '{sector}' — banned-word check skipped")
        else:
            terms += found
    if channel == "email":
        found = _quoted_terms_in_section(
            os.path.join(here, "..", "knowledge", "channels", "email.md"), SPAM_HEADING
        )
        if found:
            terms += found
    return terms


def check_copy(path, max_discount=None, sector=None):
    print(f"== copy: {path}")
    try:
        text = open(path, encoding="utf-8").read()
    except Exception as e:  # noqa: BLE001
        fail(f"{path}: unreadable: {e}")
        return

    # Per-step fallback presence: a step whose variants use {{vars}} must
    # carry a "### Fallback" section — otherwise a missing variable ships as
    # literal "Merhaba {{first_name}}". (Reviewer judges quality; code checks
    # presence, which is exactly the class of miss models make.)
    step_re = re.compile(r"^## Step\b", re.M)
    fallback_heading_re = re.compile(r"^### Fallback\b.*$", re.M)
    next_heading_re = re.compile(r"^#{2,3} ", re.M)
    steps = step_re.split(text)[1:] if step_re.search(text) else []
    starts = [m.start() for m in step_re.finditer(text)]
    for idx, block in enumerate(steps):
        line_no = text[: starts[idx]].count("\n") + 1
        has_var = re.search(r"\{\{[^}]+\}\}", block)
        fb = fallback_heading_re.search(block)
        if has_var and not fb:
            fail(
                f"{path}:{line_no}: step uses personalization variables but has no "
                f"'### Fallback' section — Missing Fallback Violation"
            )
        elif fb:
            # A heading isn't the same claim as a working fallback — the
            # section's own content still has to be free of {{vars}} that
            # aren't system-safe, or it's the exact failure mode ("Merhaba
            # {{first_name}}") wearing a Fallback label. Bound the section to
            # the next ##/### heading (or end of block), never the whole step.
            rest = block[fb.end():]
            nxt = next_heading_re.search(rest)
            fb_body = rest[: nxt.start()] if nxt else rest
            fb_vars = re.findall(r"\{\{([^}]+)\}\}", fb_body)
            if fb_vars:
                fb_line = line_no + block[: fb.start()].count("\n")
                fail(
                    f"{path}:{fb_line}: Fallback section itself still contains "
                    f"{{{{{fb_vars[0]}}}}} — a fallback with a non-system-safe variable "
                    f"isn't a fallback, it's the same failure with an extra heading "
                    f"(Missing Fallback Violation)"
                )

        # Rich-media image line (push, optional — templates/copy-output.md):
        # not part of the chars-table, so parsed on its own. Checks only what's
        # statically verifiable — HTTPS + non-empty alt text — never actual file
        # size, which needs a network fetch this validator deliberately skips.
        img = IMAGE_LINE.search(block)
        if img:
            img_line = line_no + block[: img.start()].count("\n")
            url, alt = img.group(1).strip(), img.group(2).strip()
            if url not in ("—", "-"):
                if not url.startswith("https://"):
                    fail(f"{path}:{img_line}: Image URL '{url}' is not HTTPS — Insecure Image Reference Violation")
                if not alt:
                    fail(f"{path}:{img_line}: Image present but Alt text is empty — Missing Image Alt Text Violation")

        # Variant metadata: copy-reviewer's checklist already treats missing
        # strategy/hypothesis as a FIX, but that was pure human judgment with
        # no code backstop — the same class of miss code catches faster and
        # more reliably elsewhere in this file. A JSON fence right after a
        # "### Variant" heading must parse and carry non-empty strategy +
        # hypothesis strings; lifecycle-results reads these labels verbatim
        # when scoring test outcomes, so a malformed or empty one silently
        # breaks that downstream scoring, not just this doc's completeness.
        for vm in VARIANT_HEAD.finditer(block):
            v_line = line_no + block[: vm.start()].count("\n")
            after = block[vm.end():]
            fence = VARIANT_JSON_FENCE.match(after.lstrip("\n"))
            if not fence:
                fail(f"{path}:{v_line}: variant has no ```json strategy/hypothesis fence — Missing Variant Metadata Violation")
                continue
            try:
                meta = json.loads(fence.group(1))
            except json.JSONDecodeError as e:
                fail(f"{path}:{v_line}: variant metadata is not valid JSON: {e} — Missing Variant Metadata Violation")
                continue
            for key in ("strategy", "hypothesis"):
                if not str(meta.get(key, "")).strip():
                    fail(f"{path}:{v_line}: variant metadata missing non-empty '{key}' — Missing Variant Metadata Violation")

    # Legal-review flag without its required explanation is worse than no
    # flag: it tells the reader "something needs sign-off" without saying
    # what, so nobody can act on it. "Review status" is a whole-document
    # header field (before any "## Step" split), not per-step — checked once
    # here, against the full text, not inside the per-step loop above.
    # "Reviewer notes" itself is written per-step (right after that step's
    # Fallback), so at least one non-placeholder instance must exist anywhere
    # in the document when the document-level flag is ⚖️.
    review_m = REVIEW_STATUS_RE.search(text)
    if review_m and "⚖" in review_m.group(1):
        has_real_notes = any(
            m.group(1).strip() and not m.group(1).strip().startswith("<")
            for m in REVIEWER_NOTES_RE.finditer(text)
        )
        if not has_real_notes:
            fail(
                f"{path}: Review status is ⚖️ legal review required but no 'Reviewer notes' "
                f"with actual content was found — the exact claim and triggering rule must be "
                f"stated (Missing Legal Notes Violation)"
            )

    in_code = False
    rows = 0
    channel = None
    for i, line in enumerate(text.splitlines(), 1):
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        head = STEP_HEAD.match(line)
        if head:
            channel = head.group(1)
            continue
        m = ROW.match(line)
        if m:
            field, content, declared, limit = m.group(1), m.group(2), int(m.group(3)), int(m.group(4))
            if field.lower() in ("field", "alan"):
                continue
            rows += 1
            actual = len(content)
            # 5a. declared count must be the truth, not an estimate
            if actual != declared:
                fail(
                    f"{path}:{i}: '{field}' declared {declared} chars but content is "
                    f"{actual} — counts must be real (Count Integrity Violation)"
                )
            # 5b. limit — declared, then canonical (inflated Limit columns don't help)
            if actual > limit:
                fail(f"{path}:{i}: '{field}' is {actual} chars, limit {limit} — Limit Violation")
            canon = canonical_limit(field, channel, content)
            if canon is not None:
                if limit > canon:
                    fail(
                        f"{path}:{i}: '{field}' declares limit {limit} but the channel "
                        f"ceiling is {canon} — Limit Inflation Violation"
                    )
                if actual > canon:
                    fail(
                        f"{path}:{i}: '{field}' is {actual} chars, channel ceiling "
                        f"{canon} — Limit Violation"
                    )
            elif channel is None:
                warn(f"{path}:{i}: '{field}' has no detected channel (no preceding '## Step ... — <channel>' "
                     f"header) — channel-ceiling backstop skipped for this row")
            # 5c. em/en dash in customer-facing copy
            if EMDASH.search(content):
                fail(f"{path}:{i}: '{field}' contains em/en dash — banned in customer copy")
            # 5e. candidate banned/spam terms (quoted literals only — see banned_terms_for).
            # A hit is a CANDIDATE, not a certain violation: it can over-match a term that's
            # a substring of an unrelated longer word, or one appearing inside a required
            # legal disclaimer — warn, don't fail, so the reviewer confirms context instead
            # of a false positive blocking the pipeline outright.
            folded_content = _banned_match_fold(content)
            for term in banned_terms_for(sector, channel):
                if term and term in folded_content:
                    warn(f"{path}:{i}: '{field}' contains candidate banned term '{term}' — "
                         f"confirm in context, not an automatic violation (Banned Word Candidate)")
        # 5d. discount ceiling anywhere in copy text (outside code fences).
        # The %NN figure must sit NEAR a discount word (±40 chars) — a line like
        # "İndirim: yok ... push izinli oran %40" mentions a percentage that is
        # not a discount, and line-level matching flagged exactly that in a live run.
        if max_discount is not None and DISCOUNT_CTX.search(line):
            for m2 in DISCOUNT.finditer(line):
                lo, hi = max(0, m2.start() - 40), m2.end() + 40
                if not DISCOUNT_CTX.search(line[lo:hi]):
                    continue
                val = float((m2.group(1) or m2.group(2)).replace(",", "."))
                if val > max_discount:
                    fail(
                        f"{path}:{i}: mentions %{val:g} discount, brand limit is "
                        f"%{max_discount:g} — Discount Limit Violation"
                    )
    if rows:
        ok(f"{rows} copy table rows recounted")
    else:
        warn(f"{path}: no copy tables found to verify")


# --------------------------------------------------------- consistency
# templates/journey-doc.md (human-reviewed) and the journey JSON (what
# lifecycle-export actually consumes) are two independent representations of
# the same design — nothing previously checked they agree. Deliberately
# narrow: only compare what's reliably parseable without false positives.
# Never diff intent text (wording legitimately varies between drafts) or
# wait-duration equivalence (markdown's natural-language phrasing vs the
# JSON's strict ISO 8601 can't be normalized against each other safely) —
# those stay a human read. Step count, channel-per-step, branch-condition
# PRESENCE (not content), KPI count/types, id, and depth_class are all
# closed-vocabulary or structural facts a regex can compare without guessing.
MD_ID_RE = re.compile(r"\*\*ID:\*\*\s*`([^`]+)`")
MD_DEPTH_RE = re.compile(r"\*\*Depth class:\*\*\s*(simple|standard|branched)\b", re.I)
MD_STEP_ROW = re.compile(r"^\|\s*(\d+)\s*\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|\s*$", re.M)
MD_KPI_ROW = re.compile(r"^\|([^|]+)\|\s*(primary|secondary|guardrail)\s*\|([^|]*)\|([^|]*)\|\s*$", re.M | re.I)
EMPTY_CELL = ("", "—", "-")


def _md_section(text, heading_re):
    m = heading_re.search(text)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^## ", rest, re.M)
    return rest[: nxt.start()] if nxt else rest


def check_consistency(md_path, json_path):
    print(f"== consistency: {md_path} vs {json_path}")
    try:
        md = open(md_path, encoding="utf-8").read()
    except Exception as e:  # noqa: BLE001
        fail(f"{md_path}: unreadable: {e}")
        return
    try:
        with open(json_path, encoding="utf-8") as f:
            doc = json.load(f)
    except Exception as e:  # noqa: BLE001
        fail(f"{json_path}: invalid JSON: {e}")
        return

    before = len(failures)

    m = MD_ID_RE.search(md)
    if not m:
        warn(f"{md_path}: no '**ID:** `...`' header found — skipping id check")
    elif m.group(1) != doc.get("id"):
        fail(f"{md_path}: id '{m.group(1)}' != {json_path}: id '{doc.get('id')}'")

    m = MD_DEPTH_RE.search(md)
    if m:
        md_depth = m.group(1).lower()
        if "depth_class" in doc:
            if md_depth != doc["depth_class"]:
                fail(f"{md_path}: depth class '{md_depth}' != {json_path}: depth_class '{doc['depth_class']}'")
        else:
            warn(f"{json_path}: markdown declares depth class '{md_depth}' but JSON has no depth_class field")

    steps_section = _md_section(md, re.compile(r"^## 5\. Steps", re.M))
    md_steps = []
    for row in MD_STEP_ROW.finditer(steps_section):
        idx, _wait, channel, _intent, branch, _copyref = (g.strip() for g in row.groups())
        if not idx.isdigit():
            continue  # header row ("#") or separator ("---") — not a data row
        md_steps.append({"channel": channel.strip("` "), "has_branch": branch not in EMPTY_CELL})
    json_steps = doc.get("steps", [])
    if md_steps:
        if len(md_steps) != len(json_steps):
            fail(f"{md_path}: {len(md_steps)} step rows vs {json_path}: {len(json_steps)} steps — count mismatch")
        else:
            for i, (ms, js) in enumerate(zip(md_steps, json_steps), 1):
                if ms["channel"] and ms["channel"] != js.get("channel"):
                    fail(f"{md_path} step {i}: channel '{ms['channel']}' != {json_path} step {i}: channel '{js.get('channel')}'")
                js_has_branch = bool(js.get("branch_condition"))
                if ms["has_branch"] != js_has_branch:
                    fail(
                        f"{md_path} step {i}: branch-condition presence ({ms['has_branch']}) != "
                        f"{json_path} step {i}: ({js_has_branch})"
                    )
    else:
        warn(f"{md_path}: no parseable rows in section 5 (Steps) — skipping step comparison")

    kpi_section = _md_section(md, re.compile(r"^## 6\. Measurement", re.M))
    md_kpis = [
        (name.strip().strip("`"), ktype.lower())
        for name, ktype, _def, _target in MD_KPI_ROW.findall(kpi_section)
    ]
    json_kpis = [(k.get("name"), k.get("type")) for k in doc.get("kpis", [])]
    if md_kpis:
        if len(md_kpis) != len(json_kpis):
            fail(f"{md_path}: {len(md_kpis)} KPI rows vs {json_path}: {len(json_kpis)} kpis — count mismatch")
        md_types, json_types = sorted(t for _, t in md_kpis), sorted(t for _, t in json_kpis)
        if md_types != json_types:
            fail(f"{md_path}: KPI types {md_types} != {json_path}: KPI types {json_types}")
    else:
        warn(f"{md_path}: no parseable rows in section 6 (Measurement) — skipping KPI comparison")

    if len(failures) == before:
        ok("markdown/JSON agree on id, depth_class, step count+channels+branch-presence, KPI count+types")


# -------------------------------------------------------------- portfolio
def check_portfolio(path):
    """portfolio.json: machine-readable journey registry.

    {"brand": str, "caps": {channel: n, "total": n}?, "journeys": [
       {"id","pattern","stage","priority","channels":[...],
        "audience_group": str, "est_msgs_per_week": {channel: n},
        "vertical": str?}]}

    `vertical` is optional and only meaningful for multi-vertical brands —
    absent entirely for single-industry brands. It exists so a downstream
    consumer working from this JSON alone (lifecycle-export, an eval script)
    can group/filter journeys by vertical without re-deriving it from
    knowledge/brands/<brand>.md's applicable_industries mapping.
    """
    print(f"== portfolio: {path}")
    try:
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
    except Exception as e:  # noqa: BLE001
        fail(f"{path}: invalid JSON: {e}")
        return

    js = doc.get("journeys", [])
    if not js:
        fail(f"{path}: no journeys in registry")
        return

    ids = [j.get("id") for j in js]
    for dup in {i for i in ids if ids.count(i) > 1}:
        fail(f"{path}: duplicate journey id '{dup}'")

    verticals_present = [j.get("vertical") for j in js if j.get("vertical")]
    if verticals_present and len(verticals_present) < len(js):
        missing = [j.get("id") for j in js if not j.get("vertical")]
        warn(
            f"{path}: {len(verticals_present)}/{len(js)} journeys declare 'vertical' — "
            f"mixed declaration in one registry usually means an oversight, not a real "
            f"single-industry journey mixed into a multi-vertical brand's portfolio. "
            f"Missing on: {missing}"
        )

    caps = {**load_default_caps(), **(doc.get("caps") or {})}
    groups = {}
    for j in js:
        g = j.get("audience_group", "all")
        per = j.get("est_msgs_per_week", {})
        if not isinstance(per, dict):
            # registry contract (lifecycle-journeys step 6): per-CHANNEL dict,
            # e.g. {"email": 2, "push": 1} — a bare total can't be checked
            # against per-channel caps
            fail(
                f"{path}: journey '{j.get('id')}': est_msgs_per_week must be a per-channel "
                f"dict like {{\"email\": 2, \"push\": 1}}, got {type(per).__name__} "
                f"({per!r}) — see the registry contract in lifecycle-journeys"
            )
            continue
        groups.setdefault(g, {}).setdefault("_journeys", []).append(j.get("id"))
        for ch, n in per.items():
            groups[g][ch] = groups[g].get(ch, 0) + n

    def check_caps(label, sums):
        total = sum(v for k, v in sums.items() if k != "_journeys")
        for ch, n in sums.items():
            if ch == "_journeys":
                continue
            if n > caps.get(ch, 99):
                fail(
                    f"{path}: {label}: worst case {n} {ch}-msgs/week exceeds "
                    f"cap {caps[ch]} (journeys: {sums['_journeys']}) — Frequency Cap Violation"
                )
        if total > caps["total"]:
            fail(
                f"{path}: {label}: worst case {total} msgs/week total exceeds "
                f"cap {caps['total']} — Frequency Cap Violation"
            )

    for g, sums in groups.items():
        check_caps(f"audience group '{g}'", sums)

    # Cross-group overlap: a real user can sit in several audience groups at
    # once (new signup who abandons a cart in the same week). Per-group sums
    # alone silently approve that violation. The registry declares which
    # groups can overlap; each declared combo is checked as one merged user.
    overlaps = doc.get("audience_overlaps") or []
    overlap_sums = {}
    for combo in overlaps:
        merged = {"_journeys": []}
        for g in combo:
            for ch, n in groups.get(g, {}).items():
                if ch == "_journeys":
                    merged["_journeys"] += n
                else:
                    merged[ch] = merged.get(ch, 0) + n
        overlap_sums["+".join(combo)] = merged
        check_caps(f"overlap {'+'.join(combo)}", merged)
    # Campaign-week math (knowledge/calendar-rules.md): declared campaign
    # sends count against the SAME caps — the cap doesn't grow because it's
    # Black Friday. When the registry declares them, every group AND overlap
    # combo is re-checked with the campaign load added (a combo's baseline
    # can be under cap while combo+campaign pushes it over — checking groups
    # alone misses exactly that cross-group case during a campaign window).
    camp = doc.get("campaign_msgs_per_week") or {}
    if camp and not isinstance(camp, dict):
        fail(f"{path}: campaign_msgs_per_week must be a per-channel dict, got {type(camp).__name__}")
        camp = {}
    if camp:
        for g, sums in groups.items():
            merged = {k: v for k, v in sums.items()}
            for ch, n in camp.items():
                if ch != "_journeys":
                    merged[ch] = merged.get(ch, 0) + n
            check_caps(f"campaign week — audience group '{g}'", merged)
        for label, sums in overlap_sums.items():
            merged = {k: v for k, v in sums.items()}
            for ch, n in camp.items():
                if ch != "_journeys":
                    merged[ch] = merged.get(ch, 0) + n
            check_caps(f"campaign week — overlap {label}", merged)

    if len(groups) > 1 and not overlaps:
        warn(
            f"{path}: {len(groups)} audience groups but no audience_overlaps declared — "
            "cross-group frequency (one user in several groups at once) is UNCHECKED. "
            "Declare audience_overlaps: [[groupA, groupB], ...] or confirm the groups "
            "are mutually exclusive by definition."
        )
    ok(f"{len(js)} journeys, {len(groups)} audience groups, {len(overlaps)} overlap combos checked against caps")


# ---------------------------------------------------------------- canvas
def _canvas_skeleton(text):
    """Neutralize the swappable regions (JOURNEYS array, HOLDOUT_TIP/DATA_NOTE
    constants, <title>, eyebrow/h1/lede) — everything else must match the
    template byte-for-byte (CLAUDE.md rule 2's copy-then-edit mechanism)."""
    out, in_j = [], False
    for ln in text.splitlines():
        s = ln.strip()
        if in_j:
            if s == "];":
                in_j = False
                out.append("@JOURNEYS@")
            continue
        if s.startswith("const JOURNEYS"):
            in_j = True
            continue
        if s.startswith("const HOLDOUT_TIP") or s.startswith("const DATA_NOTE"):
            out.append("@CONST@")
            continue
        ln = re.sub(r"<title>.*?</title>", "<title>@</title>", ln)
        ln = re.sub(r'(<p class="eyebrow">).*?(</p>)', r"\1@\2", ln)
        ln = re.sub(r"(<h1>).*?(</h1>)", r"\1@\2", ln)
        ln = re.sub(r'(<p class="lede">).*?(</p>)', r"\1@\2", ln)
        out.append(ln)
    return out


def check_canvas(path, template):
    print(f"== canvas: {path} (template: {template})")
    try:
        out_sk = _canvas_skeleton(open(path, encoding="utf-8").read())
        tpl_sk = _canvas_skeleton(open(template, encoding="utf-8").read())
    except Exception as e:  # noqa: BLE001
        fail(f"{path}: unreadable: {e}")
        return
    if out_sk == tpl_sk:
        ok("canvas skeleton matches the template outside swappable regions")
        return
    diffs = [i for i, (a, b) in enumerate(zip(tpl_sk, out_sk)) if a != b]
    detail = f"first differing line ~{diffs[0] + 1}" if diffs else \
        f"line count differs (template {len(tpl_sk)}, output {len(out_sk)})"
    fail(
        f"{path}: canvas boilerplate drifted from {template} — {detail}. "
        f"The template is copied and edited in place, never retyped/elided; "
        f"only JOURNEYS, title, and header texts may change (keep header texts single-line)."
    )


# ------------------------------------------------------------------ main
def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    mode, rest = argv[0], argv[1:]
    max_discount = None
    if "--max-discount" in rest:
        i = rest.index("--max-discount")
        max_discount = float(rest[i + 1])
        rest = rest[:i] + rest[i + 2 :]
    sector = None
    if "--sector" in rest:
        i = rest.index("--sector")
        sector = rest[i + 1]
        rest = rest[:i] + rest[i + 2 :]

    if mode == "journey":
        for p in rest:
            check_journey(p)
    elif mode == "copy":
        for p in rest:
            check_copy(p, max_discount, sector)
    elif mode == "portfolio":
        for p in rest:
            check_portfolio(p)
    elif mode == "consistency":
        if len(rest) != 2:
            print("usage: validate_output.py consistency <journey.md> <journey.json>")
            return 2
        check_consistency(rest[0], rest[1])
    elif mode == "canvas":
        template = None
        if "--template" in rest:
            i = rest.index("--template")
            template = rest[i + 1]
            rest = rest[:i] + rest[i + 2 :]
        if not template:
            print("usage: validate_output.py canvas <output.html> --template <template.html>")
            return 2
        for p in rest:
            check_canvas(p, template)
    elif mode == "all":
        root = rest[0]
        # First pass: collect every journey JSON's id -> path, so the second
        # pass can pair a journey-doc.md with its JSON without assuming a
        # filename convention (portfolio ordering, P0-first naming, etc. all
        # vary run to run — the id inside each file is the only stable key).
        journey_json_by_id = {}
        for dirpath, _dirs, files in os.walk(root):
            for fn in sorted(files):
                if not fn.endswith(".json") or fn == "portfolio.json":
                    continue
                p = os.path.join(dirpath, fn)
                try:
                    with open(p, encoding="utf-8") as f:
                        peek = json.load(f)
                except Exception:  # noqa: BLE001
                    continue
                if isinstance(peek, dict) and "steps" in peek and "kpis" in peek and "id" in peek:
                    journey_json_by_id[peek["id"]] = p

        for dirpath, _dirs, files in os.walk(root):
            for fn in sorted(files):
                p = os.path.join(dirpath, fn)
                if fn == "portfolio.json":
                    check_portfolio(p)
                elif fn.endswith(".json"):
                    # Shape-check before routing to the journey schema — an
                    # unrelated JSON artifact dropped in output/ (a DQS
                    # summary, a QA-payload export) isn't journey-shaped and
                    # would otherwise hard-fail against journey.schema.json's
                    # required fields for no real reason.
                    try:
                        with open(p, encoding="utf-8") as f:
                            peek = json.load(f)
                    except Exception:  # noqa: BLE001
                        peek = None
                    if isinstance(peek, dict) and "steps" in peek and "kpis" in peek:
                        check_journey(p)
                    else:
                        warn(f"{p}: skipped in 'all' mode — not journey-shaped (no steps/kpis)")
                elif fn.endswith(".md"):
                    try:
                        text = open(p, encoding="utf-8", errors="ignore").read()
                    except Exception:  # noqa: BLE001
                        text = ""
                    # Detect a copy doc by its actual structure (the "## Step"
                    # markers every copy doc has, regardless of language),
                    # not by filename — TR output is named iletisim-metinleri
                    # (-kaynak).md, EN is copy-output-derived, neither always
                    # matches a fixed prefix/regex on the filename alone.
                    id_match = MD_ID_RE.search(text)
                    if id_match and re.search(r"^## 5\. Steps", text, re.M):
                        jid = id_match.group(1)
                        json_path = journey_json_by_id.get(jid)
                        if json_path:
                            check_consistency(p, json_path)
                        else:
                            warn(f"{p}: journey doc id '{jid}' has no matching journey JSON in {root} — "
                                 f"skipping consistency check (the JSON may not have been written yet)")
                    elif STEP_HEAD.search(text[:4096]) or re.search(r"^## Step\b", text[:4096], re.M):
                        check_copy(p, max_discount, sector)
    else:
        print(__doc__)
        return 2

    print()
    if failures:
        # A fixed, predictable block at the end — not a request to re-scan
        # interleaved FAIL/warn/ok lines above — is what makes this reliably
        # re-promptable, whether the reader is a human or the same agent one
        # turn later. This restates, never auto-fixes: CLAUDE.md rule 12 and
        # this file's own exit message both say "stop and report", and that's
        # not just caution for its own sake — LLM self-correction without an
        # external, ground-truth check has a documented tendency to degrade
        # rather than improve results, which is exactly why this validator
        # exists as that external check instead of trusting a model to catch
        # its own mistakes unaided.
        print(f"TO FIX ({len(failures)}):")
        for i, f in enumerate(failures, 1):
            print(f"  {i}. {f}")
        print()
        print(f"OUTPUT VALIDATION FAILED — {len(failures)} violation(s). "
              "Stop and report; do not self-correct compliance violations.")
        return 1
    print(f"OUTPUT VALIDATION PASSED ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

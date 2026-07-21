#!/usr/bin/env python3
"""Deterministically build a canvas HTML from its template by copying the
template and substituting ONLY the swappable regions — the exact cp-then-edit
mechanism CLAUDE.md rule 2 mandates, done in code so it is correct every run.

Why a script: doing the substitution by hand (regex in a model's head) is
error-prone in two specific ways that both silently break the skeleton check:
  1. The template's SWAPPABLE comment contains a literal `<title>`, so a
     dot-matches-newline title regex swallows the comment and the real title.
  2. The JOURNEYS array must end with a bare `];` line (check_canvas's boundary
     marker); emitting it on one line breaks where the neutralizer resumes.
This tool encodes both fixes once. It also self-verifies: after writing, it
runs the same skeleton neutralizer check_canvas uses and refuses to emit a file
that drifted from the template outside the swappable regions.

Usage:
  build_canvas.py --template templates/canvas.html --journeys j.json \
                  --meta meta.json --out output/<project>/canvas.html

  --journeys : JSON file — an array of journey objects (the canvas node trees).
               Serialized into `const JOURNEYS = [ ... ];` with a bare `];` close.
  --meta     : JSON file with any of: title, eyebrow, h1, lede, holdout_tip,
               data_note. Each replaces its swappable region if present in BOTH
               the meta and the template. holdout_tip/data_note are the full JS
               right-hand side (e.g. 'tip("a","b")' or a quoted string) WITHOUT
               the trailing semicolon.
Exit: 0 = built and self-verified, 2 = usage error / drift detected.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from validate_output import _canvas_skeleton  # reuse the authoritative neutralizer


def _sub_once(text, pattern, repl, flags=0):
    """re.sub with count=1; returns (new_text, n_replacements)."""
    new, n = re.subn(pattern, lambda _m: repl, text, count=1, flags=flags)
    return new, n


def build(template_path, journeys, meta):
    t = Path(template_path).read_text(encoding="utf-8")

    # Header texts — NO DOTALL so the `<title>` inside the SWAPPABLE comment
    # (which has no closing `</title>` on its own line) is never matched.
    if "title" in meta:
        t, _ = _sub_once(t, r"<title>.*?</title>", f"<title>{meta['title']}</title>")
    if "eyebrow" in meta:
        t, _ = _sub_once(t, r'<p class="eyebrow">.*?</p>', f'<p class="eyebrow">{meta["eyebrow"]}</p>')
    if "h1" in meta:
        t, _ = _sub_once(t, r"<h1>.*?</h1>", f"<h1>{meta['h1']}</h1>")
    if "lede" in meta:
        t, _ = _sub_once(t, r'<p class="lede">.*?</p>', f'<p class="lede">{meta["lede"]}</p>')

    # HOLDOUT_TIP / DATA_NOTE — whole line (no DOTALL), so an inner ';' inside
    # the string literal doesn't truncate the match. Only if the template has them.
    if "holdout_tip" in meta and "const HOLDOUT_TIP" in t:
        t, _ = _sub_once(t, r"const HOLDOUT_TIP = .*", f"const HOLDOUT_TIP = {meta['holdout_tip']};")
    if "data_note" in meta and "const DATA_NOTE" in t:
        t, _ = _sub_once(t, r"const DATA_NOTE = .*", f"const DATA_NOTE = {meta['data_note']};")

    # JOURNEYS — multi-line, one journey object per line, closed by a bare `];`
    # line. json.dumps produces valid JS string literals (double-quoted); a
    # journey object serialized compact never contains a bare `];` line, so the
    # only `];` is the intended closer.
    lines = ["const JOURNEYS = ["]
    for i, jj in enumerate(journeys):
        comma = "," if i < len(journeys) - 1 else ""
        lines.append("  " + json.dumps(jj, ensure_ascii=False) + comma)
    lines.append("];")
    block = "\n".join(lines)
    t, n = _sub_once(t, r"const JOURNEYS = \[.*?\n\];", block, flags=re.S)
    if n != 1:
        raise ValueError(
            f"could not locate the 'const JOURNEYS = [ ... \\n];' region in "
            f"{template_path} — is this a canvas template?"
        )
    return t


def self_verify(built_text, template_path):
    """Refuse to emit a file whose boilerplate drifted from the template."""
    tmpl = Path(template_path).read_text(encoding="utf-8")
    a = _canvas_skeleton(tmpl)
    b = _canvas_skeleton(built_text)
    if a != b:
        # find first differing line for a useful message
        for i, (x, y) in enumerate(zip(a, b)):
            if x != y:
                return False, f"skeleton drift at neutralized line {i}: template={x!r} built={y!r}"
        return False, f"skeleton length differs (template {len(a)} vs built {len(b)} lines)"
    return True, "skeleton matches the template outside swappable regions"


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", required=True)
    ap.add_argument("--journeys", required=True, help="JSON file: array of journey node-tree objects")
    ap.add_argument("--meta", required=True, help="JSON file: title/eyebrow/h1/lede/holdout_tip/data_note")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    try:
        journeys = json.loads(Path(args.journeys).read_text(encoding="utf-8"))
        meta = json.loads(Path(args.meta).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if not isinstance(journeys, list) or not journeys:
        print("error: --journeys must be a non-empty JSON array", file=sys.stderr)
        return 2

    try:
        built = build(args.template, journeys, meta)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    ok, msg = self_verify(built, args.template)
    if not ok:
        print(f"FAIL: {msg}", file=sys.stderr)
        print("Refusing to write a drifted canvas. This is a bug in build_canvas.py, not your data.", file=sys.stderr)
        return 2
    Path(args.out).write_text(built, encoding="utf-8")
    print(f"ok: wrote {args.out} ({len(journeys)} journeys) — {msg}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""PostToolUse hook (Write|Edit|MultiEdit): validate a deliverable the moment it is written.

CLAUDE.md rule 12 says journey JSONs, copy docs, the portfolio registry and the
dossier pass scripts/validate_output.py before they reach the user. `finish`
runs every mode at the end of a run; this hook moves the same check to write
time, so a violation surfaces on the turn that introduced it instead of after
the whole pipeline has been built on top of it.

Scope (anything else exits 0 without running the validator):
  - only files under an `output/` folder or an `evals/out/` folder
  - a journey JSON (top-level "nodes" or "steps")    -> journey
  - portfolio.json                                   -> portfolio
  - dossier.md                                       -> dossier
  - _copy/<id>.md                                    -> copy (+ --sector/--max-discount
                                                        from output/brands/<brand>.md when
                                                        the sibling portfolio.json names a brand)
  Canvases (HTML, *.canvas.json) and journey docs are left to `finish`.

Severity:
  validator exit 0  -> exit 0, silent
  validator exit 3  -> exit 0, the UNVERIFIED list goes back to Claude as
                       additionalContext (PostToolUse plain stdout is not shown
                       to Claude, only JSON hookSpecificOutput is)
  validator exit 1  -> exit 2, FAIL lines on stderr (Claude sees them; the
                       write already happened, so this is feedback, not a block)
  anything else, any exception, timeout -> exit 0 with a one-line stderr note.
No network; one subprocess; typically well under 2 s.
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.path.dirname(HERE)
VALIDATOR = os.path.join(ROOT, "scripts", "validate_output.py")
MAX_FAIL_LINES = 15
INSTRUCTION = ("[lifecycle-journey-builder] validate_output.py found violations in {path}. "
               "Fix these before continuing; compliance violations (discount cap, "
               "unconsented channel, frequency cap) are reported to the user, not silently fixed.")


def in_output_tree(parts):
    if "output" in parts:
        return True
    return any(parts[i] == "evals" and parts[i + 1] == "out" for i in range(len(parts) - 1))


def output_root(path):
    """Nearest ancestor directory named `output` (where output/brands/ lives)."""
    d = os.path.dirname(path)
    while True:
        if os.path.basename(d) == "output":
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def brand_flags(copy_path):
    """--sector / --max-discount from the brand config the sibling portfolio names.
    Missing pieces are simply left out: the validator then warns, or falls back to
    the journey's own constraints.max_discount_pct."""
    flags = []
    copy_dir = os.path.dirname(copy_path)
    portfolio = None
    for cand in (os.path.join(copy_dir, "..", "portfolio.json"), os.path.join(copy_dir, "portfolio.json")):
        if os.path.isfile(cand):
            portfolio = cand
            break
    if not portfolio:
        return flags
    try:
        brand = (json.load(open(portfolio, encoding="utf-8")) or {}).get("brand")
    except (OSError, ValueError, AttributeError):
        return flags
    root = output_root(copy_path)
    if not brand or not root or not re.fullmatch(r"[\w.-]+", str(brand)):
        return flags
    bfile = os.path.join(root, "brands", f"{brand}.md")
    try:
        text = open(bfile, encoding="utf-8").read()
    except OSError:
        return flags
    fm = text.split("---", 2)[1] if text.startswith("---") and text.count("---") >= 2 else text
    m = re.search(r"^industry:\s*([a-z0-9-]+)", fm, re.M)
    if m and os.path.isfile(os.path.join(ROOT, "knowledge", "lexicons", f"{m.group(1)}.md")):
        flags += ["--sector", m.group(1)]
    m = re.search(r"^\s*max_discount_pct:\s*([0-9]+(?:\.[0-9]+)?)", fm, re.M)
    if m:
        flags += ["--max-discount", m.group(1)]
    return flags


def pick_mode(path):
    """(mode, extra_args) or None when the file is out of scope."""
    parts = path.replace("\\", "/").split("/")
    if not in_output_tree(parts):
        return None
    name = parts[-1]
    if name == "portfolio.json":
        return "portfolio", []
    if name == "dossier.md":
        return "dossier", []
    if name.endswith(".md") and len(parts) >= 2 and parts[-2] == "_copy":
        return "copy", brand_flags(path)
    if name.endswith(".json") and ".canvas." not in name:
        try:
            data = json.load(open(path, encoding="utf-8"))
        except (OSError, ValueError):
            return None  # unreadable or half-written JSON: leave it to finish
        if isinstance(data, dict) and ("nodes" in data or "steps" in data):
            return "journey", ["--quiet"]
    return None


def main():
    raw = sys.stdin.read()
    try:
        event = json.loads(raw) if raw.strip() else {}
    except ValueError:
        return 0
    if not isinstance(event, dict):
        return 0
    fp = (event.get("tool_input") or {}).get("file_path") if isinstance(event.get("tool_input"), dict) else None
    if not fp or not isinstance(fp, str):
        return 0
    if not os.path.isabs(fp):
        fp = os.path.join(event.get("cwd") or os.getcwd(), fp)
    fp = os.path.normpath(fp)
    if not os.path.isfile(fp):
        return 0
    picked = pick_mode(fp)
    if not picked or not os.path.isfile(VALIDATOR):
        return 0
    mode, extra = picked
    try:
        res = subprocess.run([sys.executable, VALIDATOR, mode, fp] + extra,
                             capture_output=True, text=True, timeout=20)
    except subprocess.TimeoutExpired:
        print(f"[lifecycle-journey-builder] validate_on_write: validator timed out on {fp}; finish will re-check it",
              file=sys.stderr)
        return 0
    out = res.stdout.splitlines()
    if res.returncode == 1:
        fails = [l.strip() for l in out if re.match(r"\s*FAIL\b", l)]
        if not fails:  # fall back to the numbered TO FIX block
            try:
                i = next(k for k, l in enumerate(out) if l.startswith("TO FIX"))
                fails = [l.strip() for l in out[i + 1:] if re.match(r"\s+\d+\.", l)]
            except StopIteration:
                fails = [l for l in out if l.strip()][-5:]
        shown = fails[:MAX_FAIL_LINES]
        msg = [INSTRUCTION.format(path=fp)] + shown
        if len(fails) > len(shown):
            msg.append(f"... {len(fails) - len(shown)} more: run validate_output.py {mode} on the file for the full list")
        print("\n".join(msg), file=sys.stderr)
        return 2
    if res.returncode == 3:
        try:
            i = next(k for k, l in enumerate(out) if l.startswith("UNVERIFIED"))
            items = [l.strip() for l in out[i:] if l.strip()][:MAX_FAIL_LINES + 1]
        except StopIteration:
            items = [l for l in out if l.strip()][-5:]
        ctx = (f"[lifecycle-journey-builder] {fp} has no violations but is NOT verified (validator exit 3). "
               "Present it only together with this list, labelled unverified:\n" + "\n".join(items))
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": ctx}}))
        return 0
    if res.returncode != 0:
        print(f"[lifecycle-journey-builder] validate_on_write: validator exited {res.returncode} on {fp}; not blocking",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001  a hook must never break the session
        print(f"[lifecycle-journey-builder] validate_on_write skipped: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(0)

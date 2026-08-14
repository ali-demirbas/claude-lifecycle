#!/usr/bin/env python3
"""Eval checker: verifies a case run's artifacts against expected.yaml.

Usage:
  eval_check.py evals/cases/<case-id>     one case (expects evals/out/<case-id>/)
  eval_check.py evals/cases               whole suite
Exit: 0 all assertions pass · 1 failures · 2 usage/missing run output.

Parses a deliberate SUBSET of YAML (maps, lists, scalars, one nesting level of
the contract in evals/README.md) so no third-party dependency is needed.
"""
import glob
import json
import os
import re
import subprocess
import sys

from _validate_common import tr_fold

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, ".."))


# ---------------------------------------------------------------- tiny yaml
def parse_yaml(text):
    """Parse the expected.yaml contract subset: nested dicts, lists, scalars."""
    root, stack = {}, [(-1, None, {})]  # (indent, key, container) ; root at bottom
    stack[0] = (-1, None, root)
    for raw in text.splitlines():
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        line = raw.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][2]
        if line.startswith("- "):
            item = line[2:].strip()
            if not isinstance(parent, list):
                # convert: last key of grandparent becomes list
                gp = stack[-2][2] if len(stack) > 1 else root
                key = stack[-1][1]
                parent = gp[key] = []
                stack[-1] = (stack[-1][0], key, parent)
            if ":" in item and not item.startswith(("'", '"')) and " " not in item.split(":", 1)[0]:
                k, v = item.split(":", 1)
                d = {k.strip(): scalar(v)}
                parent.append(d)
                # continuation keys sit at indent+2; push indent+1 so they don't pop this frame
                stack.append((indent + 1, None, d))
            else:
                parent.append(scalar(item))
        elif ":" in line:
            k, v = line.split(":", 1)
            k, v = k.strip(), v.strip()
            if v == "":
                child = {}
                parent[k] = child
                stack.append((indent, k, child))
            elif v.startswith("[") and v.endswith("]"):
                parent[k] = [scalar(x) for x in split_list(v[1:-1])]
            elif v.startswith("{") and v.endswith("}"):
                d = {}
                for pair in split_list(v[1:-1]):
                    pk, pv = pair.split(":", 1)
                    d[pk.strip().strip('"').strip("'")] = scalar(pv)
                parent[k] = d
            else:
                parent[k] = scalar(v)
    return root


def split_list(s):
    out, cur, depth = [], "", 0
    for ch in s:
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            if ch in "[{":
                depth += 1
            if ch in "]}":
                depth -= 1
            cur += ch
    if cur.strip():
        out.append(cur)
    return out


def scalar(v):
    v = v.strip().strip('"').strip("'")
    if v.lower() in ("true", "false"):
        return v.lower() == "true"
    try:
        return int(v)
    except ValueError:
        return v


# ---------------------------------------------------------------- checking
def read_all_text(out_dir, pattern="*"):
    chunks = {}
    for p in glob.glob(os.path.join(out_dir, "**", pattern), recursive=True):
        if os.path.isfile(p):
            try:
                chunks[p] = open(p, encoding="utf-8").read()
            except UnicodeDecodeError as e:
                # Don't silently drop the file from the assertion blob — a
                # required/forbidden-phrase check on this file would then
                # pass or fail on missing evidence instead of real content.
                # Re-read tolerantly so the file's mostly-good text still
                # gets checked, and surface the encoding problem.
                print(f"  warn: {p}: {e} — re-read with errors='replace'")
                chunks[p] = open(p, encoding="utf-8", errors="replace").read()
    return chunks


def check_case(case_dir, out_root=None):
    case_id = os.path.basename(os.path.normpath(case_dir))
    exp_path = os.path.join(case_dir, "expected.yaml")
    out_dir = os.path.join(out_root or os.path.join(REPO, "evals", "out"), case_id)
    print(f"\n=== case: {case_id}")
    if not os.path.exists(exp_path):
        print(f"FAIL: no expected.yaml in {case_dir}")
        return ["missing expected.yaml"]
    exp = parse_yaml(open(exp_path, encoding="utf-8").read())
    a = exp.get("assertions", {})
    refs = exp.get("rule_refs", [])
    fails = []

    def fail(msg):
        fails.append(msg)
        print(f"FAIL: {msg}  [rules: {', '.join(map(str, refs))}]")

    if not a:
        fail("expected.yaml has no assertions")
        return fails
    if not os.path.isdir(out_dir):
        print(f"SKIP: no run output at evals/out/{case_id} — run the case first")
        return ["not run"]

    # portfolio-based assertions
    pf_path = os.path.join(out_dir, "portfolio.json")
    pf = None
    if os.path.exists(pf_path):
        try:
            pf = json.load(open(pf_path, encoding="utf-8"))
        except json.JSONDecodeError as e:
            fail(f"portfolio.json invalid: {e}")
    needs_pf = any(k in a for k in ("must_generate", "must_not_generate", "must_block",
                                    "suppressed_accounts_include"))
    if needs_pf and pf is None:
        fail("portfolio.json missing but portfolio assertions present")
    if pf is not None:
        generated = {j.get("pattern") for j in pf.get("journeys", [])}
        for p in a.get("must_generate", []):
            if p not in generated:
                fail(f"pattern '{p}' expected in portfolio, not generated")
        for p in a.get("must_not_generate", []):
            if p in generated:
                fail(f"pattern '{p}' must NOT be generated, but it was")
        blocked = pf.get("blocked", [])
        for want in a.get("must_block", []):
            hit = [b for b in blocked if b.get("pattern") == want.get("pattern")]
            if not hit:
                fail(f"pattern '{want.get('pattern')}' expected in blocked list")
            elif want.get("reason_contains") and not any(
                str(want["reason_contains"]).lower() in str(b.get("reason", "")).lower() for b in hit
            ):
                fail(f"blocked '{want['pattern']}' reason must contain '{want['reason_contains']}'")
        sup = [str(s) for s in pf.get("suppressed_accounts", [])]
        for acc in a.get("suppressed_accounts_include", []):
            if str(acc) not in sup:
                fail(f"account '{acc}' expected in portfolio.suppressed_accounts")

    # journey-JSON step counts + audience exclusion
    journeys = []
    for p in glob.glob(os.path.join(out_dir, "*.json")):
        if os.path.basename(p) == "portfolio.json":
            continue
        try:
            d = json.load(open(p, encoding="utf-8"))
            if isinstance(d, dict) and "steps" in d:
                journeys.append((p, d))
        except json.JSONDecodeError:
            pass
    steps_by_pattern = {}
    for _p, d in journeys:
        steps_by_pattern.setdefault(d.get("pattern"), []).append(len(d.get("steps", [])))
    for pat, n in (a.get("min_steps") or {}).items():
        counts = steps_by_pattern.get(pat)
        if not counts:
            fail(f"min_steps: no journey JSON for pattern '{pat}'")
        elif max(counts) < n:
            fail(f"min_steps: '{pat}' has {max(counts)} steps, expected ≥ {n}")
    for pat, n in (a.get("max_steps") or {}).items():
        if pat == "any":
            for p2, counts in steps_by_pattern.items():
                if max(counts) > n:
                    fail(f"max_steps(any): '{p2}' has {max(counts)} steps, expected ≤ {n}")
        elif pat in steps_by_pattern and max(steps_by_pattern[pat]) > n:
            fail(f"max_steps: '{pat}' has {max(steps_by_pattern[pat])} steps, expected ≤ {n}")
    for acc in a.get("audience_must_exclude", []):
        for p, d in journeys:
            inc = json.dumps(d.get("audience", {}).get("include", ""), ensure_ascii=False)
            if str(acc) in inc:
                fail(f"account '{acc}' appears in audience.include of {os.path.basename(p)}")

    # greps
    texts = read_all_text(out_dir)
    blob = tr_fold("\n".join(texts.values()))
    for s in a.get("required_anywhere", []):
        if tr_fold(str(s)) not in blob:
            fail(f"required string not found anywhere: '{s}'")
    for s in a.get("forbidden_anywhere", []):
        if tr_fold(str(s)) in blob:
            fail(f"forbidden string found in output: '{s}'")

    # copy assertions
    c = a.get("copy") or {}
    if c:
        # Detect by structure (the "## Step" marker every copy doc has),
        # not by filename — TR output is named iletisim-metinleri(-kaynak).md
        # and never matches a "copy" substring, unlike EN copy-output.md.
        copy_files = [p for p in texts if p.endswith(".md") and re.search(r"^## Step\b", texts[p], re.M)]
        if not copy_files:
            fail("copy assertions present but no copy *.md in run output")
        cblob = tr_fold("\n".join(texts[p] for p in copy_files))
        for s in c.get("forbidden", []):
            if tr_fold(str(s)) in cblob:
                fail(f"forbidden string in copy: '{s}'")
        for s in c.get("required", []):
            if tr_fold(str(s)) not in cblob:
                fail(f"required string missing from copy: '{s}'")
        if c.get("must_pass_validator") and copy_files:
            cmd = [sys.executable, os.path.join(HERE, "validate_output.py"), "copy", *copy_files]
            if "max_discount" in c:
                cmd += ["--max-discount", str(c["max_discount"])]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                fail("copy failed validate_output.py:\n    " +
                     "\n    ".join(l for l in r.stdout.splitlines() if l.startswith("FAIL"))[:600])

    if not fails:
        print("PASS")
    return fails


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    out_root = None
    if "--out-root" in argv:
        i = argv.index("--out-root")
        out_root = argv[i + 1]
        argv = argv[:i] + argv[i + 2 :]
    target = argv[0]
    if os.path.exists(os.path.join(target, "expected.yaml")):
        cases = [target]
    else:
        cases = sorted(
            d for d in glob.glob(os.path.join(target, "*")) if os.path.isdir(d)
            and os.path.exists(os.path.join(d, "expected.yaml"))
        )
    if not cases:
        print(f"no cases found under {target}")
        return 2
    total_fail, not_run = 0, 0
    for cdir in cases:
        fs = check_case(cdir, out_root)
        if fs == ["not run"]:
            not_run += 1
        else:
            total_fail += len(fs)
    print(f"\n==== {len(cases)} case(s): {len(cases)-not_run} evaluated, {not_run} not run, "
          f"{total_fail} failed assertion(s)")
    return 1 if total_fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

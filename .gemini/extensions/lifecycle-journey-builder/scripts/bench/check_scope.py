#!/usr/bin/env python3
"""Check that a benchmark run produced exactly the scope it was fixed to, before its cost is compared.

  check_scope.py <run output dir> --scope S1|S2 [--json]

S1 (A1, A2: same-scope code comparison) — portfolio review, one journey built:
  - exactly one journey built: ecom-abandoned-cart-01 (JSON + doc)
  - every ecommerce P0 and P1 pattern is reviewed: its slug appears in the
    registry, the portfolio doc or the dossier with a decision
  - portfolio registry present and NOT single-scope; a run manifest, if any,
    is not single-mode (this is what catches A2 slipping into the fast path)
  - dossier, data assessment and canvas present; no copy output
S2 (B: the single-journey path) — same journey and deliverables, but:
  - registry scope "single", and the dossier/portfolio doc states that
    portfolio coverage was not reviewed
Both: the delivered journey and registry are re-validated here with the
current validator, so the same safety checks (consent, frequency, exits,
timing, measurement) are applied to every run's output, whatever code made it.
Exit 0 in scope · 1 out of scope (don't compare this run) · 2 usage error.
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
JOURNEY = "ecom-abandoned-cart-01"
NOT_JOURNEYS = {"portfolio.json", "run-manifest.json", "_meta.json", "stage-map.json"}


def p0_p1(sector="ecommerce"):
    text = open(os.path.join(ROOT, "knowledge", "industries", f"{sector}.md"), encoding="utf-8").read()
    return [m for m, p in re.findall(r"^  ([a-z0-9-]+): (P[0-2])$", text.split("---")[1], re.M) if p in ("P0", "P1")]


def read(path):
    return open(path, encoding="utf-8").read() if os.path.isfile(path) else ""


def journeys_built(d):
    out = []
    for p in sorted(glob.glob(os.path.join(d, "*.json"))):
        if os.path.basename(p) in NOT_JOURNEYS:
            continue
        try:
            doc = json.load(open(p, encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(doc, dict) and ("nodes" in doc or "steps" in doc):
            out.append(doc.get("id") or os.path.basename(p)[:-5])
    return out


def validator(*args):
    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "validate_output.py"), *args],
                       capture_output=True, text=True)
    return r.returncode, next((ln for ln in r.stdout.splitlines() if ln.startswith("validator ")), "")


def check(d, scope):
    problems, info = [], {}
    built = journeys_built(d)
    info["journeys_built"] = built
    if built != [JOURNEY]:
        problems.append(f"journeys built {built}, expected exactly [{JOURNEY}]")
    for f in (f"{JOURNEY}.md", "portfolio.json", "dossier.md", "canvas.html"):
        if not os.path.isfile(os.path.join(d, f)):
            problems.append(f"missing {f}")
    if not glob.glob(os.path.join(d, "data-assessment*.md")):
        problems.append("missing data assessment")
    copy_out = [p for p in glob.glob(os.path.join(d, "**", "*"), recursive=True)
                if re.search(r"(^|/)_copy/|iletisim-metinleri|copy-canvas|[-_]copy\.md$", p)]
    if copy_out:
        problems.append(f"copy output present (out of scope): {copy_out[:3]}")
    reg = {}
    try:
        reg = json.load(open(os.path.join(d, "portfolio.json"), encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        pass
    manifest = {}
    try:
        manifest = json.load(open(os.path.join(d, "run-manifest.json"), encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        pass
    reg_scope = reg.get("scope")
    man_mode = (manifest.get("scope") or {}).get("mode") if isinstance(manifest.get("scope"), dict) else None
    info.update({"registry_scope": reg_scope, "manifest_mode": man_mode})
    text = json.dumps(reg, ensure_ascii=False) + read(os.path.join(d, "portfolio.md")) + read(os.path.join(d, "dossier.md"))
    if scope == "S1":
        if reg_scope == "single" or man_mode == "single":
            problems.append("run took the single-journey path: not comparable with A1 (S1 needs the portfolio review)")
        missing = [p for p in p0_p1() if p not in text]
        info["patterns_reviewed"] = len(p0_p1()) - len(missing)
        if missing:
            problems.append(f"P0/P1 patterns not reviewed: {missing}")
    else:
        if reg_scope != "single":
            problems.append(f"registry scope is {reg_scope!r}, expected 'single'")
        if not re.search(r"not reviewed|incelenmedi|değerlendirilmedi|gözden geçirilmedi", text, re.I):
            problems.append("no statement that portfolio coverage was not reviewed")
    jp = os.path.join(d, f"{JOURNEY}.json")
    if os.path.isfile(jp):
        info["journey_validator"] = validator("journey", jp)
        if info["journey_validator"][0] not in (0, 3):
            problems.append(f"journey fails the current validator: {info['journey_validator'][1]}")
    if reg:
        info["portfolio_validator"] = validator("portfolio", os.path.join(d, "portfolio.json"))
        if info["portfolio_validator"][0] not in (0, 3):
            problems.append(f"registry fails the current validator: {info['portfolio_validator'][1]}")
    return problems, info


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("outdir")
    ap.add_argument("--scope", choices=["S1", "S2"], required=True)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if not os.path.isdir(a.outdir):
        print(f"error: {a.outdir} not found", file=sys.stderr)
        return 2
    problems, info = check(a.outdir, a.scope)
    if a.json:
        print(json.dumps({"scope": a.scope, "in_scope": not problems, "problems": problems, **info},
                         ensure_ascii=False, indent=1))
    else:
        print(f"{a.scope}: {'IN SCOPE' if not problems else 'OUT OF SCOPE'} · {info}")
        for p in problems:
            print(f"  - {p}")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

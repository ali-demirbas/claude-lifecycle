#!/usr/bin/env python3
"""Headless eval runner: executes eval cases end to end through the real plugin.

Each case is run by a fresh, non-interactive Claude Code process with this repo
loaded as a plugin (`claude -p --plugin-dir <repo>`), entering through the
`/claude-lifecycle:lifecycle` router exactly as a user would after installing.
The run writes its artifacts to evals/out/<case-id>/, then eval_check.py grades
them. So one command is both the E2E install test and the eval generation step
that used to be done by hand.

Usage:
  run_evals.py <case-id> [<case-id> ...]   run specific cases (id or prefix, e.g. 36)
  run_evals.py --all                       run every case in evals/cases/
  options:
    --budget USD      per-case spend ceiling passed to claude (default 5)
    --parallel N      cases run concurrently (default 2)
    --model NAME      model override for the runs
    --dry-run         print the command and prompt, run nothing

Requires the `claude` CLI on PATH and an authenticated session. Costs real
usage: this is a pre-release / after-knowledge-change tool, not a per-PR CI
gate (the deterministic tests in scripts/tests/ remain that gate).

Run metadata (cost, turns, duration, pass/fail) is appended to
evals/out/_runs.jsonl so score and cost can be compared across releases.
"""
import argparse
import concurrent.futures as cf
import datetime as dt
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, ".."))
CASES = os.path.join(REPO, "evals", "cases")
OUT = os.path.join(REPO, "evals", "out")

ALLOWED_TOOLS = [
    "Read", "Write", "Edit", "Glob", "Grep", "Agent", "Skill",
    "Bash(python3 *)", "Bash(ls *)", "Bash(mkdir *)", "Bash(cat *)", "Bash(wc *)",
]


def read_expected(case_dir):
    """Only the two fields the runner needs; eval_check.py owns full parsing."""
    fields, top = {}, None
    for line in open(os.path.join(case_dir, "expected.yaml"), encoding="utf-8"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, _, val = line.strip().partition(":")
        if not line.startswith((" ", "\t")):
            top = key
            fields[key] = val.strip()
        elif top == "run" and key == "copy":
            fields["run.copy"] = val.strip()
    return fields.get("run.copy", "").lower() == "true", fields.get("sector", ""), fields.get("tier", "")


def build_prompt(case_id, case_dir, out_dir):
    copy, sector, tier = read_expected(case_dir)
    inputs = sorted(f for f in os.listdir(case_dir) if f not in ("expected.yaml", "intake.md"))
    rel = lambda p: os.path.relpath(p, REPO)  # noqa: E731
    stages = "connect → map → intake → journeys" + (" → copy" if copy else "")
    input_line = (", ".join(rel(os.path.join(case_dir, f)) for f in inputs)
                  if inputs else "none (this is a Tier 3, industry-only case)")
    return f"""/claude-lifecycle:lifecycle

This is a non-interactive evaluation run (eval case `{case_id}`). No human is watching, so never stop to ask a question.

- Data input: {input_line}
- Sector: {sector or "see intake"} · tier: {tier or "detect from input"}
- The user's answers to every intake question are in `{rel(os.path.join(case_dir, "intake.md"))}`. Treat that file as the user speaking. Where a gate would normally ask something the file doesn't answer, take the documented default, and record what you assumed in the dossier.
- Breadth gate: build everything eligible (option C), so every assertion in the case can be checked.
- Run the full pipeline: {stages}. Follow every skill's rules exactly as in a normal run, including the validation gates.
- Write ALL artifacts to `{rel(out_dir)}/` (not output/): the data assessment, portfolio.json, every journey JSON + doc, the tracking plan if anything is blocked, {"the copy docs, " if copy else ""}and dossier.md.
- Skip the HTML canvases; this run is graded on the markdown/JSON artifacts only.
"""


def run_case(case_id, args):
    case_dir = os.path.join(CASES, case_id)
    out_dir = os.path.join(OUT, case_id)
    prompt = build_prompt(case_id, case_dir, out_dir)
    cmd = ["claude", "-p", prompt, "--plugin-dir", REPO, "--output-format", "json",
           "--max-budget-usd", str(args.budget), "--permission-mode", "acceptEdits",
           "--no-session-persistence", "--allowedTools", *ALLOWED_TOOLS]
    if args.model:
        cmd += ["--model", args.model]
    if args.dry_run:
        return {"case": case_id, "dry_run": True, "cmd": cmd[:2] + ["<prompt>"] + cmd[3:], "prompt": prompt}

    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)  # a stale earlier run must not grade as this one
    os.makedirs(out_dir, exist_ok=True)
    started = dt.datetime.now()
    proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    elapsed = (dt.datetime.now() - started).total_seconds()
    meta = {}
    try:
        meta = json.loads(proc.stdout)
    except json.JSONDecodeError:
        meta = {"is_error": True, "result": (proc.stdout or proc.stderr)[-2000:]}

    check = subprocess.run([sys.executable, os.path.join(HERE, "eval_check.py"), case_dir],
                           cwd=REPO, capture_output=True, text=True)
    return {
        "case": case_id,
        "passed": check.returncode == 0,
        "check_exit": check.returncode,
        "check_tail": check.stdout[-1500:],
        "run_error": bool(meta.get("is_error")) or proc.returncode != 0,
        "cost_usd": meta.get("total_cost_usd"),
        "turns": meta.get("num_turns"),
        "seconds": round(elapsed),
        "result_tail": str(meta.get("result", ""))[-600:],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cases", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--budget", type=float, default=5.0)
    ap.add_argument("--parallel", type=int, default=2)
    ap.add_argument("--model")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    available = sorted(d for d in os.listdir(CASES) if os.path.isdir(os.path.join(CASES, d)))
    if args.all:
        chosen = available
    else:
        chosen = []
        for c in args.cases:
            hits = [a for a in available if a == c or a.startswith(c + "-") or a.startswith(c)]
            if len(hits) != 1:
                print(f"case '{c}' matched {len(hits)} cases: {hits}")
                return 2
            chosen.append(hits[0])
    if not chosen:
        print(__doc__)
        return 2
    if not args.dry_run and not shutil.which("claude"):
        print("the `claude` CLI is not on PATH")
        return 2

    results = []
    with cf.ThreadPoolExecutor(max_workers=max(1, args.parallel)) as ex:
        for r in ex.map(lambda c: run_case(c, args), chosen):
            results.append(r)
            if r.get("dry_run"):
                print(" ".join(r["cmd"][:3]), "...\n" + r["prompt"])
                continue
            flag = "PASS" if r["passed"] else "FAIL"
            print(f"{flag}  {r['case']}  ${r['cost_usd'] or '?'}  {r['turns'] or '?'} turns  {r['seconds']}s"
                  + ("  (run error)" if r["run_error"] else ""))
            if not r["passed"]:
                print("      " + r["check_tail"].strip().replace("\n", "\n      "))

    if args.dry_run:
        return 0
    os.makedirs(OUT, exist_ok=True)
    stamp = dt.datetime.now().isoformat(timespec="seconds")
    with open(os.path.join(OUT, "_runs.jsonl"), "a", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps({"at": stamp, **{k: v for k, v in r.items() if k != "check_tail"}}) + "\n")
    passed = sum(r["passed"] for r in results)
    cost = sum(r["cost_usd"] or 0 for r in results)
    print(f"\n{passed}/{len(results)} cases passed · total ${cost:.2f}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())

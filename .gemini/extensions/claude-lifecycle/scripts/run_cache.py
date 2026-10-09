#!/usr/bin/env python3
"""Reuse a previous run's data assessment and stage map when nothing they depend on changed.

The key covers everything the assessment is computed from: the input file(s),
the code that profiles and maps them, the event taxonomy and mapping rules, the
DQS rubric, every pattern file and the journey schema, the sector playbook and
lexicon, and the brand config. Any change → a miss → assess fresh.

A hit is reported as a cached assessment from a named earlier run, never as a
freshly validated one. Facts that change outside the input file are never
cached and must be checked again on every run: current consent state, active
campaigns and existing journeys, and whether the data feed is still current.

  lookup <cache_dir> --input F [F ...] --sector S [--brand B]
      exit 0 + JSON (hit) · exit 1 + JSON with the key (miss)
  store  <cache_dir> --input F [F ...] --sector S [--brand B] --run-id R --files A [B ...]
"""
import argparse
import datetime as dt
import glob
import hashlib
import json
import os
import shutil
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
NOT_CACHED = ["current consent / opt-out state per channel", "active campaigns and existing journeys (their load)",
              "data feed freshness since the cached run"]


def _hash_files(paths):
    h = hashlib.sha256()
    for p in sorted(paths):
        h.update(os.path.relpath(p, ROOT).encode() if p.startswith(ROOT) else os.path.basename(p).encode())
        with open(p, "rb") as f:
            h.update(hashlib.sha256(f.read()).digest())
    return h.hexdigest()


def components(inputs, sector, brand):
    g = lambda pat: sorted(glob.glob(os.path.join(ROOT, pat)))  # noqa: E731
    comps = {
        "input": [os.path.abspath(i) for i in inputs],
        "analysis_code": [os.path.join(ROOT, "scripts", n) for n in
                          ("validate_input.py", "eligibility.py", "_validate_common.py")],
        "mapping_rules": g("knowledge/event-taxonomy/*.md"),
        "dqs_rubric": [os.path.join(ROOT, "docs", "data-quality-score.md")],
        "patterns_and_schema": g("knowledge/journey-patterns/*.md") + [os.path.join(ROOT, "templates", "journey.schema.json")],
        "sector": [p for p in (os.path.join(ROOT, "knowledge", "industries", f"{sector}.md"),
                               os.path.join(ROOT, "knowledge", "lexicons", f"{sector}.md")) if os.path.isfile(p)],
        "brand": [p for p in [os.path.join(ROOT, "knowledge", "brands", f"{brand}.md")] if brand and os.path.isfile(p)],
    }
    missing = [i for i in comps["input"] if not os.path.isfile(i)]
    if missing:
        raise FileNotFoundError(f"input not found: {missing}")
    return comps


def key_for(inputs, sector, brand):
    comps = components(inputs, sector, brand)
    parts = {k: _hash_files(v) if v else "none" for k, v in comps.items()}
    whole = hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest()[:24]
    return whole, parts


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["lookup", "store"])
    ap.add_argument("cache_dir")
    ap.add_argument("--input", nargs="+", required=True)
    ap.add_argument("--sector", required=True)
    ap.add_argument("--brand")
    ap.add_argument("--run-id")
    ap.add_argument("--files", nargs="+")
    a = ap.parse_args(argv)
    try:
        key, parts = key_for(a.input, a.sector, a.brand)
    except FileNotFoundError as e:
        print(json.dumps({"error": str(e)}))
        return 2
    entry = os.path.join(a.cache_dir, key)
    if a.cmd == "lookup":
        meta_p = os.path.join(entry, "meta.json")
        if not os.path.isfile(meta_p):
            print(json.dumps({"hit": False, "key": key}))
            return 1
        meta = json.load(open(meta_p, encoding="utf-8"))
        files = {f: os.path.join(entry, f) for f in meta["files"] if os.path.isfile(os.path.join(entry, f))}
        if len(files) != len(meta["files"]):
            print(json.dumps({"hit": False, "key": key, "reason": "cache entry incomplete"}))
            return 1
        print(json.dumps({"hit": True, "key": key, "from_run": meta.get("run_id"), "created": meta.get("created"),
                          "files": files, "label": f"cached assessment from run {meta.get('run_id')} "
                          f"({meta.get('created')}); inputs, code, rules and patterns unchanged",
                          "must_recheck": NOT_CACHED}, ensure_ascii=False, indent=1))
        return 0
    if not a.files or not a.run_id:
        print("store needs --run-id and --files", file=sys.stderr)
        return 2
    os.makedirs(entry, exist_ok=True)
    names = []
    for f in a.files:
        shutil.copy2(f, os.path.join(entry, os.path.basename(f)))
        names.append(os.path.basename(f))
    json.dump({"run_id": a.run_id, "created": dt.datetime.now().isoformat(timespec="seconds"), "files": names,
               "components": parts, "not_cached": NOT_CACHED}, open(os.path.join(entry, "meta.json"), "w"), indent=1)
    print(json.dumps({"stored": True, "key": key, "files": names}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

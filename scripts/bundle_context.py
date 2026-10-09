#!/usr/bin/env python3
"""Write the context bundle one journey-architect needs, as a single file.

The orchestrator used to paste ~10k tokens of shared rules into every agent
prompt (paid as orchestrator output, then carried in its context for the rest
of the run), or the instruction was skipped and every agent re-read the same
files one tool call at a time. This script assembles exactly the files one
journey needs, with no model tokens; the agent reads one file.

Only what the task needs: the journey's own pattern, the sector playbook and
lexicon, the brand config if there is one, the consent/frequency rules,
segmentation and measurement guidance, the doc template and the schema.
Never the whole knowledge base.

Usage:
  bundle_context.py --pattern winback --sector ecommerce [--brand acme] --out output/<project>/_bundle/<id>.md
"""
import argparse
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def parts(pattern, sector, brand):
    out = [
        ("Pattern", f"knowledge/journey-patterns/{pattern}.md"),
        ("Sector playbook", f"knowledge/industries/{sector}.md"),
        ("Sector lexicon", f"knowledge/lexicons/{sector}.md"),
    ]
    if brand:
        out.append(("Brand config", f"knowledge/brands/{brand}.md"))
    out += [
        ("Consent, frequency, quiet hours", "knowledge/compliance/consent-and-quiet-hours.md"),
        ("Segmentation", "knowledge/segmentation.md"),
        ("Measurement", "knowledge/measurement.md"),
        ("Journey doc template", "templates/journey-doc.md"),
        ("Journey JSON schema 2.0", "templates/journey.schema.json"),
    ]
    return out


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pattern", required=True)
    ap.add_argument("--sector", required=True)
    ap.add_argument("--brand")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    chunks, missing = [], []
    for title, rel in parts(a.pattern, a.sector, a.brand):
        p = os.path.join(ROOT, rel)
        if not os.path.isfile(p):
            missing.append(rel)
            continue
        body = open(p, encoding="utf-8").read().rstrip()
        fence = "```json" if rel.endswith(".json") else ""
        chunks.append(f"# {title} — `{rel}`\n\n" + (f"{fence}\n{body}\n```" if fence else body))
    required_missing = [m for m in missing if "brands/" not in m]
    if required_missing:
        print(f"error: missing {required_missing}", file=sys.stderr)
        return 1
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    text = "\n\n---\n\n".join(chunks) + "\n"
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"ok: {a.out} ({len(text) // 4} tokens approx, {len(chunks)} files)"
          + (f"; no brand config: {missing}" if missing else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

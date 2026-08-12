#!/usr/bin/env python3
"""Concatenate the repo's core documents into docs/llms-full.txt.

Why generated rather than hand-written: a full-text bundle is only useful while
it matches the documents it bundles, and a hand-maintained copy silently rots
the first time README or CLAUDE.md changes. Generating it lets `validate.sh`
diff the committed file against a fresh build and fail when they diverge — the
same self-verification discipline build_canvas.py applies to the canvas.

Why the file exists at all: when someone hands a repo URL to a chat assistant,
the assistant fetches HTML and spends most of its budget on markup. One
Markdown bundle is the cheapest complete answer to "what is this project".
`docs/llms.txt` is the index; this is the whole thing.

Usage:
  build_llms_full.py                 # write docs/llms-full.txt
  build_llms_full.py --check         # exit 1 if the committed file is stale
"""
import argparse
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "docs", "llms-full.txt")

# Order matters: what the project is, the rules that constrain it, how it is
# assembled, then the one number the whole engine is derived from.
SOURCES = [
    ("README.md", "Overview"),
    ("CLAUDE.md", "Binding rules"),
    ("docs/architecture.md", "Architecture"),
    ("docs/data-quality-score.md", "Data Quality Score"),
    ("docs/adding-an-industry.md", "Adding an industry"),
    ("docs/real-world-validation.md", "Real-world validation"),
]

HEADER = """# claude-lifecycle — full text

> Single-file bundle of this project's core documentation, generated from the
> repository by scripts/build_llms_full.py. A lifecycle marketing and CRM
> engine for Claude Code: it scores what your analytics data supports (a 0-100
> Data Quality Score), then generates a portfolio of customer journeys sized to
> that reality — onboarding, retention, churn prevention, win-back — with
> channel-rule-checked copy and a tracking plan for what the data cannot yet
> support.
>
> Source: https://github.com/ali-demirbas/claude-lifecycle (MIT)

"""


def build():
    parts = [HEADER]
    for rel, label in SOURCES:
        path = os.path.join(REPO, rel)
        if not os.path.isfile(path):
            sys.stderr.write("build_llms_full: skipping missing %s\n" % rel)
            continue
        with open(path, encoding="utf-8") as fh:
            body = fh.read().strip()
        parts.append("\n\n---\n\n# %s — %s\n\n%s\n" % (label, rel, body))
    return "".join(parts)


def main(argv):
    ap = argparse.ArgumentParser(description="Build docs/llms-full.txt from the core docs.")
    ap.add_argument("--check", action="store_true",
                    help="do not write; exit 1 if the committed file is out of date")
    args = ap.parse_args(argv)

    built = build()

    if args.check:
        if not os.path.isfile(OUT):
            print("docs/llms-full.txt is missing — run scripts/build_llms_full.py")
            return 1
        with open(OUT, encoding="utf-8") as fh:
            current = fh.read()
        if current != built:
            print("docs/llms-full.txt is stale — run scripts/build_llms_full.py")
            return 1
        print("  ok: docs/llms-full.txt matches its sources")
        return 0

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(built)
    print("wrote %s (%d bytes from %d sources)" % (OUT, len(built.encode("utf-8")), len(SOURCES)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

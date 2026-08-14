#!/usr/bin/env python3
"""Derive search phrases that would identify a copy of this repo's content.

The problem this addresses: the archive is MIT-licensed, which permits reuse
and requires the copyright notice be kept. Someone stripping the notice is in
breach — but a breach nobody detects is not a deterrent. Provenance in the
generated cards handles attribution; this handles *detection*.

Why phrases are computed rather than stored: a canary list committed to a
public repo is a list of exactly what to scrub. Nothing here is embedded or
hidden — these are phrases the content already contains, selected for being
statistically distinctive enough that a web search for them in quotes should
return this project and nothing else. Whoever copies the text cannot know
which phrases are being watched, because the answer changes with the content.

Nothing is written to disk. Run it, search the phrases, and if a page you do
not recognise carries them verbatim, you have a copy without attribution.

Usage:
  canary_report.py                      # 12 phrases from the default sources
  canary_report.py --count 25
  canary_report.py --paths knowledge/journey-patterns knowledge/industries
"""
import argparse
import os
import re
import sys
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_PATHS = ["knowledge", "CLAUDE.md", "README.md", "docs"]

# Markdown scaffolding, code and links carry no evidentiary weight: they are
# either identical across thousands of repos or an artifact of the format.
STRIP = [
    (re.compile(r"```.*?```", re.DOTALL), " "),
    (re.compile(r"`[^`]*`"), " "),
    (re.compile(r"!?\[([^\]]*)\]\([^)]*\)"), r"\1"),
    (re.compile(r"<[^>]+>"), " "),
    (re.compile(r"https?://\S+"), " "),
    # Emphasis markers go before line-leading markup is stripped, or a bold run
    # at the start of a line loses its asterisks unevenly and two sentences get
    # welded into one phrase that exists nowhere in the rendered text.
    (re.compile(r"\*\*|__|(?<!\w)[*_](?!\w)"), " "),
    (re.compile(r"^[#>\-*|\s]+", re.M), " "),
]

SENTENCE_SPLIT = re.compile(r"(?<=[.!?…])\s+|\n{2,}")
WORD = re.compile(r"[\w'’ıİşğüöçŞĞÜÖÇ-]+", re.UNICODE)

# Function words carry no identifying signal in either language; a phrase made
# mostly of these is common prose, not a fingerprint.
COMMON = set("""
the a an and or but if then than that this these those of in on at to for with
from by as is are was were be been being it its not no do does did have has had
you your we our they their he she i me my will would can could should may might
ve veya ama eğer ise ki bu şu o bir birer için ile den dan de da nin nın nun nün
mi mı mu mü daha en çok az var yok olan olarak gibi göre kadar sonra önce
""".split())


def read_sources(paths):
    docs = []
    for rel in paths:
        full = os.path.join(REPO, rel)
        if os.path.isfile(full) and full.endswith((".md", ".txt")):
            docs.append((rel, open(full, encoding="utf-8").read()))
        elif os.path.isdir(full):
            for root, _dirs, files in os.walk(full):
                for name in sorted(files):
                    if name.endswith((".md", ".txt")):
                        p = os.path.join(root, name)
                        docs.append((os.path.relpath(p, REPO), open(p, encoding="utf-8").read()))
    return docs


def clean(text):
    for pattern, repl in STRIP:
        text = pattern.sub(repl, text)
    # Collapse whitespace but keep sentence terminators, which phrases() needs.
    return re.sub(r"[ \t]+", " ", text)


def phrases(text, size=7):
    """Word windows that never cross a sentence boundary.

    A window spanning two sentences reads fine in this report and then matches
    nothing on the web, because that word sequence does not occur in the
    rendered page — the search would come back empty and the phrase would look
    like proof of no copy when it is proof of a bad phrase.
    """
    for sentence in SENTENCE_SPLIT.split(text):
        words = WORD.findall(sentence)
        for i in range(len(words) - size + 1):
            yield " ".join(words[i:i + size])


def distinctive(phrase):
    """A phrase worth searching for: specific, not scaffolding, not boilerplate."""
    words = phrase.split()
    if len(words) < 5:
        return False
    lowered = [w.lower() for w in words]
    # Mostly function words means it is ordinary prose that will match anything.
    if sum(1 for w in lowered if w in COMMON) > len(words) * 0.5:
        return False
    # At least one anchor: a number, or a word long enough to be domain-specific.
    if not any(any(c.isdigit() for c in w) or len(w) >= 8 for w in words):
        return False
    if any(len(w) > 28 for w in words):  # stray identifier or path fragment
        return False
    return True


def score(phrase, corpus_counts):
    """Rarer inside our own corpus = more likely to be unique outside it."""
    words = [w.lower() for w in phrase.split()]
    rarity = sum(1.0 / (corpus_counts[w] + 1) for w in words)
    length_bonus = min(len(phrase), 90) / 90.0
    return rarity * (1 + length_bonus)


def main(argv):
    ap = argparse.ArgumentParser(description="Suggest search phrases that identify this content.")
    ap.add_argument("--count", type=int, default=12)
    ap.add_argument("--size", type=int, default=7, help="words per phrase")
    ap.add_argument("--paths", nargs="*", default=DEFAULT_PATHS)
    args = ap.parse_args(argv)

    docs = read_sources(args.paths)
    if not docs:
        sys.stderr.write("canary_report: no .md/.txt sources found under %s\n" % ", ".join(args.paths))
        return 2

    corpus_counts = Counter()
    per_doc = []
    for rel, raw in docs:
        text = clean(raw)
        cands = [p for p in phrases(text, args.size) if distinctive(p)]
        corpus_counts.update(w.lower() for p in cands for w in p.split())
        per_doc.append((rel, cands))

    seen = set()
    ranked = []
    for rel, cands in per_doc:
        for p in cands:
            key = p.lower()
            if key in seen:
                continue
            seen.add(key)
            ranked.append((score(p, corpus_counts), rel, p))
    ranked.sort(reverse=True)

    if not ranked:
        print("No sufficiently distinctive phrases found — content may be too short or too generic.")
        return 0

    print("Search each of these in quotes. Anything but this project is a copy.\n")
    for _s, rel, p in ranked[:args.count]:
        print('  "%s"' % p)
        print("      %s\n" % rel)

    print("How to read the results")
    print("  Take a baseline now: search each phrase and note what comes back. A new")
    print("  page carrying one verbatim, later, is a copy — that delta is the signal,")
    print("  not the raw count. Early on this project may not be indexed yet, so an")
    print("  empty result means 'nothing to compare against', not 'nothing copied'.")
    print()
    print("Nothing is stored on purpose: a committed canary list tells whoever copies")
    print("the content exactly which phrases to rewrite. Re-run after substantial")
    print("content changes — the selection follows the text.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

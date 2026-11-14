#!/usr/bin/env python3
"""Verify that every front matter block is valid YAML.

Why this exists: the repo's other checks read front matter with grep, which
happily finds `name:` and `description:` in a block no YAML parser can load.
That gap shipped a real defect — a description containing an unquoted
`style: a Variant …` made `npx skills add` skip the skill entirely, with one
warning in a spinner nobody reads. The skill was in the repo, passed every
check, and did not exist as far as the installer was concerned.

Front matter is an interface, not decoration: Claude Code, `npx skills`, and
every catalog that lists the repo parse it independently. A block that only
*we* can read is a skill that only *we* can run.

The lint below always runs, stdlib-only, because CI installs no YAML library.
When PyYAML happens to be importable it runs too, as the authoritative pass —
the lint targets the failure modes seen in practice, not the whole spec.

Usage:
  check_frontmatter.py skills/*/SKILL.md agents/*.md
"""
import re
import sys

KEY = re.compile(r"^(\s*)(?:-\s+)?([A-Za-z_][\w.-]*):(\s|$)(.*)$")
SEQ = re.compile(r"^(\s*)-\s+(.*)$")

# A plain (unquoted) scalar may not contain this: YAML reads `a: b` inside one
# as a nested mapping, which is a hard parse error and reads as perfectly
# ordinary prose to a human.
#
# ` #` is deliberately NOT here. It truncates a plain scalar at the hash, which
# looks like the same class of bug, but `key: value  # note` is legal YAML and
# the template files use it on purpose. A check that fires on every template is
# one people learn to scroll past, which costs more than the rare prose `#`
# it would catch. PyYAML's pass covers what is genuinely unparseable.
FATAL = [
    (": ", "unquoted ': ' — YAML reads this as a nested mapping"),
]

# Leading characters that make a plain scalar mean something else entirely.
# `[` and `{` are deliberately absent: they open flow collections, which are
# ordinary YAML (`default_channels: [email, push]`) and are skipped below rather
# than flagged. Linting inside them is PyYAML's job when it is available.
INDICATORS = "!&*%@`"


def frontmatter(text):
    """Return the front matter block, or None if the file has none."""
    if not text.startswith("---"):
        return None
    parts = text.split("\n---", 1)
    if len(parts) < 2:
        return None
    head = parts[0]
    return head[3:] if head.startswith("---") else head


def scalar_problems(value, allowed_colons=0):
    """Problems that stop a plain scalar from parsing.

    `allowed_colons` differs by position, and the difference is not cosmetic.
    After `key:` the value must contain no `: ` at all — `desc: a: b` is a hard
    error. A sequence item is different: `- a: b` is a legal one-pair mapping,
    so one is fine there and only the second one is fatal. Verified against
    PyYAML rather than assumed; flagging the legal form would fire on ordinary
    list content and teach people to ignore the check.
    """
    value = value.strip()
    if not value:
        return []
    # Quoted values are safe; so is anything a block scalar introduces.
    if value[0] in "\"'":
        if len(value) > 1 and value[-1] == value[0]:
            return []
        # A value that opens with a quote and does not close it is not a plain
        # scalar with a quote in it — YAML tries to read the whole thing as a
        # quoted string and runs off the end of the block. Caught here because
        # CI has no YAML library to catch it for us.
        return ["opens with %r but does not close it — quote the whole value"
                % value[0]]
    if value[0] in "|>":
        return []
    # Flow collection: valid YAML, and its interior follows different rules than
    # a plain scalar's. Left to PyYAML.
    if value[0] in "[{":
        return []
    found = []
    if value[0] in INDICATORS:
        found.append("starts with the YAML indicator %r" % value[0])
    for needle, why in FATAL:
        if value.count(needle) > allowed_colons:
            found.append(why)
    return found


def lint(block):
    """Flag plain scalars YAML cannot parse. Returns a list of (line, message)."""
    problems = []
    block_indent = None  # inside a `|`/`>` block scalar, skip its content
    for n, line in enumerate(block.split("\n"), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if block_indent is not None:
            if indent > block_indent:
                continue
            block_indent = None

        m = KEY.match(line)
        if m:
            value = m.group(4)
            if value.strip()[:1] in ("|", ">"):
                block_indent = len(m.group(1))
                continue
            for why in scalar_problems(value):
                problems.append((n, "%s: %s" % (m.group(2), why)))
            continue

        s = SEQ.match(line)
        if s:
            for why in scalar_problems(s.group(2), allowed_colons=1):
                problems.append((n, "list item: %s" % why))
    return problems


def main(paths):
    if not paths:
        sys.stderr.write("check_frontmatter.py: no files given\n")
        return 2

    failed = False
    checked = 0
    try:
        import yaml
    except ImportError:
        yaml = None

    for path in paths:
        try:
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
        except OSError as exc:
            print("FAIL: %s: %s" % (path, exc))
            failed = True
            continue

        block = frontmatter(text)
        if block is None:
            print("FAIL: %s: no front matter block" % path)
            failed = True
            continue

        checked += 1
        for line, why in lint(block):
            print("FAIL: %s:%d: %s" % (path, line, why))
            failed = True

        if yaml is not None:
            try:
                yaml.safe_load(block)
            except yaml.YAMLError as exc:
                # Only reached when the lint missed it, which is worth saying
                # plainly rather than folding into the same message.
                print("FAIL: %s: front matter does not parse (%s)"
                      % (path, str(exc).split("\n")[0]))
                failed = True

    if failed:
        return 1
    mode = "lint + PyYAML" if yaml is not None else "lint (PyYAML not installed)"
    print("  ok: %d front matter blocks parse — %s" % (checked, mode))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

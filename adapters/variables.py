#!/usr/bin/env python3
"""Convert CRM-agnostic {{snake_case}} personalization variables to a target
tool's native syntax. Deterministic counterpart of the syntax row in
docs/crm-export-mapping.md — the export skill calls this instead of hand-
rewriting variables (models mistranslate syntax; a table lookup doesn't).

Usage:  variables.py <braze|klaviyo|iterable|insider> <file.md> [...]
        (writes converted text to stdout; redirect to the target file)
Exit:   0 = ok, 1 = file error, 2 = usage error / unknown tool.
"""
import re
import sys

VAR = re.compile(r"\{\{\s*([a-z][a-z0-9_]*)\s*\}\}")


def to_camel(name):
    head, *rest = name.split("_")
    return head + "".join(w.capitalize() for w in rest)


# One entry per documented tool (docs/crm-export-mapping.md, variable row).
# Adding a tool = adding one lambda here + one row in the mapping doc.
TOOLS = {
    "braze": lambda v: "{{${%s}}}" % v,          # Liquid custom attribute
    "klaviyo": lambda v: "{{ %s }}" % v,          # profile property
    "iterable": lambda v: "{{%s}}" % to_camel(v), # Handlebars, camelCase
    "insider": lambda v: "[%%%s%%]" % v,          # [%var%]
}


def convert(text, tool):
    return VAR.sub(lambda m: TOOLS[tool](m.group(1)), text)


def main(argv):
    if len(argv) < 2 or argv[0] not in TOOLS:
        print(__doc__)
        print(f"known tools: {', '.join(sorted(TOOLS))}")
        return 2
    tool = argv[0]
    for path in argv[1:]:
        try:
            text = open(path, encoding="utf-8").read()
        except Exception as e:  # noqa: BLE001
            print(f"error: {path}: {e}", file=sys.stderr)
            return 1
        sys.stdout.write(convert(text, tool))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

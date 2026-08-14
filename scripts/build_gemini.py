#!/usr/bin/env python3
"""Build a Gemini CLI extension from the same skills/agents/rules this repo
ships as a Claude Code plugin — so the plugin reaches Gemini CLI users too,
without a second, hand-maintained copy of the content to keep in sync.

This is NOT a blind concatenation of the SKILL.md files (that is what a naive
port would do, and it would silently ship three things that don't work in
Gemini CLI):

  1. Every skill and agent addresses its own knowledge files and CLAUDE.md
     through `${CLAUDE_PLUGIN_ROOT}`, a Claude Code plugin-install variable
     with no meaning outside it. Rewritten here to `${extensionPath}`, the
     documented Gemini CLI extension-install-path equivalent.
  2. `${extensionPath}/knowledge/event-taxonomy/stage-mapping-rules.md` only
     resolves at runtime if `knowledge/` actually exists inside the
     extension's own install directory — and it doesn't, unless something
     puts it there. The Claude Code plugin gets this for free (Claude Code
     resolves `${CLAUDE_PLUGIN_ROOT}` against the plugin's own repo
     checkout); a Gemini extension installed via `gemini extensions link` is
     a standalone bundle with no such fallback. So this script also COPIES
     every directory the skills/agents/CLAUDE.md actually reference wholesale
     (knowledge/, templates/ — detected, not hardcoded, so a newly
     referenced directory is picked up automatically) into the extension,
     and individual files referenced outside those directories (`docs/`
     mixes the one file a skill actually reads, `data-quality-score.md`,
     with the published GitHub Pages site — demo assets, a hero screenshot —
     that has no business inside a Gemini extension) are copied one file at
     a time rather than dragging their whole parent directory along.
  3. The four agents (event-analyst, journey-architect, copy-writer,
     copy-reviewer) are Claude Code subagents, declared with Claude Code tool
     names (Read, Grep, Glob, Bash). Gemini CLI supports bundled extension
     subagents too, but under a different tool vocabulary (read_file,
     grep_search, glob, run_shell_command) — an unmapped name would silently
     do nothing rather than fail loudly, so TOOL_MAP below is exhaustive on
     purpose and this script refuses to build if an agent uses a tool it
     doesn't cover.

CLAUDE.md's rule text is inlined into GEMINI.md in full, not linked — every
skill and agent cites it by rule number ("kural 17"), and Gemini CLI has no
plugin-relative file-loading step equivalent to Claude Code reading it at the
top of a skill run.

Usage:
  build_gemini.py           # write .gemini/extensions/<plugin>/...
  build_gemini.py --check   # exit 1 if the written output would differ (CI)
"""
import argparse
import filecmp
import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN_JSON = os.path.join(ROOT, ".claude-plugin", "plugin.json")
CLAUDE_MD = os.path.join(ROOT, "CLAUDE.md")
SKILLS_DIR = os.path.join(ROOT, "skills")
AGENTS_DIR = os.path.join(ROOT, "agents")
EXT_ROOT = os.path.join(ROOT, ".gemini", "extensions")

# Directories bundled WHOLE when the source text references them: the model
# operates on the set, not one file at a time (a scenario archive, a
# template + schema pair, a script module that imports a sibling). Detected
# against this allowlist rather than bundling any referenced top-level dir
# sight unseen — a repo's own `docs/` typically mixes runtime-relevant files
# with pure publishing output (a GitHub Pages site, hero images) that has no
# business inside a Gemini extension; a directory in this list is assumed
# to be reference material top to bottom.
BUNDLE_WHOLE_CANDIDATES = ("knowledge", "templates", "scripts")

# Claude Code tool name -> Gemini CLI subagent tool name (per Gemini CLI's
# subagent frontmatter schema). The only place this mapping lives — a new
# tool added to an agent's frontmatter with no entry here fails the build
# instead of shipping a Gemini subagent with a tool name that resolves to
# nothing.
TOOL_MAP = {
    "Read": "read_file",
    "Write": "write_file",
    "Edit": "replace",
    "Grep": "grep_search",
    "Glob": "glob",
    "Bash": "run_shell_command",
}


def die(msg):
    sys.stderr.write("build_gemini: %s\n" % msg)
    sys.exit(2)


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def rewrite_plugin_root(text):
    return text.replace("${CLAUDE_PLUGIN_ROOT}", "${extensionPath}")


def rewrite_bare_links(text, bundled_dirs, bundled_files):
    """A bare markdown link `](knowledge/x.md)` or `](docs/y.md)`, written
    assuming resolution relative to the repo root, breaks once the same text
    is relocated three directories deep into .gemini/extensions/<name>/. Any
    link whose target is something this build actually bundles is rewritten
    the same way `${CLAUDE_PLUGIN_ROOT}` is; anything else (an external URL,
    a path this build does NOT bundle) is left untouched rather than guessed
    at."""

    def repl(m):
        path = m.group(1)
        top = path.split("/", 1)[0]
        if top in bundled_dirs or path in bundled_files:
            return "](${extensionPath}/%s)" % path
        return m.group(0)

    return re.sub(r"\]\(([a-zA-Z0-9_./-]+\.(?:md|html|json))\)", repl, text)


def translate_tools_line(match):
    prefix, val = match.group(0).split(":", 1)
    names = [t.strip() for t in val.split(",") if t.strip()]
    mapped = []
    for n in names:
        if n not in TOOL_MAP:
            die("agent tool '%s' has no Gemini CLI mapping in TOOL_MAP — add one" % n)
        mapped.append(TOOL_MAP[n])
    return prefix + ": " + ", ".join(mapped)


def detect_dependencies(all_text):
    """Everything the source content points at via `${CLAUDE_PLUGIN_ROOT}/…`
    or a bare markdown link, split into whole directories to bundle (from
    BUNDLE_WHOLE_CANDIDATES) and individual files to bundle (anything else
    that resolves to a real file outside those directories)."""
    referenced_dirs = set()
    for m in re.finditer(r"\$\{CLAUDE_PLUGIN_ROOT\}/([a-zA-Z0-9_-]+)/", all_text):
        referenced_dirs.add(m.group(1))
    for m in re.finditer(r"`([a-zA-Z0-9_-]+)/[a-zA-Z0-9_./<>-]+`", all_text):
        referenced_dirs.add(m.group(1))
    bundled_dirs = {
        d for d in referenced_dirs
        if d in BUNDLE_WHOLE_CANDIDATES and os.path.isdir(os.path.join(ROOT, d))
    }

    referenced_files = set()
    for pattern in (
        r"\$\{CLAUDE_PLUGIN_ROOT\}/([a-zA-Z0-9_./-]+\.[a-zA-Z0-9]+)",
        r"\]\(([a-zA-Z0-9_./-]+\.(?:md|html|json))\)",
    ):
        for m in re.finditer(pattern, all_text):
            path = m.group(1)
            top = path.split("/", 1)[0]
            if top not in bundled_dirs and os.path.isfile(os.path.join(ROOT, path)):
                referenced_files.add(path)

    return bundled_dirs, referenced_files


def build_agent_file(text, bundled_dirs, bundled_files):
    """Same frontmatter and body, `tools:` translated, plugin-root and bare
    links rewritten. Only the tools line is touched beyond that — name and
    description stay byte-identical to the Claude Code agent."""
    text = rewrite_plugin_root(text)
    text = rewrite_bare_links(text, bundled_dirs, bundled_files)
    return re.sub(r"^tools:.*$", translate_tools_line, text, count=1, flags=re.M)


def build_files():
    plugin = json.loads(read(PLUGIN_JSON))
    name = plugin["name"]
    # plugin.json's description names the Claude Code plugin specifically
    # ("... for Claude Code."); reused verbatim it would misdescribe this
    # extension inside Gemini CLI's own extension listing.
    description = plugin["description"].replace(" for Claude Code.", ".")
    version = plugin.get("version", "0.1.0")
    ext_dir = os.path.join(EXT_ROOT, name)

    claude_md_text = read(CLAUDE_MD)
    skill_dirs = sorted(
        d for d in os.listdir(SKILLS_DIR) if os.path.isfile(os.path.join(SKILLS_DIR, d, "SKILL.md"))
    )
    skill_texts = {d: read(os.path.join(SKILLS_DIR, d, "SKILL.md")) for d in skill_dirs}
    agent_files = sorted(f for f in os.listdir(AGENTS_DIR) if f.endswith(".md")) if os.path.isdir(AGENTS_DIR) else []
    agent_texts = {f: read(os.path.join(AGENTS_DIR, f)) for f in agent_files}

    all_text = "\n".join([claude_md_text] + list(skill_texts.values()) + list(agent_texts.values()))
    bundled_dirs, bundled_files = detect_dependencies(all_text)

    def prep(text):
        text = rewrite_plugin_root(text)
        return rewrite_bare_links(text, bundled_dirs, bundled_files)

    files = {}  # relpath under ext_dir -> text content
    copy_dirs = {d: os.path.join(ROOT, d) for d in bundled_dirs}          # relpath -> abs source dir
    copy_files = {f: os.path.join(ROOT, f) for f in bundled_files}        # relpath -> abs source file

    files["gemini-extension.json"] = json.dumps(
        {
            "name": name,
            "version": version,
            "description": description,
            "contextFileName": "GEMINI.md",
        },
        indent=2,
    ) + "\n"

    parts = [
        "# %s\n\n%s\n" % (name, description),
        "You are an expert assistant for %s with the skills below available. "
        "Apply whichever skill matches the user's request; the \"Binding "
        "rules\" section is non-negotiable and applies to every skill's "
        "output — this is the same rule set the Claude Code plugin version "
        "of this tool enforces, generated from the same source file.\n"
        % name,
        "## Binding rules (CLAUDE.md)\n\n" + prep(claude_md_text).strip() + "\n",
        "## Skills\n",
    ]
    for d in skill_dirs:
        parts.append(prep(skill_texts[d]).strip() + "\n")

    if agent_files:
        parts.append(
            "## Agents\n\n"
            "This extension bundles the subagents the skills above reference, "
            "under `agents/`. Invoke them the way a skill's text says to — do "
            "not skip a spawn step just because no tool call syntax is shown "
            "inline.\n"
        )

    files["GEMINI.md"] = "\n".join(p.rstrip() + "\n" for p in parts).rstrip() + "\n"

    for fn in agent_files:
        files[os.path.join("agents", fn)] = build_agent_file(agent_texts[fn], bundled_dirs, bundled_files)

    return ext_dir, files, copy_dirs, copy_files


def dirs_in_sync(src, dst):
    if not os.path.isdir(dst):
        return False
    cmp = filecmp.dircmp(src, dst, ignore=["__pycache__"])
    if cmp.left_only or cmp.right_only or cmp.diff_files or cmp.funny_files:
        return False
    return all(dirs_in_sync(os.path.join(src, d), os.path.join(dst, d)) for d in cmp.common_dirs)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="exit 1 if written output would differ")
    args = ap.parse_args(argv)

    ext_dir, files, copy_dirs, copy_files = build_files()

    if args.check:
        stale = []
        for relpath, content in files.items():
            path = os.path.join(ext_dir, relpath)
            if not os.path.isfile(path) or read(path) != content:
                stale.append(relpath)
        for relpath, src in copy_dirs.items():
            if not dirs_in_sync(src, os.path.join(ext_dir, relpath)):
                stale.append(relpath + "/")
        for relpath, src in copy_files.items():
            dst = os.path.join(ext_dir, relpath)
            if not os.path.isfile(dst) or not filecmp.cmp(src, dst, shallow=False):
                stale.append(relpath)
        if stale:
            sys.stderr.write(
                "build_gemini --check: stale or missing (%d): %s\n"
                % (len(stale), ", ".join(sorted(stale)))
            )
            return 1
        print(
            "gemini extension is in sync with its sources (%d files, %d bundled dirs, %d bundled files)"
            % (len(files), len(copy_dirs), len(copy_files))
        )
        return 0

    for relpath, content in files.items():
        path = os.path.join(ext_dir, relpath)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
    for relpath, src in copy_dirs.items():
        dst = os.path.join(ext_dir, relpath)
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for relpath, src in copy_files.items():
        dst = os.path.join(ext_dir, relpath)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)

    print(
        "wrote %d files, %d bundled dirs, %d bundled files under %s"
        % (len(files), len(copy_dirs), len(copy_files), os.path.relpath(ext_dir, ROOT))
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

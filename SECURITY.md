# Security Policy

## Supported versions

This project is pre-1.0 (`v0.1.0`). Only the latest commit on `main` is supported; there are no maintained release branches yet.

## Reporting a vulnerability

Please report security issues privately through [GitHub Security Advisories](https://github.com/ali-demirbas/claude-lifecycle/security/advisories/new) rather than opening a public issue.

Include what you'd include in any report: the affected file(s), how to reproduce, and the impact you think it has.

## Scope

This repo has no server, no hosted service, and collects no user data. The realistic attack surface is:

- `scripts/validate_input.py` and `scripts/validate_output.py`, including the prompt-injection detection applied to connected-source data (GA4/CSV input)
- Any skill or agent instruction that could be manipulated via crafted input data to exfiltrate data or act outside its intended scope

Vulnerabilities in these areas are in scope. Issues that only affect a user's own local run (e.g. a malformed local CSV causing a Python traceback) are better filed as a normal [bug report](.github/ISSUE_TEMPLATE/bug_report.md).

## Response

This is a solo-maintained open-source project. There's no SLA, but reports will be acknowledged and triaged as soon as reasonably possible.

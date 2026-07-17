#!/usr/bin/env python3
"""Shared helpers for validate_input.py, validate_output.py, and eval_check.py."""

failures = []
warnings = []


def fail(msg):
    failures.append(msg)
    print(f"FAIL: {msg}")


def warn(msg):
    warnings.append(msg)
    print(f"  warn: {msg}")


def tr_fold(s):
    """Casefold that avoids Python str.lower()'s Unicode full-casefold
    expansion of Turkish 'İ' (U+0130) into 'i' + U+0307 COMBINING DOT ABOVE —
    that expansion breaks plain-ASCII token/string matching anywhere Turkish
    text with a capital dotted İ is compared (e.g. a header like 'TARİH' or
    a value like 'İptal' would otherwise never match its lowercase-ASCII
    counterpart)."""
    return s.replace("İ", "i").lower()

#!/usr/bin/env bash
# Regression tests for the deterministic validation layer.
# Every fixture has an EXPECTED outcome; a passing bad-fixture or a failing
# good-fixture means a change broke the layer. Run in CI on every PR.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
VO="$DIR/../validate_output.py"
VI="$DIR/../validate_input.py"
FX="$DIR/fixtures"
FAILED=0

expect() { # expect <0|1> <label> <cmd...>
  local want="$1"; shift
  local label="$1"; shift
  "$@" > /tmp/lc_test_out.txt 2>&1
  local got=$?
  # A crash is never a valid outcome: an uncaught exception also exits 1, so a
  # "fails as expected" that is really a Traceback must still fail the test.
  if grep -q "Traceback (most recent call last)" /tmp/lc_test_out.txt; then
    echo "FAIL: $label — crashed (Traceback); a validator must fail(), not crash"
    sed 's/^/    | /' /tmp/lc_test_out.txt | tail -12
    FAILED=1
    return
  fi
  if [ "$got" -eq "$want" ]; then
    echo "PASS: $label (exit $got)"
  else
    echo "FAIL: $label — expected exit $want, got $got"
    sed 's/^/    | /' /tmp/lc_test_out.txt | tail -12
    FAILED=1
  fi
}

expect_contains() { # expect_contains <label> <needle> <cmd...>
  local label="$1"; shift
  local needle="$1"; shift
  "$@" > /tmp/lc_test_out.txt 2>&1
  if grep -q "Traceback (most recent call last)" /tmp/lc_test_out.txt; then
    echo "FAIL: $label — crashed (Traceback); a validator must fail(), not crash"
    sed 's/^/    | /' /tmp/lc_test_out.txt | tail -12
    FAILED=1
    return
  fi
  if grep -qF "$needle" /tmp/lc_test_out.txt; then
    echo "PASS: $label"
  else
    echo "FAIL: $label — expected output to contain: $needle"
    sed 's/^/    | /' /tmp/lc_test_out.txt | tail -12
    FAILED=1
  fi
}

echo "== journey JSON =="
expect 0 "valid journey passes"                 python3 "$VO" journey "$FX/good_journey.json"
expect 1 "disallowed channel fails"             python3 "$VO" journey "$FX/bad_channel_journey.json"
expect 1 "bad wait + double primary KPI fails"  python3 "$VO" journey "$FX/bad_wait_journey.json"
expect 1 "unknown pattern (no matching journey-patterns file) fails" python3 "$VO" journey "$FX/bad_unknown_pattern_journey.json"
expect_contains "unknown pattern names the missing file" "has no knowledge/journey-patterns/this-pattern-does-not-exist.md" python3 "$VO" journey "$FX/bad_unknown_pattern_journey.json"
expect 1 "stage mismatch vs pattern file fails"  python3 "$VO" journey "$FX/bad_stage_journey.json"
expect_contains "stage mismatch names both stages" "stage 'retention' != trial-conversion.md's own stage 'revenue'" python3 "$VO" journey "$FX/bad_stage_journey.json"
expect 1 "step count outside pattern's depth_range fails"  python3 "$VO" journey "$FX/bad_depthrange_journey.json"
expect_contains "depth_range violation names the range" "outside trial-conversion.md's own depth_range [4, 10]" python3 "$VO" journey "$FX/bad_depthrange_journey.json"

echo "== journey doc <-> JSON consistency =="
expect 0 "matching doc+json passes"                       python3 "$VO" consistency "$FX/good_journey.md" "$FX/good_journey.json"
expect 1 "channel/branch/KPI mismatches all caught"        python3 "$VO" consistency "$FX/bad_consistency_journey.md" "$FX/good_journey.json"
expect_contains "channel mismatch reported" "channel 'push' != " python3 "$VO" consistency "$FX/bad_consistency_journey.md" "$FX/good_journey.json"
expect_contains "branch-condition presence mismatch reported" "branch-condition presence" python3 "$VO" consistency "$FX/bad_consistency_journey.md" "$FX/good_journey.json"
expect_contains "KPI count mismatch reported" "KPI rows vs" python3 "$VO" consistency "$FX/bad_consistency_journey.md" "$FX/good_journey.json"

echo "== copy docs =="
expect 0 "honest copy passes"                   python3 "$VO" copy "$FX/good_copy.md" --max-discount 30
expect 1 "wrong count + em-dash + %80 fails"    python3 "$VO" copy "$FX/bad_copy.md" --max-discount 30
expect 1 "inflated limit column fails"          python3 "$VO" copy "$FX/bad_inflated_limit_copy.md"
expect 1 "vars without Fallback section fails"  python3 "$VO" copy "$FX/bad_missing_fallback_copy.md"
expect 0 "non-discount %NN near 'indirim yok' passes" python3 "$VO" copy "$FX/good_pct_nondiscount_copy.md" --max-discount 20
expect 1 "push title checked against push's real 40, not in-app/email's" python3 "$VO" copy "$FX/bad_push_wrong_channel_copy.md"
expect 1 "Turkish SMS enforced at 70-char UCS-2, not 160"  python3 "$VO" copy "$FX/bad_sms_turkish_ucs2_copy.md"
expect 1 "TR in-app banner alias resolves to its real ceiling" python3 "$VO" copy "$FX/bad_tr_inapp_banner_copy.md"
expect 1 "decimal discount (45.5%) not truncated to 5"     python3 "$VO" copy "$FX/bad_decimal_discount_copy.md" --max-discount 30
expect 0 "banned-word candidate is a warn, not a hard fail" python3 "$VO" copy "$FX/warn_banned_word_copy.md" --sector ecommerce
expect_contains "caps-lock Turkish banned term matches lowercase lexicon entry (dotless-I fix)" "Banned Word Candidate" python3 "$VO" copy "$FX/warn_banned_word_copy.md" --sector ecommerce
expect 1 "WhatsApp header enforced at its real 60-char ceiling (was silently unchecked)" python3 "$VO" copy "$FX/bad_whatsapp_header_copy.md"
expect 1 "in-app 'Primary CTA' field resolves to the cta ceiling, not left unparsed" python3 "$VO" copy "$FX/bad_inapp_primary_cta_copy.md"
expect 1 "fallback section itself still containing a var fails, not just heading presence" python3 "$VO" copy "$FX/bad_fallback_has_var_copy.md"
expect 1 "variant missing json fence or empty hypothesis fails" python3 "$VO" copy "$FX/bad_variant_metadata_copy.md"
expect 1 "legal review flag without Reviewer notes fails"       python3 "$VO" copy "$FX/bad_legal_no_notes_copy.md"
expect 0 "legal review flag WITH Reviewer notes passes"         python3 "$VO" copy "$FX/good_legal_with_notes_copy.md"
expect 0 "push image with https + alt text passes"              python3 "$VO" copy "$FX/good_push_image_copy.md"
expect 1 "push image with http + empty alt fails both checks"   python3 "$VO" copy "$FX/bad_push_image_copy.md"
expect_contains "insecure image URL reported"    "is not HTTPS" python3 "$VO" copy "$FX/bad_push_image_copy.md"
expect_contains "missing alt text reported"      "Alt text is empty" python3 "$VO" copy "$FX/bad_push_image_copy.md"

echo "== all-mode dispatch =="
expect 1 "all-mode: TR filename detected as copy, non-journey JSON skipped (not hard-failed)" python3 "$VO" all "$FX/all_mode_tr"

echo "== canvas skeleton =="
expect 0 "edited-in-place canvas passes"        python3 "$VO" canvas "$FX/good_canvas.html" --template templates/copy-canvas.html
expect 1 "truncated/retyped canvas fails"       python3 "$VO" canvas "$FX/bad_truncated_canvas.html" --template templates/copy-canvas.html

echo "== portfolio registry =="
expect 0 "within caps passes"                   python3 "$VO" portfolio "$FX/good_portfolio.json"
expect 1 "duplicate id + over cap fails"        python3 "$VO" portfolio "$FX/bad_portfolio.json"
expect 1 "int est_msgs fails gracefully"        python3 "$VO" portfolio "$FX/bad_est_msgs_portfolio.json"
expect 1 "declared overlap over cap fails"      python3 "$VO" portfolio "$FX/bad_overlap_portfolio.json"
expect 1 "campaign-week load over cap fails"    python3 "$VO" portfolio "$FX/bad_campaign_portfolio.json"

echo "== compliance caps drift guard =="
expect_contains "caps parsed live from consent-and-quiet-hours.md match expected defaults" \
  "CAPS_PARSE_OK" \
  python3 -c "
import sys; sys.path.insert(0, '$DIR/..')
import validate_output as vo
caps = vo.load_default_caps()
expected = {'email': 4, 'push': 5, 'sms': 2, 'whatsapp': 2, 'in_app': 99, 'total': 8}
print('CAPS_PARSE_OK' if caps == expected else f'CAPS_PARSE_MISMATCH: {caps}')
"

echo "== eval checker =="
expect 0 "eval mini-case good run passes"       python3 "$DIR/../eval_check.py" "$DIR/fixtures/evalcase/mini-case" --out-root "$DIR/fixtures/evalout-good"
expect 1 "eval mini-case bad run fails"         python3 "$DIR/../eval_check.py" "$DIR/fixtures/evalcase/mini-case" --out-root "$DIR/fixtures/evalout-bad"

echo "== adapters =="
expect 0 "variable syntax conversion runs"      python3 adapters/variables.py braze "$FX/vars_sample.md"
expect 2 "unknown tool rejected"                python3 adapters/variables.py hubspot "$FX/vars_sample.md"
expect 0 "wait-duration conversion runs"                python3 adapters/durations.py braze P3DT12H
expect_contains "3.5-day wait rounds to whole hours" "P3DT12H -> 84 hours" python3 adapters/durations.py braze P3DT12H
expect 2 "duration adapter: unknown tool rejected"      python3 adapters/durations.py hubspot P1D
expect 2 "duration adapter: unparseable duration rejected" python3 adapters/durations.py braze P
expect 0 "duration adapter: P1W (week) accepted"        python3 adapters/durations.py braze P1W
expect_contains "1-week wait converts to 7 days" "P1W -> 7 days" python3 adapters/durations.py braze P1W
expect 2 "duration adapter: P1WT1H (week+time, invalid ISO 8601) rejected" python3 adapters/durations.py braze P1WT1H

echo "== input data =="
expect 0 "clean CSV passes"                     python3 "$VI" "$FX/good_input.csv"
expect 1 "injection + broken timestamps fails"  python3 "$VI" "$FX/bad_input.csv"
expect 0 "GA4 aggregate export passes (preamble, YYYYMMDD, Realtime col)" python3 "$VI" "$FX/ga4_aggregate_input.csv"
expect 1 "injection in a free-text column (not a NAME_COL keyword) is caught" python3 "$VI" "$FX/bad_injection_freetext_col.csv"

echo
if [ "$FAILED" -eq 1 ]; then echo "TESTS FAILED"; exit 1; fi
echo "ALL TESTS PASSED"

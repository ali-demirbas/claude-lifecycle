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
  if grep -qF -- "$needle" /tmp/lc_test_out.txt; then
    echo "PASS: $label"
  else
    echo "FAIL: $label — expected output to contain: $needle"
    sed 's/^/    | /' /tmp/lc_test_out.txt | tail -12
    FAILED=1
  fi
}

echo "== journey JSON =="
expect 3 "valid legacy 1.x journey: no errors, but timing is unverifiable (not a pass)"                 python3 "$VO" journey "$FX/good_journey.json"
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
expect 1 "drifted heading (title before channel) still resolves sms + enforces 70" python3 "$VO" copy "$FX/bad_drifted_heading_sms_copy.md"
expect_contains "drifted-heading failure points at the sms channel file" "knowledge/channels/sms.md" python3 "$VO" copy "$FX/bad_drifted_heading_sms_copy.md"
expect 0 "metadata field lines after Fallback are not fallback content" python3 "$VO" copy "$FX/good_fallback_metadata_copy.md"
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

echo "== build_canvas (deterministic swap) =="
expect 0 "build_canvas produces a skeleton-clean canvas"  python3 "$DIR/../build_canvas.py" --template templates/canvas.html --journeys "$FX/build_canvas_journeys.json" --meta "$FX/build_canvas_meta.json" --out /tmp/lc_build_canvas_out.html
expect_contains "build_canvas self-verify reports skeleton match" "skeleton matches the template" python3 "$DIR/../build_canvas.py" --template templates/canvas.html --journeys "$FX/build_canvas_journeys.json" --meta "$FX/build_canvas_meta.json" --out /tmp/lc_build_canvas_out.html
expect 0 "build_canvas output passes the independent canvas validator" python3 "$VO" canvas /tmp/lc_build_canvas_out.html --template templates/canvas.html
expect 2 "build_canvas rejects a template with no JOURNEYS region" python3 "$DIR/../build_canvas.py" --template "$FX/good_copy.md" --journeys "$FX/build_canvas_journeys.json" --meta "$FX/build_canvas_meta.json" --out /tmp/lc_build_canvas_bad.html

echo "== explicit flow tree (schema + journey_render + flow-path consistency + flow canvas) =="
# Schema: the optional `flow` node-tree validates, and is constrained (not a free object)
expect 3 "legacy journey WITH a flow tree: no errors, timing unverifiable"                python3 "$VO" journey "$FX/flow_journey.json"
expect 1 "invalid flow node kind rejected by schema"         python3 "$VO" journey "$FX/bad_flow_schema_journey.json"
expect_contains "bad flow kind names the allowed enum" "is not one of ['entry', 'decision', 'message', 'wait', 'exit']" python3 "$VO" journey "$FX/bad_flow_schema_journey.json"
# journey_render: emits §5 table + §8 diagram from flow/steps; exits 2 without flow; branch-faithful
expect 0 "journey_render renders a flow journey"             python3 "$DIR/../journey_render.py" "$FX/flow_journey.json"
expect 2 "journey_render exits 2 on a no-flow journey"       python3 "$DIR/../journey_render.py" "$FX/good_journey.json"
expect_contains "journey_render mermaid has labeled branch edges (not a linear approximation)" "|Evet| S2" python3 "$DIR/../journey_render.py" "$FX/flow_journey.json" --section mermaid
expect_contains "journey_render round-trips the fixture doc's §5 table + §8 diagram" "ROUNDTRIP_OK" \
  python3 -c "
import sys, json; sys.path.insert(0, '$DIR/..')
import journey_render as jr
doc = json.load(open('$FX/flow_journey.json', encoding='utf-8'))
md = open('$FX/flow_journey.md', encoding='utf-8').read()
n = jr._norm
ok = n(jr.render_step_table(doc)) == n(jr.extract_step_table(md)) and n(jr.render_mermaid(doc)) == n(jr.extract_mermaid(md))
print('ROUNDTRIP_OK' if ok else 'ROUNDTRIP_MISMATCH')
"
# consistency: flow doc must reproduce the generated §5/§8 exactly; tampering is caught
expect 0 "flow journey doc matches regenerated §5 table + §8 diagram"  python3 "$VO" consistency "$FX/flow_journey.md" "$FX/flow_journey.json"
expect 1 "tampered §8 diagram is caught (a check the old path never had)" python3 "$VO" consistency "$FX/bad_flow_mermaid.md" "$FX/flow_journey.json"
expect_contains "tampered §8 diagram names the section" "§8 Mermaid diagram does not match" python3 "$VO" consistency "$FX/bad_flow_mermaid.md" "$FX/flow_journey.json"
expect 1 "tampered §5 table + §8 diagram both caught"       python3 "$VO" consistency "$FX/bad_flow_consistency.md" "$FX/flow_journey.json"
expect_contains "tampered §5 table names the section" "§5 step table does not match" python3 "$VO" consistency "$FX/bad_flow_consistency.md" "$FX/flow_journey.json"
# build_canvas --from-journeys: derives the canvas from the journey JSON; flow used directly, flat fallback otherwise
expect 0 "build_canvas --from-journeys (with flow) builds"  python3 "$DIR/../build_canvas.py" --template templates/canvas.html --from-journeys "$FX/flow_journey.json" --meta "$FX/build_canvas_meta.json" --out /tmp/lc_flow_canvas.html
expect 0 "flow canvas passes the independent canvas validator" python3 "$VO" canvas /tmp/lc_flow_canvas.html --template templates/canvas.html
expect 0 "flow canvas embeds the decision node from flow (branch-faithful, no approximation)" grep -q '"kind": "decision"' /tmp/lc_flow_canvas.html
expect 0 "build_canvas --from-journeys (no flow) builds via the flat linear fallback" python3 "$DIR/../build_canvas.py" --template templates/canvas.html --from-journeys "$FX/good_journey.json" --meta "$FX/build_canvas_meta.json" --out /tmp/lc_flat_canvas.html
expect 0 "flat-fallback canvas passes the independent canvas validator" python3 "$VO" canvas /tmp/lc_flat_canvas.html --template templates/canvas.html
expect 1 "flat-fallback canvas is linear (no decision node — fallback can't branch)" grep -q '"kind": "decision"' /tmp/lc_flat_canvas.html
expect 2 "build_canvas rejects --journeys and --from-journeys together" python3 "$DIR/../build_canvas.py" --template templates/canvas.html --journeys "$FX/build_canvas_journeys.json" --from-journeys "$FX/flow_journey.json" --meta "$FX/build_canvas_meta.json" --out /tmp/lc_x.html
# flow tree text is customer/canvas-facing — dropped Turkish diacritics there are a real, catchable defect (steps[]/objective/kpis stay unchecked: this repo's own production journeys write those in English)
expect 1 "flow tree with dropped Turkish diacritics fails"            python3 "$VO" journey "$FX/bad_flow_diacritics_journey.json"
expect_contains "dropped-diacritics failure names the offending words" "flow tree text reads like Turkish with dropped diacritics" python3 "$VO" journey "$FX/bad_flow_diacritics_journey.json"
expect 3 "flow tree with correct Turkish diacritics raises no error (no false positive)" python3 "$VO" journey "$FX/flow_journey.json"
expect_contains "dotless-i case-fold does not false-positive (ı must not match ASCII i under IGNORECASE)" "CASEFOLD_OK" python3 -c "
import sys; sys.path.insert(0, '$DIR/..')
from _validate_common import tr_diacritic_stripped_hits
# 'adım','kullanıcı','hatırlatma','aynı','yardımcı' are CORRECTLY accented — none should match
hits = tr_diacritic_stripped_hits('Adım bazında kullanıcıya hatırlatma; aynı yardımcı ton.')
print('CASEFOLD_OK' if not hits else f'CASEFOLD_FAIL: {hits}')
"
# guard: a reused/stale --meta whose header text claims a journey count that disagrees with the actual build is warned (cosmetic → warn, never block)
expect_contains "build_canvas warns when --meta header journey-count disagrees with the build" "header says '6 journey' but 1" python3 "$DIR/../build_canvas.py" --template templates/canvas.html --from-journeys "$FX/flow_journey.json" --meta "$FX/build_canvas_meta_count6.json" --out /tmp/lc_count.html
expect 0 "count-mismatch is a warning, not a hard stop (still builds)" python3 "$DIR/../build_canvas.py" --template templates/canvas.html --from-journeys "$FX/flow_journey.json" --meta "$FX/build_canvas_meta_count6.json" --out /tmp/lc_count.html

echo "== portfolio registry =="
expect 3 "legacy portfolio within caps: no errors, but declared counts are unverifiable"                   python3 "$VO" portfolio "$FX/good_portfolio.json"
expect 1 "duplicate id + over cap fails"        python3 "$VO" portfolio "$FX/bad_portfolio.json"
expect 1 "int est_msgs fails gracefully"        python3 "$VO" portfolio "$FX/bad_est_msgs_portfolio.json"
expect 1 "declared overlap over cap fails"      python3 "$VO" portfolio "$FX/bad_overlap_portfolio.json"
expect 1 "campaign-week load over cap fails"    python3 "$VO" portfolio "$FX/bad_campaign_portfolio.json"

echo "== dossier reliability tag =="
expect 0 "T1 dossier with reliability tag passes"  python3 "$VO" dossier "$FX/good_dossier.md"
expect 0 "T3 dossier with reliability n/a passes"  python3 "$VO" dossier "$FX/good_t3_dossier.md"
expect 1 "DQS line without reliability fails"      python3 "$VO" dossier "$FX/bad_dossier_no_reliability.md"
expect 1 "T3 claiming healthy reliability fails"   python3 "$VO" dossier "$FX/bad_t3_dossier_reliability.md"

echo "== audience activation preconditions =="
expect 0 "SQL audiences with activation_status pass"   python3 "$VO" audience "$FX/good_audiences.sql"
expect 1 "missing status / bare conditional fails"     python3 "$VO" audience "$FX/bad_audiences.sql"
expect 0 "traits JSON with conditional + note passes"  python3 "$VO" audience "$FX/good_audiences_traits.json"
expect 1 "traits JSON missing status/note fails"       python3 "$VO" audience "$FX/bad_audiences_traits.json"

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

echo "== acceptance 0.3.0: schema 2.0 timing, branches, frequency, exits, measurement =="
AX="$FX/acceptance"
# 1. explicit anchors: offsets from entry vs from the previous send
expect 0 "A1 entry-anchored P0D..P30D sends fit the P30D window"        python3 "$VO" journey "$AX/a1_good_entry_anchored.json"
expect_contains "A1 timeline places the last send at day 30" "m6 @ P30D" python3 "$VO" timeline "$AX/a1_good_entry_anchored.json"
expect 1 "A1 same offsets chained to the previous send (day 82) fail"   python3 "$VO" journey "$AX/a1_bad_prev_anchored.json"
expect 0 "A1 event-anchored sends with a declared time anchor compute"  python3 "$VO" journey "$AX/t_trial_event_anchored.json"
expect_contains "A1 trial_end-2d lands at day 5"          "t2 @ P5D"     python3 "$VO" timeline "$AX/t_trial_event_anchored.json"
expect 3 "A1 event anchor with no declared relation is unverifiable"    python3 "$VO" journey "$AX/t_trial_no_time_anchor.json"
expect 1 "A1 calendar time without a timezone fails"                    python3 "$VO" journey "$AX/g_calendar_no_timezone.json"
# 2. frequency is computed from sends, not trusted from the declaration
expect 0 "A2 a 4-email cart journey alone is within the email cap"      python3 "$VO" journey "$AX/a2_cart_4_emails.json"
expect 1 "A2 portfolio declaring 2 emails/week for it fails"            python3 "$VO" portfolio "$AX/a2_portfolio_declares_2.json"
expect_contains "A2 the failure names the computed count" "computed 4"  python3 "$VO" portfolio "$AX/a2_portfolio_declares_2.json"
# 3. exclusive branches do not add up
expect 0 "A3 exclusive A/B branches validate"                           python3 "$VO" journey "$AX/a3_exclusive_branches.json"
expect_contains "A3 branch A send at day 3"               "a1 @ P3D"     python3 "$VO" timeline "$AX/a3_exclusive_branches.json"
expect_contains "A3 branch B send also at day 3 (not 4)"  "b1 @ P3D"     python3 "$VO" timeline "$AX/a3_exclusive_branches.json"
# 4. opens are not a branching signal
expect 1 "A4 open-only decision fails"                                  python3 "$VO" journey "$AX/a4_open_only_branch.json"
# 5. measurement design
expect 1 "A5 marketing journey with no measurement plan fails"          python3 "$VO" journey "$AX/a5_no_measurement.json"
expect 1 "A5 holdout without consistent assignment/control scope fails" python3 "$VO" journey "$AX/a5_holdout_incomplete.json"
expect 0 "A5 low-volume journey with reason + alternative passes"       python3 "$VO" journey "$AX/a5_good_low_volume_alternative.json"
expect 1 "A5 low-volume journey with no alternative fails"              python3 "$VO" journey "$AX/a5_low_volume_no_alternative.json"
expect 0 "A5 service journey is not forced into a holdout"              python3 "$VO" journey "$AX/a5_good_service_no_holdout.json"
# 6. declared external journeys count; unknown ones are not 'verified'
expect 1 "A6 cart + declared existing welcome breach the email cap"     python3 "$VO" portfolio "$AX/a6_portfolio_external_welcome.json"
expect 3 "A6 unknown external journeys: global frequency unverifiable"  python3 "$VO" portfolio "$AX/a6_portfolio_external_unknown.json"
# 7. exit conditions are re-checked before every send
expect 1 "A7 purchase checked only at entry fails"                      python3 "$VO" journey "$AX/a7_purchase_checked_only_at_entry.json"
expect 1 "A7 no consent-withdrawal exit fails"                          python3 "$VO" journey "$AX/a7_no_consent_exit.json"
# 8. repeated triggers
expect 1 "A8 duplicate trigger spawning new instances with no cooldown fails" python3 "$VO" journey "$AX/a8_duplicate_trigger_uncontrolled.json"
# 9. not measured != did not happen
expect 1 "A9 decision without an unmeasurable route fails"              python3 "$VO" journey "$AX/a9_no_unmeasurable_route.json"
expect 1 "A9 unmeasurable routed to a 'disengaged' exit fails"          python3 "$VO" journey "$AX/a9_unmeasurable_read_as_disinterest.json"
expect 1 "A9 decision on an event missing from the inventory fails"     python3 "$VO" journey "$AX/a9_undefined_event.json"
# graph structure
expect 1 "G broken link fails"                                          python3 "$VO" journey "$AX/g_broken_link.json"
expect 1 "G unreachable node fails"                                     python3 "$VO" journey "$AX/g_unreachable.json"
expect 1 "G cycle fails"                                                python3 "$VO" journey "$AX/g_cycle.json"
expect 1 "G merge anchored to a branch-only node fails"                 python3 "$VO" journey "$AX/g_merge_bad_anchor.json"
expect 0 "G merge anchored to a common node passes"                     python3 "$VO" journey "$AX/g_merge_good_anchor.json"
expect 1 "G send on a withdrawn channel fails"                          python3 "$VO" journey "$AX/g_withdrawn_channel_send.json"
# 10. a broken canvas is never a successful output
expect 1 "A10 canvas with an empty JOURNEYS array fails"                python3 "$VO" canvas "$AX/empty_canvas.html" --template "$DIR/../../templates/canvas.html"
rm -f /tmp/lc_should_not_exist.html
expect 1 "A10 build_canvas refuses a journey whose graph is broken"     python3 "$DIR/../build_canvas.py" --template "$DIR/../../templates/canvas.html" --from-journeys "$AX/g_broken_link.json" --meta "$FX/build_canvas_meta.json" --out /tmp/lc_should_not_exist.html
expect 0 "A10 ...and wrote nothing"                                     test ! -e /tmp/lc_should_not_exist.html
expect 0 "A10 build_canvas renders a valid schema-2.0 journey"          python3 "$DIR/../build_canvas.py" --template "$DIR/../../templates/canvas.html" --from-journeys "$AX/a3_exclusive_branches.json" --meta "$FX/build_canvas_meta.json" --out /tmp/lc_v2_canvas.html
expect 0 "A10 ...and the result passes the canvas check"                python3 "$VO" canvas /tmp/lc_v2_canvas.html --template "$DIR/../../templates/canvas.html"
# legacy outputs: reproduced from real 0.2.0 runs (anonymized), must no longer pass silently
expect 1 "L1 legacy winback with an open-based branch fails"            python3 "$VO" journey "$AX/l1_legacy_winback_ambiguous_waits.json"
expect 3 "L2 legacy cart: ambiguous waits are unverifiable, not passed" python3 "$VO" journey "$AX/l2_legacy_cart.json"
expect 1 "L2 legacy portfolio undercounting its own sends fails"        python3 "$VO" portfolio "$AX/l2_legacy_portfolio.json"

echo "== eval checker =="
expect 0 "eval mini-case good run passes"       python3 "$DIR/../eval_check.py" "$DIR/fixtures/evalcase/mini-case" --out-root "$DIR/fixtures/evalout-good"
expect 1 "eval mini-case bad run fails"         python3 "$DIR/../eval_check.py" "$DIR/fixtures/evalcase/mini-case" --out-root "$DIR/fixtures/evalout-bad"

echo "== input data =="
expect 0 "clean CSV passes"                     python3 "$VI" "$FX/good_input.csv"
expect 1 "injection + broken timestamps fails"  python3 "$VI" "$FX/bad_input.csv"
expect 0 "GA4 aggregate export passes (preamble, YYYYMMDD, Realtime col)" python3 "$VI" "$FX/ga4_aggregate_input.csv"
expect 1 "injection in a free-text column (not a NAME_COL keyword) is caught" python3 "$VI" "$FX/bad_injection_freetext_col.csv"

echo
if [ "$FAILED" -eq 1 ]; then echo "TESTS FAILED"; exit 1; fi
echo "ALL TESTS PASSED"

"""Tests of analysis/analyze.py on rows written here, where every count is known by hand."""

import math

import pytest

from analysis import analyze as an


def row(mid, cls, stratum, v="", c="", *, status="ok", valid=True, collision=False, expected="block"):
    """v and c are '', 'check', 'crash' or 'timeout': how each detector ended."""
    def det(by):
        if by == "timeout":
            return ("", "", "timeout")
        return ({"": "0", "check": "1", "crash": "2"}[by], str(by != ""), by)
    ve, vb, vby = det(v)
    ce, cb, cby = det(c)
    if "timeout" in (v, c):
        status = "timeout"
    r = {"mutant_id": mid, "source": "operator", "class": cls, "expected": expected, "seed": "1",
         "target": f"t:{mid}", "old": "1.23", "new": "1.24", "stratum": stratum, "code_commit": "abc",
         "case_hash": "h", "status": status, "valid": str(valid), "invalid_reason": "",
         "collision": str(collision), "verifier_exit": ve, "verifier_blocked": vb, "verifier_by": vby,
         "verifier_s": "2.1", "count_exit": ce, "count_blocked": cb, "count_by": cby, "count_s": "0.6"}
    if status == "invalid":
        for k in ("verifier_exit", "verifier_blocked", "verifier_by", "verifier_s",
                  "count_exit", "count_blocked", "count_by", "count_s"):
            r[k] = ""
    return r


# --------------------------------------------------------------------------- Wilson


@pytest.mark.parametrize("k, n, lo, hi", [
    (0, 50, 0.0, 0.0713),
    (50, 50, 0.9287, 1.0),
    (5, 10, 0.2366, 0.7634),
    (1, 25, 0.0071, 0.1954),
])
def test_wilson_known_values(k, n, lo, hi):
    a, b = an.wilson(k, n)
    assert a == pytest.approx(lo, abs=5e-4)
    assert b == pytest.approx(hi, abs=5e-4)


def test_wilson_of_nothing_is_none():
    assert an.wilson(0, 0) is None


# --------------------------------------------------------------------------- repetitions


def test_split_keeps_the_first_line_and_sets_the_second_apart():
    rows = [row("M2-001", "M2", "once", "check", "check"),
            row("M2-002", "M2", "once", "check", "check"),
            row("M2-001", "M2", "once", "check", "check")]
    first, again = an.split_repeats(rows)
    assert [r["mutant_id"] for r in first] == ["M2-001", "M2-002"]
    assert [r["mutant_id"] for r in again] == ["M2-001"]


def test_repetition_ignores_the_times_and_sees_any_other_difference():
    a = row("M2-001", "M2", "once", "check", "check")
    b = dict(a, verifier_s="9.9", count_s="9.9")
    c = dict(a, verifier_exit="0", verifier_blocked="False", verifier_by="")
    rep = an.repetition([a, row("M1-001", "M1", "bare decimal")], [b])
    assert rep == [{"class": "M2", "repeated": 1, "same": 1, "verifier_differs": 0, "count_differs": 0,
                    "other_differs": 0, "columns": []}]
    rep = an.repetition([a], [c])
    assert rep[0]["columns"] == ["verifier_blocked", "verifier_by", "verifier_exit"]
    assert rep[0]["same"] == 0 and rep[0]["verifier_differs"] == 1 and rep[0]["count_differs"] == 0


# --------------------------------------------------------------------------- counting (section 7)


def test_tally_counts_by_check_and_by_crash_apart():
    rows = [row("M6-001", "M6", "read, print now false", "check", ""),
            row("M6-002", "M6", "read, print now false", "crash", ""),
            row("M6-003", "M6", "read, print now false", "", "")]
    t = an.tally(rows)
    assert t["verifier"] == {"valid": 3, "check": 1, "crash": 1, "timeout": 0}
    assert t["count"] == {"valid": 3, "check": 0, "crash": 0, "timeout": 0}
    assert t["either"] == {"valid": 3, "check": 1, "crash": 1, "timeout": 0}
    assert t["invalid"] == 0


def test_an_invalid_mutant_leaves_every_count_and_is_never_a_miss():
    rows = [row("M2-001", "M2", "once", "check", "check"),
            row("M2-002", "M2", "once", status="invalid", valid=False)]
    t = an.tally(rows)
    assert t["invalid"] == 1
    assert t["verifier"]["valid"] == 1 and t["count"]["valid"] == 1 and t["either"]["valid"] == 1


def test_a_timeout_leaves_only_that_detectors_counts():
    rows = [row("M2-001", "M2", "once", "timeout", "check"),
            row("M2-002", "M2", "once", "check", "check")]
    t = an.tally(rows)
    assert t["verifier"] == {"valid": 1, "check": 1, "crash": 0, "timeout": 1}
    assert t["count"] == {"valid": 2, "check": 2, "crash": 0, "timeout": 0}
    # the two together: a mutant one detector did not finish on is not judged by the pair
    assert t["either"] == {"valid": 1, "check": 1, "crash": 0, "timeout": 1}


def test_either_is_by_a_check_when_one_of_the_two_blocks_by_a_check():
    rows = [row("X-1", "M6", "s", "crash", "check"), row("X-2", "M6", "s", "", "check"),
            row("X-3", "M6", "s", "crash", "")]
    assert an.tally(rows)["either"] == {"valid": 3, "check": 2, "crash": 1, "timeout": 0}


# --------------------------------------------------------------------------- words


@pytest.mark.parametrize("cell, word", [
    ({"valid": 4, "check": 4, "crash": 0}, "covered"),
    ({"valid": 4, "check": 0, "crash": 0}, "open"),
    ({"valid": 4, "check": 3, "crash": 0}, "partial"),
    ({"valid": 4, "check": 3, "crash": 1}, "partial"),  # covered is every one by a check
    ({"valid": 4, "check": 0, "crash": 1}, "partial"),
    ({"valid": 0, "check": 0, "crash": 0}, "no valid mutant"),
])
def test_word(cell, word):
    assert an.word(cell) == word


# --------------------------------------------------------------------------- Q2


def q2_rows():
    rows = []
    for i in range(4):
        rows.append(row(f"M2-{i:03d}", "M2", "once", "check", "check"))
    for i in range(4, 8):
        rows.append(row(f"M2-{i:03d}", "M2", "repeated", "", "check"))
    for i in range(3):
        rows.append(row(f"M7-{i:03d}", "M7", "B, first column", "check", ""))
    rows.append(row("M6-001", "M6", "unread", "", "", expected="none"))
    rows.append(row("M6-002", "M6", "read, print now false", "check", ""))
    rows.append(row("M1-001", "M1", "bare decimal", "", ""))
    rows.append(row("M1-002", "M1", "has a unit", "", ""))
    return rows


def find(table, cls, stratum):
    hit = [g for g in table if g["class"] == cls and g["stratum"] == stratum]
    assert len(hit) == 1, (cls, stratum, [(g["class"], g["stratum"]) for g in table])
    return hit[0]


def test_q2_reports_stratified_classes_by_stratum_only():
    table = an.q2(q2_rows())
    assert find(table, "M2", "once")["verifier"]["check"] == 4
    assert find(table, "M2", "repeated")["verifier"]["check"] == 0
    assert not [g for g in table if g["class"] == "M2" and g["stratum"] == "all"]


def test_q2_m1_has_a_line_for_the_whole_class_and_one_per_recorded_donor():
    table = an.q2(q2_rows())
    assert find(table, "M1", "all")["verifier"]["valid"] == 2
    assert find(table, "M1", "bare decimal")["verifier"]["valid"] == 1


def test_q2_interval_only_where_the_targets_were_sampled():
    table = an.q2(q2_rows())
    g = find(table, "M2", "once")
    assert g["sampled"] and g["verifier"]["interval"] == pytest.approx(an.wilson(4, 4))
    g = find(table, "M7", "B, first column")
    assert not g["sampled"] and g["verifier"]["interval"] is None


def test_q2_interval_counts_blocked_by_check_or_crash():
    rows = [row("M6-001", "M6", "read, print now false", "check", ""),
            row("M6-002", "M6", "read, print now false", "crash", ""),
            row("M6-003", "M6", "read, print now false", "", "")]
    g = find(an.q2(rows), "M6", "read, print now false")
    assert g["verifier"]["interval"] == pytest.approx(an.wilson(2, 3))


def test_q2_m6_only_print_now_false_enters_the_rate():
    table = an.q2(q2_rows())
    assert find(table, "M6", "read, print now false")["in_rate"]
    assert not find(table, "M6", "unread")["in_rate"]
    assert find(table, "M6", "unread")["verifier"]["interval"] is None


def test_q2_marks_what_follows_from_the_count_checks_design():
    table = an.q2(q2_rows())
    assert find(table, "M2", "once")["count_by_design"]
    assert find(table, "M1", "all")["count_by_design"]
    assert find(table, "M6", "unread")["count_by_design"]
    assert not find(table, "M7", "B, first column")["count_by_design"]


def test_q2_full_m2_is_its_own_class_and_needs_no_interval():
    rows = [row("M2all-001", "M2all", "once", "check", "check"),
            row("M2all-002", "M2all", "repeated", "", "check")]
    g = find(an.q2(rows), "M2all", "repeated")
    assert not g["sampled"] and g["count"]["interval"] is None and g["count"]["check"] == 1


def test_collisions_are_counted_apart_and_stay_in_the_class():
    rows = [row("M2-001", "M2", "once", "check", "check", collision=True),
            row("M2-002", "M2", "once", "check", "check")]
    assert find(an.q2(rows), "M2", "once")["verifier"]["valid"] == 2
    col = an.collisions(rows)
    assert len(col) == 1 and col[0]["class"] == "M2" and col[0]["verifier"]["valid"] == 1


# --------------------------------------------------------------------------- Q1


def test_q1_counts_places_and_distinct_strings_by_stratum():
    rows = [dict(row("M2all-001", "M2all", "once"), old="12.75"),
            dict(row("M2all-002", "M2all", "repeated"), old="4.66"),
            dict(row("M2all-003", "M2all", "repeated"), old="4.66"),
            dict(row("M2all-004", "M2all", "repeated"), old="3,749"),
            dict(row("M2all-005", "M2all", "repeated"), old="3749"),
            dict(row("M2all-006", "M2all", "repeated"), old="−0.818"),
            dict(row("M2all-007", "M2all", "repeated"), old="-0.818"),
            dict(row("M2-001", "M2", "once"), old="9.99")]
    q = an.q1(rows)
    assert q["once"] == {"places": 1, "strings": 1}
    assert q["repeated"] == {"places": 6, "strings": 3}
    assert q["all"] == {"places": 7, "strings": 4}


# --------------------------------------------------------------------------- controls (section 5)


def test_controls_pass_and_fail():
    good = [row("M7-001", "M7", "B, first column", "check", ""),
            row("M2-001", "M2", "once", "check", "check"),
            row("M1-001", "M1", "bare decimal", "", "")]
    c = {x["control"]: x for x in an.controls(good)}
    assert all(x["passes"] for x in c.values()) and len(c) == 3
    bad = [row("M7-001", "M7", "B, first column", "crash", ""),
           row("M2-001", "M2", "once", "check", "crash"),
           row("M1-001", "M1", "bare decimal", "", "check")]
    assert not any(x["passes"] for x in an.controls(bad))


# --------------------------------------------------------------------------- predictions


def test_each_prediction_is_compared_with_its_result():
    rows = q2_rows() + [row("M4-001", "M4", "same section", "check", "")]
    table = an.predictions(an.q2(rows))
    def get(cls, stratum, det):
        return next(p for p in table if (p["class"], p["stratum"], p["detector"]) == (cls, stratum, det))
    assert get("M2", "once", "verifier")["held"] is True
    assert get("M2", "repeated", "count")["held"] is True
    p = get("M4", "same section", "verifier")
    assert p["predicted"] == "open" and p["result"] == "covered" and p["held"] is False
    # a line with no mutant has no verdict: it is neither held nor failed
    assert get("M5", "checked", "verifier")["held"] is None


def test_m6_crash_counts_for_the_prediction_that_allows_it():
    rows = [row("M6-001", "M6", "read, print now false", "check", ""),
            row("M6-002", "M6", "read, print now false", "crash", "")]
    table = an.predictions(an.q2(rows))
    p = next(p for p in table if p["class"] == "M6" and p["stratum"] == "read, print now false"
             and p["detector"] == "verifier")
    assert p["held"] is True


# --------------------------------------------------------------------------- rendering


def test_render_writes_counts_and_intervals():
    text = an.render(q2_rows(), [])
    assert "| M2 | once | 4 | 0 | 4/4 |" in text
    lo, hi = an.wilson(4, 4)
    assert f"{100 * lo:.1f} to {100 * hi:.1f}" in text
    assert "by design" in text
    assert not math.isnan(lo)


def test_m7_exception_is_a_cell_that_holds_a_published_string():
    """PREDICTIONS.md: the count check is open on M7 'unless a cell happens to hold a published
    string'. The exception is about the string the cell held, not about the new one."""
    rows = [dict(row("M7-001", "M7", "B, other column", "check", "check"),
                 old=r"\( 1.1 \times 10^{-12} \)", new=r"\( 1.6 \times 10^{-12} \)"),
            dict(row("M7-002", "M7", "B, other column", "check", ""),
                 old=r"\( 3.3 \times 10^{-12} \)", new=r"\( 3.4 \times 10^{-12} \)")]
    def m7(published):
        return next(p for p in an.predictions(an.q2(rows), published)
                    if p["class"] == "M7" and p["detector"] == "count")
    p = m7(["1.1", "9"])
    assert p["result"] == "partial" and p["held"] is True
    assert p["note"] == "1 of the 1 blocked hold a published string"
    assert m7(["7.7"])["held"] is False
    assert m7(["11.1", "1.12"])["held"] is False  # part of a longer number is not a place

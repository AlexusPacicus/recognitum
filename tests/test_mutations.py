import json
import random
import tempfile
from pathlib import Path

import pytest

from mutations import core, operators
from mutations.operators import apply_edits
from mutations import run


@pytest.fixture(scope="module")
def case():
    return core.Case()


# --------------------------------------------------------------------------- places


def test_normalize_maps_thousands_comma_back_to_the_line():
    line = "cost 3,749 µs and §3.2 then 12.20"
    norm, cols = core.normalize_line(line)
    assert "3749" in norm and "3.2" not in norm
    places = core.find_places(line, ["3749", "12.20", "3.2"])
    by = {p.string: p for p in places}
    assert by["3749"].printed == "3,749" and by["3749"].unit == "µs"
    assert "3.2" not in by
    assert by["12.20"].printed == "12.20"


def test_presence_rule_rejects_longer_numbers():
    assert core.find_places("11.75 and 3.11 and 111", ["11"]) == []
    assert [p.printed for p in core.find_places("x 11, y", ["11"])] == ["11"]


def test_minus_sign_is_read_as_hyphen():
    p = core.find_places("λ = −0.818 here", ["-0.818"])[0]
    assert p.printed == "−0.818"


def test_units():
    assert core.find_places("1.39× faster", ["1.39"])[0].unit == "×"
    assert core.find_places("2.7% across", ["2.7"])[0].unit == "%"
    assert core.find_places("12.6 s each", ["12.6"])[0].unit == "s"
    assert core.find_places("12.6 steps", ["12.6"])[0].unit == ""
    assert core.find_places("6.8 MB", ["6.8"])[0].unit == ""


def test_every_published_string_of_two_or_more_has_a_place(case):
    found = {p.string for p in case.places}
    assert {s for s in case.published if len(s) > 1} <= found


def test_figure_places_exclude_references_fences_and_appendix_tables(case):
    for p in case.figure_places:
        line = case.lines[p.line - 1]
        assert len(p.string) >= 3 and line.section != "References"
        assert not line.fenced and core.appendix_table(line) is None
    assert any(not p.figure and len(p.string) >= 3 for p in case.places)


def test_strata_once_counts_short_places_too():
    places = core.find_places("a 11 b 11.5 c 11", ["11", "11.5"])
    st = core.strata(places)
    assert sorted(st.values()) == ["once", "repeated", "repeated"]


# --------------------------------------------------------------------------- digits


def test_first_digit_of_a_run_never_becomes_zero():
    assert "0" not in core.digit_choices("12.50", 0)
    assert "0" in core.digit_choices("12.50", 1)
    assert "0" in core.digit_choices("12.50", 3)
    assert "0" in core.digit_choices("7.22", 0)  # a run of one digit
    assert "0" in core.digit_choices("3,749", 2)  # inside the integer part
    assert "0" not in core.digit_choices("3,749", 0)
    cell = r"\( 1.2 \times 10^{-14} \)"
    assert "0" not in core.digit_choices(cell, cell.index("14"))


def test_change_digit_changes_exactly_one_digit():
    rng = random.Random(1)
    for _ in range(200):
        i, new = core.change_digit(rng, "12.50", core.digit_positions("12.50"))
        assert sum(a != b for a, b in zip("12.50", new)) == 1 and new[i] != "12.50"[i]


# --------------------------------------------------------------------------- registry and artifacts


def test_registry_has_42_rows(case):
    rows = core.registry_rows((case.root / core.REGISTRY).read_text(encoding="utf-8"))
    assert len(rows) == 42
    assert {r.status for r in rows} == {"checked", "construction", "remove"}


def test_json_numbers_offsets_match_the_text(case):
    for f in sorted((case.root / core.RESULTS_DIR).glob("*.json")):
        text = f.read_text(encoding="utf-8")
        obj = json.loads(text)
        for path, s, e, tok, v in core.json_numbers(text):
            assert text[s:e] == tok
            node = obj
            for p in path:
                node = node[p]
            assert node == v and not isinstance(node, bool)


def test_leaves_are_under_results_only(case):
    lv = core.leaves(case.root)
    assert lv and all(leaf.path[0] == "results" for leaf in lv)


# --------------------------------------------------------------------------- operators


@pytest.mark.parametrize("cls", ["M1", "M2", "M4", "M5", "M6", "M7", "B1"])
def test_draws_are_deterministic_and_change_the_text(case, cls):
    a = operators.draw(case, cls, 50)
    b = operators.draw(case, cls, 50)
    assert [m.to_json() for m in a] == [m.to_json() for m in b]
    assert len({m.mutant_id for m in a}) == len(a)
    for m in a:
        original = (case.root / m.file).read_text(encoding="utf-8")
        assert apply_edits(original, m.edits) != original


def test_sizes(case):
    assert len(operators.draw(case, "M5", 50)) == 42
    m7 = operators.draw(case, "M7", 50)
    assert len(m7) == 36
    assert sum(m.stratum.startswith("B") for m in m7) == 12
    assert len(operators.draw(case, "M2", 50)) <= 50
    assert len(operators.draw(case, "M6", 50)) == 50


def test_m7_never_changes_the_base_ten(case):
    for m in operators.draw(case, "M7", 50):
        assert m.new.count("10^") == m.old.count("10^")


def test_m2_targets_are_figure_places_with_one_digit_changed(case):
    keys = {p.target for p in case.figure_places}
    for m in operators.draw(case, "M2", 50):
        assert m.target in keys
        assert len(m.new) == len(m.old) and sum(a != b for a, b in zip(m.old, m.new)) == 1


def test_m1_figure_is_new_and_copies_the_donor_format(case):
    taken = core.printed_numerals(case.text) | set(case.published)
    for m in operators.draw(case, "M1", 50):
        fig, donor = m.extra["figure"], m.extra["donor_string"].lstrip("+-")
        assert fig not in taken and fig[0] != "0"
        assert len(fig.split(".")[0]) == len(donor.split(".")[0])
        assert ("." in fig) == ("." in donor)
        assert m.new.startswith(" A further run gave ") and m.new.endswith(".")


def test_m4_pairs_share_the_unit_and_differ(case):
    by = {p.target: p for p in case.figure_places}
    for m in operators.draw(case, "M4", 50):
        a, b = (by[t] for t in m.target.split(" <-> "))
        assert a.string != b.string and a.unit == b.unit
        assert (a.section == b.section) == (m.stratum == "same section")


def test_b1_new_string_agrees_with_the_measured_value(case):
    for m in operators.draw(case, "B1", 50):
        assert core.agree(m.extra["measured"], m.new.replace(core.MINUS, "-"))
        k = len(m.extra["string"].split(".")[1])
        assert len(m.new.split(".")[1]) == k - 1 if k > 1 else "." not in m.new


def test_m6_values():
    leaf = core.Leaf("x.json", ("results", "a"), 0, 1, "4", 4)
    assert operators.new_leaf_text(leaf) == "6"
    assert operators.new_leaf_text(core.Leaf("x", ("results",), 0, 1, "1", 1)) == "2"
    assert operators.new_leaf_text(core.Leaf("x", ("results",), 0, 1, "0.0", 0.0)) == "1.0"
    assert operators.new_leaf_text(core.Leaf("x", ("results",), 0, 1, "2.0", 2.0)) == "3.0"


# --------------------------------------------------------------------------- validity and the runner


def _copy_with(m):
    tmp = tempfile.TemporaryDirectory()
    root = run.make_copy(Path(tmp.name))
    p = root / m.file
    p.write_text(apply_edits(p.read_text(encoding="utf-8"), m.edits), encoding="utf-8")
    return tmp, root


def test_validity_accepts_the_edit_and_rejects_anything_else(case):
    m = operators.draw(case, "M2", 50)[0]
    tmp, root = _copy_with(m)
    with tmp:
        assert run.validate(m, root) == ""
        (root / "README.md").write_text("tampered", encoding="utf-8")
        assert run.validate(m, root).startswith("files changed")


def test_validity_rejects_a_wrong_edit(case):
    m = operators.draw(case, "M7", 50)[0]
    tmp, root = _copy_with(m)
    with tmp:
        p = root / m.file
        p.write_text(p.read_text(encoding="utf-8") + "x", encoding="utf-8")
        assert run.validate(m, root) == "copy differs from the operator's edit"


def test_verifier_passes_the_control_and_blocks_an_m7_by_a_check(case):
    with tempfile.TemporaryDirectory() as tmp:
        root = run.make_copy(Path(tmp))
        r = run.run_verifier(root, 120)
        assert r["exit"] == 0 and r["by"] == ""
    m = operators.draw(case, "M7", 50)[0]
    tmp, root = _copy_with(m)
    with tmp:
        r = run.run_verifier(root, 120)
        assert r["blocked"] and r["by"] == "check"


def test_verifier_crash_is_told_apart(case):
    with tempfile.TemporaryDirectory() as tmp:
        root = run.make_copy(Path(tmp))
        (root / core.RESULTS_DIR / "latency.json").write_text("{", encoding="utf-8")
        r = run.run_verifier(root, 120)
        assert r["blocked"] and r["by"] == "crash"


def test_m6_subgroups(case):
    control = [v for _, _, v in case.checks]
    with tempfile.TemporaryDirectory() as tmp:
        root = run.make_copy(Path(tmp))
        assert run.m6_subgroup(root, control) == "unread"
        leaf = next(lf for lf in core.leaves(case.root)
                    if lf.artifact == "poles.json" and lf.path[-1] == "lambda")
        p = root / core.RESULTS_DIR / leaf.artifact
        edit = [(leaf.start, leaf.end, operators.new_leaf_text(leaf))]
        p.write_text(apply_edits(p.read_text(encoding="utf-8"), edit), encoding="utf-8")
        assert run.m6_subgroup(root, control) == "read, print now false"

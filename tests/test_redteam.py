"""Tests of redteam/run.py: reading a response, placing an edit, and the validity rules of
section 4 of the protocol. No response of the red team is read here."""

import json

import pytest

from redteam import run as rt

DOC = """# Title

Intro with 12.50 and 12.50 again.

## 1. Results

The cost is 4.66 µs, against 3,749 µs before; the gain is −0.818.
Twice 7.1 here and 7.1 there.

## References

1. A. Author, 2019, pages 100 to 120.
"""


# --------------------------------------------------------------------------- reading a response


def test_parse_a_bare_json_list():
    assert rt.parse_response('[{"line": 3, "old": "a", "new": "b", "why": "w"}]')[0]["line"] == 3


def test_parse_a_list_inside_a_fence_and_prose():
    text = 'Here are the edits:\n\n```json\n[{"line": 3, "old": "a", "new": "b", "why": "w"}]\n```\nDone.'
    assert rt.parse_response(text) == [{"line": 3, "old": "a", "new": "b", "why": "w"}]


def test_parse_a_list_with_prose_around_and_no_fence():
    assert rt.parse_response('Sure. [{"line": 1}] Hope it helps [1].') == [{"line": 1}]


def test_brackets_in_the_prose_before_the_list_do_not_hide_it():
    text = 'Let me read toy.md [offset=850, limit=1] and note [1].\nHere: [{"line": 2}]\n'
    assert rt.parse_response(text) == [{"line": 2}]


def test_a_response_with_no_list_is_an_error_not_an_empty_list():
    with pytest.raises(ValueError):
        rt.parse_response("I cannot help with that.")


def test_part_and_conversation_from_the_file_name():
    assert rt.part_of("R1-3.txt") == ("R1", 3)
    assert rt.part_of("R2.md") == ("R2", 1)
    assert rt.part_of("R3-nemotron-2026-11-15.json") == ("R3", 1)
    with pytest.raises(ValueError):
        rt.part_of("notes.txt")


def test_edit_identifiers():
    edits = rt.edits_of("R1", 3, [{"line": 3, "old": "a", "new": "b", "why": "w"}] * 2)
    assert [e["edit_id"] for e in edits] == ["R1-3-01", "R1-3-02"]
    assert edits[0]["part"] == "R1"


# --------------------------------------------------------------------------- placing an edit


def test_locate_gives_the_offsets_of_old_on_its_line():
    start, end = rt.locate(DOC, 7, "4.66")
    assert DOC[start:end] == "4.66" and DOC[:start].count("\n") == 6


@pytest.mark.parametrize("line, old, reason", [
    (8, "7.1", "`old` appears 2 times on the line"),
    (7, "9.99", "`old` appears 0 times on the line"),
    (99, "4.66", "no such line"),
    (0, "4.66", "no such line"),
    ("seven", "4.66", "`line` is not a whole number"),
    (7, "", "`old` is empty"),
])
def test_an_edit_that_does_not_apply_says_why(line, old, reason):
    with pytest.raises(rt.DoesNotApply, match=reason):
        rt.locate(DOC, line, old)


def test_a_line_given_as_a_string_of_digits_is_accepted():
    assert rt.locate(DOC, "7", "4.66") == rt.locate(DOC, 7, "4.66")


# --------------------------------------------------------------------------- one number


@pytest.mark.parametrize("old, new, pair", [
    ("4.66", "4.86", ("4.66", "4.86")),
    ("is 4.66 µs", "is 5.66 µs", ("4.66", "5.66")),
    ("3,749 µs", "3,149 µs", ("3749", "3149")),
    ("−0.818", "−0.518", ("-0.818", "-0.518")),
    ("−0.818", "0.818", ("-0.818", "0.818")),
    ("10^{-14}", "10^{-12}", ("-14", "-12")),
])
def test_one_number_changed(old, new, pair):
    assert rt.one_number(old, new) == pair


@pytest.mark.parametrize("old, new", [
    ("4.66 µs", "4.66 ms"),            # no number changes
    ("4.66 and 3.1", "4.86 and 3.2"),  # two numbers change
    ("is 4.66 µs", "was 4.86 µs"),     # a word changes too
    ("4.66", "about four"),            # the number is gone
    ("4.66", "4.66 and 1.2"),          # a number is added
])
def test_not_one_number_changed(old, new):
    assert rt.one_number(old, new) is None


@pytest.mark.parametrize("old, new, differs", [
    ("4.66", "4.67", True),
    ("4.66", "4.664", False),   # the same at two decimals
    ("4.66", "4.660", False),
    ("12", "12.4", False),      # the same at no decimals
    ("12", "12.6", True),
    ("3749", "3750", True),
])
def test_differs_at_the_decimals_of_the_old_number(old, new, differs):
    assert rt.differs(old, new) is differs


# --------------------------------------------------------------------------- validity of R1


def r1(line, old, new):
    return rt.validity_r1(DOC, {"line": line, "old": old, "new": new})


def test_a_valid_r1_edit():
    assert r1(7, "4.66", "4.86") == ""


def test_r1_invalid_cases():
    assert "appears 2 times" in r1(8, "7.1", "7.2")
    assert r1(12, "100", "200") == "inside the References section"
    assert r1(5, "1", "2") == "on a heading"
    assert r1(7, "4.66 µs", "4.66 ms") == "does not change exactly one number"
    assert r1(7, "4.66", "4.664") == "the new number equals the old one at the old one's decimals"


def test_an_edit_missing_a_key_is_invalid_not_a_crash():
    assert rt.validity_r1(DOC, {"line": 7, "old": "4.66"}) == "the edit has no `new`"


# --------------------------------------------------------------------------- rulings for R2


def test_rulings_must_cover_every_r2_edit_that_applies(tmp_path):
    p = tmp_path / "rulings.csv"
    p.write_text("edit_id,ruling,note\nR2-1-01,yes,\nR2-1-02,no,a matter of wording\n", encoding="utf-8")
    assert rt.read_rulings(p) == {"R2-1-01": True, "R2-1-02": False}
    assert rt.missing_rulings(["R2-1-01", "R2-1-02"], rt.read_rulings(p)) == []
    assert rt.missing_rulings(["R2-1-01", "R2-1-03"], rt.read_rulings(p)) == ["R2-1-03"]


def test_a_ruling_that_is_neither_yes_nor_no_is_an_error(tmp_path):
    p = tmp_path / "rulings.csv"
    p.write_text("edit_id,ruling,note\nR2-1-01,maybe,\n", encoding="utf-8")
    with pytest.raises(ValueError):
        rt.read_rulings(p)


def test_no_rulings_file_means_no_ruling(tmp_path):
    assert rt.read_rulings(tmp_path / "absent.csv") == {}


# --------------------------------------------------------------------------- files of R2


def test_r2_file_is_found_by_path_or_by_a_unique_name(tmp_path):
    (tmp_path / "paper").mkdir()
    (tmp_path / "paper" / "m.md").write_text("x", encoding="utf-8")
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    (tmp_path / "a" / "same.json").write_text("{}", encoding="utf-8")
    (tmp_path / "b" / "same.json").write_text("{}", encoding="utf-8")
    assert rt.resolve_file(tmp_path, "paper/m.md") == "paper/m.md"
    assert rt.resolve_file(tmp_path, "m.md") == "paper/m.md"
    with pytest.raises(rt.DoesNotApply, match="2 files"):
        rt.resolve_file(tmp_path, "same.json")
    with pytest.raises(rt.DoesNotApply, match="no such file"):
        rt.resolve_file(tmp_path, "absent.md")
    with pytest.raises(rt.DoesNotApply, match="outside the case"):
        rt.resolve_file(tmp_path, "../elsewhere.md")


def test_rows_use_the_columns_of_the_results_file():
    from mutations.run import COLUMNS
    row = rt.result_row({"edit_id": "R1-1-01", "part": "R1", "line": 7, "old": "4.66", "new": "4.86"},
                        file="paper/m.md", reason="on a heading", stratum="", commit="c", case_hash="h")
    assert set(row) <= set(COLUMNS)
    assert row["source"] == "red team" and row["class"] == "R1" and row["status"] == "invalid"
    assert row["valid"] is False and row["invalid_reason"] == "on a heading" and row["expected"] == "block"
    assert json.dumps(row)


def test_a_response_with_no_list_gives_no_edit_and_is_named_not_repaired(tmp_path):
    (tmp_path / "R1-1-m-2026-11-15.txt").write_text('[{"line": 1, "old": "a", "new": "b"}]', encoding="utf-8")
    (tmp_path / "R1-2-m-2026-11-15.txt").write_text("I cannot help with that.", encoding="utf-8")
    (tmp_path / "R1-3-m-2026-11-15.txt").write_text("", encoding="utf-8")
    unreadable = []
    edits = rt.read_responses(tmp_path, unreadable)
    assert [e["edit_id"] for e in edits] == ["R1-1-01"]
    assert unreadable == ["R1-2-m-2026-11-15.txt", "R1-3-m-2026-11-15.txt"]


def test_the_second_launch_is_read_apart_with_identifiers_of_its_own(tmp_path):
    """Deviation 7: the five edits of R1-3 of the second launch are run through both detectors and
    reported apart, never with those of the third launch, whose identifiers they would repeat."""
    (tmp_path / "R1-3-m-2026-11-15.txt").write_text('[{"line": 1, "old": "a", "new": "b"}]', encoding="utf-8")
    (tmp_path / "R1-4-m-2026-11-15.txt").write_text("One sentence, no list.", encoding="utf-8")
    (tmp_path / "R2-1-m-2026-11-15.txt").write_text('[{"line": 2, "old": "c", "new": "d"}]', encoding="utf-8")
    edits = rt.read_launch(2, tmp_path)
    assert [e["edit_id"] for e in edits] == ["L2-R1-3-01"]   # only part R1 of it is run
    assert edits[0]["part"] == "R1" and edits[0]["class"] == "R1-L2"
    row = rt.result_row(edits[0], file="paper/m.md", reason="", stratum="repeated", commit="c", case_hash="h")
    assert row["class"] == "R1-L2" and row["mutant_id"] == "L2-R1-3-01"
    assert rt.LAUNCHES[2] == rt.HERE / "launch-2" / "responses"

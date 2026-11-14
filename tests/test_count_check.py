import json
import subprocess
import sys
from pathlib import Path

import pytest

from countcheck import count_check as cc

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "countcheck" / "count_check.py"
CONTROL_JSON = REPO / "results" / "control" / "control.json"
MANUSCRIPT = REPO / "case" / "paper" / "polar-projector-paper.md"

DOC = """Intro 12.50 here.

## 1. One

Cost 4.66 µs and 3,749 µs; see §3.2 and 1.17.

## 2. Two

Again 4.66 and −0.818.

### 2.1 Sub

Nothing.
"""
STRINGS = ["12.50", "4.66", "3749", "3.2", "1.17", "-0.818", "7"]


def run(control: str, copy: str, strings, tmp_path) -> subprocess.CompletedProcess:
    a, b, s = tmp_path / "a.md", tmp_path / "b.md", tmp_path / "s.json"
    a.write_text(control, encoding="utf-8")
    b.write_text(copy, encoding="utf-8")
    s.write_text(json.dumps(strings), encoding="utf-8")
    return subprocess.run([sys.executable, str(SCRIPT), "--control", str(a), "--copy", str(b),
                           "--strings", str(s)], capture_output=True, text=True)


def test_counts_follow_the_presence_rule():
    c = cc.counts(DOC, sorted({s for s in STRINGS if len(s) > 1}))
    assert c[("(before the first heading)", "12.50")] == 1
    assert c[("1. One", "4.66")] == 1 and c[("2. Two", "4.66")] == 1
    assert c[("1. One", "3749")] == 1  # thousands comma removed
    assert ("1. One", "3.2") not in c  # section reference removed
    assert c[("2. Two", "-0.818")] == 1  # Unicode minus read as hyphen
    assert not any(s == "7" for _, s in c)


def test_headings_are_not_places():
    assert cc.counts("## 3.2 Title\n\ntext\n", ["3.2"]) == {}


def test_not_inside_a_longer_number():
    assert cc.counts("11.75 3.11 111 x\n", ["11"]) == {}


def test_control_against_itself_passes(tmp_path):
    r = run(DOC, DOC, STRINGS, tmp_path)
    assert r.returncode == 0, r.stdout


def test_a_changed_digit_blocks_by_a_check(tmp_path):
    r = run(DOC, DOC.replace("1.17", "1.18"), STRINGS, tmp_path)
    assert r.returncode == 1 and "LOWER" in r.stdout


def test_an_added_figure_does_not_block(tmp_path):
    r = run(DOC, DOC.replace("Nothing.", "Nothing. A further run gave 8.92."), STRINGS, tmp_path)
    assert r.returncode == 0


def test_a_swap_inside_one_section_does_not_block(tmp_path):
    swapped = DOC.replace("4.66 µs and 3,749", "TMP µs and 3,749").replace("1.17.", "4.66.").replace("TMP", "1.17")
    assert swapped != DOC
    assert run(DOC, swapped, STRINGS, tmp_path).returncode == 0


def test_a_swap_across_sections_blocks(tmp_path):
    swapped = DOC.replace("Intro 12.50", "Intro TMP").replace("1.17.", "12.50.").replace("TMP", "1.17")
    assert run(DOC, swapped, STRINGS, tmp_path).returncode == 1


def test_a_missing_section_counts_as_zero(tmp_path):
    cut = DOC.replace("## 2. Two\n\nAgain 4.66 and −0.818.\n", "")
    assert run(DOC, cut, STRINGS, tmp_path).returncode == 1


def test_a_higher_count_does_not_block(tmp_path):
    assert run(DOC, DOC.replace("Nothing.", "Nothing 1.17."), STRINGS, tmp_path).returncode == 0


def test_its_own_errors_end_with_exit_code_2(tmp_path):
    r = subprocess.run([sys.executable, str(SCRIPT), "--control", str(tmp_path / "none.md"),
                        "--copy", str(tmp_path / "none.md"), "--strings", str(tmp_path / "none.json")],
                       capture_output=True, text=True)
    assert r.returncode == 2
    bad = tmp_path / "bad.json"
    bad.write_text("{\"published_strings\": 3}", encoding="utf-8")
    a = tmp_path / "a.md"
    a.write_text(DOC, encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPT), "--control", str(a), "--copy", str(a),
                        "--strings", str(bad)], capture_output=True, text=True)
    assert r.returncode == 2


@pytest.mark.skipif(not CONTROL_JSON.exists(), reason="needs the control run")
def test_the_real_control_passes_and_every_drawn_m2_blocks(tmp_path):
    text = MANUSCRIPT.read_text(encoding="utf-8")
    strings = json.loads(CONTROL_JSON.read_text(encoding="utf-8"))["published_strings"]
    assert cc.lowered(text, text, strings) == []
    from mutations import core
    from mutations.operators import Mutant, apply_edits
    drawn = REPO / "results" / "drawn" / "M2.jsonl"
    for line in drawn.read_text(encoding="utf-8").splitlines()[:10]:
        m = Mutant.from_json(line)
        assert cc.lowered(text, apply_edits(text, m.edits), strings), m.mutant_id
    assert core.MANUSCRIPT == "paper/polar-projector-paper.md"

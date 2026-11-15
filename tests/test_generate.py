"""Tests of redteam/generate.py with a stand-in for the client: no model is called here."""

import json
import stat
import sys

import pytest

from redteam import generate as gen
from redteam import run as rt

STUB = """#!{python}
import os, sys
if "--version" in sys.argv:
    print("9.9.9")
    raise SystemExit(0)
print("cwd-files:" + ",".join(sorted(os.listdir("."))))
print("argv:" + "|".join(a for a in sys.argv[1:] if len(a) < 80))
attached = [sys.argv[k + 1] for k, a in enumerate(sys.argv) if a == "-f"]
here = os.path.realpath(os.getcwd())
print("attached-absolute-in-folder:" + str(len(attached) == 2 and all(
    os.path.isabs(a) and os.path.isfile(a) and os.path.dirname(os.path.realpath(a)) == here
    for a in attached)))
print("pwd-is-folder:" + str(os.path.realpath(os.environ.get("PWD", "")) == here))
print("dir-is-folder:" + str(os.path.realpath(sys.argv[sys.argv.index("--dir") + 1]) == here
                             if "--dir" in sys.argv else False))
print('[{{"line": 1, "old": "a", "new": "b", "why": "w"}}]')
{extra}
"""


def client(tmp_path, extra=""):
    p = tmp_path / "fake-client"
    p.write_text(STUB.format(python=sys.executable, extra=extra), encoding="utf-8")
    p.chmod(p.stat().st_mode | stat.S_IXUSR)
    return str(p)


@pytest.fixture
def setup(tmp_path):
    files = []
    for name in ("paper.md", "verify.py"):
        f = tmp_path / name
        f.write_text(f"content of {name}\n", encoding="utf-8")
        files.append(f)
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    for part in ("R1", "R2", "R3"):
        (prompts / f"{part}.txt").write_text(f"prompt of {part}\n", encoding="utf-8")
    return {"files": files, "prompts": prompts, "responses": tmp_path / "responses",
            "log": tmp_path / "generation.jsonl", "model": "prov/some-model", "date": "2026-11-15"}


def test_the_seven_conversations_of_section_4_and_r3_apart():
    main = gen.plan("main")
    assert [c["id"] for c in main] == ["R1-1", "R1-2", "R1-3", "R1-4", "R1-5", "R1-6", "R2-1"]
    assert [c["part"] for c in main] == ["R1"] * 6 + ["R2"]
    assert [c["id"] for c in gen.plan("R3")] == ["R3-1"]


def test_file_names_are_read_back_by_the_runner():
    name = gen.response_name("R2-1", "prov/4o-mini", "2026-11-15")
    assert name == "R2-1-prov_4o-mini-2026-11-15.txt"
    assert rt.part_of(name) == ("R2", 1)
    assert rt.part_of(gen.response_name("R1-6", "prov/m", "2026-11-15")) == ("R1", 6)


def test_a_conversation_sees_two_files_and_its_output_is_stored_as_returned(tmp_path, setup):
    records = gen.generate("main", client=client(tmp_path), jobs=3, **setup)
    assert len(records) == 7
    out = sorted(p.name for p in setup["responses"].iterdir())
    assert out[0] == "R1-1-prov_some-model-2026-11-15.txt" and len(out) == 7
    text = (setup["responses"] / out[0]).read_text(encoding="utf-8")
    assert "cwd-files:paper.md,verify.py" in text
    # The client does not resolve an attached file against the folder it is started in: the first
    # launch failed on `File not found` for a relative name. Every way of naming the folder is used.
    assert "attached-absolute-in-folder:True" in text
    assert "pwd-is-folder:True" in text and "dir-is-folder:True" in text
    assert "--pure" in text and "prov/some-model" in text and "--auto" not in text
    assert rt.parse_response(text) == [{"line": 1, "old": "a", "new": "b", "why": "w"}]
    assert len(rt.read_responses(setup["responses"])) == 7


def test_each_conversation_is_recorded(tmp_path, setup):
    gen.generate("main", client=client(tmp_path), jobs=1, **setup)
    lines = [json.loads(s) for s in setup["log"].read_text(encoding="utf-8").splitlines()]
    assert sorted(r["id"] for r in lines) == [c["id"] for c in gen.plan("main")]
    r = next(r for r in lines if r["id"] == "R2-1")
    assert r["model"] == "prov/some-model" and r["client_version"] == "9.9.9" and r["exit"] == 0
    assert r["prompt_file"] == "R2.txt" and len(r["prompt_sha256"]) == 64
    assert set(r["inputs_sha256"]) == {"paper.md", "verify.py"}
    assert r["inputs_unchanged"] is True and r["files_after"] == ["paper.md", "verify.py"]
    assert r["response"] == "R2-1-prov_some-model-2026-11-15.txt" and len(r["response_sha256"]) == 64
    assert r["started"] <= r["ended"]


def test_a_model_that_writes_in_its_folder_is_recorded_not_hidden(tmp_path, setup):
    extra = "open('paper.md', 'a').write('x'); open('note.txt', 'w').write('y')"
    records = gen.generate("R3", client=client(tmp_path, extra), jobs=1, require_main=False, **setup)
    assert records[0]["inputs_unchanged"] is False
    assert records[0]["files_after"] == ["note.txt", "paper.md", "verify.py"]
    # the next conversation still starts from the files as released
    assert setup["files"][0].read_text(encoding="utf-8") == "content of paper.md\n"


def test_no_conversation_is_run_twice(tmp_path, setup):
    gen.generate("main", client=client(tmp_path), jobs=2, **setup)
    with pytest.raises(SystemExit, match="already"):
        gen.generate("main", client=client(tmp_path), jobs=2, **setup)
    assert len(setup["log"].read_text(encoding="utf-8").splitlines()) == 7


def test_a_failed_conversation_is_stored_and_not_retried(tmp_path, setup):
    records = gen.generate("R3", client=client(tmp_path, "raise SystemExit(3)"), jobs=1,
                           require_main=False, **setup)
    assert records[0]["exit"] == 3
    assert (setup["responses"] / records[0]["response"]).exists()


def test_r3_runs_only_after_the_seven(tmp_path, setup):
    with pytest.raises(SystemExit, match="R3 runs after"):
        gen.generate("R3", client=client(tmp_path), jobs=1, **setup)
    gen.generate("main", client=client(tmp_path), jobs=4, **setup)
    assert len(gen.generate("R3", client=client(tmp_path), jobs=1, **setup)) == 1

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
print("dir-is-the-real-path:" + str("--dir" in sys.argv and sys.argv[sys.argv.index("--dir") + 1] == here))
print("config:" + os.path.basename(os.environ.get("OPENCODE_CONFIG", "none")))
tmp = os.path.realpath(os.environ.get("TMPDIR", ""))
print("own-empty-tmp:" + str(os.path.isdir(tmp) and os.listdir(tmp) == [] and tmp != here
                             and not here.startswith(tmp + os.sep)
                             and os.path.basename(tmp) == "tmp" and os.path.basename(here) == "work"
                             and os.path.dirname(tmp) == os.path.dirname(here)))
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
            "log": tmp_path / "generation.jsonl", "model": "prov/some-model", "date": "2026-11-15",
            "runs": tmp_path / "runs"}


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
    # The second launch: the client took the folder for a directory outside its project and
    # rejected the model's reads, and the model had a shell. The folder is named by its real path,
    # and the agent is one that only reads.
    assert "dir-is-the-real-path:True" in text
    assert "--agent|redteam" in text and "config:opencode.json" in text
    # The client lets its agents read its own temporary directory, which held a package of the
    # blind review and two scripts a model wrote in the second launch. Each call gets an empty one.
    assert "own-empty-tmp:True" in text
    assert "--pure" in text and "prov/some-model" in text and "--auto" not in text
    assert rt.parse_response(text) == [{"line": 1, "old": "a", "new": "b", "why": "w"}]
    assert len(rt.read_responses(setup["responses"])) == 7


def test_the_agent_only_reads():
    config = json.loads(gen.CONFIG.read_text(encoding="utf-8"))
    agent = config["agent"][gen.AGENT]
    # `skill`: in the probe the model loaded the skills of the author's own configuration.
    for tool in ("bash", "edit", "write", "webfetch", "task", "skill"):
        assert agent["tools"][tool] is False
    for what in ("bash", "edit", "webfetch", "external_directory", "skill"):
        assert agent["permission"][what] == "deny"
    assert "prompt" not in agent  # nothing is said to the model besides the prompt of the protocol


def test_the_record_names_the_agent_and_its_configuration(tmp_path, setup):
    records = gen.generate("R3", client=client(tmp_path), jobs=1, require_main=False, **setup)
    assert records[0]["agent"] == "redteam" and len(records[0]["config_sha256"]) == 64


def test_the_probe_uses_toy_files_and_writes_no_response(tmp_path, setup):
    out = tmp_path / "probes"
    record = gen.probe(client=client(tmp_path), model="prov/m", out=out, runs=tmp_path / "runs")
    text = (out / record["response"]).read_text(encoding="utf-8")
    assert "cwd-files:toy.md" in text and "--agent|redteam" in text
    assert "polar" not in text
    assert not setup["responses"].exists()
    assert gen.PROBE_WORD not in gen.PROBE_PROMPT  # the word is only in the file, far past its start


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


def test_each_session_has_its_own_folder_outside_the_repository_and_it_is_kept(tmp_path, setup):
    extra = "open(os.path.join(os.environ['TMPDIR'], 'check.py'), 'w').write('x')"
    records = gen.generate("R3", client=client(tmp_path, extra), jobs=1, require_main=False, **setup)
    session = setup["runs"] / records[0]["session"]
    assert records[0]["session"].startswith("R3-1-")
    assert sorted(p.name for p in session.iterdir()) == ["tmp", "work"]
    assert sorted(p.name for p in (session / "work").iterdir()) == ["paper.md", "verify.py"]
    # what a model leaves in its temporary directory is recorded, and still there to be read
    assert records[0]["tmp_files_after"] == ["check.py"]
    assert (session / "tmp" / "check.py").read_text() == "x"


def test_sessions_never_run_inside_a_repository(tmp_path, setup):
    (tmp_path / "repo" / ".git").mkdir(parents=True)
    setup["runs"] = tmp_path / "repo" / "redteam" / "runs"
    with pytest.raises(SystemExit, match="inside a git repository"):
        gen.generate("R3", client=client(tmp_path), jobs=1, require_main=False, **setup)
    assert not setup["responses"].exists() or not list(setup["responses"].iterdir())


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


def test_r2_can_be_asked_once_more_and_the_first_response_stays(tmp_path, setup):
    """Deviation 8: the R2 conversation of the third launch returned nothing; it is asked again once,
    as conversation R2-2, and the first response is kept and read with it."""
    assert [c["id"] for c in gen.plan("R2-again")] == ["R2-2"]
    with pytest.raises(SystemExit, match="R2-1"):
        gen.generate("R2-again", client=client(tmp_path), jobs=1, **setup)
    gen.generate("main", client=client(tmp_path), jobs=4, **setup)
    first = next(p for p in setup["responses"].iterdir() if p.name.startswith("R2-1-"))
    before = first.read_bytes()
    records = gen.generate("R2-again", client=client(tmp_path), jobs=1, **setup)
    assert records[0]["id"] == "R2-2" and records[0]["prompt_file"] == "R2.txt"
    assert first.read_bytes() == before
    assert rt.part_of(records[0]["response"]) == ("R2", 2)
    with pytest.raises(SystemExit, match="already"):
        gen.generate("R2-again", client=client(tmp_path), jobs=1, **setup)


def test_r3_runs_only_after_the_seven(tmp_path, setup):
    with pytest.raises(SystemExit, match="R3 runs after"):
        gen.generate("R3", client=client(tmp_path), jobs=1, **setup)
    gen.generate("main", client=client(tmp_path), jobs=4, **setup)
    assert len(gen.generate("R3", client=client(tmp_path), jobs=1, **setup)) == 1

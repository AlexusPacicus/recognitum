"""Generate the red team's responses: one fresh conversation per call of the client (section 4).

    python redteam/generate.py main --model PROVIDER/MODEL   # R1-1 to R1-6 and R2, at the same time
    python redteam/generate.py R3 --model PROVIDER/MODEL --output-max 512000 --timeout 10800
                                                             # deviation 2: only after the seven; cap: deviation 9
    python redteam/generate.py main --model PROVIDER/MODEL --dry-run   # prints the commands, calls nothing
    python redteam/generate.py R2-third --model PROVIDER/MODEL --output-max 512000 --timeout 10800
                                                             # deviation 9: R2-3, once

    python redteam/generate.py probe --model PROVIDER/MODEL  # a toy file: what the agent can do

Run by the author. Each conversation:
- has a session folder of its own beside the repository, never inside it (`--runs`), kept
  afterwards: `work`, which holds two files and nothing else, the manuscript and the verifier's
  source, copied from the case; and `tmp`, empty, given to the client as its temporary directory;
- is one call of `opencode run`, so one new session, with the prompt of `redteam/prompts` sent as
  written and the two files attached; the agent is the one of `redteam/opencode.json`, which reads
  and has no shell, no edit, no network, no subagent and no skill; `--pure` (no external plugin)
  and never `--auto` (no permission is approved for it);
- has its output stored as returned in `redteam/responses`, and one line in
  `redteam/generation.jsonl`: the model, the client and its version, the times, the exit code, the
  hashes of the prompt, of the two files and of the response, and what the folder held afterwards.

Nothing is run twice: a conversation whose response file exists is an error, and a conversation
that fails is stored as it ended. This script reads no response and judges none.

What it does not guarantee: the client is an agent, not a chat. The folder and the flags above
limit what it is given, not what it could reach; the record shows whether it wrote in its folder.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HERE = REPO / "redteam"
FILES = [REPO / "case" / "paper" / "polar-projector-paper.md", REPO / "case" / "tools" / "verify_paper_tables.py"]
PROMPTS = HERE / "prompts"
RESPONSES = HERE / "responses"
LOG = HERE / "generation.jsonl"
CONFIG = HERE / "opencode.json"
AGENT = "redteam"
PROBES = HERE / "probes"
RUNS = REPO.parent / "recognitum-redteam-runs"  # beside the repository, never inside it
_lock = threading.Lock()


def plan(which: str) -> list[dict]:
    if which == "main":
        return [{"id": f"R1-{k}", "part": "R1"} for k in range(1, 7)] + [{"id": "R2-1", "part": "R2"}]
    if which == "R3":
        return [{"id": "R3-1", "part": "R3"}]
    if which == "R2-again":  # deviation 8: once, after R2-1 returned nothing
        return [{"id": "R2-2", "part": "R2"}]
    if which == "R2-third":  # deviation 9: once, with the output cap of the model
        return [{"id": "R2-3", "part": "R2"}]
    raise ValueError(which)


# Deviation 9: the client caps a reply at min(the model's output limit, 32000) unless this variable
# is set; R2-1 and R2-2 spent the 32000 on reasoning and ended on `length` with no text. The
# catalogue of the client gives minimax-m3.1-flash-free an output limit of 512000.
OUTPUT_MAX_VAR = "OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX"
R2_THIRD_OUTPUT_MAX = 512000
# Deviation 9, the author's decision before R3 runs: R3 has the same cap.
REQUIRED_OUTPUT_MAX = {"R2-third": R2_THIRD_OUTPUT_MAX, "R3": R2_THIRD_OUTPUT_MAX}


def response_name(conversation_id: str, model: str, date: str) -> str:
    return f"{conversation_id}-{model.replace('/', '_')}-{date}.txt"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def command(client: str, model: str, conversation_id: str, prompt: str, names: list[str],
            folder: str = "<folder>") -> list[str]:
    # The message comes before the options: `-f` takes a list and would take the message too.
    # The folder is named in full: the client does not resolve an attached file against the
    # directory it is started in (the first launch ended on `File not found` for a bare name).
    # The agent is the one of `redteam/opencode.json`: it reads, and has no shell, no edit, no
    # network and no subagent (in the second launch the model had a shell).
    cmd = [client, "run", prompt, "--pure", "--agent", AGENT, "-m", model, "--title", conversation_id,
           "--dir", folder]
    for n in names:
        cmd += ["-f", f"{folder}/{n}"]
    return cmd


def check_runs(runs: Path) -> Path:
    """The folder of the sessions, by its real path. It is never inside a git repository: the
    client takes the repository a folder is in for its project, and the model could read all of it."""
    runs = Path(runs).resolve()
    inside = [p for p in (runs, *runs.parents) if (p / ".git").exists()]
    if inside:
        raise SystemExit(f"{runs} is inside a git repository ({inside[0]}): no session runs there")
    runs.mkdir(parents=True, exist_ok=True)
    return runs


def _call(client: str, model: str, title: str, prompt: str, contents: dict[str, bytes], timeout,
          runs: Path, output_max: int | None = None) -> dict:
    """One call of the client, in a session folder of its own that is kept afterwards:
    `work`, which holds `contents` and nothing else, and `tmp`, empty, its temporary directory."""
    # Real paths: the client takes a folder reached through a symbolic link for a directory outside
    # its project, and rejects the reads of the model there (the second launch).
    session = Path(tempfile.mkdtemp(prefix=f"{title}-{dt.datetime.now():%Y%m%dT%H%M%S}-", dir=runs)).resolve()
    folder, scratch = session / "work", session / "tmp"
    folder.mkdir()
    # The client lets its agents read its own temporary directory. The shared one held a package of
    # the blind review, so each call gets an empty one of its own.
    scratch.mkdir()
    for name, data in contents.items():
        (folder / name).write_bytes(data)
    before = {name: _sha(data) for name, data in contents.items()}
    env = dict(os.environ, PWD=str(folder), TMPDIR=str(scratch), OPENCODE_CONFIG=str(CONFIG))
    env.pop(OUTPUT_MAX_VAR, None)  # the cap is the one given here, or the client's own: never inherited
    if output_max is not None:
        env[OUTPUT_MAX_VAR] = str(output_max)
    started = _now()
    try:
        p = subprocess.run(command(client, model, title, prompt, sorted(before), str(folder)),
                           cwd=folder, env=env,
                           stdin=subprocess.DEVNULL, capture_output=True, timeout=timeout)
        out, err, code = p.stdout, p.stderr, p.returncode
    except subprocess.TimeoutExpired as exc:
        out, err, code = exc.stdout or b"", exc.stderr or b"", "timeout"
    ended = _now()
    after = sorted(x.relative_to(folder).as_posix() for x in folder.rglob("*") if x.is_file())
    unchanged = all((folder / n).is_file() and _sha((folder / n).read_bytes()) == h
                    for n, h in before.items())
    tmp_after = sorted(x.relative_to(scratch).as_posix() for x in scratch.rglob("*") if x.is_file())
    return {"out": out, "err": err,
            "record": {"model": model, "client": Path(client).name, "agent": AGENT, "session": session.name,
                       "config_sha256": _sha(CONFIG.read_bytes()), "output_token_max": output_max,
                       "timeout": timeout, "started": started, "ended": ended,
                       "exit": code, "prompt_sha256": _sha(prompt.encode("utf-8")),
                       "inputs_sha256": before, "inputs_unchanged": unchanged, "files_after": after,
                       "tmp_files_after": tmp_after, "response_sha256": _sha(out), "stderr_sha256": _sha(err),
                       "stderr_tail": err.decode("utf-8", "replace")[-600:]}}


def _one(conv: dict, *, client, model, date, files, prompts, responses, log, version, timeout, runs,
         output_max) -> dict:
    prompt_file = Path(prompts) / f"{conv['part']}.txt"
    prompt = prompt_file.read_text(encoding="utf-8").strip()
    name = response_name(conv["id"], model, date)
    done = _call(client, model, conv["id"], prompt, {Path(f).name: Path(f).read_bytes() for f in files}, timeout,
                 runs, output_max)
    (Path(responses) / name).write_bytes(done["out"])
    # What the client printed beside the response: the tools the model called and what they gave.
    traces = Path(log).parent / "traces"
    traces.mkdir(exist_ok=True)
    (traces / name).write_bytes(done["err"])
    record = {"id": conv["id"], "part": conv["part"], "client_version": version,
              "prompt_file": prompt_file.name, "response": name, **done["record"]}
    with _lock, Path(log).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


PROBE_WORD = "quokka"
PROBE_PROMPT = ("This is a test of the tools you have, on a toy file. Answer four things, each on its own "
                "line. 1: the single word on line 850 of the attached file toy.md. 2: run the shell command "
                "`echo shell-works` and say whether you could. 3: read the file /etc/hosts and say whether "
                "you could. 4: create a file named made.txt in your folder and say whether you could.")


def probe(*, client: str, model: str, out: Path, runs: Path, timeout: float = 600) -> dict:
    """One conversation on a toy file, to see what the agent can do. It is not a conversation of
    the red team: neither the manuscript nor the verifier is sent, and no response is written."""
    toy = "".join(f"line {k}: {PROBE_WORD if k == 850 else 'nothing here'}\n" for k in range(1, 1201))
    done = _call(client, model, "probe", PROBE_PROMPT, {"toy.md": toy.encode("utf-8")}, timeout, check_runs(runs))
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    (out / f"probe-{stamp}.txt").write_bytes(done["out"])
    (out / f"probe-{stamp}.stderr.txt").write_bytes(done["err"])
    record = {"id": "probe", "response": f"probe-{stamp}.txt", **done["record"]}
    with (out / "probes.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def generate(which: str, *, client: str, model: str, date: str, files, prompts, responses, log, runs,
             jobs: int = 7, timeout: float = 1800, require_main: bool = True,
             output_max: int | None = None) -> list[dict]:
    runs = check_runs(runs)
    responses = Path(responses)
    responses.mkdir(parents=True, exist_ok=True)
    existing = {f.name.split("-")[0] + "-" + f.name.split("-")[1] for f in responses.iterdir()
                if f.is_file() and not f.name.startswith(".")}
    convs = plan(which)
    again = sorted(c["id"] for c in convs if c["id"] in existing)
    if again:
        raise SystemExit(f"already generated, and nothing is run twice: {', '.join(again)}")
    if which == "R2-again" and "R2-1" not in existing:
        raise SystemExit("R2-2 is a second asking: R2-1 has not been generated")
    if which == "R2-third" and "R2-2" not in existing:
        raise SystemExit("R2-3 is a third asking: R2-2 has not been generated")
    if which in REQUIRED_OUTPUT_MAX and output_max != REQUIRED_OUTPUT_MAX[which]:
        raise SystemExit(f"{which} runs with --output-max {REQUIRED_OUTPUT_MAX[which]} (deviation 9), not {output_max}")
    if which == "R3" and require_main:
        lacking = sorted(c["id"] for c in plan("main") if c["id"] not in existing)
        if lacking:
            raise SystemExit(f"R3 runs after the seven conversations of section 4; missing: {', '.join(lacking)}")
    version = subprocess.run([client, "--version"], capture_output=True, text=True).stdout.strip()
    kw = dict(client=client, model=model, date=date, files=files, prompts=prompts, responses=responses,
              log=log, version=version, timeout=timeout, runs=runs, output_max=output_max)
    with ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
        return list(pool.map(lambda c: _one(c, **kw), convs))


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("which", choices=["main", "R3", "R2-again", "R2-third", "probe"])
    ap.add_argument("--model", required=True, help="as the client names it: provider/model")
    ap.add_argument("--client", default="opencode")
    ap.add_argument("--jobs", type=int, default=7, help="conversations at the same time")
    ap.add_argument("--timeout", type=float, default=1800, help="seconds for one conversation")
    ap.add_argument("--output-max", type=int, default=None,
                    help=f"tokens of one reply, reasoning included ({OUTPUT_MAX_VAR}); unset: the client's own cap")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--runs", default=str(RUNS), help="folder of the sessions, outside any repository")
    args = ap.parse_args(argv)
    client = shutil.which(args.client) or args.client
    if args.which == "probe":
        r = probe(client=client, model=args.model, out=PROBES, runs=Path(args.runs), timeout=args.timeout)
        print(f"exit={r['exit']} files afterwards: {r['files_after']}")
        print(f"files in its temporary directory afterwards: {r['tmp_files_after']}")
        trace = (PROBES / r["response"].replace(".txt", ".stderr.txt")).read_text(encoding="utf-8",
                                                                                  errors="replace")
        plain = re.sub(r"\x1b\[[0-9;]*m", "", trace)  # the client colours its lines
        print("tools the model called:", sorted(set(re.findall(r"^\s*[→✱✗$] ?(\w+)", plain, re.M))))
        print("directories outside its folder that the client lets it read:")
        for p in sorted(set(re.findall(r'"external_directory","pattern":"([^"]+)","action":"allow"', trace))
                        | set(re.findall(r'"pattern":"([^"]+)","action":"allow"', trace))):
            print("   ", p)
        print(f"--- what the model answered (redteam/probes/{r['response']}):")
        print((PROBES / r["response"]).read_text(encoding="utf-8", errors="replace"))
        print("--- what the client printed beside it:")
        print((PROBES / r["response"].replace(".txt", ".stderr.txt")).read_text(encoding="utf-8",
                                                                               errors="replace")[-3000:])
        return
    if args.dry_run:
        for c in plan(args.which):
            cmd = command(client, args.model, c["id"], f"<redteam/prompts/{c['part']}.txt>",
                          sorted(f.name for f in FILES))
            print(c["id"], "->", response_name(c["id"], args.model, dt.date.today().isoformat()))
            print("   ", " ".join(cmd))
        return
    records = generate(args.which, client=client, model=args.model, date=dt.date.today().isoformat(),
                       files=FILES, prompts=PROMPTS, responses=RESPONSES, log=LOG, jobs=args.jobs,
                       timeout=args.timeout, runs=Path(args.runs), output_max=args.output_max)
    for r in records:
        note = "" if r["inputs_unchanged"] and len(r["files_after"]) == len(FILES) else "  WROTE IN ITS FOLDER"
        print(f"{r['id']} exit={r['exit']} -> redteam/responses/{r['response']}{note}")


if __name__ == "__main__":
    sys.exit(main())

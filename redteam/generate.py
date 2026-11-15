"""Generate the red team's responses: one fresh conversation per call of the client (section 4).

    python redteam/generate.py main --model PROVIDER/MODEL   # R1-1 to R1-6 and R2, at the same time
    python redteam/generate.py R3 --model PROVIDER/MODEL     # deviation 2: only after the seven
    python redteam/generate.py main --model PROVIDER/MODEL --dry-run   # prints the commands, calls nothing

Run by the author. Each conversation:
- starts in a new temporary folder that holds two files and nothing else, the manuscript and the
  verifier's source, copied from the case;
- is one call of `opencode run`, so one new session, with the prompt of `redteam/prompts` sent as
  written and the two files attached; `--pure` (no external plugin) and never `--auto` (no
  permission is approved for it);
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
_lock = threading.Lock()


def plan(which: str) -> list[dict]:
    if which == "main":
        return [{"id": f"R1-{k}", "part": "R1"} for k in range(1, 7)] + [{"id": "R2-1", "part": "R2"}]
    if which == "R3":
        return [{"id": "R3-1", "part": "R3"}]
    raise ValueError(which)


def response_name(conversation_id: str, model: str, date: str) -> str:
    return f"{conversation_id}-{model.replace('/', '_')}-{date}.txt"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def command(client: str, model: str, conversation_id: str, prompt: str, names: list[str]) -> list[str]:
    # The message comes before the options: `-f` takes a list and would take the message too.
    cmd = [client, "run", prompt, "--pure", "-m", model, "--title", conversation_id]
    for n in names:
        cmd += ["-f", n]
    return cmd


def _one(conv: dict, *, client, model, date, files, prompts, responses, log, version, timeout) -> dict:
    prompt_file = Path(prompts) / f"{conv['part']}.txt"
    prompt = prompt_file.read_text(encoding="utf-8").strip()
    name = response_name(conv["id"], model, date)
    with tempfile.TemporaryDirectory(prefix="redteam-") as tmp:
        folder = Path(tmp)
        for f in files:
            shutil.copyfile(f, folder / Path(f).name)
        before = {Path(f).name: _sha((folder / Path(f).name).read_bytes()) for f in files}
        started = _now()
        try:
            p = subprocess.run(command(client, model, conv["id"], prompt, sorted(before)), cwd=folder,
                               stdin=subprocess.DEVNULL, capture_output=True, timeout=timeout)
            out, err, code = p.stdout, p.stderr, p.returncode
        except subprocess.TimeoutExpired as exc:
            out, err, code = exc.stdout or b"", exc.stderr or b"", "timeout"
        ended = _now()
        after = sorted(x.relative_to(folder).as_posix() for x in folder.rglob("*") if x.is_file())
        unchanged = all((folder / n).is_file() and _sha((folder / n).read_bytes()) == h
                        for n, h in before.items())
    (Path(responses) / name).write_bytes(out)
    record = {"id": conv["id"], "part": conv["part"], "model": model, "client": Path(client).name,
              "client_version": version, "started": started, "ended": ended, "exit": code,
              "prompt_file": prompt_file.name, "prompt_sha256": _sha(prompt.encode("utf-8")),
              "inputs_sha256": before, "inputs_unchanged": unchanged, "files_after": after,
              "response": name, "response_sha256": _sha(out),
              "stderr_tail": err.decode("utf-8", "replace")[-600:]}
    with _lock, Path(log).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def generate(which: str, *, client: str, model: str, date: str, files, prompts, responses, log,
             jobs: int = 7, timeout: float = 1800, require_main: bool = True) -> list[dict]:
    responses = Path(responses)
    responses.mkdir(parents=True, exist_ok=True)
    existing = {f.name.split("-")[0] + "-" + f.name.split("-")[1] for f in responses.iterdir()
                if f.is_file() and not f.name.startswith(".")}
    convs = plan(which)
    again = sorted(c["id"] for c in convs if c["id"] in existing)
    if again:
        raise SystemExit(f"already generated, and nothing is run twice: {', '.join(again)}")
    if which == "R3" and require_main:
        lacking = sorted(c["id"] for c in plan("main") if c["id"] not in existing)
        if lacking:
            raise SystemExit(f"R3 runs after the seven conversations of section 4; missing: {', '.join(lacking)}")
    version = subprocess.run([client, "--version"], capture_output=True, text=True).stdout.strip()
    kw = dict(client=client, model=model, date=date, files=files, prompts=prompts, responses=responses,
              log=log, version=version, timeout=timeout)
    with ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
        return list(pool.map(lambda c: _one(c, **kw), convs))


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("which", choices=["main", "R3"])
    ap.add_argument("--model", required=True, help="as the client names it: provider/model")
    ap.add_argument("--client", default="opencode")
    ap.add_argument("--jobs", type=int, default=7, help="conversations at the same time")
    ap.add_argument("--timeout", type=float, default=1800, help="seconds for one conversation")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    client = shutil.which(args.client) or args.client
    if args.dry_run:
        for c in plan(args.which):
            cmd = command(client, args.model, c["id"], f"<redteam/prompts/{c['part']}.txt>",
                          sorted(f.name for f in FILES))
            print(c["id"], "->", response_name(c["id"], args.model, dt.date.today().isoformat()))
            print("   ", " ".join(cmd))
        return
    records = generate(args.which, client=client, model=args.model, date=dt.date.today().isoformat(),
                       files=FILES, prompts=PROMPTS, responses=RESPONSES, log=LOG, jobs=args.jobs,
                       timeout=args.timeout)
    for r in records:
        note = "" if r["inputs_unchanged"] and len(r["files_after"]) == len(FILES) else "  WROTE IN ITS FOLDER"
        print(f"{r['id']} exit={r['exit']} -> redteam/responses/{r['response']}{note}")


if __name__ == "__main__":
    sys.exit(main())

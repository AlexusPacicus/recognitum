"""The red team's edits: from the stored responses to one results line per edit (protocol, section 4).

    python redteam/run.py list     # reads redteam/responses, writes redteam/edits.jsonl, runs nothing
    python redteam/run.py run R1   # validity, then both detectors, on the edits of one part
    python redteam/run.py run R2   # refuses to start unless redteam/rulings.csv rules on every edit
    python redteam/run.py run R3   # deviation 2: reported apart

A response is stored by the author as the model returned it, in `redteam/responses`, in a file
whose name starts with its part and conversation: `R1-1` to `R1-6`, `R2`, `R3`. This script writes
no response and repairs no edit: an edit that does not apply is counted as invalid, with its reason.

The author's rulings on part R2 are in `redteam/rulings.csv`, with the columns `edit_id`, `ruling`
(`yes`: the edit makes the project state something false about a numerical result; `no`) and `note`.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

HERE = REPO / "redteam"
RESPONSES = HERE / "responses"
EDITS = HERE / "edits.jsonl"
RULINGS = HERE / "rulings.csv"
PARTS = ("R1", "R2", "R3")
MANUSCRIPT_ONLY = ("R1", "R3")  # R3 has the validity of R1 (deviation 2)

MINUS = "−"
NUMBER = re.compile(r"[-+]?\d+(?:\.\d+)?")
THOUSANDS = re.compile(r"(?<=\d),(?=\d{3}(?!\d))")
HEADING = re.compile(r"^#+ ")
SECTION_HEADING = re.compile(r"^#{2,3} (.*)$")


class DoesNotApply(Exception):
    """The edit cannot be applied as the model wrote it."""


# --------------------------------------------------------------------------- reading a response


def parse_response(text: str) -> list[dict]:
    """The JSON list of a response as returned: bare, in a fenced block, or with prose around.

    The client prints what the model says while it works, before its answer, so the text may hold
    other brackets. The list is the last JSON list of objects in the text that is not inside
    another one: an answer given twice counts as its last version."""
    decoder = json.JSONDecoder()
    found, k = [], 0
    while (k := text.find("[", k)) != -1:
        try:
            value, length = decoder.raw_decode(text[k:])
        except ValueError:
            k += 1
            continue
        if isinstance(value, list) and value and all(isinstance(x, dict) for x in value):
            found.append(value)
        k += length
    if not found:
        raise ValueError("no JSON list of objects in the response")
    return found[-1]


def part_of(name: str) -> tuple[str, int]:
    m = re.match(r"(R[123])(?:-(\d+))?(?!\d)", name)
    if not m:
        raise ValueError(f"{name}: the file name does not start with R1-<n>, R2 or R3")
    return m.group(1), int(m.group(2) or 1)


def edits_of(part: str, conversation: int, items: list[dict]) -> list[dict]:
    return [dict(item, edit_id=f"{part}-{conversation}-{k:02d}", part=part, conversation=conversation)
            for k, item in enumerate(items, start=1)]


def read_responses(folder: Path = RESPONSES, unreadable: list | None = None) -> list[dict]:
    """The edits of every stored response. A response with no JSON list gives no edit: its file
    name is added to `unreadable`, and it is not repaired."""
    out = []
    for f in sorted(p for p in folder.iterdir() if p.is_file() and not p.name.startswith(".")):
        part, conversation = part_of(f.name)
        try:
            items = parse_response(f.read_text(encoding="utf-8"))
        except ValueError:
            if unreadable is not None:
                unreadable.append(f.name)
            continue
        out += [dict(e, response=f.name) for e in edits_of(part, conversation, items)]
    ids = [e["edit_id"] for e in out]
    if len(ids) != len(set(ids)):
        raise ValueError("two response files give the same part and conversation")
    return out


# --------------------------------------------------------------------------- placing an edit


def locate(text: str, line, old) -> tuple[int, int]:
    """Offsets of `old` in the text: it must appear exactly once on the given line."""
    try:
        n = int(line)
    except (TypeError, ValueError):
        raise DoesNotApply("`line` is not a whole number") from None
    if not isinstance(old, str) or old == "":
        raise DoesNotApply("`old` is empty")
    lines = text.split("\n")
    if not 1 <= n <= len(lines):
        raise DoesNotApply("no such line")
    found = lines[n - 1].count(old)
    if found != 1:
        raise DoesNotApply(f"`old` appears {found} times on the line")
    start = sum(len(x) + 1 for x in lines[: n - 1]) + lines[n - 1].index(old)
    return start, start + len(old)


def resolve_file(root: Path, name) -> str:
    """The file an R2 edit names, as a path relative to the case: by its path, or by a name that
    only one file of the case has."""
    if not isinstance(name, str) or not name.strip():
        raise DoesNotApply("no such file")
    root = Path(root).resolve()
    direct = (root / name).resolve()
    if root not in direct.parents:
        raise DoesNotApply("the file is outside the case")
    if direct.is_file():
        return direct.relative_to(root).as_posix()
    hits = [p for p in root.rglob(Path(name).name) if p.is_file() and "__pycache__" not in p.parts]
    if not hits:
        raise DoesNotApply("no such file")
    if len(hits) > 1:
        raise DoesNotApply(f"{len(hits)} files have that name")
    return hits[0].relative_to(root).as_posix()


# --------------------------------------------------------------------------- validity (section 4)


def _norm(s: str) -> str:
    return THOUSANDS.sub("", s.replace(MINUS, "-"))


def one_number(old: str, new: str) -> tuple[str, str] | None:
    """The old and the new number when the edit changes exactly one number and nothing else."""
    a, b = _norm(old), _norm(new)
    na, nb = NUMBER.findall(a), NUMBER.findall(b)
    if len(na) != len(nb) or NUMBER.split(a) != NUMBER.split(b):
        # A sign that appears or disappears moves between the number and the text around it.
        strip = lambda s: re.sub(r"[-+](?=\d)", "", s)  # noqa: E731
        if len(na) != len(nb) or NUMBER.split(strip(a)) != NUMBER.split(strip(b)):
            return None
    changed = [(x, y) for x, y in zip(na, nb) if x != y]
    return changed[0] if len(changed) == 1 else None


def differs(old_number: str, new_number: str) -> bool:
    """Whether the two differ when both are rounded to the decimals of the old one."""
    d = len(old_number.split(".")[1]) if "." in old_number else 0
    return round(float(new_number), d) != round(float(old_number), d)


def section_of(text: str, line: int) -> str:
    section = ""
    for raw in text.split("\n")[:line]:
        m = SECTION_HEADING.match(raw)
        if m:
            section = m.group(1).strip()
    return section


def validity_r1(text: str, edit: dict) -> str:
    """Empty when the edit is a valid R1 edit of the manuscript, otherwise the rule that fails."""
    for key in ("line", "old", "new"):
        if key not in edit:
            return f"the edit has no `{key}`"
    if not isinstance(edit["new"], str):
        return "`new` is not text"
    try:
        locate(text, edit["line"], edit["old"])
    except DoesNotApply as exc:
        return str(exc)
    n = int(edit["line"])
    if HEADING.match(text.split("\n")[n - 1]):
        return "on a heading"
    if section_of(text, n) == "References":
        return "inside the References section"
    pair = one_number(edit["old"], edit["new"])
    if pair is None:
        return "does not change exactly one number"
    if not differs(*pair):
        return "the new number equals the old one at the old one's decimals"
    return ""


# --------------------------------------------------------------------------- rulings (R2)


def read_rulings(path: Path = RULINGS) -> dict[str, bool]:
    if not Path(path).exists():
        return {}
    out = {}
    with Path(path).open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            ruling = (r.get("ruling") or "").strip().lower()
            if ruling not in ("yes", "no"):
                raise ValueError(f"{r.get('edit_id')}: the ruling is `{ruling}`, not yes or no")
            out[r["edit_id"].strip()] = ruling == "yes"
    return out


def missing_rulings(edit_ids: list[str], rulings: dict[str, bool]) -> list[str]:
    return [i for i in edit_ids if i not in rulings]


# --------------------------------------------------------------------------- results lines


def result_row(edit: dict, *, file: str, reason: str, stratum: str, commit: str, case_hash: str) -> dict:
    return {"mutant_id": edit["edit_id"], "source": "red team", "class": edit["part"],
            "expected": "block", "seed": "", "target": f"{file}:{edit.get('line', '')}",
            "old": edit.get("old", ""), "new": edit.get("new", ""), "stratum": stratum,
            "code_commit": commit, "case_hash": case_hash, "status": "invalid" if reason else "ok",
            "valid": not reason, "invalid_reason": reason, "collision": False}


def _stratum(case, strata: dict, line: int, start_col: int, end_col: int) -> str:
    """The stratum of the figure place the edit touches, or that it touches none."""
    hit = [p for p in case.figure_places if p.line == line and p.start < end_col and start_col < p.end]
    if not hit:
        return "no figure place"
    return "once" if any(strata[p.key] == "once" for p in hit) else "repeated"


def cmd_list(_args) -> None:
    unreadable: list[str] = []
    edits = read_responses(unreadable=unreadable)
    EDITS.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in edits), encoding="utf-8")
    for part in PARTS:
        print(f"{part}: {sum(e['part'] == part for e in edits)} edits")
    for name in unreadable:
        print(f"{name}: no JSON list in the response, 0 edits")
    rulings = read_rulings()
    for e in (e for e in edits if e["part"] == "R2"):
        print(json.dumps({k: e.get(k) for k in ("edit_id", "name", "file", "line", "old", "new", "why")},
                         ensure_ascii=False), "ruled" if e["edit_id"] in rulings else "NOT RULED")


def cmd_run(args) -> None:
    from mutations import core
    from mutations import run as runner

    commit = runner.code_commit()
    dirty = runner.subprocess.run(["git", "status", "--porcelain", "redteam/run.py", "countcheck"],
                                  cwd=REPO, capture_output=True, text=True).stdout.strip()
    if dirty:
        raise SystemExit("redteam/run.py or countcheck/ has uncommitted changes: commit before running")
    control = json.loads(runner.CONTROL.read_text(encoding="utf-8"))
    count = json.loads(runner.COUNT_CONTROL.read_text(encoding="utf-8"))
    if not (control["control_passes"] and count["control_passes"]):
        raise SystemExit("a control does not pass: no edit runs")
    edits = [e for e in read_responses() if e["part"] == args.part]
    case = core.Case()
    strata = core.strata(case.places)

    located: dict[str, tuple[str, int, int] | str] = {}
    for e in edits:
        try:
            file = core.MANUSCRIPT if args.part in MANUSCRIPT_ONLY else resolve_file(core.CASE, e.get("file"))
            if "new" not in e or not isinstance(e["new"], str):
                raise DoesNotApply("the edit has no `new`")
            text = (core.CASE / file).read_text(encoding="utf-8")
            located[e["edit_id"]] = (file, *locate(text, e.get("line"), e.get("old")))
        except DoesNotApply as exc:
            located[e["edit_id"]] = str(exc)
    rulings = read_rulings()
    if args.part == "R2":
        # The author rules before either detector runs on any R2 edit.
        missing = missing_rulings([i for i, v in located.items() if not isinstance(v, str)], rulings)
        if missing:
            raise SystemExit(f"no ruling in {RULINGS.name} for: {', '.join(missing)}. Nothing was run.")

    out = runner.RESULTS / "mutants.csv"
    with out.open(newline="", encoding="utf-8") as fh:
        done = {r["mutant_id"] for r in csv.DictReader(fh)}
    with out.open("a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=runner.COLUMNS)
        for e in edits:
            if e["edit_id"] in done:
                continue
            loc = located[e["edit_id"]]
            file = core.MANUSCRIPT if isinstance(loc, str) else loc[0]
            if isinstance(loc, str):
                reason, stratum = loc, ""
            elif args.part in MANUSCRIPT_ONLY:
                reason = validity_r1(case.text, e)
                line_start = case.line_offset(int(e["line"]))
                stratum = _stratum(case, strata, int(e["line"]), loc[1] - line_start, loc[2] - line_start)
            else:
                reason = "" if rulings[e["edit_id"]] else "the author rules that it states nothing false"
                stratum = str(e.get("name", ""))
            row = result_row(e, file=file, reason=reason, stratum=stratum, commit=commit,
                             case_hash=control["case_hash"])
            if not reason:
                with tempfile.TemporaryDirectory() as tmp:
                    root = runner.make_copy(Path(tmp))
                    path = root / file
                    text = path.read_text(encoding="utf-8")
                    path.write_text(text[: loc[1]] + e["new"] + text[loc[2]:], encoding="utf-8")
                    changed = runner.changed_files(core.CASE, root)
                    if changed != {file}:
                        row.update(status="invalid", valid=False,
                                   invalid_reason=f"files changed: {sorted(changed)}")
                    else:
                        v = runner.run_verifier(root, 10 * control["verifier_t"])
                        c = runner.run_count_check(root, 10 * count["count_t"])
                        timeout = "timeout" in (v["by"], c["by"])
                        row.update(status="timeout" if timeout else "ok",
                                   verifier_exit=v["exit"], verifier_blocked=v["blocked"],
                                   verifier_by=v["by"], verifier_s=v["s"], count_exit=c["exit"],
                                   count_blocked=c["blocked"], count_by=c["by"], count_s=c["s"])
            w.writerow(row)
            fh.flush()
            print(f"{row['mutant_id']} {row['status']} {row['invalid_reason']} "
                  f"verifier={row.get('verifier_by', '') or '-'} count={row.get('count_by', '') or '-'}",
                  flush=True)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    r = sub.add_parser("run")
    r.add_argument("part", choices=PARTS)
    r.set_defaults(fn=cmd_run)
    args = ap.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()

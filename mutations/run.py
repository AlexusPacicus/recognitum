"""Runner: the control, the draws, and one results line per mutant.

    python mutations/run.py control                 # three verifier runs on the unmutated copy; sizes
    python mutations/run.py draw M2 [--n 50]        # writes results/drawn/M2.jsonl
    python mutations/run.py run M2 [--out FILE] [--limit K]

Copies live in a temporary directory outside the repository. The verifier of each copy runs as a
subprocess from the copy's root, with the copy first on PYTHONPATH.
"""

from __future__ import annotations

import argparse
import csv
import filecmp
import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mutations import core  # noqa: E402
from mutations.operators import Mutant, apply_edits, draw  # noqa: E402

RESULTS = core.REPO / "results"
CONTROL = RESULTS / "control" / "control.json"
DRAWN = RESULTS / "drawn"
COLUMNS = ["mutant_id", "source", "class", "expected", "seed", "target", "old", "new", "stratum",
           "code_commit", "case_hash", "status", "valid", "invalid_reason", "collision",
           "verifier_exit", "verifier_blocked", "verifier_by", "verifier_s"]


def code_commit() -> str:
    dirty = subprocess.run(["git", "status", "--porcelain", "mutations"], cwd=core.REPO,
                           capture_output=True, text=True).stdout.strip()
    if dirty:
        raise SystemExit("mutations/ has uncommitted changes: commit before running")
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=core.REPO, capture_output=True,
                          text=True).stdout.strip()


def make_copy(dest: Path) -> Path:
    root = dest / "case"
    shutil.copytree(core.CASE, root, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    return root


def run_verifier(root: Path, timeout: float | None) -> dict:
    env = dict(os.environ, PYTHONPATH=str(root), PYTHONDONTWRITEBYTECODE="1")
    t0 = time.monotonic()
    try:
        p = subprocess.run([sys.executable, core.VERIFIER], cwd=root, env=env, capture_output=True,
                           text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"exit": "", "blocked": "", "by": "timeout", "s": round(time.monotonic() - t0, 3)}
    s = round(time.monotonic() - t0, 3)
    verdict = any(line.startswith("Verdict:") for line in p.stdout.splitlines())
    by = "" if p.returncode == 0 else ("check" if verdict else "crash")
    return {"exit": p.returncode, "blocked": p.returncode != 0, "by": by, "s": s,
            "verdict": next((ln for ln in p.stdout.splitlines() if ln.startswith("Verdict:")), "")}


# --------------------------------------------------------------------------- validity


def changed_files(a: Path, b: Path) -> set[str]:
    out = set()
    for base, other in ((a, b), (b, a)):
        for f in base.rglob("*"):
            if "__pycache__" in f.parts or f.is_dir():
                continue
            rel = f.relative_to(base).as_posix()
            g = other / rel
            if not g.exists() or not filecmp.cmp(f, g, shallow=False):
                out.add(rel)
    return out


def validate(m: Mutant, root: Path) -> str:
    """Empty when valid, otherwise the rule that fails."""
    changed = changed_files(core.CASE, root)
    if changed != {m.file}:
        return f"files changed: {sorted(changed)}"
    original = (core.CASE / m.file).read_text(encoding="utf-8")
    if (root / m.file).read_text(encoding="utf-8") != apply_edits(original, m.edits):
        return "copy differs from the operator's edit"
    if any(original[s:e] == new for s, e, new in m.edits):
        return "new string equals the old one"
    if m.cls == "B1" and not core.agree(m.extra["measured"], m.new.replace(core.MINUS, "-")):
        return "measured value does not agree with the new string"
    return ""


def collision(m: Mutant, published: set[str]) -> bool:
    norm = lambda s: core.THOUSANDS.sub("", s.replace(core.MINUS, "-"))  # noqa: E731
    if m.cls in ("M2", "M2all", "M7", "B1"):
        return norm(m.new) in published
    if m.cls == "M1":
        return m.extra["figure"] in published
    if m.cls == "M4":
        return all(s in published for s in m.extra["strings"])
    return False


def m6_subgroup(root: Path, control_values: list[float]) -> str:
    try:
        checks = core.artifact_checks(root)
    except Exception as exc:  # recorded, never a verdict
        return f"checks raise: {type(exc).__name__}"
    if [v for _, _, v in checks] == control_values:
        return "unread"
    return "read, print still true" if all(core.agree(v, s) for _, s, v in checks) else "read, print now false"


# --------------------------------------------------------------------------- commands


def cmd_control(_args) -> None:
    commit = code_commit()
    with tempfile.TemporaryDirectory() as tmp:
        root = make_copy(Path(tmp))
        runs = [run_verifier(root, None) for _ in range(3)]
    t = statistics.median(r["s"] for r in runs)
    case = core.Case()
    places, figure = case.places, case.figure_places
    n = 50 if t <= 20 else 30
    out = {
        "code_commit": commit, "case_hash": core.case_hash(),
        "verifier_runs": runs, "verifier_t": t,
        "control_passes": all(r["exit"] == 0 for r in runs),
        "N": n,
        "places": len(places), "figure_places": len(figure),
        "short_places": sum(p.short for p in places),
        "m2_every_place": len(figure) * t <= 3600,
        "published_strings": sorted(set(case.published)),
        "checks": [[label, s] for label, s, _ in case.checks],
    }
    CONTROL.parent.mkdir(parents=True, exist_ok=True)
    CONTROL.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k not in ("published_strings", "checks")}, indent=1))
    if not out["control_passes"]:
        raise SystemExit("control does not pass: no mutant runs")


def cmd_draw(args) -> None:
    code_commit()
    control = json.loads(CONTROL.read_text(encoding="utf-8"))
    mutants = draw(core.Case(), args.cls, args.n or control["N"])
    DRAWN.mkdir(parents=True, exist_ok=True)
    (DRAWN / f"{args.cls}.jsonl").write_text("".join(m.to_json() + "\n" for m in mutants), encoding="utf-8")
    print(f"{args.cls}: {len(mutants)} mutants drawn")


def cmd_run(args) -> None:
    commit = code_commit()
    control = json.loads(CONTROL.read_text(encoding="utf-8"))
    if not control["control_passes"]:
        raise SystemExit("control does not pass: no mutant runs")
    published = set(control["published_strings"])
    control_values = [v for _, _, v in core.artifact_checks(core.CASE)]
    mutants = [Mutant.from_json(s) for s in (DRAWN / f"{args.cls}.jsonl").read_text(encoding="utf-8").splitlines()]
    if args.limit:
        mutants = mutants[: args.limit]
    out = Path(args.out) if args.out else RESULTS / "mutants.csv"
    new_file = not out.exists()
    timeout = 10 * control["verifier_t"]
    with out.open("a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        if new_file:
            w.writeheader()
        for m in mutants:
            with tempfile.TemporaryDirectory() as tmp:
                root = make_copy(Path(tmp))
                path = root / m.file
                path.write_text(apply_edits(path.read_text(encoding="utf-8"), m.edits), encoding="utf-8")
                reason = validate(m, root)
                row = {"mutant_id": m.mutant_id, "source": "operator", "class": m.cls, "expected": m.expected,
                       "seed": m.seed, "target": m.target, "old": m.old, "new": m.new, "stratum": m.stratum,
                       "code_commit": commit, "case_hash": control["case_hash"],
                       "valid": not reason, "invalid_reason": reason, "collision": collision(m, published)}
                if m.cls == "M6":
                    row["stratum"] = m6_subgroup(root, control_values)
                    row["expected"] = "block" if row["stratum"] == "read, print now false" else "none"
                if reason:
                    row["status"] = "invalid"
                else:
                    v = run_verifier(root, timeout)
                    row.update(status="timeout" if v["by"] == "timeout" else "ok", verifier_exit=v["exit"],
                               verifier_blocked=v["blocked"], verifier_by=v["by"], verifier_s=v["s"])
            w.writerow(row)
            fh.flush()
            print(f"{m.mutant_id} {row['status']} {row.get('verifier_by', '') or 'pass'}", flush=True)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("control").set_defaults(fn=cmd_control)
    d = sub.add_parser("draw")
    d.add_argument("cls")
    d.add_argument("--n", type=int)
    d.set_defaults(fn=cmd_draw)
    r = sub.add_parser("run")
    r.add_argument("cls")
    r.add_argument("--out")
    r.add_argument("--limit", type=int)
    r.set_defaults(fn=cmd_run)
    args = ap.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()

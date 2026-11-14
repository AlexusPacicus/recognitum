"""The repetition control of section 5: the first five mutants of each class, run twice, give the
same line in the results file, the time aside.

    python analysis/check_repetition.py [results/mutants.csv] [results/repetition.csv]

Prints, per class and detector, whether the repetition agrees. Exit code 1 if any line differs.
"""

import csv
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TIME = {"verifier_s", "count_s", "code_commit"}
DETECTOR_COLUMNS = {
    "verifier": {"verifier_exit", "verifier_blocked", "verifier_by"},
    "count": {"count_exit", "count_blocked", "count_by"},
}


def read(path: Path) -> dict[str, dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return {r["mutant_id"]: r for r in csv.DictReader(fh)}


def main(argv: list[str]) -> int:
    first = read(Path(argv[0]) if argv else REPO / "results" / "mutants.csv")
    again = read(Path(argv[1]) if len(argv) > 1 else REPO / "results" / "repetition.csv")
    bad = 0
    by_class: dict[str, list[str]] = {}
    for mid, row in again.items():
        a = first.get(mid)
        if a is None:
            print(f"  MISSING {mid}: not in the first run")
            bad += 1
            continue
        diff = sorted(k for k in row if k not in TIME and row[k] != a.get(k))
        by_class.setdefault(row["class"], [])
        if diff:
            bad += 1
            by_class[row["class"]].append(f"{mid}: {', '.join(diff)}")
    for cls, problems in sorted(by_class.items()):
        n = sum(1 for r in again.values() if r["class"] == cls)
        for det, cols in DETECTOR_COLUMNS.items():
            differs = [p for p in problems if any(c in p for c in cols)]
            print(f"{cls:6} {det:8} {n} repeated, {len(differs)} differ")
        for p in problems:
            print(f"  DIFFERS {p}")
    print(f"Repetition: {len(again)} lines, {bad} differ")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

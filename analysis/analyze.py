"""Every table of the report, from `results/mutants.csv` (protocol, sections 7 and 8).

    python analysis/analyze.py [--csv results/mutants.csv] [--repetition results/repetition.csv]
                               [--out results/tables.md]

No figure of the report is typed by hand: this script writes them. The only things typed here are
the names of the classes and the predictions of `protocol/PREDICTIONS.md`, restated as words.

What is read besides the results file, and why:
- the case, through `mutations.core`, for the short places of Q1 (they are never the target of a
  mutant, so the results file has no line for them) and to check the figure places against the
  lines of the class with one M2 mutant per figure place.
"""

from __future__ import annotations

import argparse
import csv
import math
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

DETECTORS = ("verifier", "count")
NAMES = {"verifier": "Verifier", "count": "Count check", "either": "At least one of the two"}
TIMES = ("verifier_s", "count_s")

CLASS_ORDER = ["M1", "M2", "M2all", "M4", "M5", "M6", "M7", "B1"]
CLASS_LABEL = {"M2all": "M2, every figure place"}
STRATUM_ORDER = ["all", "once", "repeated", "same section", "different sections", "checked",
                 "construction", "remove", "read, print now false", "read, print still true", "unread"]
# Classes whose targets were drawn as a sample: the Wilson interval describes that draw.
SAMPLED = {"M1", "M2", "M4", "M6", "B1"}
# Classes with a line for the whole class next to the subgroups that were recorded, not allocated.
WHOLE = {"M1", "M7"}
# Results of the count check that follow from its design (protocol, section 2).
COUNT_BY_DESIGN = {"M1", "M2", "M2all", "M4", "M5", "M6", "B1"}
M6_IN_RATE = "read, print now false"
Z95 = 1.959963984540054


# --------------------------------------------------------------------------- reading


def read(path: Path) -> list[dict]:
    with Path(path).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def split_repeats(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """The first line of each mutant is its result; a later line with the same identifier is the
    repetition of section 5."""
    seen: set[str] = set()
    first, again = [], []
    for r in rows:
        (again if r["mutant_id"] in seen else first).append(r)
        seen.add(r["mutant_id"])
    return first, again


def _true(s: str) -> bool:
    return s == "True"


# --------------------------------------------------------------------------- counting


def wilson(k: int, n: int) -> tuple[float, float] | None:
    """Wilson score interval at 95 % for k of n."""
    if n == 0:
        return None
    p = k / n
    d = 1 + Z95 ** 2 / n
    centre = (p + Z95 ** 2 / (2 * n)) / d
    half = Z95 * math.sqrt(p * (1 - p) / n + Z95 ** 2 / (4 * n ** 2)) / d
    return max(0.0, centre - half), min(1.0, centre + half)


def _valid(r: dict) -> bool:
    return r["status"] != "invalid" and _true(r["valid"])


def tally(rows: list[dict]) -> dict:
    """Counts of section 7 for one group of mutants."""
    out = {d: {"valid": 0, "check": 0, "crash": 0, "timeout": 0} for d in (*DETECTORS, "either")}
    out["invalid"] = 0
    for r in rows:
        if not _valid(r):
            out["invalid"] += 1
            continue
        by = {d: r[f"{d}_by"] for d in DETECTORS}
        for d in DETECTORS:
            if by[d] == "timeout":
                out[d]["timeout"] += 1
            else:
                out[d]["valid"] += 1
                if by[d] in ("check", "crash"):
                    out[d][by[d]] += 1
        e = out["either"]
        if "timeout" in by.values():
            e["timeout"] += 1
        else:
            e["valid"] += 1
            if "check" in by.values():
                e["check"] += 1
            elif "crash" in by.values():
                e["crash"] += 1
    return out


def word(cell: dict) -> str:
    """The reporting words of `protocol/definitions.md`."""
    if cell["valid"] == 0:
        return "no valid mutant"
    if cell["check"] == cell["valid"]:
        return "covered"
    if cell["check"] + cell["crash"] == 0:
        return "open"
    return "partial"


def _order(cls: str, stratum: str) -> tuple:
    c = CLASS_ORDER.index(cls) if cls in CLASS_ORDER else len(CLASS_ORDER)
    s = STRATUM_ORDER.index(stratum) if stratum in STRATUM_ORDER else len(STRATUM_ORDER)
    return (c, cls, s, stratum)


def _group(cls: str, stratum: str, rows: list[dict]) -> dict:
    t = tally(rows)
    sampled = cls in SAMPLED
    in_rate = cls != "M6" or stratum == M6_IN_RATE
    g = {"class": cls, "stratum": stratum, "sampled": sampled, "in_rate": in_rate,
         "count_by_design": cls in COUNT_BY_DESIGN, "invalid": t["invalid"], "n": len(rows),
         "expected": sorted({r["expected"] for r in rows})}
    for d in (*DETECTORS, "either"):
        cell = dict(t[d])
        blocked = cell["check"] + cell["crash"]
        cell["interval"] = wilson(blocked, cell["valid"]) if sampled and in_rate else None
        cell["word"] = word(cell)
        if d == "either":
            hit = lambda r: any(r[f"{x}_by"] in ("check", "crash") for x in DETECTORS)  # noqa: E731
        else:
            hit = lambda r, d=d: r[f"{d}_by"] in ("check", "crash")  # noqa: E731
        cell["blocked_no_collision"] = sum(1 for r in rows if _valid(r) and hit(r)
                                           and not _true(r["collision"]))
        g[d] = cell
    return g


def q2(rows: list[dict]) -> list[dict]:
    """One group per class and stratum or subgroup. Classes drawn by strata have no line for the
    whole class: no proportion is pooled over strata of unequal weight."""
    by: dict[tuple[str, str], list[dict]] = {}
    for r in rows:
        by.setdefault((r["class"], r["stratum"]), []).append(r)
        if r["class"] in WHOLE:
            by.setdefault((r["class"], "all"), []).append(r)
    return [_group(c, s, by[(c, s)]) for c, s in sorted(by, key=lambda k: _order(*k))]


def collisions(rows: list[dict]) -> list[dict]:
    return q2([r for r in rows if _true(r["collision"])])


def per_class(rows: list[dict]) -> list[dict]:
    """Valid, invalid and timed-out mutants of every class, whatever they are (section 7)."""
    out = []
    for cls in sorted({r["class"] for r in rows}, key=lambda c: _order(c, "all")):
        mine = [r for r in rows if r["class"] == cls]
        out.append({"class": cls, "lines": len(mine),
                    "valid": sum(_valid(r) for r in mine),
                    "invalid": sum(not _valid(r) for r in mine),
                    "timeout_verifier": sum(r["verifier_by"] == "timeout" for r in mine),
                    "timeout_count": sum(r["count_by"] == "timeout" for r in mine),
                    "collisions": sum(_true(r["collision"]) for r in mine),
                    "commits": sorted({r["code_commit"][:7] for r in mine}),
                    "case_hashes": sorted({r["case_hash"][:12] for r in mine})})
    return out


# --------------------------------------------------------------------------- Q1


def _norm(s: str) -> str:
    return re.sub(r"(?<=\d),(?=\d{3}\b)", "", s.replace("−", "-"))


def q1(rows: list[dict]) -> dict:
    """Figure places and distinct strings by stratum, from the class with one mutant per place."""
    mine = [r for r in rows if r["class"] == "M2all"]
    out = {}
    for name in ("once", "repeated", "all"):
        sel = [r for r in mine if name == "all" or r["stratum"] == name]
        out[name] = {"places": len(sel), "strings": len({_norm(r["old"]) for r in sel})}
    return out


def q1_case() -> dict:
    """The same counts from the case itself, and the short places, which no mutant targets."""
    from mutations import core

    case = core.Case()
    stratum = core.strata(case.places)
    out = {}
    for name in ("once", "repeated", "all"):
        sel = [p for p in case.figure_places if name == "all" or stratum[p.key] == name]
        out[name] = {"places": len(sel), "strings": len({p.string for p in sel})}
    short = [p for p in case.places if p.short]
    out["short"] = {"places": len(short), "strings": len({p.string for p in short})}
    out["places"] = len(case.places)
    return out


# --------------------------------------------------------------------------- controls


def controls(rows: list[dict]) -> list[dict]:
    """The controls of section 5 that the results file can show."""
    def cell(cls, det):
        return tally([r for r in rows if r["class"] == cls])[det]

    m7, m2, m1 = cell("M7", "verifier"), cell("M2", "count"), cell("M1", "count")

    def line(name, c, ok):
        return {"control": name, "valid": c["valid"], "check": c["check"], "crash": c["crash"],
                "passes": ok if c["valid"] else None}

    return [
        line("M7: the verifier blocks every valid mutant by a check", m7, m7["check"] == m7["valid"]),
        line("M2: the count check blocks every valid mutant by a check", m2, m2["check"] == m2["valid"]),
        line("M1: the count check blocks no valid mutant", m1, m1["check"] + m1["crash"] == 0),
    ]


def repetition(first: list[dict], again: list[dict]) -> list[dict]:
    """Repeated lines against the first line of the same mutant, the times aside."""
    index = {r["mutant_id"]: r for r in first}
    out: dict[str, dict] = {}
    for r in again:
        o = out.setdefault(r["class"], {"class": r["class"], "repeated": 0, "same": 0,
                                        "verifier_differs": 0, "count_differs": 0, "other_differs": 0,
                                        "columns": []})
        o["repeated"] += 1
        base = index[r["mutant_id"]]
        diff = {k for k in r if k not in TIMES and r[k] != base.get(k)}
        v = any(k.startswith("verifier_") for k in diff)
        c = any(k.startswith("count_") for k in diff)
        other = any(not k.startswith(("verifier_", "count_")) for k in diff)
        o["verifier_differs"] += v
        o["count_differs"] += c
        o["other_differs"] += other
        o["same"] += not diff
        o["columns"] = sorted(set(o["columns"]) | diff)
    return sorted(out.values(), key=lambda o: _order(o["class"], "all"))


# --------------------------------------------------------------------------- predictions


# `protocol/PREDICTIONS.md`, line by line. "blocked" is "covered, or blocked by a crash": every
# valid mutant blocked. "open*" is "open, unless a cell happens to hold a published string".
PREDICTED = [
    ("M1", "all", "open", "open"),
    ("M2", "once", "covered", "covered"),
    ("M2", "repeated", "open", "covered"),
    ("M4", "same section", "open", "open"),
    ("M4", "different sections", "open", "covered"),
    ("M5", "checked", "open", "open"),
    ("M5", "construction", "open", "open"),
    ("M5", "remove", "open", "open"),
    ("M6", "read, print now false", "blocked", "open"),
    ("M6", "read, print still true", "open", "open"),
    ("M6", "unread", "open", "open"),
    ("M7", "all", "covered", "open*"),
    ("B1", "once", "covered", "covered"),
    ("B1", "repeated", "open", "covered"),
]
# "Taken together, the two detectors should leave open".
PREDICTED_EITHER = [("M1", "all"), ("M4", "same section"), ("M5", "checked"), ("M5", "construction"),
                    ("M5", "remove"), ("M6", "unread")]
PREDICTED_TEXT = {"blocked": "covered, or blocked by a crash",
                  "open*": "open, unless a cell holds a published string"}


def _held(predicted: str, cell: dict) -> bool | None:
    if cell is None or cell["valid"] == 0:
        return None
    blocked = cell["check"] + cell["crash"]
    if predicted == "covered":
        return cell["check"] == cell["valid"]
    if predicted == "open":
        return blocked == 0
    if predicted == "blocked":
        return blocked == cell["valid"]
    if predicted == "open*":
        return cell["blocked_no_collision"] == 0
    raise ValueError(predicted)


def predictions(table: list[dict]) -> list[dict]:
    index = {(g["class"], g["stratum"]): g for g in table}
    lines = [(c, s, d, p) for c, s, pv, pc in PREDICTED for d, p in (("verifier", pv), ("count", pc))]
    lines += [(c, s, "either", "open") for c, s in PREDICTED_EITHER]
    out = []
    for cls, stratum, det, predicted in lines:
        g = index.get((cls, stratum))
        cell = g[det] if g else None
        out.append({"class": cls, "stratum": stratum, "detector": det,
                    "predicted": PREDICTED_TEXT.get(predicted, predicted),
                    "result": cell["word"] if cell else "no mutant",
                    "valid": cell["valid"] if cell else 0,
                    "check": cell["check"] if cell else 0,
                    "crash": cell["crash"] if cell else 0,
                    "held": _held(predicted, cell)})
    return out


# --------------------------------------------------------------------------- rendering


def _table(head: list[str], body: list[list]) -> str:
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    lines += ["| " + " | ".join(str(x) for x in r) + " |" for r in body]
    return "\n".join(lines) + "\n"


def _interval(cell: dict) -> str:
    if cell["interval"] is None:
        return "—"
    lo, hi = cell["interval"]
    return f"{100 * lo:.1f} to {100 * hi:.1f}"


def _label(cls: str) -> str:
    return CLASS_LABEL.get(cls, cls)


def _should(g: dict) -> str:
    return {"block": "yes", "pass": "no: a block is a false alarm", "none": "outside the rate"}.get(
        "/".join(g["expected"]), "/".join(g["expected"]))


def _q2_table(table: list[dict], det: str) -> str:
    head = ["Class", "Stratum or subgroup", "Valid", "Invalid", "Blocked by a check",
            "Blocked by a crash", "95 % interval of blocked, %", "Word", "Should a detector block"]
    if det == "count":
        head.append("Follows from the design")
    body = []
    for g in table:
        c = g[det]
        r = [_label(g["class"]), g["stratum"], c["valid"], g["invalid"], f"{c['check']}/{c['valid']}",
             f"{c['crash']}/{c['valid']}", _interval(c), c["word"], _should(g)]
        if det == "count":
            r.append("by design" if g["count_by_design"] else "measured")
        body.append(r)
    return _table(head, body)


def _yes(v) -> str:
    return {True: "yes", False: "NO", None: "no valid mutant"}[v]


def render(first: list[dict], again: list[dict], case_q1: dict | None = None) -> str:
    table = q2(first)
    out = ["# Tables\n",
           "Written by `analysis/analyze.py` from `results/mutants.csv`. Not edited by hand.\n",
           f"Lines read: {len(first) + len(again)}; mutants: {len(first)}; repeated lines: {len(again)}.\n"]

    out.append("## Mutants by class (section 7)\n")
    out.append(_table(
        ["Class", "Mutants", "Valid", "Invalid", "Timeout, verifier", "Timeout, count check",
         "Collisions", "Commit of the scripts", "Hash of the case"],
        [[_label(p["class"]), p["lines"], p["valid"], p["invalid"], p["timeout_verifier"],
          p["timeout_count"], p["collisions"], ", ".join(p["commits"]), ", ".join(p["case_hashes"])]
         for p in per_class(first)]))

    out.append("## Q1. Figure places and distinct strings\n")
    q = q1(first)
    out.append("From the lines of the class with one M2 mutant per figure place.\n")
    out.append(_table(["Stratum", "Figure places", "Distinct strings"],
                      [[n, q[n]["places"], q[n]["strings"]] for n in ("once", "repeated", "all")]))
    if case_q1 is not None:
        same = all(case_q1[n] == q[n] for n in ("once", "repeated", "all"))
        out.append("From the case itself, which is where the short places are counted "
                   "(no mutant targets them).\n")
        out.append(_table(["", "Places", "Distinct strings"],
                          [[f"figure places, {n}", case_q1[n]["places"], case_q1[n]["strings"]]
                           for n in ("once", "repeated", "all")]
                          + [["short places", case_q1["short"]["places"], case_q1["short"]["strings"]],
                             ["places of every kind", case_q1["places"], "—"]]))
        out.append(f"The two counts of figure places agree: {_yes(same)}.\n")

    out.append("## Q2. Detection by class and stratum\n")
    out.append("Counts are of valid mutants on which the detector ended. The interval is given where "
               "the targets were a sample, and describes that draw; both detectors are deterministic. "
               "For B1 the proportion blocked is a rate of false alarms.\n")
    for det in (*DETECTORS, "either"):
        out.append(f"### {NAMES[det]}\n")
        out.append(_q2_table(table, det))

    out.append("## Collisions, apart\n")
    col = collisions(first)
    if col:
        out.append("Mutants whose new figure string equals a published string. They are valid and "
                   "are also in the tables above.\n")
        out.append(_table(
            ["Class", "Stratum or subgroup", "Collisions", "Verifier: blocked by a check",
             "Count check: blocked by a check", "At least one: blocked by a check"],
            [[_label(g["class"]), g["stratum"], g["n"]]
             + [f"{g[d]['check']}/{g[d]['valid']}" for d in (*DETECTORS, "either")] for g in col]))
    else:
        out.append("None.\n")

    out.append("## Controls (section 5)\n")
    out.append(_table(["Control", "Valid", "Blocked by a check", "Blocked by a crash", "Comes out"],
                      [[c["control"], c["valid"], c["check"], c["crash"], _yes(c["passes"])]
                       for c in controls(first)]))
    out.append("### Repetition\n")
    rep = repetition(first, again)
    if rep:
        out.append(_table(["Class", "Mutants run twice", "Same line, the time aside",
                           "Verifier differs", "Count check differs", "Another column differs",
                           "Columns that differ"],
                          [[_label(r["class"]), r["repeated"], r["same"], r["verifier_differs"],
                            r["count_differs"], r["other_differs"], ", ".join(r["columns"]) or "—"] for r in rep]))
    else:
        out.append("No repeated line in the results file.\n")

    out.append("## Predictions and results\n")
    out.append("Each line of `protocol/PREDICTIONS.md` for Q2, next to its result.\n")
    out.append(_table(
        ["Class", "Stratum or subgroup", "Detector", "Predicted", "Result", "Blocked by a check",
         "Blocked by a crash", "Valid", "Prediction held"],
        [[_label(p["class"]), p["stratum"], NAMES[p["detector"]], p["predicted"], p["result"],
          p["check"], p["crash"], p["valid"], _yes(p["held"])] for p in predictions(table)]))
    most = q["repeated"]["places"] * 2 > q["all"]["places"] if q["all"]["places"] else None
    out.append(f"Q1, predicted: most figure places are in the `repeated` stratum. Result: "
               f"{q['repeated']['places']} of {q['all']['places']}. Prediction held: {_yes(most)}.\n")
    return "\n".join(out)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=str(REPO / "results" / "mutants.csv"))
    ap.add_argument("--out", default=str(REPO / "results" / "tables.md"))
    ap.add_argument("--repetition", default=str(REPO / "results" / "repetition.csv"),
                    help="lines of the mutants run twice, if the runner wrote them to a file of their own")
    args = ap.parse_args(argv)
    first, again = split_repeats(read(Path(args.csv)))
    if Path(args.repetition).exists():
        again += read(Path(args.repetition))
    text = render(first, again, q1_case())
    Path(args.out).write_text(text, encoding="utf-8")
    print(f"{args.out}: {len(first)} mutants, {len(again)} repeated lines")


if __name__ == "__main__":
    main()

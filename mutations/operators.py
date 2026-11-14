"""The frame and the operator of each class of section 3 of the protocol.

Each class draws with one `random.Random(20261114 + number)` (8 for B1), from its frame sorted by
file, line and position, in the order each function below states. No function reads the count
check or its output.
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass, field

from mutations import core
from mutations.core import Case, Place

BASE_SEED = 20261114
CLASS_NUMBER = {"M1": 1, "M2": 2, "M4": 4, "M5": 5, "M6": 6, "M7": 7, "B1": 8}


def seed_of(cls: str) -> int:
    return BASE_SEED + CLASS_NUMBER[cls[:2]]


@dataclass
class Mutant:
    mutant_id: str
    cls: str
    seed: int
    target: str
    old: str
    new: str
    stratum: str
    expected: str  # block, pass, or decided after the run (M6)
    file: str  # path relative to the case root
    edits: list[tuple[int, int, str]]  # offsets in the file's text, and the new text
    extra: dict = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @staticmethod
    def from_json(s: str) -> "Mutant":
        d = json.loads(s)
        d["edits"] = [tuple(e) for e in d["edits"]]
        return Mutant(**d)


def apply_edits(text: str, edits) -> str:
    for start, end, new in sorted(edits, key=lambda e: e[0], reverse=True):
        text = text[:start] + new + text[end:]
    return text


def _ids(cls: str, mutants: list[Mutant]) -> list[Mutant]:
    for k, m in enumerate(mutants, start=1):
        m.mutant_id = f"{cls}-{k:03d}"
    return mutants


def _half(n: int) -> tuple[int, int]:
    """The first stratum named takes the extra one."""
    return n - n // 2, n // 2


def _place_edit(case: Case, p: Place, new_printed: str) -> tuple[int, int, str]:
    off = case.line_offset(p.line)
    return (off + p.start, off + p.end, new_printed)


def _digit_mutant(case: Case, rng, p: Place, cls: str, stratum: str) -> Mutant:
    i, new = core.change_digit(rng, p.printed, core.digit_positions(p.printed))
    return Mutant("", cls, seed_of(cls), p.target, p.printed, new, stratum, "block",
                  core.MANUSCRIPT, [_place_edit(case, p, new)], {"string": p.string, "digit": i})


# --------------------------------------------------------------------------- M2


def frame_m2(case: Case) -> list[Place]:
    return case.figure_places


def draw_m2(case: Case, n: int) -> list[Mutant]:
    """Stratum `once` first, then `repeated`. Within a stratum, target by target: the place, the
    digit, the new digit."""
    rng = random.Random(seed_of("M2"))
    st = core.strata(case.places)
    out = []
    for stratum, size in zip(("once", "repeated"), _half(n)):
        pool = [p for p in frame_m2(case) if st[p.key] == stratum]
        for _ in range(min(size, len(pool))):
            p = pool.pop(rng.randrange(len(pool)))
            out.append(_digit_mutant(case, rng, p, "M2", stratum))
    return _ids("M2", out)


def draw_m2_every_place(case: Case) -> list[Mutant]:
    """One M2 mutant for every figure place, in frame order, with the M2 seed: the digit, the new digit."""
    rng = random.Random(seed_of("M2"))
    st = core.strata(case.places)
    return _ids("M2all", [_digit_mutant(case, rng, p, "M2all", st[p.key]) for p in frame_m2(case)])


# --------------------------------------------------------------------------- M1


M1_SECTIONS = {"3.1", "3.2", "3.3", "3.4", "3.5", "4.1", "4.2", "4.3"}


def frame_m1(case: Case) -> list[core.Line]:
    with_places = {p.section for p in case.figure_places}
    lines = case.lines
    out = []
    for k, line in enumerate(lines):
        nxt = lines[k + 1].text if k + 1 < len(lines) else ""
        if (line.prose and core.section_number(line.section) in M1_SECTIONS
                and line.section in with_places and not nxt.strip()):
            out.append(line)
    return out


def _donor_kind(p: Place) -> str:
    if p.unit:
        return "unit"
    return "bare decimal" if "." in p.string else "bare integer"


def draw_m1(case: Case, n: int) -> list[Mutant]:
    """Target by target: the line; the donor among the figure places of its section; each digit
    of the new figure from left to right, drawn again while the figure is already printed or is
    a published string."""
    rng = random.Random(seed_of("M1"))
    pool = frame_m1(case)
    taken = core.printed_numerals(case.text) | set(case.published)
    out = []
    for _ in range(min(n, len(pool))):
        line = pool.pop(rng.randrange(len(pool)))
        donors = [p for p in case.figure_places if p.section == line.section]
        donor = rng.choice(donors)
        digits = donor.string.lstrip("+-")
        int_digits = len(digits.split(".")[0])
        decimals = len(digits.split(".")[1]) if "." in digits else 0
        while True:
            first = rng.choice("123456789")
            rest = "".join(rng.choice("0123456789") for _ in range(int_digits - 1 + decimals))
            figure = first + rest[: int_digits - 1]
            if decimals:
                figure += "." + rest[int_digits - 1:]
            if figure not in taken:
                break
        sentence = f" A further run gave {figure}{donor.unit_text}."
        end = case.line_offset(line.number) + len(line.text)
        out.append(Mutant("", "M1", seed_of("M1"), f"{core.MANUSCRIPT}:{line.number}:{len(line.text)}",
                          "", sentence, _donor_kind(donor), "block", core.MANUSCRIPT,
                          [(end, end, sentence)],
                          {"figure": figure, "donor": donor.target, "donor_string": donor.string}))
    return _ids("M1", out)


# --------------------------------------------------------------------------- M4


def _pairs_with(p: Place, places: list[Place], same_section: bool) -> list[Place]:
    return [q for q in places if q.key != p.key and q.string != p.string and q.unit == p.unit
            and (q.section == p.section) == same_section]


def draw_m4(case: Case, n: int) -> list[Mutant]:
    """Stratum `same section` first, then `different sections`. Target by target: the first place,
    among those with an unused partner; then the second among its unused partners."""
    rng = random.Random(seed_of("M4"))
    places = case.figure_places
    used: set[frozenset] = set()
    out = []
    for stratum, same, size in (("same section", True, _half(n)[0]),
                                ("different sections", False, _half(n)[1])):
        for _ in range(size):
            firsts = [p for p in places
                      if any(frozenset((p.key, q.key)) not in used for q in _pairs_with(p, places, same))]
            if not firsts:
                break
            p = rng.choice(firsts)
            q = rng.choice([q for q in _pairs_with(p, places, same) if frozenset((p.key, q.key)) not in used])
            used.add(frozenset((p.key, q.key)))
            out.append(Mutant("", "M4", seed_of("M4"), f"{p.target} <-> {q.target}",
                              f"{p.printed} | {q.printed}", f"{q.printed} | {p.printed}", stratum, "block",
                              core.MANUSCRIPT, [_place_edit(case, p, q.printed), _place_edit(case, q, p.printed)],
                              {"strings": [p.string, q.string]}))
    return _ids("M4", out)


# --------------------------------------------------------------------------- M5


def draw_m5(case: Case) -> list[Mutant]:
    text = (case.root / core.REGISTRY).read_text(encoding="utf-8")
    out = []
    for row in core.registry_rows(text):
        out.append(Mutant("", "M5", seed_of("M5"), f"{core.REGISTRY}:{row.line}", row.claim, "",
                          row.status, "block", core.REGISTRY, [(row.start, row.end, "")],
                          {"status": row.status}))
    return _ids("M5", out)


# --------------------------------------------------------------------------- M6


def new_leaf_text(leaf: core.Leaf) -> str:
    if isinstance(leaf.value, int):
        return str(leaf.value + max(1, abs(leaf.value) // 2))
    return "1.0" if leaf.value == 0 else repr(leaf.value * 1.5)


def draw_m6(case: Case, n: int) -> list[Mutant]:
    """N spread evenly over the artifacts in name order, the remainder to the first ones; within an
    artifact, leaf by leaf, uniform without replacement."""
    rng = random.Random(seed_of("M6"))
    by_artifact: dict[str, list[core.Leaf]] = {}
    for leaf in core.leaves(case.root):
        by_artifact.setdefault(leaf.artifact, []).append(leaf)
    names = sorted(by_artifact)
    base, rem = divmod(n, len(names))
    out = []
    for k, name in enumerate(names):
        pool = list(by_artifact[name])
        for _ in range(min(base + (k < rem), len(pool))):
            leaf = pool.pop(rng.randrange(len(pool)))
            new = new_leaf_text(leaf)
            out.append(Mutant("", "M6", seed_of("M6"), leaf.target, leaf.text, new, "", "after run",
                              f"{core.RESULTS_DIR}/{name}", [(leaf.start, leaf.end, new)],
                              {"artifact": name, "path": list(leaf.path)}))
    return _ids("M6", out)


# --------------------------------------------------------------------------- M7


def m7_cells(case: Case) -> list[tuple[str, int, int, int, int, str]]:
    """(table, line, column index, start, end, cell text) for every body cell of the two tables."""
    out = []
    for letter in "BC":
        rows = [line for line in case.lines if core.appendix_table(line) == letter]
        body = [r for r in rows[2:]]  # header row and separator row dropped
        for line in body:
            col, pos = 0, line.text.index("|") + 1
            while True:
                nxt = line.text.find("|", pos)
                while nxt != -1 and line.text[nxt - 1] == "\\":
                    nxt = line.text.find("|", nxt + 1)
                if nxt == -1:
                    break
                raw = line.text[pos:nxt]
                lead = len(raw) - len(raw.lstrip())
                cell = raw.strip()
                out.append((letter, line.number, col, pos + lead, pos + lead + len(cell), cell))
                col, pos = col + 1, nxt + 1
    return out


def m7_positions(cell: str) -> list[int]:
    base = set()
    for k in range(len(cell) - 2):
        if cell[k:k + 3] == "10^":
            base.update((k, k + 1))
    return [k for k in core.digit_positions(cell) if k not in base]


def draw_m7(case: Case) -> list[Mutant]:
    """Cell by cell in frame order: the digit, the new digit."""
    rng = random.Random(seed_of("M7"))
    out = []
    for letter, line, col, start, end, cell in m7_cells(case):
        i, new = core.change_digit(rng, cell, m7_positions(cell))
        off = case.line_offset(line)
        stratum = f"{letter}, {'first column' if col == 0 else 'other column'}"
        out.append(Mutant("", "M7", seed_of("M7"), f"{core.MANUSCRIPT}:{line}:{start}", cell, new, stratum,
                          "block", core.MANUSCRIPT, [(off + start, off + end, new)], {"digit": i}))
    return _ids("M7", out)


# --------------------------------------------------------------------------- B1


def b1_string(published: str, measured: float) -> str:
    k = len(published.split(".")[1])
    return f"{round(measured, k - 1):.{k - 1}f}"


def frame_b1(case: Case) -> list[tuple[Place, float, str]]:
    out = []
    for p in case.figure_places:
        if "." not in p.string or "," in p.string:
            continue
        values = [v for _, s, v in case.checks if s == p.string]
        news = {b1_string(p.string, v) for v in values}
        if len(news) == 1:
            out.append((p, values[0], news.pop()))
    return out


def draw_b1(case: Case, n: int) -> list[Mutant]:
    """Stratum `once` first, then `repeated`; place by place, uniform without replacement."""
    rng = random.Random(seed_of("B1"))
    st = core.strata(case.places)
    out = []
    for stratum, size in zip(("once", "repeated"), _half(n)):
        pool = [t for t in frame_b1(case) if st[t[0].key] == stratum]
        for _ in range(min(size, len(pool))):
            p, measured, new = pool.pop(rng.randrange(len(pool)))
            if core.MINUS in p.printed:
                new = new.replace("-", core.MINUS)
            out.append(Mutant("", "B1", seed_of("B1"), p.target, p.printed, new, stratum, "pass",
                              core.MANUSCRIPT, [_place_edit(case, p, new)],
                              {"string": p.string, "measured": measured}))
    return _ids("B1", out)


# --------------------------------------------------------------------------- all


def draw(case: Case, cls: str, n: int) -> list[Mutant]:
    return {
        "M1": lambda: draw_m1(case, n),
        "M2": lambda: draw_m2(case, n),
        "M2all": lambda: draw_m2_every_place(case),
        "M4": lambda: draw_m4(case, n),
        "M5": lambda: draw_m5(case),
        "M6": lambda: draw_m6(case, n),
        "M7": lambda: draw_m7(case),
        "B1": lambda: draw_b1(case, n),
    }[cls]()

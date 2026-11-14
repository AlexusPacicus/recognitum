"""What the frames are built from: the manuscript, its places, the registry and the artifacts.

Every rule here follows `protocol/definitions.md`. Nothing here reads the count check.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
from dataclasses import dataclass, field
from json.decoder import scanstring
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CASE = REPO / "case"
MANUSCRIPT = "paper/polar-projector-paper.md"
REGISTRY = "paper/claims.md"
RESULTS_DIR = "bench/results"
VERIFIER = "tools/verify_paper_tables.py"

MINUS = "−"


# --------------------------------------------------------------------------- verifier


_loaded = 0


def load_verifier(root: Path):
    """Import the verifier of one copy of the case, so its paths point at that copy."""
    global _loaded
    _loaded += 1
    root = Path(root)
    added = str(root) not in sys.path
    if added:
        sys.path.insert(0, str(root))
    try:
        spec = importlib.util.spec_from_file_location(f"_verifier_{_loaded}", root / VERIFIER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        if added:
            sys.path.remove(str(root))
    return module


def artifact_checks(root: Path) -> list[tuple[str, str, float]]:
    return load_verifier(root)._artifact_checks()


def agree(measured: float, published: str) -> bool:
    """The verifier's `_agree`, restated."""
    nd = len(published.split(".")[1]) if "." in published else 0
    return round(float(measured), nd) == float(published)


# --------------------------------------------------------------------------- lines


HEADING = re.compile(r"^#+ ")
SECTION_HEADING = re.compile(r"^(#{2,3}) (.*)$")
TABLE_ROW = re.compile(r"^\s*\|")
LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+\.)\s")
IMAGE = re.compile(r"^\s*!\[")


@dataclass
class Line:
    number: int  # from 1
    text: str
    section: str
    heading: bool
    fenced: bool
    display: bool
    table_row: bool

    @property
    def prose(self) -> bool:
        return not (
            not self.text.strip()
            or self.heading
            or self.table_row
            or LIST_ITEM.match(self.text)
            or IMAGE.match(self.text)
            or self.display
            or self.fenced
        )


def split_lines(text: str) -> list[Line]:
    out: list[Line] = []
    section = "(before the first heading)"
    fenced = display = False
    for i, raw in enumerate(text.split("\n"), start=1):
        heading = bool(HEADING.match(raw)) and not fenced
        m = SECTION_HEADING.match(raw)
        if m and not fenced:
            section = m.group(2).strip()
        is_fence = raw.lstrip().startswith("```")
        in_fence = fenced or is_fence
        starts_display = not in_fence and raw.lstrip().startswith("\\[")
        in_display = display or starts_display
        out.append(Line(i, raw, section, heading, in_fence, in_display,
                        bool(TABLE_ROW.match(raw)) and not in_fence))
        if is_fence:
            fenced = not fenced
        if starts_display:
            display = True
        if display and "\\]" in raw:
            display = False
    return out


def section_number(section: str) -> str | None:
    m = re.match(r"(\d+(?:\.\d+)*)\s", section)
    return m.group(1) if m else None


def is_references(section: str) -> bool:
    return section == "References"


def appendix_table(line: Line) -> str | None:
    """'B' or 'C' when the line is a row of the table of Appendix B or Appendix C."""
    if not line.table_row:
        return None
    for letter in "BC":
        if line.section.startswith(f"Appendix {letter}"):
            return letter
    return None


# --------------------------------------------------------------------------- places


THOUSANDS = re.compile(r"(?<=\d),(?=\d{3}\b)")
SECTION_REF = re.compile(r"§+\s?[A-D\d]+(?:\.\d+)*(?:\s?[–-]\s?§?[A-D\d]+(?:\.\d+)*)?")
UNIT = re.compile(r" ?(×|\\times|\\%|%|µs(?![A-Za-z0-9_])|ms(?![A-Za-z0-9_])|s(?![A-Za-z0-9_])"
                  r"|GB(?![A-Za-z0-9_]))")
UNIT_NAME = {"\\times": "×", "\\%": "%"}


def _drop(chars: list[tuple[str, int]], pattern: re.Pattern) -> list[tuple[str, int]]:
    s = "".join(c for c, _ in chars)
    dropped: set[int] = set()
    for m in pattern.finditer(s):
        dropped.update(range(m.start(), m.end()))
    return [ch for k, ch in enumerate(chars) if k not in dropped]


def normalize_line(text: str) -> tuple[str, list[int]]:
    """The verifier's presence text for one line, with the original column of each character."""
    chars = [(c.replace(MINUS, "-"), k) for k, c in enumerate(text)]
    chars = _drop(chars, THOUSANDS)
    chars = _drop(chars, SECTION_REF)
    return "".join(c for c, _ in chars), [k for _, k in chars]


def string_pattern(published: str) -> re.Pattern:
    return re.compile(rf"(?<![\d.]){re.escape(published)}(?!\d|\.\d)")


@dataclass(frozen=True)
class Place:
    line: int
    start: int  # column in the line as written
    end: int
    string: str  # the published string
    printed: str  # the characters of the line in [start, end), commas and minus sign included
    section: str
    unit: str  # normalized unit name, or "" for none
    unit_text: str  # what follows the place as written, the separating space included
    figure: bool
    short: bool

    @property
    def key(self) -> tuple[int, int]:
        return (self.line, self.start)

    @property
    def target(self) -> str:
        return f"{MANUSCRIPT}:{self.line}:{self.start}"


def find_places(text: str, published: list[str]) -> list[Place]:
    strings = sorted({p for p in published if len(p) > 1})
    out: list[Place] = []
    for line in split_lines(text):
        if line.heading:
            continue
        norm, cols = normalize_line(line.text)
        for s in strings:
            for m in string_pattern(s).finditer(norm):
                start, end = cols[m.start()], cols[m.end() - 1] + 1
                um = UNIT.match(line.text, end)
                unit_text = um.group(0) if um else ""
                unit = UNIT_NAME.get(um.group(1), um.group(1)) if um else ""
                figure = (len(s) >= 3 and not is_references(line.section) and not line.fenced
                          and appendix_table(line) is None)
                out.append(Place(line.number, start, end, s, line.text[start:end], line.section,
                                 unit, unit_text, figure, len(s) == 2))
    return sorted(out, key=lambda p: (p.line, p.start, p.end))


def strata(places: list[Place]) -> dict[tuple[int, int], str]:
    """`once` when the string has exactly one place in the whole manuscript, else `repeated`."""
    count: dict[str, int] = {}
    for p in places:
        count[p.string] = count.get(p.string, 0) + 1
    return {p.key: "once" if count[p.string] == 1 else "repeated" for p in places}


NUMERAL = re.compile(r"\d+(?:\.\d+)?")


def printed_numerals(text: str) -> set[str]:
    return set(NUMERAL.findall(THOUSANDS.sub("", text.replace(MINUS, "-"))))


# --------------------------------------------------------------------------- digits


def digit_choices(s: str, i: int) -> list[str]:
    """Digits that may replace s[i]: never itself, never 0 for the first digit of a run of two or more."""
    prev = s[i - 1] if i > 0 else ""
    joined = prev.isdigit() or prev == "." or (prev == "," and i >= 2 and s[i - 2].isdigit())
    run, k = 0, i
    while k < len(s) and (s[k].isdigit() or (s[k] == "," and k + 1 < len(s) and s[k + 1].isdigit())):
        run += s[k].isdigit()
        k += 1
    banned_zero = not joined and run >= 2
    return [d for d in "0123456789" if d != s[i] and not (d == "0" and banned_zero)]


def change_digit(rng, s: str, positions: list[int]) -> tuple[int, str]:
    """Draw, in order, the position and the new digit. Returns (position, new string)."""
    i = rng.choice(positions)
    d = rng.choice(digit_choices(s, i))
    return i, s[:i] + d + s[i + 1:]


def digit_positions(s: str) -> list[int]:
    return [k for k, c in enumerate(s) if c.isdigit()]


# --------------------------------------------------------------------------- registry


ROW_ID = re.compile(r"[ACPR]\d+")


@dataclass(frozen=True)
class RegistryRow:
    line: int
    start: int  # offset of the line in the file
    end: int  # offset just past its newline
    claim: str
    status: str


def registry_rows(text: str) -> list[RegistryRow]:
    out, offset = [], 0
    for n, raw in enumerate(text.split("\n"), start=1):
        cells = [c.strip() for c in raw.strip().strip("|").split("|")]
        if raw.strip().startswith("|") and len(cells) == 6 and ROW_ID.fullmatch(cells[0]):
            out.append(RegistryRow(n, offset, offset + len(raw) + 1, cells[0], cells[2]))
        offset += len(raw) + 1
    return out


# --------------------------------------------------------------------------- artifacts


NUMBER = re.compile(r"-?(?:0|[1-9]\d*)(\.\d+)?([eE][-+]?\d+)?")


@dataclass(frozen=True)
class Leaf:
    artifact: str  # file name
    path: tuple
    start: int
    end: int
    text: str
    value: float | int

    @property
    def target(self) -> str:
        return f"{RESULTS_DIR}/{self.artifact}:" + "/".join(str(p) for p in self.path)


def json_numbers(text: str) -> list[tuple[tuple, int, int, str, float | int]]:
    """Every number token of a JSON text, with its path and its offsets."""
    out = []
    i = 0

    def ws():
        nonlocal i
        while i < len(text) and text[i] in " \t\r\n":
            i += 1

    def value(path):
        nonlocal i
        ws()
        c = text[i]
        if c == "{":
            i += 1
            ws()
            if text[i] == "}":
                i += 1
                return
            while True:
                ws()
                key, i = scanstring(text, i + 1)
                ws()
                i += 1  # colon
                value(path + (key,))
                ws()
                if text[i] == ",":
                    i += 1
                    continue
                i += 1  # closing brace
                return
        if c == "[":
            i += 1
            ws()
            if text[i] == "]":
                i += 1
                return
            k = 0
            while True:
                value(path + (k,))
                k += 1
                ws()
                if text[i] == ",":
                    i += 1
                    continue
                i += 1
                return
        if c == '"':
            _, i = scanstring(text, i + 1)
            return
        for word in ("true", "false", "null", "NaN", "Infinity", "-Infinity"):
            if text.startswith(word, i):
                i += len(word)
                return
        m = NUMBER.match(text, i)
        if not m:
            raise ValueError(f"unexpected JSON at offset {i}")
        tok = m.group(0)
        v = float(tok) if (m.group(1) or m.group(2)) else int(tok)
        out.append((path, m.start(), m.end(), tok, v))
        i = m.end()

    value(())
    return out


def leaves(root: Path) -> list[Leaf]:
    out = []
    for f in sorted((Path(root) / RESULTS_DIR).glob("*.json")):
        text = f.read_text(encoding="utf-8")
        for path, start, end, tok, v in json_numbers(text):
            if path and path[0] == "results":
                out.append(Leaf(f.name, path, start, end, tok, v))
    return out


def json_set(obj, path, v):
    for p in path[:-1]:
        obj = obj[p]
    obj[path[-1]] = v


# --------------------------------------------------------------------------- the case


def case_hash(root: Path = REPO) -> str:
    return hashlib.sha256((Path(root) / "case.sha256").read_bytes()).hexdigest()


@dataclass
class Case:
    root: Path = CASE
    text: str = field(init=False)
    lines: list[Line] = field(init=False)
    checks: list[tuple[str, str, float]] = field(init=False)
    published: list[str] = field(init=False)
    places: list[Place] = field(init=False)

    def __post_init__(self):
        self.root = Path(self.root)
        self.text = (self.root / MANUSCRIPT).read_text(encoding="utf-8")
        self.lines = split_lines(self.text)
        self.checks = artifact_checks(self.root)
        self.published = [p for _, p, _ in self.checks]
        self.places = find_places(self.text, self.published)

    @property
    def figure_places(self) -> list[Place]:
        return [p for p in self.places if p.figure]

    def line_offset(self, n: int) -> int:
        return sum(len(line.text) + 1 for line in self.lines[: n - 1])

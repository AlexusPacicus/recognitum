"""The count check: the second detector of the protocol (section 2).

    python countcheck/count_check.py --control CONTROL.md --copy COPY.md --strings STRINGS.json

For each section and each published string of more than one character, it counts the places of that
string in that section, in the control and in the copy. It ends with exit code 1 if any count is
lower in the copy than in the control, and with 0 otherwise. A section of the control missing from
the copy counts as zero. On any error of its own it ends with exit code 2. It reads no artifact and
no registry.

STRINGS.json is a JSON list of published strings, or an object whose key `published_strings` holds
that list: the strings of the verifier's `_artifact_checks` on the control, taken once.

Places and sections follow `protocol/definitions.md`. Presence: heading lines and section
references are removed, the commas that separate thousands are removed, the Unicode minus is read as
a hyphen, and a string is not part of a longer number. Sections are cut at second- and third-level
headings; the text before the first heading is a section of its own.
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

SECTION_HEADING = re.compile(r"^#{2,3} (.*)$")
HEADING = re.compile(r"^#+ ")
THOUSANDS = re.compile(r"(?<=\d),(?=\d{3}\b)")
SECTION_REF = re.compile(r"§+\s?[A-D\d]+(?:\.\d+)*(?:\s?[–-]\s?§?[A-D\d]+(?:\.\d+)*)?")
BEFORE_FIRST = "(before the first heading)"


def sections(text: str) -> dict[str, str]:
    """Section name -> its presence text. Two sections with one name are joined."""
    out: dict[str, list[str]] = {}
    name = BEFORE_FIRST
    fenced = False
    for raw in text.split("\n"):
        if raw.lstrip().startswith("```"):
            fenced = not fenced
        m = SECTION_HEADING.match(raw)
        if m and not fenced:
            name = m.group(1).strip()
        if HEADING.match(raw) and not fenced:
            raw = ""
        line = raw.replace("−", "-")
        line = THOUSANDS.sub("", line)
        line = SECTION_REF.sub("", line)
        out.setdefault(name, []).append(line)
    return {k: "\n".join(v) for k, v in out.items()}


def counts(text: str, strings: list[str]) -> Counter:
    c: Counter = Counter()
    for name, body in sections(text).items():
        for s in strings:
            n = len(re.findall(rf"(?<![\d.]){re.escape(s)}(?!\d|\.\d)", body))
            if n:
                c[(name, s)] = n
    return c


def lowered(control: str, copy: str, strings: list[str]) -> list[tuple[str, str, int, int]]:
    strings = sorted({s for s in strings if len(s) > 1})
    a, b = counts(control, strings), counts(copy, strings)
    return [(name, s, n, b.get((name, s), 0)) for (name, s), n in sorted(a.items()) if b.get((name, s), 0) < n]


def load_strings(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data["published_strings"]
    if not isinstance(data, list) or not all(isinstance(s, str) for s in data):
        raise ValueError("strings file must hold a list of strings")
    return data


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--control", required=True, type=Path)
    ap.add_argument("--copy", required=True, type=Path)
    ap.add_argument("--strings", required=True, type=Path)
    args = ap.parse_args(argv)
    try:
        found = lowered(args.control.read_text(encoding="utf-8"), args.copy.read_text(encoding="utf-8"),
                        load_strings(args.strings))
    except Exception as exc:  # any error of its own
        print(f"count check error: {type(exc).__name__}: {exc}")
        return 2
    for name, s, n, m in found:
        print(f"  LOWER  {name!r}: {s!r} {n} -> {m}")
    print(f"Count check: {len(found)} count(s) lower than in the control")
    return 1 if found else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException as exc:  # noqa: BLE001
        print(f"count check error: {type(exc).__name__}: {exc}")
        sys.exit(2)

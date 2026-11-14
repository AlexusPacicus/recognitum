"""Check that every numeral of a report file is printed in one of its sources.

    python analysis/check_report.py report/method-results.md [--sources FILE ...]

By default the sources are `results/tables.md`, `results/control/control.json`,
`protocol/PROTOCOL.md` and `DEVIATIONS.md`. Ends with exit code 1 and lists the numerals found in
no source.

This is a presence check, the verifier's own method, and it has the verifier's limit: it shows that
a numeral is printed somewhere in a source, not that it is the right one for its sentence.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SOURCES = ["results/tables.md", "results/control/control.json", "protocol/PROTOCOL.md", "DEVIATIONS.md"]
THOUSANDS = re.compile(r"(?<=\d),(?=\d{3}(?!\d))")
CODE = re.compile(r"`[^`\n]*`")
NUMERAL = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?![\w]|\.\d)")


def _plain(text: str) -> str:
    return THOUSANDS.sub("", text.replace("−", "-"))


def numerals(text: str) -> list[str]:
    """Numerals of a text, outside code spans (commit names, paths)."""
    return NUMERAL.findall(_plain(CODE.sub(" ", text)))


def missing(report: str, sources: str) -> list[tuple[int, str]]:
    known = set(NUMERAL.findall(_plain(sources)))
    return [(n, x) for n, line in enumerate(report.split("\n"), start=1)
            for x in numerals(line) if x not in known]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("report")
    ap.add_argument("--sources", nargs="*", default=[str(REPO / s) for s in SOURCES])
    args = ap.parse_args(argv)
    sources = "\n".join(Path(s).read_text(encoding="utf-8") for s in args.sources)
    found = missing(Path(args.report).read_text(encoding="utf-8"), sources)
    for n, x in found:
        print(f"{args.report}:{n}: {x} is printed in no source")
    print(f"{len(found)} numeral(s) printed in no source")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())

# recognitum

What escapes a claims verifier: planted errors against a check that ties a paper's figures to its
code output.

Made for the AI x Epistemics Research Sprint (Apart Research), 13–15 November 2026, Track 2: Trust
Infrastructure. Author: Alexis Zapico Fernández (independent).

The name comes from *descriptum et recognitum*, "copied and checked", the formula that closed
official Roman copies of a document.

## What this is

A paper can keep a registry of its numerical claims and a verifier that runs in CI and checks each
registered figure against stored code output. This repository measures what such a verifier
misses. It plants errors in a real paper, asks a model that has read the verifier's source to write
more, and records which ones make the check fail.

The verifier studied here starts from its own checks. Outside two appendix tables, which it compares
cell by cell, it looks each published string up anywhere in the manuscript. The results show what that leaves open, and why a detector that starts from each
printed figure is needed. That detector, the matrix, is specified in `design/matrix` with its
predictions, written before any run; it was not built during the sprint.

Recognitum does not propose the count check as a solution. It uses a low-cost check as an
experimental baseline, to characterise the limits of presence-based verification and to justify a
matrix-based architecture for numerical traceability.

## Results, in short

Every count is from [`results/tables.md`](results/tables.md), which `analysis/analyze.py` writes
from `results/mutants.csv`. The report, as submitted to the sprint on 16 November 2026, is
[`report/recognitum-apart-sprint.pdf`](report/recognitum-apart-sprint.pdf): *Recognitum: what escapes
a claims verifier when results become prose*.

- **Exposure (Q1).** The manuscript has 419 figure places. 114 hold a string printed once; 305 hold
  one of 79 strings printed more than once.
- **Mutants drawn by code (Q2).** 747 mutants, all valid. The verifier blocks a changed digit only
  where its string is printed once: 114 of 114 there, 0 of 305 elsewhere, because another copy of
  the string is still present. It blocks no added figure, no exchange of two figures and no deleted
  registry row. Every prediction held; one subgroup had no mutant.
- **Edits written by a model (Q3).** The verifier blocked none of the red team's valid edits: 0 of 30
  in part R1, 0 of 10 in part R2, 0 of 4 in part R3 (not pre-registered) and 0 of 5 in the second
  launch, reported apart. In part R2 the model also found kinds of error other than a changed result
  figure: a unit, a word, a parameter of the method, a duplicated table row.
- **A second detector, the count check,** written during the sprint, compares the count of each
  published string per section with the released manuscript. It blocks most edits on a repeated
  string, and every edit in class B1, which plants no error: those are false alarms.

## Repository

| Path | What it holds |
|---|---|
| `protocol/` | The pre-registration: protocol, predictions and definitions, frozen in commit `4bad83a` after two rounds of blind review (`reviews/`). |
| `DEVIATIONS.md` | Every change made after the freeze, nine in all, each with its date and its reason. |
| `mutations/` | Frames, operators and the runner of the mutants drawn by code. |
| `countcheck/` | The count check. |
| `redteam/` | The prompts, the script that generated the responses, the responses as returned, the author's rulings on part R2, and the script that applies the edits. |
| `analysis/` | The script that writes every table, and the check that each numeral of the report is printed in a source. |
| `results/` | The control, the draws, one line per mutant or edit, and the tables. |
| `report/` | The report as submitted to the sprint (PDF), and the drafts of its method, results and related work. |
| `design/matrix/` | The matrix: specified, with its predictions; not built. |
| `BLUEPRINT.md` | The plan the sprint started from. What was run is the protocol; its change log says what changed. |

To write the tables again from the results file, and to run the tests:

```bash
python analysis/analyze.py
```

```bash
pytest
```

The traces of the red team's client are published with two strings replaced, the author's home
folder and the identifier of the author's synced skills; `redteam/traces/REDACTED.md` says how.

## What existed before the sprint

The tag `sprint-start` marks the boundary. `git diff sprint-start` shows everything made during
the sprint.

- **`case/`** is the paper under study: the tree of
  [AlexusPacicus/polar-projector](https://github.com/AlexusPacicus/polar-projector) at commit
  `f59430a` (tag `v1.0-paper`), with its manuscript, its claims registry, its stored results and
  its verifier. It is not modified here.
- **A technical report** on the method, by the same author, published on 12 November 2026:
  [10.5281/zenodo.24163509](https://doi.org/10.5281/zenodo.24163509). The idea for this sprint came
  up while writing it.
- **An exploratory version of the matrix** and a design for it, written by an AI agent on 2–4
  November 2026. They were never reviewed or published. They are not in this repository, and
  nothing here runs or copies them. They informed the specification in `design/matrix`, written
  during the sprint.
- **Actuarii**, the author's kit of write rules for coding agents, installed here as a tool.

## Checking the case

`case.sha256` lists the sha256 of each file under `case/`. To rebuild the case from the public
repository and compare:

```bash
git clone https://github.com/AlexusPacicus/polar-projector && cd polar-projector
```

```bash
mkdir ../case-check && git archive f59430a | tar -x -C ../case-check
```

```bash
cd ../case-check && find . -type f | LC_ALL=C sort | xargs shasum -a 256 | diff - ../recognitum/case.sha256
```

The last command prints nothing when the two trees are the same.

## Use of AI

- **An AI agent (Claude)** drafted the plan with the author, wrote the code and its tests, and
  drafted the methods, results, related work, discussion and limitations appendix of the report,
  and edited and translated its abstract and conclusion.
- **The red team's edits** were written by another model, `minimax-m3.1-flash-free`, through the
  agent client `opencode`, one conversation per call of `redteam/generate.py`.
- **The author** decided the protocol and every deviation, ruled on each edit of part R2 before
  either detector ran, approved every number, and wrote the introduction, the abstract and the
  conclusion of the report.

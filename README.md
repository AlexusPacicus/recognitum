# recognitum

What escapes a claims verifier: planted errors against a check that ties a paper's figures to its
code output.

Work in progress for the AI x Epistemics Research Sprint (Apart Research), 13–15 November 2026,
Track 2: Trust Infrastructure. Author: Alexis Zapico Fernández (independent).

The name comes from *descriptum et recognitum*, "copied and checked", the formula that closed
official Roman copies of a document.

## What this is

A paper can keep a registry of its numerical claims and a verifier that runs in CI and checks each
registered figure against stored code output. This repository measures what such a verifier
misses. It plants errors in a real paper and records which ones make the check fail.

The plan is in `BLUEPRINT.md`. The pre-registration will be in `protocol/`, frozen in one commit
before any run.

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
- **An exploratory version of the second detector** (the "matrix") and a design for it, written by
  an AI agent on 2–4 November 2026. They were never reviewed or published. They are not in this
  repository, and nothing here runs or copies them. They informed the design of the matrix built
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

An AI agent (Claude) drafted the plan with the author and writes the code. The author decides the
protocol, fills in the hand-check sheet and approves every number. The report says who did what.

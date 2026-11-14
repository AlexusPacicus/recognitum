# Sprint blueprint: what escapes a claims verifier

AI x Epistemics Research Sprint (Apart Research), 13–15 November 2026. Track 2: Trust Infrastructure.
Author: Alexis Zapico Fernández (independent).

This file is the living plan. It may change, and every change goes in the change log at the end.
The pre-registration is `protocol/PROTOCOL.md`, with `protocol/PREDICTIONS.md` beside it. Both are
frozen in one commit before any run. This file calls them `PROTOCOL.md` and `PREDICTIONS.md`.

**Status: draft 3, not committed yet.** Lines marked **[open]** are not decided.

## Goal

Measure what escapes a containment mechanism for numerical claims, a claims registry with a verifier
in CI, on a real paper: what it ties, which errors it blocks, and which pass with a green check.

## The idea in one paragraph

Mutation testing changes a program to see whether its tests notice. Here the document is the
program and the verifier is its test suite: we plant errors in the paper and see whether the check
blocks them. Each class of error is a specification written before any run: "faced with this, the
check must block". The sprint reports three things:

1. **The deployed verifier**, which checks that a figure is printed somewhere, not where.
2. **A second detector built during the sprint**, the matrix, which reads from the text back to the
   code, behind a gate that blocks. It is written test-first, against planted errors.
3. **Errors we did not choose.** A model that never saw the matrix writes its own errors and its own
   ways of attacking the verifier. They are the held-out set.

The limit all of it shares: a check is deterministic until language comes in. A detector can tie a
string to a stored value. It does not know what the sentence says.

## Where this comes from

The idea came up while the author wrote a one-week technical report on the method, published on
12 November 2026 (version 1.1, DOI: 10.5281/zenodo.24163509). Its limits section says that tests written from the claim, with checks
in both directions between registry, text and code, would catch part of what the verifier misses,
and that this was not tested. The sprint tests it.

During that week an AI agent wrote an exploratory version of the matrix (2 November) and a design
for it (4 November). Neither was reviewed or published, and neither is run or copied here. They
informed the design of the matrix built in the sprint, and the report says so.

## Questions

- **Q1, coverage.** Of the paper's result figures, what fraction is tied with location, tied by
  presence only, or untied? Descriptive.
- **Q2, detection.** For each class of planted error, what fraction does each detector block? And
  for a harmless edit, what fraction does it block by mistake? Central.
- **Q3, how far to trust the matrix.** How well does the matrix agree with the author's reading of
  a sample of figures, on what kind of figure each is and, apart, on whether it is tied? When an
  error escapes the matrix, how does it escape? And how far does its detection drop from the errors
  it was built against to errors it never saw? This is agreement with the author, not an
  independent validation.

## Scope

**In:**

- the Polar Projector paper at release `f59430a`, as an exported tree;
- the verifier of that tree, as deployed at the release;
- a matrix and a gate, both built in the sprint;
- the error classes of `PROTOCOL.md`, drawn by code;
- a red team: errors and attacks written by a model.

**Out:**

- Actuarii as a subject (see "Write rules");
- other papers or domains;
- new verifier features, and fixes to the matrix prompted by the red team;
- changes to the paper or its registry;
- a formal syntax where each figure carries its key: designed in the author's notes, left as future
  work;
- an agent doing research under the tool, with its natural errors measured: future work;
- whether the code measures what the text describes (the C16 kind of error).

## Repository, and what is preexisting

The sprint has its own repository, `~/Documents/NGI/recognitum`, public. The name comes from
*descriptum et recognitum*, "copied and checked", the formula that closed official Roman copies of a
document.

- **The first commit holds only what existed before:** the case, exported with
  `git archive f59430a` from the paper's public repository into `case/`, and a manifest of its file
  hashes, `case.sha256`. The README gives the command that reproduces the manifest. That commit,
  `0c6aa2d`, carries the tag `sprint-start`. Its 54 files have the same git blob hashes as the tree
  of `f59430a`. The only other file in it is a five-line `.gitignore`.
- **Everything after the tag is sprint work.**
- **Actuarii**, the author's write-rule kit, is installed in the repository as a tool. It is
  preexisting and declared.
- **Declared, not included:** the exploratory matrix and its design notes (see "Where this comes
  from").

There is no CI in the new repository. What is measured is the exit code of the command the paper's
CI runs, `python tools/verify_paper_tables.py`, on each copy of the case. The report says "the check
blocks", and explains this once.

## Detectors

A mutant is **detected** only if the detector blocks it. Anything else is a miss. "Blocks" means
that the check fails: its exit code is not 0. Whether a failed check stops a change from being
published depends on how a repository is set up, and that is outside this study.

**What detection means here, and what it does not.** Three things are kept apart:

- **Detecting an introduced change.** This is what Q2 measures. Each mutant is judged against the
  paper as released.
- **Detecting a numerical error.** A wrong figure that was already in the released paper is the
  same in the control and in every mutant, so Q2 cannot see it. Q1 and the hand check are the only
  places where the released state itself is looked at.
- **A tie being right in its meaning.** A figure tied to a check can still sit in a sentence that
  says something else. No detector here reads the sentence.

| Detector | What it is | Blocks when |
|---|---|---|
| Verifier (baseline) | `case/tools/verify_paper_tables.py`, unchanged | its exit code is not 0 |
| Matrix + gate | `matrix/` then `gate/`, both new | the gate's exit code is not 0 |

### The matrix

One row per numeral printed in the manuscript. It is deliberately small: only what the gate needs.

- **Reader.** Finds each numeral with its line, its rank on the line, its section, its context
  (prose, table, formula, caption, list, heading), and its table row and column.
- **Category, from context only.** Result, parameter, math, environment, citation, structure,
  notation, or unclassified. No rule looks at whether the figure matches a check. In the exploratory
  version one did, and a wrong figure could then fall out of the results.
- **Tie.** For a result: the verifier checks whose printed string equals the figure, taken by
  running the verifier, not by reading it. A check counts if it belongs to the figure's section or,
  in a table, names its row or column. The Appendix B and C cells are matched cell by cell.
- **Registry.** The rows of `paper/claims.md` that name those checks.
- **States of a result:** tied-located, tied-check, tied-check-1c (single character),
  string-elsewhere, check-fails, untied.

It does not trace which artifact each check reads, nor script dependencies, nor parameters against
configuration. Those belonged to other questions.

**How it is written.** Test-first. The tests are one per rule, plus a few planted errors chosen by
hand. The kit's red-green check records, for each test, that it failed before the code and passed
after (**[open]**: to confirm on the first test that this flow works in the new repository). The
matrix is frozen with a commit before the red team runs and before the campaign.

### The gate

A separate piece. The matrix describes; the gate decides. It reads two outputs of the matrix, the
control and the candidate, and nothing else.

- **Open item:** a result whose state is string-elsewhere, check-fails or untied, or a checked figure
  whose check has no registry row.
- **Rule:** the gate blocks if the candidate has an open item the control does not have. It compares
  multisets of (section, figure, state), not line numbers, so moving a sentence does not block.
- **Why differential:** the paper as released already has open items. An absolute gate would be red
  before any mutant.
- **Unclassified is a miss.** If a mutated figure ends unclassified, or in a category outside the
  count, the gate does not block and the mutant counts as missed. The gate records how it escaped.
- **A second policy, reported next to the first:** fail-closed, where any new unclassified numeral
  also blocks. It needs no extra run: the analysis computes it from the recorded outcome. The first
  policy stays the main one.

## Mutants drawn by code

Each operator draws its target from a frame fixed in `PROTOCOL.md`, with a fixed seed. No target is
picked by hand. Each frame is built from the manuscript, the registry, the artifacts and the
verifier, never from the matrix's output.

**Error classes: the detector should block.**

| Class | Planted error | Limit it probes | Frame | Subgroups |
|---|---|---|---|---|
| M1 | A new figure in prose, with no artifact and no row | Figures nobody registered | Prose sentences of §3 and §4; the figure copies the format of a figure the verifier checks, drawn from the same section | with a unit, bare decimal, bare integer |
| M2 | One digit changed in one occurrence | Presence instead of location | Every occurrence of a string the verifier checks, found with the verifier's own pattern | the string is printed once, or more than once |
| M4 | Two figures swapped, both still printed | Which claim a figure belongs to | Pairs of checked occurrences with different strings | same section or not; prose or table |
| M5 | A registry row deleted | How much depends on the registry | All 42 rows, exhaustive | checked (31), construction (4), remove (7) |
| M6 | A stored value changed | What the checks really read | Numeric leaves of `bench/results/*.json`, changed by a factor well above the printed precision | read by some check, or by none |
| M7 | An Appendix B or C cell changed | None: the positive control | Every cell of both tables, exhaustive | B, C |

**Harmless class: the detector should not block.**

| Class | Edit | Frame |
|---|---|---|
| B1 | A checked figure printed with one digit fewer, correctly rounded from its artifact | As M2 |

**Notes.**

- **There is no M3.** A change of rounding keeps the value, so it is B1. If a detector blocks it, that
  is the price of matching strings, reported as a false alarm.
- **M7 is the positive control.** The verifier compares each printed cell with its stored constant
  exactly, in both tables. The two-decade tolerance of Appendix B is between the constant and the
  recomputation, not the printed cell. Both detectors should block every M7 mutant; if one does not,
  the harness is wrong.
- **Collisions are kept.** A changed digit can produce another checked string, and the mutant then
  passes. It is counted and flagged, not redrawn.
- **Mutants nobody can see.** An M6 change to a value no check reads, or an M5 deletion of a `remove`
  row, changes nothing either detector reads. They are reported as such, in one line.

## The red team

A model writes errors we did not choose. It answers the weakness of the design above: the matrix is
built against planted errors and then measured with planted errors of the same classes.

- **What it sees:** the manuscript and the verifier's source. The verifier is the deployed, public
  tool, so a white-box attack on it is the realistic one.
- **What it never sees:** the matrix, the gate, their tests, this blueprint's class table.
- **Part R1, errors.** N numerical errors of its choice, each as an exact edit with one sentence on
  why it is an error.
- **Part R2, attacks.** Up to K ways of getting an error past the verifier that it finds by itself,
  each with one worked instance: the exact edit, why it is an error, and the verdict it expects.
- **It writes no file.** It returns a structured list. A script of ours applies each edit to a copy
  of the case, checks the diff, and runs both detectors. That executed row is its test.
- **Validity, decided without the matrix.** R1: the diff touches only the manuscript, changes one
  numeral, and the new value differs from the old at the printed precision. R2: the author reads each
  class and rules whether it is an error. With K at most 10, that is half an hour.
- **When.** After the matrix is frozen. The prompt, the model, N, K and the validity rule are in
  `PROTOCOL.md` before anything is generated. Every response is stored as returned.
- **What is done with it.** Reported. Nothing from the red team is used to change the matrix during
  the sprint; that would spend the held-out set.
- **Isolation, by folder.** The red team runs from a separate folder that holds only the manuscript
  and the verifier's source, exported from `case/`. The matrix is not there to be opened. This needs
  no tool and works with any client.
- **Sizes.** N = 30 errors, from 6 separate calls of 5, so that one call does not condition the
  next. K is at most 10 attacks, from one more call.
- **[open]** The model. A model from another family would be more independent of the agent that
  writes the matrix. Within one family, a different model for each pair of calls adds some variety,
  not independence.

**What it is not.** It is not an independent researcher. We write its task, and it may share blind
spots with the agent that builds the matrix. The report calls it "errors written by a model that did
not see the instrument".

## What we expect

`PREDICTIONS.md` records these before the campaign, and the report shows them next to the results.
They are kept out of `PROTOCOL.md` so that the blind reviewer never reads what we expect. For
the verifier they are read from its source. For the matrix they are what its specification requires.

| Class | Verifier | Matrix + gate |
|---|---|---|
| M1 | Passes: it never starts from the text | Blocks when the context marks a result (unit, decimal in prose, table cell); misses a bare integer |
| M2 | Blocks if the string was printed once; passes if it is printed elsewhere | Blocks, unless the mutated figure collides or leaves the result category |
| M4 | Passes: both strings are still printed | In prose, mostly passes: it matches by string. In tables, blocks when the check names the row or column |
| M5 | Passes | Blocks for checked rows; nothing to see for the rest |
| M6 | Blocks when a read value moves past the printed precision | The same |
| M7 | Blocks | Blocks |
| B1 | Blocks when the string was printed once: a false alarm | Blocks |
| R1, R2 | Not predicted | Not predicted |

For the verifier, most of these follow from its design. The campaign checks that the design does
what we read. The numbers that are not known in advance are the matrix's on M1, M2 and M4, and both
detectors' on the red team.

## Architecture

```
case/  (the tree of f59430a)
  → control: verifier exit code, matrix output
  → mutant source: operator + seed, or a stored red-team edit
  → mutated copy + diff check
  → verifier (exit code)
  → matrix → gate against the control (exit code, outcome)
  → results/mutants.csv
  → analysis/analyze.py → every table of the report
```

**Components, all new:**

- `matrix/`: reader, categories, ties, registry; one output file per run.
- `gate/gate.py`: the rule above.
- `sample/`: builds the frame for the hand check with the reader, and draws the sheet.
- `mutations/frames.py`, `operators.py`, `run.py`: the frame of each class, one operator per class,
  and the runner.
- `redteam/`: the prompt, the stored responses, and the script that turns a response into mutants.
- `analysis/analyze.py`: reads `mutants.csv` and the hand-check sheet, and writes every table the
  report uses, with English labels. No figure in the report is typed by hand.

**Dependencies:** the standard library plus numpy, which the case's verifier needs. No network,
except the red-team calls.

**Constraints to check on the first dry run.**

- With Actuarii installed, the agent runs only committed Python scripts, each through its own entry
  point. Every script is committed before it runs, which is also what the protocol asks.
- The runner starts the verifier of each mutated copy as a subprocess. The copies live in a temporary
  directory, outside the repository.

## Sample sizes

- M5 and M7 are exhaustive: 42 rows, and every cell of the two tables.
- The other classes draw N targets per class: 50 if one verifier run on a mutant takes 20 s or
  less, 30 if it takes more. The seed is fixed.
- The matrix runs on the same mutants, in the order they were drawn. If it is too slow to cover them
  all before the stop rule, it covers the first ones of each class, and the report gives the count.
- Both detectors are deterministic. The interval around a proportion (Wilson, 95 %) describes the
  draw of targets, not noise in the detector. The report says so.
- **M2 is exhaustive for the verifier.** Its verdict depends only on whether the string is printed
  elsewhere, so every checked occurrence is counted, and the proportion has no interval. The matrix
  runs on the sampled M2 mutants, like the other classes.

## Data contract

### `results/mutants.csv`: one row per mutant

| Column | Type | Meaning |
|---|---|---|
| `mutant_id` | str | `{class}-{nnn}` |
| `source` | str | `operator` or `redteam` |
| `class` | str | M1, M2, M4–M7, B1, R1, R2 |
| `expected` | str | `block` for an error, `pass` for a harmless edit |
| `seed` | int | seed of the draw; empty for the red team |
| `target` | str | `file:line:k`, or artifact path and key, or registry row |
| `original` | str | value as it was |
| `mutated` | str | value after the edit |
| `stratum` | str | the subgroup of the class; for R2, the attack's name |
| `code_commit` | str | commit of the scripts that produced the row |
| `case_hash` | str | hash of the case manifest |
| `status` | str | `ok`, `invalid`, `error` or `timeout` |
| `excluded_reason` | str | empty when `status` is `ok`; otherwise the rule that excludes the row |
| `valid` | bool | passes the validity rule of its class |
| `collision` | bool | the mutated string equals another string the verifier checks |
| `diff_ok` | bool | the diff contains exactly the intended change |
| `verifier_exit` | int | verifier exit code |
| `verifier_blocked` | bool | `verifier_exit != 0` |
| `verifier_blocked_by` | str | `check` when a check reported the failure, `crash` when the verifier stopped on an exception |
| `gate_exit` | int | gate exit code |
| `matrix_blocked` | bool | `gate_exit != 0` |
| `matrix_outcome` | str | `blocked`, `unchanged`, `unclassified`, `excluded` (left the result category) or `tied-elsewhere` |
| `matrix_flags` | str | the open items that are new against the control, `;`-separated |
| `runtime_s` | float | wall time of the run |

### Counting rules

Fixed here and in `PROTOCOL.md` before any run. No row is dropped after its result is seen.

- **Invalid mutant** (`diff_ok` or `valid` is false): the edit is not the intended error. The row
  stays in the file with `status = invalid`, leaves every denominator, and is counted in the report.
  It is never a miss.
- **Timeout or harness error:** `status = timeout` or `error`. The row leaves the denominators and
  is counted in the report. If more than one row in ten of a class ends this way, the class is
  reported as not measured.
- **A detector that crashes** has a non-zero exit code, so in CI it would block. It counts as
  blocked, with `verifier_blocked_by = crash`, and the report gives the two kinds apart: a block by
  a check is detection by design, a block by a crash is not.
- **Mutants nobody can see** (an M6 leaf no check reads, an M5 `remove` row) are valid and stay in
  the denominators of their own subgroup. They are misses that the design explains.
- **A fixed harness bug** means the whole class runs again with the same seed, and the report says
  so.

### `results/control/`

The verifier's exit code and the matrix's output on the unmutated tree. The control must pass before
the campaign runs: verifier exit code 0, and the gate, given the control twice, exit code 0.

### Hand-check sheet

`unit, line, k, token, section, context, table_row, table_col, excerpt, category, tied, root, note`

The sheet is drawn in the sprint, not reused.

- **Frame:** every numeral the reader finds in the manuscript outside the References section.
- **Strata:** the reader's context only (prose, table, formula and the rest). No category of any
  matrix takes part.
- **Size and seed:** 25 units, seed in `PROTOCOL.md`. Fifty were planned; the cut to 25 was taken
  on Friday evening, before the draw, because the sprint started late.
- **What the author fills in:** `category`, from the matrix's list without unclassified; `tied`, for
  results only (yes, no, unsure); `root`, where in code output the figure comes from; `note`.
- **What the author reads while filling it in:** code and artifacts. Not the matrix's output, which
  does not exist yet, and not `paper/claims.md`.
- `PROTOCOL.md` fixes how `tied` maps onto the matrix's states.

## Analysis

- **Q1:** the category-by-state table of the control run, and the list of results not tied.
- **Q2:** for each class, subgroup and detector, the count blocked over the count run, with its
  interval where the class was sampled. Error classes give a detection rate; B1 gives a false-alarm
  rate. Collisions are shown apart. R2 is a list, one row per attack, not a rate.
- **Q3, the sheet, kind of figure:** the count of units where the author and the matrix give the
  same category, the confusion matrix, and every figure the author calls a result and the matrix
  does not, listed one by one.
- **Q3, the sheet, tie:** only on the units both call results, a two-by-two table of tied or not,
  with the author's `unsure` apart. This is a separate table from the one above.
- **No kappa.** With 25 units it would describe little. The report gives counts and lists every
  disagreement.
- **Q3, how errors escape:** for each error class, the missed mutants split by `matrix_outcome`.
- **Q3, three sets:** the matrix's detection on the hand-picked errors of its own tests, on the
  operators' sampled errors, and on the red team's. The first is built to be 100 %. The distance
  from the second to the third says how much the matrix fits our own cases.
- **The hand check is not blind.** The author had seen the summary of the exploratory matrix. The
  report says so.

## Write rules

Actuarii is not a subject of this sprint, and the campaign does not run under it. It is used for
what code outside the model can enforce:

- `hand-check/` is a governed path from the start: the agent cannot fill in or change the author's
  labels.
- `protocol/` becomes a governed path in the freeze commit: after it, the agent cannot write to the
  protocol or the predictions, and a change by the author carries a `Human-Record` trailer.

The author installs the kit with `--govern` for both paths, outside any session. The report says
this in one sentence under "who did what" and gives the number of denied writes, if any.

## Blind review of the instrument

The author's method puts one step before any run: audit the instrument. The kit already has the
tool for it, and the author has used it in another project. A reviewer agent reads a package built
from one commit, holding the record under review and the files it cites, with their hashes. While
the review runs, a hook denies every read outside the package. The reviewer starts without project
instructions, memory or git state, cannot run or write anything, and returns PASS or CHANGES with
numbered items.

- **The record** is `PROTOCOL.md`: the rules of the matrix and the gate, the frames and operators,
  the validity rules, the controls, and the decision rules of the analysis.
- **What the reviewer never reads:** `PREDICTIONS.md`, this blueprint, `results/`, `redteam/`,
  `hand-check/`, `reviews/` and `report/`. If it meets an expected result, it must say so and stop.
- **Phase 1, Friday, before the freeze.** The specification, before the code exists. Among its fixed
  checks: nothing reads the answer it is judged against, every threshold has a source, and there is
  a control that can fail.
- **Phase 2, Saturday, before the campaign.** Each line of the record maps to code, and the tests
  can fail. It runs only if the matrix passes its tests by 18:00.
- **A cap.** Two rounds in phase 1, one in phase 2. A blocking item still open after that goes to the
  limitations, by name.
- **Kept:** each verdict, as returned, in `reviews/`. The report cites them.
- **Configuration.** The author fills in the `review` key of `.actuarii.json`: the kit's
  `blind-review` skill as the procedure, `protocol/definitions.md` as the base document,
  `protocol` as the records directory, and the denied paths above.
- **While the lock is on,** every agent's reads are confined to the package, this session's too. The
  lock is cleared as soon as the verdict is back.

The reviewer is a model of the same family as the agent that writes the protocol. It does not see
our expectations, and it can still share our blind spots. The report says so.

## Layout

```
README.md       what this is, what is preexisting, how to reproduce
BLUEPRINT.md    this file
protocol/       PROTOCOL.md, PREDICTIONS.md and definitions.md; frozen at one commit (governed)
reviews/        the blind reviewer's verdicts, as returned
case/           the tree of f59430a, with its manifest of hashes (preexisting)
matrix/         reader, categories, ties, registry; tests
gate/           the gate and its tests
sample/         frame and draw for the hand check
hand-check/     the filled sheet (governed)
mutations/      frames, operators and runner
redteam/        prompt, stored responses, conversion script
results/        mutants.csv, control/, logs
analysis/       analyze.py and the generated tables
report/         sources of the PDF
tools/, .claude/   Actuarii (preexisting)
```

## Roles

**The author:**

- decides the scope and every change to `PROTOCOL.md`;
- fills in the hand-check sheet himself;
- rules on each red-team attack: an error, or not;
- approves every number;
- writes the abstract, the introduction, the discussion, the limitations, the conclusion and the
  dual-use appendix in his own words;
- submits.

**The agent (Claude, in chat and in Claude Code):**

- drafts `BLUEPRINT.md` and `PROTOCOL.md` for the author;
- writes the matrix, the gate, the sample draw, the operators, the runner and the analysis,
  test-first, and runs the campaign;
- drafts the method and results sections;
- never edits `PROTOCOL.md` after the freeze;
- never fills in the hand-check sheet.

**The red-team model:** writes errors and attacks from the manuscript and the verifier. It sees
nothing else and writes no file.

**The blind reviewer (a Claude agent of the kit):** reviews the protocol, and later the code, from a
package. It sees no expectation and writes no file.

The report states who did what.

## Schedule and budget

Times are CET. The plan was 30 hours from Friday 15:15. Friday went to the design until 18:00, so
the schedule below starts there: about 4.5 hours on Friday, 14 on Saturday, 9 on Sunday and 1.5 on
Monday, 29 in all.

| When | Block | Hours |
|---|---|---|
| Fri, from 18:00 | New repository: case import, manifest, Actuarii, README; tag `sprint-start` | 1 |
| Fri | `PROTOCOL.md`, `PREDICTIONS.md`, `definitions.md`: matrix rules, frames, gate rule, counting rules, red-team prompt | 2.5 |
| Fri, by 22:30 | Blind review, phase 1, two rounds at most; freeze: commit and push | 1 |
| Sat, first | Reader and sample draw, test-first | 1.5 |
| Sat | Hand check of the 25 units, by the author, while the agent writes the operators; commit. It must come before any output of the matrix | 1 |
| Sat | Operators, frames, runner, control, dry run; time one verifier run and fix N | 3 |
| Sat | Verifier campaign in the background; analysis script and tables on the verifier's columns | 3 |
| Sat | Red-team conversion script, tested on a made-up response | 0.5 |
| Sat, to 20:00 at the latest | Categories, ties, registry and gate, test-first | 4 |
| Sat 18:00 | If the matrix passes its tests by now: blind review, phase 2, one round | 0.5 |
| Sat 20:00 | Decision on the matrix. Freeze it; red team: generate, convert, author rules on R2 | 1 |
| Sat, to midnight | Matrix and red-team runs; the analysis script runs again on the full file | 0.5 |
| Sunday | Report on the official template, references opened, appendix | 9 |
| Mon by 11:00 | Final review, links, submission | 1.5 |

The submission deadline is Monday 16 November, 12:59 CET (Sunday 23:59 AoE).

## Decision points, cut order and stop rule

**Saturday 20:00, the matrix.** If the matrix and the gate do not pass their tests by then, the
sprint is delivered without a second detector. The exploratory matrix is not brought in.

Because the decision comes late in the day, Saturday is ordered so that nothing waits for the
matrix: the operators, the verifier's campaign and the analysis script are finished first. At 20:00
a matrix that passes only adds its columns to `mutants.csv`, and the analysis runs again. The red
team is generated after the freeze, or after 20:00 if there is no matrix, and runs against the
verifier either way.

What remains without the matrix:

- Q2 for the verifier alone, on the operators' classes and on the red team;
- Q1 as an estimate from the hand-check sheet, where the author marked each result tied or not;
- Q3 dropped, and the unfinished matrix described in the limitations.

**If the work falls behind,** cut in this order, and declare each cut in the report:

1. the harmless class B1; the report then says nothing about false alarms;
2. the red team's part R2, then part R1;
3. the number of mutants per class, as the rule in `PROTOCOL.md` allows.

Already taken: the hand check is 25 units, not 50.

Never cut the protocol freeze, phase 1 of the blind review, the controls, the positive control M7 or
the limitations appendix.

**Stop rule:** at midnight on Saturday (24:00), the analysis runs on whatever has run by then.
Sunday is for writing.

## For the limitations and dual-use appendix

Notes for the author, who writes it.

- One paper, one verifier, one author.
- The matrix is new code written by an AI agent in a day; the hand check and the red team are what
  stand between it and its own tests.
- The red team is not independent (see "What it is not").
- Detectors are deterministic; the intervals describe sampling.
- Dual use: part R2 is a list of ways to get a wrong number past a verifier of this kind. They are
  published with the check that would catch each one, where there is one.

## Open before the freeze

1. The red team's model.
2. The word "containment". In an AI safety sprint it reads as containing an AI, and the verifier
   reports a failure rather than holding anything back. The framing and the title are the author's.

## Done

- [ ] Report PDF on the official template from the Guidelines tab.
- [ ] 8 pages or fewer before references and appendices.
- [ ] Abstract of 150 to 250 words.
- [ ] Author and affiliation.
- [ ] Limitations and Dual-Use / Ethical Considerations appendix.
- [ ] Preexisting work marked in the README and in the report.
- [ ] Every reference opened by the author.
- [ ] Every link works.
- [ ] Submitted before Monday 11:00 CET, and the confirmation email checked against the right PDF.

## Change log

- 2026-11-13: created.
- 2026-11-13, draft 2: detection means blocking; the gate as a separate piece; unclassified counts as
  a miss; M3 becomes the harmless class B1; M5 and M7 exhaustive; frames built without the matrix.
- 2026-11-13, draft 3: the sprint gets its own repository; the matrix is rebuilt in the sprint,
  test-first, and the exploratory one is declared but not used; the hand-check sample is drawn
  again; a red team writes the held-out errors; the keyed-syntax proof of concept goes to future
  work; without a working matrix by Saturday 20:00, the sprint is delivered without a second
  detector, and Saturday is ordered so that the verifier's campaign and the analysis come first.
  The repository is named `recognitum`. The stop rule moves from 22:00 to midnight on Saturday.
- 2026-11-13, review of the open points: B1 is in; the fail-closed policy is reported as a second
  column; M2 is exhaustive for the verifier only; the red team is 30 errors in 6 calls and at most
  10 attacks, isolated by folder instead of by Actuarii; the author also writes the abstract and
  the dual-use appendix; the note is cited by its version 1.1 DOI.
- 2026-11-13, 18:00, after an outside review of earlier drafts: counting rules for invalid mutants,
  errors, timeouts and crashes; what detection means and does not; the sheet's two agreements kept
  apart, with no kappa; versions and status in the data contract; a column for the limit each class
  probes. The hand check is cut to 25 units. The schedule starts from the real hour.
- 2026-11-13: blind review of the instrument added, with the kit's reviewer: phase 1 before the
  freeze, phase 2 before the campaign if the matrix is ready by 18:00. The protocol moves to
  `protocol/`, and the predictions leave it for their own file.
- 2026-11-14: the sprint started a day late, and what was run is the frozen protocol, not the fuller
  plan above. The matrix and the hand check were not built or run; the matrix is kept as a
  specification with its predictions in `design/matrix`. The second detector is the count check.
  The red team is run by the author in another model's chat. The questions are the three of
  `protocol/PROTOCOL.md`, not the three of this blueprint. The text above is left as it was.

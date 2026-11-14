# Protocol

Pre-registration of the sprint. It is frozen in one commit before any run. A change after the freeze
is not made here: it is written in `DEVIATIONS.md`, with its date and its reason, and the report
lists every one.

Words in this file are used as `protocol/definitions.md` fixes them.

## 1. What is measured

Three questions, on one case.

- **Q1, exposure.** Of the places where the manuscript prints a figure the verifier checks, how many
  print a string found only once in the manuscript, and how many a string found more than once.
- **Q2, detection.** For each class of planted edit, how many mutants each detector blocks.
- **Q3, edits we did not choose.** How many of the edits written by a model that read the verifier's
  source each detector blocks, and which kinds of attack that model finds.

Q2 and Q3 judge each mutant against the paper as released. A wrong figure already in the released
paper is the same in the control and in every mutant, so they do not see it. No detector here reads
what the sentence around a figure says.

## 2. The two detectors

Both run on the same mutants, each on an identical copy.

| Detector | What it is | Blocks when |
|---|---|---|
| Verifier | `python tools/verify_paper_tables.py`, from the root of the copy. It belongs to the case and is not changed | its exit code is not 0 |
| Count check | A script written during the sprint. It reads the manuscript of the copy and of the control, and the list of published strings | its exit code is not 0 |

**The count check.** The published strings are taken once, from the verifier's `_artifact_checks` on
the control. For each section and each published string of more than one character, the check
counts the places of that string in that section, in the control and in the copy. It ends with exit
code 1 if any count is lower in the copy than in the control, and with 0 otherwise. A section of the
control that is missing from the copy counts as zero. It reads no artifact and no registry.

**Differences between the two, declared.**

- The verifier existed before the sprint. The count check is written after reading the verifier and
  with the classes of section 3 in mind, so its counts on those classes follow from its design and
  are not an independent measurement. Section 4 is the set it was not designed against.
- The count check is frozen in a commit before the agent that writes it opens any response of the
  red team.
- The count check is offered as an addition to the verifier, not a replacement. The analysis also
  reports mutants blocked by at least one of the two.

## 3. Mutants drawn by code

Each class has a frame and an operator. The frame is built from the manuscript, the registry, the
artifacts and the verifier. It never reads the count check or its output. Targets are drawn without
replacement with Python's `random.Random`, seeded with 20261114 plus the number in the class's name
(8 for B1), from the frame sorted by file, line and position.

**Shared rule for changing a digit.** One digit of the string is chosen uniformly and replaced by a
different digit chosen uniformly. The first digit of an integer part of two digits or more is never
replaced by 0.

**The frame of places:** every place in the manuscript outside the Appendix B and Appendix C tables.
Its two strata are `once`, when the string has exactly one place in the whole manuscript, and
`repeated`.

| Class | Should the detector block? | Frame | Operator | Strata and allocation |
|---|---|---|---|---|
| M1 | yes | Prose lines of sections 3.1 to 3.5 and 4.1 to 4.3 that end a paragraph (the next line is empty) and whose section holds at least one place | A place of the same section is drawn as a donor. A new figure copies the donor's count of integer digits, its count of decimals and the unit written after it, with every digit drawn uniformly and a first digit from 1 to 9. It is drawn again while it equals a numeral already printed or a published string. The sentence ` A further run gave <figure>.` is added at the end of the line | Recorded, not allocated: the donor has a unit, or is a bare decimal, or is a bare integer |
| M2 | yes | The frame of places | One digit of the place is changed | Half of N from each stratum; a stratum smaller than that is taken whole |
| M4 | yes | Pairs of places with different strings and the same unit after them, or none after both | The two strings are exchanged | Half of N from pairs in the same section, half from pairs in different sections |
| M5 | yes | The 42 registry rows | The row's line is deleted | All 42. Recorded: the row's status |
| M6 | yes | Every leaf of every artifact | A float is multiplied by 1.5, or set to 1.0 if it is 0. An integer v becomes v plus the larger of 1 and half of its absolute value, rounded down | N spread evenly over the artifacts in name order, the remainder going to the first ones; uniform within an artifact. Recorded after the run: `read` if any measured value of `_artifact_checks` differs from the control's, `unread` otherwise |
| M7 | yes | The 36 cells of the Appendix B and Appendix C tables | One digit of the cell is changed. In a cell written as a power of ten, only the digits of the exponent and of the mantissa can be chosen, never the base | All 36. Recorded: B or C; first column or not |
| B1 | no | Places whose published string has at least one decimal and no comma | The string is replaced by the check's measured value rounded to one decimal fewer, with Python's `round` | As M2 |

B1 is the one class of harmless edit: the value is kept and only its printed precision changes. A
detector that blocks it gives a false alarm.

**Sizes.** The time t of one verifier run is the median of three runs on the control.

- N is 50 if t is 20 seconds or less, and 30 otherwise.
- If the count of places times t is 60 minutes or less, both detectors also run on one M2 mutant
  for every place, drawn with the same seed. Those counts need no interval.

**Validity of a mutant,** checked before any detector runs. The difference between the copy and the
case is exactly the operator's edit and touches one file (two places of one file for M4). For B1,
the check's measured value agrees with the new string. A mutant that fails this is invalid.

**Collisions** are valid. They are flagged and reported apart.

## 4. Edits written by a model: the red team

A model writes edits that the authors of the detectors did not choose.

- **What it is given:** two files and nothing else, the manuscript and the verifier's source.
- **Model:** Nemotron 3.5 Super VL Free. Each response is stored as returned in
  `redteam/responses`, with the model's name and the date.
- **Part R1.** Six separate conversations, each asking for five edits: thirty in all.
- **Part R2.** One more conversation, asking for at most ten ways of getting an error past the
  verifier.
- **It writes no file.** A script applies each edit to a copy of the case: the string `old` must
  appear exactly once on the given line of the given file, and is replaced by `new`.

**Prompt of part R1**, sent as written:

> You are given a scientific manuscript and the source of a program that checks its figures. Propose
> five edits to the manuscript. Each edit must change exactly one number so that the manuscript
> states something false, and each should be an error you think the checking program may fail to
> notice. Choose them yourself. Do not explain your strategy. Answer with a JSON list of five
> objects with the keys `line` (the line number in the manuscript), `old` (text that appears exactly
> once on that line), `new` (its replacement) and `why` (one sentence saying what is now false).

**Prompt of part R2**, sent as written:

> You are given a scientific manuscript and the source of a program that checks its figures. Find
> ways of introducing an error about a numerical result into the project that the checking program
> would not report. The error may be in the manuscript or in any file the program reads. Give at
> most ten, each different in kind from the others. Answer with a JSON list of objects with the keys
> `name` (a short name for the kind of attack), `file`, `line`, `old` (text that appears exactly
> once on that line), `new`, `why` (one sentence saying what is now false) and `expects` (`pass` or
> `fail`: what you think the checking program will do).

**Validity.**

- R1: the edit applies, touches the manuscript only, changes one number, and the new number differs
  from the old one when both are rounded to the decimals of the old one.
- R2: the edit applies, and the author rules that it makes the project state something false about
  a numerical result. The author writes each ruling in `redteam/rulings.csv` before either detector
  runs on any R2 edit.

## 5. Controls

| Control | Must come out | If it does not |
|---|---|---|
| The unmutated copy | Verifier exit code 0. Count check, given the control as the copy, exit code 0 | No mutant runs until it does |
| Each mutant's difference | Exactly the operator's edit | The mutant is invalid (section 7) |
| M7, the verifier's positive control | The verifier blocks every valid M7 mutant by a check | The campaign stops. If the cause is the harness, it is fixed, logged as a deviation, and every class runs again with the same seeds. If the verifier itself lets an M7 mutant through, that is reported first among its results |
| M2, the count check's positive control | The count check blocks every valid M2 mutant | The same, for the count check |
| Repetition | The first five mutants of each class, run twice, give the same line in the results file, the time aside | The class is reported as not measured for the detector that differs |

## 6. Order of work

1. This protocol and the predictions are frozen in one commit.
2. The frames, the operators and the runner are written, with tests. The control runs. N is fixed.
3. The count check is written, with tests, and frozen in a commit.
4. The campaign: both detectors on every mutant of section 3.
5. The red team is generated by the author in parallel with steps 2 to 4. The agent opens its
   responses only after step 3. The author rules on part R2, and then both detectors run on the red
   team's edits.
6. The analysis runs. At midnight on Saturday 14 November it runs on whatever has finished.

If step 3 is not done by 21:30 CET on Saturday, the sprint is reported with the verifier alone, and
the report says so.

## 7. Counting

One line per mutant in `results/mutants.csv`, never removed.

- **Invalid:** the mutant leaves every count and is reported in a count of its own. It is never a
  miss.
- **Timeout:** a detector that has not ended after ten times its time on the control. The mutant
  leaves that detector's counts and is reported in a count of its own.
- **Not measured:** if more than one mutant in ten of a class ends invalid or in a timeout for a
  detector, the class is reported as not measured for that detector.
- **Blocked by a crash** counts as blocked and is reported apart from blocked by a check.
- **Mutants that change nothing a detector reads** (for the verifier, an M6 leaf recorded as
  `unread` or an M5 row whose status is not `checked`; for the count check, every M5 and M6 mutant)
  are valid and stay in the counts of their own subgroup.

Each line holds: the mutant's identifier, its source (operator or red team), its class, whether the
detector should block it, the seed, the target, the old and new values, the subgroup, the commit of
the scripts, the hash of the case's manifest, the status (ok, invalid, timeout), validity, collision,
and for each detector its exit code, whether it blocked, and whether by a check or by a crash.

## 8. Analysis

- **Q1.** The count of places, by stratum, and the count of distinct published strings, by stratum.
- **Q2.** For each class, each recorded subgroup and each detector, and for the two together:
  mutants blocked by a check, blocked by a crash, and valid. Where the class was sampled, the Wilson
  interval at 95 % of the proportion blocked. Both detectors are deterministic: the interval
  describes the draw of targets. Each class and subgroup is called covered, open or partial. For B1
  the proportion blocked is a rate of false alarms. Collisions are reported apart.
- **Q3.** For part R1, the same counts as a class of Q2, and next to them the counts of the mutants
  of section 3 taken together, with no threshold. For part R2, a list: one line per edit, with its
  name, the author's ruling, what the model expected and what each detector did.

No figure in the report is typed by hand: a script writes every table from `results/mutants.csv`.

## 9. Thresholds, and where each comes from

| Threshold | Value | Source |
|---|---|---|
| N per sampled class | 50, or 30 if a verifier run takes more than 20 s | The five sampled classes, the 42 rows and the 36 cells then fit in a two-hour run |
| M2 on every place | if it takes 60 minutes or less | The time left in the background on Saturday |
| The M6 factor | 1.5 | Large enough to change the first digit of any printed figure, so that agreement at the printed decimals cannot hide it |
| Red team | 30 edits in 6 conversations; at most 10 attacks | Half an hour of the author's reading for part R2. Separate conversations so that one answer does not condition the next |
| Timeout | ten times the time on the control | Wide enough for a slow run, short enough to end a hung one |
| Not measured | more than one mutant in ten | Chosen before any run; no further source |
| Confidence level | 95 % | Convention |
| Count check deadline | Saturday 21:30 CET | The red team's edits and the analysis still fit before midnight |

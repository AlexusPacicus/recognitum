# Protocol

Pre-registration of the sprint. It is frozen in one commit before any run, together with the
predictions in `protocol/PREDICTIONS.md`. A change after the freeze is not made here: it is written
in `DEVIATIONS.md`, with its date and its reason, and the report lists every one.

Words in this file are used as `protocol/definitions.md` fixes them.

## 1. What is measured

Three questions, on one case.

- **Q1, exposure.** How many figure places the manuscript has, and how many of them hold a string
  that has no other place in the manuscript. Short places are counted apart. A place is a match of
  characters: Q1 counts where a checked string is printed, not where the checked figure is.
- **Q2, detection.** For each class of planted edit, how many mutants each detector blocks.
- **Q3, edits we did not choose.** How many of the edits written by a model that read the verifier's
  source each detector blocks, and which kinds of attack that model finds.

Q2 and Q3 judge each mutant against the paper as released. A wrong figure already in the released
paper is the same in the control and in every mutant, so they do not see it. No detector here reads
what the sentence around a figure says.

## 2. The two detectors

Both run on the same mutants.

| Detector | What it is | What it reads | Blocks when |
|---|---|---|---|
| Verifier | `case/tools/verify_paper_tables.py`, run from the root of the copy. It belongs to the case and is not changed | The copy alone | its exit code is not 0 |
| Count check | A script written during the sprint | The manuscript of the copy, the manuscript of the control, and the published strings | its exit code is not 0 |

**The count check.** The published strings are taken once, from the verifier's `_artifact_checks` on
the control. For each section and each published string of more than one character, the check
counts the places of that string in that section, in the control and in the copy. It ends with exit
code 1 if any count is lower in the copy than in the control, and with 0 otherwise. A section of the
control that is missing from the copy counts as zero. On any error of its own it ends with exit code
2. It reads no artifact and no registry.

**Differences between the two, declared.**

- **They do not get the same inputs.** The verifier judges a copy by itself. The count check
  compares the copy with a reference, and here the reference is the released manuscript, the same
  text every mutant is made from. In real use the reference would be the last accepted version of
  the manuscript.
- **Some of the count check's results are not measurements.** An edit that removes a place lowers a
  count, so the count check blocks it by construction. That is the case of every valid M2 and B1
  mutant and of M4 between sections. An edit that removes no place cannot be blocked by it: M1, M4
  inside one section, and every mutant that does not touch the manuscript. The report marks these
  results as following from the design. What the campaign checks for them is that the script does
  what its design says.
- **What is measured for the count check** is the red team of section 4, which it was not designed
  against, and its false alarms on B1.
- The count check is written after reading the verifier and with the classes of section 3 in mind.
  It is frozen in a commit before the agent that writes it opens any response of the red team.
- The count check is offered as an addition to the verifier, not a replacement. The analysis also
  reports mutants blocked by at least one of the two.

## 3. Mutants drawn by code

Each class has a frame and an operator. The frame is built from the manuscript, the registry, the
artifacts and the verifier's `_artifact_checks`. It never reads the count check or its output.

**Drawing.** Targets are drawn without replacement with Python's `random.Random`, seeded with
20261114 plus the number in the class's name (8 for B1), from the frame sorted by file, line and
position. One generator serves a whole class, and its draws are made in the order the operator's
description gives them, target by target. Where half of N is not whole, the first stratum named
takes the extra one.

**Changing a digit.** One digit of the string is chosen uniformly and replaced by a different digit
chosen uniformly. The first digit of a run of two digits or more, in an integer part or in an
exponent, is never replaced by 0. Signs are never changed.

**Strata of figure places:** `once`, when the string has exactly one place in the whole manuscript,
short places included, and `repeated`.

| Class | Frame | Operator | Strata and allocation |
|---|---|---|---|
| M1 | Prose lines of sections 3.1 to 3.5 and 4.1 to 4.3 that end a paragraph (the next line is empty) and whose section holds at least one figure place | Draws, in order: the line; a figure place of the same section as donor; each digit of the new figure from left to right. The new figure copies the donor's count of integer digits, its count of decimals and its unit, with a first digit from 1 to 9. It is drawn again while it equals a numeral already printed or a published string. The sentence ` A further run gave <figure>.` is added at the end of the line | Recorded, not allocated: the donor has a unit, or is a bare decimal, or is a bare integer |
| M2 | Figure places | One digit of the place is changed | Half of N from `once`, half from `repeated`; a stratum smaller than that is taken whole |
| M4 | Pairs of figure places with different strings and the same unit, or no unit for both | Draws the first place, then the second among those that make a pair with it. The two strings are exchanged | Half of N from pairs in the same section, half from pairs in different sections |
| M5 | The 42 registry rows | The row's line is deleted | All 42. Recorded: the row's status |
| M6 | Every leaf of every artifact | A float is multiplied by 1.5, or set to 1.0 if it is 0. An integer v becomes v plus the larger of 1 and half of its absolute value, rounded down | N spread evenly over the artifacts in name order, the remainder going to the first ones; uniform within an artifact. Subgroups recorded after the run, below |
| M7 | The 36 cells of the Appendix B and Appendix C tables | One digit of the cell is changed. In a cell written as a power of ten, the digits of the mantissa and of the exponent can be chosen, never the base 10 | All 36. Recorded: B or C; first column or not |
| B1 | Figure places whose published string has at least one decimal and no comma, and for which every check with that published string gives the same new string | With k the count of decimals of the published string and v the check's measured value, the new string is `f"{round(v, k-1):.{k-1}f}"`. A minus sign is written with the character the manuscript used | As M2 |

**What each class plants, and whether a detector should block it.**

- **M1, M2, M4, M7:** the manuscript now states a figure that the stored results do not support. A
  detector should block.
- **M5:** the registry is the paper's record of what it claims and of what it withdrew. A deleted
  row is a loss of that record whatever its status, and a detector should block. Results are given
  by status, because the verifier reads only the rows that are present.
- **M6** has three subgroups, decided after the run from the verifier's `_artifact_checks` and
  `_agree` on the mutant, without any detector's verdict:
  - `unread`: no measured value differs from the control's. Nothing the paper prints depends on the
    leaf. Reported as a count: how much of the stored results no check reads.
  - `read, print still true`: some measured value differs, and every measured value still agrees
    with its published string. The edit plants no error in what is printed. Reported as a count,
    outside the detection rate.
  - `read, print now false`: some measured value no longer agrees with its published string. A
    detector should block. Only this subgroup enters the detection rate.
- **B1:** the value is kept and only its printed precision changes. A detector should not block, and
  one that does gives a false alarm.

**Limits of the frames, declared.** A figure place is a match of characters of three or more, so a
few may print another quantity with the same digits; a mutant there still changes a number the
paper prints. The M6 frame leaves out values under `config` that the verifier reads.

**Sizes.** The time t of one verifier run is the median of three runs on the control.

- N is 50 if t is 20 seconds or less, and 30 otherwise.
- If the count of figure places times t is 60 minutes or less, both detectors also run on one M2
  mutant for every figure place, drawn with the same seed. Those counts need no interval.

**Validity of a mutant,** checked before any detector runs. The difference between the copy and the
case is exactly the operator's edit and touches one file (two places of one file for M4), and the
new string differs from the old one. For B1, the check's measured value agrees with the new string.
A mutant that fails this is invalid.

**Collisions** are valid. They are flagged and reported apart.

## 4. Edits written by a model: the red team

A model writes edits that the authors of the detectors did not choose.

- **What it is given:** two files and nothing else, the manuscript and the verifier's source.
- **Model:** Nemotron 3.5 Super VL Free, in its chat interface with the settings it comes with,
  which the author cannot fix. Each response is stored as returned in `redteam/responses`, with the
  model's name and the date.
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

- R1: the edit applies, touches the manuscript only, outside the References section and outside
  headings, changes one number, and the new number differs from the old one when both are rounded to
  the decimals of the old one. A detector should block every valid R1 edit.
- R2: the edit applies, and the author rules that it makes the project state something false about
  a numerical result. The author writes each ruling in `redteam/rulings.csv` before either detector
  runs on any R2 edit.

## 5. Controls

| Control | Must come out | If it does not |
|---|---|---|
| The unmutated copy | Verifier exit code 0. Count check, given the control as the copy, exit code 0 | No mutant runs until it does |
| Each mutant's difference | Exactly the operator's edit | The mutant is invalid (section 7) |
| M7, the verifier's positive control | The verifier blocks every valid M7 mutant by a check | The campaign pauses for a diagnosis. If the cause is the harness, it is fixed, logged as a deviation, and every class runs again with the same seeds. If the verifier itself lets an M7 mutant through, the campaign goes on and that is reported first among its results |
| M2 and M1, the count check's control, in both directions | The count check blocks every valid M2 mutant by a check, with exit code 1, and blocks no valid M1 mutant. Both follow from its design, so this control tests the script and the harness, not the design: it fails if the script cuts sections or matches places wrongly, or if the harness hands it the wrong copy | The same as for M7, for the count check |
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
- Every class is reported with its count of valid, invalid and timed-out mutants, whatever they
  are. No class is dropped for having too few.
- **Blocked by a crash** counts as blocked and is reported apart from blocked by a check.
- **Mutants that change nothing a detector reads** (for the verifier, an M5 row whose status is not
  `checked`; for the count check, every M5, M6 and M7 mutant that leaves the places unchanged) are
  valid and stay in the counts of their own subgroup.

Each line holds: the mutant's identifier, its source (operator or red team), its class, whether a
detector should block it, the seed, the target, the old and new values, the subgroup, the commit of
the scripts, the hash of the case's manifest, the status (ok, invalid, timeout), validity, collision,
and for each detector its exit code, whether it blocked, and whether by a check or by a crash.

## 8. Analysis

- **Q1.** The count of figure places and of distinct strings, by stratum; and, apart, the count of
  short places and of their strings.
- **Q2.** For each class, each stratum or subgroup and each detector, and for the two together:
  mutants blocked by a check, blocked by a crash, and valid. Where a stratum was sampled, the Wilson
  interval at 95 % of its proportion blocked. Classes drawn by strata are reported by stratum only:
  no proportion is pooled over strata of unequal weight. Both detectors are deterministic: the
  interval describes the draw of targets. Each stratum or subgroup is called covered, open or
  partial. Results that follow from the count check's design (section 2) are marked as such. For B1
  the proportion blocked is a rate of false alarms. Collisions are reported apart.
- **Q3.** For part R1, the same counts as a class of Q2. For part R2, a list: one line per edit,
  with its name, the author's ruling, what the model expected and what each detector did.

No figure in the report is typed by hand: a script writes every table from `results/mutants.csv`.

## 9. Thresholds, and where each comes from

| Threshold | Value | Source |
|---|---|---|
| N per sampled class | 50, or 30 if a verifier run takes more than 20 s | At 20 s, the five sampled classes, the 42 rows, the 36 cells and the 35 repeated runs are 363 verifier runs, about two hours. Past that the stop rule of section 6 cuts the campaign |
| M2 on every figure place | if it takes 60 minutes or less | The time left in the background on Saturday |
| The M6 change | half the value | A change far larger than any rounding the paper applies. It does not make every printed figure false, which is why the subgroups of section 3 exist |
| A figure place | a string of three characters or more | Two-character strings also match step numbers, settings, exponents and reference numbers. Three is the smallest length that leaves those out; it is a rule of thumb, set before any run |
| Red team | 30 edits in 6 conversations; at most 10 attacks | Half an hour of the author's reading for part R2. Separate conversations so that one answer does not condition the next |
| Timeout | ten times the time on the control | Wide enough for a slow run, short enough to end a hung one |
| Confidence level | 95 % | Convention |
| Count check deadline | Saturday 21:30 CET | The red team's edits and the analysis still fit before midnight |

## 10. Reviews

The verdicts are in `reviews`, as returned. The change made after the second verdict, to the count
check's control in section 5, was not reviewed again.

Reviewed by: Claude Code (blind-review, claude-opus-5-5), 2026-11-14, phase 1, commit 4592d9ab36b08e2b8b5cc656db293fabc1a3cbf1, CHANGES (7 blocking, 12 non-blocking)

Reviewed by: blind-reviewer subagent (kit blind-review procedure, phase 1), 2026-11-14, commit b0d00eab0d14cc7fd019e1ba45389d0d244e353d, CHANGES (1 blocking, 2 non-blocking)

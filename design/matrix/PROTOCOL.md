# Protocol

Pre-registration of the sprint. It is frozen in one commit before any run. A change after the freeze
is not made here: it is written in `DEVIATIONS.md`, with its date and its reason, and the report
lists every one.

Words in this file are used as `protocol/definitions.md` fixes them.

## 1. What is measured

Three questions, on one case.

- **Q1.** Of the result figures the manuscript prints, how many are tied with location, tied by a
  check, tied as a single character, or not tied.
- **Q2.** For each class of planted edit, how many mutants each detector blocks.
- **Q3.** How far the matrix agrees with the author's reading of a sample of figures; how the
  mutants the matrix misses escape it; and how its count on edits it was built against compares
  with its count on edits written by a model that never saw it.

Q2 judges each mutant against the paper as released. A wrong figure already in the released paper
is the same in the control and in every mutant, so Q2 does not see it.

## 2. The two detectors

Both detectors run on the same mutants, each on an identical copy.

| Detector | Command, from the root of the copy | Blocks when |
|---|---|---|
| Verifier | `python tools/verify_paper_tables.py` | exit code is not 0 |
| Matrix and gate | the matrix, then the gate against the control | the gate's exit code is not 0 |

The verifier belongs to the case and is not changed. The matrix and the gate are written during the
sprint.

**Differences between the two, declared.**

- The matrix is written test-first against a few planted edits chosen by hand, of the same classes
  as section 5. Its counts on those classes are therefore not an independent measurement. Section 6
  is the set it never saw.
- If the matrix is too slow to cover every mutant before the stop rule, it covers the mutants of
  each class in the order they were drawn, and the report gives the count it covered.
- Section 5 allows one class, M2, to run on its whole frame for the verifier only.

## 3. The matrix

One row per token of the manuscript. It reads the manuscript, the registry and the output of the
verifier's `_artifact_checks`, taken by calling it, on the copy it is given. It reads nothing else:
not the hand-check sheet, not the mutants file, not the red team's output.

### 3.1 Reader

A token is the longest match, at each position, of one of these forms:

- a number times a power of ten written in LaTeX, mantissa and exponent together;
- a power of ten written in LaTeX;
- a version number of three or four parts;
- a plain number: digits, with optional commas between thousands, an optional decimal part and an
  optional exponent.

For each token the reader records its line, its rank, its section, its context, whether it sits
inside inline math, a code span or a link, a sign written directly before it, a unit written directly
after it (×, %, µs, ms, s, GB, °), and, in a table, the header of its column, the first cell of its
row and the index of its column from 0.

### 3.2 Category

The category comes from the token's context only. No rule looks at the checks, the artifacts or the
registry. The first rule that applies gives the category.

1. **citation:** the token is in the References section; or it is a year from 1950 to 2029 written
   directly after an author's name.
2. **structure:** the token is before the Abstract, or in a heading, or directly after a word that
   names a part of the document (section, appendix, figure, table, proposition, corollary, remark,
   lemma, algorithm, equation, step, rule, phase, part, item, or the sign §), or it is the marker
   of a list item or the number of an algorithm step.
3. **notation:** the token is inside a code span or a link, or in the two closing statements
   (code and data availability, use of generative AI), or is a subscript or a superscript, or is
   glued to letters as part of a name.
4. **environment:** the token is a version number, or carries the unit GB, or follows the name of a
   machine or of a software package, or is followed by GB, GHz or the word cores.
5. **parameter:** the token follows a setting written with an equals sign (d, N, K, k, n, B, W, δ)
   or the sign @ or the word seed; or is followed by a counted noun (chunks, queries, steps,
   vectors, runs, repetitions, samples, dimensions, neighbours and their like); or is in the first
   column of a table whose header names a setting; or is the first column of the Appendix B or
   Appendix C table.
6. **result:** the token carries one of the units ×, %, µs, ms or s; or is a table cell in a column
   after the first, outside the Notation section; or is a number with a decimal part in prose, a
   list or a caption, outside math; or is a power of ten greater than 1 outside a table.
7. **math:** the token is inside inline math or a formula and is an integer; or carries the unit °.
8. **unclassified:** anything else, including a decimal or a number in scientific notation inside
   math.

The exact patterns behind these rules are code. Each rule has at least one test that passes and one
that fails. Between this freeze and the freeze of the matrix (section 9) the patterns may be
adjusted against the manuscript and the tests only. A rule added, removed or reordered is a
deviation.

### 3.3 State of a result

A check is a **candidate** for a result token when its published string equals the token's string,
with the Unicode minus read as a hyphen and the commas between thousands removed. A check whose
label holds the sign % is a candidate only for a token printed with %.

In order:

1. **Appendix B and C cells.** A result token in one of the two tables is compared with the
   verifier's constant for its row and column. If the token equals the constant, and the verifier's
   recomputation agrees with the constant under the verifier's own tolerance, the state is
   **tied-located**. Otherwise it is **check-fails**.
2. **No candidate:** the state is **untied**.
3. **A token of one character:** if a candidate belongs to the token's section, has a measured value
   equal to the token's value, and its label shares a word with the 60 characters before the token
   or the 40 after it, the state is **tied-check-1c**. Otherwise it is **untied**.
4. **A token in a table,** other than those of step 1: a candidate is accepted if its label shares a
   word with the first cell of the token's row, or if it belongs to the token's section and its
   label shares a word with the header of the token's column.
5. **A token elsewhere:** a candidate is accepted if it belongs to the token's section.
6. If no candidate is accepted, the state is **string-elsewhere**.
7. If some accepted candidate's measured value agrees with its published string, the state is
   **tied-check**. If none does, it is **check-fails**.

### 3.4 Registry

For a tied token, the registry rows are those whose sixth cell names, between backticks, the
beginning of the label of one of its accepted checks. For a tied-located token they are the rows
that name the reserved name of its appendix. A tied token with no such row carries the flag
`no-row`.

### 3.5 Output

One file per run, with one line per token: line, rank, string, section number, context, table row
and column, category, the rule that gave it, state, accepted checks, registry rows, flag.

## 4. The gate

The gate reads two outputs of the matrix, the control's and the candidate's, and nothing else.

- It builds the multiset of open items of each.
- It ends with exit code 1 if the candidate holds an open item more times than the control does, and
  with 0 otherwise. Line numbers take no part, so a moved sentence changes nothing.
- A token that becomes unclassified, or leaves the result category, adds no open item. The gate does
  not block on it, and the mutant is missed.

For each mutant the runner also records the **outcome**, from the mutated token's line in the
candidate and the gate's exit code:

| Outcome | When |
|---|---|
| `blocked` | the gate's exit code is 1 |
| `unclassified` | not blocked, and the mutated token's category is unclassified |
| `excluded` | not blocked, and its category is neither result nor unclassified |
| `tied-elsewhere` | not blocked, and the mutated token is tied |
| `unchanged` | not blocked, and the candidate's output equals the control's, line numbers aside |

**A second policy, computed in the analysis from the outcome, with no further run:** the mutant also
counts as blocked when the outcome is `unclassified`. It is reported next to the first policy and
never replaces it.

## 5. Mutants drawn by code

Each class has a frame and an operator. The frame is built from the manuscript, the registry, the
artifacts and the verifier. It never reads the matrix or its output. Targets are drawn without
replacement with Python's `random.Random`, seeded with 20261114 plus the number in the class's name
(8 for B1), from the frame sorted by file, line and position.

**Shared rule for changing a digit.** One digit of the string is chosen uniformly and replaced by a
different digit chosen uniformly. The first digit of an integer part of two digits or more is never
replaced by 0.

**The M2 frame**, used by four classes: every place in the manuscript where a published string of
more than one character is present in the sense of the definitions, outside the Appendix B and C
tables. Its two strata are `once`, when the string is present exactly once in the whole manuscript,
and `repeated`.

| Class | Should the detector block? | Frame | Operator | Strata and allocation |
|---|---|---|---|---|
| M1 | yes | Prose lines of sections 3.1 to 3.5 and 4.1 to 4.3 that end a paragraph (the next line is empty) and whose section holds at least one place of the M2 frame | A place of the M2 frame in the same section is drawn as a donor. A new figure copies the donor's count of integer digits, its count of decimals and its unit, with every digit drawn uniformly and a first digit from 1 to 9. It is drawn again while it equals a numeral already printed or a published string. The sentence ` A further run gave <figure>.` is added at the end of the line | Recorded, not allocated: the donor has a unit, or is a bare decimal, or is a bare integer |
| M2 | yes | The M2 frame | One digit of the place is changed | Half of N from each stratum; a stratum smaller than that is taken whole |
| M4 | yes | Pairs of places of the M2 frame with different strings and the same unit after them, or none after both | The two strings are exchanged | Half of N from pairs in the same section, half from pairs in different sections. Recorded: both in prose, or at least one in a table |
| M5 | yes | The 42 registry rows | The row's line is deleted | All 42. Recorded: the row's status |
| M6 | yes | Every leaf of every artifact | A float is multiplied by 1.5, or set to 1.0 if it is 0. An integer v becomes v plus the larger of 1 and half of its absolute value, rounded down | N spread evenly over the artifacts in name order, the remainder going to the first ones; uniform within an artifact. Recorded after the run: `read` if any measured value of `_artifact_checks` differs from the control's, `unread` otherwise |
| M7 | yes | The 36 cells of the Appendix B and Appendix C tables | One digit of the cell is changed. In a cell written as a power of ten, only the digits of the exponent and of the mantissa can be chosen, never the base | All 36. Recorded: B or C; first column or not |
| B1 | no | Places of the M2 frame whose published string has at least one decimal and no comma | The string is replaced by the check's measured value rounded to one decimal fewer, with Python's `round` | As M2 |

**Sizes.** The time t of one verifier run is the median of three runs on the control.

- N is 50 if t is 20 seconds or less, and 30 otherwise.
- If the size of the M2 frame times t is 60 minutes or less, the verifier also runs on one M2
  mutant for every place of the frame, drawn with the same seed. The matrix does not.

**Validity of a mutant,** checked before any detector runs. The difference between the copy and the
case is exactly the operator's edit and touches one file (two places of one file for M4). For B1,
the check's measured value agrees with the new string. A mutant that fails this is invalid.

**Collisions** are valid. They are flagged and reported apart.

## 6. Edits written by a model: the red team

A model writes edits that the authors of the matrix did not choose.

- **What it is given:** a folder that holds two files and nothing else, the manuscript and the
  verifier's source. It is run from that folder.
- **Model:** [to fill in before the freeze]. Each response is stored as returned, with the model's
  name and the date.
- **Part R1.** Six separate calls, each asking for five edits: thirty in all. Each call starts with
  no memory of the others.
- **Part R2.** One call, asking for at most ten ways of getting an error past the verifier.
- **It writes no file.** A script applies each edit to a copy of the case: the string `old` must
  appear exactly once on the given line of the given file, and is replaced by `new`.
- **When:** after the matrix is frozen (section 9). Nothing the red team returns is used to change
  the matrix or the gate.

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

- R1: the edit applies, touches the manuscript only, changes one token, and the new token's value
  differs from the old one's when both are rounded to the decimals of the old one.
- R2: the edit applies, and the author rules that it makes the project state something false about
  a numerical result. The author writes each ruling in `redteam/rulings.csv` before either detector
  runs on any R2 edit.

## 7. The hand check

The author reads a sample of tokens and says what each is, without the matrix.

- **Frame:** every token the reader finds outside the References section.
- **Strata, from the reader's context only:** prose; table; everything else.
- **Sample:** 25 tokens: 10 from prose, 10 from tables, 5 from the rest. Drawn without replacement
  with seed 20261114, then shuffled with the same generator.
- **The sheet** shows, for each token, its line, its rank, its string, its section, its context, its
  table row and column, and its line of text with the token marked. It shows no category and no
  state.
- **The author fills in:** `category`, one of the seven categories other than unclassified; `tied`,
  for a result only, as `yes`, `no` or `unsure`; `root`, where in the code's output the figure comes
  from; `note`.
- **The author reads** the case: its manuscript, its code and its artifacts. Not the registry, not
  any output of the matrix, not the mutants file.
- **Order.** The sheet is drawn with the reader alone, before the category and state rules are
  code. The author fills it in and commits it before the matrix is frozen. The agent that writes the
  matrix does not open the filled sheet until the matrix is frozen. Nothing enforces this last rule;
  it is declared.
- **Comparison.** Tokens are joined on line, rank and string. For `tied`: `yes` matches tied-located,
  tied-check and tied-check-1c; `no` matches string-elsewhere, check-fails and untied.

The author had seen the summary of an earlier, exploratory matrix on this paper. The hand check is
the author's reading, not an independent one.

## 8. Controls

| Control | Must come out | If it does not |
|---|---|---|
| The unmutated copy | Verifier exit code 0. The gate, given the control's output twice, exit code 0 | No mutant runs until it does |
| Each mutant's difference | Exactly the operator's edit | The mutant is invalid (section 10) |
| M7, the positive control | Both detectors block every valid M7 mutant by a check | The campaign stops. If the cause is the harness, it is fixed, logged as a deviation, and every class runs again with the same seeds. If the detector itself lets an M7 mutant through, that is reported first among that detector's results |
| Repetition | The first five mutants of each class, run twice, give the same line in the results file, the time aside | The class is reported as not measured for the detector that differs |

## 9. Order of work

1. This protocol and the predictions are frozen in one commit.
2. The reader is written, and the hand-check sheet is drawn.
3. The author fills in the sheet and commits it.
4. The frames, the operators and the runner are written. The control runs. N is fixed.
5. The verifier runs on the mutants of section 5.
6. The category rules, the state rules and the gate are written, test-first. They are frozen in one
   commit: **the freeze of the matrix**. If they do not pass their tests by Saturday 14 November,
   20:00 CET, the sprint is reported without the matrix: sections 3, 4 and the matrix's part of
   sections 5 to 7 are not run, and the report says so.
7. The red team is generated. The author rules on part R2.
8. The matrix and the gate run on the mutants of section 5. Both detectors run on the red team's
   edits.
9. The analysis runs. At midnight on Saturday it runs on whatever has finished.

## 10. Counting

One line per mutant in `results/mutants.csv`, never removed.

- **Invalid:** the mutant leaves every count and is reported in a count of its own. It is never a
  miss.
- **Timeout:** a detector that has not ended after ten times its time on the control. The mutant
  leaves that detector's counts and is reported in a count of its own.
- **Not measured:** if more than one mutant in ten of a class ends invalid or in a timeout for a
  detector, the class is reported as not measured for that detector.
- **Blocked by a crash** counts as blocked and is reported apart from blocked by a check. For the
  second detector this includes the matrix stopping on an error before the gate can run: its
  command has ended with an exit code other than 0.
- **Mutants that change nothing a detector reads** (an M6 leaf recorded as `unread`, an M5 row whose
  status is not `checked`) are valid and stay in the counts of their own subgroup.

## 11. Analysis

- **Q1.** From the matrix's output on the control: the count of tokens by category and state, and
  the list of results that are not tied.
- **Q2.** For each class, each recorded subgroup and each detector: mutants blocked by a check,
  blocked by a crash, and valid. Where the class was sampled, the Wilson interval at 95 % of the
  proportion blocked. Both detectors are deterministic: the interval describes the draw of targets.
  Each class and subgroup is called covered, open or partial. For B1 the proportion blocked is a
  rate of false alarms. Collisions are reported apart. Part R2 is a list, one line per edit, with
  the author's ruling.
- **Q3, the sheet.** Two tables, kept apart. Category: the count of tokens on which the author and
  the matrix agree, the table of the author's category against the matrix's, and every token the
  author calls a result and the matrix does not, one by one. Tie: on the tokens both call results,
  tied or not for each, with the author's `unsure` apart. No coefficient of agreement is computed.
- **Q3, escapes.** For each class the detector should block, the missed mutants by outcome.
- **Q3, three sets.** The matrix's count on the planted edits of its own tests, on the mutants of
  section 5, and on part R1. The difference between the last two is reported with both counts and
  no threshold.

No figure in the report is typed by hand: a script writes every table from `results/mutants.csv` and
the sheet.

## 12. Thresholds, and where each comes from

| Threshold | Value | Source |
|---|---|---|
| N per sampled class | 50, or 30 if a verifier run takes more than 20 s | The five sampled classes, the 42 rows and the 36 cells then fit in a two-hour run |
| M2 on its whole frame, verifier only | if it takes 60 minutes or less | The time left in the background on Saturday |
| The M6 factor | 1.5 | Large enough to change the first digit of any printed figure, so that agreement at the printed decimals cannot hide it |
| Hand-check sample | 25 tokens, as 10, 10 and 5 | One hour of the author's time. Fifty were planned; the sprint started late. Results are printed in prose and tables, so those two strata take four fifths |
| Red team | 30 edits in 6 calls; at most 10 attacks | Half an hour of the author's reading for part R2. Separate calls so that one answer does not condition the next |
| Timeout | ten times the time on the control | Wide enough for a slow run, short enough to end a hung one |
| Not measured | more than one mutant in ten | Chosen before any run; no further source |
| Confidence level | 95 % | Convention |
| Words for tied-check-1c | 60 characters before, 40 after | Chosen before any run; no further source |
| Matrix deadline | Saturday 20:00 CET | Four hours remain for the red team, the last runs and the analysis |

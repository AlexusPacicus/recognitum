# Method and results: draft for the report

Draft by the agent, 14 November 2026, for the author to move onto the official template; Q3 and the
deviations from (3) on, 15 November. It covers the two sections the agent writes. Every count below
is copied from `results/tables.md`, which `analysis/analyze.py` writes from `results/mutants.csv`;
`analysis/check_report.py` checks that each numeral here is printed in a source.

## Method

**The case.** One released paper, Polar Projector, with its manuscript, its registry of claims, its
stored results and its verifier, imported unchanged. The verifier holds a list of checks, each a
published string and a value measured from a stored result. It passes when every measured value
agrees with its string, every string of more than one character is present somewhere in the
manuscript, and every cell of the tables of Appendix B and Appendix C equals a constant it holds.

**Pre-registration.** The protocol, the predictions and the definitions were frozen in one commit
(`4bad83a`) before any run, after two rounds of blind review. Changes made later are in
`DEVIATIONS.md` and listed below.

**Places.** A place is a position in the manuscript where a published string is present. A figure
place is a place whose string has three characters or more, outside the References, fenced blocks
and the two appendix tables. A figure place is in the stratum `once` when its string has exactly
one place in the manuscript, and `repeated` otherwise. A place is a match of characters: it does
not show that the checked figure is printed there.

**Two detectors.** The verifier, run on a copy of the case, blocks when its exit code is not 0. The
count check, written during the sprint, compares the manuscript of the copy with the released
manuscript: for each section and each published string, it blocks when the string has fewer places
in the copy. The two do not get the same inputs, and the count check was written with the classes
below in mind: its results on edits that remove a place, or that remove none, follow from its
design and are marked as such. It is offered as an addition to the verifier.

**Mutants drawn by code.** Each mutant is a copy of the case with one planted edit, drawn with a
fixed seed from a frame built without reading the count check.

| Class | The edit | Should a detector block |
|---|---|---|
| M1 | A sentence with a new figure is added at the end of a paragraph | yes |
| M2 | One digit of a figure place is changed | yes |
| M4 | Two figure places with different strings and the same unit are exchanged | yes |
| M5 | One row of the registry is deleted | yes |
| M6 | One number of a stored result is changed by half its value | only if a printed figure is now false |
| M7 | One digit of a cell of the Appendix B or C tables is changed | yes |
| B1 | A figure is printed with one decimal fewer, its value kept | no: a block is a false alarm |

One verifier run on the unmutated copy took 2.364 s (median of three), so the sampled classes have
50 mutants each, M5 and M7 cover every row and every cell, and M2 was also run once on every figure
place. A mutant is valid when the difference between the copy and the case is exactly the
operator's edit. For M6 the subgroup is decided after the run from the verifier's own checks,
without any detector's verdict.

**Counting.** One line per mutant in `results/mutants.csv`. Blocked by a check is counted apart from
blocked by a crash. For a class or stratum and a detector, *covered* means every valid mutant was
blocked by a check, *open* that none was blocked, *partial* anything between. Where targets were
sampled, the Wilson interval at 95 % is given for the proportion blocked; both detectors are
deterministic, so the interval describes the draw of targets. Classes drawn by strata are reported
by stratum only.

**Controls.** The unmutated copy passes both detectors. M7 is the verifier's positive control; M2
and M1 are the count check's, in both directions. The first five mutants of each class were run
twice.

## Results

**The campaign.** 747 mutants ran. All 747 are valid; none timed out on either detector.

**Controls.** The verifier blocked all 36 M7 mutants by a check. The count check blocked all 50 M2
mutants by a check and none of the 50 M1 mutants. Of the 40 lines run twice, 38 are the same as the
first, the time aside. The other two are M7 mutants whose detector columns are the same and whose
recorded commit of the scripts differs: their first run was at `a44cae4`, before the commit that
lets the runner resume (`2d8724a`).

**Q1, exposure.** The manuscript has 419 figure places holding 193 distinct strings. 114 places
hold a string printed once; 305 places hold one of 79 strings that are printed more than once. 51
short places, of 8 strings, are counted apart, and the manuscript has 472 places of every kind.

**Q2, the verifier.**

| Class | Stratum or subgroup | Blocked by a check | 95 % interval, % | Word |
|---|---|---|---|---|
| M1 | all | 0/50 | 0.0 to 7.1 | open |
| M2 | once | 25/25 | 86.7 to 100.0 | covered |
| M2 | repeated | 0/25 | 0.0 to 13.3 | open |
| M2, every figure place | once | 114/114 | — | covered |
| M2, every figure place | repeated | 0/305 | — | open |
| M4 | same section | 0/25 | 0.0 to 13.3 | open |
| M4 | different sections | 0/25 | 0.0 to 13.3 | open |
| M5 | checked | 0/31 | — | open |
| M5 | construction | 0/4 | — | open |
| M5 | remove | 0/7 | — | open |
| M6 | read, print now false | 16/16 | 80.6 to 100.0 | covered |
| M7 | all | 36/36 | — | covered |
| B1 | once | 25/25 | 86.7 to 100.0 | covered: false alarms |
| B1 | repeated | 0/25 | 0.0 to 13.3 | open |

No mutant was blocked by a crash. The verifier blocks a changed digit only where the string is
printed once: 114 of the 419 figure places. On the other 305 a changed digit passes, because
another copy of the string is still present. It blocks no added figure, no exchange of two figures
and no deleted registry row. Where a stored result that a check reads was changed so that a printed
figure became false, it blocked every time. Of the 50 M6 mutants, 34 changed a number that no check
reads and 16 made a printed figure false; none fell in the subgroup `read, print still true`.

**Q2, the count check.** By design it blocks every mutant that removes a place: all 50 of M2, all
419 of M2 on every figure place, the 25 of M4 between sections, and all 50 of B1, which are false
alarms. By design it blocks none of M1 (0/50), M4 inside one section (0/25), M5 (0/42 over the three
statuses) and M6 (0/50). The campaign confirms that the script does what its design says. Its one
measured result among the drawn mutants is M7: it blocked 2 of 36, both in Appendix B, where the
cell held a published string.

**Q2, the two together.** At least one detector blocked every valid mutant of M2, of M4 between
sections, of M6 `read, print now false` and of M7. Both leave open M1 (0/50), M4 inside one section
(0/25) and M5 (0/42). Both false-alarm on B1 where the string is printed once, and the count check
on every B1 mutant, so together they block 50 of 50 edits that plant no error.

**Collisions.** 10 M2 mutants, 43 of M2 on every figure place and 12 B1 mutants gave a new string
that is itself a published string; all 50 M4 mutants are collisions by construction. Their results
do not differ from those of their strata.

**Predictions.** Every prediction for Q2 and Q1 held. Two notes: no mutant fell in M6 `read, print
still true`, so its two lines have no result; and the count check's line for M7 held through its
stated exception, for the 2 of 36 above.

**Q3, the red team.** The edits were written by `minimax-m3.1-flash-free`, not the model the
protocol named, through the agent client `opencode`: one new session per conversation, given the
manuscript and the verifier's source and nothing else, with no shell, no edit and no network. They
were generated on Sunday, after the stop rule; Q1 and Q2 were not.

| Part | Stratum | Valid | Invalid | Verifier | Count check | At least one |
|---|---|---|---|---|---|---|
| R1 | all | 30 | 0 | 0/30 | 17/30 | 17/30 |
| R1 | repeated | 15 | 0 | 0/15 | 14/15 | 14/15 |
| R1 | no figure place | 15 | 0 | 0/15 | 3/15 | 3/15 |
| R3, not pre-registered | all | 4 | 1 | 0/4 | 3/4 | 3/4 |

Counts are of edits blocked by a check; no edit was blocked by a crash. The verifier blocked no
valid edit of R1 or R3. None of these edits touches a figure place in the stratum `once`, the only
one where the verifier blocks a changed digit: half of the R1 edits touch a repeated place and half
touch no figure place, and the four valid R3 edits all touch a repeated place. The count check
blocked 14 of the 15 R1 edits on a repeated place and 3 of the 15 elsewhere. The invalid R3 edit
names a line on which its `old` text does not appear.

Part R2 asked for at most ten ways of getting an error past the verifier, of different kinds. The
author ruled each edit before either detector ran, and ruled all ten to make the project state
something false about a numerical result. One, `R2-3-05`, changes a parameter of the method rather
than a measured figure; the author's note: a figure is true only if what it comes from is true.

| Edit | Name of the attack | The model expected | Verifier | Count check |
|---|---|---|---|---|
| `R2-3-01` | one-character-figure-exemption | pass | passed | passed |
| `R2-3-02` | unit-header-relabel | pass | passed | passed |
| `R2-3-03` | prose-comparison-flip | pass | passed | passed |
| `R2-3-04` | figure-caption-falsification | pass | passed | blocked by a check |
| `R2-3-05` | unregistered-parameter-edit | pass | passed | passed |
| `R2-3-06` | unchecked-placeholder-fill | pass | passed | passed |
| `R2-3-07` | duplicate-row-shadowing | pass | passed | passed |
| `R2-3-08` | non-positional-presence | pass | passed | blocked by a check |
| `R2-3-09` | cell-value-permutation | pass | passed | passed |
| `R2-3-10` | unchecked-derivation | pass | passed | passed |

All ten edits are valid and touch only the manuscript, although the prompt allowed any file the
verifier reads. The verifier passed all ten, as the model expected. The count check, which the
model was not shown, blocked two. The eight that passed both change a one-character figure, a
unit, a word, a parameter of the method, an empty cell, a duplicated row, the order of two figures
and a derivation.

*A note outside the questions.* The `why` of `R2-3-01` describes something other than the edit it
comes with; the author ruled the edit, not its `why`. The protocol asked nothing about whether a
model's stated reasons match its edits, and this is one case, found by reading, not a measurement.

**Deviations.** (1) The count check was committed 77 minutes after its deadline and kept. (2) A
part R3 was added to the red team, asking for edits that overstate the results; it is reported
apart and marked as not pre-registered. (3) The red team was generated and run on Sunday, after the
stop rule; the analysis of Saturday night covered the mutants drawn by code alone. (4) The red
team's model was changed to `minimax-m3.1-flash-free`. (5) Its responses were generated by a
script through an agent client, not in a chat interface; the client's own system prompt reaches the
model and is not recorded. (6) The first launch failed before any conversation reached the model,
and was run again. (7) The second launch reached the model with a faulty harness: the client
rejected the model's reads, and the model had a shell, with which it may have read the protocol.
The seven conversations were run a third time, which breaks a rule written after the first
failure. The red team is the third launch; the second is kept apart, and its five edits are to be
reported apart. (8) The R2 conversation returned nothing and was asked again, after the results of
part R1 were known; it returned nothing again. (9) Both R2 conversations had ended on the client's
own output cap of 32,000 tokens, spent on reasoning before any answer, which neither the protocol
nor the harness had set. R2 was asked a third time with the cap the client's catalogue gives the
model, 512,000, and R3, decided before it ran, with the same. Part R2 was therefore asked three
times, and the second and third askings were decided after the results of part R1 were known.

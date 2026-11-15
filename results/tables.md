# Tables

Written by `analysis/analyze.py` from `results/mutants.csv`. Not edited by hand.

Lines read: 787; mutants drawn by code: 747; edits of the red team: 0; repeated lines: 40.

## Mutants by class (section 7)

| Class | Mutants | Valid | Invalid | Timeout, verifier | Timeout, count check | Collisions | Commit of the scripts | Hash of the case |
|---|---|---|---|---|---|---|---|---|
| M1 | 50 | 50 | 0 | 0 | 0 | 0 | 2d8724a | 0e109781f03f |
| M2 | 50 | 50 | 0 | 0 | 0 | 10 | 2d8724a | 0e109781f03f |
| M2, every figure place | 419 | 419 | 0 | 0 | 0 | 43 | 2d8724a | 0e109781f03f |
| M4 | 50 | 50 | 0 | 0 | 0 | 50 | 2d8724a | 0e109781f03f |
| M5 | 42 | 42 | 0 | 0 | 0 | 0 | 2d8724a | 0e109781f03f |
| M6 | 50 | 50 | 0 | 0 | 0 | 0 | 2d8724a | 0e109781f03f |
| M7 | 36 | 36 | 0 | 0 | 0 | 0 | 2d8724a, a44cae4 | 0e109781f03f |
| B1 | 50 | 50 | 0 | 0 | 0 | 12 | 2d8724a | 0e109781f03f |

## Q1. Figure places and distinct strings

From the lines of the class with one M2 mutant per figure place.

| Stratum | Figure places | Distinct strings |
|---|---|---|
| once | 114 | 114 |
| repeated | 305 | 79 |
| all | 419 | 193 |

From the case itself, which is where the short places are counted (no mutant targets them).

|  | Places | Distinct strings |
|---|---|---|
| figure places, once | 114 | 114 |
| figure places, repeated | 305 | 79 |
| figure places, all | 419 | 193 |
| short places | 51 | 8 |
| places of every kind | 472 | — |

The two counts of figure places agree: yes.

## Q2. Detection by class and stratum

Counts are of valid mutants on which the detector ended. The interval is given where the targets were a sample, and describes that draw; both detectors are deterministic. For B1 the proportion blocked is a rate of false alarms.

### Verifier

| Class | Stratum or subgroup | Valid | Invalid | Blocked by a check | Blocked by a crash | 95 % interval of blocked, % | Word | Should a detector block |
|---|---|---|---|---|---|---|---|---|
| M1 | all | 50 | 0 | 0/50 | 0/50 | 0.0 to 7.1 | open | yes |
| M1 | bare decimal | 33 | 0 | 0/33 | 0/33 | 0.0 to 10.4 | open | yes |
| M1 | bare integer | 1 | 0 | 0/1 | 0/1 | 0.0 to 79.3 | open | yes |
| M1 | unit | 16 | 0 | 0/16 | 0/16 | 0.0 to 19.4 | open | yes |
| M2 | once | 25 | 0 | 25/25 | 0/25 | 86.7 to 100.0 | covered | yes |
| M2 | repeated | 25 | 0 | 0/25 | 0/25 | 0.0 to 13.3 | open | yes |
| M2, every figure place | once | 114 | 0 | 114/114 | 0/114 | — | covered | yes |
| M2, every figure place | repeated | 305 | 0 | 0/305 | 0/305 | — | open | yes |
| M4 | same section | 25 | 0 | 0/25 | 0/25 | 0.0 to 13.3 | open | yes |
| M4 | different sections | 25 | 0 | 0/25 | 0/25 | 0.0 to 13.3 | open | yes |
| M5 | checked | 31 | 0 | 0/31 | 0/31 | — | open | yes |
| M5 | construction | 4 | 0 | 0/4 | 0/4 | — | open | yes |
| M5 | remove | 7 | 0 | 0/7 | 0/7 | — | open | yes |
| M6 | read, print now false | 16 | 0 | 16/16 | 0/16 | 80.6 to 100.0 | covered | yes |
| M6 | unread | 34 | 0 | 0/34 | 0/34 | — | open | outside the rate |
| M7 | all | 36 | 0 | 36/36 | 0/36 | — | covered | yes |
| M7 | B, first column | 4 | 0 | 4/4 | 0/4 | — | covered | yes |
| M7 | B, other column | 8 | 0 | 8/8 | 0/8 | — | covered | yes |
| M7 | C, first column | 6 | 0 | 6/6 | 0/6 | — | covered | yes |
| M7 | C, other column | 18 | 0 | 18/18 | 0/18 | — | covered | yes |
| B1 | once | 25 | 0 | 25/25 | 0/25 | 86.7 to 100.0 | covered | no: a block is a false alarm |
| B1 | repeated | 25 | 0 | 0/25 | 0/25 | 0.0 to 13.3 | open | no: a block is a false alarm |

### Count check

| Class | Stratum or subgroup | Valid | Invalid | Blocked by a check | Blocked by a crash | 95 % interval of blocked, % | Word | Should a detector block | Follows from the design |
|---|---|---|---|---|---|---|---|---|---|
| M1 | all | 50 | 0 | 0/50 | 0/50 | 0.0 to 7.1 | open | yes | by design |
| M1 | bare decimal | 33 | 0 | 0/33 | 0/33 | 0.0 to 10.4 | open | yes | by design |
| M1 | bare integer | 1 | 0 | 0/1 | 0/1 | 0.0 to 79.3 | open | yes | by design |
| M1 | unit | 16 | 0 | 0/16 | 0/16 | 0.0 to 19.4 | open | yes | by design |
| M2 | once | 25 | 0 | 25/25 | 0/25 | 86.7 to 100.0 | covered | yes | by design |
| M2 | repeated | 25 | 0 | 25/25 | 0/25 | 86.7 to 100.0 | covered | yes | by design |
| M2, every figure place | once | 114 | 0 | 114/114 | 0/114 | — | covered | yes | by design |
| M2, every figure place | repeated | 305 | 0 | 305/305 | 0/305 | — | covered | yes | by design |
| M4 | same section | 25 | 0 | 0/25 | 0/25 | 0.0 to 13.3 | open | yes | by design |
| M4 | different sections | 25 | 0 | 25/25 | 0/25 | 86.7 to 100.0 | covered | yes | by design |
| M5 | checked | 31 | 0 | 0/31 | 0/31 | — | open | yes | by design |
| M5 | construction | 4 | 0 | 0/4 | 0/4 | — | open | yes | by design |
| M5 | remove | 7 | 0 | 0/7 | 0/7 | — | open | yes | by design |
| M6 | read, print now false | 16 | 0 | 0/16 | 0/16 | 0.0 to 19.4 | open | yes | by design |
| M6 | unread | 34 | 0 | 0/34 | 0/34 | — | open | outside the rate | by design |
| M7 | all | 36 | 0 | 2/36 | 0/36 | — | partial | yes | measured |
| M7 | B, first column | 4 | 0 | 0/4 | 0/4 | — | open | yes | measured |
| M7 | B, other column | 8 | 0 | 2/8 | 0/8 | — | partial | yes | measured |
| M7 | C, first column | 6 | 0 | 0/6 | 0/6 | — | open | yes | measured |
| M7 | C, other column | 18 | 0 | 0/18 | 0/18 | — | open | yes | measured |
| B1 | once | 25 | 0 | 25/25 | 0/25 | 86.7 to 100.0 | covered | no: a block is a false alarm | by design |
| B1 | repeated | 25 | 0 | 25/25 | 0/25 | 86.7 to 100.0 | covered | no: a block is a false alarm | by design |

### At least one of the two

| Class | Stratum or subgroup | Valid | Invalid | Blocked by a check | Blocked by a crash | 95 % interval of blocked, % | Word | Should a detector block |
|---|---|---|---|---|---|---|---|---|
| M1 | all | 50 | 0 | 0/50 | 0/50 | 0.0 to 7.1 | open | yes |
| M1 | bare decimal | 33 | 0 | 0/33 | 0/33 | 0.0 to 10.4 | open | yes |
| M1 | bare integer | 1 | 0 | 0/1 | 0/1 | 0.0 to 79.3 | open | yes |
| M1 | unit | 16 | 0 | 0/16 | 0/16 | 0.0 to 19.4 | open | yes |
| M2 | once | 25 | 0 | 25/25 | 0/25 | 86.7 to 100.0 | covered | yes |
| M2 | repeated | 25 | 0 | 25/25 | 0/25 | 86.7 to 100.0 | covered | yes |
| M2, every figure place | once | 114 | 0 | 114/114 | 0/114 | — | covered | yes |
| M2, every figure place | repeated | 305 | 0 | 305/305 | 0/305 | — | covered | yes |
| M4 | same section | 25 | 0 | 0/25 | 0/25 | 0.0 to 13.3 | open | yes |
| M4 | different sections | 25 | 0 | 25/25 | 0/25 | 86.7 to 100.0 | covered | yes |
| M5 | checked | 31 | 0 | 0/31 | 0/31 | — | open | yes |
| M5 | construction | 4 | 0 | 0/4 | 0/4 | — | open | yes |
| M5 | remove | 7 | 0 | 0/7 | 0/7 | — | open | yes |
| M6 | read, print now false | 16 | 0 | 16/16 | 0/16 | 80.6 to 100.0 | covered | yes |
| M6 | unread | 34 | 0 | 0/34 | 0/34 | — | open | outside the rate |
| M7 | all | 36 | 0 | 36/36 | 0/36 | — | covered | yes |
| M7 | B, first column | 4 | 0 | 4/4 | 0/4 | — | covered | yes |
| M7 | B, other column | 8 | 0 | 8/8 | 0/8 | — | covered | yes |
| M7 | C, first column | 6 | 0 | 6/6 | 0/6 | — | covered | yes |
| M7 | C, other column | 18 | 0 | 18/18 | 0/18 | — | covered | yes |
| B1 | once | 25 | 0 | 25/25 | 0/25 | 86.7 to 100.0 | covered | no: a block is a false alarm |
| B1 | repeated | 25 | 0 | 25/25 | 0/25 | 86.7 to 100.0 | covered | no: a block is a false alarm |

## Q3. Edits written by a model: the red team

No edit of the red team is in the results file.

## Collisions, apart

Mutants whose new figure string equals a published string. They are valid and are also in the tables above.

| Class | Stratum or subgroup | Collisions | Verifier: blocked by a check | Count check: blocked by a check | At least one: blocked by a check |
|---|---|---|---|---|---|
| M2 | once | 4 | 4/4 | 4/4 | 4/4 |
| M2 | repeated | 6 | 0/6 | 6/6 | 6/6 |
| M2, every figure place | once | 14 | 14/14 | 14/14 | 14/14 |
| M2, every figure place | repeated | 29 | 0/29 | 29/29 | 29/29 |
| M4 | same section | 25 | 0/25 | 0/25 | 0/25 |
| M4 | different sections | 25 | 0/25 | 25/25 | 25/25 |
| B1 | once | 4 | 4/4 | 4/4 | 4/4 |
| B1 | repeated | 8 | 0/8 | 8/8 | 8/8 |

## Controls (section 5)

| Control | Valid | Blocked by a check | Blocked by a crash | Comes out |
|---|---|---|---|---|
| M7: the verifier blocks every valid mutant by a check | 36 | 36 | 0 | yes |
| M2: the count check blocks every valid mutant by a check | 50 | 50 | 0 | yes |
| M1: the count check blocks no valid mutant | 50 | 0 | 0 | yes |

### Repetition

| Class | Mutants run twice | Same line, the time aside | Verifier differs | Count check differs | Another column differs | Columns that differ |
|---|---|---|---|---|---|---|
| M1 | 5 | 5 | 0 | 0 | 0 | — |
| M2 | 5 | 5 | 0 | 0 | 0 | — |
| M2, every figure place | 5 | 5 | 0 | 0 | 0 | — |
| M4 | 5 | 5 | 0 | 0 | 0 | — |
| M5 | 5 | 5 | 0 | 0 | 0 | — |
| M6 | 5 | 5 | 0 | 0 | 0 | — |
| M7 | 5 | 3 | 0 | 0 | 2 | code_commit |
| B1 | 5 | 5 | 0 | 0 | 0 | — |
| every class | 40 | 38 | 0 | 0 | 2 | code_commit |

## Predictions and results

Each line of `protocol/PREDICTIONS.md` for Q2, next to its result.

| Class | Stratum or subgroup | Detector | Predicted | Result | Blocked by a check | Blocked by a crash | Valid | Prediction held | Note |
|---|---|---|---|---|---|---|---|---|---|
| M1 | all | Verifier | open | open | 0 | 0 | 50 | yes | — |
| M1 | all | Count check | open | open | 0 | 0 | 50 | yes | — |
| M2 | once | Verifier | covered | covered | 25 | 0 | 25 | yes | — |
| M2 | once | Count check | covered | covered | 25 | 0 | 25 | yes | — |
| M2 | repeated | Verifier | open | open | 0 | 0 | 25 | yes | — |
| M2 | repeated | Count check | covered | covered | 25 | 0 | 25 | yes | — |
| M4 | same section | Verifier | open | open | 0 | 0 | 25 | yes | — |
| M4 | same section | Count check | open | open | 0 | 0 | 25 | yes | — |
| M4 | different sections | Verifier | open | open | 0 | 0 | 25 | yes | — |
| M4 | different sections | Count check | covered | covered | 25 | 0 | 25 | yes | — |
| M5 | checked | Verifier | open | open | 0 | 0 | 31 | yes | — |
| M5 | checked | Count check | open | open | 0 | 0 | 31 | yes | — |
| M5 | construction | Verifier | open | open | 0 | 0 | 4 | yes | — |
| M5 | construction | Count check | open | open | 0 | 0 | 4 | yes | — |
| M5 | remove | Verifier | open | open | 0 | 0 | 7 | yes | — |
| M5 | remove | Count check | open | open | 0 | 0 | 7 | yes | — |
| M6 | read, print now false | Verifier | covered, or blocked by a crash | covered | 16 | 0 | 16 | yes | — |
| M6 | read, print now false | Count check | open | open | 0 | 0 | 16 | yes | — |
| M6 | read, print still true | Verifier | open | no mutant | 0 | 0 | 0 | no valid mutant | — |
| M6 | read, print still true | Count check | open | no mutant | 0 | 0 | 0 | no valid mutant | — |
| M6 | unread | Verifier | open | open | 0 | 0 | 34 | yes | — |
| M6 | unread | Count check | open | open | 0 | 0 | 34 | yes | — |
| M7 | all | Verifier | covered | covered | 36 | 0 | 36 | yes | — |
| M7 | all | Count check | open, unless a cell holds a published string | partial | 2 | 0 | 36 | yes | 2 of the 2 blocked hold a published string |
| B1 | once | Verifier | covered | covered | 25 | 0 | 25 | yes | — |
| B1 | once | Count check | covered | covered | 25 | 0 | 25 | yes | — |
| B1 | repeated | Verifier | open | open | 0 | 0 | 25 | yes | — |
| B1 | repeated | Count check | covered | covered | 25 | 0 | 25 | yes | — |
| M1 | all | At least one of the two | open | open | 0 | 0 | 50 | yes | — |
| M4 | same section | At least one of the two | open | open | 0 | 0 | 25 | yes | — |
| M5 | checked | At least one of the two | open | open | 0 | 0 | 31 | yes | — |
| M5 | construction | At least one of the two | open | open | 0 | 0 | 4 | yes | — |
| M5 | remove | At least one of the two | open | open | 0 | 0 | 7 | yes | — |
| M6 | unread | At least one of the two | open | open | 0 | 0 | 34 | yes | — |

Q1, predicted: most figure places are in the `repeated` stratum. Result: 305 of 419. Prediction held: yes.

# Response to the blind review, phase 1, round 1

Verdict reviewed: `reviews/phase1-round1.md`, CHANGES with 7 blocking and 12 non-blocking items, on
commit 4592d9a.

The plan allowed one round. The changes below were made to the protocol and the definitions after
this verdict and **were not reviewed again**. The report says so.

Drafted by the planning agent on 14 November 2026, about 18:30 CET, for the author, who enters the
changes and commits them.

## Blocking items

| # | Item | What changed |
|---|---|---|
| 1 | The count check reads the paper it is judged against; the difference in inputs was not declared | Section 2 now says the two detectors do not get the same inputs, what the reference stands for in real use, and which of the count check's results follow from its design and are not measurements. Section 8 marks them |
| 2 | A place is a match of characters, not where the checked figure is printed | The definitions separate a place, a figure place (three characters or more, outside the References, fenced blocks and the two appendix tables) and a short place. Mutants target figure places only. Q1 is reworded: it counts where a checked string is printed, and reports short places apart. The limit that remains is declared |
| 3 | "Unit" was undefined | Defined in the definitions, with its LaTeX forms |
| 4 | The B1 operator was not exact | The format is fixed as `f"{round(v, k-1):.{k-1}f}"`. A place enters the B1 frame only if every check with its published string gives the same new string. Validity requires the new string to differ from the old |
| 5 | The source of the M6 factor was false, and some edits plant no printed error | The source is corrected. M6 now has three subgroups, decided from `_artifact_checks` and `_agree`: unread; read with the print still true; read with the print now false. Only the last enters the detection rate |
| 6 | The count check's crash and check could not be told apart, and its control did not require "by a check" | Exit code 1 for a lowered count, 2 for its own error. The M2 control requires a block by a check, with exit code 1 |
| 7 | "Not measured" had no source | The threshold is removed. Every class is reported with its counts of valid, invalid and timed-out mutants |

## Non-blocking items

| # | What changed |
|---|---|
| 1 | The source of N now counts the 35 repeated runs: 363 runs, about two hours at 20 s. Past that the stop rule cuts the campaign |
| 2 | If the verifier itself lets an M7 mutant through, the campaign goes on and it is reported first |
| 3 | A prose line is defined in the definitions |
| 4 | The order of the generator's draws and the split of an odd half are stated |
| 5 | A place is recorded by its line and its span in the line as written |
| 6 | Classes drawn by strata are reported by stratum only; nothing is pooled |
| 7 | Declared: the M6 frame leaves out `config` values the verifier reads |
| 8 | The reason a detector should block any deleted registry row is given; results are by status |
| 9 | R1 validity now excludes the References and headings, and says a detector should block. The model's settings are declared as not controllable |
| 10 | The digit rule covers exponents; signs are never changed |
| 11 | The predictions' path is named in the protocol |
| 12 | Paths are written from the repository's root |

## Not changed

- The sentence that M1 adds, ` A further run gave <figure>.`, is fixed and arbitrary. Another
  sentence could change how a reader of context would class the figure. It does not affect either
  detector of this protocol, and it goes to the limitations.
- `case/bench/results` was not in the reviewer's package, so the M6 frame was not checked. It still
  is not.

# Predictions

Written before any run and frozen in the same commit as the protocol. The blind reviewer does not
read this file. The report shows each prediction next to its result.

The verifier's column was approved by the author on 14 November. The rest is the agent's reading,
for the author to approve or change before the freeze.

## Q2: the mutants drawn by code

| Class, subgroup | Verifier | Count check |
|---|---|---|
| M1, any donor | open | open: a new figure lowers no count |
| M2, string printed once | covered | covered |
| M2, string repeated | open | covered |
| M4, same section | open | open: the counts of the section do not change |
| M4, different sections | open | covered |
| M5, row with status `checked` | open | open: it does not read the registry |
| M5, other rows | open | open |
| M6, read, print now false | covered, or blocked by a crash where the leaf is used as a key | open: it does not read the artifacts |
| M6, read, print still true | not blocked; a count, outside the rate | not blocked |
| M6, unread | not blocked; a count, outside the rate. Expected to be most of the leaves | not blocked |
| M7, every cell | covered | open, unless a cell happens to hold a published string |
| B1, string printed once | blocked every time: a false alarm | blocked every time: a false alarm |
| B1, string repeated | never blocked | blocked every time: a false alarm |

Why, in one line each:

- The verifier starts from its own checks and looks each published string up in the text. It never
  starts from a figure in the text.
- It looks for a string anywhere in the manuscript, so a second copy of the string hides a change
  to the first, and an exchange of two figures leaves both present.
- Its registry check goes from rows to checks. A deleted row leaves fewer rows to check.
- The count check notices that a checked string has one place fewer in a section. It cannot notice
  a figure that was never checked, nor two figures exchanged inside one section.

**Taken together,** the two detectors should leave open: M1, M4 inside one section, M5, and M6 on
leaves no check reads.

## Q1

Most places will be in the `repeated` stratum: the Abstract, the Introduction and the Discussion
print again the figures of section 3.

## Q3: the red team

Not predicted in numbers. Three expectations:

- part R1 will hold mostly changes to figures printed more than once, since the verifier's source
  shows the presence check;
- the verifier will block few of them, and the count check most of them;
- part R2 will include at least one attack that changes what a sentence says without changing any
  checked figure, such as a unit or a comparison word, and neither detector will block it.

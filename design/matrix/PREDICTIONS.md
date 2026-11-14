# Predictions

Written before any run and frozen in the same commit as the protocol. The blind reviewer does not
read this file. The report shows each prediction next to its result.

**Status of this draft:** the agent's reading. For the verifier it comes from reading its source.
For the matrix it is what the protocol's rules require. The author approves or changes each line
before the freeze, and may add his own.

## Q2: the mutants drawn by code

| Class, subgroup | Verifier | Matrix and gate |
|---|---|---|
| M1, donor with a unit | open | covered |
| M1, bare decimal | open | covered |
| M1, bare integer | open | open: the new figure ends unclassified or as a parameter |
| M2, string printed once | covered | partial: missed when the context marks the figure as a parameter, as in a count followed by a noun |
| M2, string repeated | open | partial: a changed decimal is blocked; a changed bare integer can leave the result category |
| M4, same section, prose | open | open: both strings still match a check of that section |
| M4, different sections | open | nearly covered: the moved string only matches a check of another section, which is a new open item |
| M4, a table cell involved | open | partial: blocked when the check names the row or the column |
| M5, row with status `checked` | open | partial: blocked unless another row names the same checks |
| M5, other rows | open | open: nothing either detector reads has changed |
| M6, leaf read by a check | covered, or blocked by a crash where the leaf is used as a key | less than the verifier: missed when the figure it feeds is a parameter by context |
| M6, leaf read by no check | open | open |
| M7, every cell | covered | covered |
| B1, string printed once | blocked every time: a false alarm | partial: not blocked when the rounding leaves an integer that stops reading as a result |
| B1, string repeated | never blocked | partial, for the same reason |

Why, in one line each:

- The verifier starts from its own checks and looks each published string up in the text. It never
  starts from a figure in the text.
- It looks for a string anywhere in the manuscript, so a second copy of the string hides a change
  to the first, and an exchange of two figures leaves both present.
- Its registry check goes from rows to checks. A deleted row leaves fewer rows to check.
- The matrix starts from each printed figure, so it sees a figure with no check. It recognises a
  result by its unit, its decimals or its table cell, and a bare integer in prose has none of these.
- In prose the matrix ties by string and section. It does not know which sentence a figure belongs
  to.

## Q2: the red team

Not predicted in numbers. Two expectations:

- part R1 will hold mostly changes to figures that are printed more than once, since the verifier's
  source shows the presence check;
- the matrix will block a smaller share of part R1 than of the mutants drawn by code.

## Q1 and Q3

- **Q1.** Most result figures will be tied by a check and few with location: only the 26 value
  cells of the two appendix tables are compared cell by cell. A visible share will be
  string-elsewhere, because the Abstract, the Introduction and the Discussion repeat figures whose
  checks belong to section 3.
- **Q3, the sheet.** Where the author and the matrix disagree on a tie, it will mostly be a repeated
  figure outside section 3 that the author calls tied and the matrix calls string-elsewhere.
- **Q3, escapes.** The commonest outcome among missed mutants will be `tied-elsewhere` for M4 and
  `unclassified` for M1.

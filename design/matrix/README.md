# The matrix: specified, not built

These three files are the fuller design the sprint started from, written on 14 November 2026 before
any run. They describe a second detector, the matrix, that reads every numeral of the manuscript,
gives it a category from its context, and ties each result to the verifier's checks.

The sprint started a day late and the matrix was not built. Its one mechanical rule, counting the
places of each checked string in each section, was built and measured as the count check of
`protocol/PROTOCOL.md`.

What is here, and its status:

- `PROTOCOL.md`: the full protocol with the matrix, sections 3 and 4, and the hand check, section 7.
  Not reviewed, not run.
- `PREDICTIONS.md`: what the matrix was expected to block, class by class, written before it
  exists.
- `definitions.md`: its vocabulary.

They are committed with the frozen protocol, so that a later build of the matrix is tested against
predictions made before it was written.

Known before building, from reading the rules against the manuscript: because the category comes
from context only, a checked figure that its context marks as a parameter gets no state, and the
matrix does not see a change to it. The matrix would not contain the verifier; it would add to it.

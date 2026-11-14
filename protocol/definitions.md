# Definitions

Base document of the protocol. It fixes the words the protocol uses and the rules of the case's
verifier that the protocol relies on. It states no expectation about any result.

## The case

- **The case** is the directory `case`: the Polar Projector paper as released, with its manuscript,
  its registry, its stored results and its verifier. It is never modified. Every run works on a copy.
- **The manuscript** is `case/paper/polar-projector-paper.md`. Lines are numbered from 1.
- **The registry** is `case/paper/claims.md`. A **registry row** is a table line with six cells whose
  first cell is an identifier: one of the letters A, C, P or R followed by digits. The third cell is
  the row's status (`checked`, `construction` or `remove`).
- **An artifact** is one of the JSON files in the case's `bench/results` directory. A **leaf** is a
  finite number, integer or float and not a boolean, found under the artifact's `results` key.

## The verifier

**The verifier** is `case/tools/verify_paper_tables.py`, run from the root of a copy of the case with
no arguments. It ends with exit code 0 when every check passes and 1 otherwise.

- **A check** is one item of the list returned by the verifier's function `_artifact_checks`: a
  label, a **published string** (the figure as the paper prints it) and a **measured value** (read
  from an artifact).
- **Agreement.** A measured value agrees with a published string when the value, rounded to the
  number of decimals the string has, equals the string read as a number. This is the verifier's
  function `_agree`.
- **Presence.** The verifier removes heading lines and section references from the manuscript,
  removes the commas that separate thousands, and reads the Unicode minus as a hyphen. A published
  string of more than one character is **present** when it appears in that text and is not part of
  a longer number: it is not preceded by a digit or a point, and not followed by a digit or by a
  point and a digit. A published string of one character is not looked for. This is the verifier's
  function `_verify_presence`.
- **A place** is one position in the manuscript where a published string of more than one
  character is present.
- **The two appendix tables.** The verifier holds constants for the tables of Appendix B and
  Appendix C, and requires each printed cell to equal its constant, with a relative tolerance of
  1e-12. This is the verifier's function `_verify_manuscript_tables`.

## Sections

The manuscript is cut at its second-level and third-level headings. **A section** is the text from
one such heading to the next. The text before the first heading is a section of its own.

## Detection

- **The control** is the unmutated copy of the case and the output of both detectors on it.
- **A detector blocks** a copy of the case when its command ends with an exit code other than 0.
- **Blocked by a check** means the detector ran to its end and reported a failure. **Blocked by a
  crash** means it stopped on an error before reporting. For the verifier, the first prints a line
  that starts with `Verdict:` and the second does not.
- **A mutant** is a copy of the case with one planted edit. It is **detected** by a detector when
  that detector blocks it. Otherwise it is **missed** by that detector.
- **A collision** is a mutant whose new figure string equals the published string of some check.

## Reporting words

For one class of mutants, or one subgroup of a class, and one detector:

- **covered:** every valid mutant is blocked by a check;
- **open:** no valid mutant is blocked;
- **partial:** anything in between, reported with its count.

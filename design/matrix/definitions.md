# Definitions

Base document of the protocol. It fixes the words the protocol uses and the three rules of the case's
verifier that the protocol relies on. It states no expectation about any result.

## The case

- **The case** is the directory `case`: the Polar Projector paper as released, with its manuscript,
  its registry, its stored results and its verifier. It is never modified. Every run works on a copy.
- **The manuscript** is `case/paper/polar-projector-paper.md`. Lines are numbered from 1.
- **The registry** is `case/paper/claims.md`. A **registry row** is a table line with six cells whose
  first cell is an identifier: one of the letters A, C, P or R followed by digits. The third cell is
  the row's status (`checked`, `construction` or `remove`). The sixth cell names, between backticks,
  the checks that back the row.
- **An artifact** is one of the JSON files in the case's `bench/results` directory. A **leaf** is a
  finite number, integer or float and not a boolean, found under the artifact's `results` key.

## The verifier

**The verifier** is `case/tools/verify_paper_tables.py`, run from the root of a copy of the case with
no arguments. It ends with exit code 0 when every check passes and 1 otherwise.

- **A check** is one item of the list returned by the verifier's function `_artifact_checks`: a
  label, a **published string** (the figure as the paper prints it) and a **measured value** (read
  from an artifact). A check's **section** is the section number that follows the sign § at the
  start of its label.
- **Agreement.** A measured value agrees with a published string when the value, rounded to the
  number of decimals the string has, equals the string read as a number. This is the verifier's
  function `_agree`.
- **Presence.** The verifier removes heading lines and section references from the manuscript,
  removes the commas that separate thousands, and reads the Unicode minus as a hyphen. A published
  string of more than one character is **present** when it appears in that text and is not part of
  a longer number: it is not preceded by a digit or a point, and not followed by a digit or by a
  point and a digit. A published string of one character is not looked for. This is the verifier's
  function `_verify_presence`.
- **The two appendix tables.** The verifier holds constants for the tables of Appendix B and
  Appendix C. It reads the two tables from the manuscript and requires each printed cell to equal
  its constant, with a relative tolerance of 1e-12. Separately, it recomputes each constant and
  requires the recomputation to agree with the constant: within two decades for Appendix B, within
  0.1 % for Appendix C. This is the verifier's function `_verify_manuscript_tables` and its `main`.
- **Registry check.** For each row whose status is `checked`, each name between backticks must be
  the beginning of some check's label, or one of three reserved names. This is the verifier's
  function `_verify_registry`.

## The matrix

- **A token** is one numeral as the reader finds it in the manuscript: its string, its line, and
  its **rank**, the count of tokens before it on the same line, from 0.
- **Section.** A token's section is the pair of the nearest second-level heading and the nearest
  third-level heading above it. Its **section number** is the number or letter that starts the
  nearest of the two that has one (`3.5`, `4.1`, `B`). The Abstract and the Introduction have their
  own names as section numbers.
- **Context.** One of: heading, table, formula (a display formula), caption, list, prose.
- **Category.** One of: result, parameter, math, environment, citation, structure, notation,
  unclassified. The protocol gives the rules.
- **State.** Only a result has one: tied-located, tied-check, tied-check-1c, string-elsewhere,
  check-fails or untied. The protocol gives the rules.
- **Tied.** A result is tied when its state is tied-located, tied-check or tied-check-1c.
- **Two strings share a word** when some word of four letters or more in one, lower-cased, begins
  a word of the other or is begun by it.

## The gate, and detection

- **The control** is the unmutated copy of the case and the outputs of both detectors on it.
- **An open item** is a triple of section number, figure string and state, for a result whose state
  is string-elsewhere, check-fails or untied; or a triple of section number, figure string and the
  word `no-row`, for a tied result none of whose checks is named by a registry row.
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

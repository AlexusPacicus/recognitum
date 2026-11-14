<!--
Blind review, phase 1, round 1. Verdict stored as returned by the kit's blind-reviewer subagent.
Record: protocol/PROTOCOL.md at 4592d9ab36b08e2b8b5cc656db293fabc1a3cbf1.
Package: built by tools/audit/build_review_package.py build --lock, 2026-11-14.
Delegation message: package path, record, phase, git facts and the builder's unresolved citations; nothing else.
-->

**Blindness statement**
I read only files inside the package:
- `MANIFEST.json`
- `.claude/skills/blind-review/SKILL.md` (the procedure)
- `protocol/PROTOCOL.md` (the record)
- `protocol/definitions.md` (the base document)
- `case/paper/claims.md`
- `case/tools/verify_paper_tables.py`
- `case/paper/polar-projector-paper.md`, in part: a heading grep, lines 1176–1254, and a grep for standalone two-digit numerals

I made no attempt to read outside the package. No Read was denied. My context held no CLAUDE.md, memory or git snapshot. Neither the delegation message nor any file I read states an expected or prior result of this sprint. `claims.md` and the manuscript hold the case paper's own figures, which are the object being mutated, not results of this protocol. The manifest lists one denied prefix, `reviews/`, and as built I cannot tell whether a prior review exists. Phase 1 applies: the caller gave no fact saying the sprint code exists.

**Gate**
- The record and the base document are committed in 4592d9ab36b08e2b8b5cc656db293fabc1a3cbf1 (caller's git facts).
- Every phase-1 item is answered below.
- The caller did not give the round number; I treat this as round 1.
- Unresolved citations:
  - `bench/results` (that is, `case/bench/results`) is not in the package. I could not check the M6 frame: which leaves exist and how many per artifact.
  - `tools/verify_paper_tables.py` is cited relative to the copy's root. It resolves to `case/tools/verify_paper_tables.py`, which is in the package.
- Also cited but not in the package and not in the manifest: `DEVIATIONS.md` (presumably not written yet), and the "predictions" of §6 step 1, which the record never names by path.

**What holds**
- The definitions match the verifier's code:
  - agreement = `_agree` (verify_paper_tables.py:246-248)
  - presence = `_verify_presence` (:599-627)
  - the appendix tables use rel_tol 1e-12 (:187-211)
  - exit codes 0/1 and the "Verdict:" line printed in both outcomes (:725-731)
  - the registry row rule (:644-654)
- 42 registry rows: A1–A15, C1–C22, P1, R1–R4 (claims.md:68-124). The statuses are checked, construction and remove.
- 36 appendix cells: B is 4×3 (paper:1185-1190), C is 6×4 (paper:1235-1242).
- M7 is a real positive control. Any digit change in a cell moves its value past rel_tol 1e-12 or breaks the row-key set, so a broken harness can make it fail.
- Seeds are fixed. Draw order is fixed (sorted by file, line and position). The frames never read the count check.
- Both detectors run on identical copies.
- The red team is separated from the count check (frozen before any response is opened), and the R2 rulings are written before any detector runs.
- Validity, timeout, invalid, collision and repetition rules are stated, and failed mutants are never counted as misses.
- One results line per mutant. No figure in the report is typed by hand.

**Blocking items**
1. **The count check reads the paper it is judged against, and the input difference is not declared.** PROTOCOL.md:30, 32-36 and 19.
   - Q2/Q3 judge each mutant "against the paper as released". The count check reads that very manuscript (the control) as its reference; the verifier does not.
   - This breaks "nothing reads the answer it is judged against". The two detectors also get different inputs, and §2 "Differences" (lines 38-46) does not list this.
   - Fix: declare it and state what the reference stands for in real use (for example, the last accepted version). Also state that any count-lowering edit is detected by construction, so Q2's count-check figures for such classes are not measurements.
2. **"Place" is a lexical match, but Q1 and the M2/M4/B1 ground truth treat it as "where the paper prints the checked figure".** PROTOCOL.md:13-14, 59-61, 66-67, 71; definitions.md:34-35.
   - Two-digit published strings such as "11", "15", "24", "29", "28", "80" and "90" (verifier :456, :469-470, :505, :510, :520, :538, :514) match unrelated numerals in the manuscript:
     - algorithm step numbers (paper:313, 319, 327)
     - k = 15 and recall@15 (paper:508, 584, 721-722)
     - the exponent 10^{-11} (paper:1189, 1213)
     - reference numbers and journal volumes (paper:1056, 1064, 1068, 1077, 1087, 1089, 1104, 1110)
   - These inflate the `repeated` stratum and Q1. They also become M2/M4 targets labelled "should block: yes" and B1 targets whose "check's measured value" does not belong to that place.
   - Fix: define, before any run and without detector output, which places print the checked figure, and report the rest as a recorded subgroup or exclude them. Then align Q1's wording with that definition.
3. **"Unit" is undefined.** PROTOCOL.md:65 (M1 donor) and 67 (the M4 frame: "the same unit after them, or none after both").
   - Which tokens after a figure count as a unit (µs, ms, s, %, ×, MB, a closing bracket)? This decides who is in the M4 frame and so which pairs are drawn.
4. **The B1 operator is not exact.** PROTOCOL.md:71.
   - (a) Formatting is unspecified. Python's `round` returns a float, so `str(round(59.98, 0))` is "60.0": no change from "60.0", hence an invalid or empty mutant. `str()` also drops trailing zeros, so a 3-decimal string rounded to 2 decimals can come out with 1.
   - (b) Many published strings map to several checks with different measured values, for example "0.543", "1.17", "4.66", "0.0000", "1.46", "1.01", "4.3", "3.2" (verifier :304-310, :318-321, :341-359, :427-437, :554-564). "The check's measured value" is ambiguous.
   - Both choices change which B1 mutants are valid and the false-alarm rate, and can push B1 past the "not measured" line.
   - Fix: fix the formatting (for example `f"{round(v, k-1):.{k-1}f}"`) and a rule for picking the check.
5. **The M6 factor's source is false, so the "should block: yes" label is wrong for some leaves.** PROTOCOL.md:69 and 192.
   - Multiplying by 1.5 does not change the first digit when the mantissa is in [1, 4/3): 1.2 becomes 1.8.
   - More importantly, some leaves read through printed or threshold precision stay correct after the edit: still-step p95 values of about 4e-16 printed as "0.0000", or compared with `< 1e-9` and `< 1e-12` (verifier :300, :478). Their measured value changes (recorded `read`), yet the manuscript stays true. The verifier then gets a "miss" on an edit that plants no error.
   - Fix: correct the source, and define before any run how such leaves are labelled or grouped.
6. **For the count check, "blocked by a crash" and "blocked by a check" cannot be told apart, and its positive control does not require "by a check".** PROTOCOL.md:30, 34-35, 135; definitions.md:49-51.
   - The crash/check rule is defined only for the verifier (the "Verdict:" line). An uncaught Python exception also exits with code 1.
   - The M2 control row says only "blocks", unlike M7's "by a check". A count check that crashes on mutated copies (but not on the control) therefore passes its positive control, which means the control cannot fail in that case.
   - Fix: give the count check a distinct crash signal (another exit code or a final line) and require "by a check" in the M2 control.
7. **A threshold has no source.** PROTOCOL.md:195, "Not measured: more than one mutant in ten — Chosen before any run; no further source".
   - The procedure treats a threshold without a source as a CHANGES item, and this one decides whether a class is reported at all.

**Non-blocking items**
1. PROTOCOL.md:190: the source arithmetic does not close.
   - At t = 20 s: 5×50 + 42 + 36 = 328 verifier runs, about 109 min. Adding the repetition control (5 per class × 7 classes = 35 runs) gives about 121 min, more than two hours.
   - At N = 30 the run fits only if t ≤ about 31 s, and there is no rule for a larger t.
2. PROTOCOL.md:134: say whether the campaign continues when the verifier itself, and not the harness, lets an M7 mutant through. As written, "The campaign stops" sits next to "reported first".
3. PROTOCOL.md:65: define "prose lines": list items, captions, display math, table rows and the algorithm block at paper:300-330.
4. PROTOCOL.md:51-53 and 65-67: give the order of RNG draws for compound operators (M1 line, then donor, then digits; M4 pairs; the digit choice in M2/M7) and how an odd half is split.
5. PROTOCOL.md:59 and 52-53; definitions.md:28-35: presence runs on normalized text (thousands commas removed, headings and section references removed). Say how a place maps back to file, line and column for sorting and editing, for example "3,749" at the place behind "3749".
6. PROTOCOL.md:176-179: M2, M4 and B1 draw strata with equal allocation, so the pooled class proportion is not the frame's proportion. Give per-stratum Wilson intervals or weight them.
7. PROTOCOL.md:69: the M6 frame (leaves under `results`) excludes `config` values the verifier reads (verifier :527-537). Declare it.
8. PROTOCOL.md:68: deleting a registry row can never fail the verifier, which checks only rows that are present (verifier :640-672). Give the "should block: yes" rationale for rows whose status is `remove` or `construction`, or label them.
9. PROTOCOL.md:122-123 and 92-95:
   - R1 validity does not require that the changed number be a result (a citation year or a reference number would pass), and the "should block" label for R1 is only implied.
   - The model's sampling parameters are not fixed.
10. PROTOCOL.md:55-57 and 70: say how the shared digit rule ("integer part of two digits or more") applies to exponents such as "-14" in the Appendix B cells.
11. PROTOCOL.md:140: name the path of the "predictions" frozen with the protocol. The git facts show only PROTOCOL.md and definitions.md in the reviewed commit, so the reviewer cannot confirm the freeze.
12. Citation form: write `case/tools/verify_paper_tables.py` and `case/bench/results` as repository paths, or say "of the copy", so the package builder resolves them.

**Verdict:** CHANGES, with 7 blocking items (listed above) and 12 non-blocking items. The blocking items must be fixed and the record reviewed again before phase 2.

**Reviewed by: line text**
Reviewed by: Claude Code (blind-review, claude-opus-5-5), 2026-11-14, phase 1, commit 4592d9ab36b08e2b8b5cc656db293fabc1a3cbf1, CHANGES (7 blocking, 12 non-blocking)

Files read:
- /private/tmp/claude-501/-Users-test-Documents-NGI-recognitum/78620479-8b59-4398-a403-f8f3f935295a/scratchpad/review-phase1/protocol/PROTOCOL.md
- /private/tmp/claude-501/-Users-test-Documents-NGI-recognitum/78620479-8b59-4398-a403-f8f3f935295a/scratchpad/review-phase1/protocol/definitions.md
- /private/tmp/claude-501/-Users-test-Documents-NGI-recognitum/78620479-8b59-4398-a403-f8f3f935295a/scratchpad/review-phase1/case/tools/verify_paper_tables.py
- /private/tmp/claude-501/-Users-test-Documents-NGI-recognitum/78620479-8b59-4398-a403-f8f3f935295a/scratchpad/review-phase1/case/paper/polar-projector-paper.md
- /private/tmp/claude-501/-Users-test-Documents-NGI-recognitum/78620479-8b59-4398-a403-f8f3f935295a/scratchpad/review-phase1/case/paper/claims.md

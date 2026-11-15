# Related work: draft for the report

Draft by the agent, 15 November 2026, for the author to read, correct and move onto the official
template. The author opens every reference before it goes in. What the agent checked:

- opened in this session, title, authors and abstract read: Alfaqeeh et al. (arXiv 2610.38691),
  Litvak (arXiv 2611.12820), Cotton-Barratt and Finnveden (Forethought, 2026);
- cited from memory, not opened: DeMillo, Lipton and Sayward (1978); Jia and Harman (2011);
  Nuijten et al. (2016);
- the author's own report, as the README cites it.

The figures quoted from other papers are not in this repository's sources, so this file is kept
apart from `method-results.md`, which `analysis/check_report.py` checks.

## Related work

**Mutation testing.** Planting small faults in a program and counting how many a test suite catches
is an old way to measure a test suite rather than the program (DeMillo, Lipton and Sayward, 1978;
see Jia and Harman, 2011, for a survey). We apply the same idea one level up: the program under test
is a claims verifier, and the mutants are edits to the paper and to the records it checks.

**Checking the numbers of a paper.** Some tools check reported statistics for internal consistency,
such as statcheck, which recomputes p-values from the test statistics a paper reports (Nuijten et
al., 2016). Others generate the numbers of a document from code, so that a printed figure cannot
drift from its source. The case studied here is a third pattern: a registry of the paper's numerical
claims and a verifier, run in CI, that ties each registered figure to stored code output (the
author's report on the method: Zapico Fernández, 2026). That report's limits section says that checks
in both directions between registry, text and code would catch part of what the verifier misses,
and that this was not tested. We do not propose the pattern; we measure what it lets through.

**Verifying numerical claims in papers written by AI agents.** Alfaqeeh et al. (2026) re-analyse the
judgments of a public benchmark of AI research agents and label 256 numerical claims by hand. They
find that most unsupported claims are not fabricated: about four in five are values from the
agent's own files, taken from the wrong experiment, metric or run. They describe the existing checks
as testing a paper for internal consistency or testing "whether a reported value appears somewhere
in an agent's output", which is the presence check of the verifier studied here, and they introduce
a deterministic checker that scores whether the context around a number identifies the claimed
result. Our measurements are of the other side of that problem. They study the errors that agents
make in practice; we plant errors and ask a model to write some, to count which ones a presence
check lets through, and how many places in one paper it leaves unprotected.

**Planted errors as ground truth.** Litvak (2026) plants 100 errors into 10 psychology papers and
runs them through frontier models and commercial AI review tools: the best single system catches
71, all of them together 93, and the seven that none catches are all omissions. False positives
were not measured. Our setting differs in what is evaluated (a deterministic check that already runs
in CI, not a reviewer), and we count false alarms with edits that plant no error (class B1). The
omissions point the same way in both: a deleted row of the registry escapes both of our detectors.

**Trust infrastructure.** Cotton-Barratt and Finnveden (2026) warn of trust lock-in: tools that win
early trust may not deserve it, and incumbency makes them hard to displace. They call for open and
auditable epistemic infrastructure, so that whether a tool is trustworthy can be measured. A
verifier that passes in CI is such a tool on a small scale: its green check is read as "the figures
were checked". This project measures how much of the paper that check actually covers.

## References

- Alfaqeeh, M., Horani, O. M., Hourani, M. and Alfaqeeh, H. (2026). Beyond fabrication:
  Misattributed numbers in papers written by AI research agents. arXiv:2610.38691.
- Cotton-Barratt, O. and Finnveden, L. (2026). AI for AI for Epistemics. Forethought.
  https://www.forethought.org/research/ai-for-ai-for-epistemics
- DeMillo, R. A., Lipton, R. J. and Sayward, F. G. (1978). Hints on test data selection: Help for
  the practicing programmer. *Computer*, 11(4), 34–41.
- Jia, Y. and Harman, M. (2011). An analysis and survey of the development of mutation testing.
  *IEEE Transactions on Software Engineering*, 37(5), 649–678.
- Litvak, P. (2026). How well does AI peer review work? A benchmark built from 100 planted errors.
  arXiv:2611.12820.
- Nuijten, M. B., Hartgerink, C. H. J., van Assen, M. A. L. M., Epskamp, S. and Wicherts, J. M.
  (2016). The prevalence of statistical reporting errors in psychology (1985–2013). *Behavior
  Research Methods*, 48(4), 1205–1226.
- Zapico Fernández, A. (2026). Technical report on the method, version 1.1. Zenodo.
  https://doi.org/10.5281/zenodo.24163509 *(title to be filled in by the author)*

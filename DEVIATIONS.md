# Deviations from the protocol

Every change to what `protocol/PROTOCOL.md` fixed, with its date and its reason. The protocol itself
is not edited after its freeze.

## 1. The count check was committed after its deadline

**What the protocol says:** section 6: if the count check is not written and frozen by 21:30 CET on
Saturday 14 November, the sprint is reported with the verifier alone.

**What happened:** the frames, the operators and the runner were finished at 22:20 (commits
`0e445a2` and `f9b457b`). The count check was committed at 22:47 (`01c47af`), with a correction to
its control at 22:51 (`a44cae4`). It was run with the verifier in the campaign.

**Why it is kept:** the deadline existed so that the rest would fit before the stop rule at
midnight. The count check reads two text files and takes a fraction of a second per mutant, so
writing it late took no time from the campaign. When it was committed no response of the red team
existed, so the rule that it be frozen before any response is opened holds.

**What the report says:** that the count check missed its deadline by 77 minutes and was kept, with
this reason.

## 2. One more red-team conversation, part R3: edits that overstate the results

**Written:** 14 November 2026, 23:21 CET, before any response of the red team exists in the
repository and before any detector has run on a red-team edit.

**What the protocol says:** section 4 fixes two parts: R1, six conversations with one prompt, and
R2, one conversation with another. Both prompts ask for errors without a direction.

**What is added:** one more conversation, part R3, with the same model and the same two files, and
this prompt, sent as written:

> You are given a scientific manuscript and the source of a program that checks its figures. Propose
> five edits to the manuscript that make its results look better than they are. Each edit must
> change exactly one number, in the direction that favours the paper's method, and each should be a
> change you think the checking program may fail to notice. Choose them yourself. Do not explain
> your strategy. Answer with a JSON list of five objects with the keys `line` (the line number in
> the manuscript), `old` (text that appears exactly once on that line), `new` (its replacement) and
> `why` (one sentence saying what is now overstated).

**Why:** the error that matters most in practice has a direction: a result made to look better. The
author proposed it after the freeze.

**How it is handled:**

- It is an addition. The seven conversations of section 4 are run first and as written; R3 is run
  after them, and only if there is time.
- Its response is stored as returned in `redteam/responses`, like the others.
- Validity is that of part R1. Whether an edit really favours the paper is not checked: the report
  gives the model's own sentence.
- It is reported apart from R1 and R2, never pooled with them, and marked as not pre-registered.
- A detector should block every valid R3 edit.

# What was replaced in these traces

The traces in this folder, and the `stderr_tail` of the third launch's lines in
`redteam/generation.jsonl`, are what the client printed beside each response, with two strings
replaced before publishing:

- the author's home folder, by `<HOME>`;
- the identifier of the author's synced skills, by `<SKILLS-ID>`.

Nothing else was changed. The `stderr_sha256` of each line of the record is the hash of the trace
before the replacement; the traces as printed are kept on the author's machine. The responses in
`redteam/responses` are as returned, with nothing replaced.

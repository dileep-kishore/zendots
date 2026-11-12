# Grounding

Finders sometimes cite files, lines, or quotes that do not exist. A missing
citation does not prove a finding false, but it does prove the report
described something its author did not read. The coordinator checks
citations mechanically, never judges a finding with them, and stops a
report that fails the check from counting as coverage.

## Check each report

After every finder finishes and before merging duplicates, check the
citations in each original report against the pinned state. Record the
result per report and per finding; a merged finding keeps each source's
result.

A citation is grounded when all of these hold:

- **Path.** The file exists at the pinned state: `git cat-file -e
  <pinned>:<path>` for committed content; on disk under the checkout for
  working changes, design documents, and ignored files such as drafts; or
  the absolute path the brief named. For a file the diff deletes or modifies,
  the base revision counts too: a finder may quote removed text and cite
  old-side line numbers.
- **Lines.** `1 <= start <= end <= line count + 1` at that state; the extra
  line is the empty one some viewers number after the final newline. A
  single line has `end = start`.
- **Quote.** Text of 4 or more words that the finding attributes to a named
  file, in quotation marks or a code span, appears in that file once both the
  quote and a copy of the file have each line's leading `>`, `#`, `//`, `*`,
  or `--` marker removed and whitespace collapsed to single spaces.
  Check a quote attributed to the intent, spec, or diff against that pinned
  file, never against saved command output.

```bash
norm() {  # [:space:] includes CRLF's \r
  sed -E 's,^[[:space:]]*(>+|#+|//+|[*]+|--)[[:space:]]?,,' | tr '[:space:]' ' ' | tr -s ' '
}
norm < "$file" > "$scratch/norm.txt"
printf '%s' "$quote" | norm | rg -qF -f - "$scratch/norm.txt"
```

An **ungrounded citation** is a missing path, an invalid line range, or an
unfound quote. In one report, each distinct path and each distinct quote
counts once, however many findings repeat it. The quarantine threshold and
the log's `ungrounded` column both use this count.

## Verify every finding anyway

A grounding miss never refutes. Every finding goes to verification:

- Give the verifier each miss as a fact: the citation, the command, and its
  output.
- Findings whose citations are all ungrounded share one verifier per finder
  report, like the P3 batch. Others keep one verifier per P0 to P2 finding.
- A REFUTED verdict whose only failing gate is the missing citation enters
  the ledger as `dismissed (ungrounded)`. It never suppresses a later finding
  of the same failure that cites grounded paths.

## Quarantine a report

A report is quarantined when either holds:

- **Grounding trigger**, before verification: 2 or more ungrounded
  citations.
- **Verification trigger**, after verification: 3 or more findings with at
  least two thirds REFUTED, and no accepted fallback report covers the seat.

A quarantined report's findings stand on their verdicts. Discard the rest of
it: concern map, coverage claims, `None` results, Requirements marks, and
score. Its score reads `withheld (ungrounded)` or `withheld (refuted)`.

On the grounding trigger, relaunch the seat at once by its fallback in
[reviewers.md](reviewers.md), under that file's fallback rules, in parallel
with verifying the first report's findings. Do not cancel or discard the
first report. Ground and verify the fallback report like any other before
triage; when it is not quarantined, it supplies the seat's coverage and
score. A seat with no fallback, or whose fallback is quarantined too, is
partial, and its lens is uncovered.

The verification trigger fires too late to relaunch. With no accepted
fallback, report the lens as uncovered and the review as partial.

These rules apply to every finder model.

## Check verifier citations

Apply the path and line rules to each REFUTED verdict's refuting file:line.
When a finding's ungrounded citation names code or text that does not exist,
the verifier may refute with the search it ran and its empty output instead;
check that the search names real directories. An ungrounded refuting citation makes the verdict UNVERIFIED:
rerun it once with a fresh verifier, whatever the severity. If the rerun's
citation is ungrounded too, the finding stays UNVERIFIED and `open`.

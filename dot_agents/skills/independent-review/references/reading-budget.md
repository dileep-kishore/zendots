## Reading budget

This budget outranks thoroughness. Agents on this model tend to read files in
small slices, re-read what they already have, and open files they guess at.

1. Start from the saved diff and the list of changed files named under
   Scope. Do not explore the repository tree.
2. Read each file you need once: in full when it is under 800 lines,
   otherwise in blocks of at least 200 lines. Never read a range you already
   read, and never re-read to confirm something.
3. Before opening a file outside the change, find the exact lines with one
   `rg -n` call and read only that region. Never guess a path; list
   candidates with `rg --files <dir>` first.
4. Use at most 12 reads of files outside the change and at most 60 tool calls
   in total. When either runs out, stop and write the report, and list what
   you did not read under Coverage.
5. After every 15 tool calls, ask: what have I found, what is left, and is the
   next read necessary to settle a finding?

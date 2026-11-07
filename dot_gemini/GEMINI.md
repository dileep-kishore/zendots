# Reading files

Every read stays in the context sent with each later turn and spends quota,
so read the way a careful engineer would.

- Locate before reading. Find a symbol or string with one `rg -n` call (or
  `grep_search`) and read only the region it points to. Never guess a path;
  list candidates with `rg --files <dir>` first.
- Read each file once, in full when it is under 800 lines, otherwise in
  blocks of at least 200 lines. Never read 10 to 30 line slices of the same
  file in a row.
- Never re-read a range already in context, before or after an edit. Trust
  the edit tool's result instead of reopening the file to confirm it.
- Do not survey the repository. Read only what the current step needs, and
  stop reading once you can act.
- If the same read or search would repeat, stop and state in one sentence
  what you still need, then take a different approach.
- When a task names its scope, work within it without asking; when it needs
  many files, read the most relevant first and say what you skipped.

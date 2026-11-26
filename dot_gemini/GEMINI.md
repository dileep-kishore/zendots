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

# T3 Code browser and macOS captures

- For browser work in T3 Code, call `preview_status` first. When it returns
  `available: false` with `tabId: null`, call `preview_open` without a
  `tabId`. Pass `open: true` when the user wants to watch. For a local dev
  server on the thread's host, pass
  `target: {kind: "environment-port", port}`.
- Run desktop capture and GUI tools from the logged-in macOS GUI session.
  Before capturing on a headless Mac, check the console lock with
  `ioreg -n Root -d1 | grep CGSSessionScreenIsLocked`, where no match means
  unlocked. If the display is asleep, try `caffeinate -u -t 2` and recheck.
  If a screen lock remains, stop and report it.

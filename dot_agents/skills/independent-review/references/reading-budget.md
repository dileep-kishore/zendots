## Reading budget

Every Gemini finder gets a context bundle and the rules below, inserted before
its Intent section. Without them, Antigravity's Gemini models read files in
small slices, open files they guess at, search the web, and run analysis
scripts. In a November 2026 benchmark the bundle cut Carbon's reads from 16 to
57 per review to 3 to 14, with no range read twice.

### Build the bundle

When you launch a Gemini finder, and not before (a seat that might fall back
to Gemini later needs no bundle until then), write `bundle.md` into the
private directory. Number every file you include with its real line numbers
(`nl -ba -w4 -s': ' <file>`), and exclude `.claude/` and other worktree copies
from every search.

- **Change review:** the log, the diffstat, and the full diff; each changed
  file in full at the pinned state (for a file over about 1,500 lines, its
  changed hunks with 40 lines of context instead); for each changed function,
  class, or config key, the `rg -n` hits outside the change and the 20 to 60
  lines each important hit points at; and the paths and sizes of changed test
  files left out.
- **Design review:** the spec and its intent file in full; the `REVIEW.md`
  files and earlier specs pinned with them; and, for each module, command, or
  config key the spec names, the `rg -n` hits in the code and the lines around
  them.
- **Repository or folder audit:** the scope manifest; the README, build and
  deploy configuration, and entry points; the files on the main data flows you
  mapped, in full up to about 3,000 lines in all; and every other file in scope
  listed under "Paths to inspect" with its size.

Fill `<N>` below with the bundle's line count and `<PAGES>` with page starts
every 600 lines (1, 601, 1201, ...). `agy`'s file tool returns at most 800
lines or 46,080 bytes per call, and 600 numbered lines usually fit both. Fill
`<CALLS>` with 20 plus 10 per page after the first, and `<MINUTES>` with this
finder's own deadline minus 5. Render the rules again for each launch: a
fallback model gets its own deadline, so its numbers differ.

### Rules to insert

```markdown
## Working rules (read first; they outrank thoroughness)

1. Everything you need is in one file: `<bundle path>` (<N> lines). Read it
   once, one call per page, starting at lines <PAGES>. When the tool says a
   page was cut at its byte limit, make the continuation call it names; that
   is not a re-read. Do not read the files the bundle already holds in full.
2. Read nothing else unless a finding needs a line the bundle lacks, or the
   bundle lists the path under "Paths to inspect". Then make one search for
   the exact symbol and one read of at most 120 lines around the hit. At most
   10 such extra reads in the whole review.
3. Never re-read a file or a range you already have.
4. Do not search the web, open URLs or a browser, run shell commands, start
   subagents, call MCP or T3 tools, or write any file. You review by reading.
5. Stop at <CALLS> tool calls or <MINUTES> minutes, whichever comes first, and
   write the report with what you have; list what you did not check, and each
   lens or area the bundle did not let you cover, under Coverage.
6. Think, then write the whole report once, as your final message.
```

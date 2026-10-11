---
name: clean-comments
description: Use when the user asks to clean up, audit, or de-slop code comments, or to remove AI-sounding, noisy, or redundant comments from a file, diff, branch, or repository.
---

# Clean comments

Remove comments that read as generated and keep the ones that carry
information. Only comments change; the code, its formatting, and its behaviour
stay byte-for-byte the same.

## 1. Scope

Work on what the user names. With nothing named, take the uncommitted change,
untracked files included. Read each comment with the code it sits on before
judging it.

For an audit or review request, list the proposed removals and rewrites per
file with their line numbers and edit nothing. Apply them only when the user
asks for the cleanup.

Never touch executable code, identifiers, imports, whitespace outside the
comment, docstrings (they are runtime strings, not comments), license headers,
encoding declarations, shebangs, type comments and linter pragmas
(`# type: int`, `// eslint-disable`, `# noqa`), or generated files.

## 2. Remove

- Banners: `// ===== AUTH =====`, `# -------- ROUTES --------`, box drawing.
  Keep a plain one-line label only where a long file needs it.
- Restating the line: `// Initialize count` above `count = 0`, `// User class`.
- Step narration: `// Step 1: validate`, `// First...`, `// Finally...`, or a
  comment on every line. One comment per logical block at most.
- Empty labels: `// Main logic`, `// Helper function`, `// Important!`.
- TODOs that name no task: `// TODO: improve this`. Keep a TODO that says what
  and why.
- End markers: `} // end if`, `# end of function`.
- Decorative emoji: `// ✅ Validation`, `// 🚀 Fast path`.
- Stiff or loud wording: rewrite `// MAIN LOGIC` or a formal paragraph as a
  short sentence-case note.

## 3. Shorten

A comment that is all true but runs to a paragraph: cut it to the constraint
itself, one line, two when the second is a separate fact. Drop the issue
number, version history, and "because X, so Y, therefore Z" chain.

## 4. Keep

Comments that explain intent, a business rule, an architectural decision,
security, performance trade-offs, concurrency, protocol details, API
contracts, workarounds, edge cases and assumptions, and legal notices. These
may be shortened, never deleted.

```js
// Stripe retries webhook deliveries for up to three days.
// Ignore duplicate events using the event ID.
```

## 5. Verify

Read every hunk of the diff: each removed or added line must be a comment or
blank. For Python, run the bundled checker from inside the repository, passing
the files you cleaned:

```bash
python3 -I ~/.agents/skills/clean-comments/scripts/check_comments_only.py <file>...
```

It compares token streams with `HEAD`, ignoring only ordinary comments and
blank lines, and exits 0 when no code changed. Fix any file it prints as
`CODE CHANGED`. `UNCHECKED` means a version did not tokenize, and `NEW FILE` or
`DELETED` means there is no baseline to compare; review those hunks by hand.
Then run the project's formatter check and tests.

## Output

Per file: comments removed, shortened, and any kept on purpose that a reader
might expect gone, with one line saying why. For an audit, the proposed
changes instead.

Adapted from `antislop-code` in miqdadbadjuber/anti-slop.

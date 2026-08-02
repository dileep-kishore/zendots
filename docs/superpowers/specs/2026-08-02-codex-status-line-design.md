# Codex Status Line Native Parity Design

## Goal

Make the managed Codex footer resemble the Claude Code status line as closely
as Codex's native status items allow.

## Options

1. Use native Codex items (recommended): add branch changes and show context
   used instead of context remaining. This is supported and needs no script.
2. Keep the current footer: supported, but it omits change counts and presents
   context in the opposite direction from Claude.
3. Patch or wrap Codex for exact parity: would be fragile and is unnecessary.

## Change

Edit only `dot_codex/private_config.toml.tmpl`:

- keep `model-with-reasoning`, `current-dir`, `git-branch`, `five-hour-limit`,
  `weekly-limit`, and `fast-mode`;
- add `branch-changes`;
- replace `context-remaining` with `context-used`.

Codex does not expose custom footer scripts, cost, elapsed time, Vim mode,
worktree name, or custom progress-bar styling, so those Claude fields remain
out of scope.

## Verification

Render the chezmoi template and parse the result as TOML. Then show the scoped
`chezmoi diff ~/.codex/config.toml`. Do not apply it without user confirmation.

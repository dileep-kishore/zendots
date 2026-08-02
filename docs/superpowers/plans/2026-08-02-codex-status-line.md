# Codex Status Line Native Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the managed Codex footer match the Claude Code status line as closely as Codex's native items allow.

**Architecture:** Keep Codex's built-in `[tui].status_line` and change only its ordered item list. Do not add a renderer, wrapper, dependency, or test file.

**Tech Stack:** chezmoi templates, TOML, Python standard-library `tomllib` for verification

## Global Constraints

- Modify only `dot_codex/private_config.toml.tmpl`.
- Preserve all unrelated working-tree changes.
- Do not add automated tests for this dotfiles configuration.
- Do not run `chezmoi apply` without explicit user confirmation.

---

### Task 1: Configure native status-line parity

**Files:**
- Modify: `dot_codex/private_config.toml.tmpl:16`

**Interfaces:**
- Consumes: Codex's native `tui.status_line` item identifiers.
- Produces: An ordered footer containing model/reasoning, directory, branch,
  branch changes, context used, rate limits, and fast-mode state.

- [ ] **Step 1: Update the item list**

Replace the existing status-line list with:

```toml
status_line = [
    "model-with-reasoning",
    "current-dir",
    "git-branch",
    "branch-changes",
    "context-used",
    "five-hour-limit",
    "weekly-limit",
    "fast-mode",
]
```

- [ ] **Step 2: Render and validate the template**

Run:

```bash
chezmoi execute-template < dot_codex/private_config.toml.tmpl |
  python -c 'import sys, tomllib; data = tomllib.loads(sys.stdin.read()); assert data["tui"]["status_line"] == ["model-with-reasoning", "current-dir", "git-branch", "branch-changes", "context-used", "five-hour-limit", "weekly-limit", "fast-mode"]'
```

Expected: exit code 0 with no output.

- [ ] **Step 3: Inspect the focused source diff**

Run:

```bash
git diff --check -- dot_codex/private_config.toml.tmpl
git diff -- dot_codex/private_config.toml.tmpl
```

Expected: only `branch-changes` is added and `context-remaining` becomes
`context-used`.

- [ ] **Step 4: Commit the source change**

```bash
git add dot_codex/private_config.toml.tmpl
git commit -m "feat(codex): align status line with claude"
```

- [ ] **Step 5: Preview the destination change**

Run:

```bash
chezmoi diff --no-pager ~/.codex/config.toml
```

Expected: the rendered `~/.codex/config.toml` status-line list has the same two
focused changes. Show this diff and request confirmation before applying it.

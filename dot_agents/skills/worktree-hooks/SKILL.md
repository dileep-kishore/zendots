---
name: worktree-hooks
description: Generate the setup (and where supported, teardown) shell script that makes a newly created git worktree usable, for Orca, T3 Code, or any host that runs a script on worktree creation. Explores the repo to decide which gitignored files to copy, which large data to symlink, and which dependencies to reinstall, then delivers the script in the form that host expects. Use when the user says "worktree setup script", "orca worktree hooks", "t3 code setup script", "setup action", "t3.json", "archive script", or asks how to make new worktrees usable without manual setup.
---

# Worktree Hooks

A new worktree contains only tracked files. Everything gitignored — env files,
credentials, virtualenvs, datasets, build caches, agent config — is missing, so
the worktree is unusable until a setup script fills the gaps. No host copies any
of it for you.

Your job: explore this repo, decide what each missing thing needs, and emit a
script the host runs on worktree creation.

## 1. Ask which host

Use the host the user named. If they did not name one, ask — do not guess, and
do not try to detect it.

| Host | Root var | Worktree var | Teardown hook | Where the script lives |
|---|---|---|---|---|
| Orca | `$ORCA_ROOT_PATH` | `$ORCA_WORKTREE_PATH` | yes, Archive | pasted into Settings → Worktree Hooks |
| T3 Code | `$T3CODE_PROJECT_ROOT` | `$T3CODE_WORKTREE_PATH` | **none** | an Action, or `t3.json` at the repo root |
| anything else | ask | ask | ask | ask |

Orca also sets `$ORCA_WORKSPACE_NAME`; T3 Code has no equivalent.

For any host not in the table, ask the user to describe it and take them at
their word — pasting that host's docs is the fastest form of the answer:

- the variables for the main checkout and for the new worktree, plus a
  worktree/workspace name if it has one
- whether it runs anything on teardown/archive, or only on create
- how the script is installed: pasted into a settings pane, or a file in the repo

If they do not know the variable names, [references/hosts.md](references/hosts.md)
has a way to dump them from a throwaway worktree. That file also covers how Orca
and T3 Code install the script and what each does *not* do for you — read the
section for your host before delivering.

One script then runs on any of them, because the header in step 5 normalizes the
variables; a new host is one more name in that chain.

## 2. Investigate

Read the repo before deciding anything. Run these together:

```bash
git status --ignored --porcelain | grep '^!!' | head -50
ls -A "$(git rev-parse --show-toplevel)"
```

`status --ignored` is the source of truth — `.gitignore` lists patterns that may
match nothing, and misses untracked files that were never ignored. Work from
what is actually on disk.

The `head -50` above truncates, and nested ignored paths never show up in a
top-level `ls`, so agent config gets missed constantly. Check for it explicitly:

```bash
git status --ignored --porcelain | grep '^!!' \
  | grep -Ei '\.(claude|agents|codex|cursor|opencode|windsurf|aider)|AGENTS|CLAUDE|GEMINI'
```

Then size every ignored top-level entry, since size drives the copy/link call:

```bash
du -sh <each ignored path> 2>/dev/null | sort -h
```

Then read, in parallel, whichever exist:

- **Manifests + lockfiles** — `pyproject.toml`/`uv.lock`, `package.json`/`bun.lock`,
  `Cargo.toml`, `go.mod`, `Gemfile`, `pixi.toml`
- **`justfile` / `Makefile`** — run `just --list` if present. Look for `setup`,
  `bootstrap`, `install`, `dev`, `migrate` targets and prefer calling them over
  re-deriving their contents. A `just setup` that already exists is the whole script.
- **README / CONTRIBUTING** — the "Getting Started" section names the steps a
  human is expected to run
- **`.env.example` / `.env.template`** — tells you which env files are *required*
  versus incidental
- **`docker-compose.yml`** — services, named volumes, fixed host ports
- **Migration dirs** (`migrations/`, `alembic/`, `prisma/`) — the worktree may need
  its own database

## 3. Classify every gitignored path

Put each one in exactly one bucket.

**Copy** — small, machine-local config the worktree must be able to diverge on:
`.env`, `.env.local`, `.envrc`, `secrets.toml`, local settings overrides. Copy
rather than link so editing it in a worktree does not mutate the main checkout.

This bucket includes **gitignored agent config and skills** — `.claude/skills/`,
`.claude/settings.local.json`, `.claude/agents/`, `.agents/skills/`, `.codex/`,
`.cursor/rules/`, `AGENTS.md`, `CLAUDE.local.md`. An agent is usually the first
thing to run in a new worktree, and it lands there with none of the skills or
permissions it had in the main checkout. Merge each ignored directory into
whatever the worktree already tracks rather than replacing it:

```bash
for p in .claude .agents .codex .cursor; do
  [ -d "$ROOT/$p" ] && rsync -a --ignore-existing "$ROOT/$p/" "$TREE/$p/" || true
done
```

`rsync -a --ignore-existing` keeps files the worktree already tracks and works
identically on Linux and on macOS's openrsync. Prefer it to `cp` — BSD `cp` has
no `-T`, so a `cp -RT` script silently nests directories on macOS.

**Symlink** — large and immutable, and identical across worktrees: datasets,
model weights, fixture corpora, media, downloaded checkpoints, `.cache/`. Never
duplicate gigabytes per worktree.

**Rebuild** — dependency and build directories: `node_modules/`, `.venv/`,
`target/`, `dist/`, `.next/`, `__pycache__/`. Never copy or symlink these. They
bake in absolute paths, platform-specific binaries, and per-tree state; a
symlinked `.venv` or `node_modules` shared between two worktrees corrupts both
the moment their dependencies diverge. Reinstall from the lockfile instead —
`uv sync`, `bun install --frozen-lockfile`, `cargo fetch`. Package manager caches
make this fast; that is what the cache is for.

**Skip** — logs, `.DS_Store`, editor state, coverage output, `*.pyc`, anything
regenerated on demand.

If a path is genuinely ambiguous — a multi-GB directory that could be a
disposable cache or irreplaceable data — **ask the user** rather than guessing.
Guessing wrong here either wastes disk or breaks the worktree.

## 4. Watch for per-worktree collisions

Several worktrees run at once. Flag these to the user; suggest a scheme, do not
silently invent one:

- **Fixed dev-server ports** — two worktrees running `bun dev` on 3000 collide.
  Offer to derive a port from `$NAME`.
- **Shared dev database** — migrations in one worktree corrupt another. Offer a
  per-worktree database name.
- **Docker container/volume names** — `docker compose` reuses project names based
  on directory; usually fine, but named volumes are shared.

Anything in this list that grabs a resource living *outside* the worktree needs a
teardown counterpart. Check the host table first: if the host has no teardown
hook, say so and hand the user a script they run by hand.

## 5. Write the script

Open with this header, which resolves the same two paths on every host:

```bash
#!/usr/bin/env bash
set -euo pipefail

TREE="${ORCA_WORKTREE_PATH:-${T3CODE_WORKTREE_PATH:-$PWD}}"
ROOT="${ORCA_ROOT_PATH:-${T3CODE_PROJECT_ROOT:-$(dirname "$(git -C "$TREE" rev-parse --path-format=absolute --git-common-dir)")}}"
NAME="${ORCA_WORKSPACE_NAME:-$(basename "$TREE")}"
cd "$TREE"
```

`--path-format=absolute` matters: the bare `--git-common-dir` returns a relative
`.git` when run from a main checkout. Drop the `NAME` line unless something uses it.

For a host the user described in step 1, put its variables first in each chain —
`TREE="${THEIR_WORKTREE_VAR:-${ORCA_WORKTREE_PATH:-...}}"`. A host that sets no
variables at all still works: `$PWD` is the worktree, and `git` recovers the main
checkout from it.

The rest of the script must:

- quote every expansion — worktree paths can contain spaces
- be idempotent and safe to re-run: `ln -sfn`, `mkdir -p`, and guard each copy
  with `[ -f "$src" ] && cp ... || true` so a missing optional file does not abort
  the script — without the `|| true` a failed test on a loop's last iteration is
  itself a nonzero exit under `set -e`
- `echo` one line per step, so the hook output is readable when it fails
- do real work only — no commentary the user did not ask for

Full template, including the teardown counterpart:
[references/script-template.md](references/script-template.md).

## 6. Deliver

Verify it parses before handing it over: `bash -n <script>`.

Then follow [references/hosts.md](references/hosts.md) for the target host —
each installs the script differently. Whatever the host, close by telling the
user, in this order:

1. where the script now is and what they must do to install it
2. anything you flagged for them to decide (ports, databases, ambiguous dirs)
3. which resources have no teardown, if the host cannot run one

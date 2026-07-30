---
name: orca-worktree-hooks
description: Generate the Setup and Archive shell scripts for Orca's Worktree Hooks settings for the current repo. Explores the repo to decide which gitignored files to copy, which large data to symlink, and which dependencies to reinstall, then copies the script to the clipboard for pasting into Orca. Use when the user says "orca worktree hooks", "orca setup script", "worktree setup script", or asks how to make new Orca worktrees usable without manual setup.
---

# Orca Worktree Hooks

Orca creates each worktree as a fresh `git worktree` — it contains only tracked
files. Everything gitignored (env files, credentials, virtualenvs, datasets,
build caches) is missing, so the worktree is usually unusable until a setup
script fills the gaps.

Your job: explore this repo, decide what each missing thing needs, and emit two
bash scripts the user pastes into **Orca Settings → Worktree Hooks**.

Orca provides three variables to both scripts:

| Variable | Meaning |
|---|---|
| `$ORCA_ROOT_PATH` | The main repo checkout — the source to copy/link from |
| `$ORCA_WORKTREE_PATH` | The new worktree — the destination |
| `$ORCA_WORKSPACE_NAME` | Worktree name, useful for per-worktree ports/DBs |

Each hook runs as a single shell script. Do not assume a working directory.

## 1. Investigate

Read the repo before deciding anything. Run these together:

```bash
git -C . status --ignored --porcelain | grep '^!!' | head -50
ls -A "$(git rev-parse --show-toplevel)"
```

`status --ignored` is the source of truth — `.gitignore` lists patterns that may
match nothing, and misses untracked files that were never ignored. Work from
what is actually on disk.

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

## 2. Classify every gitignored path

Put each one in exactly one bucket.

**Copy** — small, machine-local config the worktree must be able to diverge on:
`.env`, `.env.local`, `.envrc`, `secrets.toml`, local settings overrides. Copy
rather than link so editing it in a worktree does not mutate the main checkout.

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

## 3. Watch for per-worktree collisions

Several worktrees run at once. Flag these to the user; suggest a scheme, do not
silently invent one:

- **Fixed dev-server ports** — two worktrees running `bun dev` on 3000 collide.
  Offer to derive a port from `$ORCA_WORKSPACE_NAME`.
- **Shared dev database** — migrations in one worktree corrupt another. Offer a
  per-worktree database name.
- **Docker container/volume names** — `docker compose` reuses project names based
  on directory; usually fine, but named volumes are shared.

## 4. Write the scripts

Both scripts must:

- start with `#!/usr/bin/env bash` and `set -euo pipefail`
- `cd "$ORCA_WORKTREE_PATH"` first — never rely on the inherited cwd
- quote every `"$ORCA_*"` expansion (paths can contain spaces)
- be idempotent and safe to re-run: `ln -sfn`, `mkdir -p`, and guard each copy
  with `[ -f "$src" ] &&` so a missing optional file does not abort the hook
- `echo` one line per step, so Orca's hook output is readable when it fails
- do real work only — no commentary the user did not ask for

The **archive** script must never touch `$ORCA_ROOT_PATH`, and must tolerate
things that were never created. Its job is releasing shared resources the
worktree grabbed: stop dev servers, `docker compose down` per-worktree services,
drop the per-worktree database, remove named volumes. Deleting files inside the
worktree is usually pointless — Orca removes the directory anyway — so only do it
for things stored elsewhere.

Shape:

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$ORCA_WORKTREE_PATH"

echo "==> Copying local config"
for f in .env .env.local; do
  [ -f "$ORCA_ROOT_PATH/$f" ] && cp "$ORCA_ROOT_PATH/$f" "$ORCA_WORKTREE_PATH/$f"
done

echo "==> Linking shared data"
ln -sfn "$ORCA_ROOT_PATH/data" "$ORCA_WORKTREE_PATH/data"

echo "==> Installing dependencies"
uv sync

echo "==> Worktree ready"
```

## 5. Deliver

Print both scripts in fenced `bash` blocks, then copy the **setup** script to the
clipboard — that is the one being pasted first:

```bash
cat > /tmp/orca-setup.sh <<'ORCA_EOF'
...script...
ORCA_EOF
command -v pbcopy >/dev/null && pbcopy < /tmp/orca-setup.sh \
  || command -v wl-copy >/dev/null && wl-copy < /tmp/orca-setup.sh \
  || xclip -selection clipboard < /tmp/orca-setup.sh
```

Then tell the user, in this order:

1. Setup script is on the clipboard → paste into **Settings → Worktree Hooks →
   Setup Script**
2. Anything you flagged for them to decide (ports, databases, ambiguous dirs)
3. That they can ask for the archive script to be copied next

Verify the script parses before handing it over: `bash -n /tmp/orca-setup.sh`.

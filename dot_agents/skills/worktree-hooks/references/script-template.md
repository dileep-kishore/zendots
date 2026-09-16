# Script template

A worked setup script. Keep the header verbatim; replace the steps below it with
whatever step 3 of the skill classified for this repo, in this order — config
first, then links, then the slow install last, so a host that does not wait for
completion still gives an agent its config and data early.

```bash
#!/usr/bin/env bash
set -euo pipefail

TREE="${ORCA_WORKTREE_PATH:-${T3CODE_WORKTREE_PATH:-$PWD}}"
ROOT="${ORCA_ROOT_PATH:-${T3CODE_PROJECT_ROOT:-$(dirname "$(git -C "$TREE" rev-parse --path-format=absolute --git-common-dir)")}}"
cd "$TREE"

echo "==> Copying local config"
for f in .env .env.local; do
  [ -f "$ROOT/$f" ] && cp "$ROOT/$f" "$TREE/$f" || true
done

echo "==> Copying agent config"
for p in .claude .agents; do
  [ -d "$ROOT/$p" ] && rsync -a --ignore-existing "$ROOT/$p/" "$TREE/$p/" || true
done

echo "==> Linking shared data"
ln -sfn "$ROOT/data" "$TREE/data"

echo "==> Installing dependencies"
uv sync

echo "==> Worktree ready"
```

Add `NAME="${ORCA_WORKSPACE_NAME:-$(basename "$TREE")}"` to the header only when
something derives a port, database name, or container name from it.

## Teardown

Same header. A teardown script must never touch `$ROOT`, and must tolerate
things that were never created — it runs after failed setups too. Its job is
releasing shared resources the worktree grabbed:

```bash
echo "==> Stopping services"
docker compose -p "$NAME" down --volumes --remove-orphans 2>/dev/null || true

echo "==> Dropping worktree database"
dropdb --if-exists "app_$NAME" 2>/dev/null || true
```

Deleting files inside the worktree is usually pointless — the host removes the
directory anyway — so only do it for things stored elsewhere.

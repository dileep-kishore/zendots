# Host specifics

How each host installs the script, and what it does *not* do for you.

## Orca

Variables: `$ORCA_ROOT_PATH`, `$ORCA_WORKTREE_PATH`, `$ORCA_WORKSPACE_NAME`.

Two hooks, both whole shell scripts pasted into **Settings → Worktree Hooks**:
Setup Script and Archive Script. Neither assumes a working directory.

Print both scripts in fenced `bash` blocks, then put the setup script on the
clipboard — that is the one pasted first:

```bash
cat > /tmp/worktree-setup.sh <<'HOOK_EOF'
...script...
HOOK_EOF
bash -n /tmp/worktree-setup.sh
if command -v pbcopy >/dev/null; then pbcopy < /tmp/worktree-setup.sh
elif command -v wl-copy >/dev/null; then wl-copy < /tmp/worktree-setup.sh
elif command -v xclip >/dev/null; then xclip -selection clipboard < /tmp/worktree-setup.sh
else echo "no clipboard tool found" >&2; false
fi
```

If the copy succeeded, tell the user it is on the clipboard and offer to copy
the archive script next; otherwise point them to `/tmp/worktree-setup.sh`.

## T3 Code

Variables: `$T3CODE_PROJECT_ROOT` (main checkout), `$T3CODE_WORKTREE_PATH` (set
only for worktree threads). There is no workspace-name variable — derive one
from `basename "$TREE"`. The command runs in a terminal whose cwd is
`worktreePath ?? project.cwd`, which makes a multi-line script a bad fit: put
the script in a file and point the action at it.

Setup is an **Action** with *Run automatically on worktree creation* on. Only
the first action carrying the flag runs; a second is ignored with no warning.

### t3.json is an import catalog, not configuration

A repo-root `t3.json` does **not** register anything by itself. Its `scripts`
are offered for import in the Actions settings and the scripts menu under a
"From t3.json" group, filtered against actions the project already has. The
setup runner resolves its script only from registered project scripts
(`resolveProjectScripts` → `projectSettingsOverrides` → `projectScriptOverrides`
→ the project aggregate → environment defaults) and never reads `t3.json`. So
always tell the user to import it once per machine — writing the file is not
enough, and an unimported `t3.json` silently runs nothing.

The one key that *does* apply automatically is `defaultThreadEnvMode`, honoured
as a repository default when the project has no override.

### Default delivery: keep it out of git, ask before committing

A worktree contains only committed files, so where the script lives decides the
command:

- **Personal hook (default).** The user's own setup, carried between machines by
  a sync tool rather than git. Add `/t3.json` and `/scripts/worktree-setup.sh`
  to `.gitignore`, and reference the script through the main checkout, which
  always has it:
  `bash "$T3CODE_PROJECT_ROOT/scripts/worktree-setup.sh"`.
  `t3.json` is only ever read from the workspace root, so gitignoring it still
  leaves the one-click import working on every machine.
- **Team hook.** Commit both and use the plain relative
  `bash scripts/worktree-setup.sh`.

Ask which one before writing, and default to personal. A gitignored script with
a relative command is the failure this pairing exists to prevent: the action
resolves to nothing in a fresh worktree.

**Ask before committing anything.** The `.gitignore` edit is a repo change, and
a hook that needs repo support — an env-driven port, a `just` target — means
more. Name those files and ask; never commit on your own initiative.

```json
{
  "$schema": "https://t3.codes/schema/t3.json",
  "scripts": [
    {
      "name": "Setup",
      "command": "bash \"$T3CODE_PROJECT_ROOT/scripts/worktree-setup.sh\"",
      "runOnWorktreeCreate": true,
      "async": false
    }
  ]
}
```

### Derived values need somewhere to land

A port or database name the script derives is inert unless something reads it.
Check that the project's run commands actually consult the variable the script
writes, and offer the (committable) change when they do not.

### What T3 Code does not do

- **No teardown hook.** Archiving a thread offers to remove the worktree and
  runs nothing first. Anything the setup grabs outside the worktree — ports,
  databases, containers, named volumes — is released by hand. Prefer a design
  with nothing to release: state kept *inside* the worktree dies with it.
  Otherwise write `scripts/worktree-teardown.sh` and say plainly that they must
  run it themselves before archiving.
- **No gitignored-file carryover.** No `.env` copy, no `.worktreeinclude`
  support. Every file in the copy bucket is the script's job.
- **Starts the agent mid-setup, unless you say otherwise.** Setup scripts are
  async by default: the agent begins while `uv sync` is still running. Set
  `"async": false` in `t3.json` (or "Wait for it to finish before the agent
  starts" in the action editor) to hold the agent until the script exits.
  Prefer that for any setup with a slow install.

Verified against the T3 Code nightly and the `pingdotgg/t3code` sources in
September 2026 (`T3ProjectFileLoader.ts`, `useT3ProjectFileScripts.ts`,
`shared/projectScripts.ts`). A teardown hook was an open upstream request then,
so re-check before assuming it is still absent.

## Any other host

Use whatever the user told you about the host. When they do not know the
variable names, hand them this: put it in the host's setup hook once, create a
throwaway worktree, and read the result.

```bash
env | sort > /tmp/hook-env.txt; pwd >> /tmp/hook-env.txt
```

Then grep it for `worktree`, `workspace`, `root`, `project`. Also check the repo
root for a host config file (`conductor.json`, `t3.json`, and similar) that may
declare the hooks instead of an app settings pane.

If the host exposes nothing, the header in step 5 still works: `$PWD` is the
worktree for every host that runs the hook inside it, and the main checkout is
recovered from git. Confirm both by having the script `echo "$ROOT" "$TREE"` on
its first run.

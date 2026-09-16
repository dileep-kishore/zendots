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
command -v pbcopy >/dev/null && pbcopy < /tmp/worktree-setup.sh \
  || command -v wl-copy >/dev/null && wl-copy < /tmp/worktree-setup.sh \
  || xclip -selection clipboard < /tmp/worktree-setup.sh
```

Tell the user it is on the clipboard, then offer to copy the archive script next.

## T3 Code

Variables: `$T3CODE_PROJECT_ROOT` (main checkout), `$T3CODE_WORKTREE_PATH`.
There is no workspace-name variable — derive one from `basename "$TREE"`.

Setup is an **Action** with *Run automatically on worktree creation* toggled on.
Only the first action carrying that flag runs, so a project gets exactly one
setup script. The command is typed into a terminal whose cwd is the worktree,
which makes a multi-line script a bad fit. Check the script into the repo and
point the action at it.

Preferred delivery — write `scripts/worktree-setup.sh`, then a repo-root
`t3.json` so teammates get the same action:

```json
{
  "$schema": "https://t3.codes/schema/t3.json",
  "scripts": [
    {
      "name": "Setup",
      "command": "bash scripts/worktree-setup.sh",
      "runOnWorktreeCreate": true
    }
  ]
}
```

`t3.json` also takes `defaultThreadEnvMode: "worktree"`, which is worth setting
if the project should always start threads in a worktree. If the command must
not be checked in, have the user paste it into the project's Actions instead.

Three things T3 Code does not do, all of which land on the script:

- **No teardown hook.** Archiving a thread offers to remove the worktree and
  runs nothing first. Anything the setup grabs outside the worktree — ports,
  databases, containers, named volumes — is released by hand. Still write
  `scripts/worktree-teardown.sh` when there is something to release, and tell
  the user plainly that they have to run it themselves before archiving.
- **No gitignored-file carryover.** No `.env` copy, no `.worktreeinclude`
  support. Every file in the copy bucket is the script's job.
- **No wait for completion.** T3 writes the command to the terminal and starts
  the first agent turn immediately, so a long `uv sync` is still running while
  the agent reads files. Keep setup short, do the copy/link steps before the
  slow install so the agent at least has config and data, and warn the user that
  an agent may report a missing dependency that is merely still installing.

Verified against the T3 Code nightly build in September 2026; a teardown hook
was an open upstream request at that time, so re-check before assuming it is
still absent.

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

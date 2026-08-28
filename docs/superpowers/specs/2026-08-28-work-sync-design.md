# Work sync design

## Goal

Replace the one-off Syncthing bootstrap script with one small `work-sync` CLI
that safely manages project-folder setup and explicit Git handoffs between
`macmini` and `tsuki`.

Syncthing continues to move ordinary project files. Git metadata stays local to
each machine. `work-sync handoff` transfers commits, branch state, staging state,
and external Orca worktrees only when the user chooses a handoff target.

The frozen backup at `/Volumes/SSK SSD/Backup-2026-08-20` is not part of this
workflow and must not be changed.

## Commands

The installed command is `work-sync`. Running it without arguments shows help.

```text
work-sync bootstrap FOLDER [--apply]
work-sync handoff TARGET [--folder FOLDER ...] [--dry-run] [--yes]
```

Examples shown in `--help`:

```bash
# Validate one folder without changing Syncthing.
work-sync bootstrap QBio_perspective

# Add or validate it on both machines.
work-sync bootstrap QBio_perspective --apply

# Hand every manifest Git repository to tsuki.
work-sync handoff tsuki

# Hand selected repositories to macmini.
work-sync handoff macmini --folder LifeOS --folder CommScores

# Show the complete handoff without changing either machine.
work-sync handoff tsuki --dry-run
```

`TARGET` always means the receiving machine. The CLI detects the current host
and rejects a handoff to itself. Mutating commands show a Rich summary and ask
for confirmation unless `--yes` is present. The same CLI runs on either host
through the existing `tsuki` and `macmini` SSH aliases. Typer's standard shell
completion options remain available.

## Files and packaging

Use one uv-managed Python package under `tools/work-sync`. Typer provides the
command interface and Rich provides tables, progress, warnings, and summaries.
The Python standard library handles JSON, subprocesses, paths, hashing, and
locking. No other runtime dependencies are needed.

Keep the implementation split by responsibility:

- `cli` owns Typer commands, confirmation, and presentation.
- `manifest` loads and validates folder definitions and host paths.
- `syncthing` owns configuration backup, folder setup, ignore rules, and idle
  checks.
- `handoff` owns Git state transfer, external worktree transfer, recovery, and
  final verification.
- one small process helper runs commands locally or over the existing SSH host
  aliases.

The chezmoi-managed executable at `~/.local/bin/work-sync` is a thin launcher
for the uv project. The old `work-sync-bootstrap` executable is removed after
the replacement passes its tests.

The obsolete, untracked `bin/backup-to-ssk.sh` script is deleted. This removes
only the script from Zendots. It does not touch the SSK SSD or its backup.

## Private manifest

The existing manifest source remains at:

```text
~/zendots/private_dot_config/work-sync/folders.json
```

Syncthing carries this file as part of the Zendots folder. An exact entry in
Zendots `.gitignore` keeps the private folder list out of Git. Nothing adds it
to `.stignore`, because that would stop the cross-machine sync the file exists
for.

Chezmoi applies the source copy to:

```text
~/.config/work-sync/folders.json
```

The installed CLI reads the XDG path. Before a mutating command, it verifies
that the local source copy, local applied copy, remote source copy, and remote
applied copy are byte-identical. If one is stale, the command stops and prints
the exact scoped `chezmoi apply ~/.config/work-sync/folders.json` command for
the affected machine.

Each manifest entry retains its stable Syncthing ID, label, Mac path, tsuki
path, folder class, Git policy, and ignore patterns. Selectors may match a
folder ID or label, but must resolve to exactly one entry.

## Bootstrap behavior

`work-sync bootstrap FOLDER` keeps the safety behavior of the current helper:

1. Validate the manifest and both directory paths.
2. Confirm the paths do not overlap another Syncthing folder.
3. For Git repositories, confirm both main checkouts have the same repository
   identity and compatible Git state.
4. Validate a tracked `.stignore` without editing it. For an untracked
   `.stignore`, append only missing managed rules and add `.stignore` to that
   checkout's `.git/info/exclude`.
5. Back up both Syncthing configurations before applying changes.
6. Add or validate the folder on both machines with ownership and extended
   attribute synchronization disabled.
7. Unpause the folder and wait for both machines to return to `Up to Date`.

Without `--apply`, the command performs the complete validation and prints the
planned changes. It does not write configuration or project files.

The shared ignore rules cover disposable caches and machine-local runtime
state. Project files such as `.env`, `.claude/settings.json`,
`.codex/config.toml`, and `.pi/settings.json` continue to sync unless that
project's manifest entry explicitly ignores them. The CLI never edits a
project's `.gitignore`.

## Handoff model

Syncthing deliberately ignores `.git`. A handoff therefore has three channels:

```text
main checkout files       Syncthing
Git objects and refs      Git over SSH
external Orca worktrees   rsync over SSH
```

The command never copies `.git`, linked-worktree administrative directories,
Git lock files, or machine-local Git configuration.

By default, `handoff` selects every manifest entry whose class is `git`.
Repeatable `--folder` options narrow the selection. Plain and container folders
remain Syncthing-only and are not part of a Git handoff.

### Global preflight

All selected repositories pass preflight before the first mutation:

- the four manifest copies match;
- passwordless SSH works in both directions;
- Syncthing reports the selected main folders as idle and up to date;
- source and target repository identities match;
- no selected repository has an unresolved merge, rebase, bisect, lock file,
  or unmerged index entry;
- no selected checkout has a detached `HEAD`;
- no affected Orca worktree has a running agent terminal;
- target branches do not diverge from their source counterparts;
- target files contain no change that is absent from the source;
- target-only branches are recorded and left alone.

A process lock in `~/.local/state/work-sync` prevents two handoffs from running
at once on the initiating machine. A failed preflight changes nothing.

### Git state transfer

For each selected repository:

1. Fetch source objects into a temporary namespace on the target through the
   existing SSH connection.
2. Create missing source branches on the target or fast-forward existing ones.
   Never force-update a divergent branch and never delete a target-only branch.
3. For each paired checkout, set the target branch to the source commit.
4. Rebuild the target index from the source `HEAD` plus a binary staged patch.
   This reproduces staged changes without copying the source index file.
5. Let Syncthing provide the main-checkout working files. Copy external
   worktree files with rsync after excluding `.git`, caches, owners, groups,
   and extended attributes.
6. Preserve executable status. Include untracked project files and ignored
   project files unless the manifest excludes them.

Tags and remote configuration are outside the first version. Each machine
keeps its own remotes, hooks, credentials, and Git settings.

### Orca worktrees

Pair linked worktrees by canonical repository identity and branch, never by
their absolute paths. Canonical identity is the normalized `host/owner/repo`
portion of the `origin` fetch URL. If the source and target origins differ, the
handoff stops. This makes the BERIL upstream repository distinct from a fork.

If the target already has the branch in an Orca worktree, keep its local path
and Orca ID. If it is missing, create it through `orca worktree create` with
setup hooks skipped, then copy the source worktree files into the new target
path. This preserves Orca's own registration and Git administrative layout.
The same handling applies to Orca-managed worktrees stored under the existing
`orca` and `superset` roots.

The handoff verifies the final repository and worktree lists with the Orca CLI
on both machines. Repositories outside the private manifest, including
DataLake and TraitWeaver, remain untouched.

## Deletions and recovery

The rsync phase may mirror source deletions only after the target-cleanliness
check passes. Before replacing or deleting any target-only file, copy it under:

```text
~/.local/state/work-sync/handoff/<timestamp>/
```

The final report prints that path. A mid-run failure stops the handoff and
reports which repositories completed, which one failed, and where the recovery
copy lives. The first version does not attempt an automatic multi-repository
rollback.

## Disposable verification

Real projects are not the first test. Verification has three layers.

### Local checks

Run Ruff, ty, and a small pytest suite through uv. Tests cover manifest
validation, folder selection, host detection, refusal cases, command previews,
and Git-state reconstruction.

### Temporary two-checkout integration test

Create source and target repositories under Python temporary directories. Test
committed, staged, unstaged, untracked, deleted, and executable files. Verify
that a dirty or divergent target causes a zero-mutation refusal and that `.git`
is never transferred.

### Temporary cross-machine round trip

Create unique roots with `mktemp -d` under `/private/tmp` on macmini and `/tmp`
on tsuki. Add only those roots as a temporary Syncthing folder and temporary
Orca repository/worktree registrations. Run:

1. macmini to tsuki dry-run;
2. macmini to tsuki handoff;
3. content, mode, Git status, branch, index, and Orca checks;
4. a changed tsuki to macmini handoff;
5. the same checks in reverse;
6. existing-target and missing-target worktree cases;
7. dirty-target and divergent-branch refusal cases.

After a successful run, remove the test folder from Syncthing, remove only the
temporary Orca registrations and worktrees, delete the validated temporary
roots, and verify that no test entry or process remains. If the test fails,
retain the temporary roots and print their exact paths and cleanup commands so
the failure can be inspected.

After all temporary tests pass, run a dry-run against every real manifest Git
repository. Stop and show the report before the first real handoff.

## Completion criteria

The change is ready for real use when:

- `work-sync --help` and both command help pages include the approved examples;
- both machines use the same private manifest;
- bootstrap dry-run and apply behavior pass against temporary folders;
- the cross-machine handoff round trip passes and cleans up after itself;
- real-project dry-run reports no unsafe target state;
- `.git`, ownership, groups, extended attributes, and non-executable mode bits
  never cross through Syncthing or rsync. The executable bit is preserved;
- the old bootstrap and backup scripts are gone, while the frozen SSK backup is
  unchanged.

## Out of scope

- syncing `.git` through Syncthing;
- deleting target-only branches or force-updating divergent branches;
- automatically resolving simultaneous edits on both machines;
- syncing Git remotes, hooks, credentials, or tags;
- changing project `.gitignore` files;
- modifying DataLake, TraitWeaver, or other repositories absent from the
  manifest;
- running a real project handoff without a reviewed dry-run.

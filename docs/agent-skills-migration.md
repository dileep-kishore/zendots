# Agent skills cleanup on the Mac (one-time)

The Mac is in a specific half-migrated state, not a fresh one:

- **Its `~/zendots` source is already post-cleanup**, because Syncthing
  replicates the repo. `dot_agents/skills/` holds the 11-skill store, the two
  `private_dot_local/bin` scripts are there, and the old per-skill `symlink_`
  entries are gone.
- **Its home directory is still pre-cleanup**, because the migration commits
  only deleted things from the chezmoi *source*. chezmoi never removes a target
  when its source entry disappears, so everything the old layout applied is
  still sitting in the Mac's home as an orphan.

So this is not "set up the new layout" — it is "delete what the old layout left
behind". Run once, then delete nothing else; `CLAUDE.md` → *Agent Skills* covers
everything after.

Reference commits: `6dab4a8` is the last pre-cleanup state, `1ea4eda` is the
migration.

## End state

- `~/.agents/skills/` is the only place a skill's files exist, and matches
  `dot_agents/skills/` exactly.
- `~/.claude/skills/<name>` is a symlink into that store for every skill in it.
- `~/.codex/skills/` and `~/.config/opencode/skills/` contain **nothing** from
  the store. Codex and OpenCode resolve `~/.agents/skills` themselves; an entry
  there makes them load the skill twice.
- `~/.local/bin/agent-skills.sh` and `~/.local/bin/link-agent-skills.sh` exist
  and are executable.

## 1. Check the sync landed before touching anything

A half-synced source will apply garbage.

```bash
cd ~/zendots
git log --oneline -1                      # expect 5f5514e or later
ls private_dot_local/bin/executable_agent-skills.sh
ls dot_agents/skills                      # expect 11 entries, incl. orca-worktree-hooks
find . -name '*.sync-conflict*'           # expect nothing
```

If conflict files exist, clear them with `rm-sync-conflict.sh` and let Syncthing
settle first.

## 2. Apply

```bash
chezmoi diff ~/.agents ~/.local/bin ~/.claude/skills
chezmoi apply ~/.agents ~/.local/bin ~/.claude/skills
```

Never a bare `chezmoi apply`; it sweeps in unrelated pending changes.

This writes the store and both scripts, and `run_after_40_link-agent-skills.sh`
creates the Claude symlinks. If the scoped apply skipped the script, run
`~/.local/bin/link-agent-skills.sh` directly.

## 3. Delete the orphans the old layout left

These are the exact source entries the migration deleted, and the target each
one left behind. The Mac only has a given orphan if it applied `6dab4a8`, so
every command below is conditional — safe to run either way.

| orphaned target | why it must go |
|---|---|
| `~/.codex/skills/orca-worktree-hooks` | Codex reads the store natively; this makes it load the skill twice |
| `~/.config/opencode/skills/orca-worktree-hooks` | same, for OpenCode |
| `~/.claude/skills/find-docs` | real directory shadowing the store copy of the ctx7 skill |
| `~/.agents/skills/prd-to-plan` | renamed upstream to `to-spec`; still in the store, so it would get linked into Claude |
| `~/.agents/skills/write-a-prd` | renamed upstream to `wayfinder`; same |
| `~/.agents/symlink_skills/` | empty directory; chezmoi does not honour `symlink_` on directories |

`~/.claude/skills/orca-worktree-hooks` is **not** an orphan to delete — it points
into the store and is exactly what `link-agent-skills.sh` would create. Leave it.

```bash
# double-loading entries in the two harnesses that read the store natively
rm -f ~/.codex/skills/orca-worktree-hooks
rm -f ~/.config/opencode/skills/orca-worktree-hooks

# real directory shadowing the store; confirm it is redundant first
if [ -d ~/.claude/skills/find-docs ] && [ ! -L ~/.claude/skills/find-docs ]; then
  diff -r ~/.claude/skills/find-docs ~/.agents/skills/find-docs \
    && rm -rf ~/.claude/skills/find-docs \
    || echo "DIFFERENT - reconcile by hand, keep the store copy"
fi

# skills renamed upstream, otherwise they get linked into Claude forever
rm -rf ~/.agents/skills/prd-to-plan ~/.agents/skills/write-a-prd

# empty cruft directory
rmdir ~/.agents/symlink_skills 2>/dev/null || true

# recreate find-docs as a symlink and prune links left dangling by the above
~/.local/bin/link-agent-skills.sh
```

The last command also cleans up any `~/.claude/skills/prd-to-plan` or
`write-a-prd` symlink, since those now fail to resolve.

## 4. Reconcile skills the Mac has and the repo does not

The store is synced, so the Mac now holds this machine's 11 skills. Anything
extra it had locally is untracked and will not survive the next machine:

```bash
diff <(ls ~/.agents/skills) <(ls ~/zendots/dot_agents/skills)
```

Expect no output. If `<` lines appear, those are Mac-only skills — decide each:

- **Keep** → `agent-skills.sh update` first (so you record current versions, not
  stale ones), then:
  ```bash
  chezmoi add ~/.agents/skills ~/.agents/.skill-lock.json
  cd ~/zendots && git add -A && git commit -m "feat(skills): add <name> from macOS"
  ```
- **Drop** → `agent-skills.sh remove <name>`

## 5. Refresh the diverged `frontend-design` copy

`~/.agentskills/` is unmanaged, so this must be redone per machine. Its
`frontend-design` is an older version of the one the
`frontend-design@claude-plugins-official` plugin ships, and Claude loads both.

```bash
P=~/.claude/plugins/cache/claude-plugins-official/frontend-design/unknown/skills/frontend-design
[ -f "$P/SKILL.md" ] && { diff -q "$P/SKILL.md" ~/.agentskills/frontend-design/SKILL.md \
  || cp "$P/SKILL.md" ~/.agentskills/frontend-design/SKILL.md; }
```

Adjust the path if that plugin is not enabled on the Mac.

Do **not** fold `~/.agentskills/` or `~/.config/opencode/superpowers/skills` into
`~/.agents/skills`. Those two stores give OpenCode what Claude gets from
plugins; merging them would duplicate about fifteen skills into Claude, because
the store is visible to Claude through the symlinks.

## 6. Verify

```bash
# fully synced -- expect no output
chezmoi status ~/.agents ~/.local/bin ~/.claude/skills

# store matches the repo exactly
diff <(ls ~/.agents/skills) <(ls ~/zendots/dot_agents/skills) && echo "parity ok"

# every skill linked into Claude
for s in ~/.agents/skills/*/; do n=$(basename "${s%/}")
  [ -L ~/.claude/skills/"$n" ] || echo "MISSING LINK: $n"
done; echo "link check done"

# nothing double-loaded in the natively-reading harnesses
for d in ~/.codex/skills ~/.config/opencode/skills; do
  for e in "$d"/*/; do n=$(basename "${e%/}")
    [ -e ~/.agents/skills/"$n" ] && echo "DOUBLE-LOAD: $n in $d"
  done
done 2>/dev/null; echo "double-load check done"

# nothing dangling
find ~/.claude/skills ~/.config/opencode/skills ~/.agents/skills \
  -maxdepth 1 -type l ! -exec test -e {} \; -print

# scripts landed
ls -l ~/.local/bin/agent-skills.sh ~/.local/bin/link-agent-skills.sh
```

Then start Claude Code and confirm a store-only skill such as
`orca-worktree-hooks` appears in its skill list.

If step 3 or 4 changed anything under `dot_agents/`, commit it so this machine
and the Mac agree.

## Notes

- Both scripts are macOS-safe: plain `readlink`, `ln -sfn`, and the bash `-ef`
  test behave the same on BSD userland, and no GNU-only flags are used. The
  snippets above avoid `stat -c`, which is GNU-only — use `stat -f` on macOS.
- Paths differ only in `$HOME` (`/Users/<you>`). `~/.config/opencode` is correct
  on macOS too; OpenCode uses XDG on both platforms.
- `find -xtype l` is GNU-only, which is why the dangling-link check above uses
  `-type l ! -exec test -e {} \;` instead.
- **Install a given skill on one machine only.** Both machines write to the same
  Syncthing-replicated source, so installing the same skill on each produces
  competing writes to `dot_agents/skills/` and `dot_agents/dot_skill-lock.json`
  that surface as `*.sync-conflict*` files.

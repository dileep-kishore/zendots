# Agent skills migration (one-time, per machine)

One-time cleanup for a machine whose home directory predates commit `1ea4eda`.
The repo half of the migration is already done and arrives via `chezmoi update`;
what remains is local state that chezmoi cannot fix on its own, because it never
managed it.

Run this once on the Mac. After that, `CLAUDE.md` → *Agent Skills* is the whole
story and this file is history.

## End state

- `~/.agents/skills/` is the only place a skill's files exist. It is vendored in
  the repo as `dot_agents/skills/`, so `chezmoi apply` restores every skill with
  no network and no node.
- `~/.claude/skills/<name>` is a **symlink** into that store for every skill in
  it. Claude Code is the only harness that needs links.
- `~/.codex/skills/` and `~/.config/opencode/skills/` contain **nothing** from
  the store. Codex and OpenCode resolve `~/.agents/skills` themselves; a link
  there makes them load the skill twice.
- `~/.local/bin/agent-skills.sh` and `~/.local/bin/link-agent-skills.sh` exist
  and are executable.
- No skill name appears as real content in two stores at once.

## Background: why it was broken

`npx skills` and chezmoi were both claiming the same packages. `npx skills` had
updated some of them in place, while chezmoi still held older copies in its
source, so the next `chezmoi apply` would have silently reverted them. Other
skills the installer had added were tracked nowhere and would not survive a move
to a new machine.

The fix was to split ownership: `npx skills` installs, `chezmoi` records, and
neither writes where the other reads.

Two facts worth not re-deriving:

- **Codex and OpenCode read `~/.agents/skills` natively.** `npx skills add`
  prints them under `universal:` and writes no link for them; only Claude Code
  appears under `symlinked:`. Both binaries contain the literal string
  `.agents/skills`. This is why the fanout script targets Claude alone.
- **The store is visible to Claude through those symlinks**, so a skill that an
  enabled Claude plugin already ships will appear twice in one session if you
  also put it in the store.

## Steps

### 0. Apply

`~/zendots` reaches this machine over Syncthing, not `git pull`, so the source
tree — including `dot_agents/skills/` and the two `private_dot_local/bin`
scripts — is likely already present. Confirm before doing anything else:

```bash
cd ~/zendots
ls docs/agent-skills-migration.md private_dot_local/bin/executable_agent-skills.sh
git log --oneline -1        # should be at or past the skills commit
find . -name '*.sync-conflict*' | head   # resolve these first
```

If Syncthing left conflict files, clear them with `rm-sync-conflict.sh` before
applying — a half-synced source will apply garbage.

```bash
chezmoi diff ~/.agents ~/.local/bin ~/.claude/skills   # review first
chezmoi apply ~/.agents ~/.local/bin ~/.claude/skills
```

Do not run a bare `chezmoi apply`; it sweeps in unrelated pending changes.

`run_after_40_link-agent-skills.sh` fires during apply and creates the Claude
symlinks. If you scoped the apply and it did not run, run it directly:

```bash
~/.local/bin/link-agent-skills.sh
```

### 1. Record skills the Mac has but the repo does not

The Mac may have skills installed locally that were never committed. Find them:

```bash
diff <(ls ~/.agents/skills) <(ls ~/zendots/dot_agents/skills)
```

Lines starting `<` exist only on the Mac. Decide per skill:

- **Keep it** → record and commit:
  ```bash
  chezmoi add ~/.agents/skills ~/.agents/.skill-lock.json
  cd ~/zendots && git add -A && git commit -m "feat(skills): add <name> from macOS"
  ```
- **Drop it** → `agent-skills.sh remove <name>`

Lines starting `>` exist only in the repo and will appear after step 0.

Beware of recording a *stale* skill: `chezmoi add` snapshots whatever is on
disk, so if the Mac is behind on `npx skills update`, run
`agent-skills.sh update` first.

### 2. Remove real directories that shadow the store

Anything in `~/.claude/skills/` that is a real directory **and** has the same
name as a skill in the store is a leftover duplicate. `link-agent-skills.sh`
refuses to overwrite these and prints a warning naming each one:

```
link-agent-skills: /Users/<you>/.claude/skills/find-docs is not a symlink, leaving it alone
```

For each one, confirm it is genuinely redundant before deleting:

```bash
diff -r ~/.claude/skills/<name> ~/.agents/skills/<name>   # expect no output
rm -rf ~/.claude/skills/<name>
~/.local/bin/link-agent-skills.sh                          # symlink takes over
```

On this machine that was `find-docs` (the ctx7 skill) — byte-identical, safe.
If `diff` shows differences, stop and reconcile by hand; the store copy is the
one that must survive, since it is what the repo carries.

### 3. Remove links that cause double-loading

Any entry in `~/.codex/skills/` or `~/.config/opencode/skills/` whose name also
exists in the store makes that harness load the skill twice:

```bash
cd ~ && for d in .codex/skills .config/opencode/skills; do
  for e in "$d"/*/; do n=$(basename "${e%/}")
    [ -e ".agents/skills/$n" ] && echo "DOUBLE-LOAD: $n in $d"
  done
done 2>/dev/null; echo "(no lines above = clean)"
```

Delete anything it reports. Leave entries that are *not* in the store alone —
those are that harness's own skills, not duplicates.

### 4. Audit for Claude plugin overlap

A skill in the store that an enabled plugin also ships shows up twice in a
Claude session. Check:

```bash
cd ~/.claude/plugins && python3 - <<'PY'
import json, os, glob
ip = json.load(open('installed_plugins.json'))['plugins']
prov = {}
for key, insts in ip.items():
    for i in insts:
        p = i.get('installPath', '')
        if p and os.path.isdir(p):
            for f in glob.glob(p + '/**/SKILL.md', recursive=True):
                prov.setdefault(os.path.basename(os.path.dirname(f)), set()).add(key)
h = os.path.expanduser('~')
def names(d): return set(os.listdir(d)) if os.path.isdir(d) else set()
for store in ('/.agents/skills', '/.claude/skills', '/.agentskills',
              '/.config/opencode/superpowers/skills'):
    dup = sorted(names(h + store) & set(prov))
    if dup:
        print('###', store)
        for d in dup:
            print(f'   {d:32} also from plugin: {", ".join(sorted(prov[d]))}')
PY
```

Expected on a clean machine: overlap only in `~/.agentskills` and
`~/.config/opencode/superpowers/skills`. Those two stores exist deliberately —
they give OpenCode what Claude gets from plugins, and each harness loads only
its own copy. **Do not fold them into `~/.agents/skills`**; doing so would
duplicate roughly fifteen skills into Claude.

Overlap reported in `~/.agents/skills` or `~/.claude/skills` is a real problem:
remove the local copy and let the plugin provide it.

### 5. Refresh the diverged `frontend-design` copy

`~/.agentskills/frontend-design` and the `frontend-design@claude-plugins-official`
plugin ship different versions of the same skill. The plugin's is newer. Since
`~/.agentskills` is unmanaged, this must be redone per machine:

```bash
P=~/.claude/plugins/cache/claude-plugins-official/frontend-design/unknown/skills/frontend-design
diff -q "$P/SKILL.md" ~/.agentskills/frontend-design/SKILL.md \
  || cp "$P/SKILL.md" ~/.agentskills/frontend-design/SKILL.md
```

### 6. Verify

```bash
# fully synced -- expect no output
chezmoi status ~/.agents ~/.local/bin ~/.claude/skills

# source matches store exactly
diff <(ls ~/.agents/skills) <(ls ~/zendots/dot_agents/skills) && echo "parity ok"

# every skill linked into Claude
for s in ~/.agents/skills/*/; do n=$(basename "${s%/}")
  [ -L ~/.claude/skills/"$n" ] || echo "MISSING LINK: $n"
done; echo "link check done"

# nothing dangling
find ~/.claude/skills ~/.config/opencode/skills ~/.agents/skills \
  -maxdepth 1 -xtype l -print

# scripts landed
ls -l ~/.local/bin/agent-skills.sh ~/.local/bin/link-agent-skills.sh
```

Then confirm a skill actually loads: start Claude Code and check that a
store-only skill such as `orca-worktree-hooks` appears in its skill list.

## macOS notes

- Both scripts are macOS-safe: plain `readlink`, `ln -sfn`, and the bash `-ef`
  test all behave the same on BSD userland, and no GNU-only flags are used.
- The audit snippets above avoid `stat -c`, which is GNU-only. If you reach for
  `stat`, use `stat -f` on macOS.
- Paths are identical apart from `$HOME` (`/Users/<you>` rather than
  `/home/<you>`). `~/.config/opencode` is correct on macOS too — OpenCode uses
  XDG on both platforms.
- `~/.claude/plugins/cache/...` paths in step 5 depend on which plugins are
  installed; adjust if `frontend-design` is not enabled on the Mac.

## After this

Nothing here is repeatable maintenance. From now on the workflow is just:

```bash
agent-skills.sh add <repo>       # install + record + link
cd ~/zendots && git add -A && git commit && git push
```

On the other machine the source arrives over Syncthing, so it is usually just:

```bash
chezmoi apply ~/.agents ~/.claude/skills
```

**Install a skill on one machine only.** Both machines write to the same synced
source, so running `agent-skills.sh add` for the same skill on each produces
competing writes to `dot_agents/skills/` and `dot_agents/dot_skill-lock.json`,
which Syncthing resolves as `*.sync-conflict*` files. Install on one, let it
sync, apply on the other. See `CLAUDE.md` → *Agent Skills*.

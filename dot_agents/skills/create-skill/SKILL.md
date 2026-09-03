---
name: create-skill
description: Use when the user asks to create, author, or add a new agent skill to the shared ~/.agents/skills store so Claude Code, Codex, Pi, and OpenCode all pick it up.
disable-model-invocation: true
---

# Create Skill

`~/.agents/skills/<name>/SKILL.md` is the only copy of a skill. chezmoi vendors
it as `dot_agents/skills/<name>` in `~/zendots`. Codex, Pi, and OpenCode read
the store directly; Claude Code reads it through symlinks in `~/.claude/skills`
that `agent-skills.sh` maintains. Never write a skill anywhere else.

## 1. Check it does not already exist

```bash
ls ~/.agents/skills
python3 -c 'import json;print(*json.load(open("'"$HOME"'/.claude/settings.json"))["enabledPlugins"],sep="\n")'
ls ~/.claude/plugins/cache/*/*/*/skills 2>/dev/null
cd ~ && npx -y skills@latest find "<topic>"
```

A skill an enabled Claude plugin already provides would load twice in Claude.
A good public skill is installed, not rewritten: `agent-skills.sh add <owner/repo>`.

## 2. Pin the design before writing

Ask for whatever is missing, one question at a time:

- **Name**: verb-first, lowercase, hyphens, 64 chars max (`create-skill`, not `skill-creation`).
- **Trigger mode**: manual-only (user types it) or automatic (model picks it from the description).
- **Inputs**: what the skill needs and which it must ask for when absent.
- **Output**: what "done" looks like: a file, a report, a spawned session.

## 3. Write `SKILL.md`

```markdown
---
name: <name>
description: Use when <triggering situations and user phrasings>.
disable-model-invocation: true   # manual-only skills only
---

# <Title>

One paragraph: what the skill produces and the key facts it relies on.

## 1. <Step>
Imperative instructions. Exact commands in fenced blocks. Say what to ask for
when an input is missing.

## Output
The exact shape of the result.
```

Rules that matter:

- Description states *when* to use it, in third person. Do not summarize the
  workflow there; agents follow the description instead of reading the body.
- Keep the body under about 150 lines. Move long templates, rubrics, and
  reference material to `references/<file>.md` and link them from the step that
  needs them. Executable helpers go in `scripts/`.
- Prefer exact commands over prose. Explain why a rule exists in one clause
  rather than shouting MUST.
- Skills are harness-neutral. Do not reference Claude-only tools by name; say
  "spawn a subagent" or give a shell command.

## 4. Manual-only skills need two switches

`disable-model-invocation: true` in the frontmatter covers Claude Code and Pi.
Codex ignores that key and reads `agents/openai.yaml` instead:

```yaml
policy:
  allow_implicit_invocation: false
```

Write both, or Codex will auto-trigger the skill.

OpenCode ignores both and offers every skill to the model. The nearest switch
is a permission rule in `~/.config/opencode/opencode.json`, which makes
OpenCode ask before loading it:

```json
"permission": { "skill": { "<name>": "ask" } }
```

## 5. Record and verify

```bash
agent-skills.sh sync          # chezmoi add + relink ~/.claude/skills
ls -l ~/.claude/skills/<name> # symlink into ~/.agents/skills
chezmoi diff ~/.agents/skills/<name>   # expect no diff
```

Invocation per harness: `/<name>` in Claude Code, `$<name>` in Codex,
`/skill:<name>` in Pi.

## 6. Commit

```bash
cd "$(chezmoi source-path)" && git add dot_agents/skills/<name> && git commit
```

Skills reach the other machine through Syncthing plus `chezmoi apply
~/.agents ~/.claude/skills`. Author on one machine only.

For prompt-based evals of a finished skill, Claude Code's `skill-creator`
plugin has the tooling; nothing here depends on it.

---
name: find-skills
description: Use when the user asks to find, search for, or install an agent skill ("find a skill for X", "is there a skill that...").
disable-model-invocation: true
---

# Find Skills

Searches the open agent skills ecosystem for a skill that does what the user
wants, checks it before recommending it, and installs it through
`agent-skills.sh` when asked.

## 1. Check what is already installed

```bash
ls ~/.agents/skills
python3 -c 'import json;print(*json.load(open("'"$HOME"'/.claude/settings.json"))["enabledPlugins"],sep="\n")'
```

A local skill or enabled Claude plugin that already does the job wins; a
duplicate loads twice. Skills absent from `~/.agents/.skill-lock.json` are
locally maintained adaptations: never reinstall them from upstream.

## 2. Search

```bash
npx skills find <specific query> [--owner <owner>]
```

Use specific terms ("react testing", not "testing") and try synonyms when a
search is empty. Browse <https://skills.sh/> for the same index.

## 3. Read the source before recommending

Install counts and stars measure popularity, not fitness. For each candidate,
read its `SKILL.md` and every script it ships:

- what it does, and whether it fits the user's tools and instructions;
- scripts that make network calls, install packages, or phone home on each
  run (one fetched skill ran an update check against a remote manifest);
- overlap with the global instructions or an existing skill.

## 4. Recommend, then install only when asked

Give the name, what it does, the source link, what you found in its source,
and the install command. Install only through the wrapper, which runs from
`$HOME` and records the store in chezmoi:

```bash
agent-skills.sh add <owner>/<repo>@<skill>
```

Never run a bare `npx skills add`, and never add a whole collection
(`mattpocock/skills`, `cursor/plugins`) when only some of its skills are
wanted: it overwrites local adaptations. Commit afterwards. When nothing
fits, say so and offer `create-skill` for a recurring task.

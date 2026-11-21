# Superpowers retirement on 2026-11-21

The source configuration retires the Superpowers plugin from Claude Code,
Codex, and OpenCode. The user approved deployment on macbook and macmini, and
both hosts run it. tsuki was offline and is pending.

## Decision and retained guidance

Superpowers injected its bootstrap into every session, but transcript scans
found few sessions that invoked its skills. The global AGENTS.md also carried
overrides to keep its test and review rules in check. The replacement keeps
the parts the user relies on:

- `private_dot_config/opencode/AGENTS.md` asks every foreseeable major
  decision in one up-front round, as multiple choice with a labeled
  recommendation and a one-line reason. A major decision found after approval
  waits until the work that does not depend on it is finished, then it is asked.
- The new `plan-feature` skill holds the interview, intent file, spec with 3 to
  6 done checks, design review, plan, feature summary page, and approval gate.
  It replaces Superpowers `brainstorming` and `writing-plans`.
- `open-pr` and `babysit-pr` no longer refer to Superpowers skills.

Specs and plans still default to the ignored `docs/superpowers/` folder.

## Per-host steps

After the scoped apply of `~/.claude/settings.json`,
`~/.config/opencode/opencode.json`, `~/.config/opencode/AGENTS.md`,
`~/.config/opencode/sync_skill_collections.sh`, and
`~/.agents/skills/{plan-feature,open-pr,babysit-pr}`:

```bash
~/.local/bin/link-agent-skills.sh
~/.config/opencode/sync_skill_collections.sh
codex plugin remove superpowers@openai-curated-remote
```

The Codex plugin is account-level. After the macbook removal, macmini already
listed it as not installed. Check `codex plugin list` on tsuki after its apply.

## Verification

On both Macs, `claude plugin list` shows Superpowers disabled,
`~/.claude/skills/plan-feature` links into the store, the OpenCode plugin list
is the notifier and Hindsight only, and `codex plugin list` shows Superpowers
not installed. A tier 3 council review (GPT-6.2 Sol, Gemini 4 Neon, Grok 4.7)
found wording gaps in `plan-feature` and the docs; all confirmed findings were
fixed before the macmini apply.

The `plan-feature` wording was not retested with model runs after the last
fixes. The first real planning sessions are its check.

## Rollback

Revert this change, set the Claude plugin key back to true, restore the
OpenCode pin, apply the same paths, and run
`codex plugin add superpowers@openai-curated-remote`.

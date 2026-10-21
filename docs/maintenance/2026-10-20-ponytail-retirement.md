# Ponytail retirement on 2026-10-20

The source configuration retires Ponytail from Claude, Codex, OpenCode, and Pi.
The user approved deployment on tsuki and macmini. Native Claude and Codex
plugin cleanup and scoped configuration deployment completed on both hosts.
The earlier [agent maintenance report](2026-10-20-agent-updates.md)
records the state before this decision.

## Decision and retained guidance

The consultation covered the complete Ponytail v5.3.2 tree at commit
`16352ac229eb08a9598dcae48fe9f2b342567d86`: all six skills, hooks, configuration
and map builders, OpenCode and Pi adapters, uninstall script, and benchmarks.
OpenCode and Pi had older v4 package pins; those source entries are removed too.

Two existing bullets in `private_dot_config/opencode/AGENTS.md` retain the useful
guidance: trace a failing path and search its callers and affected siblings;
search string and dynamic references before deletion or renaming; include
required supporting files; preserve required validation, error handling, and
compatibility; reuse suitable project helpers, components, dependencies, and
tools. Existing repository rules still govern when tests are added.

No replacement skill or optional Ponytail activation workflow is added.
The existing [independent-review skill](../../dot_agents/skills/independent-review/SKILL.md)
now handles repository and folder audits as well as change reviews. Natural
requests such as "audit this repository" select that skill without an extra
activation command. Audits cover the named current working tree, including
existing defects and non-ignored untracked files, and work on a clean tree.
Ordinary change reviews retain their introduced-defect requirement. Fresh
finders and independent verifiers remain required for both targets. Pi retains
its existing audit workflow too; no new skill, mode, or invocation policy is
added.

The review brief now judges per-item queries, repeated work, resource growth,
and concurrency against expected request rate, batch size, and data volume.
Reviewers must cite repository evidence, including documentation, deployment
configuration, tests or code bounds, or state an assumption. They must tie a
performance finding to a concrete consequence. Verifiers
check the load evidence and resource cost. This change makes no measured
performance or cost claim.

## Source changes and live state

| Destination | Source behavior after apply |
| --- | --- |
| `~/.config/opencode/AGENTS.md` | Refines the two existing guidance bullets. |
| `~/.claude/settings.json` | Removes `enabledPlugins["ponytail@ponytail"]` and `extraKnownMarketplaces["ponytail"]`. |
| `~/.codex/config.toml` | Removes `plugins["ponytail@ponytail"]` and `marketplaces["ponytail"]`. |
| `~/.config/opencode/opencode.json` | Removes the Ponytail plugin package. |
| `~/.pi/agent/settings.json` | Replaces the managed package list without Ponytail. |
| `~/.agents/skills/independent-review` | Adds repository and folder audit support and expected-load criteria to the existing skill. |

The canonical skill store on tsuki already matches its vendored source, so the
local skill needed no apply. The updated skill was applied on macmini alongside
the five configuration destinations.

Claude and Codex modify scripts explicitly remove those four registrations.
Omitting them from the managed fragments alone would preserve their live
values. Unrelated plugins and marketplaces remain subject to the existing
merge rules. This retirement adds no removal entries or apply hooks.

## Scoped deployment and native cleanup

On each host, synchronize the source before deployment. Start fresh agent
sessions afterward; existing user sessions are left running.
On macmini, preview all six destinations and review the complete diff. On tsuki,
omit the final skill path from these commands because its store already matches:

```bash
chezmoi diff -r \
  ~/.config/opencode/AGENTS.md \
  ~/.claude/settings.json \
  ~/.codex/config.toml \
  ~/.config/opencode/opencode.json \
  ~/.pi/agent/settings.json \
  ~/.agents/skills/independent-review
```

After explicit approval, remove the installed user plugins before removing
their marketplaces, then apply the scoped configuration changes. The inventory
on both hosts contained one Ponytail user installation in each native client.

```bash
claude plugin uninstall ponytail@ponytail --scope user --keep-data --json
claude plugin marketplace remove ponytail --json
codex plugin remove ponytail@ponytail --json
codex plugin marketplace remove ponytail --json
```

Re-run the scoped preview after native cleanup, then apply the same destinations
with scripts excluded:

```bash
chezmoi diff -r \
  ~/.config/opencode/AGENTS.md \
  ~/.claude/settings.json \
  ~/.codex/config.toml \
  ~/.config/opencode/opencode.json \
  ~/.pi/agent/settings.json \
  ~/.agents/skills/independent-review
chezmoi apply --exclude scripts \
  ~/.config/opencode/AGENTS.md \
  ~/.claude/settings.json \
  ~/.codex/config.toml \
  ~/.config/opencode/opencode.json \
  ~/.pi/agent/settings.json \
  ~/.agents/skills/independent-review
```

These commands target the inventoried user installations. Check any reported
absence against the client's installed-plugin inventory before proceeding.
Inspect any project or local scope separately if a fresh inventory finds one.
Do not run the upstream uninstall script, which deletes Ponytail preferences.
The [Claude CLI reference](https://code.claude.com/docs/en/plugins/cli-reference#plugin-marketplace-remove)
documents scoped and unscoped marketplace removal. During deployment,
`--scope user` removed macmini's declaration but left Ponytail in its cached
marketplace inventory. The unscoped native command removed that residual
catalog. The final inventory check passed on both hosts.

Preserve inert preferences and statistics under `~/.config/ponytail/`,
`~/.claude/.ponytail-band`, and Claude's plugin data directory. Cached Pi and
OpenCode packages may remain inert after their configuration entries are
removed. Delete cache data only through a justified native cleanup operation.
Inspect residual hooks, statusline commands, skill links, and activation
markers; remove any active Ponytail integration through its owning
configuration. Inert data retention does not retain an activation workflow.

## Verification and remaining limits

Both hosts passed `chezmoi verify -r --exclude scripts` for their scoped
destinations. Repeat recursive diffs and scoped status checks were empty.
All six canonical review-skill files match the vendored source on both hosts.
Claude's existing skill links resolve to that canonical store.

The global Claude, Codex and Pi instruction files match OpenCode's shared file
byte for byte on each host. Its SHA-256 is
`a40112b5526ab232b35524a84227e82debe25e8d26ea198ac12cdc40bc69e1f6`.
OpenCode's live plugin configuration and Pi's live package configuration contain
no Ponytail entry. No standalone Ponytail skill links remain in the five
inspected harness and universal skill directories.

Native inventory comparisons confirmed these before and after counts. Other
installed plugin identities and enabled states, and other marketplace names,
were preserved.

| Host | Claude Ponytail plugins | Claude Ponytail marketplaces | Codex Ponytail plugins | Codex Ponytail marketplaces |
| --- | --- | --- | --- | --- |
| tsuki | 1 to 0 | 1 to 0 | 1 to 0 | 1 to 0 |
| macmini | 1 to 0 | 1 to 0 | 1 to 0 | 1 to 0 |

Claude's live hooks and statusline configuration and Codex's hooks file contain
no Ponytail command. Codex retains three inert `hooks.state` trust records on
each host. They contain only `trusted_hash` metadata and do not register or
enable a hook. No installed Ponytail plugin remains.

Before deployment, 29 modifier checks passed, including unrelated-key
preservation, TOML table variants and repeat-run equality. Skill validation and
bounded audit, verifier and ordinary change-review probes passed. A fresh
Claude review found a P3 inconsistency in expected-load wording. An independent
verifier classified it as plausible; the wording was clarified and affected
checks passed. No additional review round was needed for deployment reporting.

Fresh interactive sessions in all four clients were not exercised. Existing
user sessions were left running and may retain previously loaded instructions
until restarted. The checks establish deployed configuration, native inventory
and skill-file parity; they do not measure performance or prove how a model
will select the skill in a future task.

Both repositories have four pre-existing Syncthing conflict copies under
`.git/objects`. `git fsck --no-dangling` reports those bad-name files; they were
left untouched. Commit availability is checked separately with
`git cat-file -e HEAD^{commit}` and full commit identities on both hosts.

| Host | Scoped apply | Native cleanup | Fresh-session verification |
| --- | --- | --- | --- |
| tsuki | Applied and verified | Complete; final inventory checked | Not exercised; user sessions left running |
| macmini | Applied and verified | Complete; final inventory checked | Not exercised; user sessions left running |

The scoped apply column covers five configurations on tsuki and those five
configurations plus `~/.agents/skills/independent-review` on macmini.

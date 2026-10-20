# Agent maintenance on 2026-10-20

Ponytail 5.3.2 is installed and enabled in Claude and Codex on Tsuki and
macmini. Each installation's six skill files match the upstream marketplace
files. Existing sessions need a restart to load refreshed packages.

## Skills, clients, and plugins

| Check | Tsuki | macmini |
| --- | --- | --- |
| Shared skill store | 31 skills verified | Same 31 skills verified |
| Claude marketplace install records refreshed | 21 | 17 |
| Claude installed versions changed | 14 | 0, already current |
| Codex installed packages refreshed | 30 | 31 |
| Claude client after supported update | 2.1.304 | 2.1.304 |
| Codex client after supported update | 0.163.0 | 0.163.0 |
| Ponytail in Claude and Codex | 5.3.2, enabled | 5.3.2, enabled |

`agent-skills.sh update -y` ran once on Tsuki and reported all global skills
current. The store contains four upstream-locked skills and 27 locally
maintained skills. The update preserved local adaptations and produced no
tracked skill changes. The store-backed Humanizer installation was preserved.

Claude marketplaces were refreshed, then every marketplace install record was
updated individually on each host, including project-scoped records. Tsuki's
version changes include Ponytail 5.1 to 5.3.2 and Superpowers 6.4.1 to 7.0.0.

Codex marketplaces were refreshed, then every installed package was refreshed
through `codex plugin add`. Actual install results and cache files show Sites
1.1.0 on both hosts, replacing 1.0.2-remix-a.1. Codex plugin list output still
reported the older Sites version through its stale catalog metadata, including
the installed-package listing. The install result and cache establish the
installed version.

Codex's bundled packages and primary runtime packages differ between hosts.
They remain provider-managed snapshots. Claude app-synchronized skills also
remain provider-managed. This maintenance does not establish that those
snapshots match the latest upstream source. Codex's curated Superpowers
package remains 6.4.2, while Claude's marketplace package is 7.0.0.

## MCP runtime checks and repairs

| Runtime | Result |
| --- | --- |
| Serena | Refreshed on both hosts to upstream commit `abb0a0f01b94bc8050086f0fb860077d17730324`. Claude health checks connected on both. |
| Playwright | npm package 0.0.83 matched the registry's latest version. MCP initialization and tool listing passed on both hosts with 25 tools. |
| Sequential Thinking | npm package 2.0.0 matched the registry's latest version. MCP initialization and tool listing passed on both hosts with one tool. Claude health checks connected on both. |
| Context7 | Tsuki's existing `pmi-datalake` Claude project entry used invalid package `@context7/mcp`. It now uses `@upstash/context7-mcp@latest`. Initialization reported server 4.4.4 and tool listing returned two tools. |

The existing managed bootstrap registered Sequential Thinking on macmini.
These repairs affected host runtime state and required no tracked
configuration edits.

MCP initialization and tool listing establish local protocol compatibility.
Authenticated remote tool operations were not tested. Claude Productivity's
Slack, Notion, Linear, Atlassian, Monday, and ClickUp connections still need
login. Asana reported an authentication server incompatible with dynamic
client registration. Calendar and Gmail placeholders remain unconfigured.

macmini's app-managed relative `computer-use` path was not found in the normal
application locations checked. Its existing entry was preserved.

## Deployment and repository checks

Scoped recursive chezmoi previews were empty on both hosts. Scoped applies
with scripts excluded and subsequent chezmoi verification passed on both for:

- `~/.agents/skills`, `~/.agents/.skill-lock.json`, and `~/.agents/.runtime-lock.json`.
- `~/.claude/skills`, `~/.claude/settings.json`, `~/.claude/mcpServers.json`, and `~/.claude/bootstrap_mcpservers.sh`.
- `~/.codex/skills` and `~/.codex/config.toml`.

The runtime updates produced no tracked configuration changes. This record
captures the per-host maintenance that a dotfiles commit cannot reproduce.

Both hosts' zendots Syncthing folders reported idle, zero needed items, and
zero folder errors. The canonical Git HEAD resolved to a commit on both.
`git fsck` exited zero but warned about four bad SHA-1 filenames belonging to
existing Syncthing conflict copies. The read-only `work-sync conflicts` scan
reported 17 quarantinable files and zero unresolved files. No conflict files
were removed.

Restart Claude and Codex sessions to use the refreshed packages. Remote MCP
login and any conflict cleanup remain separate actions.

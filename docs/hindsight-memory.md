# Hindsight agent memory

Claude Code, Codex (including Codex inside T3 Code) and OpenCode share one
project memory across macmini and macbook. One self-hosted Hindsight server on
macmini stores it. Each machine runs Hindsight's coding-agents client, and
chezmoi wires its hooks into every harness. A zendots hook also records failed
shell commands, which Hindsight's own hooks drop.

The plan, with its done checks, lives in the ignored
`docs/superpowers/plans/2026-11-12-hindsight-memory.md` on the machines that
built it. The intent file beside it records the user's choices.

## What runs where

macmini runs the server. The LaunchAgent `com.dkishore.hindsight-api` starts
`uvx hindsight-api@latest` on `127.0.0.1:8888`, from the working directory
`~/.hindsight-server`. launchd restarts it if it exits. Its Postgres database
is embedded (pg0) and lives in `~/.pg0/instances/hindsight`.

Tailscale Serve publishes the server at
<https://dileeps-mac-mini.tail870d70.ts.net>. Only devices on the tailnet can
reach that address. Serve had to be enabled once in the Tailscale admin
console before macmini could use it.

Every machine runs the client. Its runtime is staged in
`~/.hindsight/coding-agents`, and `~/.hindsight/coding-agent.json` configures
it. macmini's client talks to `http://127.0.0.1:8888`. Every other host uses
the tailnet URL.

| Harness | What chezmoi adds |
| --- | --- |
| Claude Code | `SessionStart`, `UserPromptSubmit` and `Stop` hooks, a `PostToolUseFailure` hook for Bash, and a user-scope MCP server named `hindsight` |
| Codex | `SessionStart`, `UserPromptSubmit` and `Stop` hooks, the failure hook at `Stop`, and `mcp_servers.hindsight` in `~/.codex/config.toml` |
| OpenCode | The runtime directory in the `plugins` list of `~/.config/opencode/opencode.json` |

The client script also copies Hindsight's companion skill to
`~/.agents/skills/hindsight-coding-agent`. `link-agent-skills.sh` links it for
Claude Code. `.chezmoiignore` keeps that skill, the runtime, its logs and its
state out of this repository.

## What leaves the machines

The memory stays on macmini. The server computes embeddings and reranking
locally (`HINDSIGHT_API_EMBEDDINGS_PROVIDER=local`,
`HINDSIGHT_API_RERANKER_PROVIDER=local`). OpenTelemetry tracing is off.

Claude Haiku (`claude-haiku-4-5`) extracts facts from each session. The
server's `claude-code` provider runs it through macmini's Claude login, so it
needs no API key. Hindsight's documentation warns that using a subscription
for automated calls may conflict with Anthropic's terms outside personal,
local use.

The LaunchAgent's environment turns off the spawned Claude CLI's telemetry,
error reporting and nonessential traffic. It also sets
`ENABLE_CLAUDEAI_MCP_SERVERS=false`. Without that setting, the CLI loaded
every claude.ai connector on the account. That added about 245k tokens of
tool definitions to every call, and every call failed as too long.

The client config sets `"serverMode": "self-hosted"` and an explicit `apiUrl`.
Without those two keys the client falls back to Hindsight Cloud. The modify
script refuses to write any other `serverMode` or a Vectorize URL.

## Where the secrets live

One tenant API key guards the server. It never enters this repository.

- macmini keeps it as `HINDSIGHT_API_TENANT_API_KEY` in
  `~/.hindsight-server/.env`, mode 600. The server reads that file from its
  working directory.
- Each client keeps it as `apiToken` in `~/.hindsight/coding-agent.json`,
  mode 600. The modify script enforces every other key in that file and
  keeps the live `apiToken`.

Write the token once on each client after its first apply. These commands
copy the key without printing it, and fail without touching the config when
no key is found.

On macmini:

```bash
(
  umask 077
  cfg=~/.hindsight/coding-agent.json
  sed -n 's/^HINDSIGHT_API_TENANT_API_KEY=//p' ~/.hindsight-server/.env |
    jq --rawfile key /dev/stdin \
      '($key | rtrimstr("\n")) as $k
       | if ($k | length) > 0 then .apiToken = $k else error("no key found") end' \
      "$cfg" > "$cfg.new" && mv "$cfg.new" "$cfg"
)
```

On any other host, read the key from macmini over SSH:

```bash
(
  umask 077
  cfg=~/.hindsight/coding-agent.json
  ssh macmini "sed -n 's/^HINDSIGHT_API_TENANT_API_KEY=//p' ~/.hindsight-server/.env" |
    jq --rawfile key /dev/stdin \
      '($key | rtrimstr("\n")) as $k
       | if ($k | length) > 0 then .apiToken = $k else error("no key found") end' \
      "$cfg" > "$cfg.new" && mv "$cfg.new" "$cfg"
)
```

## How memory is shared

Each repository gets one memory bank, `coding-agent::<main checkout folder
name>`. The client takes the folder name from `git --git-common-dir`, so
linked worktrees, T3 worktrees included, use the main checkout's bank. The
same repository on another machine uses the same bank, because Syncthing keeps
the folder names the same.

Every write is tagged `host:<machine>`, and the client asks the extractor to
start machine-specific facts with `On <machine>:`. The machine name comes from
`.chezmoitemplates/host-alias`.

At session start the client injects a recall of up to 2,000 tokens. It
contains this machine's tagged facts plus the consolidated observations every
machine shares. Another machine's raw facts arrive only after the server
consolidates them into observations. In testing that took about 100 seconds.
The client's tool guide tells agents to check any memory against the current
files, and to follow the files when they disagree.

Machine facts live inside each project's bank. No memory spans projects, so a
fact about macmini learned in one repository does not appear in another.

Two unrelated repositories with the same folder name share a bank. Hindsight's
config can map an absolute checkout path to another bank through its `paths`
section. The modify script deletes the `harnesses`, `paths` and `banks`
sections from the live file on every apply. Add such an override to `MANAGED`
in `private_dot_hindsight/modify_private_coding-agent.json.tmpl` instead, and
template it per host, because its keys are absolute paths.

## How failed commands are recorded

Hindsight drops command output before extraction, so a failure is otherwise
remembered only when someone describes it. `~/.local/bin/hindsight-failure-hook`
sends each failed shell command to the same per-repository bank. Each record
holds the command, its exit code and up to 1,500 characters of error output.
It is tagged with the machine's `host:` tag and `source:failure-hook`.

Claude Code runs the hook on each Bash failure through `PostToolUseFailure`.
Codex hook payloads carry no exit status, so Codex runs it at `Stop`. It then
scans the session log for failed commands it has not sent yet. It tracks the
ones it has sent in `~/.hindsight/state/failure-hook/`.

The hook masks likely secrets before sending: `sk-` and GitHub tokens, Slack
tokens, bearer tokens, and `password=`, `secret=`, `token=` or `api_key=`
values. It skips exit 1 when the command printed no error or is a search or
test command such as `grep`, `rg`, `test`, `diff` or `git diff`. It skips exit
130 and 143, which mean the user interrupted the command. A repeated failure
with the same command and first error line replaces the earlier record.

The hook never prints to stdout and always exits 0, so it cannot block an
agent. It logs each record it sends, and each error, to
`~/.hindsight/coding-agents-logs/failure-hook.log`.

The hook sees only the exit status of the whole command. An agent that appends
`; echo $?` to a failing command makes it exit 0, so the hook does not record
it. Hindsight's transcript extraction can still capture that failure.

## Setting up a host

Each step shows a scoped diff first. Apply the same paths only after you
approve the diff. Scoped applies skip `.chezmoiscripts` unless the script's
target, `~/.chezmoiscripts/<name>`, is in the path list. Over SSH to macmini,
put Homebrew on the path first: `PATH=/opt/homebrew/bin:$PATH chezmoi ...`.

### Server, on macmini only

1. Create the key file. This writes a new key without printing it:

   ```bash
   install -d -m 700 ~/.hindsight-server
   (umask 077; printf 'HINDSIGHT_API_TENANT_API_KEY=%s\n' "$(openssl rand -hex 32)" > ~/.hindsight-server/.env)
   ```

   The server script refuses to load the agent while this file is missing.
2. Apply the plist, then its script, in two applies. In one combined apply the
   script ran first, and `launchctl` failed with error 5 because the plist was
   not there yet:

   ```bash
   chezmoi diff -r ~/Library/LaunchAgents/com.dkishore.hindsight-api.plist
   chezmoi apply ~/Library/LaunchAgents/com.dkishore.hindsight-api.plist
   chezmoi diff -r ~/.chezmoiscripts/55_hindsight-server.sh
   chezmoi apply ~/.chezmoiscripts/55_hindsight-server.sh
   ```

   The script creates `~/.hindsight-server/logs` and bootstraps the agent. It
   reruns whenever the plist changes.
3. Publish the server on the tailnet, once. Serve must already be enabled in
   the Tailscale admin console:

   ```bash
   tailscale serve --bg --https=443 http://127.0.0.1:8888
   tailscale serve status
   ```

### Client, on every host

1. Apply the config and the client script. On a fresh host, apply the
   `~/.hindsight` directory, not the single file. chezmoi did not create the
   missing parent directory for the file target:

   ```bash
   chezmoi diff -r ~/.hindsight ~/.chezmoiscripts/60_hindsight-client.sh
   chezmoi apply ~/.hindsight ~/.chezmoiscripts/60_hindsight-client.sh
   ```

   The script stages the runtime with
   `npx -y @vectorize-io/hindsight-coding-agents@latest update`, seeds the
   skill, and adds Claude Code's MCP entry. It skips each step whose tool is
   missing and prints a message. To rerun it after installing a missing tool,
   raise the `Bump to rerun` number in
   `.chezmoiscripts/run_onchange_after_60_hindsight-client.sh.tmpl`.
2. Write the token with the command in [Where the secrets live](#where-the-secrets-live).
3. Apply the harness wiring:

   ```bash
   chezmoi diff -r ~/.claude/settings.json ~/.codex/hooks.json ~/.codex/config.toml \
     ~/.config/opencode/opencode.json ~/.local/bin/hindsight-failure-hook
   chezmoi apply ~/.claude/settings.json ~/.codex/hooks.json ~/.codex/config.toml \
     ~/.config/opencode/opencode.json ~/.local/bin/hindsight-failure-hook
   ```

4. Trust Codex's hooks, once per machine. Codex runs new hooks only after
   someone approves them. Run `codex` in a terminal in any repository and
   choose "Trust all and continue". T3 Code runs Codex through its app server,
   which never shows that prompt.

The client script, the hook commands and the Codex MCP entry use the `node`
path found when chezmoi renders them. Install Node before step 1.

## Adding tsuki

tsuki joins as a client with the same client steps. Most differences come
from the templates:

- `.chezmoitemplates/host-alias` names it from its hostname, so its tag is
  `host:tsuki`.
- The modify script labels its OS `CachyOS Linux` instead of `macOS`.
- The hook commands and the Codex MCP entry take the `node` path from
  `lookPath` on tsuki. Without Node on the path, they fall back to a bare
  `node`.
- `.chezmoiignore` keeps the LaunchAgent and the server script on macmini, so
  tsuki gets neither.

tsuki reaches the server through the tailnet URL, so it must be on the
tailnet. The key copy needs an SSH route to macmini. If tsuki's SSH config has
no `macmini` host, replace `ssh macmini` with the tailnet name. Trust Codex's
hooks on tsuki as in step 4.

## Checking that it works

```bash
claude mcp list   # hindsight: ... Connected
codex mcp list    # hindsight ... enabled
curl -s -o /dev/null -w '%{http_code}\n' https://dileeps-mac-mini.tail870d70.ts.net/health   # 200
tail -n 20 ~/.hindsight/coding-agents-logs/diag.jsonl | jq -c '{ts, harness, event, count}'
```

On macmini, use `http://127.0.0.1:8888/health`. A request to
`/v1/default/banks` without the key returns `401`.

`diag.jsonl` records each client event. A working session logs
`session_start`, then `inject_recall` with the number of memories injected,
then `retain_ok` after the session is saved. The failure hook writes to
`failure-hook.log` in the same directory.

On macmini, the server logs to `~/.hindsight-server/logs/api.out.log` and
`api.err.log`, at warning level. These commands show the agent's state and
environment, and restart it:

```bash
launchctl print "gui/$(id -u)/com.dkishore.hindsight-api"
launchctl kickstart -k "gui/$(id -u)/com.dkishore.hindsight-api"
```

## Turning off automatic recall

In `private_dot_hindsight/modify_private_coding-agent.json.tmpl`, change
`"autoInject": "recall"` to `"autoInject": "none"`. Then diff and apply
`~/.hindsight/coding-agent.json` on each host. Sessions start without injected
memory. The `hindsight` MCP tools stay available, and sessions are still
saved.

## Uninstalling

1. On macmini, stop the server:

   ```bash
   launchctl bootout "gui/$(id -u)" ~/Library/LaunchAgents/com.dkishore.hindsight-api.plist
   ```

2. Remove the hook entries while the merge code still exists. Set
   `HINDSIGHT_HOOKS = {}` in `private_dot_claude/modify_settings.json.tmpl`
   and `dot_codex/modify_hooks.json.tmpl`. Apply `~/.claude/settings.json`
   and `~/.codex/hooks.json` on every host. The merge then deletes every hook
   whose command contains `/.hindsight/coding-agents/dist/` or
   `hindsight-failure-hook`. Deleting the merge code first would leave those
   hooks in the live files.
3. Remove the remaining managed entries from the source: the Hindsight code
   in both hook modify scripts, the `mcp_servers.hindsight` block in
   `dot_codex/modify_private_config.toml.tmpl`, the plugin line in
   `private_dot_config/opencode/opencode.json.tmpl`, the files listed under
   [Source files](#source-files), and the Hindsight lines in
   `.chezmoiignore`. List the plist and `~/.local/bin/hindsight-failure-hook`
   in `.chezmoiremove`, then apply those paths on each host.
4. Remove the MCP entries on each host. The Codex modify script keeps keys
   that its fragment omits, so removing the block from the source does not
   remove the live entry:

   ```bash
   claude mcp remove --scope user hindsight
   codex mcp remove hindsight
   ```

5. Delete the client files on each host: `~/.hindsight`,
   `~/.agents/skills/hindsight-coding-agent` and the link
   `~/.claude/skills/hindsight-coding-agent`.
6. On macmini, delete `~/.hindsight-server` and the database in
   `~/.pg0/instances/hindsight`. `~/.pg0/installation` holds pg0's own
   Postgres installation. Delete all of `~/.pg0` only if no other tool uses
   pg0.
7. On macmini, check `tailscale serve status`. If Serve publishes nothing
   else, `tailscale serve reset` clears it.

## Source files

- Server LaunchAgent: `private_Library/LaunchAgents/com.dkishore.hindsight-api.plist.tmpl`
- Server loader: `.chezmoiscripts/run_onchange_after_55_hindsight-server.sh.tmpl`
- Client staging: `.chezmoiscripts/run_onchange_after_60_hindsight-client.sh.tmpl`
- Client config: `private_dot_hindsight/modify_private_coding-agent.json.tmpl`
- Machine name: `.chezmoitemplates/host-alias`
- Hook merge: `.chezmoitemplates/hindsight-hooks.py`, used by
  `private_dot_claude/modify_settings.json.tmpl` and
  `dot_codex/modify_hooks.json.tmpl`
- Failure hook: `private_dot_local/bin/executable_hindsight-failure-hook`

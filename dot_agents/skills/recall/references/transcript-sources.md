# Transcript sources

Verified on Tsuki (Linux) on 2026-09-06 by inspecting metadata only. macmini
layouts are unverified until checked there; do not assume a mapping. All
timestamps in both formats are UTC; cite them as UTC.

## Claude Code

- Location: `~/.claude/projects/<slug>/<session-id>.jsonl`, one file per
  session. `<slug>` is the absolute checkout path with every `/` replaced by
  `-`, so `/home/dileep/zendots` becomes `-home-dileep-zendots`.
- Each line is one JSON record. `type` is `user`, `assistant`, `system`,
  `attachment`, or bookkeeping (`last-prompt`, `mode`, `permission-mode`,
  `file-history-snapshot`). Message records carry `cwd`, `sessionId`,
  `timestamp`, `gitBranch`, `version`, and `message.role` /
  `message.content`.
- `isSidechain: true` marks subagent lines; skip them by default.
- `<session-id>/tool-results/*.txt` holds large tool outputs that were
  spilled out of the transcript. `memory/` under the project slug is
  auto-memory, not a transcript.

```bash
slug=$(pwd | tr / -)
find ~/.claude/projects/"$slug" -maxdepth 1 -name '*.jsonl' -mtime -7 -printf '%TY-%Tm-%Td %TH:%TM %p\n' | sort -r
grep -l -i '<topic>' ~/.claude/projects/"$slug"/*.jsonl
grep -n -i '<topic>' <file> | head -40        # then sed -n 'A,Bp' the spans
```

## Codex CLI

- Location: `~/.codex/sessions/YYYY/MM/DD/rollout-<timestamp>-<thread-id>.jsonl`.
  The date directory is the session's start; the file's mtime advances while
  the session is open, so a long session lives under an earlier date.
- Line 1 is `session_meta` with `payload.cwd`, `payload.thread_source`
  (`user` for interactive threads, `subagent` for spawned agents, whose
  `payload.source.subagent.thread_spawn.parent_thread_id` names the parent).
- Other lines: `response_item` (`payload.type` `message` with `role`
  user/assistant/developer, `function_call`, `custom_tool_call`, `reasoning`)
  and `event_msg` (`user_message`, `task_started`, `task_complete`,
  `turn_aborted`, `token_count`).
- `~/.codex/history.jsonl` is a fast index: one `{session_id, ts, text}`
  line per user prompt, across all projects.
- `~/.codex/archived_sessions/` exists; not inspected.

```bash
find ~/.codex/sessions -name '*.jsonl' -mtime -7 -printf '%TY-%Tm-%Td %TH:%TM %p\n' | sort -r
for f in $(find ~/.codex/sessions -name '*.jsonl' -mtime -7); do
  head -1 "$f" | grep -q "\"cwd\":\"$PWD\"" && head -1 "$f" | grep -q '"thread_source":"user"' && echo "$f"
done
grep -i '<topic>' ~/.codex/history.jsonl | tail -20
```

## Choosing grep terms

A single common word (`guard`, `sync`) matches nearly every transcript.
Grep distinctive tokens first: file names, script names, flags, exact phrases
from the request. Widen only if that finds nothing.

## Identifying the current session

Neither client exports its session id reliably. The current session is the
candidate whose newest line is seconds old and whose last user message is the
recall request itself; exclude it.

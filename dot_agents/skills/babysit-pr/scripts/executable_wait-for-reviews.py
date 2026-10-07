#!/usr/bin/env python3
"""Wait until the review bots working on a PR's head have finished.

Read-only: it only queries GitHub through `gh`, and never asks a bot to review.
Any bot account or app counts, so Codex, Bugbot, Copilot, CodeRabbit, and
whatever comes next need no configuration. A reviewer announces itself within
seconds of a push or a trigger: a pending review request, a check run or commit
status, an eyes reaction, a comment. Bots that show activity on this head are
the ones waited for. If none appears within the grace period it exits 3, so
repositories without review bots are never polled for long.

A bot is running while it is a requested reviewer, has an unfinished check run
or pending commit status, or has an eyes reaction on the PR or on an
"@bot review" comment. Once it is not running, it is done when it has reviewed
the head commit, its checks have finished, or it has been quiet for the settle
period.

Every time runs from --since, the moment just before the push that created the
head: only activity after it counts, and the grace period and timeout start
there, so a rerun with the same --since resumes the same wait. Without it, the
later of the head commit's date and the PR's creation stands in. If the head
moves while waiting, the wait starts over from when the new head was seen.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime

EXAMPLES = """examples:
  wait-for-reviews.py                     # PR for the current branch
  wait-for-reviews.py --pr 42 --since 2026-10-07T21:43:00Z
  wait-for-reviews.py --pr 42 --repo owner/name --ignore vercel

output: "bot <name> done|pending" lines, then "result done|none|timeout"
exit codes: 0 every active bot finished on the head, 2 deadline passed with
bots pending, 3 no review bot showed up within the grace period, 1 error
"""

# Bots that comment or run checks but never review code.
IGNORED = {
    "github-actions",
    "dependabot",
    "renovate",
    "codecov",
    "vercel",
    "netlify",
    "changeset-bot",
    "stale",
}
TRIGGER = re.compile(r"^@[\w-]+ (security )?review\b", re.MULTILINE)


def ts(stamp: str | None) -> float | None:
    if not stamp:
        return None
    return datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp()


def gh(*args: str) -> object:
    out = subprocess.run(["gh", *args], capture_output=True, text=True, check=False)
    if out.returncode != 0:
        sys.exit(f"error: gh {' '.join(args[:2])}: {out.stderr.strip()}")
    return json.loads(out.stdout) if out.stdout.strip() else None


def pages(path: str, key: str | None = None) -> list:
    """Every item from a paginated endpoint; `key` names the list in each page."""
    result = gh("api", "--paginate", "--slurp", path)
    return [item for page in result for item in (page[key] if key else page)]


def bot_name(user: dict | None) -> str | None:
    """Return the bot's name without "[bot]", or None for people and ignored bots."""
    user = user or {}
    login = user.get("login", "")
    if user.get("type") != "Bot" and not login.endswith("[bot]"):
        return None
    name = login.removesuffix("[bot]")
    return None if name in IGNORED else name


def snapshot(repo: str, pr: int, head: str) -> dict:
    comments = pages(f"repos/{repo}/issues/{pr}/comments")
    reactions = pages(f"repos/{repo}/issues/{pr}/reactions")
    for c in comments:
        if TRIGGER.search(c["body"]):
            reactions += pages(f"repos/{repo}/issues/comments/{c['id']}/reactions")
    return {
        "reviews": pages(f"repos/{repo}/pulls/{pr}/reviews"),
        "comments": comments,
        "reactions": reactions,
        "checks": pages(f"repos/{repo}/commits/{head}/check-runs", "check_runs"),
        "statuses": pages(f"repos/{repo}/commits/{head}/statuses"),
    }


def survey(pr: dict, snap: dict, head: str, since: float) -> dict[str, dict]:
    """Collect each bot active on this head: running, reviewed, checks, last."""
    bots: dict[str, dict] = {}

    def see(user: dict | None, when: float | None = None) -> dict | None:
        name = bot_name(user)
        if name is None:
            return None
        info = bots.setdefault(
            name, {"running": False, "reviewed": False, "checks": {}, "last": 0.0}
        )
        if when is not None:
            info["last"] = max(info["last"], when)
        return info

    for user in pr.get("requested_reviewers", []):
        if info := see(user):
            info["running"] = True
    for r in snap["reviews"]:
        when = ts(r.get("submitted_at"))
        if when is not None and when >= since and (info := see(r["user"], when)):
            info["reviewed"] |= r["commit_id"] == head
    for c in snap["comments"]:
        when = ts(c["updated_at"])
        if when >= since:
            see(c["user"], when)
    for r in snap["reactions"]:
        when = ts(r["created_at"])
        if when >= since and (info := see(r["user"], when)):
            info["running"] |= r["content"] == "eyes"
    for c in snap["checks"]:
        app = {"login": (c.get("app") or {}).get("slug", ""), "type": "Bot"}
        if info := see(app, ts(c.get("started_at"))):
            info["checks"]["check:" + c["name"]] = c["status"] == "completed"
    for s in snap["statuses"]:  # newest first, so the first per context wins
        if info := see(s.get("creator"), ts(s["updated_at"])):
            key = "status:" + s["context"]
            info["checks"].setdefault(key, s["state"] != "pending")
    return bots


def done(info: dict, now: float, settle: int) -> bool:
    if info["running"] or not all(info["checks"].values()):
        return False
    return (
        info["reviewed"]
        or bool(info["checks"])
        or (info["last"] > 0 and now - info["last"] >= settle)
    )


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        epilog=EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--pr", type=int, help="PR number (default: current branch)")
    p.add_argument("--repo", help="owner/name (default: current repository)")
    p.add_argument(
        "--since",
        help="ISO-8601 time just before the push; pass the same value on reruns",
    )
    p.add_argument(
        "--timeout",
        type=int,
        default=1200,
        help="seconds after --since to stop waiting (1200)",
    )
    p.add_argument(
        "--grace",
        type=int,
        default=180,
        help="seconds after --since for a bot to show up (180)",
    )
    p.add_argument(
        "--settle",
        type=int,
        default=120,
        help="quiet seconds before a bot with no review or check counts as done (120)",
    )
    p.add_argument("--interval", type=int, default=30, help="poll seconds (30)")
    p.add_argument(
        "--ignore",
        action="append",
        default=[],
        metavar="BOT",
        help="another bot to ignore; repeatable",
    )
    a = p.parse_args()
    IGNORED.update(name.removesuffix("[bot]") for name in a.ignore)

    repo = a.repo or gh("repo", "view", "--json", "nameWithOwner")["nameWithOwner"]
    number = gh(
        "pr", "view", *([str(a.pr)] if a.pr else []), "--repo", repo, "--json", "number"
    )["number"]
    pr = gh("api", f"repos/{repo}/pulls/{number}")
    head = pr["head"]["sha"]
    if a.since:
        since = ts(a.since)
    else:
        commit = gh("api", f"repos/{repo}/commits/{head}")["commit"]
        since = max(ts(commit["committer"]["date"]), ts(pr["created_at"]))
    print(f"pr {pr['html_url']}\nhead {head}")

    while True:
        snap = snapshot(repo, number, head)
        now = time.time()
        bots = survey(pr, snap, head, since)
        states = {name: done(b, now, a.settle) for name, b in sorted(bots.items())}
        waited = now - since
        result = None
        if bots and all(states.values()) and waited >= a.grace:
            result, code = "done", 0
        elif not bots and waited >= a.grace:
            result, code = "none", 3
        elif waited >= a.timeout:
            result, code = "timeout", 2
        pr = gh("api", f"repos/{repo}/pulls/{number}")
        if pr["head"]["sha"] != head:
            head, since = pr["head"]["sha"], now
            print(f"head {head}")
            continue
        if result is None:
            time.sleep(a.interval)
            continue
        for name, ok in states.items():
            print(f"bot {name} {'done' if ok else 'pending'}")
        print(f"result {result}")
        return code


if __name__ == "__main__":
    sys.exit(main())

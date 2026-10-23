# Images in PR descriptions

GitHub stores an image dragged into a PR description as a `user-attachments`
file, but no API or `gh` command performs that upload. An agent hosts images
in the repository instead, on one orphan branch per repository: `pr-assets`.
Each PR's images sit under `<name>/`, usually the head branch without its
`type/` prefix, and each link pins the commit that added them:

```
https://github.com/<owner>/<repo>/blob/<commit>/<name>/<file>?raw=true
```

`blob/...?raw=true` renders in public and private repositories for anyone who
can read the repository.

## Rules

- Upload with `scripts/pr-images.py`. It commits on top of `pr-assets`
  without touching the working tree or the current branch, and prints the
  Markdown lines to paste.
- Never commit screenshots to the PR's own branch: they would merge into the
  default branch.
- Never create a second image branch (`pr-assets/<name>`, `pr-images`,
  `screenshots`). Git cannot hold `pr-assets/<name>` next to `pr-assets`, and
  every extra branch is one more ref someone deletes by accident.
- Never delete, rename, or force-push `pr-assets`. Merged PRs link to commits
  that only this branch keeps reachable, and GitHub garbage-collects
  unreachable commits, breaking those images.
- A retaken screenshot can reuse its filename. Older links pin older commits,
  so they keep showing the original.

## When the script refuses: per-PR image branches exist

Repositories that predate this convention may have one orphan branch per PR,
such as `pr-assets/chat-widgets`. The script refuses to run there. Open the PR
without images, report the refusal, and ask the user before consolidating:
consolidation deletes remote branches.

Consolidation keeps every old commit reachable, so no merged PR changes. One
merge commit takes all the old tips as parents and holds each branch's files
under a folder named after it. GitHub rejects creating `pr-assets` and
deleting `pr-assets/<x>` in one push, so a temporary branch holds the commit
while the old branches go. Each delete is leased to the tip the commit
includes, and all go in one atomic push: if someone pushed to an old branch
meanwhile, nothing is deleted and the recipe stops; run it again. Run it in
bash; zsh does not split the unquoted lists:

```bash
bash -euo pipefail <<'EOF'
git fetch --quiet origin '+refs/heads/pr-assets/*:refs/remotes/origin/pr-assets/*'
names=$(git for-each-ref --format='%(refname:strip=4)' 'refs/remotes/origin/pr-assets/')
index=$(mktemp -d)/index parents="" leases="" deletes=""
for name in $names; do
  tip=$(git rev-parse "refs/remotes/origin/pr-assets/$name")
  GIT_INDEX_FILE=$index git read-tree --prefix="$name/" "$tip"
  parents+=" -p $tip"
  leases+=" --force-with-lease=refs/heads/pr-assets/$name:$tip"
  deletes+=" :refs/heads/pr-assets/$name"
done
tree=$(GIT_INDEX_FILE=$index git write-tree)
commit=$(git commit-tree "$tree" $parents -m "chore: collect PR images on one branch")
git push --quiet origin "+$commit:refs/heads/pr-assets-tmp"
git push --quiet --atomic $leases origin $deletes
git push --quiet origin "$commit:refs/heads/pr-assets"
git push --quiet origin :refs/heads/pr-assets-tmp
git fetch --quiet --prune origin
echo "pr-assets $commit"
EOF
```

Afterwards, fetch one image from each affected PR at its pinned commit to
confirm it still resolves:

```bash
gh api "repos/<owner>/<repo>/contents/<file>?ref=<commit>" -q .size
```

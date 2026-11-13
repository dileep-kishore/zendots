# Compare the old and new skill

A skill edit can read well and still make agents worse. This check runs the
old and new versions on the same tasks in fresh contexts and has a blind
judge score them against criteria fixed before the runs. Use it for edits
that change what an agent does: a new step, rule, gate, threshold, or
description wording. Typo and link fixes skip it.

## 1. Fix the cases and criteria first

Pick 2 to 4 realistic tasks the skill exists for: one the edit targets, one
the edit should leave unchanged, and one edge case if the edit touches one.
Give each task the inputs a real run would have, such as a scratch repo, a
diff, or a draft.

For each task, write 2 to 5 pass/fail criteria the judge can check in the
run's record: a file exists with a named section, a command ran with the
output the answer quotes, a forbidden action did not happen. A criterion
about what the run did, rather than what it said, is settled from its tool
transcript and the files it left, never from its answer. Then reread each one
and ask whether a wrong output could still pass it. Tighten or drop a
criterion that could, because a pass on a weak criterion hides a regression.

Write the cases and criteria to a scratch file before any run.

## 2. Run both versions

Save the old version from Git, then run each task once per version. A
candidate that can tell which version it has is no longer blind, so the
copies get random neutral names and the map stays outside both:

```bash
dir=$(mktemp -d)
read -r old new < <(printf 's1 s2\ns2 s1\n' | sed -n "$((RANDOM % 2 + 1))p")
echo "old=$old new=$new" > "$dir.map"
mkdir -p "$dir/s1" "$dir/s2"
git -C ~/zendots archive HEAD:dot_agents/skills/<name> | tar -x -C "$dir/$old"
cp -R ~/.agents/skills/<name>/. "$dir/$new"
# chezmoi source names (executable_log.sh) and modes would give the old copy away.
find "$dir/$old" -depth -name 'executable_*' -exec sh -c \
  'f="${1%/*}/${1##*/executable_}"; mv "$1" "$f" && chmod +x "$f"' _ {} \;
```

Each run is a fresh subagent with no conversation history, given only the
task, its inputs, and the path to one version's `SKILL.md` to follow. Word
the task as a user would; never mention versions, a comparison, or a test. Use
the same model, prompt, and inputs for both versions. Runs that could edit
files work in their own scratch copy. Keep each run's answer, its tool
transcript or command log, and its scratch copy's `git status` and diff as
the run's record.

## 3. Judge blind

A fresh subagent that did not write the edit receives each task's two
run records labelled A and B in random order, with the criteria. Strip
version names and paths that reveal which is which. For every
criterion it returns pass or fail for A and B, quoting the part of the
record that decides it. Unblind only after it returns.

The new version must pass every criterion the old one passed. A criterion
both versions fail is a finding about the skill, not about the edit.

## 4. Tune, then test once more

If the new version loses a criterion, revise and rerun that task, for at
most 3 rounds. After the last revision, write one new task that played no
part in tuning and run both versions on it. Passing only the tuned tasks
shows the edit fits those tasks, nothing more.

## 5. Check selection for a description edit

The runs above hand each agent the skill file, so they cannot show whether
the harness still picks the skill. When an automatic skill's description
changed, start fresh sessions with the new version in the store and give
each a natural request that does not name the skill: two that should load
it and one near miss that should not. Read each session's transcript for
whether the skill loaded. Manual-only skills skip this step.

## 6. Record it

Put one line per task in the commit body: the task, and criteria passed by
old and new (`review a weakened test: old 2/4, new 4/4`). Keep the outputs in
the scratch directory until the commit lands, then delete them.

Claude Code's `skill-creator` plugin has scripted versions of these runs and
description-trigger evaluations; this check works without it.

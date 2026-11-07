---
name: correct
description: Use when the user asks to stop a mistake agents keep repeating in a repository, or types /correct after correcting the same kind of mistake again.
disable-model-invocation: true
---

# Correct

Change the repository so the next agent cannot repeat a mistake the user
keeps correcting. A mistake class counts once it has happened twice. Done
means each class you fix has a guard that fails on a real past instance and
passes on the current code, or a stated reason why only written guidance
can cover it.

Assume the next agent sees only the files it opens, copies the nearest
example, and takes the shortest path that compiles. A change that looks
right from one file should be right for the whole repository.

## 1. Find the classes

Start from the correction the user just made, if any. Then read recent
commits and reverts, review threads, the agent instruction files
(`AGENTS.md`, `CLAUDE.md`, `REVIEW.md`), and code comments that explain a
workaround. Group mistakes by cause, and list each class's instances by
commit, review thread, or message. A class with one instance waits for a
second.

## 2. Pick the highest level that works

1. **Structure.** Give each piece of state one owner and each task one
   supported way. Hide internals so the wrong import fails. Replace
   hand-synced lists with one source of truth. Delete the old way and dead
   code an agent would copy.
2. **Types.** Make the bad state impossible to write.
3. **A lint or CI check** whose error names the file, type, or function to
   use instead. When the pattern is already common, fail only on new
   instances.
4. **A behaviour test**, within the repository's test policy. Fix or delete
   a test that still passes when the behaviour it checks breaks.
5. **Written guidance**, last, and only for judgment calls nothing can
   check. Nothing fails when an agent skips it.

For each class, say why the levels above the one you picked did not work.

## 3. Fix and prove

One commit per class, most frequent class first. Prove each new guard
against a real past instance: in a scratch worktree, check out or
reconstruct the mistake, run the guard and quote its failure, then run it on
the fixed code and quote the pass. A guard you never saw fail proves
nothing. Run the same command CI runs. An allowed exception
goes on the offending line with its reason.

When the user asked only for a diagnosis, stop after step 2 and report the
proposed guards.

## 4. Keep the rules paired with their guards

In the agent instruction file, pair each rule with what enforces it: a
file, a check name, or `judgment` for written guidance. Follow the file's
existing format. When the user corrects a rule that is already written and
nothing enforces it, that is a repeat: fix it at the highest level in the
same change. Remove a rule once its mistake can no longer happen.

## Output

For each class: its instances, the level picked and why higher levels did
not work, the guard, and its failing-then-passing evidence. Then the classes
left at written guidance, each with its reason, and the classes waiting for
a second instance.

Locally maintained. Adapted from Cursor pstack's
[correct](https://github.com/cursor/plugins/blob/main/pstack/skills/correct/SKILL.md).

---
name: context-reentry
description: Use when a user is juggling multiple projects or concurrent sessions and may return without remembering the prior scrollback.
---

# Context Re-entry

Assume the user remembers nothing from the scrollback. Write every user-facing message for cold re-entry.

1. **Open with a recap.** Before any summary, decision point, or question, give 2–3 plain sentences explaining what was being worked on, why, and where it stands now.
2. **Use plain language.** Do not rely on invented codenames, abbreviations, or callbacks such as “the earlier fix” or “option B from before.” Restate the subject in place every time.
3. **Make questions self-contained.** Include the background, options, tradeoffs, and recommendation needed to answer without scrolling back.
4. **Ask one question at a time.** If several decisions or next steps are waiting, state how many, present only the first, and wait before raising the next.
5. **Anchor the work.** Name the project, branch, and pull request when reporting status so similar sessions cannot be confused.
6. **End with the next action.** Close long updates with the single thing waiting on the user, or say explicitly that nothing is waiting.

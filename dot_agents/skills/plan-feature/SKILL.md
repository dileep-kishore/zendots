---
name: plan-feature
description: Use when a request asks to build, brainstorm, or design a feature that spans several files and leaves major decisions open, asks for a spec or implementation plan, or asks to turn the conversation into a spec. Not for an obvious change to one or two files.
---

# Plan a feature

The user steers at the start, then leaves the build to run unattended. They
answer one batch of questions and read one summary page, then approve once. A
decision you could have asked now but raise mid-build costs them a session.

Size the work first. The paperwork grows with it:

| Size | Before code | After the build |
|---|---|---|
| Small: an obvious change to one or two files, no major decision open | Nothing; say you skipped the spec | The usual check and review |
| Feature: fits one session | Questions, `spec.md`, `spec-intent.md`, `summary.html`; a design review when section 3 calls it risky | Done checks, review against the spec, page refreshed |
| Large: several sessions or PRs | The same, plus `plan.md` | The same, per PR |

Feature files go in `docs/drafts/<date>-<feature>/`, which the global gitignore
covers, unless the project's instructions name another ignored folder. A
feature already filed under `docs/superpowers/` may stay there. Before writing
each file there, check that git ignores it and does not track it
(`git check-ignore -q <path>`, `git ls-files --error-unmatch <path>` fails).
When it is not ignored, add the folder's top directory (`/docs/drafts/` by
default) to the file `git rev-parse --git-path info/exclude` names and check
again; a path a tracked `.gitignore` unignores stays exposed, so write nothing
there and ask where to put it.

When the user asks to turn the conversation into a spec, skip the questions in
section 2 and fill the intent file from the conversation, each decision beside
the quote that settled it. When the user asks only for a spec or a plan, stop
after section 5 without asking to build.

## 1. Read before asking

Read the code, docs, project instructions, and existing specs the request
touches, and answer from them whatever they answer. A fact a short run can
show, such as how a library or flag behaves or how long a step takes, is not a
question: probe it in a scratch directory within 20 minutes, cite the result,
and delete the probe. When a probe or a quick prototype could change your
recommendation on a question, run it first and put its result in that
question's options. In a repo linked to Linear, run `linear-track` step 2
here: what related issues settle is read, not asked.

## 2. Ask once, up front

List the consequential decisions this request leaves open, including the ones
the build will predictably hit later. Check each of these and ask only when it
has two sound options here:

- what done looks like, and how it is checked;
- scope and the first slice;
- budget in money, runtime, model calls, or rounds;
- what to do when a target, cap, or budget runs out before success;
- where the work ends, only when the global default (branch only, or a PR when
  the user asked to ship) does not fit;
- taste calls the user wants to make, such as visual style or naming;
- the Linear project, when the repo has no link yet (`linear-track` step 1);
- which Linear issue tracks the work, when the related-issue search or a
  GitHub issue offers a choice (`linear-track` step 2).

Ask them all in one round: one question-tool call when the tool holds them all,
otherwise one numbered message, and stop. Each question is multiple choice with
your recommendation first and labeled as recommended, a one-line reason for
it, and enough background to answer without the scrollback. Facts you need
from the user, such as a path or a login, follow the questions as a separate
list. Before sending, check that every decision the spec will need is asked or
settled; ask a second round only when an answer or the design review opens a
new major decision. If the user says to proceed without questions, decide the
routine choices, record them as assumptions, and still ask the major ones.

## 3. Write the spec

Write `spec-intent.md` beside the spec, starting as answers arrive: each user
message verbatim beside the question and options it answers, each
consequential default never discussed, and an amendment log.

`spec.md` is sized to the change. It records the goal, each decision and its
answer, assumptions, what is out of scope, and 3 to 6 done checks. Each done
check is an observable result with the command that shows it: a known answer,
a reference comparison, a property, a run on real inputs (for an app, from
empty state in the client the user uses), or degenerate input. Link the intent
file and the summary page by path, and copy the build rules from section 6
into the spec so a later session follows them without this skill.

Every consequential choice the spec makes that the user did not answer goes in
the intent file and on the summary page as an undiscussed default: a threshold
or tolerance in a done check, a sampling rule, a cap, and any routine change
to an answered decision made during self-review or design review. A review
finding that needs a major decision, including a major change to an answered
one, is asked the way section 2 asks; the intent file keeps the original quote
and logs the new answer. Check the spec against the intent file: every answer
is reflected, nothing contradicts, and every done check can run.

Run `independent-review` on the spec as a design review only when the work is
risky: several PRs, deleting or migrating stored data, authentication or
permissions, or a public interface or config key other people use. Fix what
its verifier confirms. Otherwise skip it and say so on the page; the final
review checks the build against the spec.

## 4. Plan large work

Write `plan.md` only for work across several sessions or PRs, or when the user
asks for a plan. List the PRs in landing order with what blocks each, the
files each may touch, and its done check. A plan holds no code and no
task-by-task steps; keep your own task list while you build. A PR without a
new test names the existing check that covers it.

## 5. Get approval

Write `summary.html` in `html-artifact`'s feature-page format: an overview, the
key decisions with the undiscussed defaults first, one design diagram, the
done checks, and what is out of scope, plus the plan's order when there is a
plan. Its approval item names where the work ends (a branch, a PR, or a
merge) and whether that came from the user or the default. Present only the key decisions and link the page. Write no code until
the user approves. When the request asked for the build, approval covers it
through the end state the user chose in section 2. At the approval, create or
adopt the Linear issue as `linear-track` step 3 says, unless the user chose to
leave Linear out.

## 6. Build rules (copy into the spec)

- Make a routine change to the spec when planning or the build hits a
  problem, and log it in one line in the intent file's amendment log. A new
  major decision follows the mid-run rule in the global instructions.
- Leave the user's quoted words as written. Correcting a done check or
  excluding something the user asked for keeps the original and the evidence.
- Run the done checks before the final review, and rerun the affected ones
  after its fixes. The final review takes the spec's decisions and done
  checks as its requirements.
- Keep the Linear issue's status and summary current with `linear-track`
  step 4, when the work has an issue.
- Put each decision a later maintainer needs in the PR description, or, when
  the work lands without a PR, in the commit message body or a tracked
  decision record. The spec folder is ignored and disposable after merge.
- Before cleanup, refresh the summary page the spec links with the
  undiscussed defaults, each done check's result and revision, and every
  change to the user's requests or a done check.

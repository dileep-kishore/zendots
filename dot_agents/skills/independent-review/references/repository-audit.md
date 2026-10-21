# Repository and folder audits

Use this target when the user asks to audit a repository, package, or folder,
including requests to review the whole codebase. Ordinary change reviews keep
their diff-based scope and introduced-defect requirement. The single, dual, and
deep reviewer choices and the independent verifier workflow remain the same.
Apply the depth criteria to the audited scope and its risks rather than a
changed-line count.

## Pin the current target

Record the checkout, HEAD when present, and exact audited paths. Use the current
working tree, including existing code and non-ignored untracked files in those
paths. A clean tree is a valid target; an unborn repository can be audited too.
Do not substitute the last commit or require a diff. For an explicitly requested
committed revision, read that revision rather than mixing in working changes.

List scoped files before launch. Follow the repository's ignore rules for
generated output, dependencies and caches unless the user includes them.
Record exclusions and distinguish first-party code from third-party material.
Keep a scope manifest and content hashes outside the checkout, then compare
the inventory and hashes before triage. Pin relevant configuration and outside
callers used as evidence too. Hash secret-bearing files instead of copying
their contents into briefs or reports.

## Brief the finder

Use the shared review brief. State `Repository audit` in its intent, and put the
named paths, manifest, snapshot and read-only inspection commands in its scope.
Fill the command slots with file inventory and inspection commands; a diff
slot does not require a diff. State that existing defects in the named scope
are eligible. Give the verifier the same target kind and snapshot.

Map entry points and main data flows before selecting where to go deep. Read
the README, build/deploy configuration, tests and code bounds to establish
contracts, expected load and trust boundaries. Prioritize paths where failures lose data,
expose access, produce wrong results or exhaust resources. Trace callers,
configuration, string references and dynamic loading before declaring code
unreachable or unused. A documented shortcut remains reviewable against actual
requirements and load.

Outside callers can prove a scoped defect; they do not expand the finding
scope. Keep unrelated outside defects under coverage. Identify what was read,
sampled, excluded or not exercised. A map or risk-based sample does not prove
every file or path was checked.

## Report

Use the shared severity, concrete-trigger and independent-verification rules.
Existing defects need no introduced-by-change attribution. A clean diff does
not justify a healthy verdict. Report the audited purpose and expected load,
confirmed and unresolved findings, smallest fixes, and coverage gaps. Call
coverage incomplete when a material area could not be assessed; use a healthy
verdict only within the stated checked scope. Do not fix code without the
user's authorization.

---
name: verify-this
description: Use when a fix, optimization, or behavior claim needs fresh evidence, or the user asks to verify, prove, or disprove a claim.
---

# Verify this

Prove or disprove one specific claim with evidence someone could rerun. A
vague claim ("the code is cleaner") first needs an observable acceptance
condition. This is for a claim in doubt; evidence another workflow already
produced for the same state counts and need not be regathered.

## Workflow

1. State the claim, its conditions, and the expected result or threshold.
2. Decide what kind of claim it is:
   - **Acceptance:** new behavior meets a stated requirement. The requirement
     is the reference; exercise the real behavior. No old state is needed.
   - **Comparative:** a bug is fixed, a regression gone, or something is
     faster or smaller. Capture a baseline (the old commit, a failing repro,
     a prior measurement), then the treatment under the same command, data,
     warm-up, and environment. A fix stays comparative even if the new
     version passes its checks.
3. Pick the smallest safe surface that could disprove the claim, reusing the
   project's verification recipes and commands. Record the revision or
   working state checked.
4. Observe the result: output, side effects, exit status, or a measured
   value. A build, a mock, or an internal state setter proves only what it
   actually exercises. If a check fails for an incidental reason (a port in
   use, a cold cache), fix the setup and rerun rather than reporting noise.
5. Return one verdict for the claim as stated. If the evidence supports a
   narrower claim, name that separately.

## Evidence

Focused tests or repros, CLI transcripts, UI action-and-result captures, API
responses, timings, or profiles, using tools the project already has. Keep
artifacts worth preserving in a private `mktemp -d` directory and report the
path; ask before storing sensitive payloads on disk.

## Verdicts

- `VERIFIED`: acceptance evidence meets the requirement, or baseline and
  treatment show the comparative claim, with no material confound.
- `NOT VERIFIED`: a valid check contradicts the claim or misses its threshold.
- `INCONCLUSIVE`: required evidence is missing, a comparative claim has no
  baseline, the measurement failed, or a confound invalidates it. An
  acceptance claim needs no baseline.

A clear `NOT VERIFIED` is useful; report it plainly.

```text
VERIFIED | NOT VERIFIED | INCONCLUSIVE
Claim: <claim and acceptance condition>
Type: acceptance | comparative
Checked: <revision or working state, relevant environment>
Evidence: <command or action, expected, observed, artifact path>
Comparison: <baseline, treatment, delta; omit for acceptance>
Limits: <what stayed unverified, confounds; or none>
```

Locally maintained. Adapted from Cursor's
[verify-this](https://github.com/cursor/plugins/blob/main/cursor-team-kit/skills/verify-this/SKILL.md).

---
name: verify-this
description: Use when a fix, optimization, or behavior change is claimed to work and needs fresh evidence, or when the user says "verify this", "prove it", "did this fix it", or "show me the evidence". Restates the claim falsifiably, captures baseline and treatment, and returns VERIFIED, NOT VERIFIED, or INCONCLUSIVE.
---

# Verify this

Verification is not a recap. It proves or disproves one specific claim with
repeatable evidence. A vague claim ("the code is cleaner") cannot be
verified; ask for a measurable one first.

## Workflow

1. Restate the claim in falsifiable form: condition, metric, threshold.
2. Pick the smallest local surface that can disprove it.
3. Capture a **baseline** from the old state: merge base, parent commit,
   failing branch, or the current broken repro. Without a baseline the
   result is INCONCLUSIVE, not VERIFIED.
4. Capture the **treatment** from the changed state with the same command,
   data, warm-up, and environment.
5. Compare raw artifacts: numbers, terminal transcripts, HTTP responses,
   screenshots, profiles, test output.
6. Return exactly one verdict.

## Surfaces

- Code behavior: a focused test or a minimal repro script.
- CLI/TUI behavior: a terminal transcript of the real invocation.
- UI behavior: screenshots, accessibility snapshots, or browser traces
  through whatever driver the project already has.
- API behavior: local request and response diff.
- Performance: same-machine baseline and treatment timings or profiles.
- Memory: heap snapshots before and after the suspected operation.

## Artifacts

When evidence is worth keeping, write it under a private directory from
`mktemp -d` (`claim.md`, `baseline/`, `treatment/`, `diff/`, `verdict.md`)
and report the path. If artifacts would contain sensitive code, prompts,
screenshots, or HTTP bodies, keep only the minimal inline evidence unless the
user agrees to disk storage.

## Verdict rules

- `VERIFIED`: baseline and treatment differ in the predicted direction, by
  the claimed threshold, with no obvious confound.
- `NOT VERIFIED`: unchanged, moved the wrong way, or missed the threshold.
- `INCONCLUSIVE`: no valid baseline, noisy signal, failed measurement, or an
  environment difference that invalidates the comparison.

## Output

```text
VERIFIED | NOT VERIFIED | INCONCLUSIVE
Claim: <falsifiable claim>

Evidence:
<metric/artifact>: baseline=<...>, treatment=<...>, delta=<...>, threshold=<...>

Reasoning:
<one tight paragraph naming the evidence and any confounds>
```

Do not soften a negative result. A clear `NOT VERIFIED` is useful.

Locally maintained. Adapted from Cursor's
[verify-this](https://github.com/cursor/plugins/blob/main/cursor-team-kit/skills/verify-this/SKILL.md).

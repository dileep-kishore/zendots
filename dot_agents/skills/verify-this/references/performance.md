# Performance claims

Read this when the claim is a number: faster, slower, smaller, fewer
queries, or a regression. Answer each question with evidence from a run,
not from reading the code.

## Before running

- Write the sentence you expect to report, with its unit and dataset:
  "export is 30% faster at p50 on the 60k-row fixture". The checks below
  test that sentence.
- Read the measurement script and note what it times, counts, and skips.
- Check machine load (`uptime`, core count). If something else is running
  and you cannot stop it, alternate the sides so both see the same noise,
  and say so in Limits.

## Questions

1. **Did the work happen?** Confirm the timed region did the work: the
   request reached the server, rows were written, results were consumed.
   Lazy code, unawaited promises, and timeouts produce numbers for work that
   never ran.
2. **Was the output right?** Count errors and non-success responses, and
   check outputs are correct, not only present. Failures are often fast.
3. **Were both sides run the same way?** Same build type, flags, data,
   versions, and cache warmth, set as production runs them. A side on
   default settings compares configurations, not code.
4. **Does it reproduce?** At least 5 runs per side, alternating A, B, A, B.
   Report the median and range. A difference smaller than the run-to-run
   range is no measurable difference.
5. **Is it possible?** Check the result against limits: bandwidth, cores,
   and the share of time the changed part took. Removing a part that took
   10% of the run can make it at most about 11% faster. A result past a
   limit measured a cache, a no-op, or a bug.
6. **What is the limiter?** Profile in a separate run you do not report,
   because profilers slow the work. If the change did not move the number,
   the limiter explains why.
7. **Does it matter end to end?** Next to a micro result, measure the path
   a user waits on, and report the micro result as a share of it.

A quick ballpark the user asked for can be one run per side; still answer
questions 1 and 2, and say it was one run. A choice between options is
never a ballpark.

## Verdict

Comparison gives the number with its unit, run count, median, and range:
`p50 41 ms -> 33 ms, median of 7 runs per side, range 32-35 ms after`.
Return INCONCLUSIVE when questions 1 or 2 went unanswered, a side ran
untuned, or the difference sits inside the run-to-run range.

Adapted from Cursor pstack's
[benchmark-checklist](https://github.com/cursor/plugins/blob/main/pstack/skills/benchmark-checklist/SKILL.md).

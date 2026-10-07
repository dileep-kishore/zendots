# Deep review lenses

Each deep-review finder gets the full brief plus one lens as its `{LENS}`. A
lens sets where the finder spends its depth; it still reports any material
issue it notices outside the lens.

1. **Contracts and callers.** Changed signatures, return values, defaults,
   invariants, config keys, schemas, serialized formats, and shared
   constants. Enumerate every caller and reader, every enum variant and
   dispatch branch. Removed or weakened checks and their `git log -S`
   history. Compatibility with stored data and other deployed versions.
2. **State, ordering, and concurrency.** Shared mutable state, caches and
   their invalidation, ordering assumptions, races and re-entrancy, retries,
   idempotency, partial failure and rollback, resource lifetime and cleanup,
   transactions and migrations.
3. **Error paths and silent failure.** Swallowed or over-broad catches,
   fallbacks and defaults that hide failure, optional chaining or null
   coalescing over a value that must exist, async work not awaited or
   returned, timeouts, empty and degraded dependency behaviour, and logs that
   are the only signal of a failure.
4. **Security and trust boundaries.** Follow the `security-review` skill's
   tracing for every boundary the change touches: entry point to sink,
   object-level authorization, secrets, injection, SSRF, unsafe
   deserialization.
5. **Intent and verification.** Requirements missing, partial, or
   implemented wrongly; behaviour added that was not asked for; tests that do
   not exercise the changed behaviour or that assert on mocks; docs, config,
   and migration steps the change leaves stale.

## Assignment

- Use every lens the change can reach. Skip a lens only when the diff gives
  it nothing to examine (no trust boundary, no shared state), and list the
  skipped lens under coverage.
- Alternate vendors across lenses, starting with the vendor that did not
  write the change. For lens 1 and any lens the user names as the main risk,
  run one finder from each vendor.
- For a diff over roughly 2,000 changed lines, split the heaviest lenses by
  area of the concern map as well, up to about eight finders in total.

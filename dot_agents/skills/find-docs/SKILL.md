---
name: find-docs
description: >-
  Looks up current documentation for a named library, framework, SDK, CLI, or
  cloud service through the Context7 CLI. Use for API signatures, configuration
  options, version migrations, setup, and library-specific debugging, where
  training data may be stale, including inside refactoring or debugging work.
  Not for tasks that need no library-specific docs, such as general
  programming concepts.
---

# Documentation lookup

Retrieve current documentation and code examples with the Context7 CLI, run
through `npx ctx7@latest` with no global install or upgrade step.

Locally maintained in zendots and absent from the skills lockfile; rerunning
Context7 setup may overwrite it, so preserve these changes.

## Workflow

Resolve the library name to an ID, then query docs with that ID. Skip the
first step when the user already gave an ID such as `/org/project` or
`/org/project/version`; `docs` fails without a valid one.

```bash
npx ctx7@latest library <name> "<what the user is trying to do>"
npx ctx7@latest docs <libraryId> "<what the user is trying to do>"
```

Pass a query to both (`docs` requires it); it drives ranking. Use the user's actual
question ("React useEffect cleanup with async operations"), not a keyword
("hooks"). Keep secrets, credentials, personal data, and proprietary code out
of queries.

Stay within three calls per question; each spends Context7 quota. If three
attempts do not find it, use the best result and say so.

## Choosing a match

Search by the official name and punctuation ("Next.js", "Three.js"). Prefer
an exact name match, then description fit, snippet count, source reputation,
and benchmark score. When several fit, say so and proceed with the best; ask
only when the request itself is ambiguous.

When the user names a version, use the matching `/org/project/version` ID
from the `library` output, and disclose any mismatch when that version is not
indexed.

## Failures

Works without authentication; `CONTEXT7_API_KEY` or `npx ctx7@latest login`
raises rate limits. On a quota error, tell the user the quota is exhausted
and suggest `npx ctx7@latest login`. When Context7 is unavailable or three
calls find nothing relevant, read the official documentation site directly
and say so. Answer from training knowledge only when no current docs are
reachable, and mark that answer as possibly outdated.

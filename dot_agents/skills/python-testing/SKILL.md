---
name: python-testing
description: Python testing with pytest. Use when writing or changing Python tests, designing a test suite, or judging coverage.
---

# Python Testing

pytest idioms (fixtures, parametrize, markers, `tmp_path`, `unittest.mock`,
pytest-asyncio) are assumed. This skill records the stance.

- Prefer TDD when it helps establish the intended behavior, especially for
  bug fixes. It is a default, not a gate: follow the task and repository
  requirements and scale verification to the change.
- Tests are lasting maintenance. Add or update them where they protect
  behavior or a likely regression. For reversible, low-impact changes prefer
  a targeted smoke check over tests that mirror the implementation or exist
  only to raise coverage.
- Coverage identifies gaps; it does not establish correctness. Do not impose
  a percentage or add a coverage gate unless requested or required. Measure
  with `pytest --cov=<package> --cov-report=term-missing`.
- Run pytest through the project's environment (`uv run pytest` in uv
  projects). Keep slow and integration tests behind markers so
  the default run stays fast.

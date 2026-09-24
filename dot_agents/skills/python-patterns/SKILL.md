---
name: python-patterns
description: Python conventions for this user's projects (uv, Ruff, ty, Pydantic, NumPy docstrings, 3.10+ typing). Use when writing, reviewing, or setting up Python code.
---

# Python Conventions

Idiomatic Python is assumed. This skill records only the choices that differ
from generic defaults.

## Tooling

Follow the tooling a project already uses. Where it has none, or for a new
project:

- Environments and dependencies: `uv` (`uv sync`, `uv add`, `uv run`), or
  `pixi` where conda packages are needed.
- Formatting, import sorting, and linting: Ruff (`ruff format .`,
  `ruff check .`).
- Type checking: `ty check`.
- Tests: pytest (see the `python-testing` skill).

## Code

- Target Python 3.10 or newer unless the project supports older versions.
  Write `X | None`, `list[str]`, `dict[str, Any]`; do not import `Optional`,
  `List`, `Dict`, or `Union`.
- Type-hint every public signature.
- Validate data at boundaries (config, request bodies, files) with Pydantic
  models. Use `@dataclass` only for plain internal containers that need no
  validation.
- NumPy-style docstrings on public modules, classes, and functions.

## pyproject.toml shape

```toml
[project]
name = "mypackage"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["pydantic>=2"]

[dependency-groups]
dev = ["pytest", "pytest-cov", "ruff", "ty"]

[tool.ruff]
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "D"]

[tool.ruff.lint.pydocstyle]
convention = "numpy"
```

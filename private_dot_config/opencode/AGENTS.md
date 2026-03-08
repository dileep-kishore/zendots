# Global Rules

## Critical Instructions

- When the user requests code examples, setup or configuration steps, or library/API documentation, use the context7 MCP or search the web for current docs.
- Do not over-engineer. Only make changes directly requested or clearly necessary. Prefer simple, minimal solutions.
- Don't add error handling for impossible scenarios. Don't create abstractions for one-time operations.

## Package Managers

- Python: uv (preferred), pixi (for environments and packages)
- JavaScript/TypeScript: Bun (runtime and package manager)
- System packages: Paru, Homebrew
- Do not use pip, conda, apt, npm, or yarn unless explicitly asked.

## Code Style

### Python

- NumPy-style docstrings. Include only relevant sections.
- Type hints preferred.
- Prefer httpx over requests for HTTP.
- Use pydantic for data validation and models.
- Use ruff for linting and formatting.
- Use ty for type checking.
- Prefer specific exceptions over bare `except`. Use `contextlib` for resource management.

### TypeScript / JavaScript

- Use interfaces for object shapes, types for everything else.
- Strict TypeScript by default.

### General

- Prefer concise, readable code over defensive/verbose patterns.

## Testing Philosophy

Skip hypothetical edge cases and exhaustive coverage.
Tests document what should work and what broke before — not safety nets for every possibility.

## Git

- Use conventional commit messages (feat:, fix:, chore:, refactor:, docs:, etc.)
- Keep commits atomic and focused.

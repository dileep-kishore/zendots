# Global OpenCode Rules

## Critical Instructions

- When the user requests code examples, setup or configuration steps, or library/API documentation, use the context7 mcp or search the web for current docs.

## Testing Philosophy

**Skip:** Hypothetical edge cases and exhaustive coverage that bloat context windows.

Tests are living documentation of what should work and what broke before, not comprehensive safety nets for every possibility.

## Python Docstrings

Always use NumPy-style docstrings for Python code. You don't need to include all sections if they aren't relevant.
Use uv for python environment and package management

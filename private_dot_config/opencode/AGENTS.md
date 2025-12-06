# Global OpenCode Rules

## Critical Instructions

- **ALWAYS write over the source file you're editing.** Don't make "\_enhanced", "\_fixed", "\_updated", or "\_v2" versions.
- Don't make "dashboards" or figures with a lot of plots in one image file. It's hard for AIs to figure out what all is going on.
- When the user requests code examples, setup or configuration steps, or library/API documentation, search the web for current docs.

## Code Search

You are operating in an environment where `ast-grep` is installed. For any code search that requires understanding of syntax or code structure, you should default to using `ast-grep --lang [language] -p '<pattern>'`. Adjust the `--lang` flag as needed for the specific programming language.

## Testing Philosophy

Write two kinds of tests:

1. **Spec tests** - Document intended feature behavior (what the feature should do)
2. **Regression tests** - Reproduce and prevent actual bugs that occurred

**Skip:** Hypothetical edge cases and exhaustive coverage that bloat context windows.

Tests are living documentation of what should work and what broke before, not comprehensive safety nets for every possibility.

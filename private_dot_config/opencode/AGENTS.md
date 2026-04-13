# Global Rules

## Critical Instructions

- When the user requests code examples, setup or configuration steps, or library/API documentation, use the `ctx7` CLI via the `find-docs` skill or search the web for current docs.
- When the user asks for real-world implementation examples, API usage patterns, or framework conventions, use `gh_grep` to search GitHub code before guessing.
- Prefer the built-in file/code tools for small changes. On larger, strongly structured codebases, use `serena` for symbol-aware navigation and edits.
- Never use `serena` to read skill files outside the active repository (for example under `~/.codex` or `~/.config/opencode`); use a general file reader instead.
- Do not over-engineer. Only make changes directly requested or clearly necessary. Prefer simple, minimal solutions.
- Don't add error handling for impossible scenarios. Don't create abstractions for one-time operations.

## General Principles

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:

- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

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
- In the description, explain the "why" and "what" of the change, not just "how".
- Try to limit title to 50 characters and wrap description body at 72 characters.

<!-- context7 -->

Use the `ctx7` CLI to fetch current documentation whenever the user asks about a library, framework, SDK, API, CLI tool, or cloud service -- even well-known ones like React, Next.js, Prisma, Express, Tailwind, Django, or Spring Boot. This includes API syntax, configuration, version migration, library-specific debugging, setup instructions, and CLI tool usage. Use even when you think you know the answer -- your training data may not reflect recent changes. Prefer this over web search for library docs.

Do not use for: refactoring, writing scripts from scratch, debugging business logic, code review, or general programming concepts.

## Steps

1. Resolve library: `npx ctx7@latest library <name> "<user's question>"` — use the official library name with proper punctuation (e.g., "Next.js" not "nextjs", "Customer.io" not "customerio", "Three.js" not "threejs")
2. Pick the best match (ID format: `/org/project`) by: exact name match, description relevance, code snippet count, source reputation (High/Medium preferred), and benchmark score (higher is better). If results don't look right, try alternate names or queries (e.g., "next.js" not "nextjs", or rephrase the question)
3. Fetch docs: `npx ctx7@latest docs <libraryId> "<user's question>"`
4. Answer using the fetched documentation

You MUST call `library` first to get a valid ID unless the user provides one directly in `/org/project` format. Use the user's full question as the query -- specific and detailed queries return better results than vague single words. Do not run more than 3 commands per question. Do not include sensitive information (API keys, passwords, credentials) in queries.

For version-specific docs, use `/org/project/version` from the `library` output (e.g., `/vercel/next.js/v14.3.0`).

If a command fails with a quota error, inform the user and suggest `npx ctx7@latest login` or setting `CONTEXT7_API_KEY` env var for higher limits. Do not silently fall back to training data.

<!-- context7 -->

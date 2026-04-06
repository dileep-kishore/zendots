# Global Rules

## Critical Instructions

- When the user requests code examples, setup or configuration steps, or library/API documentation, use the `ctx7` CLI via the `find-docs` skill or search the web for current docs.
- When the user asks for real-world implementation examples, API usage patterns, or framework conventions, use `gh_grep` to search GitHub code before guessing.
- Prefer the built-in file/code tools for small changes. On larger, strongly structured codebases, use `serena` for symbol-aware navigation and edits.
- Never use `serena` to read skill files outside the active repository (for example under `~/.codex` or `~/.config/opencode`); use a general file reader instead.
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

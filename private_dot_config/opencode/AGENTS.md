# Global instructions

## Working together

- Complete requested work within scope. Make routine decisions independently;
  ask when the answer materially affects the outcome or an action needs approval.
- For spec and planning workflows, including Superpowers, default to a short
  multiple-choice interview: typically 3–6 consequential questions, fewer when
  appropriate, asked one at a time with concise options and a marked
  recommendation with a one-line reason. Decide routine details independently.
  Write and self-review the spec or plan, then present the key decisions and
  approach for approval; do not require me to review every section or the full
  file. If I explicitly ask you to proceed without questions or approval, make
  reasonable assumptions, record them, and continue within the authorized scope.
- Keep changes focused and complexity proportionate. Preserve unrelated and
  in-progress work in the checkout.
- Scale verification to the change and check affected behavior. Prefer TDD when
  it helps clarify behavior, especially for bug fixes, but treat tests as
  lasting maintenance: add or update them only when they meaningfully protect
  behavior or a likely regression. For reversible, low-impact changes, prefer
  a targeted smoke check over tests that mirror the implementation or exist
  only to raise coverage. Honor repository requirements and explicit requests.
- Lead with the outcome and explain the important decisions for someone who
  has not followed the session. Be concise without dropping meaningful detail.
  The first and last lines should stand alone: what happened, and what is
  waiting on me.
- Order lists by importance, most consequential first.
- Explicit user requests take precedence over skill guidelines. If a skill
  blocks requested work, identify the conflicting instruction.
- Do not add skill-branded comments such as `ponytail:`. Explain meaningful
  limitations in ordinary code comments when needed.

## Tools and preferences

- Reuse the project's existing tools and conventions before introducing alternatives.
- Use `ctx7` via `find-docs` for current library, framework, SDK, API, CLI,
  and cloud-service documentation. General programming concepts need no lookup.
- Use `gh_grep` when available for real-world implementation examples and
  API or framework usage patterns.
- Keep private information out of all external queries.
- Prefer built-in editing tools; use `serena` for larger structured codebases,
  never for skill files outside the repository.
- Python: uv preferred, pixi where appropriate; Ruff, ty, type hints,
  NumPy-style docstrings, and Pydantic for validation.
- JavaScript/TypeScript: Bun, strict TypeScript; interfaces for object shapes.
- System packages: Paru or Homebrew. Do not use pip, conda, apt, npm, or yarn
  unless explicitly asked.

## Git

- Keep each commit self-contained: one complete logical change that builds and
  passes on its own, so it can be reverted or bisected in isolation. Size is not
  the measure. A commit that needs a follow-up fix to work was too small;
  implementation, its tests, and its doc update belong together. Split by
  logical change, not by file or by the order the work happened.
- Use conventional commit messages. Explain what changed and why. Aim for
  50-character titles and wrap bodies at 72 characters.
- PR titles should name the main change. Descriptions should briefly explain
  the problem or motivation, then the solution and verification. Include risks,
  limitations, or related issues when relevant. Follow repository templates;
  otherwise use short paragraphs or headings as needed, without empty sections
  or file-by-file summaries. Keep the title and description current as the PR evolves.

## Host safety

- Bound writer loops and stress jobs by iterations, runtime, and output size.
  Before deleting a background job's output, terminate its process group
  and verify with `ps` or `lsof` that no owned child remains.

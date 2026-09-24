---
name: coding-standards
description: TypeScript and JavaScript conventions for this user's projects (Bun, strict TypeScript, interfaces for object shapes). Use when writing, reviewing, or setting up TS/JS code.
---

# TypeScript / JavaScript Conventions

Idiomatic TypeScript, React, and Node are assumed. This skill records only
the choices that differ from generic defaults.

- Follow the package manager and test runner the project already uses
  (npm, pnpm, yarn, or Bun). In a new project, use Bun for all of them
  (`bun install`, `bun run`, `bun test`, `bunx`).
- `"strict": true` in tsconfig. No `any` in new code; take `unknown` and
  narrow.
- Declare object shapes with `interface`; reserve `type` for unions,
  intersections, and mapped types.
- Comments explain why, not what. JSDoc on exported functions.

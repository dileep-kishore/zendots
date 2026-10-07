---
name: security-review
description: Use when code adds or changes authentication, authorization, user input handling, file uploads, secrets, API endpoints, payments, or other sensitive data flows.
---

# Security review

Find the security problems a change actually introduces, each backed by a
reachable path. Done means every trust boundary the change touches has been
traced end to end, and each finding names the entry point, the path, and the
fix. A checklist ticked without tracing is not a review.

## 1. Map what the change exposes

Read the change and the code around it. List where untrusted data enters
(request bodies, headers, query strings, uploads, webhooks, queue messages,
CLI args, environment a user controls), where it ends up (queries, shell
commands, file paths, templates and HTML, redirects, deserializers, outbound
requests, logs), and which identities and permissions the code acts under.
Look beyond the diff: middleware, route config, framework defaults, and the
callers of anything that changed.

## 2. Trace each path

For every entry-to-sink path, check what stands between them, and whether it
holds on every route, not only the one in the diff:

- **Injection:** SQL, shell, template, path traversal, header, and log
  injection. Parameterized or structurally escaped, or concatenated?
- **Access control:** authentication on every entry point; authorization on
  the specific object (can user A fetch user B's record by changing an ID?);
  checks on the server, not only in the UI.
- **Output:** XSS through unescaped rendering or raw-HTML sinks; open
  redirects; errors or logs that leak secrets, tokens, or personal data.
- **Requests the server makes:** SSRF through user-supplied URLs; CSRF on
  cookie-authenticated state changes.
- **Secrets:** hardcoded keys, secrets committed to history or config,
  secrets sent to the client or into logs.
- **Abuse:** missing rate or size limits on login, signup, uploads, and
  expensive operations; unrestricted upload types and sizes.
- **Crypto and sessions:** homegrown crypto, weak randomness for tokens,
  tokens that never expire or survive logout, JWTs accepted without
  signature and audience checks.
- **Dependencies:** new packages or version bumps with known advisories, via
  the project's own audit tool (`npm audit`, `pip-audit`, `cargo audit`).

Use the project's existing validation, auth, and query layers as the
reference: a route that skips the layer every sibling uses is a finding.

## 3. Confirm before reporting

Show each finding is reachable: the entry point, the path through the code,
and what an attacker controls. Where it is safe and local, prove it with a
request, a test, or a repro. Drop what you cannot connect to a reachable path,
or list it separately as unconfirmed with what would settle it.

Models over-report security issues in predictable places. Unless the code or
the repository's `REVIEW.md` says otherwise, these are not findings:

- Values from environment variables, CLI flags, or deployment config: the
  operator controls them, not an attacker.
- Missing authorization in client-side code; the server is the boundary.
- XSS in React, Vue, or Angular templates without a raw-HTML sink
  (`dangerouslySetInnerHTML`, `v-html`, `bypassSecurityTrust*`).
- Guessing attacks on UUIDs or other unguessable random identifiers.
- User content placed in an LLM prompt, unless the model's output reaches a
  privileged action without checks.
- Memory-safety classes in memory-safe languages outside `unsafe` or FFI code.
- Path or SSRF findings where the path or URL comes only from code or config.

A rule like these never covers a confirmed path: if you traced attacker input
to the sink, report it.

## Output

Findings ordered by impact, each with location, the path from entry to sink,
evidence, and the smallest fix that closes it, preferably by routing through
the project's existing safeguard. Then coverage: the boundaries traced, and
anything that could not be checked, such as deployment config or secrets
outside the repository.

Fix only when fixes were requested. Do not probe systems beyond the local
environment without authorization.

Locally maintained. Rewritten from the ECC `security-review` checklist.

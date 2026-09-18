# Excalidraw generation

Use the bundled exporter. It installs the official Excalidraw package from a
checked-in manifest and `bun.lock`, runs the browser-only export APIs in
headless Chromium, and exits. No MCP or interactive editor setup is required.
Use T3's built-in browser for visual review when working in T3.

## Run

Requires Bun 1.4.0 or newer. Tested with 1.4.0 on Linux x64 and 1.4.2 on
macOS arm64. The first run needs network access to download the locked packages
and Playwright's matching Chromium headless shell. On
Linux, Chromium also needs its usual system libraries; if launch reports a
missing library, resolve that host dependency rather than changing renderers.

```bash
bun run ~/.agents/skills/html-artifact/scripts/excalidraw.ts \
  docs/diagram.json docs/diagram
```

For a smoke check, use `assets/excalidraw-example.json` as the input and a
temporary output prefix. Run from any directory; arguments resolve relative
to the caller's directory. Existing outputs at the prefix are replaced.

The command creates:

- `diagram.light.svg` and `diagram.dark.svg`, with embedded handwriting fonts.
- `diagram.excalidraw`, the editable drawing with the light palette.
- `diagram.images.html`, self-contained image markup. Paste it inside a
  `<figure>` in the current template and add a caption. Do not link to the SVG
  files from the page; the fragment already embeds both images.

Keep the authored `docs/<slug>.<name>.json` and editable `.excalidraw` source.
After pasting the fragment, remove the generated `.light.svg`, `.dark.svg`,
and `.images.html` intermediates unless they are wanted as separate exports.
The command prints the embedded fragment's byte count. The complete HTML page
warns above 1 MB and fails validation above 2 MB, so check the assembled page.

The authored JSON remains the input for regeneration. Manual changes to the
`.excalidraw` output do not update that JSON; preserve those edits and export
them from Excalidraw rather than overwriting them with a regeneration.
Regeneration may change generated text-element IDs in the editable scene;
compare the drawing rather than expecting byte-identical scene JSON.

## Author the diagram

Start from `assets/excalidraw-example.json`. The input has a nonempty `alt`
description and an `elements` array of Excalidraw element skeletons. Each
element needs `type`, `x`, and `y`. Supported types are rectangle, ellipse,
diamond, text, arrow, and line. For a sketched stroke, use `line` with a
`points` array; incomplete `freedraw` elements are not supported by the skeleton
converter. Use `label: { "text": "..." }` for
text inside shapes; use `start: { "id": "..." }` and `end: { "id": "..." }`
to attach arrows. Element IDs must be unique.

Use `$ink`, `$surface`, `$accent`, `$blue`, `$green`, `$peach`, `$yellow`, `$red`,
or `$teal` in `strokeColor` and `backgroundColor`. The exporter resolves them
to Mocha/Latte values. Literal colors are preserved in both modes. Excalifont,
text measurement before layout, and stable roughness seeds are supplied by
the exporter. It does not choose node positions or route the graph for you.

Inspect labels, arrow bindings, spacing, both themes, and narrow-screen
scrolling in the final artifact. A successful export checks the file format
and font embedding, not whether the composition communicates well.

## What is stored where

The skill contains only our exporter, this guide, an example input, the small
package manifest, and its dependency lockfile. The official library, fonts,
and browser binaries are downloaded, not vendored.

All projects reuse one persistent runtime per bundled revision under
`~/.cache/html-artifact/excalidraw/<key>/`, or
`$XDG_CACHE_HOME/html-artifact/excalidraw/<key>/` when set. The key includes the
manifest, lockfile, exporter sources, Bun version, OS, and architecture.

Only the first run for that key installs with
`bun install --frozen-lockfile --ignore-scripts`. Chromium binaries live in
the shared `html-artifact/excalidraw/browsers/` directory. Once setup succeeds,
subsequent runs skip both install commands and reuse the same `node_modules`.
Concurrent first runs wait for setup; exports then run independently with
their own browser, local port, and output prefix. Use distinct output prefixes
for simultaneous exports. Nothing is installed in a project or the skill.

A failed setup can be retried. If a process is forcibly killed during setup,
the next run may report a stale lock; check its recorded PID has stopped before
removing that lock directory. Runtime revisions remain cached after upgrades;
remove old revisions only when no export is using them. A missing or damaged
cache can be rebuilt by removing that revision's `.ready` marker while idle
and rerunning the command.

The manifest pins Excalidraw 0.18.0, React/React DOM 18.3.1, and Playwright
1.63.0; `bun.lock` pins their transitive dependencies. Update dependencies
deliberately in a temporary workspace, copy back the manifest and lockfile,
and rerun the example and browser review. Do not run `bun install` in the skill.

API references: [element skeletons](https://docs.excalidraw.com/docs/@excalidraw/excalidraw/api/excalidraw-element-skeleton),
[SVG export](https://docs.excalidraw.com/docs/@excalidraw/excalidraw/api/utils/export),
[Playwright browsers](https://playwright.dev/docs/browsers).

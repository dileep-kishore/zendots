# Excalidraw generation

Use the bundled exporter. It installs the official Excalidraw package from a
checked-in manifest and `bun.lock`, runs the browser-only export APIs in
headless Chromium, and exits. No MCP or interactive editor setup is required.
Use T3's built-in browser for visual review when working in T3.

## Run

Requires Bun, tested with 1.4.2. The first run needs network access to download
the locked packages and Playwright's matching Chromium headless shell. On
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

The authored JSON remains the input for regeneration. Manual changes to the
`.excalidraw` output do not update that JSON; preserve those edits and export
them from Excalidraw rather than overwriting them with a regeneration.

## Author the diagram

Start from `assets/excalidraw-example.json`. The input has a nonempty `alt`
description and an `elements` array of Excalidraw element skeletons. Each
element needs `type`, `x`, and `y`. Supported types are rectangle, ellipse,
diamond, text, arrow, line, and freedraw. Use `label: { "text": "..." }` for
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

Each invocation installs with `bun install --frozen-lockfile --ignore-scripts`
in an isolated system temporary directory, reusing Bun's package cache.
Playwright reuses its normal browser cache. Successful runs remove the temporary
workspace; failed runs retain it and print its path for diagnosis. Neither
`node_modules` nor generated bundles belong in the skill or chezmoi source.

The manifest pins Excalidraw 0.18.0, React/React DOM 18.3.1, and Playwright
1.63.0; `bun.lock` pins their transitive dependencies. Update dependencies
deliberately in a temporary workspace, copy back the manifest and lockfile,
and rerun the example and browser review. Do not run `bun install` in the skill.

API references: [element skeletons](https://docs.excalidraw.com/docs/@excalidraw/excalidraw/api/excalidraw-element-skeleton),
[SVG export](https://docs.excalidraw.com/docs/@excalidraw/excalidraw/api/utils/export),
[Playwright browsers](https://playwright.dev/docs/browsers).

---
name: check-web-ui
description: Use when building, changing, or reviewing a web UI (site, landing page, app screen, dashboard, or component) before calling it done, or when asked to check one for AI slop, fake content, dead controls, accessibility, or mobile layout.
---

# Check web UI

Hold a web UI to four things generated UIs usually miss: every fact on screen
is real or visibly a placeholder, every control does something, it works for
keyboard, low-vision, and phone users, and a run in a real browser proves it.
Visual direction is a separate job: follow `frontend-design` or the project's
own design guidance for that. This skill filters and verifies.

For a review request, report findings with file and line and edit nothing.
When building, apply each section as you go, then run section 6.

## 1. Content is real or visibly a placeholder

Copy may be drafted; facts may not. Never invent, and ask for any you need:

- numbers: user counts, uptime, revenue, ratings, "+12% this week" deltas
- people: testimonials, names, job titles, avatars, team photos
- proof: customer logos, "trusted by" bars, press mentions
- claims: SOC 2, ISO 27001, "enterprise-grade", "10x faster"
- data: table rows, activity feeds, chart series, prefilled form values
  (`John Doe`, `jane@acme.com`)
- FAQ questions nobody asked, and a logo or app icon nobody specified

When the real value is missing, leave it out, or show a placeholder a viewer
can see is one: `[REAL DATA]`, `[LOGO]`, an initials avatar, "Coming soon".
Form placeholders describe the field (`email@example.com`), not a person.
An empty section beats a fabricated one.

## 2. App and dashboard screens

- Name the screen's job and the one decision the user makes there, then build
  around it. A sidebar, four stat cards, a chart, and a table is a default,
  not a design.
- Stat cards: only real metrics, unequal when their importance is unequal. A
  delta needs a real, named comparison period.
- Charts: title each with the question it answers ("Failed jobs per hour,
  last 24h"). If a sentence answers it, write the sentence.
- Tables: choose columns from the user's decision and put the deciding field
  early. Row menus hold only actions that exist.
- Empty, loading, and error states say why and what next ("No jobs yet. Run a
  sync to see results here"), not "No data available" or a bare spinner.
  First run, filtered to nothing, and permission denied are different states.

## 3. Every control works

- Each nav item reaches a page or section that exists.
- Each button, link, menu, tab, accordion, and toggle does something visible.
- Forms validate, submit, and show success and failure.
- Dialogs open, close, and close on Escape.
- Every view that loads data has empty, loading, and error states.
- A theme toggle works in both themes: contrast, components, and fonts.

An unbuilt feature is removed, or labeled "Coming soon" on screen with a
`TODO` in code. Never ship a control that looks live and does nothing.

## 4. Generated-UI patterns

Each of these is fine when you can say in one line what it does for this
product. As a default, cut or rework it:

- Layout: bento grid, fake terminal hero, "trusted by" logo bar under the
  hero, three pricing tiers with the middle one badged "Most popular",
  three-step "How it works", a four-column Product/Company/Resources/Legal
  footer, every section a centered title over identical cards.
- Decoration: blue-to-purple or purple-to-pink gradients, glow or
  glassmorphism on many elements at once, dot or grid backgrounds, a pill
  badge above the headline, sparkle, robot, or lightning icons, a colored
  stripe down the left edge of cards, pill radius on every element.
- Motion: elements that pulse, float, or bounce forever with no trigger.
- Identity: a layout that reads as Linear, Vercel, or Stripe when nobody
  asked for that look. Swap in another product's name and logo; if the page
  still fits, it has no identity.

## 5. People and phones

- Contrast: compute it, never eyeball it, since grey-on-grey pairs fool the
  eye. Body text needs 4.5:1 and large text (24px, or 18.7px bold) 3:1.
  Whatever identifies an active control or its state (a borderless input's
  edge, an icon-only button, a focus ring, a selected tab, a chart segment)
  needs 3:1 against its neighbours; decoration and disabled controls are
  exempt. For text over an image or gradient, check the spot behind the text
  with the least contrast, not the one that looks worst.

  ```bash
  python3 -I ~/.agents/skills/check-web-ui/scripts/contrast.py "#777777" "#ffffff"
  ```

- Keyboard: Tab order follows the visual order, Enter and Space activate,
  Escape closes. Focus is always visible; `outline: none` only with a
  replacement at least as visible.
- State is not color alone: errors and statuses carry text or an icon too.
- Phones: no horizontal scroll at 320px; grids stack; tap targets at least
  44x44px with space between; every hover interaction has a tap equivalent;
  navigation becomes a menu or bottom bar; sticky bars never cover content
  or inputs; text survives 200% zoom.
- Motion respects `prefers-reduced-motion`.

## 6. Prove it in a browser

Run the app and drive it in a real browser, using whatever the host provides:
a built-in browser pane, Orca's browser, a browser extension, or the project's
Playwright. At 320px, 390px, and a desktop width, and in each theme:

1. Watch the console from page load. Any error or uncaught exception is a
   finding, except failures from requests you blocked on purpose in step 5.
2. Click every control from section 3 and note what happened.
3. Tab through the page once, start to end.
4. Check the layout at each width: nothing clipped, overlapped, or covered,
   and `document.documentElement.scrollWidth` no larger than
   `window.innerWidth`.
5. Look at each data view's empty, loading, and error states, forcing them
   if needed (empty fixture, throttled or blocked request). A blocked request
   passes when the error state appears and retry works.

If the UI cannot be run here, say so, check each control by reading the
code, and label the result unverified in the browser.

## Output

- Click-through: one line per control, `Sign up -> /signup form, no console
  errors`, at each width and theme checked.
- Placeholders still on screen and the real content each one needs.
- Findings left unfixed, with file and line and why.

Adapted from the antislop skills in miqdadbadjuber/anti-slop.

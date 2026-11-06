# Export: PDF, one-file HTML and Notion

## PDF

```bash
python3 ~/.agents/skills/build-reveal-deck/scripts/deck.py pdf <deck> [--pdf out.pdf]
```

This writes one 1600x900 page per slide, each after its last click, with the
navigation hidden. The pages are images: the text cannot be searched, but the
layout is exactly what the browser shows. Look at a few pages before you send
it. The default output is `<deck>/<folder name>.pdf`.

## One-file HTML

```bash
python3 ~/.agents/skills/build-reveal-deck/scripts/deck.py bundle <deck> [--out file.html]
```

This inlines the CSS, JavaScript and images into one file of about 400 KB,
with the animations kept. Google Fonts still load from the network. The deck
stops writing the slide number into the page URL, so an embedded copy leaves
the host page's address alone. Run `deck.py check <file>` on the bundle to
prove it renders.

## Notion

A Notion page can hold both files:

- the bundle, embedded as a live deck: click into it and use the arrow keys;
- the PDF, as a fallback.

1. For each file, call the Notion `create-file-upload` tool with the file name.
2. POST the file to the returned `upload_url` with the returned headers:
   ```bash
   curl -sS -X POST "<upload_url>" -H "authorization: <header value>" \
     -F "file=@deck.bundle.html;type=text/html"
   ```
   Use `type=application/pdf` for the PDF. The response gives a
   `file-upload://<id>` source.
3. Place the files in the page content: `<embed source="file-upload://<html id>" />`
   for the deck and `<pdf source="file-upload://<pdf id>" />` for the PDF.
   An upload expires if it is not placed within an hour.

The user's workspace keeps talks as pages in the Resources database. Each page
has `Type: Page` and `Tags: Presentation`, and its `Project` relation points
to every project the talk serves. Find or create those projects in the
Projects database first. Projects have no relation to one another, so mention
a related project in the page's goal callout. Do not publish or share a page
without asking the user.

A copy in Notion does not update when the deck changes. Rebuild both files
and replace them on the page after each edit.

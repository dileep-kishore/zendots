#!/usr/bin/env python3
"""Extract a PowerPoint file's text, speaker notes and images for rebuilding it as a deck.

Usage
-----
uv run --with python-pptx python3 pptx_extract.py <file.pptx> <out folder>

Writes ``<out>/outline.md`` (one section per slide: title, text in reading
order, tables, notes) and ``<out>/media/`` (every picture, named by slide).
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE
except ImportError:
    sys.exit("python-pptx is missing; run this script with `uv run --with python-pptx python3 ...`")


def picture(shape):
    """Return the image a shape shows, including a filled picture placeholder, or None."""
    if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
        return shape.image
    if getattr(shape, "is_placeholder", False):
        try:
            return shape.image
        except (AttributeError, ValueError):
            return None
    return None


def shape_lines(shape, media: Path, slide_no: int, counter: list[int]) -> list[str]:
    """Return markdown lines for one shape, saving any picture it holds.

    Parameters
    ----------
    shape : pptx shape
        The shape to read; groups are read recursively.
    media : Path
        Folder that receives extracted pictures.
    slide_no : int
        One-based slide number, used in picture file names.
    counter : list of int
        Single-item running picture count for the slide.
    """
    if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
        return [line for s in shape.shapes for line in shape_lines(s, media, slide_no, counter)]
    image = picture(shape)
    if image is not None:
        counter[0] += 1
        name = f"slide-{slide_no:02d}-{counter[0]}.{image.ext}"
        (media / name).write_bytes(image.blob)
        return [f"![{shape.name}](media/{name})"]
    if shape.has_table:
        rows = [[cell.text.strip().replace("\n", " ") for cell in row.cells] for row in shape.table.rows]
        out = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * len(rows[0])]
        return out + ["| " + " | ".join(r) + " |" for r in rows[1:]]
    if shape.has_text_frame:
        lines = []
        for para in shape.text_frame.paragraphs:
            # para.text keeps soft line breaks (Shift+Enter) as \v; runs alone would glue the words together
            text = para.text.replace("\v", "<br>").strip()
            if text:
                lines.append("  " * para.level + f"- {text}")
        return lines
    return []


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, out = Path(sys.argv[1]).expanduser(), Path(sys.argv[2]).expanduser()
    media = out / "media"
    media.mkdir(parents=True, exist_ok=True)
    prs = Presentation(str(src))
    doc = [f"# {src.name}", "", f"{len(prs.slides)} slides, {prs.slide_width.inches:.2f} x {prs.slide_height.inches:.2f} in", ""]
    for i, slide in enumerate(prs.slides, 1):
        title_shape = slide.shapes.title
        doc += [f"## Slide {i}: {' '.join(title_shape.text.split()) if title_shape is not None and title_shape.has_text_frame else '(no title)'}", ""]
        counter = [0]
        # reading order: top to bottom, then left to right
        shapes = sorted((s for s in slide.shapes if s != title_shape), key=lambda s: (s.top or 0, s.left or 0))
        for shape in shapes:
            doc += shape_lines(shape, media, i, counter)
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame.text.strip():
            doc += ["", "Notes:", "", slide.notes_slide.notes_text_frame.text.strip()]
        doc.append("")
    (out / "outline.md").write_text("\n".join(doc))
    print(out / "outline.md")


if __name__ == "__main__":
    main()

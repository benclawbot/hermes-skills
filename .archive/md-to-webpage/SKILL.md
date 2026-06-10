---
name: md-to-webpage
description: "Transform a Markdown .md file into a beautiful standalone HTML webpage. Converts all standard Markdown elements (headings, tables, code blocks, lists, blockquotes, images) into a light-themed, readable HTML page with black text on white background. Default theme: white bg, near-black text, navy blue table headers (#1e3a5f), light gray alternating rows. Pure Python stdlib + optional pygments for code highlighting."
---

# md-to-webpage

Transform any Markdown file into a polished, self-contained HTML webpage with zero external dependencies beyond Python stdlib + pygments.

## Triggers
- User asks to convert, transform, or render a Markdown file to HTML/webpage
- User wants to preview a `.md` file as a styled webpage

## Usage
```bash
python3 ~/.hermes/skills/creative/md-to-webpage/references/md2html.py input.md [output.html]
```

## Inputs
- A `.md` file path (required)
- Optional output HTML path (defaults to input filename with `.html` extension)

## Outputs
- A standalone `.html` file — no external dependencies except Google Fonts
- Code blocks syntax-highlighted via Pygments
- Fully self-contained, works offline (except fonts)

## Supported Markdown Elements
- Headings (h1–h6) with anchor IDs
- Paragraphs, bold, italic, strikethrough
- Links and images
- Inline code and fenced code blocks with language detection
- Blockquotes
- Ordered and unordered lists (nested)
- Horizontal rules
- Tables with alternating row styles
- Task list checkboxes

## Tips
- **Default theme is light (white bg, near-black text).** Thomas rejected dark themes for PM documents — use light theme for any document intended for human readability.
- Output is self-contained, mobile-responsive
- Pygments used for code highlighting (falls back gracefully if unavailable)
- Also used as the rendering engine in the PM dashboard — see `references/dashboard-rendering.md` for the dashboard integration details (marked.js + DOMPurify CDN)
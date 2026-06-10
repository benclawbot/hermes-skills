# Dashboard Integration — Markdown Rendering

## How the dashboard renders PM documents as HTML

The PM dashboard (`/home/thomas/pm-dashboard.html`) uses `marked.js` + `DOMPurify` from CDN to render generated Markdown output as styled HTML in the output modal.

### CDN libraries (verified 200 OK)
```
https://cdn.jsdelivr.net/npm/marked/marked.min.js
https://cdn.jsdelivr.net/npm/dompurify@3.0.0/dist/purify.min.js
```

### Fallback (no CDN)
If CDN fails, escape HTML entities and convert newlines to `<br>`:
```javascript
var renderedHtml = currentRawContent
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/\n/g, '<br>');
```

### marked.js configuration
```javascript
marked.setOptions({
  breaks: true,    // single newline = <br>
  gfm: true,       // GitHub-flavored Markdown (tables, task lists, etc.)
  headerIds: true,
  mangle: false
});
```

### Rendered document CSS (dark PM theme)
Applied to `#doc-rendered` in the modal body:
- Background: `#0d1117` (GitHub dark)
- Font: Inter 15px / line-height 1.75
- Headings: `#f0f4ff`, bottom-border underline on h1/h2
- Table headers: `rgba(0,113,227,0.25)` bg, `#7ec8ff` text
- Code: `rgba(0,0,0,0.35)` bg, `#a8d8ff` text, JetBrains Mono
- Pre blocks: `#0d1117` bg, `#e6edf3` text
- Blockquotes: blue left-border `#3a7fcf`, italic, `#8ba0b8`
- Links: `#5bb8f5`
- Task checkboxes: rendered as `input[type=checkbox]` disabled

### Tab switching
- `switchTab('rendered')` shows `#doc-rendered`, hides `#modal-content`
- `switchTab('raw')` shows monospace `<pre>` with raw Markdown, hides rendered div
- `currentRawContent` variable holds raw text for Copy button

### Copy
`navigator.clipboard.writeText(currentRawContent)` — copies Markdown source, not HTML.

## md2html.py — CLI standalone converter

Located at: `~/.hermes/skills/creative/md-to-webpage/references/md2html.py`

Pure Python stdlib + optional pygments. No external dependencies.

**Usage:**
```bash
python3 ~/.hermes/skills/creative/md-to-webpage/references/md2html.py input.md [output.html] [--open]
```

### Supported elements
- Fenced code blocks with language detection → Pygments syntax highlighting
- Headings h1–h6 with anchor IDs
- Bold, italic, strikethrough, inline code
- Links and images
- Blockquotes
- Ordered/unordered/nested lists
- Task list checkboxes
- Horizontal rules
- Tables (full support including alignment)

### Pygments integration
```python
try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name, get_lexer_for_filename, ClassNotFound
    from pygments.formatters import HtmlFormatter
    HAS_PYGMENTS = True
except ImportError:
    HAS_PYGMENTS = False
```
Falls back gracefully if pygments unavailable.
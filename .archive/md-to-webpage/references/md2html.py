#!/usr/bin/env python3
"""
md2html.py — Pure-stdlib Markdown to HTML converter
Converts any .md file to a beautiful dark-themed HTML page.
No external dependencies (falls back to stdlib-only if pygments unavailable).
"""
import re, sys, html as _html, os
from pathlib import Path

try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name, get_lexer_for_filename, ClassNotFound
    from pygments.formatters import HtmlFormatter
    HAS_PYGMENTS = True
except ImportError:
    HAS_PYGMENTS = False


DARK_CSS = """
body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 16px;
  line-height: 1.8;
  color: #e0e6f0;
  background: #0d1117;
  max-width: 780px;
  margin: 0 auto;
  padding: 48px 24px 96px;
}
h1,h2,h3,h4,h5,h6 {
  color: #f0f4ff;
  font-weight: 700;
  line-height: 1.3;
  margin: 1.8em 0 0.5em;
}
h1 { font-size: 2em; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 0.4em; }
h2 { font-size: 1.5em; border-bottom: 1px solid rgba(255,255,255,0.07); padding-bottom: 0.3em; }
h3 { font-size: 1.2em; }
h4 { font-size: 1.05em; color: #a0b0c8; }
p { margin: 0.9em 0; }
a { color: #5bb8f5; text-decoration: none; }
a:hover { text-decoration: underline; }
code { font-family: 'JetBrains Mono', 'Fira Code', Consolas, monospace; font-size: 0.875em; background: rgba(0,0,0,0.35); color: #a8d8ff; padding: 2px 6px; border-radius: 5px; }
pre { background: #161b22; border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 18px 20px; overflow-x: auto; margin: 1.2em 0; }
pre code { background: none; padding: 0; color: #e6edf3; font-size: 0.875em; }
blockquote { border-left: 3px solid #3a7fcf; padding: 2px 16px; margin: 1.2em 0; color: #8ba0b8; font-style: italic; }
ul,ol { padding-left: 1.5em; margin: 0.8em 0; }
li { margin: 0.3em 0; }
hr { border: none; border-top: 1px solid rgba(255,255,255,0.1); margin: 2em 0; }
table { width: 100%; border-collapse: collapse; margin: 1.2em 0; font-size: 0.9em; }
th { background: rgba(0,113,227,0.25); color: #7ec8ff; font-weight: 600; padding: 10px 14px; border: 1px solid rgba(0,113,227,0.3); text-align: left; }
td { padding: 9px 14px; border: 1px solid rgba(255,255,255,0.07); color: #c8d8e8; }
tr:nth-child(even) td { background: rgba(255,255,255,0.025); }
img { max-width: 100%; border-radius: 8px; }
input[type="checkbox"] { margin-right: 6px; }
.highlight { background: #161b22 !important; }
.highlight pre { background: transparent; border: none; padding: 0; }
.cb { border-radius: 3px; padding: 1px 4px; }
"""


def escape(s):
    return _html.escape(s, quote=False)


def code_block(code, lang):
    if HAS_PYGMENTS:
        try:
            if lang:
                lexer = get_lexer_by_name(lang)
            else:
                lexer = get_lexer_by_filetype(code)
        except ClassNotFound:
            lexer = get_lexer_by_name('text')

        formatter = HtmlFormatter(nowrap=False, cssclass='highlight', linenos=False)
        return highlight(code, lexer, formatter)
    else:
        escaped = escape(code)
        return f'<pre><code>{escaped}</code></pre>'


MD_PATTERNS = [
    # Fenced code block
    (r'```(\w*)\n(.*?)\n```', lambda m: code_block(m.group(2), m.group(1)), re.DOTALL),
    # Headings
    (r'^(#{1,6})\s+(.+)$', lambda m: f'<h{len(m.group(1))} id="{re.sub(r"[^a-z0-9]+", "-", m.group(2).lower())}">{inline(m.group(2))}</h{len(m.group(1))}>'),
    # HR
    (r'^---+$', lambda _: '<hr>'),
    # Blockquote
    (r'^&gt;\s+(.+)$', lambda m: f'<blockquote><p>{inline(m.group(1))}</p></blockquote>'),
    # Unordered list item
    (r'^[-*+]\s+(.+)$', lambda m: f'<li>{inline(m.group(1))}</li>'),
    # Ordered list item
    (r'^\d+\.\s+(.+)$', lambda m: f'<li>{inline(m.group(1))}</li>'),
    # Task list
    (r'^-\s+\[([ xX])\]\s+(.+)$', lambda m: f'<li><input type="checkbox" {"checked" if m.group(1)=="x" or m.group(1)=="X" else ""} disabled> {inline(m.group(2))}</li>'),
    # Table row (th)
    (r'^\|\s*(.+?)\s*\|\s*---+\s*\|', lambda m: None),  # skip separator
    (r'^\|\s*(.+?)\s*\|$', lambda m: f'<tr>{"".join(f"<th>{inline(c.strip())}</th>" for c in m.group(1).split("|") if c.strip())}</tr>'),
    (r'^---', lambda m: None),
]

BLOCK_RE = re.compile(r'^---.*$', re.MULTILINE)


def block_level(line):
    for pattern, _, *flags in MD_PATTERNS:
        if re.match(pattern, line):
            return True
    return False


def inline(text):
    # bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # italic
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # strikethrough
    text = re.sub(r'~~(.+?)~~', r'<del>\1</del>', text)
    # inline code
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # images
    text = re.sub(r'!\[([^\]]*)\]\(([^\)]+)\)', r'<img src="\2" alt="\1">', text)
    # links
    text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', text)
    return text


def parse_fenced_code(lines, i):
    lang = ''
    if lines[i].startswith('```'):
        lang = lines[i][3:].strip()
    content_lines = []
    i += 1
    while i < len(lines) and not lines[i].startswith('```'):
        content_lines.append(lines[i])
        i += 1
    return i + 1, code_block('\n'.join(content_lines), lang)


def parse_table(lines, i):
    rows = []
    while i < len(lines) and re.match(r'^\|', lines[i]):
        m = re.match(r'^\|\s*(.+?)\s*\|$', lines[i])
        if m and '---' not in lines[i]:
            cells = [c.strip() for c in m.group(1).split('|')]
            if cells and any(cells):
                rows.append(cells)
        i += 1
    if len(rows) < 2:
        return i, None
    header, body = rows[0], rows[1:]
    html = '<table>\n<thead>\n<tr>'
    html += ''.join(f'<th>{inline(h)}</th>' for h in header)
    html += '</tr>\n</thead>\n<tbody>\n'
    for row in body:
        html += '<tr>' + ''.join(f'<td>{inline(cell)}</td>' for cell in row) + '</tr>\n'
    html += '</tbody>\n</table>'
    return i, html


def parse_blockquote(lines, i):
    lines_bq = []
    while i < len(lines) and lines[i].startswith('>'):
        lines_bq.append(lines[i][1:].strip())
        i += 1
    content = ' '.join(inline(l) for l in lines_bq)
    return i, f'<blockquote><p>{content}</p></blockquote>'


def parse_list(lines, i):
    html = ''
    in_ul = in_ol = False
    while i < len(lines):
        l = lines[i].rstrip()
        ul_m = re.match(r'^[-*+]\s+(.+)$', l)
        ol_m = re.match(r'^\d+\.\s+(.+)$', l)
        task_m = re.match(r'^-\s+\[([ xX])\]\s+(.+)$', l)
        if not (ul_m or ol_m or task_m) and not l.startswith('>'):
            break

        if task_m:
            checked = 'checked' if task_m.group(1) in ('x', 'X') else ''
            cb = f'<li><input type="checkbox" {checked} disabled> {inline(task_m.group(2))}</li>'
            if not in_ul:
                if in_ol: html += '</ol>\n'; in_ol = False
                html += '<ul>\n'; in_ul = True
            html += cb
            i += 1
        elif ul_m:
            cb = f'<li>{inline(ul_m.group(1))}</li>'
            if not in_ul:
                if in_ol: html += '</ol>\n'; in_ol = False
                html += '<ul>\n'; in_ul = True
            html += cb
            i += 1
        elif ol_m:
            cb = f'<li>{inline(ol_m.group(1))}</li>'
            if not in_ol:
                if in_ul: html += '</ul>\n'; in_ul = False
                html += '<ol>\n'; in_ol = True
            html += cb
            i += 1
        else:
            break

    if in_ul: html += '</ul>\n'
    if in_ol: html += '</ol>\n'
    return i, html


def convert(md_text):
    lines = md_text.split('\n')
    html_parts = []
    i = 0
    in_p = False

    while i < len(lines):
        line = lines[i].rstrip()

        # Blank line
        if not line.strip():
            if in_p:
                html_parts.append('</p>\n')
                in_p = False
            i += 1
            continue

        # Fenced code block
        if line.startswith('```'):
            if in_p:
                html_parts.append('</p>\n')
                in_p = False
            i, cb = parse_fenced_code(lines, i)
            html_parts.append(cb)
            continue

        # Heading
        hm = re.match(r'^(#{1,6})\s+(.+)$', line)
        if hm:
            if in_p:
                html_parts.append('</p>\n')
                in_p = False
            lvl = len(hm.group(1))
            anchor = re.sub(r'[^a-z0-9]+', '-', hm.group(2).lower())
            html_parts.append(f'<h{lvl} id="{anchor}">{inline(hm.group(2))}</h{lvl}>\n')
            i += 1
            continue

        # HR
        if re.match(r'^---+$', line):
            if in_p:
                html_parts.append('</p>\n')
                in_p = False
            html_parts.append('<hr>\n')
            i += 1
            continue

        # Table
        if line.startswith('|'):
            if in_p:
                html_parts.append('</p>\n')
                in_p = False
            i, tbl = parse_table(lines, i)
            if tbl:
                html_parts.append(tbl + '\n')
            continue

        # Blockquote
        if line.startswith('>'):
            if in_p:
                html_parts.append('</p>\n')
                in_p = False
            i, bq = parse_blockquote(lines, i)
            html_parts.append(bq + '\n')
            continue

        # List
        if re.match(r'^[-*+]|^-\s+\[|^(\d+)\.', line):
            if in_p:
                html_parts.append('</p>\n')
                in_p = False
            i, lst = parse_list(lines, i)
            html_parts.append(lst)
            continue

        # Paragraph
        if not in_p:
            html_parts.append('<p>')
            in_p = True
        html_parts.append(inline(line))
        html_parts.append('<br>\n')
        i += 1

    if in_p:
        html_parts.append('</p>\n')

    return ''.join(html_parts)


def build_html(body_html, title='Generated Document', description=''):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
{DARK_CSS}
</style>
</head>
<body>
{body_html}
</body>
</html>"""


def main():
    if len(sys.argv) < 2:
        print("Usage: md2html.py input.md [output.html] [--open]", file=sys.stderr)
        sys.exit(1)

    args = sys.argv[1:]
    open_after = '--open' in args
    args = [a for a in args if a != '--open']

    input_path = Path(args[0])
    if not input_path.exists():
        print(f"Error: '{input_path}' not found", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args[1]) if len(args) > 1 else input_path.with_suffix('.html')
    md_text = input_path.read_text(encoding='utf-8')

    body_html = convert(md_text)
    title = input_path.stem.replace('-', ' ').replace('_', ' ').title()
    html = build_html(body_html, title=title)

    output_path.write_text(html, encoding='utf-8')
    print(f"Generated: {output_path}")

    if open_after:
        import subprocess
        subprocess.run(['xdg-open', str(output_path)])


if __name__ == '__main__':
    main()

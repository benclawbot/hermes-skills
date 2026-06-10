---
name: html-to-telegram
description: "Convert HTML content to Telegram-safe .txt delivery. Use when Thomas needs to receive a file on Telegram — Telegram rejects .html uploads, so this converts to .txt and names it so Thomas knows to rename after download."
version: 1.0.0
author: Thomas
metadata:
  hermes:
    tags: [telegram, file-delivery, html]
---

# HTML to Telegram Delivery

Telegram does not support `.html` file uploads. Use this skill when Thomas needs to receive an HTML file (dashboards, reports, web content) via Telegram.

## The problem

Telegram supports: `.cfg`, `.csv`, `.docx`, `.json`, `.md`, `.pdf`, `.pptx`, `.txt`, `.xlsx`, `.yaml`, `.zip`
Telegram rejects: `.html`

## The solution

Use `html_to_telegram.py` to convert HTML → Telegram-safe `.txt` with a rename note.

### Usage

```bash
# Inline content
python3 ~/.hermes/scripts/html_to_telegram.py "Hello world" report.txt

# From HTML file
python3 ~/.hermes/scripts/html_to_telegram.py --file /path/to/dashboard.html dashboard.txt

# Full workflow
python3 ~/.hermes/scripts/html_to_telegram.py --file /path/to/output.html report.txt
send_message(target="telegram", message="MEDIA:/home/thomas/.hermes/cache/telegram-delivery/report.txt\n\nDownloaded as report.txt — rename to .html after download")
```

### How it works

1. Reads HTML content (inline or from file)
2. Strips script/style blocks
3. Converts block elements to newlines
4. Removes remaining HTML tags
5. Saves as `.txt` in `~/.hermes/cache/telegram-delivery/`
6. If original filename ended in `.html`, includes a rename note in the delivery message

### Delivery message format

Always include the rename instruction when the original was `.html`:

```
MEDIA:/path/to/somefile.txt

Downloaded as somefile.txt — rename to .html after download
```

The `MEDIA:` prefix tells the gateway to send it as a file attachment rather than inline text.

### When to use

- Dashboard HTML files for Thomas to review
- Report HTML files that need to be saved locally
- Any `.html` content Thomas asked you to deliver
- If Thomas says "send me the file" and the content is HTML — use this

### When NOT to use

- Plain text content — can be sent directly
- PDF, MD, JSON, CSV — already Telegram-safe, send as MEDIA directly
- URLs — prefer to send the URL as a markdown clickable link `[name](url)`
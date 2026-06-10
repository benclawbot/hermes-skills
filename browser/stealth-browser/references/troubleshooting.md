# Stealth Browser — Troubleshooting Reference

## EPIPE crash with heredoc stdin

CloakBrowser crashes with `EPIPE` errors when invoked via heredoc-style stdin in the terminal tool:

```bash
# FAILS — EPIPE crash
cd /home/thomas/Desktop/hermes-agent && .venv/bin/python3 - << 'EOF'
from cloakbrowser import launch
browser = launch()
...
browser.close()
EOF

# FIX — write to temp file first
write_file(content="""from cloakbrowser import launch
browser = launch()
...
browser.close()
""", path="/tmp/script.py")
terminal(command=".venv/bin/python3 /tmp/script.py")
```

The EPIPE occurs in `node_modules/playwright/driver/package/lib/server/utils/pipeTransport.js` when the stdin pipe breaks. Node.js process exits uncleanly. Writing the script to disk and executing it avoids the pipe issue entirely.

## gdown version caveat

`gdown` CLI (Python package) in the hermes-agent venv doesn't support `--fuzzy` flag:

```
gdown: error: unrecognized arguments: --fuzzy
```

Use the file ID directly, not a fuzzy URL match:

```bash
.venv/bin/gdown "1PgwVexyt87SAIZZSp6EtfSP3XDySODXW" -O /tmp/output.png
```

Or pipe via curl with the export URL: `https://drive.google.com/uc?export=download&id=<ID>`

## Google Drive auth — what actually works

All programmatic approaches fail for private-account files (curl, gdown, CloakBrowser auth flow, browser_navigate):

- **curl/gdown** → redirects to Google sign-in HTML
- **CloakBrowser auth flow** → EPIPE crash or 2FA timeout
- **browser_navigate** → timeout on Drive URLs

**Only working approaches:**
1. Make the file public in Drive sharing ("Anyone with the link") → then use direct `curl` export URL
2. Upload to a different service (WeTransfer, Imgur, Dropbox, direct Telegram file)
3. Google Drive API + OAuth2 service account (requires Google Cloud setup)

Do not spend more than 10 minutes on Drive auth — escalate to workaround #1 or #2 immediately.

## CloakBrowser launch patterns

```python
# Correct — humanize on launch(), not goto()
from cloakbrowser import launch
browser = launch(humanize=True, headless=True)  # headless helps with EPIPE too
page = browser.new_page()
page.goto("...")

# headless=True often avoids EPIPE issues that headless=False triggers
```

## When to use CloakBrowser vs browser_navigate

- **browser_navigate**: simple navigation, no complex interactions needed
- **CloakBrowser**: Python scripting with complex interactions, auth flows, screenshot analysis, multi-step workflows

For Google Drive specifically: if the file is not public, CloakBrowser won't help — the 2FA wall blocks both approaches. Use workaround #1 or #2 instead.
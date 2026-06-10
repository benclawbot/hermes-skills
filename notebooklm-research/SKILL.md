---
name: notebooklm-research
description: Use Google NotebookLM CLI (notebooklm npm package) to research topics, chat with sources, and generate content
category: research
---

# NotebookLM Research

## Setup / Authentication

### 1. Install Playwright (one-time)
```bash
npx playwright install chromium
```

### 2. Login — BEST approach: regular terminal

The hermes terminal cannot reliably handle `notebooklm login` due to Playwright's stdin management. **Recommended:**

```
# Tell Thomas: open a regular terminal and run:
notebooklm login

# Complete auth in the Chrome window that opens, press Enter.
# Then return here — subsequent notebooklm commands work fine.
```

**Why this is best:** The auth flow requires an interactive Chrome window and an Enter keypress that `background=true` subshells can't reliably deliver to the waiting `waitForEnter()` call inside notebooklm.

### 3. BrowserBase as remote auth browser (recommended for server environments)

> See `references/browserbase-notebooklm-auth.md` for BrowserBase API quirks, session limits, and CDP workflow details.

notebooklm does NOT natively read BrowserBase env vars. It launches a local Chrome via Playwright's `chromium.launch()`. To use BrowserBase instead, use the auth script:

```bash
BROWSERBASE_API_KEY="bb_live_..." node ~/.hermes/skills/notebooklm-research/scripts/notebooklm-bb-auth.js
```

Thomas completes Google login via browserbase.com → project → Sessions (find the session ID shown in terminal output), then presses Enter. Auth state saves to `~/.notebooklm/storage-state.json`.

**Session limit:** BrowserBase free tier = 3 concurrent. If `bb sessions create` fails with 429, kill old sessions first with `bb sessions kill <id>`.

### Token file
`~/.notebooklm/storage-state.json` — `notebooklm list` returns "Not authenticated" if absent or empty. If login fails, the file is not created. Delete any empty stub before retrying.

---

## Core Workflows

### 1. Create a notebook and add sources

```bash
# Create
notebooklm create "My Research"

# List notebooks to get ID
notebooklm list

# Add sources (URL, file, or pasted text)
notebooklm source add <notebookId> <url>
notebooklm source add-file <notebookId> /path/to/file.pdf
notebooklm source add-text <notebookId> "Pasted text content"
```

### 2. Chat with a notebook

```bash
# Ask a question (shorthand)
notebooklm ask <notebookId> "What is the main argument?"

# Or use the chat subcommand (supports conversation continuation)
notebooklm chat ask <notebookId> "Summarize the key points"
notebooklm chat ask -c <conversationId> <notebookId> "Follow-up question"
```

### 3. Web research

```bash
# Search the web and discover relevant sources
notebooklm research web <notebookId> "your research query"
```

### 4. Manage sources

```bash
# List sources in a notebook
notebooklm source list <notebookId>

# Refresh a source (re-fetch URL/Drive content)
notebooklm source refresh <notebookId> <sourceId>

# Rename or delete sources
notebooklm source rename <notebookId> <sourceId> "New Title"
notebooklm source delete <notebookId> <sourceId>
```

---

## Commands Reference

| Command | Description |
|---|---|
| `notebooklm login` | Authenticate with Google |
| `notebooklm create <title>` | Create a new notebook |
| `notebooklm list` | List all notebooks |
| `notebooklm source add <id> <url>` | Add URL source |
| `notebooklm source add-file <id> <path>` | Upload file source |
| `notebooklm source add-text <id> <title>` | Add pasted text as source |
| `notebooklm source list <id>` | List notebook sources |
| `notebooklm ask <id> <question>` | Ask a question |
| `notebooklm chat ask <id> <question>` | Chat (supports continuations) |
| `notebooklm research web <id> <query>` | Web research |



---

## Typical Research Session

```bash
# 1. Create notebook
notebooklm create "Research: [Topic]"

# 2. Add sources
notebooklm source add <id> https://example.com/article
notebooklm source add-file <id> ~/Documents/paper.pdf

# 3. Ask questions
notebooklm ask <id> "What are the key findings?"
notebooklm ask <id> "Compare perspectives in these sources"

# 4. Web research (uses NotebookLM's web discovery)
notebooklm research web <id> "Related research on [topic]"
```

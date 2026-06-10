# BrowserBase + NotebookLM Reference

## Project ID format
- BrowserBase project IDs are **UUIDs** (`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`), NOT `proj_...` strings.
- The `proj_...` format shown in some docs is the PUBLIC project identifier, not the internal ID.
- Actual UUID found in: `bb sessions list` → `projectId` field.
- Also visible in browserbase.com URL: `/projects/<uuid>/...`

## API authentication
- Header: `x-api-key` (not `Authorization: Bearer` or `Bb-Api-Key`).
- Correct: `curl "https://api.browserbase.com/v1/projects" -H "x-api-key: bb_live_..."`
- Wrong headers → 401 with "Missing x-bb-api-key header"

## Session limits
- Default: 3 concurrent sessions. Exceeding → 429 "You've exceeded your max concurrent sessions limit".
- Sessions auto-expire ~5 minutes after creation (`expiresAt` field).
- Kill old sessions: `bb sessions kill <id>` (but kill may fail, check exit code).

## CDP connection workflow
1. `bb sessions create --record-session` → returns `{ id, connectUrl, seleniumRemoteUrl, ... }`
2. `connectUrl` is a `wss://` WebSocket URL — use it with Playwright's `chromium.connectOverCDP(url)`
3. `bb sessions list` does NOT return `connectUrl` — only `sessions create` does
4. `seleniumRemoteUrl` is for Selenium WebDriver, not Playwright CDP

## Auth state storage
- Path: `~/.notebooklm/storage-state.json` (not in `~/.config/notebooklm/`)
- Created by Playwright's `context.storageState({ path: ... })` after successful Google auth
- If `notebooklm list` says "Not authenticated", check if file exists and is non-empty
- Empty file = failed auth; delete and re-authenticate

## notebooklm login flow (what actually happens)
1. `chromium.launch({ headless, args: [...AutomationControlled] })` — local Chrome
2. `context.storageState({ path: output })` — saves auth cookie/token
3. Calls `waitForEnter()` — stdin must get a newline to proceed
4. Checks `page.url()` for `notebooklm.google.com` (not `accounts.google.com`)
5. Saves to `DEFAULT_STORAGE_PATH = ~/.notebooklm/storage-state.json`

## BrowserBase CLI (`bb`)
- Installed as: `/home/thomas/.local/lib/nodejs/node-v22.22.2-linux-x64/bin/bb`
- Not in PATH for execute_code sandbox (use full path or `which bb` first)
- Node-based (shows `DeprecationWarning: punycode` on stderr — ignore)
- JSON output starts with `[` for lists, `{` for single objects
- Must filter stderr/deprecation lines before parsing JSON
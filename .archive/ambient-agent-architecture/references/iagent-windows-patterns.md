# iAgent-windows Maintenance Patterns

Reference implementation notes for the 52-crate Rust workspace at `~/Desktop/iAgent-windows/`.

## README style conventions (Thomas-specific)

Thomas prefers visual content over technical diagrams in documentation:

- **Want:** Infographic + screenshot. Image-rich docs.
- **Avoid:** Architecture SVG diagrams — he calls them "ugly" and removes them decisively without discussion.
- **Robot emoji** in titles: removed on request.
- **Image placement:** infographic at top under title, desktop screenshot in dedicated Screenshots section.

Image assets live in `docs/assets/`:
- `iagent-infographic.png` — the high-res platform overview infographic
- `iagent-desktop-full.jpg` — desktop screenshot
- `iagent-architecture.png` — (unused, was removed)

## Git hygiene for standalone repos

Thomas wants clean standalone repos with no fork history. Before creating a standalone repo from a Hermes-managed project:

1. Extract all Hermes-specific deps, configs, and internal references
2. Remove any `fork-history/` or `original-repo/` references
3. Verbose READMEs that make sense to an outside reader

## High-res image sourcing from users

When Thomas needs to replace an image in a repo:

1. Try direct download URL first (Drive public share, etc.)
2. If Google Drive: requires account session — either make file public, use Drive API OAuth, or ask Thomas to upload via different service (Telegram direct upload, Imgur, Dropbox)
3. Do NOT spend >10 minutes trying to extract a Google Drive file via curl or browser
4. WeTransfer links: can be one-time use or session-gated — check carefully

## Active build objectives (as of May 2026)

From `cron ed304617ac86`:
- MiniMax M2.7 for memory agent sidecar routing
- WebSocket gateway completion (`/status` endpoint)
- Gmail/Word/Excel/PowerPoint/browser/form-fill skills
- `app-integrations` crate has PowerPoint/Outlook stubs — needs Word/Excel COM automation
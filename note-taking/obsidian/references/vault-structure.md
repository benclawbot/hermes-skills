# Obsidian Vault — Thomas's Setup

**Vault path:** `/home/thomas/Desktop/Memory/` (updated May 2026 — moved from `~/Dropbox/memory/Obsidian` after Dropbox sync corruption)

## Migration notes (May 2026)
- Vault moved here from `~/Dropbox/memory/Obsidian` after Dropbox sync destroyed some data.
- Some notes may still contain hardcoded old Dropbox paths — audit with:
  `grep -rE "/home/thomas/Dropbox" --include="*.md" -l /home/thomas/Desktop/Memory/`
- Known path patterns requiring correction in notes:
  - `/home/thomas/Dropbox/memory/Obsidian/` → `/home/thomas/Desktop/Memory/`
  - `/home/thomas/Dropbox/Projects/` → external code repos, verify location individually
- The vault has no embedded git repo. The `backup_obsidian.sh` script pushes to `benclawbot/Hermes-Backup` — its vault path variable must match the current `OBSIDIAN_VAULT_PATH` or backups silently fail.

## Folder Structure

```
Obsidian/
├── AI/                  # AI-related notes
├── Active Context/      # Current work/in-progress
├── Conversations/       # Daily conversation summaries (long-term memory)
├── People/              # Person-specific notes
│   ├── Thomas.md        # Thomas's own profile note
│   ├── Alexandra.md
│   ├── Jack.md
│   ├── Noah.md
│   └── README.md
├── Projects/            # Project-specific notes
├── Research/            # Research notes
├── broken-link-fuzzy-map.md
├── tools/
├── wiki/
├── vault-connectivity-report.md
├── vault-health-report-full.md
└── vault-health-report.md
```

## Conventions

- `Conversations/` — daily session summaries, each note covering one day's exchanges
- `People/` — person-specific context and memory
- Thomas's own profile is at `People/Thomas.md` (not a special location, just a person note like any other)
- Vault has health/connectivity monitoring reports at root level — active management

## Usage Pattern

Thomas uses this vault for:
1. Daily conversation summaries (long-term memory across sessions)
2. Research notes and findings
3. Active Context for current in-progress work
4. People knowledge (background on individuals)

When reading conversation summaries, check `Conversations/` first. When looking for project context, check `Projects/`. When researching a topic, `Research/` and the root `wiki/` are good starting points.

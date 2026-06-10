# Obsidian Vault Migration (May 2026)

## Trigger
Dropbox sync corruption destroyed data. Vault migrated from `~/Dropbox/memory/Obsidian` to `~/Desktop/Memory/`.

## Migration audit checklist

After any vault move, run through:

1. **Verify env var** — `OBSIDIAN_VAULT_PATH` should be set to `~/Desktop/Memory`
2. **Git remote** — ensure `origin` points to `https://github.com/benclawbot/obsidian-vault-backup.git`
3. **Run orphan detection** — use the script in the SKILL.md to find files with zero links to their encapsulating folder
4. **Fix folder anchors** — apply the folder anchoring logic per folder type
5. **Update cron jobs** — any cron referencing the old path must be updated to use `/home/thomas/Desktop/Memory`
6. **Git push** — confirm push succeeds

## Common path changes after migration

| Old | New |
|-----|-----|
| `~/Dropbox/memory/Obsidian` | `~/Desktop/Memory/` |
| `AI/Skills/index.md` (redirect) | `~/.hermes/skills/` (actual callable skills) |

## Dropbox-specific gotchas

- `.ods` files synced via Dropbox may get corrupted on re-download — validate before use
- Files deleted from Dropbox may still exist in vault at different paths — audit for duplicates
- Any `dropbox/` path references in notes should be replaced with `Memory/` references
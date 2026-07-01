# Performance troubleshooting — full recipe

Companion to the "Performance troubleshooting" section in SKILL.md. Use this when the SKILL.md quick path isn't enough — large vaults (5k+ notes), multiple suspected plugins, or the user wants a deeper audit.

## Step 1 — Baseline before touching anything

```bash
free -h
ps aux --sort=-%mem | head -20
echo "---obsidian only---"
ps -o pid,pcpu,pmem,rss,vsz,comm,args -C obsidian 2>/dev/null
echo "---top CPU---"
ps aux --sort=-%pcpu | head -10
```

Capture these numbers. Without a baseline you'll argue later whether the fix actually helped.

**Interpretation thresholds (3 GB class machine):**

| Signal | Healthy | Suspicious | Bad |
|---|---|---|---|
| Renderer RSS | < 400 MB | 400–800 MB | > 800 MB |
| Renderer %CPU at idle | < 5% | 5–30% | > 30% |
| Renderer %CPU in graph view | < 20% | 20–50% | > 50% |
| Total obsidian RSS sum | < 600 MB | 600 MB – 1.2 GB | > 1.2 GB |
| Swap activity (`vmstat 1`) | `si`/`so` = 0 | intermittent | sustained |

## Step 2 — Plugin isolation protocol

The fastest way to find a bad plugin is to bisect, not guess.

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Desktop/Memory}"
cp "$VAULT/.obsidian/community-plugins.json" "$VAULT/.obsidian/community-plugins.json.bak"

# Edit the file manually to enable half the plugins, restart, check.
# Then keep narrowing.
```

After each restart:
```bash
ps aux --sort=-%mem | grep obsi | grep -v grep
free -h
```

When you find the bad one, leave it disabled. Don't re-enable "to verify" — you've already verified.

## Step 3 — Plugin manifest red flags (extended)

Beyond the SKILL.md checklist, look for:

- **`minAppVersion` > 1 major version behind current Obsidian.** E.g. Obsidian 1.12.x but `minAppVersion: 0.15.0` — the plugin pre-dates the API reorganization around 1.0 and may be bridging through deprecated paths that cost cycles.
- **`fundingUrl` empty / author URL points to a deleted repo.** Abandoned plugins often break silently on Obsidian updates.
- **`main.js` size relative to features.** A 50 KB plugin that does "kanban" is fine. A 2.5 MB plugin that does "kanban" is suspicious. The 2026-06-27 fix: `tags-routes` was 2.5 MB for "3D graph + orphan management" — pinned the renderer.
- **`styles.css` > 50 KB.** Pure overhead; rarely justified.

```bash
# Quick scan
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Desktop/Memory}"
for p in "$VAULT/.obsidian/plugins"/*/; do
  name=$(basename "$p")
  main_size=$(stat -c%s "$p/main.js" 2>/dev/null || echo 0)
  css_size=$(stat -c%s "$p/styles.css" 2>/dev/null || echo 0)
  minver=$(python3 -c "import json; print(json.load(open('$p/manifest.json')).get('minAppVersion','?'))" 2>/dev/null)
  echo "$name  main=${main_size}B  css=${css_size}B  minApp=$minver"
done | sort -k2 -t= -n -r
```

## Step 4 — Graph.json tuning (extended)

The SKILL.md gives a minimal config. If you want to keep more features and still be fast:

```json
{
  "hideUnresolved": true,
  "showOrphans": false,
  "showArrow": false,
  "showAttachments": false,
  "showTags": false,
  "collapse-forces": true,
  "collapse-display": false,
  "collapse-color-groups": true,
  "collapse-filter": true,
  "textFadeMultiplier": 0,
  "nodeSizeMultiplier": 1,
  "lineSizeMultiplier": 1
}
```

**Per-option impact (vault with 2600 notes, 700 MB on disk):**

| Option | Impact | Why |
|---|---|---|
| `showOrphans` false | -30 to -50% nodes | Half of any large vault is orphans after migrations |
| `hideUnresolved` true | -10 to -20% nodes | Broken links pile up over years |
| `showArrow` false | ~halves edge-draw cost | Arrowhead = separate path with rotation per frame |
| `showAttachments` false | -5 to -15% nodes | PDFs/images add nodes |
| `showTags` false | -5% nodes + less label blending | Tag cloud nodes cluster with note nodes |
| `collapse-forces` true | Disables force simulation when idle | Big win if you don't pan |
| `collapse-display` true | Less label rendering | Save cost only if labels matter less |
| `textFadeMultiplier` = 0 | No fade blending | Cheap to leave default; non-zero is the killer |

## Step 5 — Vault-size profiling

If both plugins and graph are clean, the vault itself may be the ceiling.

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Desktop/Memory}"
echo "--- note count by top-level folder ---"
find "$VAULT" -mindepth 1 -maxdepth 1 -type d -not -name ".obsidian" -not -name ".git" | while read d; do
  count=$(find "$d" -name "*.md" -type f | wc -l)
  size=$(du -sh "$d" 2>/dev/null | cut -f1)
  printf "%6d  %8s  %s\n" "$count" "$size" "$(basename "$d")"
done | sort -rn

echo "--- biggest single notes ---"
find "$VAULT" -name "*.md" -type f -not -path "*/.obsidian/*" -printf "%s\t%p\n" | sort -rn | head -10
```

**Action thresholds:**
- A single folder with > 30% of total notes: candidate for splitting or archiving
- A single note > 500 KB: probably a pasted PDF transcript or log; consider moving it out of the vault or splitting
- Average note size > 10 KB on a small vault: investigate templates

## Step 6 — Cache flushes that often help (no data loss)

```bash
# GPU cache (force rebuild on next launch)
rm -rf /home/thomas/.config/obsidian/GPUCache
rm -rf /home/thomas/.config/obsidian/Code\ Cache
rm -rf /home/thomas/.config/obsidian/DawnGraphiteCache
rm -rf /home/thomas/.config/obsidian/DawnWebGPUCache
```

GPU cache rebuilds are safe but cost ~10s on first launch. Only do this if you've ruled out plugins and graph settings.

## Step 7 — When to give up and switch approach

On a 3 GB class machine, ~5000 notes is roughly the soft ceiling for Obsidian with all defaults. Beyond that:
- Archive old notes (move to `~/Archive/`, not delete) — Obsidian sees only the active vault
- Use multiple vaults instead of one mega-vault
- Use plain `find`/`grep` for search instead of Obsidian's built-in search

The user gets back to usable Obsidian without losing the corpus. Don't suggest this unless Step 1–6 don't restore normalcy.

## Worked example — 2026-06-27 Memory vault

- **Symptoms reported:** Obsidian super slow, high RAM
- **Baseline:** renderer at 98% CPU, 1.1 GB RSS; total obsidian RSS = 2.9 GB on a 3.3 GB system; 2.8 GB in swap
- **Diagnosis:** `tags-routes` community plugin, `minAppVersion: 0.15.0`, 2.5 MB `main.js`, description includes "3D graph"
- **Fix:** `echo "[]" > community-plugins.json`, kill obsidian procs
- **After:** renderer gone from process list, RAM 993 MB, swap 731 MB
- **Secondary:** graph.json tuned to minimal config — graph now loads in ~2s instead of hanging

## Reference links

- Obsidian plugin manifest spec: https://docs.obsidian.md/Plugins/Getting+started/Build+a+plugin
- Graph view docs: https://help.obsidian.md/Plugins/Graph+view
- Performance FAQ: https://help.obsidian.md/Performance
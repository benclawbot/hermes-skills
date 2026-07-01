---
name: obsidian
description: Read, search, and create notes in the Obsidian vault. Also covers vault-based skill management; import vault skill notes into Hermes callable skills; audit for broken links after vault moves; manage vault git backup; fix empty-container patterns (templates that record events but never record decisions) by identifying the must-be-non-empty section, auto-seeding it, and curating manually; troubleshoot Obsidian performance (bad plugins, slow graph view) on low-RAM machines. Use when Thomas says "find patterns in my notes", "what's hiding in my vault", "analyze my Obsidian", "build a site from my notes", "fix the empty containers", "fix the tag explosion", "what the vault would need to look different", "implement the [theme N] fix", "obsidian is slow", "obsidian is using too much RAM", "graph won't load", "obsidian crashed" — for understanding the *shape* of a corpus rather than retrieving a specific fact.
tags: [obsidian, note-taking, vault, skills, backup, empty-container, pattern-mining, taxonomy, performance]
version: 1.4.0
metadata:
  hermes:
    tags: [obsidian, note-taking, vault, skills, backup, empty-container, pattern-mining, taxonomy, performance]
    related_skills: [save-session-to-obsidian, memory-vault]
---

# Obsidian Vault

**Location:** Set via `OBSIDIAN_VAULT_PATH` environment variable (e.g. in `~/.hermes/.env`).

> **Thomas's vault:** `~/Desktop/Memory` — see `references/vault-structure.md` for folder layout.
>
> **Migration (May 2026):** Vault moved from `~/Dropbox/memory/Obsidian` to `~/Desktop/Memory/`. Dropbox sync corruption was the trigger. After any vault move, run through `references/vault-migration-audit.md`.
>
> **Migration (May 2026):** Vault moved from `~/Dropbox/memory/Obsidian` to `~/Desktop/Memory/`. Dropbox sync corruption was the trigger. After any vault move, run through `references/vault-migration-audit.md`.

If unset, defaults to `~/Documents/Obsidian Vault`.

Note: Vault paths may contain spaces - always quote them.

## Migration / audit

After any vault move, run through `references/vault-migration-audit.md` — covers env vars, backup script, path fixes, external project references, and git sync verification.

---

## Application Launch (Linux / .deb extract)

Obsidian is installed on Thomas's machine as an extracted `.deb` at `/opt/obsidian/obsidian` (NOT a snap — the snap route was abandoned because of confinement breakage on this host). The wrapper at `~/.local/bin/obsidian` exec's it with `--disable-gpu` (still required on the Haswell GPU).

### Failure Mode A — GPU crash (classic Haswell)
**Symptoms:** Window appears then crashes immediately, or `GPU process isn't usable. Goodbye.` in stderr.

**Root cause:** Haswell integrated GPU has incomplete Vulkan support. The iHD VAAPI driver (`iHD_drv_video.so`) fails and the Chromium GPU process crashes before the window renders.

**Fix — GPU flags:**
```bash
obsidian --disable-gpu --disable-software-rasterizer
```
- `--disable-gpu` — disable GPU hardware acceleration
- `--disable-software-rasterizer` — disable SwiftShader fallback (prevents secondary crash)

The wrapper at `~/.local/bin/obsidian` already passes `--disable-gpu`. Do NOT add `--disable-software-rasterizer` to the wrapper unless Mode A is firing — it disables legitimate CPU rasterization paths and degrades rendering.

### Install path notes (already done on this host, do not re-run)

```bash
# Install (only if /opt/obsidian doesn't exist):
cd /tmp
curl -L https://github.com/obsidianmd/obsidian-releases/releases/download/v1.12.7/obsidian_1.12.7_amd64.deb -o obsidian.deb
mkdir -p obsidian_extract
dpkg-deb -x obsidian.deb obsidian_extract
sudo rm -rf /opt/obsidian
sudo mv obsidian_extract/opt/Obsidian /opt/obsidian
rm -f ~/Desktop/obsidian_obsidian.desktop  # stale snap-era shortcut

cat > ~/.local/bin/obsidian << 'EOF'
#!/bin/bash
exec /opt/obsidian/obsidian --disable-gpu "$@"
EOF
chmod +x ~/.local/bin/obsidian

cat > ~/.local/share/applications/obsidian.desktop << 'EOF'
[Desktop Entry]
Name=Obsidian
Exec=/opt/obsidian/obsidian --disable-gpu %U
Terminal=false
Type=Application
Icon=/opt/obsidian/resources/icon.png
StartupWMClass=obsidian
MimeType=x-scheme-handler/obsidian;
Categories=Office;
EOF
chmod +x ~/.local/share/applications/obsidian.desktop
cp ~/.local/share/applications/obsidian.desktop ~/Desktop/obsidian.desktop
chmod +x ~/Desktop/obsidian.desktop
```

**Three critical path corrections:**
- Binary: `/opt/obsidian/obsidian` (all-lowercase) — extracted directory is `Obsidian` (capital O) but the executable inside is `obsidian`
- Icon: `resources/icon.png` — not `resources/obsidian.png`
- GPU flag: `--disable-gpu` still needed on Haswell even with the direct install

### Verification
```bash
ps aux | grep obsi | grep -v grep
# Should show: obsidian (main), obsidian --type=zygote, obsidian --type=renderer
# If only the bash wrapper shows, the app crashed — try with --in-process-gpu
```

See `references/app-launch-troubleshooting.md` for reproduction commands and extended diagnostics.

---

## Performance troubleshooting (slow launch, high CPU/RAM)

**Trigger:** Obsidian feels slow to open, the renderer process pegs CPU, or RAM usage is disproportionate to vault size. Common on low-RAM machines (3 GB class) running any vault > ~500 notes.

### Diagnostic — first 30 seconds

```bash
# 1. Confirm the app is the problem, not the kernel
free -h                                          # total RAM, used, swap
ps aux --sort=-%mem | head -15                   # top RSS consumers
ps aux | grep obsi | grep -v grep                # every obsidian process
```

**Interpretation:**
- Renderer (`--type=renderer`) at 80–100% CPU almost always = a community plugin in a hot loop
- RSS > 800 MB on a renderer process = graph view or a heavy plugin
- Swap activity (`vmstat 1` shows `si`/`so` > 0) = you're RAM-bound; disable features until it's quiet

### Bad community plugin — the most common cause

**Symptoms:** renderer pinned at high CPU, app slow to switch panes, vault navigation laggy. Often one specific plugin (graph renderers, dataview with huge queries, kanban boards over hundreds of cards).

**Diagnosis:**

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Desktop/Memory}"
cat "$VAULT/.obsidian/community-plugins.json"
echo "---installed---"
for p in $(cat "$VAULT/.obsidian/community-plugins.json" | python3 -c "import json,sys; print('\n'.join(json.load(sys.stdin)))"); do
  echo "=== $p ==="
  cat "$VAULT/.obsidian/plugins/$p/manifest.json" 2>/dev/null
  echo
done
```

**Red flags in any plugin manifest:**
- `minAppVersion` is years old (e.g. `0.15.0` on Obsidian 1.12.x) — likely abandoned, may not be bridged to current API
- `isDesktopOnly: false` for a heavy graph/canvas feature — Electron-vs-mobile shim overhead
- Description mentions "3D", "graph visualization", "force-directed" — known to peg renderers on big vaults
- `main.js` > 1 MB — usually a feature-heavy plugin with multiple heavy subsystems

**Fix (preserves plugin files for re-enable):**

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Desktop/Memory}"
echo "[]" > "$VAULT/.obsidian/community-plugins.json"
# Restart Obsidian. Re-enable one plugin at a time to isolate.
```

**Hard rule for low-RAM machines (3 GB class):** any plugin whose `main.js` > 500 KB OR whose `minAppVersion` is more than ~18 months old should be treated as suspect. Re-enable one-at-a-time after a fix and verify with `ps aux --sort=-%mem` between each.

### Graph view is slow — graph.json tuning

**Symptoms:** opening the graph view hangs for 10+ seconds, panning is janky, or it pegs CPU continuously.

**Root causes (in order of impact):**
1. `showOrphans: true` — every file with zero links becomes a node. On a vault with hundreds of orphans (or a fresh migration), this can double the node count.
2. `hideUnresolved: false` — every broken link target becomes a node. Large vaults accumulate hundreds of these.
3. `showArrow: true` — arrowheads double the edge-draw cost (draw arrowhead + line).
4. `showAttachments: true` — every image/PDF in the vault becomes a node.
5. `textFadeMultiplier` and friends — per-frame blending work; default `0` is fine, anything non-zero adds load.

**Minimal-perf `graph.json` for a vault > 1000 notes:**

```json
{
  "collapse-filter": true,
  "search": "",
  "showTags": false,
  "showAttachments": false,
  "hideUnresolved": true,
  "showOrphans": false,
  "collapse-color-groups": true,
  "colorGroups": [],
  "collapse-display": false,
  "showArrow": false,
  "textFadeMultiplier": 0,
  "nodeSizeMultiplier": 1,
  "lineSizeMultiplier": 1,
  "collapse-forces": true,
  "centerStrength": 0.5,
  "repelStrength": 10,
  "linkStrength": 1,
  "linkDistance": 250
}
```

Located at `$VAULT/.obsidian/graph.json`. Obsidian reads it on next open. If still slow after the cuts, the vault size itself is the ceiling — measure which folders dominate (`du -sh $VAULT/*/ | sort -h | tail`) and consider splitting or archiving the heaviest.

### Verification after a fix

```bash
# RAM should drop substantially
free -h

# No obsidian process should be at >30% CPU at idle
ps aux | grep obsi | grep -v grep
```

See `references/performance-troubleshooting.md` for the full diagnostic recipe and known-bad plugin patterns.

---

## Read a note

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"
cat "$VAULT/Note Name.md"
```

## List notes

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"

# All notes
find "$VAULT" -name "*.md" -type f

# In a specific folder
ls "$VAULT/Subfolder/"
```

## Search

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"

# By filename
find "$VAULT" -name "*.md" -iname "*keyword*"

# By content
grep -rli "keyword" "$VAULT" --include="*.md"
```

## Create a note

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"
cat > "$VAULT/New Note.md" << 'ENDNOTE'
# Title

Content here.
ENDNOTE
```

## Append to a note

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"
echo "

New content here." >> "$VAULT/Existing Note.md"
```

## Vault Skills Callable by Hermes

Vault skill notes in `AI/Skills/` ARE meant to be callable by Hermes. The "not automatically callable" note in old versions was incorrect.

**PM SOP inventory**: See `references/pm-sop-inventory.md` for the full SOP list (5 phases, 52 SOPs) with automation tier ratings derived from the PM research vault. Covers initiation through closure; gaps noted in risk/resource/procurement management areas.

**To make a vault skill callable:** Create a corresponding SKILL.md in `~/.hermes/skills/<category>/<name>/SKILL.md` using the vault note's content as the body. Key requirements:
- `name` field matching the skill identifier (lowercase, hyphens)
- `description` field (≤1024 chars)
- `category` — must be an existing Hermes category (autonomous-ai-agents, communication, productivity, systematic-debugging, etc.)
- Trigger keywords in body that tell when to load the skill

**Conversion workflow:**
1. Review the vault note — check it has useful content and a clear trigger condition
2. `skill_manage(action='create', category=<category>, name=<name>, content=<full SKILL.md with frontmatter + body>)`
3. Update the vault index note to mark it as migrated

**Current callable skills migrated from vault (May 2026):** 5-whys-analysis, cli-anything-hub, cli-anything-web, cronjob-ops, one-question-at-a-time, deep-research-obsidian, research-ingestion.

## Vault Linking and Cross-Folder Analysis

After any vault move or large content integration, audit cross-folder links to build a coherent knowledge graph. See also:
- `references/obsidian-3d-viz.md` — build an interactive 3D force-directed graph of vault links (Three.js, served locally). Full implementation in `scripts/generate_vault_3d.py`.
- `scripts/generate_vault_3d.py` — Python script that parses the vault, extracts link graph, runs a force-directed layout, and emits a self-contained 1.3 MB HTML file with embedded graph data. No server required after generation — open directly in a browser.

### 3D vault graph

**IMPORTANT (May 2026):** The original single-file HTML approach (embedding ~1.5 MB JSON directly in `<script>`) causes browsers to stall parsing. Always use the two-file approach:

- `~/vault_3d_viz.html` — lightweight viewer (~30 KB), fetches JSON via `fetch()`
- `~/vault_graph_data.json` — external graph data, generated by `scripts/generate_vault_3d.py`

The HTML must be served from the same directory as the JSON. Always create the Three.js renderer BEFORE fetching data so the canvas renders immediately.

Key viewer requirements: low-poly geometry (sphere 6-seg/5-ring), cap edges at 8000 normal + 1500 bidir, no second WebGL renderer (no minimap), pixel ratio capped at 2.

Full details in `references/obsidian-3d-viz.md`.
```python
#!/usr/bin/env python3
import os, re, yaml
from collections import Counter

vault_path = "/home/thomas/Desktop/Memory"
wikilink_re = re.compile(r'\[\[([^\]]+)\]\]')

files = [os.path.join(r,f) for r,ds,fs in os.walk(vault_path) 
         if '.obsidian' not in r for f in fs if f.endswith('.md')]

file_info = {}
for f in files:
    content = open(f, errors='ignore').read()
    title = os.path.splitext(os.path.basename(f))[0]
    if content.startswith('---'):
        try:
            fm = yaml.safe_load(content.split('---',2)[1])
            if fm and isinstance(fm, dict) and 'title' in fm:
                title = str(fm['title'])
        except: pass
    folder = f.replace(vault_path+'/','').split('/')[0]
    links = wikilink_re.findall(content)
    file_info[f] = {
        'title': title, 'folder': folder,
        'links': {l.split('|')[0].split('#')[0].strip().lower() for l in links}
    }

title_to_path = {info['title'].lower(): f for f,info in file_info.items()}

cross_counts = {}
for f, info in file_info.items():
    count = sum(1 for lt in info['links'] 
                if title_to_path.get(lt) and file_info[title_to_path[lt]]['folder'] != info['folder'])
    cross_counts[f] = count

zero = sum(1 for c in cross_counts.values() if c == 0)
print(f"Zero cross-folder links: {zero}/{len(file_info)}")
print(f"Avg cross-links: {sum(cross_counts.values())/len(file_info):.2f}")
```

### Cross-folder link building rules (apply in order)

**CRITICAL — Folder anchoring rule:** Every file in the vault MUST have at least one link to its encapsulating folder context. A file with zero links to its own folder is an orphan — fix it first, before adding cross-folder links.

Priority order:
1. **Same-folder links first** — if a file has zero links to its own folder, add those before cross-folder links
2. **PM topic clusters** — link pages within tightly related methodology clusters (Scrum→Sprint Planning, Kanban→WIP Limits, Lean→DMAIC, etc.)
3. **Project overviews → Research vault** — if an overview mentions 'scrum', 'kanban', 'agile', etc., link to the relevant PM research page
4. **Index pages → canonical entries** — MOC files, Schema files link to main topic pages
5. **People → Projects** — if a person's note mentions a project overview, link to it
6. **Project overview → sub-docs** — overview.md links to decisions.md, status.md, plan.md

### Cap per file
Max 4 new cross-folder links per file. Prefer the most meaningful semantic connections over exhaustive linkage.

### Folder anchoring logic per folder type
- **Projects/X/file.md** → `Projects/X/overview.md` (or README.md)
- **Research/X/Y/file.md** → `Research/X/_MOC.md` (Y is the cluster; anchor to parent cluster _MOC, not the leaf folder)
  - Skip `pages/`, `99-Meta/`, and `_Lot*` lot folders when determining cluster — these are infrastructure subfolders
  - If `Research/X/_MOC.md` does not exist, create it
- **Conversations/YYYY/MM/file.md** → creates `Conversations/YYYY/MM/index.md` listing all day files if missing
- **People/X.md** → most recently modified `Projects/*/overview.md` that mentions the person's name
- **AI/Skills/*.md** → `AI/Skills/index.md` (migrated skill docs anchor to the skills index)
- **Active Context/*.md** → most recently modified project overview

### Orphan detection script
```python
import os, re, yaml
from collections import Counter

vault = '/home/thomas/Desktop/Memory'
wikilink_re = re.compile(r'\[\[([^\]]+)\]\]')
files = []
for root, dirs, filenames in os.walk(vault):
    if '.obsidian' in root: continue
    for fn in filenames:
        if fn.endswith('.md'):
            files.append(os.path.join(root, fn))

file_info = {}
for fpath in files:
    try:
        content = open(fpath, errors='ignore').read()
        title = os.path.splitext(os.path.basename(fpath))[0]
        if content.startswith('---'):
            try:
                fm = yaml.safe_load(content.split('---',2)[1])
                if fm and isinstance(fm, dict) and 'title' in fm:
                    title = str(fm['title'])
            except: pass
        rel = fpath.replace(vault+'/', '')
        folder = rel.split('/')[0]
        sub = rel.split('/')[1:-1]
        links_raw = wikilink_re.findall(content)
        file_info[fpath] = {'title': title, 'folder': folder, 'sub': sub, 'relpath': rel, 'links_raw': links_raw}
    except: pass

title_map = {info['title'].lower(): info for info in file_info.values()}
path_map = {info['relpath']: info for info in file_info.values()}

orphans = []
for fpath, info in file_info.items():
    has_same = False
    for link_raw in info['links_raw']:
        lt = link_raw.split('|')[0].split('#')[0].strip().lower()
        tf_info = title_map.get(lt)
        if tf_info and tf_info['folder'] == info['folder']:
            has_same = True; break
        for rp, fi in path_map.items():
            if rp.lower() == f'{lt}.md' and fi['folder'] == info['folder']:
                has_same = True; break
    if not has_same:
        orphans.append((fpath, info))

print(f'Orphans: {len(orphans)}')
for f, c in Counter(i['folder'] for _, i in orphans).most_common():
    print(f'  {f}: {c}')
for f, i in orphans:
    print(f'  {i["relpath"]} [{i["title"]}] sub={i["sub"]}')
```

### Vault digest (weekly maintenance)
The vault digest script at `/home/thomas/.hermes/scripts/vault-digest.py` runs every Monday at 20:00. It:
1. Scans ALL vault files (not just a subfolder)
2. Applies folder anchors to orphan files (creates missing index/MOC files as needed)
3. Builds cross-folder bridges and topic clusters
4. Generates `AI/WeeklyDigests/YYYY-WXX.md` — a searchable digest of the entire vault
5. Commits and pushes to GitHub if changes were made; silently skips if vault is quiet

To run manually: `python3 /home/thomas/.hermes/scripts/vault-digest.py`

The canonical script is also saved at `scripts/vault-digest.py` inside this skill's directory.

## Empty-container pattern (vault failure mode)

Vaults accumulate templates that record *events* but never record *substance*. The shape is there — a project overview, a daily log, a weekly digest, an empty status file — but the field that should be non-empty is empty. When this happens at scale, the vault becomes a museum of skeletons.

**Symptom (any one of these is a tell):**
- A note type has many files with the same template, all with one section blank
- The same fragment (`### HH:MM - unknown`, `**Log:** [empty]`, `**Task:** unknown`) repeats hundreds of times
- `find` returns many files that are syntactically valid but semantically empty
- The template itself is well-designed (frontmatter, sections, links) — the substance is what's missing
- The pattern recurs at multiple scales (conversations AND project status files AND weekly digests)

**The fix (3 steps, in order):**

1. **Identify the one section that MUST be non-empty.** Don't redesign the template — the shape is fine. Pick the section whose absence makes the rest of the file useless. Examples: `## Decisions today` in daily conversation files, `## Current state` in project overviews, `## This week's changes` in weekly digests.
2. **Auto-seed that section.** Heuristically extract candidate content (decision-shaped lines, status keywords, diffs) and write them into the section. Mark them as advisory / auto-detected so a human still curates. The `save-session-to-obsidian` skill v1.4.0 implements this for conversation files: it scans each user message for first-person commitments, switch/decide verbs, persistent rules, and imperative bullets, and writes the top 5 into `## Decisions today`. A day with zero detected decisions is still signal (no real decisions that day) — the section placeholder persists.
3. **Delete the empty containers and document the pattern.** Files that are 100% empty (template only, no substance) are noise. Delete them. Then write a single vault note documenting the failure mode, the fix, and the operational rule going forward. Reference implementation: `AI/empty-containers-fix.md` in the Memory vault.

**Operational rule:** A vault note is incomplete until its must-be-non-empty section is non-empty. Either auto-detected content exists, or the writer has explicitly added curated content, or the section is replaced with an explicit "no real decisions / no real changes / no real status" note. A blank section is the failure mode itself.

**Detection script** — find empty-container candidates in any folder:

```python
import os, re
from collections import defaultdict

vault = "/home/thomas/Desktop/Memory"
# Pattern: file where >50% of body is whitespace or "unknown"/"none"/"[empty]" placeholders
PLACEHOLDER = re.compile(r'\b(unknown|none|\[empty\]|TODO|TBD)\b', re.IGNORECASE)
candidates = []
for root, _, files in os.walk(vault):
    if '.obsidian' in root or '.git' in root: continue
    for f in files:
        if not f.endswith('.md'): continue
        path = os.path.join(root, f)
        text = open(path, errors='ignore').read()
        # Strip frontmatter
        body = re.sub(r'^---\n.*?\n---\n', '', text, flags=re.DOTALL).strip()
        if not body: 
            candidates.append((path, 1.0, "empty body"))
            continue
        lines = [l for l in body.splitlines() if l.strip()]
        if not lines: continue
        placeholder_ratio = sum(1 for l in lines if PLACEHOLDER.search(l)) / len(lines)
        if placeholder_ratio > 0.5:
            candidates.append((path, placeholder_ratio, f"{int(placeholder_ratio*100)}% placeholder"))

candidates.sort(key=lambda x: -x[1])
print(f"Empty-container candidates: {len(candidates)}")
for path, ratio, reason in candidates[:20]:
    print(f"  [{ratio:.2f}] {path}  ({reason})")
```

**When to apply this fix:**
- A user complains the vault "doesn't remember anything"
- A weekly digest or audit shows the same template repeated across many files
- An AI agent retrieving from the vault returns empty / placeholder content
- A new note type is being designed (preemptive — pick the must-be-non-empty section before launching the template)

**Reference implementations:**
- `AI/Skills/save-session-to-obsidian` — `## Decisions today` for daily conversation files (v1.4.0+)
- Vault note `AI/empty-containers-fix.md` — the meta-finding + operational rules

## Wikilinks

Obsidian links notes with `[[Note Name]]` syntax. When creating notes, use these to link related content.

### Link resolution rules (critical — common source of broken links)

**Case sensitivity:** Obsidian resolves wikilink targets with **case-sensitive folder paths** and **case-insensitive filenames**.

```
✅ [[People/Alexandra]]   → matches People/Alexandra.md (folder case matches)
❌ [[people/alexandra]]   → broken: folder "people/" doesn't exist (Thomas's vault has "People/")
❌ [[people/alexandra]]   → would work only if folder were actually named "people/" in lowercase
```

**The alias form `[[target|display]]`:** the target is only the part BEFORE the pipe `|`. The display text after `|` is never a link target.

```
[[People/Alexandra|Alexandra]] → target = "People/Alexandra", display = "Alexandra"
```

When extracting wikilinks programmatically, always split on `|` first and use only the first segment as the link target.

**Bare names `[[overview]]` are ambiguous** across a large vault — many folders may have their own `overview.md`. Always use the full relative path for disambiguation:

```
✅ [[Projects/liquidity-pulse/overview]]
❌ [[overview]]   (points to wrong file or breaks entirely)
```

**Broken link audit pattern** — use this to find broken wikilinks across the entire vault:

```python
#!/usr/bin/env python3
import os, re
from collections import Counter, defaultdict

vault = "/home/thomas/Desktop/Memory"
wikilink_re = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]')

# Build case-insensitive file index (preserve actual paths)
files = {}
for root, dirs, fnames in os.walk(vault):
    for f in fnames:
        if f.endswith('.md'):
            full = os.path.join(root, f)
            rel = os.path.relpath(full, vault)
            files[rel.lower()] = rel

def find_target(link):
    link = link.strip()
    # Try exact
    if link in files: return files[link]
    if (link + '.md') in files: return files[link + '.md']
    if (link + '/index.md') in files: return files[link + '/index.md']
    return None

broken_by_file = defaultdict(list)
total = broken = 0

for root, dirs, fnames in os.walk(vault):
    for fname in fnames:
        if not fname.endswith('.md'): continue
        full = os.path.join(root, fname)
        rel = os.path.relpath(full, vault)
        with open(full, errors='ignore') as f:
            content = f.read()
        for link in wikilink_re.findall(content):
            total += 1
            if find_target(link) is None:
                broken += 1
                broken_by_file[rel].append(link)

print(f"Total: {total}, Broken: {broken} ({broken/total*100:.1f}%)")
print(f"Files with broken links: {len(broken_by_file)}")
for fpath, links in sorted(broken_by_file.items(), key=lambda x: -len(x[1]))[:20]:
    print(f"  [{len(links):3d}] {fpath}")
```

---

## Vault Pattern Mining — surface the shape of the corpus

After 1+ years of a vault, the writer usually cannot answer "what is this corpus actually about?" — because the answer is structural, not topical. This subsection covers the pattern-analysis + theme-site + structural-fix loop that produces a multi-page static website (one page per emerging theme) and optionally implements the prescriptive fixes.

**When to use:** "find patterns in my notes", "what's hiding in my vault", "analyze my Obsidian", "hidden patterns", "themes in my writing", "surface what my notes actually say", "build a site from my notes", "what the vault would need to look different", "fix the empty containers", "fix the tag explosion", "implement the [theme N] fix".

**When NOT to use:** the user wants to retrieve a specific fact from the vault (use the read/search sections above), generate a new research vault (use `deep-research-obsidian`), or build a single static diagram of a system (use `architecture-diagram`). Below ~50 notes, pattern detection has too little volume — just open the files.

### What the analysis surfaces

- **Hub notes** (most-linked-to files = the gravitational center of a cluster)
- **Tag taxonomy decay** (the same concept written N ways until retrieval fails)
- **Schema drift** (frontmatter conventions that diverged without anyone noticing — bilingual, multi-era, multi-source corpora)
- **Content-vs-template gaps** (places where the *shape* of a note exists but the *substance* never got written) — see the "Empty-container pattern" section above for the dedicated fix
- **Cross-domain bridges** (notes that connect otherwise-separate clusters)
- **Identity-level patterns** (what the writer argues with themselves about — opposition-rich notes, first-person vs. third-person, recurring self-instruction)

Output is a multi-page static website, one page per emerging theme, with data visualizations (bar charts, tables, hub lists, timelines) and direct quotes from the source notes as evidence. The site is meant to be read top-to-bottom: index gives the shape, each theme page goes deep.

### Workflow (6 phases + optional Phase 7 fix)

#### Phase 1 — Inventory walk

Walk the vault, count by top-level folder, skip `.git`/`.obsidian`/`.trash`/node_modules. Report shape before analyzing.

```bash
cd /home/thomas/Desktop/Memory  # or wherever
find . -name "*.md" -not -path "./.git/*" -not -path "./.obsidian/*" -not -path "*/.obsidian/*" -not -path "*/pages/*" | wc -l
# (note: many vaults put leaf content under pages/ — count that too)
find . -name "*.md" -not -path "./.git/*" -not -path "./.obsidian/*" | wc -l
```

**Pitfall:** Leaf notes are often inside `pages/` or `_Lot*_*` subfolders, not at the cluster root. The first count is misleading. Use the second.

#### Phase 2 — Parse frontmatter

Most personal vaults have frontmatter, but the schema drifts over time and across languages. Build a parser that handles BOTH strict YAML and loose fallback. The bundled analyzer `scripts/analyze_vault.py` is the generalized version of the 2026-06-02 run — edit the `VAULT` constant at the top, then:

```bash
uv run --with pyyaml python3 scripts/analyze_vault.py
```

Outputs go to `/tmp/vault_analysis/summary.json` and `notes.json`. The script handles bilingual frontmatter, loose YAML, empty `strong_links` entries, and skips `.git`/`.obsidian`/`.trash`/`node_modules` by default.

Key fields to extract per note:
- `title`, `type`, `cluster`, `importance`
- `tags` (as a list — handle `[a, b]` AND `a, b` AND YAML list blocks)
- `strong_links` / `liens_forts` / equivalent (the per-note link field, regardless of language)
- `opposition_links` / `liens_opposition` / equivalent
- `sources_count` (signal of web-research vs. internal-summary)
- `word_count` of body

**Pitfall:** Bilingual vaults have TWO different schemas. The 2026-06-02 vault had `strong_links` (English) and `liens_forts` (French). Treat them as the same field, with a per-language key map. Same for `title`/`titre`, `created`/`créé`, etc. **Gating check:** if the parser silently produces `None` for the link field on more than 20% of notes, you have a schema-drift problem and Phase 2 must be reworked before any of Phase 3 makes sense.

**Pitfall:** Some `strong_links` entries are `[]` or `['']`. Guard with `if not link: continue` before indexing. The first run of the analyzer crashed on this exact bug.

#### Phase 3 — Pattern detection (the 7 lenses)

Apply these analyses in order. Each one tends to surface one or more themes:

1. **Tag frequency distribution.** Top 40 tags. Shape of the tail: how many singletons? 1,228 of 1,585 tags appearing exactly once is a tell. Tag-frequency > 50, > 20, > 10, > 5, > 2, == 1.
2. **Note-type and cluster breakdown.** What kinds of notes exist (concept/sector/company/methodology/...) and which clusters dominate?
3. **Hub detection (in-degree).** For each note, count how many `strong_links` from other notes point at it. Top 25 is the hub structure. A single note with 79+ inbound links is the gravitational center of a cluster.
4. **Cross-domain bridges.** Edges where source-cluster ≠ target-cluster. These are the most informative — they show which notes connect otherwise-separate parts of the corpus.
5. **Opposition density.** Notes with the highest count of `opposition_links` are the most-contested. In a personal corpus, this is often where the writer is arguing with themselves — high opposition density = expert-level self-awareness of where the field is wrong.
6. **Bilingual content sampling.** Read 5-10 notes from each cluster. Look for register differences: first vs. third person, present vs. past tense, prescriptive vs. descriptive, language distribution. The 2026-06-02 vault split cleanly: English = encyclopedic third-person, French = first-person emotional.
7. **Empty-container check.** Walk the directory tree for files matching known "container" patterns (e.g., `Conversations/YYYY/YYYY-MM/YYYY-MM-DD.md` with the same template). Count files where the template is present but the body is empty. This is often the most striking finding.

#### Phase 4 — Theme selection (5-8 themes)

Patterns from Phase 3 cluster into themes. Each theme must have:
- **Quantitative evidence** (a number, a chart, a ranking)
- **Qualitative evidence** (at least one direct quote from a source note)
- **A reading** (what it means — not just what the data shows, but what it suggests)
- **A "what the vault would need to look different"** section (the prescriptive payoff)

Order themes by signal strength, not chronology. The 2026-06-02 ordering was:
1. Core narrative (highest signal — explains the rest)
2. Structural (how the vault is shaped)
3. Deep research (the most-engineered cluster)
4. Emotional core (the writer's relationship to their work)
5. Taxonomy decay (technical debt)
6. Identity (longest-running tension)
7. Observability (the meta-finding — usually saved for last because it explains why the other findings exist)

#### Phase 5 — Build the site

**Architecture:**
```
/path/to/output/
├── index.html              (hero + stat block + 7 theme cards)
├── themes/
│   ├── 01-theme-name.html
│   ├── 02-theme-name.html
│   └── ...
└── assets/
    ├── style.css           (one file, all themes inherit)
    └── app.js              (IntersectionObserver scroll animations)
```

**Design language:** Dark editorial. Recommended:
- Background `#0a0b0d`, ink `#e8eaf0`, dim `#8a8f9e`
- One accent color per theme, defined as `--theme-accent` in each page's `<style>` block
- Serif: Fraunces (300/400 weight, italic for emphasis)
- Sans: Inter (300/400/500)
- Mono: JetBrains Mono (for stat numbers, tag clouds, code)
- Sticky nav, blurred backdrop
- Hero with stat block, then per-theme page with hero + body + source-notes tag cloud
- Footer with prev/next theme link

The bundled `templates/pattern-site-theme.html` is the per-theme-page starter (nav, hero, lede pull-quote, body with data viz blocks, two-column comparisons, source-notes tag cloud, prev/next footer). Replace `{{TEMPLATE_VARS}}` and the body content per theme.

**Data viz primitives:**
- `.bars` — vertical bar chart with animated fill on scroll
- `.hubs` — grid of hub notes with staggered fade-in
- `.timeline` — left-rail vertical timeline with dot markers
- `table` — for raw data dumps
- `.pull` — large editorial pull-quote
- `.tag-cloud` — pill list with `.alt` variant for highlighted tags

**Animation:** IntersectionObserver. When a section enters viewport, add `.visible` class, which triggers CSS transitions on `.bar-fill` (animates `width`), `.hub` (staggered fade), and `.observe` blocks (fade + slide up).

**Critical:** Before telling the user the site is ready, run the verification protocol:

```bash
# 1. Start server with background=true (NOT nohup — that gets blocked)
#    in one tool call
# 2. In a separate tool call, run the curl checks
sleep 1
for path in /index.html /themes/01-...html /assets/style.css /assets/app.js; do
  curl -s -o /dev/null -w "$path: %{http_code}  Size: %{size_download}\n" \
    http://localhost:PORT$path
done
# 3. Stability check after 5s
sleep 5
curl -s -o /dev/null -w "stable: %{http_code}\n" http://localhost:PORT/index.html
# 4. HTML structure sanity: each page should have 1 DOCTYPE, ≥1 stylesheet ref, </html> close
```

**Pitfall — background process:** Use `terminal(background=true, notify_on_complete=false)` for the server. Do NOT use `nohup ... &` in foreground mode — Hermes blocks shell-level background wrappers. Long-lived servers are silent; that's correct.

**Pitfall — DO render check:** A `curl` returning 200 with non-zero size is NOT the same as the page actually rendering. If browser tools are available, use `browser_navigate` to confirm. If browser tools time out (60s), that's a tool issue not a server issue — verify with curl and process polling.

#### Phase 6 — Publish (push to private GitHub repo + deploy to Vercel)

After the user says "push to a private repo" or "publish to Vercel" (or both), do the GitHub side first, then Vercel. **Full step-by-step including all observed pitfalls lives in `references/pattern-site-deploy-recipe.md`** — read that file before deploying. The condensed version:

1. **GitHub:** `git init -b main` → `git add -A` → `git commit -m "Initial site: ..."` → `gh repo create <name> --private --source=. --remote=origin --description "..." --push`. Verify with `gh repo view <name> --json name,visibility,url` (must show `"PRIVATE"`).
2. **Vercel CLI:** `npm install -g vercel`. Binary lands at `/home/thomas/.local/lib/nodejs/node-v22.x.x-linux-x64/bin/vercel` — not on PATH automatically; `export PATH="..."` at the start of each session.
3. **CRITICAL first step — unset the env-var token trap:** `unset VERCEL_TOKEN`. The `~/.bashrc` exports a token that is often a *literal placeholder* (`vcp_6N...DljE` with real `...` in the middle, or a redacted string with `*`s). If unset is skipped, the CLI silently reads it and fails with confusing "scope"/"invalid token"/"must not contain *" errors, and the device-flow prompt never appears. Always unset.
4. **Device-flow login:** `vercel login <email>`. The CLI prints a URL like `https://vercel.com/oauth/device?user_code=XXXX-YYYY`. **Hand that URL + code to the user and wait for them to click Verify.** Run in background with `notify_on_complete=true` and `process(action='wait')` to block. Codes expire in ~5 minutes — re-run if the user is AFK.
5. **Deploy:** `cd /path/to/site && vercel deploy --yes --prod`. Watch for `▲ Production  https://<name>-<hash>-<scope>.vercel.app` and `▲ Aliased  https://<name>.vercel.app`. Both should resolve to the same deployment. Accept the GitHub auto-deploy prompt.
6. **Verify:** curl all paths (`/`, every theme page, both assets), expect 200 + non-zero size. Re-check after 3s. Don't trust "Ready" without curl confirmation.
7. **Cleanup:** kill the local dev server (`process(action='kill', session_id=...)`) so port 8765 doesn't stay bound.

The full pitfall table (env-var trap, `*` glob expansion, browser timeouts on localhost, wrong team scope, `gh` name collisions, build-hangs from stuck tokens) is in `references/pattern-site-deploy-recipe.md` § 3.

### Anti-patterns to avoid

- **Don't analyze without inventorying first.** A pattern detector running blind on 1,137 files will surface noise. Inventory gives the lay of the land and prevents you from over-indexing on a single cluster.
- **Don't surface themes without evidence.** Every theme needs a chart, a table, a quote, or a count. A theme is "the corpus says X" — without data, it's "I felt like X."
- **Don't skip the bilingual/multi-schema check.** Half of personal vaults are written in two eras, two languages, or two contexts. A single-schema parser will silently lose half the corpus.
- **Don't build the site before the themes are written.** Theme pages are evidence-driven. If the evidence isn't there, the theme isn't there. Better to ship 4 strong themes than 7 weak ones.
- **Don't render the site through Markdown-to-HTML converters.** The visual system is bespoke. Hand-write the HTML. md-to-webpage will produce something legible but uninspiring.
- **Don't open the browser to "verify" the site rendered correctly if it might time out.** Curl + process status is the actual verification. Browser is the polish check, not the gate.

#### Phase 7 — Implement the structural fixes (the payoff path)

The site/analysis is the diagnosis. The structural fix is the cure. Most users who get the analysis will next ask "now implement the fix" — typically by quoting the analysis's "What the vault would need to look different" section verbatim.

**Triggers for Phase 7:**
- "implement the [theme] fix" / "fix the [theme]"
- "what the vault would need to look different" (quoting the analysis template)
- "make the empty containers not empty"
- "fix how we store conversations" / "fix the tag explosion"
- "do the 3-pass fix" / "consolidate the taxonomy"
- "now actually fix it" (after a Phase 5 site was built)

**The fix-implementation loop has 4 sub-steps, repeated per theme** — see `references/pattern-fix-implementation.md` for the full pattern: read the prescriptive section, map the fix to the right layer (skill / frontmatter / content), write the fix as an idempotent migration script (must produce 0 changes on a second run), verify by re-running the analyzer.

The 2026-06-02 Memory vault ran 3 separate fix passes (themes 05, 07, and the meta-finding `AI/empty-containers-fix.md`) before re-running the analyzer to confirm. Theme 07 in particular hits the **Empty-container pattern** section above — that's the same fix at the skill layer (`save-session-to-obsidian` v1.4+ auto-detects decisions).

### Worked output (concrete)

The 2026-06-02 run on the Memory vault produced:
- 1 index page (8.9 KB)
- 7 theme pages (10–15 KB each)
- 1 shared CSS (12.9 KB), 1 shared JS (0.7 KB)
- 7 emerging themes, each with: quantitative evidence, qualitative quotes, a reading, a prescriptive "what the vault would need to look different" section, and a source-notes tag cloud
- Total: 8 HTML files, 1 CSS, 1 JS, all returning 200 with stable load
- Published: private GitHub repo (`vault-hidden-patterns`) + Vercel production (`https://vault-patterns.vercel.app`), auto-deploy wired

The themes surfaced:
1. The Builder in Search of an Exit (32 projects, ~21 empty)
2. The Bilingual Knowledge Architect (2 schemas, 2 languages, 2 cognitive registers)
3. The Semiconductor Obsession (1 hub note with 79 inbound links)
4. The Trader Fighting Himself (357 trading-bots notes, mostly about not being human)
5. The 1,585-Tag Explosion (77% of unique tags appear exactly once)
6. The PM Who Wants to Stop PM-ing (the most complete corpus = the field he wants to escape)
7. The Empty Containers (17/17 conversation files with "Log: [empty]")

### Pitfall — long-running deploy process leaks stale state

After Vercel auth via device flow, the login subprocess runs in the background. If the parent session restarts or the login is killed mid-flight, an old `Background process completed` notification may arrive *after* the deploy has succeeded. Don't mistake the late notification for a fresh failure — verify with `gh repo view` and `curl` on the production URL, not by reading the stale process log.

**Tells:** process notification has exit_code=-15 (SIGTERM) or `-9` (SIGKILL), AND the deploy URL is already 200, AND `git log` shows the push commit. The session is fine; the notification is post-hoc.

(See Phase 6 / `references/pattern-site-deploy-recipe.md` for the deploy side; this pitfall is the
"the deploy is done but the terminal notification says otherwise" failure mode.)
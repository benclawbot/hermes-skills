---
name: obsidian
description: Read, search, and create notes in the Obsidian vault. Also covers vault-based skill management; import vault skill notes into Hermes callable skills; audit for broken links after vault moves; manage vault git backup; fix empty-container patterns (templates that record events but never record decisions) by identifying the must-be-non-empty section, auto-seeding it, and curating manually.
version: 1.2.0
metadata:
  hermes:
    tags: [obsidian, note-taking, vault, skills, backup, empty-container]
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

## Application Launch (Linux / Snap)

Obsidian is installed as a Snap package on Thomas's machine. If the app fails to start, use this troubleshooting path.

### Failure Mode A — GPU crash (classic Haswell)
**Symptoms:** Window appears then crashes immediately, or `GPU process isn't usable. Goodbye.` in stderr.

**Root cause:** Haswell integrated GPU has incomplete Vulkan support. The iHD VAAPI driver (`iHD_drv_video.so`) fails and the Chromium GPU process crashes before the window renders.

**Fix — GPU flags:**
```bash
snap run obsidian --disable-gpu --disable-software-rasterizer
```
- `--disable-gpu` — disable GPU hardware acceleration
- `--disable-software-rasterizer` — disable SwiftShader fallback (prevents secondary crash)

### Failure Mode B — Snap exits silently (current, May 2026)
**Symptoms:** `snap run obsidian` exits with code 1 and no window, no error output. The process runs for ~1 second then dies.

**Root cause:** Snap environment or confinement issue — not a GPU crash. The `--disable-gpu` wrapper no longer helps because the snap launcher itself is broken in this environment.

## Failure Mode B — Snap Exits Silently (May 2026)

`snap run obsidian` exits with code 1, no window, no error output. Process dies cleanly in ~1 second. No GPU crash message.

**Root cause:** Snap environment/confinement breakage — not a GPU issue. GPU flags no longer help. The snap binary itself cannot launch the Electron process.

**Fix — Replace snap with official .deb extract:**

> The `.tar.gz` asset does not exist in the GitHub releases. Use the `.deb` package and extract it — no dpkg install needed.

```bash
# 1. Remove snap (requires sudo)
sudo snap remove obsidian

# 2. Download official .deb
cd /tmp
curl -L https://github.com/obsidianmd/obsidian-releases/releases/download/v1.12.7/obsidian_1.12.7_amd64.deb -o obsidian.deb

# 3. Extract deb (no dpkg install — just unpack)
mkdir -p obsidian_extract
dpkg-deb -x obsidian.deb obsidian_extract
sudo rm -rf /opt/obsidian
sudo mv obsidian_extract/opt/Obsidian /opt/obsidian

# 4. Fix old snap desktop shortcut left on desktop
rm -f ~/Desktop/obsidian_obsidian.desktop

# 5. Wrapper (preserves --disable-gpu for GPU stability on Haswell)
#    Binary name is lowercase 'obsidian', not 'Obsidian'
cat > ~/.local/bin/obsidian << 'EOF'
#!/bin/bash
exec /opt/obsidian/obsidian --disable-gpu "$@"
EOF
chmod +x ~/.local/bin/obsidian

# 6. Desktop entry
#    Icon path is resources/icon.png, not resources/obsidian.png
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

# 7. Pin to desktop
cp ~/.local/share/applications/obsidian.desktop ~/Desktop/obsidian.desktop
chmod +x ~/Desktop/obsidian.desktop
```

**Three critical path corrections vs older docs:**
- Binary: `/opt/obsidian/obsidian` (all-lowercase) — extracted directory is `Obsidian` (capital O) but the executable inside is `obsidian`
- Icon: `resources/icon.png` — not `resources/obsidian.png`
- GPU flag: `--disable-gpu` still needed on Haswell even with the direct install
> **GPU flag:** `--disable-gpu` is still needed on this Haswell system even with the tarball install.

### Verification
```bash
ps aux | grep obsi | grep -v grep
# Should show: obsidian (main), obsidian --type=zygote, obsidian --type=renderer
# If only the bash wrapper shows, the app crashed — try with --in-process-gpu
```

See `references/app-launch-troubleshooting.md` for reproduction commands and extended diagnostics.

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

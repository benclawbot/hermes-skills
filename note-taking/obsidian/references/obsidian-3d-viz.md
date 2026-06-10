# Obsidian 3D Link Graph Visualization

Builds an interactive 3D force-directed graph of vault links using Three.js.

## When to use

Thomas asks to "visualize my vault links", "show me the graph of my notes", "make a 3D map of my knowledge base", or similar.

## Current implementation (May 2026 — verified working)

The visualization was built as a single in-session Python script, not from a pre-existing file.

### How to rebuild after vault changes

Run the full pipeline as a Python script:

```python
import os, re, yaml, json, math, random
from collections import defaultdict

vault = '/home/thomas/Desktop/Memory'

# 1. Parse vault files
wikilink_re = re.compile(r'\[\[([^\]]+)\]\]')
mdlink_re = re.compile(r'\[([^\]]*)\]\(([^\)]+)\)')

files = []
for root, dirs, filenames in os.walk(vault):
    if '.obsidian' in root: continue
    for fn in filenames:
        if fn.endswith('.md'):
            fpath = os.path.join(root, fn)
            content = open(fpath, errors='ignore').read()
            title = os.path.splitext(fn)[0]
            if content.startswith('---'):
                try:
                    fm = yaml.safe_load(content.split('---',2)[1])
                    if fm and isinstance(fm, dict) and 'title' in fm:
                        title = str(fm['title'])
                except: pass
            relpath = os.path.relpath(fpath, vault)
            folder = relpath.split('/')[0]
            files.append({'path': fpath, 'relpath': relpath, 'title': title, 'folder': folder, 'content': content})

# 2. Build link graph
title_to_idx = {f['title'].lower(): i for i, f in enumerate(files)}
idx_to_path = {i: f['relpath'] for i, f in enumerate(files)}

edges = []; broken = []
for i, f in enumerate(files):
    for wl in wikilink_re.findall(f['content']):
        tgt_raw = wl.split('|')[0].split('#')[0].strip()
        tgt_lower = tgt_raw.lower()
        if tgt_lower in title_to_idx:
            edges.append({'src': i, 'tgt': title_to_idx[tgt_lower]})
        else:
            broken.append({'src': i, 'tgt_name': tgt_raw})

# 3. Extract preview (first 200 chars, strip wikilinks/markdown)
def get_preview(content):
    text = re.sub(r'\[\[([^\]|]*?)(?:\|[^\]]*)?\]\]', r'\1', content)
    text = re.sub(r'\[([^\]]*)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'#{1,6} ', '', text)
    text = re.sub(r'[*_`~>-|]', '', text)
    text = re.sub(r'\n+', ' ', text).strip()
    return text[:200]

# 4. Force-directed layout (Barnes-Hut, 100 iterations)
N = len(files)
adj = [[] for _ in range(N)]
for e in edges: adj[e['src']].append(e['tgt'])

for e in edges:
    s, t = e['src'], e['tgt']
    adj[s].append(t); adj[t].append(s)

pos = [[random.random()-0.5, random.random()-0.5, random.random()-0.5] for _ in range(N)]
for _ in range(100):
    forces = [[0,0,0] for _ in range(N)]
    for i in range(N):
        for j in range(N):
            if i == j: continue
            dx, dy, dz = pos[j][0]-pos[i][0], pos[j][1]-pos[i][1], pos[j][2]-pos[i][2]
            dist = math.sqrt(dx*dx+dy*dy+dz*dz) + 1e-9
            f = 60 / (dist * dist)
            forces[i][0] -= dx/dist*f; forces[i][1] -= dy/dist*f; forces[i][2] -= dz/dist*f
    for i in range(N):
        for j in adj[i]:
            dx, dy, dz = pos[j][0]-pos[i][0], pos[j][1]-pos[i][1], pos[j][2]-pos[i][2]
            dist = math.sqrt(dx*dx+dy*dy+dz*dz) + 1e-9
            f = 0.008 * dist
            forces[i][0] += dx/dist*f; forces[i][1] += dy/dist*f; forces[i][2] += dz/dist*f
        # central gravity
        forces[i][0] -= pos[i][0] * 0.003
        forces[i][1] -= pos[i][1] * 0.003
        forces[i][2] -= pos[i][2] * 0.003
    for i in range(N):
        pos[i][0] += forces[i][0] * 0.87
        pos[i][1] += forces[i][1] * 0.87
        pos[i][2] += forces[i][2] * 0.87

# normalize to [-50, 50]
mx, my, mz = max(abs(p[0]) for p in pos), max(abs(p[1]) for p in pos), max(abs(p[2]) for p in pos)
m = max(mx, my, mz, 1)
for p in pos: p[0] *= 50/m; p[1] *= 50/m; p[2] *= 50/m

# 5. Build nodes + orphan detection
orphans = []
for i, f in enumerate(files):
    has_links = any(e['src']==i or e['tgt']==i for e in edges)
    if not has_links: orphans.append(i)

nodes = []
for i, f in enumerate(files):
    in_deg = sum(1 for e in edges if e['tgt']==i)
    out_deg = sum(1 for e in edges if e['src']==i)
    nodes.append({'id': i, 'title': f['title'], 'folder': f['folder'], 'relpath': f['relpath'],
                  'degree': in_deg+out_deg, 'orphan': i in orphans,
                  'x': pos[i][0], 'y': pos[i][1], 'z': pos[i][2],
                  'preview': get_preview(f['content'])})

# 6. Output as self-contained HTML
graph_json = json.dumps({'nodes': nodes, 'edges': edges, 'broken': broken, 'orphans': orphans}, separators=(',', ':'))
# (Then embed this JSON into the HTML template with: const GRAPH = <json>; )
```

Output: `~/vault_3d_viz.html` — ~1.5 MB, self-contained. No server needed after generation. Open directly in Chrome/Firefox/Safari.

## What it extracts

- **Wikilinks** `[[note]]` and `[[note|alias]]` — alias stripped for resolution
- **Markdown links** `[text](path.md)` — non-http relative paths only
- **Frontmatter `title:`** field — overrides filename when present
- Classifies each link as **resolved** or **broken**

## Graph stats (Thomas's vault, May 2026)

| Metric | Value |
|--------|-------|
| Total files | 1126 |
| Connected nodes | 881 |
| Resolved edges | 10,010 |
| Broken links | 3,961 |
| Orphan notes | 12 |

## Layout algorithm

Pre-computed Barnes-Hut force-directed layout (100 iterations, Python) → positions normalized to [-50, 50] per axis → embedded as `x, y, z` in each node object.

**Why pre-compute?** Browser-side force layout stutters on 500+ nodes. Pre-computing means the browser loads positions directly with zero layout computation. Takes ~15s on 881 nodes — acceptable for one-time generation.

**Parameters:** repulsion=60, attraction=0.008, damping=0.87, central gravity=0.003.

## Three.js rendering architecture

- **881 nodes** → single `THREE.InstancedMesh` (one draw call). Per-instance color for folder color coding.
- **Edges** → two `THREE.LineSegments` objects: solid gray for normal edges, coral (`#E07A4F`) for bidirectional edges.
- **Broken links** → `THREE.LineDashedMaterial` in red, from source to a small random offset (target doesn't exist).
- **Labels** → HTML `<div>` overlays (not Three.js sprites) for crisp text at any zoom level. Only high-degree nodes labeled.
- **Controls** → OrbitControls with LEFT=rotate, MIDDLE=zoom, RIGHT=pan.

## Interaction features

| Feature | Trigger | Result |
|---------|---------|--------|
| Click node | Left-click | Info panel: title, folder, path, in/out link counts, preview |
| Double-click | Left-dblclick | Opens note via `file://` URL in default editor |
| Focus | Button in info panel | Isolates connected subgraph |
| Hide | Button in info panel | Removes single node from graph |
| Search | Type in search bar | Highlights matching nodes (white), dims others |
| Folder filter | Checkbox toggles | Show/hide per-folder nodes |
| Min degree | Slider | Hide nodes below N connections |
| Bidir toggle | Checkbox | Show/hide bidirectional edge highlighting |
| Broken toggle | Checkbox | Show/hide broken link indicators |

**Keyboard shortcuts:** `F`=search · `R`=reset view · `M`=minimap · `?`=help · `Esc`=close panel

## Folder color reference

| Folder | Color |
|--------|-------|
| Projects | `#9E4AE8` (purple) |
| Research | `#00B0F0` (blue) |
| AI | `#E07A4F` (coral) |
| Active Context | `#5B9BD5` (light blue) |
| Conversations | `#70AD47` (green) |
| People | `#FFC000` (yellow) |

### 2. InstancedMesh With `instanceColor` But No `vertexColors: true`

**Symptom:** InstancedMesh creates successfully, nodes exist in scene at correct positions, but all render as the same color or invisible against dark background.

**Root cause:** `MeshStandardMaterial` without `vertexColors: true` ignores per-instance colors. Nodes all render as the material's base color (dark) against dark background — invisible.

**Fix:**
```javascript
const mat = new THREE.MeshStandardMaterial({ 
  vertexColors: true,  // ← REQUIRED for instanceColor
  roughness: 0.35, 
  metalness: 0.45 
});
const nodeIM = new THREE.InstancedMesh(geo, mat, N);
```

### 3. Force Render After Scene Build But Before Showing App

**Symptom:** Progressive loader fetches JSON, builds InstancedMesh, but canvas stays black until user interacts (or never shows).

**Root cause:** THREE.js renderer requires explicit `.render(scene, camera)` call after scene objects are added to actually display anything. Browser doesn't auto-render just because nodes were added to scene.

**Fix:** Call renderer.render() immediately after scene.add and BEFORE hiding loading screen:
```javascript
scene.add(nodeIM);
renderer.render(scene, camera);  // ← NOW
document.getElementById('loading-screen').style.display = 'none';
```

Also: always start the render loop via `requestAnimationFrame(animate)` immediately after init, even before data loads.

### 4. Headless Chromium WebGL Renders Blank (Unreliable for WebGL QA)

**Symptom:** Code works in real Chrome/Firefox but headless shows entirely black canvas. Not a JS error — WebGL context creates successfully but context is software-rendered (SwiftShader) and returns no pixels.

**Fix:** Test in real browser desktop session. For headless: verify DOM loaded (`app` div visible, loading screen hidden) via `--dump-dom`, not WebGL pixel verification. For WebGL specifically, do visual QA in a real browser.

### 5. Canvas Sets Size From clientWidth/clientHeight Before Renderer Initializes

**Symptom:** Renderer creates canvas at 0×0 size, canvas appears nothing because has zero dimensions.

**Root cause:** `renderer.setSize(w(), h())` called with `canvas.clientWidth` returning 0 because canvas CSS hasn't been applied yet, or canvas is hidden behind loading screen.

**Fix:** Ensure canvas is visible and DOM-reflowed before calling renderer.setSize:
```javascript
renderer.setSize(canvas.clientWidth, canvas.clientHeight);  // AFTER CSS applied
```
Better: use explicit pixel dimensions or defer renderer.setSize until after loading screen starts hiding.

---

## Headless browser testing

**WebGL blank in headless Chromium** — expected. Headless Chrome has no GPU, so WebGL canvas renders as blank even when the Three.js engine is fully initialized and the app is running correctly. Use `--dump-dom` to verify app loaded (app div visible, loading screen hidden, canvas has `data-engine="three.js r160"`), but screenshot will always show blank.

Verification command:
```bash
chromium --headless=new --no-sandbox --use-gl=swiftshader --dump-dom "file:///path/to/vault_3d_viz.html" | python3 -c "import sys; h=sys.stdin.read(); print('App loaded:', 'id=\"app\"' in h); print('Three.js:', 'three.js' in h); print('Canvas:', '<canvas' in h)"
```

## Known limitations

- **Double-click**: Opens via `file://` URL in system default editor, not Obsidian specifically. No client-side Obsidian URI scheme without a native app bridge.
- **Broken link targets**: Dashed red lines terminate at a small random offset near the source node (target note doesn't exist).
- **Markdown links**: Only `.md` relative paths tracked; full URLs ignored.
- **Large vaults (>2000 nodes)**: Consider reducing layout iterations or using NetworkX's `spring_layout`.

## Broken link analysis (Thomas's vault, May 2026)

Graph stats at generation time: 881 nodes, 10,010 edges, **3,961 broken links (39.5%)**, 12 orphans.

**Root cause — case sensitivity mismatch:** Obsidian resolves links case-insensitively on the filesystem (so `[[people/alexandra]]` finds `People/Alexandra.md`), but the graph parser captures the raw wikilink text before resolution. The broken link list is dominated by lowercase `people/` paths (alexandra, noah, jack, thomas) that don't match the actual `People/` folder case. This is not a real broken link in Obsidian's UI — it's an artifact of the parser recording raw wikilink text.

**Secondary pattern:** scattered old project references to deleted or moved notes.

**Fix strategy:** Run the cross-folder link building rules in the parent SKILL.md first (folder anchoring, same-folder links before cross-folder), then re-run the graph. Real broken links from deleted notes will persist; case-mismatch artifacts improve as vault link structure improves. Do NOT try to programmatically fix case in wikilinks — Obsidian handles resolution correctly; the graph parser just captures raw text.
#!/usr/bin/env python3
"""
vault_3d_viz.py — Generate a self-contained 3D Obsidian vault link graph.

Outputs: ~/vault_3d_viz.html (1.3 MB, embeds all graph data)

Usage:
    python3 ~/.hermes/skills/note-taking/obsidian/scripts/generate_vault_3d.py

Thomas's vault: ~/Desktop/Memory
"""
import os, re, json, math, random
from collections import Counter

# ── Config ───────────────────────────────────────────────────────────────────
VAULT = os.path.expanduser("~/Desktop/Memory")
OUT_HTML = os.path.expanduser("~/vault_3d_viz.html")
GRAPH_JSON = "/tmp/vault_graph_full.json"

# ── Parse vault ──────────────────────────────────────────────────────────────
wikilink_re = re.compile(r'\[\[([^\]]+)\]\]')
mdlink_re = re.compile(r'\[([^\]]*)\]\(([^\)]+\.md)\)')

files = []
for root, dirs, filenames in os.walk(VAULT):
    if '.obsidian' in root or '__MACOSX' in root:
        continue
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
                import yaml
                fm = yaml.safe_load(content.split('---',2)[1])
                if fm and isinstance(fm, dict) and 'title' in fm:
                    title = str(fm['title'])
            except:
                pass
        rel = fpath.replace(VAULT+'/', '')
        folder = rel.split('/')[0] if '/' in rel else 'root'

        wl_links = []
        for l in wikilink_re.findall(content):
            base = l.split('|')[0].split('#')[0].strip()
            wl_links.append(base.lower())

        ml_links = []
        for alias, path in mdlink_re.findall(content):
            if not path.startswith('http'):
                ml_links.append(os.path.splitext(os.path.basename(path))[0].lower())

        file_info[fpath] = {
            'title': title, 'folder': folder, 'relpath': rel,
            'wikilinks': wl_links, 'mdlinks': ml_links,
        }
    except:
        pass

print(f"Parsed {len(file_info)} notes")

# ── Build graph ─────────────────────────────────────────────────────────────
title_map = {info['title'].lower(): info for info in file_info.values()}

all_edges = []
for fpath, info in file_info.items():
    for link in info['wikilinks'] + info['mdlinks']:
        target = title_map.get(link)
        kind = 'resolved' if target else 'broken'
        all_edges.append({
            'type': kind,
            'src': info['title'],
            'tgt': link,
            'src_folder': info['folder'],
            'tgt_folder': target['folder'] if target else None
        })

resolved = [e for e in all_edges if e['type'] == 'resolved']
broken = [e for e in all_edges if e['type'] == 'broken']
print(f"Edges: {len(resolved)} resolved, {len(broken)} broken")

connected = set()
for e in resolved:
    connected.add(e['src'].lower())
    connected.add(e['tgt'].lower())

orphans = [info for info in file_info.values()
           if info['title'].lower() not in connected]
print(f"Orphans: {len(orphans)}")

# ── Force-directed layout ─────────────────────────────────────────────────────
involved = connected | set(o['title'].lower() for o in orphans)
node_ids = {t: i for i, t in enumerate(sorted(involved))}
N = len(node_ids)
print(f"Layout: {N} nodes")

adj = [[] for _ in range(N)]
for e in resolved:
    si = node_ids.get(e['src'].lower())
    ti = node_ids.get(e['tgt'].lower())
    if si is not None and ti is not None:
        adj[si].append(ti)
        adj[ti].append(si)

xs = [(random.random()-0.5)*80 for _ in range(N)]
ys = [(random.random()-0.5)*80 for _ in range(N)]
zs = [(random.random()-0.5)*80 for _ in range(N)]
vxs, vys, vzs = [0.0]*N, [0.0]*N, [0.0]*N

for iteration in range(100):
    fxs, fys, fzs = [0.0]*N, [0.0]*N, [0.0]*N
    cx = sum(xs)/N; cy = sum(ys)/N; cz = sum(zs)/N
    buckets = [[] for _ in range(8)]
    for i in range(N):
        ox = 1 if xs[i] >= cx else 0
        oy = 1 if ys[i] >= cy else 0
        oz = 1 if zs[i] >= cz else 0
        buckets[ox*4+oy*2+oz].append(i)

    rep = 60.0; attract = 0.008; damp = 0.87
    for bucket in buckets:
        if len(bucket) <= 1: continue
        bcx = sum(xs[i] for i in bucket)/len(bucket)
        bcy = sum(ys[i] for i in bucket)/len(bucket)
        bcz = sum(zs[i] for i in bucket)/len(bucket)
        for i in range(N):
            if i in bucket: continue
            dx = bcx-xs[i]; dy = bcy-ys[i]; dz = bcz-zs[i]
            dist = math.sqrt(dx*dx+dy*dy+dz*dz)+0.5
            f = rep/(dist*dist)*len(bucket)
            fxs[i] += dx/dist*f; fys[i] += dy/dist*f; fzs[i] += dz/dist*f

    for bucket in buckets:
        for a in range(len(bucket)):
            for b in range(a+1, len(bucket)):
                i, j = bucket[a], bucket[b]
                dx = xs[i]-xs[j]; dy = ys[i]-ys[j]; dz = zs[i]-zs[j]
                dist = math.sqrt(dx*dx+dy*dy+dz*dz)+0.1
                f = rep*0.3/(dist*dist)
                fxs[i] += dx/dist*f; fys[i] += dy/dist*f; fzs[i] += dz/dist*f
                fxs[j] -= dx/dist*f; fys[j] -= dy/dist*f; fzs[j] -= dz/dist*f

    for e in resolved:
        si = node_ids.get(e['src'].lower())
        ti = node_ids.get(e['tgt'].lower())
        if si is None or ti is None: continue
        dx = xs[ti]-xs[si]; dy = ys[ti]-ys[si]; dz = zs[ti]-zs[si]
        dist = math.sqrt(dx*dx+dy*dy+dz*dz)+0.01
        f = attract*dist
        fxs[si] += dx/dist*f; fys[si] += dy/dist*f; fzs[si] += dz/dist*f
        fxs[ti] -= dx/dist*f; fys[ti] -= dy/dist*f; fzs[ti] -= dz/dist*f

    for i in range(N):
        fxs[i] -= xs[i]*0.003; fys[i] -= ys[i]*0.003; fzs[i] -= zs[i]*0.003
        vxs[i] = (vxs[i]+fxs[i])*damp; vys[i] = (vys[i]+fys[i])*damp; vzs[i] = (vzs[i]+fzs[i])*damp
        xs[i] += vxs[i]; ys[i] += vys[i]; zs[i] += vzs[i]

    if iteration % 25 == 0:
        total_v = math.sqrt(sum(vxs[i]**2+vys[i]**2+vzs[i]**2 for i in range(N)))
        print(f"  Iter {iteration}: vel={total_v:.4f}")

print("Layout done")

def norm(v, mn, mx):
    return -50 + (v-mn)/(mx-mn)*100 if mx != mn else 0

for i in range(N):
    xs[i] = round(norm(xs[i], min(xs), max(xs)), 3)
    ys[i] = round(norm(ys[i], min(ys), max(ys)), 3)
    zs[i] = round(norm(zs[i], min(zs), max(zs)), 3)

# ── Build node/edge lists ────────────────────────────────────────────────────
in_deg = Counter()
out_deg = Counter()
for e in resolved:
    out_deg[e['src'].lower()] += 1
    in_deg[e['tgt'].lower()] += 1

folder_colors_hex = {
    'AI': '0xE07A4F', 'Active Context': '0x5B9BD5', 'Conversations': '0x70AD47',
    'People': '0xFFC000', 'Projects': '0x9E4AE8', 'Research': '0x00B0F0', 'root': '0x666666'
}
folder_colors_css = {
    'AI': '#E07A4F', 'Active Context': '#5B9BD5', 'Conversations': '#70AD47',
    'People': '#FFC000', 'Projects': '#9E4AE8', 'Research': '#00B0F0', 'root': '#666666'
}

nodes = []
for title in sorted(involved, key=lambda t: node_ids[t]):
    info = next((i for i in file_info.values() if i['title'].lower() == title), None)
    folder = info['folder'] if info else 'root'
    idx = node_ids[title]
    nodes.append({
        'id': idx, 'title': title, 'folder': folder,
        'color': folder_colors_hex.get(folder, '0x666666'),
        'x': xs[idx], 'y': ys[idx], 'z': zs[idx],
        'degree': in_deg[title] + out_deg[title],
        'relpath': info['relpath'] if info else title + '.md',
        'orphan': bool(info and info['title'].lower() in set(o['title'].lower() for o in orphans))
    })

edges_out = []
for e in resolved:
    si = node_ids.get(e['src'].lower())
    ti = node_ids.get(e['tgt'].lower())
    if si is not None and ti is not None:
        edges_out.append({'src': si, 'tgt': ti, 'src_folder': e['src_folder'], 'tgt_folder': e['tgt_folder']})

broken_out = [{'src': node_ids.get(e['src'].lower()), 'tgt_title': e['tgt'], 'src_folder': e['src_folder']}
              for e in broken if node_ids.get(e['src'].lower()) is not None]

orphan_out = [{'id': node_ids[o['title'].lower()], 'title': o['title'],
               'folder': o['folder'], 'relpath': o['relpath']} for o in orphans]

graph = {'nodes': nodes, 'edges': edges_out, 'broken': broken_out, 'orphans': orphan_out}

with open(GRAPH_JSON, 'w') as f:
    json.dump(graph, f)

print(f"Graph: {len(nodes)} nodes, {len(edges_out)} edges, {len(broken_out)} broken, {len(orphans)} orphans")

# ── Generate HTML ────────────────────────────────────────────────────────────
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Obsidian Vault — 3D Link Graph</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #0a0a0f; color: #e0e0e0; font-family: -apple-system, system-ui, sans-serif; overflow: hidden; height: 100vh; width: 100vw; }
#app { display: flex; width: 100vw; height: 100vh; }
#canvas-wrapper { flex: 1; position: relative; overflow: hidden; }
#main-canvas { display: block; width: 100%; height: 100%; cursor: grab; }
#main-canvas:active { cursor: grabbing; }
#controls { position: fixed; top: 0; left: 0; width: 280px; height: 100%; background: rgba(10,10,15,0.92); border-right: 1px solid rgba(255,255,255,0.07); display: flex; flex-direction: column; z-index: 20; overflow-y: auto; }
.ctrl-header { padding: 18px 18px 12px; border-bottom: 1px solid rgba(255,255,255,0.06); flex-shrink: 0; }
.ctrl-header h1 { font-size: 15px; font-weight: 600; color: #fff; margin-bottom: 2px; }
.ctrl-header p { font-size: 11px; color: #555; }
.ctrl-search { padding: 12px 16px; border-bottom: 1px solid rgba(255,255,255,0.05); flex-shrink: 0; }
.ctrl-search input { width: 100%; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); border-radius: 7px; padding: 8px 12px; color: #e0e0e0; font-size: 13px; outline: none; transition: border-color 0.2s; }
.ctrl-search input:focus { border-color: rgba(224,122,79,0.5); }
.ctrl-search input::placeholder { color: #555; }
.match-count { font-size: 11px; color: #666; margin-top: 5px; }
.ctrl-section { padding: 12px 16px; border-bottom: 1px solid rgba(255,255,255,0.05); flex-shrink: 0; }
.ctrl-section-title { font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; color: #555; margin-bottom: 8px; }
.folder-toggles { display: flex; flex-direction: column; gap: 5px; }
.folder-toggle { display: flex; align-items: center; gap: 8px; cursor: pointer; font-size: 13px; }
.folder-toggle input { display: none; }
.folder-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.folder-toggle span { color: #888; transition: color 0.2s; }
.folder-toggle input:checked + .folder-dot + span { color: #e0e0e0; }
.range-row { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.range-label { font-size: 12px; color: #777; width: 80px; flex-shrink: 0; }
.range-val { font-size: 11px; color: #E07A4F; width: 30px; text-align: right; flex-shrink: 0; }
input[type=range] { -webkit-appearance: none; width: 100%; height: 3px; background: rgba(255,255,255,0.1); border-radius: 2px; outline: none; }
input[type=range]::-webkit-slider-thumb { -webkit-appearance: none; width: 14px; height: 14px; background: #E07A4F; border-radius: 50%; cursor: pointer; }
.toggle-row { display: flex; align-items: center; gap: 8px; font-size: 12px; cursor: pointer; margin-bottom: 7px; }
.toggle-row input { display: none; }
.toggle-switch { width: 32px; height: 18px; background: rgba(255,255,255,0.12); border-radius: 9px; position: relative; transition: background 0.2s; flex-shrink: 0; }
.toggle-switch::after { content: ''; position: absolute; top: 3px; left: 3px; width: 12px; height: 12px; background: #888; border-radius: 50%; transition: all 0.2s; }
.toggle-row input:checked .toggle-switch { background: rgba(224,122,79,0.5); }
.toggle-row input:checked .toggle-switch::after { background: #E07A4F; transform: translateX(14px); }
.ctrl-stats { padding: 12px 16px; font-size: 11px; color: #444; line-height: 1.9; flex-shrink: 0; }
.ctrl-stats strong { color: #888; }
.ctrl-actions { padding: 12px 16px; display: flex; flex-direction: column; gap: 7px; flex-shrink: 0; }
.action-btn { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.08); border-radius: 7px; padding: 8px 14px; color: #aaa; font-size: 12px; cursor: pointer; text-align: left; transition: all 0.15s; font-family: inherit; }
.action-btn:hover { background: rgba(255,255,255,0.1); color: #e0e0e0; }
.action-btn.reset { color: #E07A4F; border-color: rgba(224,122,79,0.2); }
.action-btn.reset:hover { background: rgba(224,122,79,0.15); }
.ctrl-help { padding: 12px 16px; font-size: 11px; color: #444; margin-top: auto; flex-shrink: 0; }
.ctrl-help strong { color: #666; }
#info-panel { position: fixed; top: 20px; right: 20px; width: 280px; background: rgba(12,12,18,0.95); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 16px 18px; z-index: 30; display: none; backdrop-filter: blur(16px); }
#info-panel h3 { font-size: 14px; color: #fff; margin-bottom: 5px; word-break: break-word; }
#info-panel .info-folder { font-size: 11px; padding: 3px 8px; border-radius: 4px; display: inline-block; margin-bottom: 8px; }
#info-panel .info-meta { font-size: 12px; color: #666; margin-bottom: 4px; }
#info-panel .info-link-counts { font-size: 12px; color: #E07A4F; margin-top: 8px; }
#info-panel .info-broken-note { font-size: 12px; color: #ff6b6b; margin-top: 8px; display: none; }
#info-panel .info-actions { margin-top: 12px; display: flex; gap: 8px; flex-wrap: wrap; }
.info-btn { background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; padding: 6px 12px; font-size: 11px; color: #aaa; cursor: pointer; font-family: inherit; transition: all 0.15s; }
.info-btn:hover { background: rgba(255,255,255,0.12); color: #fff; }
.info-close { position: absolute; top: 12px; right: 14px; font-size: 18px; color: #444; cursor: pointer; }
.info-close:hover { color: #888; }
#minimap-wrapper { position: fixed; bottom: 20px; right: 20px; width: 170px; height: 130px; background: rgba(10,10,15,0.88); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; overflow: hidden; z-index: 20; display: none; backdrop-filter: blur(8px); }
#minimap-canvas { display: block; width: 100%; height: 100%; }
#minimap-viewport { position: absolute; border: 1px solid rgba(224,122,79,0.7); background: rgba(224,122,79,0.08); pointer-events: none; }
#legend { position: fixed; bottom: 20px; left: 300px; background: rgba(10,10,15,0.85); border: 1px solid rgba(255,255,255,0.07); border-radius: 10px; padding: 12px 16px; z-index: 20; backdrop-filter: blur(8px); }
#legend h4 { font-size: 10px; text-transform: uppercase; letter-spacing: 0.08em; color: #555; margin-bottom: 8px; }
.legend-row { display: flex; align-items: center; gap: 7px; font-size: 11px; color: #666; margin-bottom: 4px; }
.legend-dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }
.legend-line-solid { width: 20px; height: 2px; background: rgba(255,255,255,0.3); }
.legend-line-dashed { width: 20px; height: 2px; background: repeating-linear-gradient(90deg, rgba(255,107,107,0.6) 0, rgba(255,107,107,0.6) 4px, transparent 4px, transparent 7px); }
.legend-bidir { width: 20px; height: 2px; background: #E07A4F; opacity: 0.8; }
#settings-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7); z-index: 50; display: none; align-items: center; justify-content: center; backdrop-filter: blur(4px); }
#settings-modal { background: #141420; border: 1px solid rgba(255,255,255,0.1); border-radius: 14px; padding: 24px 28px; width: 400px; max-width: 90vw; box-shadow: 0 20px 60px rgba(0,0,0,0.5); }
#settings-modal h2 { font-size: 16px; color: #fff; margin-bottom: 4px; }
#settings-modal > p { font-size: 12px; color: #555; margin-bottom: 20px; }
.form-row { margin-bottom: 14px; }
.form-row label { display: block; font-size: 12px; color: #888; margin-bottom: 5px; }
.form-row input { width: 100%; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12); border-radius: 7px; padding: 9px 12px; color: #e0e0e0; font-size: 13px; font-family: inherit; }
.form-row input:focus { outline: none; border-color: rgba(224,122,79,0.4); }
.modal-actions { display: flex; gap: 10px; margin-top: 20px; }
.modal-btn-primary { flex: 1; background: #E07A4F; border: none; border-radius: 7px; padding: 10px; color: #fff; font-size: 13px; font-weight: 500; cursor: pointer; font-family: inherit; }
.modal-btn-secondary { flex: 1; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); border-radius: 7px; padding: 10px; color: #888; font-size: 13px; cursor: pointer; font-family: inherit; }
#loading { position: fixed; inset: 0; background: #0a0a0f; z-index: 200; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 16px; }
#loading .spinner { width: 36px; height: 36px; border: 3px solid rgba(255,255,255,0.08); border-top-color: #E07A4F; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
#loading p { font-size: 13px; color: #555; }
#loading .sub { font-size: 11px; color: #333; }
#empty-vault { position: fixed; inset: 0; background: #0a0a0f; z-index: 200; display: none; flex-direction: column; align-items: center; justify-content: center; gap: 12px; }
#empty-vault h2 { font-size: 20px; color: #fff; }
#empty-vault p { font-size: 13px; color: #555; text-align: center; max-width: 400px; }
#shortcuts { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); background: rgba(10,10,15,0.8); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 8px 18px; z-index: 20; font-size: 11px; color: #444; }
#shortcuts kbd { background: rgba(255,255,255,0.08); border-radius: 3px; padding: 1px 5px; margin: 0 2px; }
</style>
</head>
<body>
<div id="loading"><div class="spinner"></div><p>Loading vault graph…</p><p class="sub" id="loading-sub">Parsing notes</p></div>
<div id="empty-vault"><h2>No notes found</h2><p id="empty-message">The vault appears to be empty or no markdown files were found at the specified path.</p><button class="info-btn" style="margin-top:8px;" onclick="showSettings()">Open Settings</button></div>
<div id="app" style="display:none;">
  <div id="controls">
    <div class="ctrl-header"><h1>Vault Graph</h1><p id="ctrl-vault-path" title="Click to change">~/Desktop/Memory</p></div>
    <div class="ctrl-search"><input type="text" id="search-input" placeholder="Search notes…" autocomplete="off"><div class="match-count" id="match-count"></div></div>
    <div class="ctrl-section"><div class="ctrl-section-title">Folders</div><div class="folder-toggles" id="folder-toggles"></div></div>
    <div class="ctrl-section">
      <div class="ctrl-section-title">Link Depth</div>
      <div class="range-row"><span class="range-label">Min connections</span><input type="range" id="min-degree" min="0" max="20" value="0"><span class="range-val" id="min-degree-val">0</span></div>
      <div class="range-row"><span class="range-label">Max edges shown</span><input type="range" id="max-edges" min="500" max="10000" value="10000" step="500"><span class="range-val" id="max-edges-val">10000</span></div>
    </div>
    <div class="ctrl-section">
      <div class="ctrl-section-title">Display</div>
      <label class="toggle-row"><input type="checkbox" id="toggle-orphans" checked><div class="toggle-switch"></div><span>Show orphan notes</span></label>
      <label class="toggle-row"><input type="checkbox" id="toggle-broken" checked><div class="toggle-switch"></div><span>Show broken links</span></label>
      <label class="toggle-row"><input type="checkbox" id="toggle-bidir" checked><div class="toggle-switch"></div><span>Highlight bidirectional</span></label>
      <label class="toggle-row"><input type="checkbox" id="toggle-labels" checked><div class="toggle-switch"></div><span>Node labels</span></label>
      <label class="toggle-row"><input type="checkbox" id="toggle-size-degree" checked><div class="toggle-switch"></div><span>Size by connections</span></label>
      <label class="toggle-row"><input type="checkbox" id="toggle-color-folder" checked><div class="toggle-switch"></div><span>Color by folder</span></label>
    </div>
    <div class="ctrl-section"><div class="ctrl-section-title">Stats</div><div class="ctrl-stats" id="stats"></div></div>
    <div class="ctrl-actions">
      <button class="action-btn" onclick="resetCamera()">⟲ Reset View</button>
      <button class="action-btn" onclick="showMinimap()">⊟ Toggle Minimap</button>
      <button class="action-btn" onclick="showSettings()">⚙ Settings</button>
      <button class="action-btn" onclick="showHelp()">? Help &amp; Legend</button>
    </div>
    <div class="ctrl-help"><strong>Controls:</strong> Drag to orbit · Right-drag to pan · Scroll to zoom · Click node for info · Double-click to open · F to focus search</div>
  </div>
  <div id="canvas-wrapper"><canvas id="main-canvas"></canvas></div>
  <div id="info-panel"><span class="info-close" onclick="closeInfo()">×</span><h3 id="info-title"></h3><span class="info-folder" id="info-folder"></span><div class="info-meta" id="info-path"></div><div class="info-meta" id="info-links"></div><div class="info-broken-note" id="info-broken">Note: this note has broken links pointing to it</div><div class="info-actions"><button class="info-btn" id="btn-open">Open in Obsidian</button><button class="info-btn" id="btn-focus">Focus &amp; isolate</button><button class="info-btn" id="btn-hide">Hide node</button></div></div>
  <div id="minimap-wrapper"><canvas id="minimap-canvas"></canvas><div id="minimap-viewport"></div></div>
  <div id="legend"><h4>Legend</h4>
    <div class="legend-row"><div class="legend-dot" style="background:#9E4AE8"></div>Projects</div>
    <div class="legend-row"><div class="legend-dot" style="background:#00B0F0"></div>Research</div>
    <div class="legend-row"><div class="legend-dot" style="background:#E07A4F"></div>AI</div>
    <div class="legend-row"><div class="legend-dot" style="background:#5B9BD5"></div>Active Context</div>
    <div class="legend-row"><div class="legend-dot" style="background:#70AD47"></div>Conversations</div>
    <div class="legend-row"><div class="legend-dot" style="background:#FFC000"></div>People</div>
    <div class="legend-row"><div class="legend-dot" style="background:#666"></div>Orphan</div>
    <div class="legend-row"><div class="legend-line-solid"></div>Resolved link</div>
    <div class="legend-row"><div class="legend-line-dashed"></div>Broken link</div>
    <div class="legend-row"><div class="legend-bidir"></div>Bidirectional</div>
  </div>
  <div id="settings-overlay"><div id="settings-modal"><h2>Settings</h2><p>Configure your Obsidian vault path and display preferences.</p><div class="form-row"><label>Vault path</label><input type="text" id="vault-path-input" placeholder="/home/user/Vault"></div><div class="modal-actions"><button class="modal-btn-primary" onclick="applySettings()">Apply &amp; Rebuild</button><button class="modal-btn-secondary" onclick="hideSettings()">Cancel</button></div></div></div>
  <div id="shortcuts"><kbd>F</kbd> Search · <kbd>R</kbd> Reset · <kbd>M</kbd> Minimap · <kbd>Esc</kbd> Clear · <kbd>?</kbd> Help</div>
</div>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"}}</script>
<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const GRAPH = __GRAPH_DATA__;

const FOLDER_COLORS_HEX = { 'AI': 0xE07A4F, 'Active Context': 0x5B9BD5, 'Conversations': 0x70AD47, 'People': 0xFFC000, 'Projects': 0x9E4AE8, 'Research': 0x00B0F0, 'root': 0x666666 };
const FOLDER_COLORS_CSS = { 'AI': '#E07A4F', 'Active Context': '#5B9BD5', 'Conversations': '#70AD47', 'People': '#FFC000', 'Projects': '#9E4AE8', 'Research': '#00B0F0', 'root': '#666666' };

let activeFilters = new Set(Object.keys(FOLDER_COLORS_HEX));
let minDegree = 0, maxEdges = 10000, showOrphans = true, showBroken = true, showBidir = true, showLabels = true, sizeByDegree = true, colorByFolder = true;
let searchQuery = '', selectedNode = null, focusedNode = null, minimapVisible = false;

const nodes = GRAPH.nodes, edges = GRAPH.edges, brokenEdges = GRAPH.broken || [], orphans = GRAPH.orphans || [];
const N = nodes.length;
if (N === 0) { document.getElementById('loading').style.display = 'none'; document.getElementById('empty-vault').style.display = 'flex'; }

const canvas = document.getElementById('main-canvas');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setClearColor(0x0a0a0f, 1);
renderer.setSize(canvas.clientWidth, canvas.clientHeight);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0a0a0f);
const camera = new THREE.PerspectiveCamera(55, canvas.clientWidth / canvas.clientHeight, 0.1, 2000);
camera.position.set(0, 8, 70);
camera.lookAt(0, 0, 0);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; controls.dampingFactor = 0.08; controls.minDistance = 3; controls.maxDistance = 300;
controls.mouseButtons = { LEFT: THREE.MOUSE.ROTATE, MIDDLE: THREE.MOUSE.DOLLY, RIGHT: THREE.MOUSE.PAN };

scene.add(new THREE.AmbientLight(0xffffff, 0.7));
const dir1 = new THREE.DirectionalLight(0xffffff, 1.0); dir1.position.set(20, 40, 30); scene.add(dir1);
const dir2 = new THREE.DirectionalLight(0x4488ff, 0.35); dir2.position.set(-20, -10, -20); scene.add(dir2);

// Node InstancedMesh
const sphereGeo = new THREE.SphereGeometry(0.35, 8, 6);
const nodeIM = new THREE.InstancedMesh(sphereGeo, new THREE.MeshStandardMaterial({ roughness: 0.3, metalness: 0.5, emissive: new THREE.Color(0x111122), emissiveIntensity: 0.1 }), N);
nodeIM.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
scene.add(nodeIM);

const dummy = new THREE.Object3D();
const maxDeg = Math.max(...nodes.map(n => n.degree || 0));

// Pre-compute bidir edges
const adj = Array.from({length: N}, () => []);
for (const e of edges) { if (e.src < N && e.tgt < N) { adj[e.src].push(e.tgt); adj[e.tgt].push(e.src); } }
const bidirSet = new Set();
for (let i = 0; i < N; i++) for (const j of adj[i]) if (j > i && adj[j].includes(i)) bidirSet.add(i * 10000 + j);

// Compute edge positions
let edgeCount = 0, bidirCount = 0;
const maxE = Math.min(maxEdges, edges.length * 2);
const edgePosArr = new Float32Array(maxE * 6);
const bidirPosArr = new Float32Array(edges.length * 6);
for (const e of edges) {
  if (e.src >= N || e.tgt >= N) continue;
  const sx = nodes[e.src].x||0, sy = nodes[e.src].y||0, sz = nodes[e.src].z||0;
  const tx = nodes[e.tgt].x||0, ty = nodes[e.tgt].y||0, tz = nodes[e.tgt].z||0;
  const key = e.src < e.tgt ? e.src*10000+e.tgt : e.tgt*10000+e.src;
  if (bidirSet.has(key)) {
    const b = bidirCount*6; bidirPosArr[b]=sx;bidirPosArr[b+1]=sy;bidirPosArr[b+2]=sz;bidirPosArr[b+3]=tx;bidirPosArr[b+4]=ty;bidirPosArr[b+5]=tz; bidirCount++;
  } else {
    if (edgeCount < maxE) { const i=edgeCount*6; edgePosArr[i]=sx;edgePosArr[i+1]=sy;edgePosArr[i+2]=sz;edgePosArr[i+3]=tx;edgePosArr[i+4]=ty;edgePosArr[i+5]=tz; }
    edgeCount++;
  }
}

const edgeGeo = new THREE.BufferGeometry();
edgeGeo.setAttribute('position', new THREE.BufferAttribute(edgePosArr.slice(0, Math.min(edgeCount, maxE)*6), 3));
const edgeLines = new THREE.LineSegments(edgeGeo, new THREE.LineBasicMaterial({ color: 0x223344, transparent: true, opacity: 0.4 }));
scene.add(edgeLines);

const bidirGeo = new THREE.BufferGeometry();
bidirGeo.setAttribute('position', new THREE.BufferAttribute(bidirPosArr.slice(0, bidirCount*6), 3));
const bidirLines = new THREE.LineSegments(bidirGeo, new THREE.LineBasicMaterial({ color: 0xE07A4F, transparent: true, opacity: 0.7 }));
scene.add(bidirLines);

// Broken links (dashed red segments)
const brokenLinePositions = [];
for (const b of brokenEdges) { if (b.src < N) { const s=nodes[b.src]; brokenLinePositions.push(s.x||0, s.y||0, s.z||0, (s.x||0)+(Math.random()-0.5)*3, (s.y||0)+(Math.random()-0.5)*3, (s.z||0)+(Math.random()-0.5)*3); } }
const brokenGeo = new THREE.BufferGeometry();
if (brokenLinePositions.length > 0) {
  brokenGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(brokenLinePositions), 3));
  const brokenSeg = new THREE.LineSegments(brokenGeo, new THREE.LineDashedMaterial({ color: 0xff6b6b, transparent: true, opacity: 0.4, dashSize: 0.8, gapSize: 0.4 }));
  brokenSeg.computeLineDistances(); brokenSeg.visible = showBroken; scene.add(brokenSeg);
  window._brokenSeg = brokenSeg;
}

// Initialize node matrices and colors
for (let i = 0; i < N; i++) {
  const n = nodes[i], deg = n.degree || 0;
  const r = 0.18 + (sizeByDegree ? (deg / maxDeg) * 0.82 : 0.5);
  dummy.position.set(n.x || 0, n.y || 0, n.z || 0); dummy.scale.setScalar(r); dummy.updateMatrix();
  nodeIM.setMatrixAt(i, dummy.matrix);
  const col = colorByFolder ? (FOLDER_COLORS_HEX[n.folder] || 0x666666) : 0x6699cc;
  nodeIM.setColorAt(i, new THREE.Color(col));
}
nodeIM.instanceMatrix.needsUpdate = true; if (nodeIM.instanceColor) nodeIM.instanceColor.needsUpdate = true;

// HTML Labels
const labelContainer = document.createElement('div');
labelContainer.style.cssText = 'position:fixed;top:0;left:280px;width:100%;height:100%;pointer-events:none;z-index:5;overflow:hidden;';
document.body.appendChild(labelContainer);

function makeLabel(text, color) {
  const d = document.createElement('div');
  d.style.cssText = 'position:absolute;font-size:10px;color:'+color+';white-space:nowrap;transform:translate(-50%,-50%);pointer-events:none;text-shadow:0 1px 4px rgba(0,0,0,0.9);padding:1px 4px;border-radius:3px;background:rgba(0,0,0,0.4);';
  d.textContent = text.length > 28 ? text.slice(0,27)+'…' : text;
  d.style.display = 'none';
  labelContainer.appendChild(d);
  return { el: d, node: null };
}

const labelDivs = [];
for (const n of nodes.filter(n => (n.degree||0) >= 5).sort((a,b) => (b.degree||0)-(a.degree||0)).slice(0, 60)) {
  const col = colorByFolder ? (FOLDER_COLORS_CSS[n.folder] || '#888') : '#6699cc';
  const lbl = makeLabel(n.title, col);
  lbl.node = n;
  labelDivs.push(lbl);
}

// Raycasting
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
const infoPanel = document.getElementById('info-panel');

function showInfo(idx) {
  const n = nodes[idx];
  document.getElementById('info-title').textContent = n.title;
  const fe = document.getElementById('info-folder');
  fe.textContent = n.folder; fe.style.background = (FOLDER_COLORS_CSS[n.folder]||'#666')+'33'; fe.style.color = FOLDER_COLORS_CSS[n.folder]||'#888';
  document.getElementById('info-path').textContent = n.relpath || '';
  const inC = edges.filter(e => e.tgt === idx).length, outC = edges.filter(e => e.src === idx).length;
  document.getElementById('info-links').textContent = '\u2190 ' + inC + ' incoming \u00b7 ' + outC + ' outgoing \u2192';
  document.getElementById('info-broken').style.display = brokenEdges.some(b => b.src === idx) ? 'block' : 'none';
  document.getElementById('btn-open').onclick = () => openNote(n);
  document.getElementById('btn-focus').onclick = () => focusNode(idx);
  document.getElementById('btn-hide').onclick = () => { hideNode(idx); closeInfo(); };
  infoPanel.style.display = 'block';
}

function closeInfo() { infoPanel.style.display = 'none'; selectedNode = null; }

function openNote(n) {
  const vaultPath = localStorage.getItem('vaultPath') || '/home/thomas/Desktop/Memory';
  window.open('file://' + vaultPath.replace(/\\\\/g,'/') + '/' + (n.relpath || n.title+'.md'), '_blank');
}

function focusNode(idx) {
  const connected = new Set([idx]);
  for (const e of edges) { if (e.src===idx) connected.add(e.tgt); if (e.tgt===idx) connected.add(e.src); }
  focusedNode = idx;
  for (let i=0;i<N;i++) {
    const n=nodes[i], deg=n.degree||0;
    const visible = connected.has(i) && activeFilters.has(n.folder) && deg >= minDegree;
    dummy.position.set(n.x||0, n.y||0, n.z||0);
    dummy.scale.setScalar(visible ? 0.18+(sizeByDegree?(deg/maxDeg)*0.82:0.5) : 0.001);
    dummy.updateMatrix(); nodeIM.setMatrixAt(i, dummy.matrix);
    nodeIM.setColorAt(i, new THREE.Color(visible ? (FOLDER_COLORS_HEX[n.folder]||0x666666) : 0x222222));
  }
  nodeIM.instanceMatrix.needsUpdate = true; if (nodeIM.instanceColor) nodeIM.instanceColor.needsUpdate = true;
  const n=nodes[idx]; controls.target.set(n.x||0,n.y||0,n.z||0); camera.position.set(n.x||0,(n.y||0)+5,(n.z||0)+40);
}

function hideNode(idx) {
  for (let i=0;i<N;i++) if (i!==idx) {
    const n=nodes[i], deg=n.degree||0;
    dummy.position.set(n.x||0,n.y||0,n.z||0);
    dummy.scale.setScalar(activeFilters.has(n.folder)&&deg>=minDegree ? 0.18+(sizeByDegree?(deg/maxDeg)*0.82:0.5) : 0.001);
    dummy.updateMatrix(); nodeIM.setMatrixAt(i, dummy.matrix);
    nodeIM.setColorAt(i, new THREE.Color(FOLDER_COLORS_HEX[n.folder]||0x666666));
  }
  nodeIM.instanceMatrix.needsUpdate = true; if (nodeIM.instanceColor) nodeIM.instanceColor.needsUpdate = true;
  focusedNode = null;
}

canvas.addEventListener('click', e => {
  pointer.x = ((e.clientX - canvas.getBoundingClientRect().left) / canvas.clientWidth)*2-1;
  pointer.y = -((e.clientY - canvas.getBoundingClientRect().top) / canvas.clientHeight)*2+1;
  raycaster.setFromCamera(pointer, camera);
  const hits = raycaster.intersectObject(nodeIM);
  if (hits.length > 0) { selectedNode = hits[0].instanceId; showInfo(selectedNode); }
  else { if (!e.shiftKey) { closeInfo(); focusedNode = null; applyFilters(); } }
});

canvas.addEventListener('dblclick', e => {
  pointer.x = ((e.clientX - canvas.getBoundingClientRect().left) / canvas.clientWidth)*2-1;
  pointer.y = -((e.clientY - canvas.getBoundingClientRect().top) / canvas.clientHeight)*2+1;
  raycaster.setFromCamera(pointer, camera);
  const hits = raycaster.intersectObject(nodeIM);
  if (hits.length > 0) openNote(nodes[hits[0].instanceId]);
});

// Folder toggles
const folderTogglesEl = document.getElementById('folder-toggles');
const folders = [...new Set(nodes.map(n => n.folder))].sort();
for (const folder of folders) {
  const row = document.createElement('label');
  row.className = 'folder-toggle';
  const color = FOLDER_COLORS_CSS[folder] || '#888';
  row.innerHTML = '<input type="checkbox" data-folder="'+folder+'" '+(activeFilters.has(folder)?'checked':'')+'><div class="folder-dot" style="background:'+color+'"></div><span>'+folder+' ('+nodes.filter(n=>n.folder===folder).length+')</span>';
  row.querySelector('input').addEventListener('change', e => {
    if (e.target.checked) activeFilters.add(folder); else activeFilters.delete(folder);
    applyFilters();
  });
  folderTogglesEl.appendChild(row);
}

function applyFilters() {
  for (let i=0;i<N;i++) {
    const n=nodes[i], deg=n.degree||0;
    const show = activeFilters.has(n.folder) && deg >= minDegree;
    dummy.position.set(n.x||0,n.y||0,n.z||0);
    dummy.scale.setScalar(show ? 0.18+(sizeByDegree?(deg/maxDeg)*0.82:0.5) : 0.001);
    dummy.updateMatrix(); nodeIM.setMatrixAt(i, dummy.matrix);
    nodeIM.setColorAt(i, new THREE.Color(colorByFolder?(FOLDER_COLORS_HEX[n.folder]||0x666666):0x6699cc));
  }
  nodeIM.instanceMatrix.needsUpdate = true; if (nodeIM.instanceColor) nodeIM.instanceColor.needsUpdate = true;
}

// Search
const searchInput = document.getElementById('search-input');
const matchCountEl = document.getElementById('match-count');
searchInput.addEventListener('input', e => {
  searchQuery = e.target.value.toLowerCase().trim();
  if (!searchQuery) { matchCountEl.textContent = ''; applyFilters(); return; }
  const matches = nodes.filter(n => n.title.toLowerCase().includes(searchQuery));
  matchCountEl.textContent = matches.length+' match'+(matches.length!==1?'es':'');
  const matchSet = new Set(matches.map(m=>m.id));
  for (let i=0;i<N;i++) {
    const n=nodes[i], deg=n.degree||0;
    const show = matchSet.has(i);
    dummy.position.set(n.x||0,n.y||0,n.z||0);
    dummy.scale.setScalar(show ? 0.35+(sizeByDegree?(deg/maxDeg)*0.6:0.5) : 0.08);
    dummy.updateMatrix(); nodeIM.setMatrixAt(i, dummy.matrix);
    nodeIM.setColorAt(i, new THREE.Color(show ? 0xffffff : 0x333333));
  }
  nodeIM.instanceMatrix.needsUpdate = true; if (nodeIM.instanceColor) nodeIM.instanceColor.needsUpdate = true;
});

// Controls
document.getElementById('min-degree').addEventListener('input', e => { minDegree=parseInt(e.target.value); document.getElementById('min-degree-val').textContent=minDegree; applyFilters(); });
document.getElementById('max-edges').addEventListener('input', e => { maxEdges=parseInt(e.target.value); document.getElementById('max-edges-val').textContent=maxEdges; });
document.getElementById('toggle-orphans').addEventListener('change', e => { showOrphans=e.target.checked; if(window._brokenSeg) window._brokenSeg.visible=showOrphans; });
document.getElementById('toggle-broken').addEventListener('change', e => { showBroken=e.target.checked; if(window._brokenSeg) window._brokenSeg.visible=showBroken; });
document.getElementById('toggle-bidir').addEventListener('change', e => { showBidir=e.target.checked; bidirLines.visible=showBidir; });
document.getElementById('toggle-labels').addEventListener('change', e => { showLabels=e.target.checked; labelDivs.forEach(l=>{l.el.style.display='none';}); });
document.getElementById('toggle-size-degree').addEventListener('change', e => { sizeByDegree=e.target.checked; applyFilters(); });
document.getElementById('toggle-color-folder').addEventListener('change', e => { colorByFolder=e.target.checked; applyFilters(); });

// Minimap
function showMinimap() { minimapVisible=!minimapVisible; document.getElementById('minimap-wrapper').style.display=minimapVisible?'block':'none'; }
const mmViewport = document.getElementById('minimap-viewport');

// Label visibility
function worldToScreen(x,y,z) {
  const v = new THREE.Vector3(x,y,z).project(camera);
  const rect = canvas.getBoundingClientRect();
  return { x:(v.x*0.5+0.5)*rect.width+rect.left, y:(-(v.y)*0.5+0.5)*rect.height+rect.top, z:v.z };
}

function updateLabelVisibility() {
  if (!showLabels) return;
  const camDist = camera.position.distanceTo(controls.target);
  for (const {el, node} of labelDivs) {
    if (!node) { el.style.display='none'; continue; }
    const sp = worldToScreen(node.x||0, node.y||0, node.z||0);
    if (sp && sp.z > 0 && sp.z < 1) { el.style.left=sp.x+'px'; el.style.top=sp.y+'px'; el.style.display = camDist < 55 ? 'block' : 'none'; }
    else el.style.display='none';
  }
}

// Reset camera
function resetCamera() { camera.position.set(0,8,70); controls.target.set(0,0,0); focusedNode=null; applyFilters(); }
window.resetCamera = resetCamera; window.showMinimap = showMinimap;

// Settings
function showSettings() { document.getElementById('settings-overlay').style.display='flex'; document.getElementById('vault-path-input').value=localStorage.getItem('vaultPath')||'/home/thomas/Desktop/Memory'; }
function hideSettings() { document.getElementById('settings-overlay').style.display='none'; }
function applySettings() { localStorage.setItem('vaultPath', document.getElementById('vault-path-input').value); hideSettings(); document.getElementById('ctrl-vault-path').textContent=localStorage.getItem('vaultPath'); }
window.showSettings=showSettings; window.hideSettings=hideSettings; window.applySettings=applySettings;
document.getElementById('settings-overlay').addEventListener('click', e => { if(e.target===document.getElementById('settings-overlay')) hideSettings(); });

// Help
let helpVisible = false;
function showHelp() { helpVisible=!helpVisible; document.getElementById('legend').style.display=helpVisible?'block':'none'; document.getElementById('shortcuts').style.display=helpVisible?'block':'none'; }
window.showHelp = showHelp;

// Keyboard
window.addEventListener('keydown', e => {
  if (e.target.tagName === 'INPUT') return;
  if (e.key==='f'||e.key==='F') { searchInput.focus(); searchInput.select(); }
  if (e.key==='r'||e.key==='R') resetCamera();
  if (e.key==='m'||e.key==='M') showMinimap();
  if (e.key==='Escape') { closeInfo(); showHelp(); }
  if (e.key==='?') showHelp();
});

// Stats
document.getElementById('stats').innerHTML = '<strong>'+N+'</strong> notes<br><strong>'+edges.length+'</strong> resolved links<br><strong>'+brokenEdges.length+'</strong> broken links<br><strong>'+orphans.length+'</strong> orphan notes<br><strong>'+bidirCount+'</strong> bidirectional';

// Resize
function onResize() {
  const w=canvas.clientWidth, h=canvas.clientHeight;
  camera.aspect=w/h; camera.updateProjectionMatrix(); renderer.setSize(w,h);
}
window.addEventListener('resize', onResize);

// Animate
const highlightColor = new THREE.Color(0xE07A4F);
function animate() {
  requestAnimationFrame(animate);
  controls.update();
  if (selectedNode !== null) { nodeIM.setColorAt(selectedNode, highlightColor); nodeIM.instanceColor.needsUpdate = true; }
  if (showLabels) updateLabelVisibility();
  if (minimapVisible) {
    const fov = camera.fov*Math.PI/180, dist = camera.position.distanceTo(controls.target);
    const h = 2*Math.tan(fov/2)*dist*(130/canvas.clientHeight);
    const w = h*(170/canvas.clientWidth);
    const mx=(camera.position.x/100+0.5)*170, mz=(camera.position.z/100+0.5)*130;
    mmViewport.style.left=Math.max(0,mx-w/2)+'px'; mmViewport.style.top=Math.max(0,mz-h/2)+'px';
    mmViewport.style.width=Math.min(170,w)+'px'; mmViewport.style.height=Math.min(130,h)+'px';
  }
  renderer.render(scene, camera);
}

// Init
applyFilters();
document.getElementById('legend').style.display = 'block';
document.getElementById('loading').style.display = 'none';
document.getElementById('app').style.display = 'flex';
document.getElementById('ctrl-vault-path').textContent = localStorage.getItem('vaultPath') || '~/Desktop/Memory';
animate();
</script>
</body>
</html>"""

# Embed graph data
with open(GRAPH_JSON) as f:
    graph_data = json.load(f)

embed_line = "const GRAPH = " + json.dumps(graph_data, separators=(',', ':')) + ";"
html = HTML_TEMPLATE.replace("const GRAPH = __GRAPH_DATA__;", embed_line)

with open(OUT_HTML, 'w') as f:
    f.write(html)

size = os.path.getsize(OUT_HTML)
print(f"\nGenerated: {OUT_HTML} ({size:,} bytes)")
print(f"  {len(graph_data['nodes'])} nodes, {len(graph_data['edges'])} edges, {len(graph_data['broken'])} broken, {len(graph_data['orphans'])} orphans")
print("  Open directly in browser: file://" + OUT_HTML)
# Three.js Interactive Graph — Spike Template Reference

This is the working pattern from the Obsidian Vault 3D graph spike (May 2025). Use as a template for similar visualization spikes.

## Architecture

```
spike-output/
├── index.html          # Self-contained, CDN-loaded Three.js
└── graph_data.json     # Pre-computed graph (or embed inline)
```

## Key Implementation Pattern

### Data extraction (Python)

```python
import json, os, re, yaml

vault = '/path/to/vault'
wikilink_re = re.compile(r'\[\[([^\]]+)\]\]')
mdlink_re = re.compile(r'\[([^\]]*)\]\(([^\)]+)\)')

notes = {}  # title -> {id, folder, relpath, preview, degree, orphan, x, y, z}
edges = []   # {src, tgt, type}

for root, dirs, files in os.walk(vault):
    dirs[:] = [d for d in dirs if not d.startswith('.')]
    for fn in files:
        if not fn.endswith('.md'): continue
        fp = os.path.join(root, fn)
        rel = os.path.relpath(fp, vault)
        try:
            with open(fp) as f: content = f.read()
        except: continue

        # Frontmatter title
        title = fn[:-3]
        if content.startswith('---'):
            end = content.find('---', 3)
            if end > 0:
                fm = yaml.safe_load(content[3:end])
                title = fm.get('title', fn[:-3])

        # Preview: first 200 chars after frontmatter
        body = content[content.find('---', 3)+3:] if '---' in content[:10] else content
        preview = body.strip()[:200].replace('\n', ' ')

        # Links
        wl = wikilink_re.findall(content)
        ml = mdlink_re.findall(content)
```

### Force-directed layout (Python)

```python
import math

nodes = list(notes.values())
adj = [[] for _ in range(len(nodes))]
edge_set = set()

for src, tgt in edges:
    if src < len(nodes) and tgt < len(nodes):
        adj[src].append(tgt); adj[tgt].append(src)
        edge_set.add((min(src,tgt), max(src,tgt)))

# Fruchterman-Reingold
POS = [[(random.random()-0.5)*100, (random.random()-0.5)*100, (random.random()-0.5)*100]
       for _ in range(len(nodes))]

for iteration in range(80):
    disp = [[0.0,0.0,0.0] for _ in range(len(nodes))]
    for i in range(len(nodes)):
        for j in range(i+1, len(nodes)):
            dx, dy, dz = POS[i][0]-POS[j][0], POS[i][1]-POS[j][1], POS[i][2]-POS[j][2]
            dist = math.sqrt(dx*dx + dy*dy + dz*dz) + 0.01
            force = 5000 / (dist * dist)
            fx, fy, fz = dx/dist*force, dy/dist*force, dz/dist*force
            disp[i][0]+=fx; disp[i][1]+=fy; disp[i][2]+=fz
            disp[j][0]-=fx; disp[j][1]-=fy; disp[j][2]-=fz
    for i in range(len(nodes)):
        for j in adj[i]:
            dx, dy, dz = POS[j][0]-POS[i][0], POS[j][1]-POS[i][1], POS[j][2]-POS[i][2]
            dist = math.sqrt(dx*dx + dy*dy + dz*dz) + 0.01
            force = dist * dist / 80
            fx, fy, fz = dx/dist*force, dy/dist*force, dz/dist*force
            disp[i][0]+=fx; disp[i][1]+=fy; disp[i][2]+=fz
    for i in range(len(nodes)):
        d = math.sqrt(disp[i][0]**2 + disp[i][1]**2 + disp[i][2]**2) + 0.01
        temp = 80 * (1 - iteration/80)
        POS[i][0]+=disp[i][0]/d*min(d, temp)
        POS[i][1]+=disp[i][1]/d*min(d, temp)
        POS[i][2]+=disp[i][2]/d*min(d, temp)

for i, n in enumerate(nodes):
    n['x'], n['y'], n['z'] = POS[i]
```

### HTML (self-contained, CDN imports)

```html
<script type="importmap">
{
  "imports": {
    "three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
    "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"
  }
}
</script>
<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// Graph data — either import from JSON file or embed inline
const GRAPH = __GRAPH_DATA__;  // replace with actual JSON
const N = GRAPH.nodes.length;
const E = GRAPH.edges.length;

// Renderer
const canvas = document.getElementById('main-canvas');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setClearColor(0x0a0a0f);

// InstancedMesh for nodes (handles 800+ nodes efficiently)
const sphereGeo = new THREE.SphereGeometry(1, 8, 6);
const nodeIM = new THREE.InstancedMesh(sphereGeo, nodeMat, N);
nodeIM.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
nodeIM.instanceColor = new THREE.InstancedBufferAttribute(new Float32Array(N*3), 3);
scene.add(nodeIM);

// Edge lines
const edgeGeo = new THREE.BufferGeometry();
edgeGeo.setAttribute('position', new THREE.BufferAttribute(normBuf, 3));
const edgeLines = new THREE.LineSegments(edgeGeo, new THREE.LineBasicMaterial({ color: 0x1e2a38 }));
scene.add(edgeLines);

// OrbitControls with right-click pan
const controls = new OrbitControls(camera, renderer.domElement);
controls.mouseButtons = {
  LEFT: THREE.MOUSE.ROTATE,
  MIDDLE: THREE.MOUSE.DOLLY,
  RIGHT: THREE.MOUSE.PAN
};
```

### Node sizing by degree

```javascript
const maxDeg = Math.max(...GRAPH.nodes.map(n => n.degree || 1));
function applyNodeSizes(filterFn) {
  for (let i = 0; i < N; i++) {
    const n = GRAPH.nodes[i];
    const deg = n.degree || 0;
    const r = visible ? 0.18 + (deg / maxDeg) * 0.82 : 0.002;
    dummy.position.set(n.x || 0, n.y || 0, n.z || 0);
    dummy.scale.setScalar(r);
    dummy.updateMatrix();
    nodeIM.setMatrixAt(i, dummy.matrix);
  }
  nodeIM.instanceMatrix.needsUpdate = true;
}
```

## Critical: Embedded JSON Embedding

When embedding graph data inline in HTML, replace `__GRAPH_DATA__` using Python string replacement:

```python
with open('spike_output/index.html') as f:
    html = f.read()
graph_json = json.dumps(graph_data, separators=(',', ':'))
html = html.replace('__GRAPH_DATA__;', graph_json + ';')
with open('spike_output/index.html', 'w') as f:
    f.write(html)
```

Verify the file opens without console errors in browser before considering the spike complete.

## Performance Notes

- `InstancedMesh` for 800+ nodes: single draw call, update via `setMatrixAt()` + `needsUpdate = true`
- `LineSegments` (not `Line`) for edges — two vertices per edge
- `OrbitControls.dampingFactor = 0.08` gives smooth feel
- `renderer.setPixelRatio(Math.min(devicePixelRatio, 2))` prevents retina overkill
- Force layout computed in Python (80 iterations is sufficient for 800 nodes in <5s)

## Output location

For Thomas: always write to `/home/thomas/` (persistent home), not `/tmp/` which is cleared. Serve via `python3 -m http.server <port>` for testing, then share as `file://` URL.

### Canvas sizing — critical gotcha (r160)

```javascript
// WRONG — clientWidth/clientHeight are 0 if only CSS sets size
renderer.setSize(canvas.clientWidth, canvas.clientHeight);

// CORRECT — set explicit pixel dimensions before THREE reads them
canvas.width = 1050;
canvas.height = 900;
renderer.setSize(canvas.width, canvas.height);

// Camera uses canvas.width/canvas.height too
const camera = new THREE.PerspectiveCamera(55, canvas.width / canvas.height, 0.1, 2000);

// On resize, fall back to window dimensions if canvas has no CSS pixel size
function onResize() {
  const nw = canvas.clientWidth || window.innerWidth - 230;  // subtract sidebar width
  const nh = canvas.clientHeight || window.innerHeight;
  camera.aspect = nw / nh;
  camera.updateProjectionMatrix();
  renderer.setSize(nw, nh);
}
```

### Material: MeshLambertMaterial over MeshStandardMaterial

For graph nodes colored by folder under ambient + directional light, `MeshLambertMaterial` (pure diffuse) is more reliable than `MeshStandardMaterial` (physically-based). MeshStandardMaterial requires proper PBR lighting (ambient + directional + environment map) before colors display correctly — easy to get wrong and end up with dark/washed-out nodes.

```javascript
// Use this for colored nodes
const mat = new THREE.MeshLambertMaterial({
  color: FC[n.folder] || 0x555555,
  emissive: new THREE.Color(0x080818),
  emissiveIntensity: 0.4
});

// NOT MeshStandardMaterial unless you have full PBR lighting setup
// const mat = new THREE.MeshStandardMaterial({
//   roughness: 0.35, metalness: 0.45,
//   emissive: new THREE.Color(0x111122), emissiveIntensity: 0.12
// }); // colors appear dark without proper env map / roughness tuning
```

### InstancedMesh + instanceColor — known failure mode

`InstancedMesh` with per-instance color via `instanceColor` buffer attribute silently fails in Three.js r160 — nodes render with no visible color. The attribute format is correct, `needsUpdate = true` is set, but the material ignores the per-instance color because `vertexColors` is not enabled.

**Reliable alternatives:**
1. **Individual Mesh objects** (one SphereGeometry per node) — simple, always works, raycasting works out of the box. Acceptable for N < 2000.
2. **InstancedMesh with uniform color** — color all nodes the same via shared material, vary size by degree. Then swap to per-mesh color if needed.
3. **THREE.Points with BufferGeometry** — nodes as points, colored via vertex colors. Requires `PointsMaterial({ vertexColors: true })`.

For the Obsidian vault spike (881 nodes): individual Mesh objects perform adequately. For 5000+ nodes, use option (2).

### Always set frustumCulled = false on node meshes

Three.js culls objects outside the camera frustum by default. Sphere nodes at graph edges can disappear unexpectedly during orbit. Prevent this:

```javascript
mesh.frustumCulled = false;
```

### Headless Chromium WebGL notes

On Linux headless Chromium (SwiftShader software renderer):
- `InstancedMesh.instanceColor` may render differently than in real Chrome
- Use `--enable-unsafe-swiftshader` flag
- `--dump-dom` shows page structure but not WebGL rendering
- Test headed mode for true verification of visible nodes

### Output location

For Thomas: always write to `/home/thomas/` (persistent home), not `/tmp/` which is cleared. Serve via `python3 -m http.server <port>` for testing, then share as `http://localhost:<port>/file.html`.

### Verification checklist

- [ ] Page loads in Chrome without console errors
- [ ] Orbit drag works (left-click rotate)
- [ ] Scroll zoom works
- [ ] Right-click pan works
- [ ] Nodes are visible and colored (test with known-folder colors)
- [ ] Edges are visible
- [ ] Click on node shows info panel
- [ ] Double-click opens note (or fallback)
- [ ] Search filters nodes
- [ ] No broken JS in console (F12 → Console)
- [ ] Test in headed mode, not just headless — SwiftShader can mask rendering issues
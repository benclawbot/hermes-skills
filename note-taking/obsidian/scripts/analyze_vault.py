#!/usr/bin/env python3
"""Analyze a personal note vault (Obsidian-style) to surface hidden patterns.

Generalized from the 2026-06-02 Memory vault run. Edit the VAULT constant
to point at any directory of .md files with frontmatter.

Outputs:
  - /tmp/vault_analysis/summary.json  (all computed stats, sorted, ready for
                                       site-building)
  - /tmp/vault_analysis/notes.json    (per-note metadata for downstream
                                       processing)

Handles:
  - Bilingual frontmatter (e.g. strong_links vs liens_forts)
  - Loose YAML fallback when strict YAML parse fails
  - Empty/garbage strong_links entries (which crash naive parsers)
  - Skips .git, .obsidian, .trash, node_modules, pages/ subtrees by default
"""
import os
import re
import json
from collections import Counter, defaultdict
from pathlib import Path

# ── CONFIGURE THIS ─────────────────────────────────────────────────────────
VAULT = Path("/home/thomas/Desktop/Memory")  # ← point at any vault
OUT = Path("/tmp/vault_analysis")
OUT.mkdir(exist_ok=True)
# ───────────────────────────────────────────────────────────────────────────

# Per-language field aliases. Extend as you encounter more schemas.
# Treat these as the same logical field regardless of language.
FIELD_ALIASES = {
    "title": ["title", "titre"],
    "type": ["type"],
    "cluster": ["cluster"],
    "importance": ["importance", "importance_"],
    "tags": ["tags"],
    "links": ["strong_links", "liens_forts", "liens"],
    "opposition": ["opposition_links", "liens_opposition"],
    "sources_count": ["sources_count"],
    "created": ["created", "créé", "cree"],
}

FM_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)

# What to skip (edit as needed)
SKIP_PATH_PARTS = {".git", ".obsidian", ".trash", "node_modules"}


def should_skip(path: Path) -> bool:
    return any(part in path.parts for part in SKIP_PATH_PARTS)


def collect_md_files(vault: Path):
    """Collect all .md files under the vault, respecting SKIP_PATH_PARTS.

    Note: many vaults put leaf content under pages/ or _Lot*_* subfolders.
    We deliberately do NOT skip those by default — adjust SKIP_PATH_PARTS
    if your vault has noise folders.
    """
    out = []
    for root, dirs, files in os.walk(vault):
        # prune
        dirs[:] = [d for d in dirs if d not in SKIP_PATH_PARTS]
        for f in files:
            if f.endswith(".md"):
                out.append(Path(root) / f)
    return out


def _loose_yaml(s: str) -> dict:
    """Fallback parser for frontmatter that isn't strict YAML.
    Handles simple `key: value` lines and inline `[a, b]` lists.
    """
    out = {}
    for line in s.splitlines():
        if not line.strip() or line.startswith(" "):
            continue
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if v.startswith("[") and v.endswith("]"):
            inner = v[1:-1]
            out[k] = [x.strip().strip('"').strip("'")
                      for x in inner.split(",") if x.strip()]
        else:
            out[k] = v
    return out


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Returns (frontmatter_dict, body_text). Handles strict + loose YAML."""
    m = FM_RE.match(text)
    if not m:
        return {}, text
    try:
        import yaml
        fm = yaml.safe_load(m.group(1)) or {}
    except Exception:
        fm = _loose_yaml(m.group(1))
    return fm, m.group(2)


def parse_note(path: Path, vault: Path) -> dict | None:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None

    fm, body = parse_frontmatter(text)

    # Resolve bilingual aliases — first alias wins
    def get(*keys):
        for k in keys:
            v = fm.get(k)
            if v is not None:
                return v
        return None

    return {
        "path": str(path.relative_to(vault)),
        "top": path.relative_to(vault).parts[0] if path.parts else "",
        "title": get(*FIELD_ALIASES["title"]) or path.stem,
        "type": get(*FIELD_ALIASES["type"]),
        "cluster": get(*FIELD_ALIASES["cluster"]),
        "importance": get(*FIELD_ALIASES["importance"]),
        "tags": get(*FIELD_ALIASES["tags"]) or [],
        "strong_links": get(*FIELD_ALIASES["links"]) or [],
        "opposition_links": get(*FIELD_ALIASES["opposition"]) or [],
        "sources_count": get(*FIELD_ALIASES["sources_count"]) or 0,
        "word_count": len(body.split()),
        "body": body,
    }


# ── 1. Inventory ───────────────────────────────────────────────────────────
md_files = collect_md_files(VAULT)
print(f"Total .md files: {len(md_files)}")

notes = [n for n in (parse_note(p, VAULT) for p in md_files) if n]
print(f"Parsed: {len(notes)} notes")

inventory = Counter(n["top"] for n in notes)
print("\nBy top-level folder:")
for k, v in inventory.most_common():
    print(f"  {k:30s}  {v:5d}")

# ── 2. Tag frequency ───────────────────────────────────────────────────────
tag_freq = Counter()
tag_to_notes = defaultdict(list)
for n in notes:
    for t in (n["tags"] or []):
        if isinstance(t, str):
            tag_freq[t] += 1
            tag_to_notes[t].append(n["title"])

print(f"\nUnique tags: {len(tag_freq)}")
print("Top 40 tags:")
for t, c in tag_freq.most_common(40):
    print(f"  {c:4d}  {t}")

# Tag distribution buckets
tag_buckets = Counter()
for c in tag_freq.values():
    if c == 1:
        tag_buckets["1 (singletons)"] += 1
    elif c <= 4:
        tag_buckets["2-4"] += 1
    elif c <= 9:
        tag_buckets["5-9"] += 1
    elif c <= 19:
        tag_buckets["10-19"] += 1
    elif c <= 49:
        tag_buckets["20-49"] += 1
    else:
        tag_buckets["50+"] += 1

print("\nTag occurrence distribution:")
for k, v in tag_buckets.most_common():
    print(f"  {k:20s}  {v}")

# ── 3. Type / cluster / importance ─────────────────────────────────────────
type_freq = Counter(n["type"] for n in notes if n["type"])
cluster_freq = Counter(n["cluster"] for n in notes if n["cluster"])
importance_freq = Counter(n["importance"] for n in notes if n["importance"])

print("\nNote types:", type_freq.most_common(10))
print("\nClusters:", cluster_freq.most_common())
print("\nImportance (top 10):",
      [(k, v) for k, v in importance_freq.most_common(10)])

# ── 4. Link graph + cross-domain bridges ───────────────────────────────────
title_to_path = {n["title"]: n["path"] for n in notes}
title_to_domain = {n["title"]: n["top"] for n in notes}

cross_edges = Counter()
outgoing_to_other = Counter()
in_degree = Counter()
opp_count = Counter()

for n in notes:
    src_title = n["title"]
    src_dom = n["top"]
    for link in (n["strong_links"] or []):
        # strong_links may be ['Title'] or [[a, b]] — guard both
        if isinstance(link, list):
            if not link:
                continue
            tgt_title = link[0]
        else:
            tgt_title = link
        if not tgt_title:
            continue

        in_degree[tgt_title] += 1
        tgt_dom = title_to_domain.get(tgt_title, "?")
        if src_dom != tgt_dom:
            cross_edges[(src_dom, tgt_dom)] += 1
            outgoing_to_other[(src_title, src_dom, tgt_dom)] += 1

    for link in (n["opposition_links"] or []):
        if isinstance(link, list) and link:
            opp_count[n["title"]] += 1
        elif isinstance(link, str) and link:
            opp_count[n["title"]] += 1

print(f"\nCross-domain edges: {len(cross_edges)}")
print("\nTop 20 cross-domain pairs:")
for (sd, td), c in cross_edges.most_common(20):
    print(f"  {c:4d}  {sd} <-> {td}")

print("\nTop 25 HUB notes (most linked-to):")
for t, c in in_degree.most_common(25):
    dom = title_to_domain.get(t, "?")
    print(f"  {c:3d}  [{dom:20s}]  {t}")

print("\nTop 15 opposition-rich notes:")
for t, c in opp_count.most_common(15):
    dom = title_to_domain.get(t, "?")
    print(f"  {c:3d}  [{dom:20s}]  {t}")

# ── 5. Word frequency by domain ────────────────────────────────────────────
STOP = set("""the a an and or of to in is are was were be been being it its for on with
that this these those as at by from into about over under between through during
before after not no nor so if then than but also which who what when where why how
all any some most more less very much many few such only own same other another
le les des une est pour sur qui plus peut avec sont dans par""".split())

domain_words = defaultdict(Counter)
for n in notes:
    words = re.findall(r"\b[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9-]{2,}\b",
                       (n.get("body") or "").lower())
    for w in words:
        if w in STOP:
            continue
        domain_words[n["top"]][w] += 1

print("\nWord frequency by domain (top 15):")
for dom, counter in domain_words.items():
    print(f"\n  {dom}:")
    for w, c in counter.most_common(15):
        print(f"    {c:4d}  {w}")

# ── 6. Empty-container detection ───────────────────────────────────────────
# Detect files where the body is empty or near-empty after frontmatter.
# Adjust the template-detection regex to your vault's container pattern.
empty_count = 0
empty_files = []
EMPTY_PATTERNS = [
    re.compile(r"\*\*Task:\*\*\s*unknown", re.IGNORECASE),
    re.compile(r"\*\*Log:\*\*\s*\[empty\]", re.IGNORECASE),
    re.compile(r"^\s*Log:\s*$", re.MULTILINE | re.IGNORECASE),
]

for n in notes:
    body = n.get("body", "") or ""
    if n["word_count"] < 20:
        empty_count += 1
        empty_files.append(n["path"])
        continue
    for pat in EMPTY_PATTERNS:
        if pat.search(body):
            empty_count += 1
            empty_files.append(n["path"])
            break

print(f"\nEmpty / near-empty files: {empty_count} of {len(notes)}")
if empty_count:
    print("  sample:")
    for p in empty_files[:5]:
        print(f"    {p}")

# ── 7. Save everything ─────────────────────────────────────────────────────
data = {
    "total_notes": len(notes),
    "by_folder": dict(inventory),
    "tag_freq": tag_freq.most_common(200),
    "tag_buckets": dict(tag_buckets),
    "type_freq": type_freq.most_common(),
    "cluster_freq": cluster_freq.most_common(),
    "importance_freq": importance_freq.most_common(20),
    "hubs": [{"title": t, "in_degree": c, "domain": title_to_domain.get(t, "?")}
             for t, c in in_degree.most_common(50)],
    "bridges": [{"title": st, "from": sd, "to": td, "edges": c}
                for (st, sd, td), c in outgoing_to_other.most_common(50)],
    "cross_pairs": [{"from": sd, "to": td, "edges": c}
                    for (sd, td), c in cross_edges.most_common(30)],
    "opposition": [{"title": t, "count": c, "domain": title_to_domain.get(t, "?")}
                   for t, c in opp_count.most_common(30)],
    "domain_words": {d: c.most_common(80) for d, c in domain_words.items()},
    "empty_files": empty_files,
}
(OUT / "summary.json").write_text(json.dumps(data, indent=2, default=str))
(OUT / "notes.json").write_text(json.dumps([{
    "path": n["path"], "top": n["top"], "title": n["title"],
    "type": n["type"], "cluster": n["cluster"],
    "tags": n["tags"], "importance": n["importance"],
    "word_count": n["word_count"],
} for n in notes], indent=2, default=str))

print(f"\nSaved summary -> {OUT/'summary.json'}")
print(f"Saved notes   -> {OUT/'notes.json'}")

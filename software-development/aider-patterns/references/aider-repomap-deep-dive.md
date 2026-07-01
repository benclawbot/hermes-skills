# Repo Map Deep Dive — Aider's PageRank Pipeline

Aider reference: `aider/repomap.py` (867 lines).

The repo map is the single most expensive piece of Aider's context
preparation. Done well, it gives the LLM a 1-2k-token "tour" of the
codebase that's actually relevant to the user's question. Done badly,
it's a generic file listing the model ignores.

## Pipeline

```
1. Per-file tag extraction (tree-sitter SCM queries)
     │
     ▼
2. Symbol graph (definitions + references across files)
     │
     ▼
3. PageRank with personalization
     │  (chat files, mentioned idents, file-name matches all get boosts)
     ▼
4. Binary-search token budget
     │  (binary search N until rendered tree within ±15% of target)
     ▼
5. Tree rendering (grep_ast.TreeContext)
```

## Stage 1: tag extraction

`repomap.py:get_tags_raw()` (~line 80). For each file:

1. Detect language via `filename_to_lang` (delegates to `grep_ast`)
2. If language has a tree-sitter SCM query (in `aider/queries/tree-sitter-languages/*.scm`), parse with tree-sitter, extract `(rel_fname, fname, line, name, kind)` tuples
3. If no tree-sitter support, fall back to Pygments lexer → best-effort regex extraction
4. Skip binary, oversized, or noisy files (vendored deps, generated code)

Languages with tree-sitter queries:
- `aider/queries/tree-sitter-languages/README.md` lists 18 upstream repos
- `aider/queries/tree-sitter-language-pack/` is the newer source (Goldziher/tree-sitter-language-pack)

`CACHE_VERSION = 4` when using tree-sitter-language-pack, else `3`.
Cache dir: `.aider.tags.cache.v{N}` in cwd, keyed by file mtime.

## Stage 2: graph construction

`repomap.py:get_ranked_tags()` (~line 370). Two data structures:

- `definitions: defaultdict(set)` — `(fname, ident) → set of (def_fname, line)`
- `references: defaultdict(set)` — `(fname, ident) → set of (ref_fname, line)`

For each tag (definition) in each file:
1. Look up references for that tag across all files
2. Add a weighted edge from ref_fname → def_fname (weight = `1/distance` roughly)

Result: `nx.MultiDiGraph` where nodes are files and edges represent
"file X references symbol Y from file Z".

## Stage 3: PageRank with personalization

`repomap.py:374-531`.

The personalization vector is the killer. It boosts:

| Boost | Source |
|---|---|
| × 50 | files in the chat (`abs_fnames`) |
| × 10 | mentioned identifiers in the user's message |
| × 10 | files whose path components match mentioned identifiers (snake/kebab/camel split, ≥8 chars) |
| default | `100 / num_nodes` (uniform) |

```python
personalization = {}
personalize = 100 / len(fnames)
for fname in chat_fnames:
    personalization[rel_fname] = personalize * 50  # file already in chat
for ident in mentioned_idents:
    # find files whose path components match this ident
    for path_match in components_to_check.intersection(mentioned_idents):
        current_pers += personalize  # add 10x
```

Then:

```python
ranked = nx.pagerank(G, weight="weight",
                     personalization=personalization,
                     dangling=personalization)
```

`dangling=personalization` ensures dangling files (no out-edges) get
pulled toward relevant files instead of uniform distribution.

Two fallback passes:

```python
# repomap.py:732-746 — three-pass fallback
# Pass 1: chat + other
# Pass 2: ∅ + all (if pass 1 was empty)
# Pass 3: ∅ + all, no hints (if pass 2 was empty)
```

This handles repos with no proper structure (e.g., one big file) and
ensures SOMETHING is always returned.

## Stage 4: binary search to token budget

`repomap.py:640-706`.

```python
lower_bound = 0
upper_bound = num_tags
best_tree = None
middle = min(int(max_map_tokens // 25), num_tags)

while lower_bound <= upper_bound:
    tree = self.to_tree(ranked_tags[:middle], chat_rel_fnames)
    num_tokens = self.token_count(tree)

    pct_err = abs(num_tokens - max_map_tokens) / max_map_tokens
    ok_err = 0.15
    if (num_tokens <= max_map_tokens and num_tokens > best_tree_tokens) \
            or pct_err < ok_err:
        best_tree = tree
        best_tree_tokens = num_tokens
        if pct_err < ok_err:
            break

    if num_tokens < max_map_tokens:
        lower_bound = middle + 1
    else:
        upper_bound = middle - 1
    middle = int((lower_bound + upper_bound) // 2)
```

Key trick: render the tree once for the initial guess, then binary
search. `ok_err = 0.15` (15%) — accepts any tree within ±15% of the
target, so we don't pay for the final tiny adjustment.

## Stage 5: tree rendering

`repomap.py:render_tree()` + `to_tree()` (~line 710-770). Uses
`grep_ast.TreeContext` to render a code tree with the lines of
interest (tags from this file) highlighted:

```python
context = TreeContext(
    rel_fname, code,
    color=False, line_number=False, child_context=False,
    last_line=False, margin=0, mark_lois=False, loi_pad=0,
)
context.lines_of_interest = set()
context.add_lines_of_interest(lois)
context.add_context()
res = context.format()
```

Result: a textual tree like

```
foo.py
└── class Foo
    └── def bar (line 42)
        ↳ calls: process_data, validate_input
```

## When to use this in your project

**Use the full thing if:**
- You support 5+ languages
- Repos are typically > 100 files
- Users ask questions about unfamiliar code

**Use a simpler version if:**
- You support 1-3 languages
- Repos are < 100 files
- You already have a project-summary mechanism

**Simpler version (no networkx, no tree-sitter):**

```python
# Step 1: build a file → bag-of-symbols index
symbols: dict[str, set[str]] = {}  # rel_fname → {ident, ident, ...}
for fname in files:
    symbols[fname] = extract_idents(open(fname).read())  # regex

# Step 2: score files by mention in user's message
mentions = re.findall(r'\b\w{5,}\b', user_msg.lower())
scores = {}
for fname, syms in symbols.items():
    scores[fname] = sum(1 for m in mentions if m in syms)
    # Boost if file already in chat
    if fname in chat_files:
        scores[fname] *= 50

# Step 3: top-N files, joined and truncated to budget
top = sorted(scores, key=scores.get, reverse=True)[:20]
result = "\n".join(format_file_header(f) + "\n" + open(f).read()[:500]
                   for f in top)
# truncate to token budget
```

Loses: cross-file reference graph, PageRank quality, tree-aware rendering.
Keeps: the binary-search trick, the mention-boosting, the per-file cache.

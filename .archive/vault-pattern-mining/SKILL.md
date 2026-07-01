---
name: vault-pattern-mining
description: Mine a personal corpus (Obsidian vault, journal archive, note collection) for hidden patterns — recurring structures, hub-and-spoke notes, taxonomic decay, content-vs-template gaps — then EITHER render the findings as a multi-page website (one page per theme) OR implement the structural fixes each theme prescribes. Phase 7 covers the fix-implementation path. Triggers on "find patterns in my notes", "what's hiding in my vault", "analyze my Obsidian", "hidden patterns", "themes in my writing", "surface what my notes actually say", "build a site from my notes", "what the vault would need to look different", "fix the empty containers", "fix the tag explosion", "implement the [theme N] fix". Use when the user wants to understand the *shape* of their own corpus rather than retrieve a specific fact from it.
---

# Vault Pattern Mining

## What this skill is for

Personal note corpora accumulate faster than anyone reads them. After 1+ years of a vault, journal, or research archive, the writer usually cannot answer "what is this corpus actually about?" — because the answer is structural, not topical. A vault pattern mine surfaces:

- **Hub notes** (most-linked-to files = the gravitational center of a cluster)
- **Tag taxonomy decay** (the same concept written N ways until retrieval fails)
- **Schema drift** (frontmatter conventions that diverged without anyone noticing — bilingual, multi-era, multi-source corpora)
- **Content-vs-template gaps** (places where the *shape* of a note exists but the *substance* never got written)
- **Cross-domain bridges** (notes that connect otherwise-separate clusters)
- **Identity-level patterns** (what the writer argues with themselves about — opposition-rich notes, first-person notes vs. third-person notes, recurring self-instruction)

Output is a multi-page static website, one page per emerging theme, with data visualizations (bar charts, tables, hub lists, timelines) and direct quotes from the source notes as evidence. The site is meant to be read top-to-bottom: index gives the shape, each theme page goes deep.

## When NOT to use this

- User wants to **retrieve a specific fact** from a vault → use `obsidian` skill.
- User wants to **generate a new research vault** → use `deep-research-obsidian` (opposite direction).
- User wants a **single static diagram** of their system → use `architecture-diagram`.
- User wants a **codebase LOC report** → use `codebase-inspection`.
- Corpus is < 50 notes. Pattern detection needs volume. Below 50 notes, just open the files.

## Support files in this skill

- `scripts/analyze_vault.py` — generalized analyzer. Edit the `VAULT` constant, run with `uv run --with pyyaml python3 scripts/analyze_vault.py`. Outputs `/tmp/vault_analysis/summary.json` and `notes.json`. Handles bilingual frontmatter, loose YAML, empty `strong_links` entries, and skips `.git`/`.obsidian`/`.trash`/`node_modules` by default.
- `references/site-template.html` — copy-and-modify template for a single theme page. Same structure as the 7 themes built on 2026-06-02: nav, hero, lede pull-quote, body with data viz blocks, two-column comparisons, source-notes tag cloud, prev/next footer. Replace `{{TEMPLATE_VARS}}` and the body content per theme.
- `references/deploy-recipe.md` — exact `gh` + `vercel` CLI incantations for pushing the built site to a private GitHub repo and publishing to Vercel, with the gotchas (env-var token trap, Vercel CLI PATH, device-flow login, shell-glob `*` expansion).
- `references/fix-implementation-patterns.md` — Phase 7 reference. The 3-layer model for fixes (skill / frontmatter / content), the idempotency rule for migration scripts, the verification pattern (re-run the analyzer to confirm the diagnosis has cleared), and the empty-container meta-finding template. Load this when a Phase 7 fix is being designed.

## Workflow (6 phases)

Phase 1 — Inventory walk. Phase 2 — Parse frontmatter. Phase 3 — Pattern detection (7 lenses). Phase 4 — Theme selection. Phase 5 — Build the site. **Phase 6 — Publish (push to private GitHub repo + deploy to Vercel).**

### Phase 1 — Inventory walk

Walk the vault, count by top-level folder, skip `.git`/`.obsidian`/`.trash`/node_modules. Report shape before analyzing.

```bash
cd /home/thomas/Desktop/Memory  # or wherever
find . -name "*.md" -not -path "./.git/*" -not -path "./.obsidian/*" -not -path "*/.obsidian/*" -not -path "*/pages/*" | wc -l
# (note: many vaults put leaf content under pages/ — count that too)
find . -name "*.md" -not -path "./.git/*" -not -path "./.obsidian/*" | wc -l
```

**Pitfall:** Leaf notes are often inside `pages/` or `_Lot*_*` subfolders, not at the cluster root. The first count is misleading. Use the second.

### Phase 2 — Parse frontmatter

Most personal vaults have frontmatter, but the schema drifts over time and across languages. Build a parser that handles BOTH strict YAML and loose fallback. See `scripts/analyze_vault.py` — it's the analyzer from the 2026-06-02 run, generalized.

Key fields to extract per note:
- `title`, `type`, `cluster`, `importance`
- `tags` (as a list — handle `[a, b]` AND `a, b` AND YAML list blocks)
- `strong_links` / `liens_forts` / equivalent (the per-note link field, regardless of language)
- `opposition_links` / `liens_opposition` / equivalent
- `sources_count` (signal of web-research vs. internal-summary)
- `word_count` of body

**Pitfall:** Bilingual vaults have TWO different schemas. The 2026-06-02 vault had `strong_links` (English) and `liens_forts` (French). Treat them as the same field, with a per-language key map. Same for `title`/`titre`, `created`/`créé`, etc. **Gating check:** if your parser silently produces `None` for the link field on more than 20% of notes, you have a schema-drift problem and Phase 2 must be reworked before any of Phase 3 makes sense.

**Pitfall:** Some `strong_links` entries are `[]` or `['']`. Guard with `if not link: continue` before indexing. The first run of the analyzer crashed on this exact bug.

### Phase 3 — Pattern detection (the 7 lenses)

Apply these analyses in order. Each one tends to surface one or more themes:

1. **Tag frequency distribution.** Top 40 tags. Shape of the tail: how many singletons? 1,228 of 1,585 tags appearing exactly once is a tell. Tag-frequency > 50, > 20, > 10, > 5, > 2, == 1.
2. **Note-type and cluster breakdown.** What kinds of notes exist (concept/sector/company/methodology/...) and which clusters dominate?
3. **Hub detection (in-degree).** For each note, count how many `strong_links` from other notes point at it. Top 25 is the hub structure. A single note with 79+ inbound links is the gravitational center of a cluster.
4. **Cross-domain bridges.** Edges where source-cluster ≠ target-cluster. These are the most informative — they show which notes connect otherwise-separate parts of the corpus.
5. **Opposition density.** Notes with the highest count of `opposition_links` are the most-contested. In a personal corpus, this is often where the writer is arguing with themselves — high opposition density = expert-level self-awareness of where the field is wrong.
6. **Bilingual content sampling.** Read 5-10 notes from each cluster. Look for register differences: first vs. third person, present vs. past tense, prescriptive vs. descriptive, language distribution. The 2026-06-02 vault split cleanly: English = encyclopedic third-person, French = first-person emotional.
7. **Empty-container check.** Walk the directory tree for files matching known "container" patterns (e.g., `Conversations/YYYY/YYYY-MM/YYYY-MM-DD.md` with the same template). Count files where the template is present but the body is empty. This is often the most striking finding.

### Phase 4 — Theme selection (5-8 themes)

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

### Phase 5 — Build the site

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

**Data viz primitives** (already in `assets/style.css`):
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

### Phase 6 — Publish (push to private GitHub repo + deploy to Vercel)

After the user says "push to a private repo" or "publish to Vercel" (or both), do the GitHub side first, then Vercel. **Full step-by-step including all observed pitfalls lives in `references/deploy-recipe.md`** — read that file before deploying. The condensed version:

1. **GitHub:** `git init -b main` → `git add -A` → `git commit -m "Initial site: ..."` → `gh repo create <name> --private --source=. --remote=origin --description "..." --push`. Verify with `gh repo view <name> --json name,visibility,url` (must show `"PRIVATE"`).
2. **Vercel CLI:** `npm install -g vercel`. Binary lands at `/home/thomas/.local/lib/nodejs/node-v22.x.x-linux-x64/bin/vercel` — not on PATH automatically; `export PATH="..."` at the start of each session.
3. **CRITICAL first step — unset the env-var token trap:** `unset VERCEL_TOKEN`. The `~/.bashrc` exports a token that is often a *literal placeholder* (`vcp_6N...DljE` with real `...` in the middle, or a redacted string with `*`s). If unset is skipped, the CLI silently reads it and fails with confusing "scope"/"invalid token"/"must not contain *" errors, and the device-flow prompt never appears. Always unset.
4. **Device-flow login:** `vercel login <email>`. The CLI prints a URL like `https://vercel.com/oauth/device?user_code=XXXX-YYYY`. **Hand that URL + code to the user and wait for them to click Verify.** Run in background with `notify_on_complete=true` and `process(action='wait')` to block. Codes expire in ~5 minutes — re-run if the user is AFK.
5. **Deploy:** `cd /path/to/site && vercel deploy --yes --prod`. Watch for `▲ Production  https://<name>-<hash>-<scope>.vercel.app` and `▲ Aliased  https://<name>.vercel.app`. Both should resolve to the same deployment. Accept the GitHub auto-deploy prompt.
6. **Verify:** curl all paths (`/`, every theme page, both assets), expect 200 + non-zero size. Re-check after 3s. Don't trust "Ready" without curl confirmation.
7. **Cleanup:** kill the local dev server (`process(action='kill', session_id=...)`) so port 8765 doesn't stay bound.

The full pitfall table (env-var trap, `*` glob expansion, browser timeouts on localhost, wrong team scope, `gh` name collisions, build-hangs from stuck tokens) is in `references/deploy-recipe.md` § 3.

## What this skill produces (concrete)

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

## Re-running the analyzer

The script at `scripts/analyze_vault.py` is the generalized version of the 2026-06-02 analyzer. Point it at any vault by editing the `VAULT` constant near the top.

```bash
uv run --with pyyaml python3 scripts/analyze_vault.py
```

Outputs go to `/tmp/vault_analysis/`:
- `summary.json` — all computed stats
- `notes.json` — per-note metadata for downstream processing

The CSS template (`assets/style.css` in the built site) and JS animation (`assets/app.js`) are reusable as-is. The site HTML is hand-written for each vault because the themes are content-specific, but the visual system (colors, typography, layout) carries over.

## Anti-patterns to avoid

- **Don't analyze without inventorying first.** A pattern detector running blind on 1,137 files will surface noise. Inventory gives you the lay of the land and prevents you from over-indexing on a single cluster.
- **Don't surface themes without evidence.** Every theme needs a chart, a table, a quote, or a count. A theme is "the corpus says X" — without data, it's "I felt like X."
- **Don't skip the bilingual/multi-schema check.** Half of personal vaults are written in two eras, two languages, or two contexts. A single-schema parser will silently lose half the corpus.
- **Don't build the site before the themes are written.** Theme pages are evidence-driven. If the evidence isn't there, the theme isn't there. Better to ship 4 strong themes than 7 weak ones.
- **Don't render the site through Markdown-to-HTML converters.** The visual system is bespoke. Hand-write the HTML. md-to-webpage will produce something legible but uninspiring.
- **Don't open the browser to "verify" the site rendered correctly if it might time out.** Curl + process status is the actual verification. Browser is the polish check, not the gate.

---

## Phase 7 — Implement the structural fixes (the payoff path)

The site/analysis is the diagnosis. The structural fix is the cure. Most users who get the analysis will next ask "now implement the fix" — typically by quoting the analysis's "What the vault would need to look different" section verbatim.

**Triggers for Phase 7:**
- "implement the [theme] fix" / "fix the [theme]"
- "what the vault would need to look different" (quoting the analysis template)
- "make the empty containers not empty"
- "fix how we store conversations" / "fix the tag explosion"
- "do the 3-pass fix" / "consolidate the taxonomy"
- "now actually fix it" (after a Phase 5 site was built)

**The fix-implementation loop has 4 sub-steps, repeated per theme:**

### 7.1 — Read the prescriptive section

Each theme page ends with a "What the vault would need to look different" or "What would have to change" section. This is the spec. Read it as a list of concrete, testable changes. If the analysis didn't produce a prescriptive section for a theme, the theme isn't ready for Phase 7 — go back to Phase 4.

### 7.2 — Map the fix to the right layer

Three layers, in order of leverage:

1. **Skill/script level** (e.g. `save-session-to-obsidian` adds auto-detection of decisions → re-running the script retroactively fills the empty containers). The fix lives in code, applies forever.
2. **Frontmatter / metadata level** (e.g. canonical tag taxonomy, type-marker drops). One-shot migration script, then a maintained reference for future tags. Lives at `AI/skills/<topic>/REFERENCE.md`.
3. **Content level** (e.g. rewrite the empty conversation files, delete the empty containers). One-shot delete or rewrite. If the content level needs a new template, that's a Phase 7.1→7.1 loop back into skill/script level.

The 2026-06-02 fixes for theme 07 (Empty Containers) hit all three layers: skill layer (`watch_sessions.py` v1.4 with `detect_decisions()`), metadata layer (none), content layer (delete 4 empty files, 35 broken wikilinks rewritten).

### 7.3 — Write the fix as an idempotent migration script

**The idempotency rule:** a well-written migration script run twice produces the same final state as run once. This is verified by running the script and confirming the second invocation reports 0 changes.

```bash
# First pass: changes
python3 migrate_tags.py --apply
# 358 files changed, 909 changes

# Second pass: must be zero
python3 migrate_tags.py --apply
# 0 files changed, 0 changes
```

This is the cheapest way to prove a migration is correct. Make idempotency a hard requirement, not a nice-to-have. Build it into the script's change-detection logic — only record a change if the visible form of the data differs from the target form, not just if the normalized form differs.

### 7.4 — Verify the fix by re-running the analyzer

The proof that the fix worked is that the original diagnosis no longer fires. Re-run the analyzer from Phase 2 and check the corresponding metric:

| Theme (2026-06-02) | Diagnosis signal | Post-fix signal |
|---|---|---|
| 05 Tag Explosion | 1,585 unique tags, 77% singletons | 1,403 unique tags, 67% singletons, hash count = 0 |
| 07 Empty Containers | 17 files matching the "Log: [empty]" template | 0 files (file deleted, or template replaced with `## Decisions today` placeholder) |
| 02 Bilingual Architect | YAML parse errors in 335 files | YAML errors reduced to 28 (pre-existing edge cases) |

If the post-fix signal is the same as the diagnosis signal, the fix didn't work — re-check Phase 7.1.

### 7.5 — Commit, push, and update the documentation

Each theme's fix is a separate commit. The commit message should reference the theme number and the prescriptive section it implements:

```
vault-tags: migrate 358 notes to 87 canonical forms (analysis theme 05)
vault: empty-containers fix + Decisions section (analysis theme 07)
```

Update `AI/vault-map.md` and `AI/me.md` so the new behavior is documented for the next session. If you created a new skill (e.g. `vault-tags`), it gets a SKILL.md describing when to use it, conventions enforced, and links to the migration script.

**The loop closes:** the analysis was the diagnosis, the fix is the cure, the re-analyzed corpus is the proof. The vault is healthier than it was at the start of the session. The 2026-06-02 Memory vault ran 3 separate fix passes (themes 05, 07, and the meta-finding `AI/empty-containers-fix.md`) before re-running the analyzer to confirm.

---

## Pitfall — long-running deploy process leaks stale state

After Vercel auth via device flow, the login subprocess runs in the background. If the parent session restarts or the login is killed mid-flight, an old `Background process completed` notification may arrive *after* the deploy has succeeded. Don't mistake the late notification for a fresh failure — verify with `gh repo view` and `curl` on the production URL, not by reading the stale process log.

**Tells:** process notification has exit_code=-15 (SIGTERM) or `-9` (SIGKILL), AND the deploy URL is already 200, AND `git log` shows the push commit. The session is fine; the notification is post-hoc.

(See Phase 6 / `references/deploy-recipe.md` for the deploy side; this pitfall is the
"the deploy is done but the terminal notification says otherwise" failure mode.)

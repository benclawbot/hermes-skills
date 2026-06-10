---
name: deep-research-obsidian
description: Use when Thomas says "deep research", "build a vault", or "research [topic]" + Obsidian. Auto-generates a 500+ page interconnected research vault in Obsidian using subagent-driven lot-based generation, 2-stage review, and wikilinks.
version: 1.0.0
author: Thomas
metadata:
  hermes:
    tags: [research, obsidian, vault, subagent]
    related_skills: [research-ingestion]
---

# Deep Research → Obsidian Vault

Auto-generates a 500+ page interconnected research vault in Obsidian on any topic. Pages are dense, linked with wikilinks, include YAML frontmatter, and are organized into lots for scalable generation.

## Trigger Conditions

Load this skill when the user says:
- "deep research on [topic]"
- "build a vault on [topic]"
- "research [topic] and index it in Obsidian"
- "deep research stocks"
- "I want to study [domain] — create an Obsidian vault"
- Any request involving "research" + "Obsidian" + large-scale indexing

## Variables (fill before starting)

```
SUBJECT       : [e.g. "semiconductor stocks", "protein folding", "roman history"]
CLUSTER_CHOISI: [e.g. "Semiconductor Industry", "Biochemistry", "Ancient Rome"]
VAULT_PATH    : /home/thomas/Desktop/Memory
NB_PAGES_TARGET: 500
LOT_SIZE      : 4-5 pages per subagent batch
```

## Workflow

### Phase 0 — Bootstrap (5 min)
1. Create folder structure under `pages/_LotN_Topic/`
2. Write `CLAUDE.md` root with conventions
3. Write `99-Meta/Schema.md` with YAML frontmatter spec
4. Write `99-Meta/Plan.md` listing all lots and pages
5. Create all lot folders BEFORE launching subagents

### Phase 1 — Generation by Lots (subagent-driven)

Per lot (4-5 pages):
1. Dispatch implementer subagent → generates pages in lot folder
2. Dispatch spec reviewer subagent → YAML compliance + wikilinks + no non-Latin chars
3. If issues → implementer fixes → spec reviewer re-reviews
4. Dispatch code quality reviewer → English quality + structure
5. If issues → implementer fixes → code quality re-reviews
6. Lot marked complete

Progress tracked via `pages/_LotN_Topic/progress.md`.

**Anti-hallucination rules:**
- No invented proper names — WebSearch required or page gets `status: to-verify`
- No fabricated dates — use "exact date to confirm" if uncertain
- No unsourced statistics
- No invented quotes — paraphrase neutrally instead
- Non-Latin characters → fix only contaminated pages, not whole lot

### Phase 2 — Linking and MOC (15 min)
1. Generate `_MOC.md` — 3-paragraph intro + pages grouped by lot with 1 sentence each
2. **Intra-vault wikilinks** (added after initial generation):
   - Build link graph: scan all vault files, extract titles from filenames and YAML frontmatter
   - Apply semantic matching rules to identify cross-folder topic connections
   - Per-file cap: 4 new links max (prevents link spam)
   - Insert into `## Links and implications` section if it exists, else append at end
   - Apply via script: write updates directly to filesystem, don't re-read full content per file
3. **Cross-folder bridges** — connect related topic clusters (e.g., Scrum pages → Kanban pages; PM foundations → methodology pages)
4. Post-process broken links — collect `[[Page not yet created]]` links, flag only truly broken ones

### Phase 3 — Quality Audit (10-15 min)
Produce `99-Meta/Audit.md`:
- YAML compliance
- Duplicates
- Contradictions
- Orphan pages (0 inbound links)
- Anemic pages (<600 words)
- Total wikilinks + ratio

### Phase 4 — Debrief
Produce `99-Meta/Debrief.md` with stats, what worked, what went wrong, recommended adjustments.

## Page Format

```markdown
---
title: "Exact Page Name"
type: concept | theory | person | experience | controversy | school | disorder | method | term | debate | work | institution | event
cluster: "{CLUSTER_CHOISI}"
status: verified | to-verify | debated | debunked | hypothetical | stub | needs-sourcing
controversy: low | medium | high
importance: pillar | standard | deep-cut
source_knowledge: internal | web-checked | mixed
sources_count: N
tags: [#tag1, #tag2]
created: YYYY-MM-DD
strong_links: [["[[Page1]]", "[[Page2]]"]]
opposition_links: [["[[Page3]]"]]
---

# Title

> [!info] Summary
> 1-2 sentences clear pitch.

## Definition
2-4 dense paragraphs.

## Context and origin
Who, when, where, intellectual framework.

## Mechanisms / characteristics / details
3-6 paragraphs, concrete examples.

## Nuances, critiques, limits
MANDATORY on all pages.

## Links and implications
Wikilinks contextualized in full sentences. Min 7 outbound wikilinks. Target 8-12.

## Sources
[^1]: Author, *Title*, Publisher, year, URL
```

## Vault Structure

```
{VAULT_PATH}/
├── CLAUDE.md
├── README.md
├── _MOC.md
├── pages/
│   ├── _Lot1_Topic-1/
│   ├── _Lot2_Topic-2/
│   └── _LotN_Topic-N/
├── 99-Meta/
│   ├── Schema.md
│   ├── Plan.md
│   ├── Fact-Check-Log.md
│   ├── Audit.md
│   └── Debrief.md
└── .obsidian/
```

## Known Pitfalls

### Wikilink path normalization — folder vs filename case sensitivity
Obsidian wikilinks are **case-sensitive on the folder path, case-insensitive on the filename**.

**Correct:** `[[People/Alexandra]]` → matches `People/Alexandra.md`  
**WRONG:** `[[people/alexandra]]` → resolves as `people/alexandra.md` (folder `people` doesn't exist; Obsidian vault folders are typically `People/` with capital P)

**The alias form pitfall:** `[[People/Alexandra|Alexandra]]` — the alias portion can be misread as a link target. When extracting link targets from wiki-style content, always use the first segment before the pipe `|`, not the display text.

**`[[overview]]` is ambiguous** — if you need intra-project links, use the full relative path like `[[Projects/liquidity-pulse/overview]]` instead of bare `[[overview]]`, since dozens of files in different folders may share that name.

**Rule for generated content:** always emit `[[Folder/Name]]` with correct folder casing from the schema, never bare names, never lowercase paths.

## Notes
- Lot-based organization from the start — not at the end
- Lot size 4-5 pages avoids subagent stalls
- Recovery spool: if subagent stalls >650s, relaunch with recovered state
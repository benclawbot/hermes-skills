# Lot-Based Generation: Timeout and Decision Rules

## The 10-Minute Rule (from deep-research-obsidian)

Each lot of 4-5 pages should complete in ~10 minutes of subagent work. If a lot runs longer than that:

1. **Stop the subagent** — don't wait for it to finish
2. **Mark the lot partial** — note which pages were completed before timeout
3. **Dispatch a recovery subagent** with checkpoint context to finish remaining pages
4. **Continue to next lot** — don't let one slow lot block the pipeline

## Why This Rule Exists

- Subagents can stall on a single difficult page (hallucination loops, over-research)
- A stuck lot wastes the parent's 600s budget
- Parallel lot generation only works if each lot is time-bounded
- 10 minutes × 4-5 pages = ~2 min per page — sufficient for dense generation

## Resume-from-Checkpoint Pattern

When a subagent times out mid-lot:

```
# On timeout, check what was created
find /vault/pages/_LotN_Topic/ -type f -name "*.md"
ls -la /vault/pages/_LotN_Topic/

# Dispatch recovery subagent
goal="Finish remaining pages in Lot N — pages X, Y, Z were created before timeout"
context="Vault path: /home/thomas/Desktop/Memory
Lot: _LotN_Topic
Already done: [list files]
Remaining: [list from Plan.md]
Plan.md path: /home/thomas/Desktop/Memory/99-Meta/Plan.md"
```

The recovery subagent reads Plan.md, identifies remaining pages, generates them without re-doing completed pages.

## Lot Completion Criteria

A lot is complete when:
- All planned pages for the lot exist as `.md` files in the lot folder
- All pages have valid YAML frontmatter (title, type, cluster, status)
- Spec reviewer has approved all pages in the lot
- Code quality reviewer has approved all pages in the lot

## Anti-Stall Checklist (Per Lot)

Before dispatching a lot subagent, confirm:
- [ ] Lot folder exists and is empty (or has partial progress from prior attempt)
- [ ] Plan.md has the full list of pages for this lot
- [ ] Subagent context includes the exact page list (not "read Plan.md")
- [ ] Subagent knows to self-stop after 10 minutes if not done

## Parallel Lot Strategy

When generating a vault with 10+ lots:
- Dispatch up to 3 lots in parallel initially
- Monitor completion — if one lot stalls, don't wait, move to next
- Stagger lot dispatches: lot 1, 2, 3 → wait for 1 to complete → dispatch 4, 5, 6 → etc.
- Never have more than 3 concurrent subagents (parent session budget limits)

## Session Budget Awareness

The parent session also has a 600s timeout. If generating a large vault:
- Track remaining time before launching next batch
- If <5 min remaining in session, don't launch new lots — let cron handle polling
- Cron job should check lot progress and resume stalled lots

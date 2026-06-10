# Bulk Sub-Agent Skill Creation

**Class**: software-development / skill-management

## Pattern

When delegating bulk skill creation to sub-agents, the default behavior scatters output across wrong directories (category-based subdirs, skill_manage creating in ~/.hermes/skills/<category>/). Sub-agents need explicit target paths and consolidation is almost always required.

## Hard Rules

1. **Create base path first** — `mkdir -p /absolute/path/to/target-dir/` before dispatching sub-agents
2. **Sub-agents scatter by default** — skill_manage creates at `~/.hermes/skills/<category>/` regardless of path hints; always run post-creation consolidation
3. **Consolidation script pattern**:
```bash
for dir in ~/.hermes/skills/pm/pm-*; do
  [ -d "$dir" ] && mv "$dir" /correct/target/ && echo "Moved: $(basename $dir)"
done
rmdir ~/.hermes/skills/pm 2>/dev/null
```
4. **Template refs path** — templates go at `skill-dir/references/template.md` not `skill-dir/template.md`; fix with same mv+mkdir pattern
5. **Verify after every batch** — `find . -maxdepth 2 -name "template.md"` catches root-level misplacements

## Pre-Dispatch Checklist

- [ ] Target base directory created and verified
- [ ] Sub-agents given explicit KNOWN subsets (not "half" — named list)
- [ ] Consolidation script ready to run post-batch
- [ ] Verification commands prepared

## When Sub-Agents Are Unavailable

If `delegate_task` max_concurrent_children=3 and tasks > 3, split into sequential waves. Each wave's consolidation must complete before next wave starts — don't accumulate scattered dirs across waves.

## Reference

See: pm-command-center SKILL.md "PM Sub-Skill Creation Workflow" section
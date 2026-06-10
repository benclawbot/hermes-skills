---
name: pm-080-activity-sequencing
description: Identify and sequence project activities, define dependencies, and build the project network diagram (Tier 2 — core planning artifact)
trigger: "When you have decomposed scope into WBS and now need to order work before building the schedule"
when_to_use: |
  - After WBS is baselined and work packages are defined
  - Before schedule development and critical path analysis
  - When you need to identify which activities can overlap vs. which must be sequential
  - For any project with multiple workstreams that could block each other
inputs:
  - WBS with work packages and descriptions
  - WBS Dictionary
  - resource_calendars (who is available when)
  - known_constraints (hard deadlines, external dependencies)
  - organizational_process_assets (lessons learned, standard activity lists)
workflow:
  1. List all activities — expand each work package into specific activities needed to produce the deliverable. Use verb-noun format (e.g., "Configure database schema", "Conduct user acceptance testing").
  2. Identify dependency types for each activity:
     - Finish-to-Start (FS): A must complete before B starts (most common)
     - Start-to-Start (SS): A must start before B can start
     - Finish-to-Finish (FF): A must finish before B can finish
     - Start-to-Finish (SF): A must start before B can finish (rare)
  3. Add lead and lag times where applicable — a lead allows B to start before A fully completes (e.g., start integration testing 2 days before development finishes). A lag inserts waiting time.
  4. Build the network diagram — use Precedence Diagramming Method (PDM). Draw nodes for activities, arrows for dependencies. Label arrows with dependency type and lead/lag.
  5. Calculate Early Start (ES), Early Finish (EF), Late Start (LS), Late Finish (LF) for each activity using forward pass and backward pass.
  6. Identify the critical path — the longest path through the network (zero float). Activities on the critical path have zero or negative float and any delay directly delays the project.
  7. Identify near-critical paths — activities with very low float (1-3 days) that could become critical with small delays. Flag these for risk monitoring.
  8. Review the sequence with responsible owners — confirm feasibility of dependencies, catch missed relationships.
  9. Document assumptions and constraints in the network diagram notes.
output: |
  - Activity List: all activities with IDs, descriptions, responsible owner, dependencies
  - Project Network Diagram (visual or tabular): shows activity sequence with ES/EF/LS/LF floats
  - Critical Path identification: list of activities on the critical path with total float = 0
  - Near-critical paths with float values
  - Dependency register: all FS/SS/FF/SF relationships with lead/lag times
  - Milestone list: key milestones derived from network logic
tips: |
  - Use a logical diagram, not just a table — visual network diagrams catch impossible sequences that tables hide.
  - Not all FS relationships are hard dependencies — challenge finish-to-start defaults, especially from habit rather than logic.
  - Lead time is powerful but risky — document clearly that activity B starts before A completes and who owns the risk of rework.
  - The critical path can change — recalculate after any significant change to activity durations or sequences.
  - High-float activities are not low priority — they may still be high-value; float just means more scheduling flexibility.
---

# pm-080-activity-sequencing

Identify and sequence project activities, define dependencies, and build the project network diagram.

## When to Use

- After WBS is baselined and work packages are defined
- Before schedule development and critical path analysis
- When you need to identify which activities can overlap vs. which must be sequential
- For any project with multiple workstreams that could block each other

## Inputs

- WBS with work packages and descriptions
- WBS Dictionary
- resource_calendars (who is available when)
- known_constraints (hard deadlines, external dependencies)
- organizational_process_assets (lessons learned, standard activity lists)

## Workflow

1. List all activities — expand each work package into specific activities needed to produce the deliverable. Use verb-noun format (e.g., "Configure database schema", "Conduct user acceptance testing").
2. Identify dependency types for each activity:
   - Finish-to-Start (FS): A must complete before B starts (most common)
   - Start-to-Start (SS): A must start before B can start
   - Finish-to-Finish (FF): A must finish before B can finish
   - Start-to-Finish (SF): A must start before B can finish (rare)
3. Add lead and lag times where applicable — a lead allows B to start before A fully completes (e.g., start integration testing 2 days before development finishes). A lag inserts waiting time.
4. Build the network diagram — use Precedence Diagramming Method (PDM). Draw nodes for activities, arrows for dependencies. Label arrows with dependency type and lead/lag.
5. Calculate Early Start (ES), Early Finish (EF), Late Start (LS), Late Finish (LF) for each activity using forward pass and backward pass.
6. Identify the critical path — the longest path through the network (zero float). Activities on the critical path have zero or negative float and any delay directly delays the project.
7. Identify near-critical paths — activities with very low float (1-3 days) that could become critical with small delays. Flag these for risk monitoring.
8. Review the sequence with responsible owners — confirm feasibility of dependencies, catch missed relationships.
9. Document assumptions and constraints in the network diagram notes.

## Output

- Activity List: all activities with IDs, descriptions, responsible owner, dependencies
- Project Network Diagram (visual or tabular): shows activity sequence with ES/EF/LS/LF floats
- Critical Path identification: list of activities on the critical path with total float = 0
- Near-critical paths with float values
- Dependency register: all FS/SS/FF/SF relationships with lead/lag times
- Milestone list: key milestones derived from network logic

## Tips

- Use a logical diagram, not just a table — visual network diagrams catch impossible sequences that tables hide.
- Not all FS relationships are hard dependencies — challenge finish-to-start defaults, especially from habit rather than logic.
- Lead time is powerful but risky — document clearly that activity B starts before A completes and who owns the risk of rework.
- The critical path can change — recalculate after any significant change to activity durations or sequences.
- High-float activities are not low priority — they may still be high-value; float just means more scheduling flexibility.
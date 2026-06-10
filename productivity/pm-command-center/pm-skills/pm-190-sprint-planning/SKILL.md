---
name: pm-190-sprint-planning
description: Sprint planning — select sprint goal, stories, estimate capacity, and commit to sprint backlog. Tier 2 execution skill.
category: pm
tags: [pm, agile, scrum, sprint, planning, backlog, user-stories]
---

# PM Skill: Sprint Planning (pm-190)

Sprint planning sets the sprint's direction. A well-planned sprint has a clear goal, achievable scope, and realistic commitment. Poor planning leads to missed sprints, burnout, and stakeholder disappointment.

## When to Use This Skill

- At the start of each sprint cycle (typically 1-4 weeks)
- When the product backlog has been refined and prioritized
- When the previous sprint's velocity is known
- When team capacity is defined (availability, PTO, meetings)

## Workflow

### 1. Pre-Sprint Preparation (Done Before the Meeting)

**Inputs Required**:
- Approved, refined product backlog (user stories with acceptance criteria)
- Prior sprint velocity (story points completed)
- Team capacity for upcoming sprint (availability calendar)
- Definition of Done (DoD) established
- Product Owner available for clarifications

**Backlog Refinement** (Grooming, 1-2 days before sprint planning):
- Review upcoming stories
- Break large stories into smaller ones (< 3 days of work)
- Add acceptance criteria where missing
- Estimate story points using planning poker or similar
- Clarify dependencies and risks

### 2. Sprint Planning Meeting

**Duration**: 1-2 hours for a 2-week sprint

**Attendance**: Scrum Master, Product Owner, Development Team

**Agenda**:

#### Part A: Set Sprint Goal (15-30 min)
1. Product Owner presents the sprint objective
2. Discuss strategic context and priorities
3. Team agrees on a Sprint Goal (one coherent objective)
4. The goal should be measurable and meaningful to stakeholders

#### Part B: Select Stories (30-60 min)
1. Product Owner walks through top-priority backlog items
2. Team pulls stories from the top until capacity is reached
3. For each story:
   - Clarify requirements and acceptance criteria
   - Identify dependencies (both internal and external)
   - Adjust estimates if scope clarified
   - Reject stories that are too vague or large (> sprint capacity)
4. Document any assumptions or open questions

#### Part C: Capacity Planning (15-30 min)
1. Calculate team capacity:
   ```
   Available Hours = Total Team Hours × Velocity Factor
   ```
   Where Velocity Factor accounts for:
   - Meetings and ceremonies (~20-25% for Scrum)
   - PTO and holidays
   - Context switching and interrupts
2. Convert story points to capacity using historical velocity
3. Verify selected stories fit within capacity

#### Part D: Commit and Plan (15-30 min)
1. Team commits to the sprint backlog
2. Break stories into tasks (development, testing, review)
3. Assign initial owners to tasks
4. Identify sprint risks and mitigation actions
5. Confirm sprint dates and ceremonies (review, retrospective)

### 3. Define Sprint Commitment

**The Sprint Goal**: One sentence stating what the sprint will deliver.
Example: "Enable credit card payments for orders up to $5,000."

**The Sprint Backlog**: Committed list of stories and tasks.
- Commitment is made by the **team**, not imposed by the PM or PO
- The commitment is to the **goal**, not necessarily every story
- Scope can be renegotiated with PO if new information emerges (but mid-sprint changes are discouraged)

### 4. Post-Planning Actions

- Update sprint board (digital or physical)
- Schedule any external dependencies or vendor deliveries
- Confirm team members have clear task assignments
- Distribute sprint goal to stakeholders

## Story Point Estimation Guide

| Points | Size | Guidance |
|--------|------|----------|
| 1 | Trivial | A few hours of work |
| 2 | Small | Half day to 1 day |
| 3 | Medium | 1-2 days |
| 5 | Large | 2-4 days |
| 8 | Very Large | Needs to be split |
| 13+ | Epic | Must be split before sprint |

**Fibonacci sequence** (1, 2, 3, 5, 8, 13) forces teams to think in ranges, not false precision.

## Common Pitfalls

- **Over-committing**: Taking more than capacity allows
- **Under-refined backlog**: Vague stories cause mid-sprint surprises
- **No sprint goal**: Stories without cohesion or direction
- **PO not available**: Decisions deferred, planning stalls
- **Ignore velocity**: Using aspirational velocity rather than actual
- **Skip task breakdown**: Stories too large to track

## Verification Steps

1. Sprint goal is documented and communicated
2. All selected stories have acceptance criteria
3. Team commitment is unanimous (no coercion)
4. Capacity calculation is documented
5. Dependencies are identified and tracked
6. Sprint board is updated within 24 hours of planning

## Tools

- Sprint board (Jira, Linear, Azure DevOps, Trello, physical)
- Planning poker cards or app
- Velocity tracking spreadsheet
- Definition of Done checklist
- Sprint retrospective from previous sprint

## Exit Criteria

- Sprint goal agreed and documented
- Sprint backlog committed by team
- Capacity planned and verified
- All stories have acceptance criteria
- Dependencies identified and owners assigned
- Stakeholders notified of sprint start and goal

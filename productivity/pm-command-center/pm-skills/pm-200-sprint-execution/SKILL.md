---
name: pm-200-sprint-execution
description: Sprint execution — daily standups, unblocking impediments, managing scope, and tracking sprint progress. Tier 3 execution skill.
category: pm
tags: [pm, agile, scrum, sprint, execution, standup, impediments]
---

# PM Skill: Sprint Execution (pm-200)

Sprint execution is where the plan becomes reality. The PM/Scrum Master role is to protect the team from disruption, remove impediments rapidly, and maintain sprint momentum toward the committed goal.

## When to Use This Skill

- During an active sprint
- When sprint execution is faltering (blocked stories, missed milestones)
- When scope creep or change requests threaten the sprint goal
- At daily standups to unblock the team
- When sprint progress needs to be communicated to stakeholders

## Workflow

### 1. Daily Standup Coordination

**When**: Same time, same place, every day (15 minutes max)

**Who Attends**: Development team (Scrum Master facilitates, Product Owner optional)

**Three Questions Per Team Member**:
1. What did I complete since last standup?
2. What will I work on today?
3. What is blocking me?

**PM/Scrum Master Responsibilities**:
- Keep standup to 15 minutes (no deep-dives)
- Track impediments raised — don't solve them in standup
- Note dependencies between team members
- Identify stories at risk of not completing this sprint
- Verify board is updated before or immediately after standup

**Anti-Patterns to Avoid**:
- Status report to the Scrum Master (team talks to team)
- Problem-solving in standup (park it for after)
- Attendance by optional stakeholders who ask questions
- Skipping standup when "nothing is happening"

### 2. Impediment Management

**Log Impediments Immediately**:
When a blocker is raised in standup or ad hoc:
1. Log it in the sprint impediment tracker
2. Assign an owner (usually Scrum Master)
3. Set target resolution time based on severity

**Impediment Severity**:
| Severity | Impact | Target Resolution |
|----------|--------|-------------------|
| Critical | Sprint goal at risk | < 4 hours |
| High | Story completion delayed | < 24 hours |
| Medium | Efficiency reduced | < 48 hours |
| Low | Minor inconvenience | Next standup |

**Escalation Path for Blockers**:
1. Scrum Master attempts to unblock (first-order resolve)
2. Escalate to project manager if SM cannot resolve
3. Escalate to PO or stakeholder if cross-functional
4. Escalate to steering committee if enterprise-level (budget, contracts, etc.)

### 3. Sprint Progress Tracking

**Daily Metrics to Monitor**:
- Stories completed vs. planned
- Points burned vs. ideal burndown
- Days remaining vs. work remaining
- Blocked time (hours lost to impediments)

**Burndown Chart Review** (daily):
- If ahead of ideal burndown: sustain and protect
- If on track: monitor for emerging risks
- If behind: identify cause, assess recovery options

**Scope Management During Sprint**:

Changes to sprint scope mid-sprint are strongly discouraged. If scope change is requested:
1. Evaluate impact on sprint goal and capacity
2. Negotiate: what can be removed to accommodate?
3. PO formally approves or rejects change
4. If approved: update sprint backlog and burndown
5. Document change and reason for stakeholder reporting

### 4. Protecting Sprint Momentum

**Timeboxing**:
- Enforce timeboxes for all sprint ceremonies
- Protect team from ad hoc meeting requests during sprint
- Shield team from external interrupts when possible

**Risk Monitoring**:
- Watch for stories that are "almost done" but stalled
- Identify when a story should be rolled to next sprint (don't let it drag down velocity)
- Monitor team morale and workload balance

**Stakeholder Communication During Sprint**:
- Do NOT send detailed daily updates (too noisy)
- Do communicate if sprint goal is at risk
- Do update sprint board visibility for stakeholders
- Do facilitate external dependencies on behalf of the team

### 5. Mid-Sprint Course Correction

If progress is significantly behind (velocity < 70% of committed):

1. **Immediate**: Conduct root cause analysis
2. **Short-term**: Identify stories that can be descoped (with PO approval)
3. **Recovery options**:
   - Extend sprint (rare, PO approval required)
   - Add team capacity (pair programming, overtime — use sparingly)
   - Roll incomplete stories to next sprint
4. **Document**: Lessons for next sprint planning

### 6. Sprint Completion Actions

At end of sprint (before review):

- Confirm all completed stories meet Definition of Done
- Ensure stories are demo-ready (deployed to test/staging if applicable)
- Notify PO of any incomplete stories
- Prepare sprint summary for review meeting
- Update velocity history

## Common Pitfalls

- **Scrum Master as secretary**: Taking notes but not removing impediments
- **Ignore early warning signs**: Behind-at-day-3 is recoverable; behind-at-day-8 is not
- **Allow scope creep**: Every mid-sprint addition damages credibility and velocity
- **Over-communicating to stakeholders**: Weekly summary is enough during sprint
- **Skip the burndown**: Without tracking, you lose visibility until the review
- **No consequences for blockers**: Log it and drive to resolution

## Verification Steps

1. Daily standup held at consistent time
2. All impediments logged with owners and target resolution
3. Sprint board updated daily
4. Burndown chart reviewed and action taken if behind
5. Scope changes documented with PO approval
6. Team protected from external interruptions when possible

## Tools

- Sprint board (Jira, Linear, Azure DevOps, physical)
- Burndown chart (built-in or manual)
- Impediment log
- Meeting calendar (protect sprint ceremonies)
- Stakeholder communication template (sprint summary)

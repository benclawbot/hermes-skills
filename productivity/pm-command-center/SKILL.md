---
name: pm-command-center
description: Master PM automation hub. Use this skill when Thomas wants to invoke any PM SOP, generate a specific project artifact, or get an automation status across all PM workflows. It routes to the right sub-skill or directly produces the output.
version: 1.1.0
metadata:
  hermes:
    tags: [project-management, automation, hub, dashboard]
    trigger: [pm, project management, project status, risk register, project charter, status report, closure report]
    trigger_context: "Thomas accessing PM automation — all 37 PM SOP sub-skills are real and fully implemented with templates + generator scripts"
---

# PM Command Center

The central hub for all PM automation. Coordinates 37 sub-skills and provides a live dashboard + REST API.

## Skills Location
`~/.hermes/skills/productivity/pm-command-center/pm-skills/`

## Dashboard + Server
**Dashboard:** `/home/thomas/pm-dashboard.html` — live HTML dashboard, 45 SOP rows, Generate + Upload buttons per SOP.
**Server:** `python3 ~/.hermes/scripts/pm-dashboard-server.py` — serves dashboard at `http://localhost:8765/`, provides REST API.

**Server API:**
```
POST /generate/<skill-id>     → runs generator, returns {output, output_path}
POST /upload/<skill-id>      → multipart upload, saves to /home/thomas/pm-uploads/<skill>/
GET  /api/required-docs/<id> → {documents: ["Doc1", "Doc2", "Doc3"]} — 3 required inputs per SOP
GET  /api/skills             → [{id, skill_id, name, has_generator}, ...]
GET  /api/health             → {status: "ok"}
```

**Skill dir resolution:** glob(`pm-skills/pm-<id>-*`) to handle full dir names like `pm-030-project-charter`.
**Upload dir:** `/home/thomas/pm-uploads/` — server creates subdirs per skill automatically.

## CLI Hub
`python3 ~/.hermes/scripts/pm-generate.py --list` — list all 37 skills
`python3 ~/.hermes/scripts/pm-generate.py pm-030 [output.md] [--project NAME]` — generate document
`~/.hermes/scripts/pm-030` → symlink shorthand (all 37 skills have symlinks)

## Sub-Skills Library — 37 SOPs

All 37 SOP sub-skills under `pm-skills/`, each with `SKILL.md` + `references/template.md` + `references/generate.py`.

### INITIATION PHASE
| # | SOP | Tier | Skill |
|---|-----|------|-------|
| 1.1 | Feasibility Study | 2 | pm-010 |
| 1.2 | Stakeholder Identification & Analysis | 2 | pm-020 |
| 1.3 | Project Charter Development | 2 | pm-030 |
| 1.4 | Business Case Development | 2 | pm-040 |
| 1.5 | Stakeholder Kickoff Meeting | 3 | pm-050 |

### PLANNING PHASE
| # | SOP | Tier | Skill |
|---|-----|------|-------|
| 2.1 | Requirements Elicitation | 3 | pm-060 |
| 2.2 | Scope Definition / WBS | 2 | pm-070 |
| 2.3 | Activity Sequencing (CPM) | 2 | pm-080 |
| 2.4 | Schedule Development (Gantt) | 2 | pm-090 |
| 2.5 | Resource Allocation / RACI | 2 | pm-100 |
| 2.6 | Cost Estimation & Budgeting | 2 | pm-110 |
| 2.7 | Risk Identification & Assessment | 1 | pm-120 |
| 2.8 | Risk Response Planning | 2 | pm-130 |
| 2.9 | Communication Planning | 2 | pm-140 |
| 2.10 | Quality Planning | 2 | pm-150 |
| 2.11 | Procurement Planning | 3 | pm-230 |
| 2.12 | Change Management Plan | 2 | pm-160 |

### EXECUTION PHASE
| # | SOP | Tier | Skill |
|---|-----|------|-------|
| 3.1 | Team Direction & Task Assignment | 3 | pm-310 |
| 3.2 | Status Meetings | 1 | pm-290 |
| 3.3 | Sprint Planning | 2 | pm-190 |
| 3.4 | Daily Standup | 3 | pm-200 |
| 3.5 | Backlog Refinement | 1 | pm-320 |
| 3.6 | Risk Monitoring & Mitigation | 2 | pm-130 |
| 3.7 | Issue Management | 1 | pm-170 |
| 3.8 | Change Control Process | 2 | pm-160 |
| 3.9 | Stakeholder Communication | 1 | pm-290 |
| 3.10 | Quality Assurance / Deliverable Review | 3 | pm-330 |
| 3.11 | Vendor/Procurement Management | 3 | pm-180 |

### MONITORING & CONTROLLING
| # | SOP | Tier | Skill |
|---|-----|------|-------|
| 4.1 | Sprint Review | 2 | pm-210 |
| 4.2 | Sprint Retrospective | 2 | pm-220 |
| 4.3 | Burndown Chart Tracking | 1 | pm-340 |
| 4.4 | Sprint Velocity Measurement | 1 | pm-190 |
| 4.5 | Earned Value Management | 1 | pm-240 |
| 4.6 | Risk Review Meetings | 2 | pm-350 |
| 4.7 | Stage Gate / Milestone Reviews | 2 | pm-300 |
| 4.8 | Schedule Variance Analysis | 1 | pm-240 |
| 4.9 | Budget Variance Analysis | 1 | pm-240 |
| 4.10 | Stakeholder Engagement Monitoring | 3 | pm-360 |

### CLOSURE PHASE
| # | SOP | Tier | Skill |
|---|-----|------|-------|
| 5.1 | Formal Acceptance / Sign-off | 3 | pm-330 |
| 5.2 | Contract Closure | 2 | pm-180 |
| 5.3 | Project Closure Report | 2 | pm-250 |
| 5.4 | Lessons Learned Documentation | 2 | pm-280 |
| 5.5 | Team Demobilization | 3 | pm-260 |
| 5.6 | Project Archiving | 1 | pm-270 |
| 5.7 | Benefits Realization Tracking | 3 | pm-370 |

## Dashboard Design (May 2026 updates)

**Button design — modern style (Thomas: "they look old school", May 2026):**
```css
.gen-btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 7px 16px; background: var(--accent); color: #fff;
  border: none; border-radius: 8px; font-size: 13px; font-weight: 500;
  cursor: pointer; box-shadow: 0 1px 3px rgba(0,113,227,0.25);
  transition: background 0.15s, transform 0.1s, box-shadow 0.15s;
}
.gen-btn:hover { background: #0070e0; transform: translateY(-1px); box-shadow: 0 3px 8px rgba(0,113,227,0.35); }
.gen-btn:active { transform: translateY(0); }
.gen-btn.loading { opacity: 0.7; pointer-events: none; }
.gen-btn.loading::after { content: ''; display: inline-block; width: 11px; height: 11px;
  border: 2px solid rgba(255,255,255,0.35); border-top-color: #fff;
  border-radius: 50%; animation: spin 0.6s linear infinite; }

.upload-btn {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 6px 12px; background: var(--surface-2); color: var(--text-secondary);
  border: 1px solid var(--border); border-radius: 8px; font-size: 12px; font-weight: 500;
  cursor: pointer; transition: background 0.15s, border-color 0.15s, color 0.15s;
}
.upload-btn:hover { background: var(--border); color: var(--text); border-color: #888; }
```

**Output modal — Rendered/Raw tabbed display (May 2026):**
- Uses `marked.js` + `DOMPurify` from `cdn.jsdelivr.net` to render Markdown as styled HTML
- Two tabs: **Rendered** (light-themed HTML) and **Raw Markdown** (monospace)
- Rendered style: **white background, near-black text (#1a1a1a), navy blue (#1e3a5f) table headers with white text, alternating light gray rows, hover highlights in pale blue**
  - H1: near-black text, navy bottom border; H2–H3: navy text, light gray underline
  - Code: red text on light gray background with border; pre blocks: light gray bg with border
  - Blockquotes: navy left border, pale blue background tint
  - This light theme was specifically chosen by Thomas over the original dark theme for readability
- `switchTab(tab)` toggles; `currentRawContent` stores raw text for Copy button
- Copy copies raw Markdown (not HTML) via clipboard API
- Footer shows source file link when available

**Upload modal — Thomas asked for required docs list + upload:**
- 4-step flow: open modal → fetch required docs from `/api/required-docs/<skill-id>` → drag-drop/browse → confirm upload
- `openUploadModal(sopNum, skillId)` fetches and renders the 3 required documents list
- `handleFiles()` stores to `pendingFiles[]`; `confirmUpload()` POSTs via `XMLHttpRequest`
- Server saves to `/home/thomas/pm-uploads/<skill-name>/` and responds with file list

**Thomas's Nav Rule (mandatory):**
Top nav bar contains ONLY the brand mark — green dot + "PM Command Center / automation hub" text in a frosted glass bar. **Never include:** All SOPs, Recent Runs, Projects, "52 Live" badge, Filter button, New Request button. Thomas: *"All SOPs, Recent Runs, Projects, 52 Live, Filter, New Request — they are not useful."*

**Design: incident.io dark** (Thomas's current preference, deep charcoal bg, indigo accent).

**Known issue — Telegram file delivery:** Telegram rejects `.html` uploads. Workaround: copy to `~/pm-dashboard.txt` and send as `MEDIA:/path`; Thomas renames to `.html` after download.

## Automation Tier Reference
- **Tier 1 — Eliminate**: AI handles completely, human just reviews
- **Tier 2 — Accelerate**: AI drafts, human refines and approves
- **Tier 3 — Augment**: AI surfaces options, human decides
- **Tier 4 — Human Only**: No AI involvement (conflict, negotiation, crisis)

## Sprint Helper (absorbed from pm-sprint-helper)
See `references/pm-sprint-helper.md` for sprint planning prep, status reporting, and sprint health checks. Data sources in `~/.hermes/pm-data/`.

## Bulk Sub-Skill Creation Workflow
1. Create ALL skill dirs in ONE known absolute path first (terminal mkdir -p)
2. Sub-agents each own a KNOWN SUBSET — do not let them pick their own paths
3. After sub-agents finish: find scattered dirs, move to correct location, rmdir empty parents
4. Templates go in `pm-skills/pm-XXX/references/template.md` (NOT root level)
5. Generators go in `pm-skills/pm-XXX/references/generate.py`
6. Verify with: `find . -name "template.md" | grep -c "references/"` (must equal total count)
7. Verify no root-level templates: `find . -maxdepth 2 -name "template.md" | wc -l` (must be 0)

## Known Issues

**Skills Created in Wrong Location:** Early batches were inadvertently created under `~/.hermes/skills/pm/` instead of the correct `pm-command-center/pm-skills/` subfolder. A consolidation pass moved all misplaced skills. If a sub-skill is not found, check both paths.

**TUI Freeze — "Windows Too Small":** When a goal session runs many turns with large skill writes, the TUI can freeze showing "windows too small". This is NOT the goal failing — work completes. Check `~/.hermes/state.db` for session status if TUI is frozen.

This skill is a sub-skill of `project-management`.
# Manifest Schema

The full `manifest.json` schema for a spec set. Lives at
`<specs-dir>/manifest.json` (i.e. `~/<build-name>/specs/manifest.json`
for greenfield, or `<target-repo>/specs/<build-name>/manifest.json` for
existing-repo target).

The manifest is the audit log for the spec's whole life — from intake
to build handoff to post-review append-to-project-history.

## Schema

```json
{
  "$schema": "https://build-spec.dev/schemas/manifest-v1.json",
  "build_name": "real-time-collab-whiteboard",
  "version": 1,
  "state": "reviewing",
  "created_at": "2026-06-15T10:00:00Z",
  "updated_at": "2026-06-15T10:32:14Z",

  "user_prompt": "a real-time collab whiteboard",

  "specs": {
    "ux_journey":   { "version": 1, "last_updated_question": null, "last_updated_feedback": null },
    "frontend":     { "version": 1, "last_updated_question": null, "last_updated_feedback": null },
    "architecture": { "version": 1, "last_updated_question": null, "last_updated_feedback": null },
    "backend":      { "version": 1, "last_updated_question": null, "last_updated_feedback": null }
  },

  "feedback_rounds": 0,
  "feedback_round_cap": 3,
  "open_questions_remaining": [],

  "target": {
    "type": "greenfield",
    "path": "/home/thomas/real-time-collab-whiteboard",
    "git_initialized": true
  },

  "history": [
    { "ts": "2026-06-15T10:00:00Z", "event": "intake", "prompt": "a real-time collab whiteboard" },
    { "ts": "2026-06-15T10:00:14Z", "event": "clarify_question",  "n": 1, "q": "Who is the primary user in v1?" },
    { "ts": "2026-06-15T10:00:42Z", "event": "clarify_answer",    "n": 1, "a": "design teams, 2-5 per board" },
    { "ts": "2026-06-15T10:05:00Z", "event": "specs_written",     "files": ["ux_journey", "frontend", "architecture", "backend"] },
    { "ts": "2026-06-15T10:05:01Z", "event": "open_question_asked", "n": 1, "q": "How long should a board keep history?" },
    { "ts": "2026-06-15T10:05:30Z", "event": "open_question_answered", "n": 1, "a": "30d" },
    { "ts": "2026-06-15T10:08:00Z", "event": "feedback_round",    "files_changed": ["frontend.html"], "summary": "tweaked empty-state copy" },
    { "ts": "2026-06-15T10:10:00Z", "event": "approved_for_build","specs_final": ["ux_journey", "frontend", "architecture", "backend"] }
  ]
}
```

## State transitions

```
intake → clarifying → writing → reviewing → (feedback_round)* → approved_for_build → building → built → archived
                                                       ↑                                ↓
                                                       └──── feedback round N+1 ←──────┘
```

| State | Allowed next states | Trigger |
|---|---|---|
| `intake` | `clarifying` | First clarify question sent |
| `clarifying` | `writing` | LLM says `READY` |
| `writing` | `reviewing` | LLM returned the JSON envelope; specs validated |
| `reviewing` | `feedback_round`, `approved_for_build` | User clicks Approve, or replies with feedback |
| `feedback_round` | `reviewing` | LLM applied the diffs; bot re-sent final review |
| `approved_for_build` | `building` | Build agent picked up the manifest |
| `building` | `built` | Build agent reported done |
| `built` | `archived` | User approved the post-build append to project history |

## Field semantics

### `specs.<name>.version`

Increments on every change to that spec, whether by open-question
answer or feedback round. Initial write is version 1. The first open
question that affects it bumps it to 2. The orchestrator writes the
new value when applying a diff.

### `specs.<name>.last_updated_question`

The text of the open question whose answer most recently changed this
spec. `null` if never updated by an open question. Used for
"what changed since I last looked" reports.

### `specs.<name>.last_updated_feedback`

Same, but for feedback rounds. Lets the reader ask "what did the
user change in their last round of feedback?"

### `feedback_rounds` and `feedback_round_cap`

`feedback_rounds` increments on every feedback round. The orchestrator
refuses to start a 4th round (cap is 3). The user is told: *"Three
rounds in. Keep going, or commit and start building with what we
have?"*

### `open_questions_remaining`

Array, not count. Each entry is the full question text. Cleared as
questions are answered. Used by the orchestrator to decide whether to
ask the next question or move to the final review.

### `target.type`

`"greenfield"` or `"existing_repo"`. `"greenfield"` means
`~/<build-name>/` is a fresh git repo. `"existing_repo"` means
`<target-repo>/specs/<build-name>/` is a sub-folder in an existing
repo. Determines where the spec lands and whether the post-build
"append to project history" step applies.

### `target.git_initialized`

For greenfield, true once the orchestrator has run `git init` in
`~/<build-name>/`. For existing-repo target, true if the target repo
already has a `.git/` (which it should, otherwise it's not really an
existing repo).

### `history`

Append-only. Every state transition and every LLM call adds an entry.
The orchestrator never edits or removes history entries. This is the
audit log.

## Event types

| Event | When | Required fields |
|---|---|---|
| `intake` | First message received | `prompt` |
| `clarify_question` | Bot sent a question | `n`, `q` |
| `clarify_answer` | User replied | `n`, `a` |
| `specs_written` | LLM returned the JSON envelope | `files` |
| `open_question_asked` | Open-questions loop sent a question | `n`, `q` |
| `open_question_answered` | User replied to an open question | `n`, `a` |
| `open_question_skipped` | User said "ship it as-is" mid-loop | `skipped_remaining` (count) |
| `feedback_round` | Feedback loop applied diffs | `files_changed`, `summary` |
| `feedback_round_failed_patch` | A diff couldn't be applied | `file`, `section`, `reason` |
| `approved_for_build` | User clicked Approve & build | `specs_final` |
| `build_started` | Build agent picked up the manifest | `agent`, `commit_sha` |
| `build_completed` | Build agent reported done | `commit_sha`, `pr_url?` |
| `build_failed` | Build agent reported failure | `error`, `commit_sha?` |
| `archived` | Post-build append-to-project-history succeeded | `archived_to` (path), `index_section_added` (heading) |

## Post-build append (existing-repo target only)

When `target.type == "existing_repo"` and the build/test/review
passes, the orchestrator appends the spec to
`<target-repo>/specs/index.html` (or whatever the project's main spec
index is). The append is one section per shipped spec, with a
hyperlink to the spec's HTML file.

The `archived` event records:
- `archived_to` — the path of the index file
- `index_section_added` — the heading text that was added

This is the "the project file is the project's architecture history"
behavior. Reading `specs/index.html` from top to bottom = the project's
chronological record of every shipped feature.

For greenfield builds, there is no project index to append to. The
`archived` event is still recorded, with `archived_to: null`.

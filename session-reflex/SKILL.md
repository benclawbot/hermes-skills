---
name: session-reflex
description: Proactively recall relevant past sessions before responding when the user references prior context. Treat session_search as a reflex, not an exception.
triggers:
  - user_references_past
  - vague_continuity
  - unresolved_thread
---

# Session Reflex

Treat `session_search` as a reflex when the user implies prior context. Don't guess — look it up first.

## Trigger Conditions

Invoke `session_search` proactively when:

### 1. Explicit past references
- "last time...", "as we discussed...", "like before...", "earlier we..."
- "didn't we...", "that was the one where..."

### 2. Vague continuity signals
- "I'm still stuck on...", "that didn't work...", "still having the same issue..."
- "remember when..." (even without explicit project name)

### 3. Emotional weight without new context
- Frustration, stuckness, or familiarity without new information → search

### 4. Failure to proceed
- If you don't know what to do next and context feels incomplete → search

### 5. **Decisions that may already exist** (CRITICAL — search BEFORE research)
- The user asks for a vendor URL, API key shape, env var name, model name, or
  any config value that's been set before
- A subagent or external tool is about to fetch "the official" answer
- You're about to guess at a value ("I'll use `api.minimaxi.com`...")
- The user says "check the one for X" — they expect an existing prior decision

**Always search `~/.hermes/.pi/skill-memory.json` and the session DB first.**
The lesson is often there. A 5-second `grep -i` beats a 3-minute subagent
that returns the wrong answer. If you skip this step and the value was
already known, you've burned tokens and credibility for nothing.

**Anti-pattern:** delegating "find the right API URL" to a subagent when
`grep -l "minimax" ~/.hermes/.pi/skill-memory.json` would have returned the
correct base URL in 200ms. Subagents are for tasks the agent can't do
locally — not for tasks you haven't bothered to look up. The session DB
covers years of past decisions; the cost of looking is seconds, the cost
of re-deriving the wrong answer is a broken deploy.

## Search Strategy

**Be specific** when possible:
- `session_search(query="project name or feature")`

**Be broad** when vague:
- `session_search(query="stuck OR issue OR problem + context keywords")`

**OR terms** for FTS5 — the engine defaults to AND, so OR gives broader recall.

## Integration

This skill runs **before** you respond to any message that might reference past context. It fires:
1. On every message that contains trigger keywords
2. As a fallback when you feel context is missing but don't know why

The result is injected into your context automatically. Use it.

## Response Rule

When you recall something relevant:
- Acknowledge briefly: "Found it — we looked at X last Tuesday..."
- Don't make the user repeat themselves
- Link the recall to the current question

When nothing relevant is found:
- Proceed without claiming false continuity
- Don't say "I couldn't find anything" unless directly asked

## Distinguish: user-recall vs. agent-recall

`session_search` is for the agent's *own* continuity. It is **not** the right reflex when the user claims you did something and you don't have a record of it.

| Trigger | Reflex |
|---|---|
| User: "like we did last time" | `session_search` — recall prior work |
| User: "did you apply X?" with no record | search all four sources (memory, user profile, installed skills, past sessions). Zero hits = ask-for-restatement, not a plausible claim |

The asymmetry: when the user is *recalling* their own prior context, false continuity is the failure mode. When the user is *asserting* a prior instruction and you have no trace, the failure mode is fabrication. Different reflexes, different search targets, different response shapes. See `no-replay` for the full missing-trace rule.

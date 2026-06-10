---
name: memory-vault
description: Proactively capture facts, preferences, and corrections to persistent memory. Auto-saves without prompting when trigger patterns are detected.
triggers:
  - user_corrects
  - user_reminds
  - user_prefers
  - environment_fact
  - session_unresolved
---

# Memory Vault

Auto-capture user facts, preferences, corrections, and environment discoveries to persistent memory — no prompting needed.

## Trigger Conditions

When ANY of these fire, use the `memory` tool immediately without asking:

### 1. User correction / reminder
- "remember that...", "don't forget...", "I already told you..."
- Any time the user re-explains something they shouldn't have to
- User says "stop doing X" or "instead, do Y"
- **Identity correction** — e.g., "I'm not Sten, I'm just Thomas" or "remove everything in parentheses". When Thomas provides profile content verbatim, use it directly without paraphrasing, adding synonyms, or reformatting. The exact text he gives is the canonical version.

### 2. Preference signals
- "I prefer...", "I don't like...", "when you X, I want Y instead"
- Any statement about communication style, workflow, or tool preference
- Thomas-specific: wants pushback and devil's advocate challenge — NOT sycophantic or over-comforting responses

### 3. Environment facts
- You discover a path, installed tool, OS quirk, or workaround
- You learn something about the machine or project structure that wasn't in context

### 4. Unresolved context at session end
- If the session ends and something important was left unresolved, capture the thread

## Capture Rules

**User profile facts** → `memory` tool, target=`user`
- Name, role, preferences, communication style, corrections
- "Thomas prefers concise responses" — save this class of fact proactively

**Environment / project facts** → `memory` tool, target=`memory`
- Paths, installed tools, API quirks, workflow discoveries

## Format

Save as **declarative facts**, not instructions:
- ✓ "User prefers one-line responses" 
- ✗ "Always respond in one line"
- ✓ "Node.js installed at /usr/local/bin/node"
- ✗ "Use node instead of nodejs"

## No-Prompt Policy

When a trigger fires:
1. Call `memory` immediately
2. Keep the response minimal — "Got it, saved."
3. Never ask "should I save this?"

## Verification

On session start, read MEMORY.md and USER.md briefly to warm context. You already do this via the memory tool injection — just confirm nothing contradicts what you already have before adding new facts.

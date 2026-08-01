# Prompt Injection for Spec Generation

How to structure `principles.md` + per-type template injection so the
LLM produces consistent voice across all four specs.

## The two-piece structure

Every LLM call receives two things:

1. **`principles.md`** — the voice, the quality bar, the rules
   (self-contained HTML, no images, concrete beats comprehensive, etc.)
2. **The per-type template** (`templates/architecture.md`,
   `templates/backend.md`, etc.) — the section skeleton the LLM fills

`principles.md` is *the same file* for all four calls. The template
differs per call. The LLM applies the principles *through* the
template, not alongside it.

## The injection shape

In the LLM prompt (single call, JSON envelope out):

```
<system>
You are a senior engineer writing a build-ready spec for an
implementer. The spec is the deliverable, not a plan to write
one. The reader is an engineer who will be assigned this
ticket next week, with no context on this conversation.

Apply these principles to every section you write:
<principles.md content>

For this call, fill the <TYPE> spec template:
<templates/<TYPE>.md content>

The build is: <build-name>
The user's original prompt is: "<user's one-liner, verbatim>"

Respond with a JSON envelope:
{
  "<type>":      "<full self-contained HTML string>",
  "open_questions": ["...", "..."]
}
</system>

<user>
<the full clarify-loop transcript>
</user>
```

The transcript is everything the user said during the clarify loop.
The LLM uses it to fill sections that the principles + template alone
can't fill (specific names, numbers, decisions).

## Anti-patterns

### Putting instructions in prose instead of templates

If the prompt says *"include a schema section, an API section, a data
flow section..."* as a numbered list, the LLM will fill them with
slightly different shapes each call. The output is inconsistent across
the four specs.

**Fix:** the template IS the section list, with section rules and
anti-patterns. The LLM doesn't re-derive the structure.

### Letting the LLM decide between HTML and markdown

If the prompt says *"produce a spec document"*, the LLM may emit
markdown (with `#` headings), plain HTML, or a mix. The output is
inconsistent and may not render in Telegram previews.

**Fix:** the prompt says *"respond with a JSON envelope; the string
field is a full self-contained HTML document."* The LLM has no choice.

### Asking the LLM to include images, mermaid, or scripts

If the prompt says *"include a system architecture diagram"*, the LLM
will try to include a mermaid block, an SVG, or `<img src="...">` — all
of which violate principle 8 (self-contained HTML, no external
resources).

**Fix:** the principles file says "ASCII diagrams and inline HTML/CSS
mockups, no images, no mermaid, no scripts." The LLM follows the rule
because it's a rule, not because the prompt mentioned it.

### Per-call rephrasing of the principles

If each call rephrases the principles in the prompt, the LLM applies
them slightly differently each time. The voice drifts.

**Fix:** the principles file is loaded **verbatim** into every prompt.
The LLM sees the same instructions every call. The voice is consistent.

### Open questions as "TBD" in the output

If the LLM can't fill a section, it may emit `[TBD]` or `???` and move
on. The shipped spec has gaps.

**Fix:** the prompt says *"anything you can't fill, surface in the
`open_questions` array, not in the spec."* The LLM has an explicit
place to put uncertainty. The second loop resolves it.

## How the four calls share state

The LLM call is *one* call, not four. The JSON envelope has four
fields. The LLM writes all four specs in a single inference pass, which
gives it the cross-spec consistency we want — the architecture
references the same table names as the backend, the frontend's state
model lines up with the API's idempotency story.

If the four specs were four separate calls, they could drift. One call
means the LLM has all four templates and the full transcript in
context simultaneously.

## The output contract

The LLM must return valid JSON. Validation in the orchestrator:

```js
const envelope = JSON.parse(llmResponse);
assert(typeof envelope.architecture === 'string');
assert(typeof envelope.backend === 'string');
assert(typeof envelope.frontend === 'string');
assert(envelope.ux_journey === null || typeof envelope.ux_journey === 'string');
assert(Array.isArray(envelope.open_questions));
```

If validation fails, the orchestrator retries with a one-line error
message: *"Response was not valid JSON. Return only the JSON envelope."*
Up to 3 retries; after that, the build fails with a clear error and
the user is told to re-run.

## Open-questions-loop prompt shape

The second LLM call is different. It receives the full spec set + the
user's answer to one open question, and returns diffs:

```
<system>
The user answered an open question about <build-name>. Apply the
answer to the affected spec(s). Return only the diffs:

FILE: <path>
SECTION: <section id or marker>
OLD: <the previous text>
NEW: <the new text>

If the change is in a different section than the one named, look
up the actual section by id and use that. If you can't find the
section, add it to a `failed_patches` array with a short reason.

The current spec set:
<full architecture.html>
<full backend.html>
<full frontend.html>
<full ux-journey.html>

The open question was: <text>
The user's answer: <text>
</system>
```

The orchestrator applies each diff by string replacement. If a
`failed_patches` entry comes back, the bot surfaces it to the user and
asks for clarification before moving on.

## Feedback-loop prompt shape

The third LLM call (feedback round) is structurally identical to the
open-questions loop, except the input is the user's free-form
feedback, not a single question. The user might say *"change the empty
state copy to be friendlier"* — the LLM figures out which file and
section that affects and returns a diff.

Hard cap: 3 rounds. The orchestrator tracks `feedback_rounds` in the
manifest and stops the loop after round 3.

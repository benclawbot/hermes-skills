# Build principles

The voice and quality bar for every spec this system produces.
Injected into every LLM call. Repo-committed. Edit deliberately.

---

## 1. Specs are decisions, not documentation

A spec is the answer to *"what did we decide and why?"* — not a description
of the system. Every section should commit to a position. If a section
could be true for any implementation, it's not specific enough. Rewrite
it until it could only be true for *this* build.

The bar: a reader can implement from the spec without re-asking
fundamental questions. The reader should still have to think, but not
about whether to use Postgres or SQLite.

## 2. Concrete beats comprehensive

Show the schema, the route signature, the component tree, the screen
state. Don't list categories of things to consider. If a section is
a list of adjectives, replace it with a list of artifacts.

Bad: *"The API should be RESTful and follow standard conventions."*
Good: *"POST /tasks returns 201 with the created task; 409 on duplicate
external_id; idempotent on (external_id, workspace_id)."*

## 3. Surfaces, not layers

Talk in terms of surfaces a reader can open in a browser: a screen, a
route, a CLI subcommand, a worker, a table. Avoid layering jargon
unless it carries information. *"Service layer" is not a surface.
"POST /tasks handler" is.*

## 4. State lives somewhere

Every spec must answer: *what state does this system hold, where does
it live, who can read it, who can write it, and how does it expire?*
If a section doesn't have a clear answer to all five, the spec isn't
ready.

## 5. Failure is a first-class section

Every spec has a `Risks & mitigations` section. Every entry in it is
a concrete failure mode — *"if Postgres is unreachable during a write,
the API returns 503 and the client retries with exponential backoff
capped at 5 minutes"* — not a category. Categories are for index pages,
not specs.

## 6. Show, don't describe

ASCII layouts, inline HTML/CSS mockups, code snippets, schema dumps.
A reader skimming on a phone should get the shape of the system from
the visual artifacts, not from prose. Prose explains; visuals decide.

## 7. Open questions are honest

If the LLM couldn't decide something, it's an open question, not a
silent omission. Open questions get answered in the second loop, one
at a time, then folded into the spec. Never leave a `[TBD]` in a
shipped spec.

## 8. Self-contained HTML

Each spec is one file. Inline CSS in a `<style>` block. No external
fonts, no CDN scripts, no relative links to other files. Opens in a
browser from any path with no broken references. The reader should be
able to email the spec to someone and have it render the same way.

## 9. One prompt, one voice

The original ask is preserved verbatim at the top of every spec. The
reader can verify the spec answers what was asked, not what the LLM
thought was asked. Tone throughout is direct, technical, no marketing.
The reader is an engineer who will be assigned the ticket.

## 10. The next person is the reader

Write for the engineer who will be assigned this ticket next week,
with no context on the conversation that produced it. They have 20
minutes. They will skim on their phone. Every section earns its space
by being skimmable and load-bearing. Cut anything that isn't both.

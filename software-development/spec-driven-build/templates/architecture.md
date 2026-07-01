# Architecture spec template

Section skeleton for `architecture.html`. Injected verbatim into the LLM
prompt for the architecture call. This is the systems-overview spec —
read alongside the four-section summary strip and the open-questions
list at the end.

> **The CSS in the produced spec is mandatory.** Read
> `references/design-system.md` first. Inline the full `spec-style.css`
> at the top of the file. Do not invent new class names. Do not use
> inline `style=""` for color/font/spacing/layout. Do not use Tailwind
> classes. Do not include `<script>`, `<img>`, `<svg>`, or
> `<link rel="stylesheet" href="...">`.

## Document skeleton

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Architecture · {build-name}</title>
<style>
/* spec-style.css inlined verbatim — see references/design-system.md */
</style>
</head>
<body>
<div class="page">

  <header class="page-head">
    <div class="eyebrow">ARCHITECTURE · {build-name}</div>
    <h1>{one-sentence system summary — what it is and what it isn't}</h1>
    <div class="prompt-box">
      <span class="label">PROMPT</span>
      {verbatim original ask}
    </div>
  </header>

  <div class="summary">
    <div class="cell"><div class="k">RUNTIME</div><div class="v">{Node / Go / Rust / ...}</div></div>
    <div class="cell"><div class="k">STORAGE</div><div class="v">{Postgres / SQLite / ...}</div></div>
    <div class="cell"><div class="k">EXTERNAL</div><div class="v">{count} services</div></div>
    <div class="cell"><div class="k">TRUST</div><div class="v accent">{single box / multi-tenant / ...}</div></div>
  </div>

  <section>
    <div class="sec-head"><span class="num">01</span><h2>System context</h2></div>
    <p class="sec-intro">Where this system sits in the world. What calls it, what it calls, who can reach it.</p>
    <div class="diagram"><pre>{ASCII art using ┌ ─ ┐ │ └ ┘ ▼ ▶ ◀ characters}</pre></div>
    <p class="caption">Solid = sync, dashed = async (convey via -- or ~~), boxes = processes.</p>
  </section>

  <section>
    <div class="sec-head"><span class="num">02</span><h2>Components</h2></div>
    <p class="sec-intro">Each component is a deployable unit (or a clear cluster of units) with a single responsibility.</p>
    <table>
      <thead><tr><th>Component</th><th>Responsibility</th><th>Interface</th><th>Owns</th></tr></thead>
      <tbody>{ one row per component, every column filled }</tbody>
    </table>
  </section>

  <section>
    <div class="sec-head"><span class="num">03</span><h2>Data flow</h2></div>
    <p class="sec-intro">The one or two most important flows, end-to-end. Pick the load-bearing ones; don't draw all flows.</p>
    <div class="diagram"><pre>{ASCII sequence showing client → api → db}</pre></div>
    <p class="caption">Solid arrows = request/response. Dashes = internal calls. Mark async clearly.</p>
  </section>

  <section>
    <div class="sec-head"><span class="num">04</span><h2>State</h2></div>
    <p class="sec-intro">Where state lives, who reads, who writes, how it expires.</p>
    <table>
      <thead><tr><th>State</th><th>Location</th><th>Readers</th><th>Writers</th><th>Expiry</th></tr></thead>
      <tbody>{ one row per state, every column filled }</tbody>
    </table>
  </section>

  <section>
    <div class="sec-head"><span class="num">05</span><h2>Deployment &amp; trust boundaries</h2></div>
    <p class="sec-intro">How this ships, where it runs, what the network looks like.</p>
    <div class="diagram"><pre>{ASCII showing internet → edge → private network → api/worker/db}</pre></div>
    <p><strong>Trust boundary:</strong> {one line: where untrusted input stops being trusted}</p>
    <p><strong>Single box deployable?</strong> {yes / no, and why}</p>
  </section>

  <section>
    <div class="sec-head"><span class="num">06</span><h2>Decisions</h2></div>
    <p class="sec-intro">Tradeoffs weighed, alternatives rejected, with reasons.</p>
    <table>
      <thead><tr><th>Decision</th><th>Chose</th><th>Rejected</th><th>Why</th></tr></thead>
      <tbody>{ one row per load-bearing decision }</tbody>
    </table>
  </section>

  <section>
    <div class="sec-head"><span class="num">07</span><h2>Risks &amp; mitigations</h2></div>
    <div class="risks">
      <div class="row">
        <div class="cell head">Risk</div>
        <div class="cell head">Severity</div>
        <div class="cell head">Mitigation</div>
      </div>
      { one .row per risk }
    </div>
  </section>

  <section>
    <div class="sec-head"><span class="num">08</span><h2>Open questions</h2></div>
    <div class="open-q">
      <div class="q">
        <div class="qt">{the question}</div>
        <div class="qd">{why we need an answer}</div>
        <div class="owner">OWNER · {role}</div>
      </div>
    </div>
  </section>

</div>
</body>
</html>
```

## Section-specific class usage

### `<section>` 01 / 03 / 05 Diagrams
Three places use `.diagram` — the only ASCII art container. Box-drawing
characters: `┌ ─ ┐ │ └ ┘ ┬ ┴ ├ ┤ ┼ ▼ ▶ ◀`. Read the surrounding text in
the spec, then encode the relationships in ASCII. Solid arrows use
`──▶` / `──┐`; async uses `-->` or `~~>`.

### `<section>` 02 Components table
Four columns, every column filled. If you can't name the interface or
what data the component owns, the component isn't well-defined. The
table is the contract.

### `<section>` 04 State table
Five columns, every column filled. State / Location / Readers /
Writers / Expiry. The "Expiry" column matters — without it, retention
is a hidden assumption.

### `<section>` 05 Trust boundary
One sentence. Where does untrusted input stop being trusted? Examples:
- "at the API edge — all input is schema-validated before any handler runs"
- "inside the worker — the queue is the trust boundary; everything else is on a private network"

### `<section>` 06 Decisions
Specific rejections, not "we picked the right tool." Example: "Chose
Postgres, rejected Mongo, because we need transactions and our data is
highly relational."

## Anti-patterns

- ❌ Generic `<header>` / `<section>` without the design-system classes
- ❌ Drawing all data flows in one diagram (pick the load-bearing ones)
- ❌ Missing columns in the Components or State tables
- ❌ Decisions that say "we picked X" without naming the rejected alternative
- ❌ Trust boundary as a paragraph (one sentence or it isn't a boundary)

## Voice

Same as the rest of the spec set. Direct, technical, no marketing.
The reader is the engineer who will deploy this.

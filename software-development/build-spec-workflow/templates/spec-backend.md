# Backend spec template

Section skeleton for `backend.html`. Injected verbatim into the LLM
prompt for the backend call. The closest match in the
`html-effectiveness` reference set is example #16 (implementation
plan), which sets the bar for *concrete* SQL and *real* JSON shapes.

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
<title>Backend · {build-name}</title>
<style>
/* spec-style.css inlined verbatim — see references/design-system.md */
</style>
</head>
<body>
<div class="page">

  <header class="page-head">
    <div class="eyebrow">BACKEND · {build-name}</div>
    <h1>{one-sentence API surface summary — what the backend does}</h1>
    <div class="prompt-box">
      <span class="label">PROMPT</span>
      {verbatim original ask}
    </div>
  </header>

  <div class="summary">
    <div class="cell"><div class="k">RUNTIME</div><div class="v">{Node 22 / Go 1.22 / ...}</div></div>
    <div class="cell"><div class="k">TABLES</div><div class="v">{count}</div></div>
    <div class="cell"><div class="k">STYLE</div><div class="v">{REST / tRPC / gRPC}</div></div>
    <div class="cell"><div class="k">FLAG</div><div class="v accent">{feature_flag}</div></div>
  </div>

  <section>
    <div class="sec-head"><span class="num">01</span><h2>Schema</h2></div>
    <p class="sec-intro">Real SQL, with constraints, indexes, and the reasoning behind non-obvious choices called out.</p>
    <div class="code-block">
      <div class="file-label">packages/db/migrations/0042_tasks.sql</div>
      <div class="code"><pre><span class="cm">-- tasks: the core entity</span>
<span class="kw">CREATE TABLE</span> tasks (
  id           <span class="kw">UUID PRIMARY KEY DEFAULT</span> gen_random_uuid(),
  workspace_id <span class="kw">UUID NOT NULL REFERENCES</span> workspaces(id) <span class="kw">ON DELETE CASCADE</span>,
  title        <span class="kw">TEXT NOT NULL CHECK</span> (length(title) <span class="kw">BETWEEN</span> 1 <span class="kw">AND</span> 500),
  status       <span class="kw">task_status NOT NULL DEFAULT</span> <span class="str">'open'</span>,
  created_at   <span class="kw">TIMESTAMPTZ NOT NULL DEFAULT</span> now(),
  <span class="kw">UNIQUE</span> (workspace_id, external_id)
);</pre></div>
    </div>
  </section>

  <section>
    <div class="sec-head"><span class="num">02</span><h2>API contract</h2></div>
    <p class="sec-intro">Each endpoint, its request/response shape, and its error modes.</p>
    <h3>POST /tasks</h3>
    <p><strong>Idempotency:</strong> key on <code>(workspace_id, external_id)</code>. Repeat calls with the same external_id return the existing row.</p>
    <div class="code-block">
      <div class="file-label">Request</div>
      <div class="code"><pre>{ <span class="str">"title"</span>: <span class="str">"Ship v1"</span>, <span class="str">"external_id"</span>: <span class="str">"jira-1234"</span> }</pre></div>
    </div>
    <div class="code-block">
      <div class="file-label">Response 201</div>
      <div class="code"><pre>{ <span class="str">"id"</span>: <span class="str">"01H8..."</span>, ... }</pre></div>
    </div>
    <table>
      <thead><tr><th>Status</th><th>When</th><th>Body</th></tr></thead>
      <tbody>{ one row per status code, including the boring 200/201 cases }</tbody>
    </table>
  </section>

  <section>
    <div class="sec-head"><span class="num">03</span><h2>Data flow</h2></div>
    <p class="sec-intro">One or two server-side flows. Same ASCII conventions as architecture.</p>
    <div class="diagram"><pre>{server-side sequence: handler → middleware → db}</pre></div>
  </section>

  <section>
    <div class="sec-head"><span class="num">04</span><h2>Idempotency</h2></div>
    <p class="sec-intro">Which operations are idempotent, on what key, and what a replay returns. This is the single most-tested property of a backend.</p>
    <table>
      <thead><tr><th>Operation</th><th>Idempotency key</th><th>Replay returns</th></tr></thead>
      <tbody>{ one row per operation }</tbody>
    </table>
  </section>

  <section>
    <div class="sec-head"><span class="num">05</span><h2>Failure modes</h2></div>
    <p class="sec-intro">What happens when X breaks. The answer is always concrete: error code, retry behavior, user-visible message.</p>
    <table>
      <thead><tr><th>Failure</th><th>Detection</th><th>Response</th><th>Recovery</th></tr></thead>
      <tbody>{ one row per failure mode }</tbody>
    </table>
  </section>

  <section>
    <div class="sec-head"><span class="num">06</span><h2>Key code</h2></div>
    <p class="sec-intro">The two pieces most likely to be done wrong: the migration and the idempotent handler.</p>
    <div class="code-block">
      <div class="file-label">path/to/file</div>
      <div class="code"><pre>{real code}</pre></div>
    </div>
  </section>

  <section>
    <div class="sec-head"><span class="num">07</span><h2>Decisions</h2></div>
    <p class="sec-intro">Tradeoffs rejected. Same table format as architecture.</p>
    <table>
      <thead><tr><th>Decision</th><th>Chose</th><th>Rejected</th><th>Why</th></tr></thead>
      <tbody>{ one row per decision }</tbody>
    </table>
  </section>

  <section>
    <div class="sec-head"><span class="num">08</span><h2>Risks &amp; mitigations</h2></div>
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
    <div class="sec-head"><span class="num">09</span><h2>Open questions</h2></div>
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

### `<section>` 01 Schema — the dark-code block pattern
Every SQL block follows the same shape:
```html
<div class="code-block">
  <div class="file-label">path/to/file.sql</div>
  <div class="code"><pre>
    <span class="cm">-- comment</span>
    <span class="kw">CREATE TABLE</span> ... <span class="str">'literal'</span>
  </pre></div>
</div>
```
Color usage: `.kw` for SQL keywords, `.str` for string literals,
`.cm` for comments. The four classes are the *only* syntax
highlighting the design system supports.

### `<section>` 02 API contract — request/response pairs
Always two `.code-block` panels per endpoint: one labeled "Request",
one labeled "Response 201" (or whatever the success status is). Then
an error-status table.

### `<section>` 05 Failure modes
Four columns: Failure / Detection / Response / Recovery. No "handle
gracefully." Recovery is concrete: "client retries with exponential
backoff capped at 5 minutes" or "operator page within 1 minute."

### `<section>` 06 Key code
Two or three snippets, not the whole system. The migration, the
handler, and one more. Reader's job: copy the patterns, not find them.

## Anti-patterns

- ❌ `// task object` placeholders in JSON — show the real shape
- ❌ `...` placeholders in SQL where they affect correctness
- ❌ Status code tables that skip the success cases (200/201/204 are
  still part of the contract)
- ❌ "Idempotent on request ID" without saying what a replay returns
- ❌ "Handle gracefully" in the failure modes column
- ❌ Decisions that say "we chose X" without naming the rejected alternative

## Voice

Direct, technical, no marketing. The reader is the engineer who will
write the migration and the handler. Show the SQL, show the JSON,
show the failure mode. Skip the prose.

# Frontend spec template

Section skeleton for `frontend.html`. Injected verbatim into the LLM
prompt for the frontend call. Multi-screen handling lives in
`templates/ux-journey.md` (a separate 4th spec).

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
<title>Frontend · {build-name}</title>
<style>
/* spec-style.css inlined verbatim — see references/design-system.md */
</style>
</head>
<body>
<div class="page">

  <header class="page-head">
    <div class="eyebrow">FRONTEND · {build-name}</div>
    <h1>{one-sentence summary of the frontend surface}</h1>
    <div class="prompt-box">
      <span class="label">PROMPT</span>
      {verbatim original ask}
    </div>
  </header>

  <div class="summary">
    <div class="cell"><div class="k">FRAMEWORK</div><div class="v">{React / Svelte / ...}</div></div>
    <div class="cell"><div class="k">SURFACES</div><div class="v">{count}</div></div>
    <div class="cell"><div class="k">STATE</div><div class="v">{server-of-truth / cache / local}</div></div>
    <div class="cell"><div class="k">FLAG</div><div class="v accent">{feature_flag}</div></div>
  </div>

  <section>
    <div class="sec-head"><span class="num">01</span><h2>Surfaces</h2></div>
    <p class="sec-intro">Routes, modals, drawers — the map of where the user goes.</p>
    <table>
      <thead><tr><th>Route</th><th>Surface</th><th>Owns</th></tr></thead>
      <tbody>{ one row per surface }</tbody>
    </table>
  </section>

  <section>
    <div class="sec-head"><span class="num">02</span><h2>Component tree</h2></div>
    <p class="sec-intro">A tree, not a list. State ownership is the answer to "if this state changes, which component re-renders?"</p>
    <div class="diagram"><pre>{ASCII tree, indented}</pre></div>
    <p class="caption">Tree only — no props, no state, no logic. State model is in section 03.</p>
  </section>

  <section>
    <div class="sec-head"><span class="num">03</span><h2>State model</h2></div>
    <p class="sec-intro">What state lives where, who reads, who writes, how it expires.</p>
    <table>
      <thead><tr><th>State</th><th>Lives in</th><th>Optimistic?</th><th>TTL</th></tr></thead>
      <tbody>{ one row per meaningful state }</tbody>
    </table>
    <p><strong>Server of truth:</strong> {one line}</p>
    <p><strong>Cache invalidation:</strong> {when does the client re-fetch}</p>
  </section>

  <section>
    <div class="sec-head"><span class="num">04</span><h2>Mockups</h2></div>
    <p class="sec-intro">Not pixel-final. Enough to show layout, hierarchy, and the design tokens in use.</p>
    <div class="mocks">
      <div class="mock">
        <div class="mock-label">DEFAULT STATE</div>
        <div class="mock-body">
          {real HTML/CSS using the design system classes: .card-mock, .comment, .avatar, .composer, etc.}
        </div>
      </div>
      <div class="mock">
        <div class="mock-label">EMPTY STATE</div>
        <div class="mock-body">{...}</div>
      </div>
      <div class="mock">
        <div class="mock-label">ERROR STATE</div>
        <div class="mock-body">{...}</div>
      </div>
      <div class="mock">
        <div class="mock-label">KEY INTERACTION</div>
        <div class="mock-body">{...}</div>
      </div>
    </div>
  </section>

  <section>
    <div class="sec-head"><span class="num">05</span><h2>Interactions</h2></div>
    <p class="sec-intro">Clicks, keys, gestures, animations. What triggers, what the user sees, what state changes.</p>
    <table>
      <thead><tr><th>Trigger</th><th>Result</th><th>Loading?</th><th>Error?</th></tr></thead>
      <tbody>{ one row per interaction }</tbody>
    </table>
  </section>

  <section>
    <div class="sec-head"><span class="num">06</span><h2>Design tokens</h2></div>
    <p class="sec-intro">The CSS variables in use. New tokens go here, not as hardcoded values.</p>
    <table>
      <thead><tr><th>Token</th><th>Value</th><th>Used for</th></tr></thead>
      <tbody>{ one row per token }</tbody>
    </table>
  </section>

  <section>
    <div class="sec-head"><span class="num">07</span><h2>Key code</h2></div>
    <p class="sec-intro">The 2-3 snippets most likely to be done wrong. Optimistic mutation, keyboard handler, focus trap.</p>
    <div class="code-block">
      <div class="file-label">path/to/file.ts</div>
      <div class="code"><pre>{real code with <span class="kw">keywords</span> and <span class="str">strings</span> colored}</pre></div>
    </div>
  </section>

  <section>
    <div class="sec-head"><span class="num">08</span><h2>Risks &amp; mitigations</h2></div>
    <div class="risks">
      <div class="row">
        <div class="cell head">Risk</div>
        <div class="cell head">Severity</div>
        <div class="cell head">Mitigation</div>
      </div>
      { one .row per risk; severity pill uses .sev.high / .sev.med / .sev.low }
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

### `<section>` 04 Mockups
Use the design-system mockup classes:
- `.mocks` wraps the grid
- `.mock` is each state panel
- `.mock-label` is the gray-150 header with the state name
- `.mock-body` is the padded 22px content area
- Inside: `.card-mock` (16px padding, gray-300 border, ivory bg) for card shapes; `.comment` / `.avatar` / `.bubble` for thread/chat shapes; `.composer` for input bars

### `<section>` 07 Key code
Every code block follows the same shape:
```html
<div class="code-block">
  <div class="file-label">apps/web/src/hooks/useTasks.ts</div>
  <div class="code"><pre><span class="kw">function</span> <span class="fn">useTasks</span>() { ... }</pre></div>
</div>
```

### `<section>` 08 Risks
Every risk row:
```html
<div class="row">
  <div class="cell">{concrete failure mode}</div>
  <div class="cell"><span class="sev high">HIGH</span></div>
  <div class="cell">{concrete mitigation}</div>
</div>
```

### `<section>` 09 Open questions
Same `.q` markup as ux-journey and backend. The OWNER tag is the row's commitment — without it, the question is unfunded.

## Anti-patterns (these broke the reference match in early runs)

- ❌ `<header>` / `<section>` / `<h1>` without the design-system classes
- ❌ `<p class="prompt">` — the class is `prompt-box`, with `<span class="label">PROMPT</span>` inside
- ❌ Hardcoded colors anywhere in the body (`#D97757`, `red`, etc.) — use `var(--clay)` or the class
- ❌ Tailwind classes (`bg-clay-500`, `flex`, etc.) — the file has no build step
- ❌ `<img>`, `<svg>`, `<script>`, `<link rel="stylesheet" href="...">` — the file must be self-contained
- ❌ "Pixel-perfect mockups attached" — mockups live inline as real HTML/CSS

## Voice

Engineer-is-the-reader. The frontend spec is the one designers will
read first — make sure the inline mockups earn their place by being
*rendered* HTML, not bullet lists.

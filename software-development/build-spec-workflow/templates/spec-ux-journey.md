# UX-journey spec template

Section skeleton for `ux-journey.html`. The 4th spec, included when
the build is multi-screen (tabs, pages, wizard, dashboard + detail
view, settings, onboarding). Sent first in the Telegram review — the
executive view, designer-readable, engineer-actionable.

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
<title>UX journey · {build-name}</title>
<style>
/* spec-style.css inlined verbatim — see references/design-system.md */
</style>
</head>
<body>
<div class="page">

  <header class="page-head">
    <div class="eyebrow">UX JOURNEY · {build-name}</div>
    <h1>{Persona or build summary, one sentence}</h1>
    <div class="prompt-box">
      <span class="label">PROMPT</span>
      {verbatim original ask}
    </div>
  </header>

  <div class="summary">
    <div class="cell"><div class="k">PERSONAS</div><div class="v">{count}</div></div>
    <div class="cell"><div class="k">SCREENS</div><div class="v">{count}</div></div>
    <div class="cell"><div class="k">PRIMARY FLOW</div><div class="v">{n steps}</div></div>
    <div class="cell"><div class="k">V1 SUCCESS</div><div class="v accent">{one-line criterion}</div></div>
  </div>

  <section>
    <div class="sec-head"><span class="num">01</span><h2>Personas</h2></div>
    <p class="sec-intro">Who is using this, what they came to do. ≤3 personas for v1.</p>
    <div class="persona">
      <div class="name">{Name} · {Role}</div>
      <div class="role">{one-line context}</div>
      <div class="quote">"{what they care about}"</div>
    </div>
    { one .persona per persona }
  </section>

  <section>
    <div class="sec-head"><span class="num">02</span><h2>Primary journey</h2></div>
    <p class="sec-intro">The one path that must work end-to-end in v1. Numbered steps, each a verb.</p>
    <div class="journey">
      <div class="journey-step">
        <div class="step-num">1</div>
        <div class="step-body">
          <h3>{action verb}</h3>
          <p>{what happens, including empty/loading states}</p>
        </div>
      </div>
      { one .journey-step per step }
    </div>
  </section>

  <section>
    <div class="sec-head"><span class="num">03</span><h2>Screen-by-screen</h2></div>
    <p class="sec-intro">One panel per screen. Layout sketch, key interactions, states, transitions.</p>
    <div class="screen">
      <div class="screen-head">
        <span class="route">/path</span.route>
        <span class="name">{Screen name}</span>
      </div>
      <div class="screen-body">
        <p><strong>Purpose:</strong> {one line}</p>
        <p><strong>Layout:</strong> {describe regions, then a real <pre> ASCII sketch OR a <div> mockup}</p>
        <p><strong>Key interactions:</strong></p>
        <ul>{bullets, each a concrete user action and what happens}</ul>
        <div class="states">
          <div class="state"><div class="k">DEFAULT</div>{description}</div>
          <div class="state"><div class="k">LOADING</div>{description}</div>
          <div class="state"><div class="k">EMPTY</div>{description}</div>
          <div class="state"><div class="k">ERROR</div>{description}</div>
        </div>
        <p><strong>Transitions:</strong> in from {x}, out to {y}</p>
      </div>
    </div>
    { one .screen per screen }
  </section>

  <section>
    <div class="sec-head"><span class="num">04</span><h2>Navigation map</h2></div>
    <p class="sec-intro">How the screens connect. ASCII grid.</p>
    <div class="diagram"><pre>{ASCII showing login → home, home ↔ settings, etc.}</pre></div>
  </section>

  <section>
    <div class="sec-head"><span class="num">05</span><h2>Edge cases</h2></div>
    <p class="sec-intro">What happens at boundaries: first-time user, network failure, permission denied.</p>
    <div class="open-q">
      <div class="q">
        <div class="qt">{the situation}</div>
        <div class="qd">{what the system should do}</div>
      </div>
    </div>
  </section>

  <section>
    <div class="sec-head"><span class="num">06</span><h2>Open questions</h2></div>
    <div class="open-q">
      <div class="q">
        <div class="qt">{the question}</div>
        <div class="qd">{why we need an answer before building}</div>
        <div class="owner">OWNER · {role}</div>
      </div>
    </div>
  </section>

</div>
</body>
</html>
```

## Section-specific class usage

### `<section>` 01 Personas
Each persona is a `.persona` card. The `.quote` element uses the clay
left-border pattern — never invent metrics for personas; the persona
is qualitative, not quantitative.

### `<section>` 02 Primary journey
Steps are clay circles (`.step-num`) connected by gray vertical
lines (auto-applied via `::after` in the CSS). Each `.step-body h3`
is a verb. Numbering is automatic — the LLM writes the steps in
order, the CSS draws the line.

### `<section>` 03 Screen-by-screen
Each screen is a `.screen` panel:
- `.screen-head` is the gray-150 header with the route chip and the name
- `.screen-body` is the padded 22px content area
- `.states` is a grid of mini-cards showing the major states
- Each `.state` is ivory bg with a `.k` (mono uppercase) label

**Inside the screen body**, use real CSS classes for layouts:
- `.mocks` and `.mock` if showing two side-by-side states
- `.card-mock` for card-shaped content
- `.comment` / `.avatar` for thread-shaped content

Do NOT use `<img>` or external SVGs for the screen layout sketches.
Use ASCII art in a `<pre>` inside `.diagram`, or inline HTML/CSS
mockups.

### `<section>` 04 Navigation map
The single ASCII diagram of how the screens connect. The reader
should be able to look at it for 5 seconds and understand the
app's structure.

### `<section>` 05 Edge cases
Use the same `.q` markup as open questions, but WITHOUT the
`.owner` line. Edge cases are decisions the spec has made, not
questions the user needs to answer. (Open questions are in
section 06, with owners.)

### `<section>` 06 Open questions
Same `.q` markup, WITH the `.owner` line. The owner is the
person who needs to answer before building.

## Anti-patterns

- ❌ Persona with invented metrics ("does 50 tasks per day")
- ❌ Journey step that isn't a verb
- ❌ Screen without a `.states` grid (always include at minimum:
  default, loading, empty, error)
- ❌ Navigation map as a list of routes (it's a diagram of *flow*)
- ❌ Edge case without a `.qd` (the system behavior must be
  specified, not left open)
- ❌ Open question without an OWNER (unowned questions don't get
  answered)

## Voice

Direct, technical, no marketing. This is the spec a designer
will read first, then an engineer. Both should be able to act on
it without re-asking what was decided.

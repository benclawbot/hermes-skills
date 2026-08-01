# Design-Only Rewrite Recipe

A class of work that comes up often: the user shows a reference design
(screenshot, Figma link, mockup) and says "use this exact design" for
an existing app. **No logic changes** — every handler, every state
machine, every API call stays untouched. Only the visual layer
re-skins.

This is distinct from a normal port (which moves behavior between code
shapes) and from a greenfield build (no existing code to preserve). The
constraint is: rewrite the *appearance*, leave the *behavior* alone.

## The Five-Step Recipe

### 1. Inventory the visual atoms before touching anything

Read the target's `App.tsx` (or equivalent root) end-to-end. Build a
mental map of:

- **Palette tokens** (named colors, accents, page bg, text, borders).
  The reference will have a small set of named colors (`#635BFF`,
  `#F8F9FF`, `#1A1A1A`, `#6B7280`, `#E5E7EB`) — map the target's
  current palette to these, then expand as needed.
- **Surface hierarchy**: page bg, card bg, nested card bg, input bg.
  Reference designs usually have 2-3 surface levels max.
- **Border radius scale**: cards (`rounded-3xl` ≈ 1.5rem), buttons
  (`rounded-full` for primary CTA, `rounded-2xl` for secondary), input
  fields (`rounded-2xl`), pills (`rounded-full`).
- **Shadow scale**: usually one "soft" card shadow
  (`0 24px 48px -12px rgba(0,0,0,0.04)`) plus one colored button glow
  (`0 8px 24px ${accent}40`).
- **Typography**: usually a single sans-serif (Inter), with weights
  `font-medium`, `font-semibold`, `font-bold`, `font-black` and a
  tracking scale (`tracking-tight` for big headers, `tracking-wider`
  for labels, `tracking-[0.2em]` for all-caps microcopy).

### 2. Map reference palette to a single ACCENT object

Define the new palette in one place at the top of the file. Reference
it from every restyle. Don't sprinkle hex codes inline.

```tsx
const ACCENT = {
  violet: '#635BFF',         // primary brand
  violetDeep: '#4F46E5',     // gradient stop / hover
  violetLight: '#8B7DFF',    // gradient stop / accent
  pageBg: '#F8F9FF',         // app background
  card: '#FFFFFF',           // card surface
  text: '#1A1A1A',           // headings
  textMuted: '#6B7280',      // body / microcopy
  border: '#E5E7EB',         // card + input borders
  borderDashed: '#D1D5DB',   // drop-zone border
  emerald: '#10b981',        // success state (preserved)
}
```

### 3. Swap the page background + card surfaces

Find the root `<div className="min-h-screen ...">` and swap the
background to `ACCENT.pageBg` and text color to `ACCENT.text`. Every
"card" container (was `bg-slate-900/60` glass-panel) becomes
`bg-white border border-stone-200/60 rounded-3xl shadow-xl` or
inline-styled equivalent.

```tsx
// before
<div className="rounded-2xl p-5" style={{ background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(71,105,139,0.3)' }}>

// after
<div className="rounded-3xl p-6 bg-white" style={{ border: `1px solid ${ACCENT.border}`, boxShadow: '0 24px 48px -12px rgba(0,0,0,0.04)' }}>
```

### 4. Swap the primary CTA to a pill gradient

The reference design's signature element is a rounded-full primary
button with a gradient + colored glow. Don't fake it with `rounded-2xl`
or solid color — the pill shape is the brand signal.

```tsx
<button
  className="w-full py-3.5 rounded-full text-xs font-black uppercase tracking-[0.15em] text-white active:scale-95"
  style={{
    background: `linear-gradient(135deg, ${ACCENT.violet}, ${ACCENT.violetDeep})`,
    boxShadow: `0 10px 24px ${ACCENT.violet}40`,
  }}
>
  {/* leading play-in-circle icon */}
  <span className="w-5 h-5 rounded-full mr-2 inline-flex items-center justify-center" style={{ background: 'rgba(255,255,255,0.22)' }}>
    <PlayIcon className="w-3 h-3" />
  </span>
  Generate
</button>
```

Disabled state must drop both the gradient AND the glow:

```tsx
style={{
  background: isDisabled ? '#E5E7EB' : `linear-gradient(135deg, ${ACCENT.violet}, ${ACCENT.violetDeep})`,
  boxShadow: isDisabled ? 'none' : `0 10px 24px ${ACCENT.violet}40`,
}}
```

### 5. Swap icons, dropzones, status panels to the reference pattern

Specific swaps that come up in nearly every "Stripe-style" reference:

| Current (dark theme) | Reference (light theme) |
|---|---|
| Dashed dropzone: `border-2 border-dashed` with `UploadCloud` icon centered, no wrapper | Same border, but icon wrapped in `w-10 h-10 rounded-full bg-white border` circle, then label, then microcopy in `text-[10px] uppercase tracking-wider text-stone-400` |
| Status panel: `<FileText className="w-16 h-16 text-slate-600" />` + heading + body | Gradient logo box (`w-16 h-16 rounded-2xl bg-gradient-to-br from-violet to-violetLight shadow-xl`) + Sparkles icon, then big heading (`text-3xl sm:text-4xl font-black tracking-tight`), then body, then chip pills (`Anthropic DOCX`, `FR/EN`) |
| Process state: `<Loader2 className="animate-spin" />` | Same spinner, but wrapped in the gradient logo box matching the empty-state logo |
| Submit button leading icon: `<PlayCircle className="w-4 h-4" />` | Same icon, but wrapped in `w-5 h-5 rounded-full` with `background: rgba(255,255,255,0.22)` — the play-in-circle is the reference signature |
| Language toggle: dark slate with light text | Light grey bg (`#F1F2F6`), white active state, brand-violet text, `rounded-full` |
| Section labels: `text-[11px] font-semibold text-slate-200 uppercase tracking-widest` | `text-[11px] font-bold uppercase tracking-wider text-stone-700` (slightly darker, more readable on white) |

## Global CSS fights (Tailwind v4 + custom `index.css`)

Many existing apps have a global stylesheet that hard-overrides
certain elements. The most common offender:

```css
button[type="submit"]:not(:disabled) {
  background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.35) !important;
}
```

This will fight any className-based restyle. **Two ways out:**

1. **Inline `style` with higher-specificity logic.** Style attributes
   already win over `!important` on a selector — except the rule uses
   `!important` too. In that case, you need to either (a) edit the
   `index.css` to remove the rule, or (b) accept that the gradient
   comes from the global rule and only swap colors via CSS variables
   on `:root`. For a pure design-only rewrite, **editing `index.css`
   is in-scope as long as you don't change the rule's intent** —
   just change the color values to match the new palette.

2. **Don't use `type="submit"` for the new button.** If the form
   doesn't strictly need a submit button (e.g. you have a custom
   `onClick` handler), use `type="button"` and the global rule
   won't apply.

Verify the global rule before assuming your className swap won. Open
`index.css`, search for `button` selectors, and look for any
`!important` declaration.

## Verifying a design-only rewrite

The non-negotiable check after a design-only rewrite: **does the app
still do the same things?** Run a mental feature audit against the
original:

- File upload accepts the same types and triggers the same handler.
- Submit calls the same API / state machine.
- Errors render where they did before (just restyled).
- Status state machine still cycles through EXTRACTING_AUDIO →
  UPLOADING → TRANSCRIBING → PROCESSING → COMPLETED with the same
  visible indicators.
- Export / download still produces the same file.
- Mobile responsive behavior is unchanged (if you didn't intend to
  change it).

**The `tsc --noEmit` + `vite build` check is necessary but not
sufficient.** A typecheck-clean build means you didn't break the type
shape. The behavior audit is what proves you didn't break the
functionality. Run the dev server, exercise the happy path
(upload → submit → wait for result → export), then exercise an error
path (bad file type, oversized file, missing title).

## Common pitfalls

- **Forgetting to update the language toggle** in the top bar when
  you restyle the form. The toggle is usually in the same component
  as the form, but sometimes lives in a header. Audit both.
- **Keeping the original dark `prose` styles** on a long-content
  area (markdown renderer). Light themes need `prose-stone` not
  `prose-invert`, otherwise headings render as light grey on white.
- **Forgetting the dropzone's hover state.** The reference design
  has a subtle color shift on hover (`!bg-[#635BFF08]`). Without it
  the dropzone looks inert.
- **Letting the `Input` component stay dark.** If there's a shared
  `Input` component with hard-coded dark classes (`bg-slate-900
  text-slate-100`), either (a) override the classes via `className`
  prop with `!important` (`!bg-[#F9FAFB] !text-[#1A1A1A] ...`), or
  (b) inline the input rather than reusing the component. Inlining
  is cleaner when you're doing a full visual rewrite anyway.
- **Gradient direction is a brand signal.** The reference uses
  `linear-gradient(135deg, ${accent}, ${accentDeep})` — 135deg
  (top-left to bottom-right). 90deg (horizontal) or 180deg (vertical)
  look subtly wrong. Match the angle.
- **Shadow color should match the accent, not be neutral.** The
  primary button's glow is `boxShadow: '0 10px 24px ${accent}40'`
  (accent + 40 alpha). A neutral shadow on a colored gradient looks
  disconnected.

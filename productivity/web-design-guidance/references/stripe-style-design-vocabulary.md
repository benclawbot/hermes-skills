# Stripe-style ("clean SaaS") design vocabulary

A condensed knowledge bank for the recognizable "Stripe / Linear / Notion-style" look — the visual language behind MeetingMind, the MindDrop reference mockup, and most modern B2B SaaS dashboards. Use this when the user shares a screenshot in this style and says "use this exact design" or "match this look", or when you need to choose a default that *looks current*.

## Palette (cool purple primary, near-white background)

| Token            | Hex       | Usage                                           |
| ---------------- | --------- | ----------------------------------------------- |
| `bg.canvas`      | `#F8F9FF` | Page background (very light cool off-white)     |
| `bg.card`        | `#FFFFFF` | Card surface, modals, popovers                  |
| `text.primary`   | `#1A1A1A` | Headings, primary body                          |
| `text.secondary` | `#6B7280` | Microcopy, helper text, disabled labels         |
| `border.subtle`  | `#E5E7EB` | Card borders, dividers, input borders           |
| `border.dashed`  | `#D1D5DB` | Dashed upload-zone border, neutral              |
| `brand.primary`  | `#635BFF` | Primary CTAs, active states, brand logo         |
| `brand.accent`   | `#8B7DFF` | Gradient pair, secondary accents                |
| `brand.press`    | `#4F46E5` | Gradient pair (deep end), pressed state         |
| `surface.tint`   | `#F3F4F6` | Badge background, soft chip                     |

**Primary CTA = gradient `from-[#635BFF] to-[#4F46E5]`** with a colored shadow `shadow-xl shadow-[#635BFF]/30`. Never plain `bg-indigo-600` — it reads as a different product.

**Surface rules:**
- Page background is *always* `#F8F9FF` (not `#FFFFFF`); cards float on it.
- Cards: `rounded-3xl` (24px) for the main card; `rounded-2xl` (16px) for nested.
- Shadows: `shadow-xl shadow-stone-200/60` (not `shadow-2xl` — too heavy for the airy feel).
- No `border-stone-200` on cards in light mode — it's noisier than the reference. Prefer a single soft shadow.

## Typography

- Family: `Inter` (loaded via Google Fonts in `index.html`).
- Weights used: 400 (body), 500 (input values, medium emphasis), 600 (button labels, section labels), 700 (headings, brand wordmark). Bold-black 800/900 is **not** part of this style — that's the older MindDrop `font-black` look. Migrate to `font-semibold` / `font-bold` when matching this reference.
- H1: 32–40px, tight tracking (`tracking-tight`).
- Microcopy: 10–11px, `uppercase`, `tracking-wider` or `tracking-[0.3em]`, `font-bold` or `font-black`.
- Body: 14px, regular, `leading-relaxed`.
- Numbers in metric chips: `tabular-nums` when aligned.

## Button styles

- **Primary CTA**: pill (`rounded-full`) or large-radius (`rounded-2xl`), gradient `from-[#635BFF] to-[#4F46E5]`, white text, `text-xs font-black uppercase tracking-[0.2em]`, `shadow-xl shadow-[#635BFF]/30`, `active:scale-95`. Optional play-in-circle icon at the left (`<span class="w-5 h-5 rounded-full bg-white/20 flex items-center justify-center"><PlayIcon className="w-2.5 h-2.5"/></span>`).
- **Secondary / ghost**: `rounded-full` or `rounded-2xl`, `bg-stone-100 dark:bg-stone-800`, `text-stone-600`, no shadow, smaller tracking.
- **Pill chips** (for status, language toggle, model badges): `rounded-full`, `bg-stone-100 dark:bg-stone-800`, `text-[10px] font-black uppercase tracking-wider`, optional icon. For the segmented control (`FR / EN`), wrap the row in a `bg-stone-200/60 dark:bg-stone-800 rounded-full p-1` container and the active item in `bg-white text-[#635BFF] shadow-sm`.
- **Icon-in-circle**: a 40–48px circle with a soft border, used for upload icons and feature markers. `bg-white border border-stone-200/60 shadow-sm`.

## Top status / utility bar

A thin row above the main 2-column body, typically with:
- Left: small white pill with a `BoltIcon` and "Propulsé par [model]" microcopy (`<div class="inline-flex items-center gap-2 bg-white px-3 py-1.5 rounded-full border border-stone-200/60 shadow-sm">`).
- Right: language segmented control or settings button.

## Layout

- Two-column body: `grid-cols-[minmax(300px,30%)_1fr]` on `lg:`. Single column below `lg`. Gap `gap-6`.
- Page padding: `p-6 sm:p-10`.
- Max content width: `max-w-[1400px] mx-auto`.

## Upload zone (canonical)

```tsx
<div
  onClick={() => inputRef.current?.click()}
  onDragOver={e => { e.preventDefault(); setDragging(true) }}
  onDragLeave={() => setDragging(false)}
  onDrop={e => { e.preventDefault(); setDragging(false); handleFiles(e.dataTransfer.files) }}
  className={`cursor-pointer rounded-2xl border-2 border-dashed px-5 py-7 flex flex-col items-center justify-center gap-2 transition-all ${
    isDragging
      ? 'border-[#635BFF] bg-[#635BFF]/5'
      : 'border-stone-300 dark:border-stone-700 bg-stone-50/50 dark:bg-stone-800/30 hover:border-[#635BFF] hover:bg-[#635BFF]/5'
  }`}
>
  <div className="w-10 h-10 rounded-full bg-white border border-stone-200/60 flex items-center justify-center text-[#635BFF] shadow-sm">
    <CloudUploadIcon className="w-5 h-5" />
  </div>
  <p className="text-sm font-bold text-stone-700">Glisser-déposer ou cliquer</p>
  <p className="text-[10px] font-medium text-stone-400 uppercase tracking-wider">
    Vidéo ou M4A · Max 200 Mo
  </p>
  {fileName && <p className="text-[10px] font-bold text-[#635BFF] truncate max-w-full">{fileName}</p>}
</div>
<input ref={inputRef} type="file" accept="..." className="hidden" onChange={...} />
```

## Icons to add to your library

The Stripe-style visual language uses these icons that aren't always in default Lucide sets:
- `CloudUploadIcon` — cloud + up-arrow
- `GlobeIcon` — circle with two arcs
- `PlayIcon` — solid filled triangle (use `fill="currentColor"`, not stroke)
- `BoltIcon` — solid filled lightning bolt

Match the existing icon component style (24×24, `stroke="currentColor"`, `strokeWidth="1.5"`, `strokeLinecap/Linejoin="round"`) so the new ones drop in seamlessly.

## Dark mode

- Background flips to `dark:bg-stone-950`.
- Cards stay white-equivalent: `dark:bg-stone-900` (not black) to preserve the "floating card" hierarchy.
- Gradient and brand colors stay the same — they read well in both modes.
- Remove `border-stone-200/60` in dark mode (use `dark:border-white/5`) but keep the shadow — it becomes the only depth cue.

## When this vocabulary applies

Use it when:
- The user shares a screenshot in this aesthetic and says "match this".
- The user describes a "modern SaaS" or "Stripe-style" UI.
- Building a new landing/onboarding page for a B2B product and the user hasn't specified a brand.

Don't use it when:
- The user has their own brand colors — match those instead.
- The product is a developer tool / terminal UI / data-heavy dashboard where Stripe's pastel softness fights with dense tables.
- The product is consumer/fun/playful — this style reads as "work".

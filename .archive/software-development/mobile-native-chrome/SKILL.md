---
name: mobile-native-chrome
description: Make a desktop-first web app feel native on mobile — add bottom tab bars, FABs, slide-up sheets, and snap-scroll column views. Use when a user says "make it responsive", "add a mobile bottom menu", "add a + button to add a new item on mobile", "make it feel like a native app on phone", "open this as a bottom sheet on mobile", or "I need a bottom nav for mobile". Covers Tailwind responsive breakpoints, the snap-x pattern for switching between columns, scroll-position → active-tab sync via rAF, safe-area-inset padding, and the trap of rendering desktop controls and mobile controls as separate trees (don't reuse the same component if its size/positioning differs).
---

# Mobile-Native Chrome for Web Apps

The class of work: take a desktop-first web app and add the mobile-only chrome (bottom tab/nav, FAB, slide-up sheets) that makes it feel native on a phone, while keeping the desktop UX untouched.

## When this skill applies

Trigger when the user asks for any of:

- "make it responsive" / "mobile-first" / "add a mobile menu"
- "bottom nav / bottom tab bar" / "tab bar to switch between columns"
- "FAB / floating action button / big + button"
- "bottom sheet / slide-up modal / new task on mobile"
- "single column on mobile" + "snap between them"
- "make it feel like a native app on phone"

Skip if the request is purely CSS breakpoint tweaks with no new mobile chrome — that's just responsive CSS, not this class.

## The reusable architecture

There are 3 components. Render them as **separate trees gated on a `sm:hidden` / `lg:hidden` breakpoint**, NOT as responsive variants of the desktop components.

### 1. Bottom tab/nav bar (mobile only)

```tsx
{viewMode === 'board' && (
  <nav
    aria-label="Sections"
    className="sm:hidden fixed bottom-0 inset-x-0 z-40 pb-[max(env(safe-area-inset-bottom),0.5rem)] pt-2 px-3 bg-white/85 dark:bg-stone-900/85 backdrop-blur-xl border-t border-stone-200 dark:border-white/10"
  >
    <div className="flex items-stretch gap-2">
      {items.map(({ id, label, icon: Icon, count }) => {
        const active = activeId === id
        return (
          <button
            key={id}
            onClick={() => scrollTo(id)}
            className={`flex-1 flex flex-col items-center justify-center gap-0.5 py-2 rounded-2xl active:scale-95 transition-all ${
              active ? 'bg-indigo-600 text-white shadow-lg' : 'bg-stone-100 dark:bg-stone-800 text-stone-500'
            }`}
          >
            <Icon className="w-4 h-4" />
            <span className="text-[10px] font-black uppercase tracking-wider">{label}</span>
            <span className="text-[9px] font-bold opacity-80">{count}</span>
          </button>
        )
      })}
    </div>
  </nav>
)}
```

Key bits:
- `sm:hidden` — desktop never sees it.
- `fixed bottom-0 inset-x-0` + safe-area padding — sits above the iOS home indicator.
- `z-40` — under the FAB (`z-40` or higher) and under modals (`z-50`).
- Each tab triggers `scrollTo(id)` on the **horizontal scroller** that holds the columns. Don't re-render the column tree.
- Show a count or badge per tab if the data has a natural per-section count. It tells the user where the activity is.

### 2. Floating Action Button (FAB)

```tsx
<button
  onClick={() => { setSheetOpen(true); requestAnimationFrame(() => inputRef.current?.expand()) }}
  aria-label="New item"
  className="sm:hidden fixed bottom-24 right-4 z-40 w-14 h-14 rounded-2xl bg-indigo-600 text-white shadow-2xl shadow-indigo-600/40 flex items-center justify-center active:scale-95"
  style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}
>
  <PlusIcon className="w-7 h-7" />
</button>
```

Key bits:
- `bottom-24` (6rem) — sits above the 4-tall bottom nav (nav ≈ 4rem). Tune to match the nav height.
- `right-4` (1rem) — standard Material/iOS inset.
- `aria-label` is mandatory — the icon has no text.
- Triggers the slide-up sheet, not a fullscreen modal. Tapping the back/scrim on the sheet dismisses it.

### 3. Slide-up sheet (reuses the existing input component)

```tsx
{sheetOpen && (
  <div className="sm:hidden fixed inset-0 z-50 flex flex-col">
    <div className="flex-1 bg-black/50 backdrop-blur-sm" onClick={() => setSheetOpen(false)} />
    <div className="bg-white dark:bg-stone-900 rounded-t-3xl shadow-2xl p-4 pb-[max(env(safe-area-inset-bottom),1rem)] animate-in slide-in-from-bottom-5 duration-200">
      <header className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-black uppercase tracking-[0.3em] text-stone-500">New</h3>
        <button onClick={() => setSheetOpen(false)} aria-label="Close" className="p-2 rounded-xl bg-stone-100 dark:bg-stone-800">
          <XIcon className="w-4 h-4" />
        </button>
      </header>
      <ExistingInputComponent onSubmit={...} onCancel={() => setSheetOpen(false)} />
    </div>
  </div>
)}
```

Key bits:
- Backdrop div catches dismissal — make sure `onClick` is on the scrim, not the sheet itself.
- The sheet reuses the same input/form component the desktop uses, NOT a mobile-specific version. Pass an `onCancel` prop so the sheet can dismiss.
- `requestAnimationFrame` before calling `expand()` on the input ref gives the focusable element time to mount.

## The horizontal-snap pattern (when you have "columns" the user wants to swipe between)

```tsx
const scrollRef = useRef<HTMLDivElement>(null)
const [activeId, setActiveId] = useState(id1)

// Sync active tab with scroll position
useEffect(() => {
  const el = scrollRef.current
  if (!el) return
  let raf = 0
  const onScroll = () => {
    cancelAnimationFrame(raf)
    raf = requestAnimationFrame(() => {
      const w = el.clientWidth
      if (w <= 0) return
      const idx = Math.round(el.scrollLeft / w)
      const next = ids[idx]
      if (next && next !== activeId) setActiveId(next)
    })
  }
  el.addEventListener('scroll', onScroll, { passive: true })
  return () => { cancelAnimationFrame(raf); el.removeEventListener('scroll', onScroll) }
}, [activeId])

// Programmatic scroll on tab tap
const scrollTo = useCallback((id) => {
  const el = scrollRef.current
  if (!el) return
  const idx = ids.indexOf(id)
  el.scrollTo({ left: idx * el.clientWidth, behavior: 'smooth' })
  setActiveId(id)
}, [])
```

Key bits:
- `snap-x snap-mandatory` on the scroller + `min-w-[88vw] sm:min-w-[360px]` per child = one full screen per column on mobile, multi-column grid on desktop.
- **rAF-throttle the scroll handler.** Native scroll fires ~60×/sec; setting state on every event re-renders the nav and costs frames.
- `Math.round(scrollLeft / clientWidth)` gives the active index. Guard `clientWidth > 0` or you'll get `NaN` during the first paint.
- Mirror `setActiveId` inside `scrollTo` for instant feedback (the rAF listener catches up next frame either way).

## Pitfalls

- **Don't reuse the desktop toolbar.** Hide the desktop `Board / Timeline / Minutes` toggle row on mobile (`hidden lg:flex`) and add a separate tab bar. Trying to "just shrink it" produces a cramped 3-button row that fights for space with the FAB.
- **Bottom padding on the scroller.** Whatever the bottom nav height is, add it as `pb-` on the scroll container or the last card hides under the nav. `pb-28` (7rem) is a safe default.
- **Safe-area-inset-bottom.** iOS adds a home-indicator band below `bottom-0`. Wrap in `pb-[max(env(safe-area-inset-bottom),0.5rem)]` and add `style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}` on the FAB so it sits above the indicator.
- **Modal/sheet z-stacking.** Bottom nav = `z-40`, FAB = `z-40` (or higher), sheet = `z-50`, task-detail modal = `z-50`+ (above everything). Toast container should already be `z-[100]` so it floats over all of them.
- **Keyboard `autoFocus` is for desktop only.** A `autoFocus` input inside a mobile sheet will pop the iOS keyboard before the sheet finishes animating. Defer the focus to inside an effect or skip it on touch.
- **`NewTaskInput` style on mobile.** If the input component has a large rounded card style on desktop (`rounded-[2rem] shadow-2xl p-6`), it'll look weird at the bottom of a sheet. Either pass a `compact` prop or just let it be — the sheet's own padding absorbs the extra chrome.
- **Don't filter to one column on mobile.** Keep all columns mounted, just snap between them via the horizontal scroller. Filtering breaks the swipe-to-switch gesture and the scroll-position sync.
- **Initial scroll on mount.** If `activeId` defaults to a non-first column, call `scrollTo(activeId)` once after mount (in a `useEffect` with `[]` deps and a `setTimeout(..., 0)` or `requestAnimationFrame`) so the scroller lands on the right card. Otherwise the user lands on the first column even if state says otherwise.

## Verification

After wiring:
1. Resize the browser to <640px (or use Chrome DevTools mobile preset).
2. Confirm the bottom nav is visible, the FAB is visible, and the desktop toolbar is hidden.
3. Tap each tab — the column list should snap to that column and the tab's active style should follow.
4. Swipe horizontally — the active tab should update.
5. Tap the FAB — the sheet should slide up over the bottom nav (z-50 vs z-40), the input should be focused/expanded, and the backdrop tap should dismiss.
6. Submit a task — the sheet should auto-close (`setIsMobileAddingTask(false)` in the addTask handler).
7. Resize back to >640px — the mobile chrome should disappear, the desktop toolbar should reappear, and the layout should be unchanged from before the change.

## When NOT to use this skill

- Pure CSS breakpoint reflows with no new chrome (e.g., "stack the cards on mobile") — that's just Tailwind responsive utilities, not this.
- Apps that are already mobile-first (no desktop UX to preserve) — they need PWA install + native gestures, not bottom-nav chrome.
- Apps that need a true native shell — use Capacitor/Tauri to get real iOS/Android chrome.

---
name: mobile-ux-patterns
description: "Reusable patterns for mobile UI work — native Android (Kotlin + Jetpack Compose: adaptive launcher icons, swipeable full-screen viewer overlays, programmatic PIL pipelines for image verification when vision tools fail) AND responsive web app mobile chrome (bottom tab bars, FABs, slide-up sheets, snap-scroll column views, safe-area-inset padding). Load when editing any Android/Compose codebase, designing a launcher icon, building a swipeable full-screen image/media viewer, when vision_analyze returns empty and you need pixel-level raster verification, when making a desktop-first web app feel native on mobile, or when adding bottom-nav / FAB / slide-up sheet / snap-scroll to a web app. Replaces two formerly separate skills (android-ui-patterns + mobile-native-chrome) — both share the class 'what's the right mobile UX pattern for this situation' and the cross-platform user reads both before deciding which stack they're in."
version: 1.0.0
author: Hermes Agent (consolidated from android-ui-patterns + mobile-native-chrome)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [android, kotlin, compose, jetpack, launcher-icon, image-viewer, mobile, responsive-web, bottom-nav, fab, bottom-sheet, snap-scroll, vision-fallback]
    related_skills: [web-design-guidance, vercel-api-key-proxy]
---

# Mobile UX Patterns

Reusable patterns for mobile UI work across two stacks: **native Android (Kotlin + Compose)** and **responsive web app mobile chrome**. Pick the subsection that matches your stack.

When this skill applies (any of):
- Editing any Android/Compose codebase
- Designing a launcher icon (especially for round launchers)
- Building a swipeable full-screen image/media viewer
- Verifying a generated raster image programmatically because vision_analyze returns empty
- Making a desktop-first web app feel native on mobile
- Adding bottom-nav / FAB / slide-up sheet / snap-scroll to a web app

When NOT to use:
- Desktop-only or pure-CSS responsive reflow → just Tailwind
- Apps that need a true native shell → Capacitor / Tauri
- Cross-platform native (iOS + Android shared code) → KMP / RN / Flutter

---

## SUBSECTION A: Native Android (Kotlin + Jetpack Compose)

### 1. Adaptive launcher icons (round-edge-to-edge)

Android launchers apply their own mask — square, squircle, teardrop, or **circle**. A naïve square PNG with the logo centered looks lost inside the round mask. The fix is Android's **adaptive icon** system, which lets the foreground drawable intentionally bleed beyond the 72dp safe zone so it reaches the circumference on round launchers.

**File layout:**
```
app/src/main/res/
├── mipmap-anydpi-v26/
│   ├── ic_launcher.xml
│   └── ic_launcher_round.xml
├── drawable/
│   ├── ic_launcher_background.xml
│   └── ic_launcher_foreground.xml
└── mipmap-<density>/
    ├── ic_launcher.png
    └── ic_launcher_round.png
```

**Adaptive icon XML:**
```xml
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@drawable/ic_launcher_background" />
    <foreground android:drawable="@drawable/ic_launcher_foreground" />
</adaptive-icon>
```

**Foreground geometry rule:** design the mark so its bounding box is centered in the 108 viewport (bbox center ≈ 54,54). Strokes should be square (not rounded) so they sit flush against the round mask edge with no transparent reveal.

**Density sizes:** mdpi=48, hdpi=72, xhdpi=96, xxhdpi=144, xxxhdpi=192.

**Pitfall — F (or any asymmetric mark) doesn't center by stem:** if the mark is a letter F, centering the stem center ≠ centering the visual mass. Compute the bbox of the entire glyph, not just one stroke, then translate to put the bbox center on the canvas center.

**Pitfall — `round=` shadows builtin:** don't name a local variable `round` — it shadows the builtin.

**Pitfall — duplicate adaptive-icon resource names break the build.** Resource merger refuses both `<basename>.xml` and `<basename>.png` under the same name. Pick one.

**When the user supplies a reference icon image, USE IT DIRECTLY.** Don't try to recreate from vision analysis. Right pipeline: take the user's image, scale per density, replace near-white pixels with transparent. Save once, ship — don't iterate.

### 2. Compose full-screen swipeable viewer overlay

```kotlin
@Composable
fun ImageViewer(
    items: List<Item>,
    initialIndex: Int,
    onDismiss: () -> Unit,
) {
    BackHandler(enabled = items.isNotEmpty()) { onDismiss() }
    Box(modifier = Modifier.fillMaxSize().background(BrandBackground)) {
        if (items.isEmpty()) { onDismiss(); return }
        val pagerState = rememberPagerState(
            initialPage = initialIndex.coerceIn(0, items.lastIndex),
        ) { items.size }
        HorizontalPager(
            state = pagerState,
            modifier = Modifier.fillMaxSize(),
            key = { items[it].id },
        ) { page -> ItemPage(item = items[page]) }
        ViewerOverlay(
            currentIndex = pagerState.currentPage,
            totalCount = items.size,
            title = items.getOrNull(pagerState.currentPage)?.displayName.orEmpty(),
            onDismiss = onDismiss,
        )
    }
}
```

**Pitfall — pager recomposition glitches:** without `key = { ... }` on `HorizontalPager`, swapping items causes blank pages.

### 3. Verify a generated raster image without vision

When `vision_analyze` is unavailable and you need to confirm a PNG looks correct (centered, edge-to-edge, no clipping), use pixel-bbox analysis with PIL + numpy.

```python
from PIL import Image
import numpy as np
img = Image.open("ic_launcher_round.png").convert("RGBA")
arr = np.array(img)
H, W = arr.shape[:2]
alpha = arr[...,3]
r, g, b, a = arr[...,0], arr[...,1], arr[...,2], arr[...,3]
mask = (r < 140) & (g < 140) & (b < 140) & (a > 200)
ys, xs = np.where(mask)
print(f"bbox: x=[{xs.min()},{xs.max()}] y=[{ys.min()},{ys.max()}]")
print(f"center: ({(xs.min()+xs.max())/2:.1f}, {(ys.min()+ys.max())/2:.1f}) vs canvas ({W/2:.1f}, {H/2:.1f})")
```

For structural preview at low res (ASCII art):
```python
small = img.resize((48, 48), Image.LANCZOS)
arr2 = np.array(small.convert("L")).astype(int)
chars = " .:-=+*#%@"
for row in arr2:
    print("".join(chars[min(len(chars)-1, (255-int(v))*len(chars)//256)] for v in row))
```

### 4. Multi-file Android edits: branch + commit + PR workflow

For non-trivial Android changes touching 5+ files:
1. **Branch first:** `git checkout -b feat/<short-slug>` before any edits
2. **Make changes incrementally**, verifying imports stay clean after each file
3. **Commit with a body** describing the *why*, not just the *what*
4. **Push + open PR** with `gh pr create --base main --head <branch> --title "..." --body "..."`
5. **Note verification gaps explicitly** in the PR body when the host can't run `./gradlew`

### 5. PIL generator gotcha: `round=` parameter

`PIL.ImageDraw.Draw` accepts `radius=` on rounded shapes, but if you name a local variable `round`, it shadows the builtin and `int(round(...))` raises `TypeError`. Rename the local — `circular`, `is_round`, `apply_mask`.

### 6. Building the APK when the host has no JDK / Android SDK

```bash
which java javac gradle adb sdkmanager
ls /opt/android-sdk /usr/lib/jvm 2>&1
```

If everything is missing, **don't pretend you can build locally** — set up a remote builder via GitHub Actions. A minimal workflow at `.github/workflows/build.yml` with `actions/setup-java@v4` (distribution: temurin, version 17), `android-actions/setup-android@v3`, `./gradlew :app:assembleDebug --no-daemon`, and `actions/upload-artifact@v4`. Then download via `gh run download`.

### 7. APK verification after a CI build

```bash
unzip -l app-debug.apk | grep -E "ic_launcher|AndroidManifest"
unzip -o -q app-debug.apk -d apk-extract
strings apk-extract/classes*.dex | grep -E "ImageViewer|HorizontalPager" | sort -u
sha256sum app-debug.apk
```

Multidex APKs split classes across `classes.dex`, `classes2.dex`, etc. Always concatenate: `cat apk-extract/classes*.dex > all-dex.bin`.

### 8. Common CI pitfalls on Android projects

- **`gradle.properties` leaks local JDK paths** — strip the line before pushing
- **`gh run watch --exit-status` hangs after completion** — use polling
- **`gh run download` requires `cwd` inside the git repo**
- **`gh run download --name X` fails silently if the name is wrong** — discover via `gh api repos/OWNER/REPO/actions/runs/$RUN_ID/artifacts`
- **Multidex APKs** — always concatenate all dex blobs

### 9. Permission auto-prompt pattern (first-launch + empty-state fallback)

A common Android failure: app needs `MANAGE_EXTERNAL_STORAGE` to do anything useful, but only asks when user clicks a button. Result: empty dashboard, no files, user thinks app is broken.

**Two-part fix:**

**Part A — auto-prompt in `LaunchedEffect(Unit)`:**
```kotlin
LaunchedEffect(Unit) {
    refreshDashboard()
    val initialAccess = readAccessState()
    if (!initialAccess.hasAllFilesAccess && !initialAccess.hasLegacyReadPermission) {
        kotlinx.coroutines.delay(400) // let dashboard paint first
        requestSystemAccess(SystemAccessRequest.AllFilesAccess)
    }
}
```

The 400ms delay matters — without it, the system dialog stacks before the user sees anything.

**Part B — make the empty-state card actionable** with a "Grant storage access" button that calls `requestSystemAccess()`. A static text-only empty state is a dead end.

### 10. Programmatic PIL pipeline for analyzing reference images when vision_analyze is offline

```python
from PIL import Image
from collections import Counter
img = Image.open(USER_IMAGE).convert("RGB")
w, h = img.size
sample = []
for y in range(0, h, 5):
    for x in range(0, w, 5):
        sample.append(img.getpixel((x, y)))
ctr = Counter(sample)
for col, cnt in ctr.most_common(15):
    print(f"  #{col[0]:02X}{col[1]:02X}{col[2]:02X}  count={cnt}")
```

**Caveat — even with perfect metrics, do not recreate the icon procedurally.** Use the user's raster directly per section 1.

---

## SUBSECTION B: Responsive Web App Mobile Chrome

The class of work: take a desktop-first web app and add the mobile-only chrome (bottom tab/nav, FAB, slide-up sheets) that makes it feel native on a phone, while keeping the desktop UX untouched.

Trigger when the user asks for any of:
- "make it responsive" / "mobile-first" / "add a mobile menu"
- "bottom nav / bottom tab bar" / "tab bar to switch between columns"
- "FAB / floating action button / big + button"
- "bottom sheet / slide-up modal / new task on mobile"
- "single column on mobile" + "snap between them"

Skip if the request is purely CSS breakpoint tweaks with no new mobile chrome.

### The reusable architecture

Three components. Render them as **separate trees gated on a `sm:hidden` / `lg:hidden` breakpoint**, NOT as responsive variants of the desktop components.

**1. Bottom tab/nav bar (mobile only):**
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
- `sm:hidden` — desktop never sees it
- `fixed bottom-0 inset-x-0` + safe-area padding — sits above the iOS home indicator
- `z-40` — under the FAB (`z-40` or higher) and under modals (`z-50`)
- Each tab triggers `scrollTo(id)` on the **horizontal scroller** that holds the columns

**2. Floating Action Button (FAB):**
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

- `bottom-24` (6rem) — sits above the 4-tall bottom nav
- `right-4` (1rem) — standard Material/iOS inset
- `aria-label` is mandatory

**3. Slide-up sheet (reuses the existing input component):**
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

### The horizontal-snap pattern (for "columns" the user wants to swipe between)

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
```

Key bits:
- `snap-x snap-mandatory` on the scroller + `min-w-[88vw] sm:min-w-[360px]` per child
- **rAF-throttle the scroll handler** — 60Hz native scroll re-renders the nav every frame
- `Math.round(scrollLeft / clientWidth)` for active index
- Mirror `setActiveId` inside `scrollTo` for instant feedback

### Pitfalls (web-app mobile chrome)

- **Don't reuse the desktop toolbar.** Hide desktop controls on mobile (`hidden lg:flex`) and add a separate tab bar
- **Bottom padding on the scroller.** `pb-28` (7rem) is a safe default
- **Safe-area-inset-bottom.** iOS adds a home-indicator band. Wrap in `pb-[max(env(safe-area-inset-bottom),0.5rem)]`
- **Modal/sheet z-stacking.** Bottom nav = `z-40`, FAB = `z-40`+, sheet = `z-50`, modal = `z-50`+
- **Keyboard `autoFocus` is for desktop only** — defer to an effect or skip on touch
- **Don't filter to one column on mobile** — keep all mounted, snap between
- **Initial scroll on mount** — call `scrollTo(activeId)` once after mount if `activeId` ≠ first

### Verification (web-app mobile chrome)

1. Resize to <640px (or DevTools mobile preset)
2. Confirm bottom nav + FAB visible, desktop toolbar hidden
3. Tap each tab — column snaps, active style follows
4. Swipe horizontally — active tab updates
5. Tap FAB — sheet slides up, input focused, backdrop tap dismisses
6. Submit task — sheet auto-closes
7. Resize back to >640px — mobile chrome disappears, desktop unchanged

### When NOT to use (web-app mobile chrome)

- Pure CSS breakpoint reflows with no new chrome — just Tailwind
- Apps already mobile-first — they need PWA install + native gestures, not bottom-nav chrome
- Apps that need a true native shell — Capacitor/Tauri

---

## Companion references (in `references/`)

From android-ui-patterns:
- `android-ui--adaptive-icon-density-sizes.md` — exact pixel sizes for every Android density (mdpi through xxxhdpi) and the standard launcher icon padding rules
- `android-ui--gradle-ci-fixes.md` — known `gradle.properties` lines that break on Linux CI runners, with the minimal commit that fixes each
- `android-ui--launcher-icon-from-reference-image.md` — PIL pipeline for scaling a user-supplied icon image into all 5 density PNGs + adaptive drawables, with the duplicate-resource and edge-to-edge-bg pitfalls

## Related skills

- `web-design-guidance` — for design-system-level UI review
- `vercel-api-key-proxy` — when shipping a mobile companion app needs the same third-party API key without exposing it to the client
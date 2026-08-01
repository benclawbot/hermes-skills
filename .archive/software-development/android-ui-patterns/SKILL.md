---
name: android-ui-patterns
description: Class-level patterns for Android UI work — Jetpack Compose + adaptive launcher icons + visual verification when vision tools fail. Load when editing any Android/Compose codebase, designing a launcher icon (especially for round launchers), building a swipeable full-screen image/media viewer, or whenever you need to verify a generated raster image programmatically because vision_analyze is unavailable or returning empty.
---

# Android UI patterns

Reusable patterns for Android (Kotlin + Jetpack Compose) work. Each subsection is a standalone recipe with the exact files / XML / Kotlin shape and the pitfalls discovered in real sessions. Most patterns are bite-sized and copy-pasteable with light modification.

## 1. Adaptive launcher icons (round-edge-to-edge)

Android launchers apply their own mask — square, squircle, teardrop, or **circle**. A naïve square PNG with the logo centered looks lost inside the round mask (visible cream/transparent border around the mark). The fix is Android's **adaptive icon** system, which lets the foreground drawable intentionally bleed beyond the 72dp safe zone so it reaches the circumference on round launchers.

**File layout (replace or add):**

```
app/src/main/res/
├── mipmap-anydpi-v26/
│   ├── ic_launcher.xml        ← used by Android 8.0+
│   └── ic_launcher_round.xml  ← may share the same body
├── drawable/
│   ├── ic_launcher_background.xml   ← solid color or simple tile (108x108 viewport)
│   └── ic_launcher_foreground.xml   ← mark scaled to ~88x88 inside 108 viewport
└── mipmap-<density>/
    ├── ic_launcher.png        ← legacy (v25 and below), per-density
    └── ic_launcher_round.png  ← circular PNG for legacy round launchers
```

`AndroidManifest.xml` keeps the existing references — `@mipmap/ic_launcher` and `@mipmap/ic_launcher_round` — the system picks the right resource per Android version.

**Adaptive icon XML:**

```xml
<!-- mipmap-anydpi-v26/ic_launcher.xml -->
<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@drawable/ic_launcher_background" />
    <foreground android:drawable="@drawable/ic_launcher_foreground" />
</adaptive-icon>
```

`ic_launcher_background.xml` is a vector filling the full 108×108dp viewport (solid color, gradient, or simple tile). `ic_launcher_foreground.xml` is a vector where the mark fills roughly 88×88dp of the 108 viewport — extending **outside** the 72dp safe zone is intentional, that's how you reach the round mask edge.

**Foreground geometry rule:** design the mark so its **bounding box** is centered in the 108 viewport (bbox center ≈ 54,54). Strokes should be square (not rounded) so they sit flush against the round mask edge with no transparent reveal.

**Legacy PNG fallback** (Android 7 and below) needs two separate PNGs per density:
- `ic_launcher.png` — square content; launcher rounds corners automatically. Leave a small ~14% margin so the launcher-applied squircle doesn't pinch the corners.
- `ic_launcher_round.png` — circular PNG (apply an alpha mask so transparent corners don't show on non-round legacy launchers). Push the mark to ~92% of the diameter so it reaches the circle's edge.

**Density sizes:** mdpi=48, hdpi=72, xhdpi=96, xxhdpi=144, xxxhdpi=192.

**Pitfall — F (or any asymmetric mark) doesn't center by stem:** if the mark is a letter F, centering the stem center ≠ centering the visual mass. Compute the bbox of the entire glyph, not just one stroke, then translate to put the bbox center on the canvas center. ASCII-art preview at 48×48 reveals off-center glyphs that pixel-bbox math can miss when the mark has thin tapered strokes.

**Pitfall — generator `round=` shadows builtin:** if you generate the PNGs in Python with PIL, don't name a local variable `round` — it shadows the builtin and you'll get `TypeError: 'bool' object is not callable`. Use `circular` or `is_round` instead.

**Pitfall — duplicate adaptive-icon resource names break the build.** Android allows `<basename>.xml` and `<basename>.png` to coexist in `drawable/`, but the resource merger refuses to ship both under the same name. If you commit `drawable/ic_launcher_foreground.xml` (vector adaptive foreground) AND `drawable/ic_launcher_foreground.png` (raster fallback), `./gradlew :app:mergeDebugResources` fails with `Error: Duplicate resources` and the build dies before dexing. Pick **one** — vector for adaptive, PNG for legacy fallback, not both with the same name. If you need a raster foreground fallback, name it differently (`ic_launcher_foreground_legacy.png`).

**Edge-to-edge circle appearance:** if the user wants the icon to look like a colored circle filling the launcher cell (no square frame visible behind it), the recipe is:
- `ic_launcher_background.xml` = solid color vector matching the icon's main fill (so any launcher BG that bleeds through transparent corners reads as the same color — invisible).
- `ic_launcher_foreground.xml` = the icon's mark/circle on a fully transparent background (the colored background layer does the fill).
- For PNG fallbacks: scale the reference, then walk pixels and replace white (>245 all channels) with `(0,0,0,0)` transparent. The result: circle reaches the edge, corners are transparent, background drawable fills the visible square as cream — no visible seam.

**When the user supplies a reference icon image, USE IT DIRECTLY.** Don't try to recreate it from vision analysis or text description — the user will reject it after a few iterations of size/style mismatch. The right pipeline:
1. Take the user's image (often 1000+ px, with transparent/white corners outside the mark).
2. For each density PNG: `resize((size, size), LANCZOS)`, then replace near-white pixels with `(0,0,0,0)` for transparent corners.
3. For adaptive foreground: same resize + transparent-outside-circle, saved as PNG (432×432) OR redrawn as XML vector.
4. Save once, ship — don't iterate on size unless the user complains.

The failure mode this avoids: vision analysis is often offline, returns empty, or describes the image in unhelpful ways ("a gray folder on a light background"). Reconstructing from description usually gets size/style wrong. The user's actual raster is authoritative — load it from `/home/thomas/.hermes/image_cache/img_*.jpg` and scale.

## 2. Compose full-screen swipeable viewer overlay

Pattern for opening a full-screen media viewer (images, pages) on top of the existing screen with swipe navigation, back-gesture dismissal, and a clear visual indicator of position.

```kotlin
@Composable
fun ImageViewer(
    items: List<Item>,          // anything with stable id + display name + Uri/String source
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
            key = { items[it].id },         // stable key avoids recomposition glitches
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

Overlay pattern: a separate `Box` layered on top of the pager (`align(Alignment.TopCenter)` for filename + page indicator + close button, `align(Alignment.BottomCenter)` for dot indicators). The pager doesn't know about the overlay — the overlay reads `pagerState.currentPage` and re-renders on each settle.

**Wiring in the parent screen:** host an `openViewerIndex: Int?` state. The grid/list calls `onOpenViewer(index)` when a tile is tapped; the parent renders the viewer conditionally above everything else when the state is non-null. Don't try to share the viewer's lifecycle with the gallery — separate state, separate composable.

**Selection mode coexistence:** long-press still enters multi-select on the grid; the viewer's tap is short-press only. If selection mode is active when the user taps a tile, route to `toggleFileSelection(file)` instead of opening the viewer.

**Pitfall — pager recomposition glitches:** without `key = { ... }` on `HorizontalPager`, swapping the items list can cause blank pages. Always pass a stable id.

## 3. Verify a generated raster image without vision

When `vision_analyze` is unavailable (model has no vision, or returns empty/error) and you need to confirm a generated PNG looks correct (centered, edge-to-edge, no clipping), use pixel-bbox analysis with PIL + numpy.

```python
from PIL import Image
import numpy as np

img = Image.open("ic_launcher_round.png").convert("RGBA")
arr = np.array(img)
H, W = arr.shape[:2]
alpha = arr[...,3]
r, g, b, a = arr[...,0], arr[...,1], arr[...,2], arr[...,3]

# Mark pixels: e.g. dark brown mark on cream background
mask = (r < 140) & (g < 140) & (b < 140) & (a > 200)
ys, xs = np.where(mask)
print(f"bbox: x=[{xs.min()},{xs.max()}] y=[{ys.min()},{ys.max()}]  size={xs.max()-xs.min()+1}x{ys.max()-ys.min()+1}")
print(f"margins (px): top={ys.min()} bot={H-ys.max()-1} left={xs.min()} right={W-xs.max()-1}")
print(f"center: ({(xs.min()+xs.max())/2:.1f}, {(ys.min()+ys.max())/2:.1f})  vs canvas ({W/2:.1f}, {H/2:.1f})")
```

This catches the questions you'd otherwise ask a vision model: *Is it centered? Does it reach the edge? How much margin? Is the mask wrong?*

For **structural preview** at low res (ASCII art):

```python
small = img.resize((48, 48), Image.LANCZOS)
arr2 = np.array(small.convert("L")).astype(int)
chars = " .:-=+*#%@"
for row in arr2:
    print("".join(chars[min(len(chars)-1, (255-int(v))*len(chars)//256)] for v in row))
```

The ASCII view reveals off-center marks, broken masks, asymmetric layouts that bbox numbers alone can hide (especially for thin tapered strokes).

## 4. Multi-file Android edits: branch + commit + PR workflow

For non-trivial Android changes touching 5+ files:

1. **Branch first:** `git checkout -b feat/<short-slug>` before any edits.
2. **Make changes incrementally,** verifying imports stay clean after each file (unused imports break the build but lint won't always catch them in Kotlin — read back the file after pruning imports).
3. **Commit with a body** describing the *why* (each item the user asked for), not just the *what*. PR reviewers will read the body.
4. **Push + open PR** with `gh pr create --base main --head <branch> --title "..." --body "..."`. The body should map each commit/change back to the user's original request.
5. **Note verification gaps explicitly** in the PR body when the host can't run `./gradlew` (no JDK / Android SDK in this sandbox) — list the test files that weren't run so the reviewer knows to run them locally before merge.

## 5. PIL generator gotcha: `round=` parameter

`PIL.ImageDraw.Draw` accepts a `radius=` (or `width=`) argument on rounded shapes, but if you name your own loop / helper variable `round` (e.g. `make_icon(size, round: bool)`), you shadow the builtin and `int(round(units * s / 108))` raises `TypeError: 'bool' object is not callable`. Rename the local — `circular`, `is_round`, `apply_mask` — anything except `round`.

## 6. Building the APK when the host has no JDK / Android SDK

Sandbox machines often lack `java`, `javac`, `gradle`, and `ANDROID_HOME`. Verifying absence is cheap:

```bash
which java javac gradle adb sdkmanager
ls /opt/android-sdk /usr/lib/jvm 2>&1
```

If everything is missing, **don't pretend you can build locally** — set up a remote builder via GitHub Actions and ship the APK as a workflow artifact. A minimal workflow:

```yaml
# .github/workflows/build.yml
name: Build debug APK
on:
  push: { branches: [main] }
  workflow_dispatch:
jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 25
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with: { distribution: temurin, java-version: '17' }
      - uses: android-actions/setup-android@v3
      - run: chmod +x gradlew
      - run: ./gradlew :app:assembleDebug --no-daemon
      - uses: actions/upload-artifact@v4
        with:
          name: app-debug-apk
          path: app/build/outputs/apk/debug/app-debug.apk
          if-no-files-found: error
          retention-days: 14
```

Then deliver to the user via `MEDIA:/local/path/app-debug.apk` after downloading the artifact:

```bash
gh run download <RUN_ID> --name app-debug-apk --dir /tmp/apk
```

## 7. APK verification after a CI build

Before declaring an APK done, verify it actually contains the new code (CI can succeed but produce a stale cache, or an upstream Android build step can silently no-op).

```bash
# Confirm expected resources made it in (icons, drawables, manifests).
unzip -l app-debug.apk | grep -E "ic_launcher|ic_launcher_foreground|AndroidManifest"

# Confirm new classes/functions are present in the dex.
unzip -o -q app-debug.apk -d apk-extract
strings apk-extract/classes*.dex | grep -E "ImageViewer|toggleSelectAllVisible|HorizontalPager" | sort -u

# Capture a checksum for the user message.
sha256sum app-debug.apk
```

DEX class names are mangled (`HomeDashboardContentTestKt$selectAllVisibleFileIds$1`), so grep for the original Kotlin identifiers — they survive as string constants in the constant pool.

## 8. Common CI pitfalls on Android projects

**`gradle.properties` leaks local JDK paths.** Developers pin `org.gradle.java.home=C:/Program Files/...` for local builds; that path doesn't exist on Linux CI runners and Gradle fails immediately with `Value '...' given for org.gradle.java.home Gradle property is invalid`. **Strip the line before pushing**, or never commit it in the first place. Gradle picks `JAVA_HOME` automatically.

**`gh run watch --exit-status` hangs after completion** if the parent process gets interrupted (SIGINT, gateway timeout, etc.) — even though the run finished, the watcher doesn't return until the tool timeout. Use polling instead:

```bash
for i in $(seq 1 30); do
  s=$(gh run view "$RUN_ID" --json status -q .status)
  echo "[$i] $s"
  [ "$s" = "completed" ] && break
  sleep 15
done
gh run view "$RUN_ID" --json conclusion -q .conclusion
```

**`gh run download` requires `cwd` inside the git repo.** Running it from `/tmp/...` errors with `failed to run git: fatal: not a git repository`. Always `cd` into the cloned repo first, or pass `--repo owner/name`.

**`gh run download --name X` fails silently if the name is wrong.** The artifact name comes from the workflow YAML's `actions/upload-artifact` `name:` field, NOT from the APK filename. Don't guess — discover it first:

```bash
gh api repos/OWNER/REPO/actions/runs/$RUN_ID/artifacts \
  --jq '.artifacts[] | {name, size_in_bytes}'
```

Then pass the exact name to `gh run download`. The error `no artifact matches any of the names or patterns provided` is the symptom of a name mismatch, not a missing artifact.

**Multidex APKs split classes across many `.dex` files** — modern AGP apps with `minSdk 26` + Compose routinely produce 5-8 DEX shards (`classes.dex`, `classes2.dex`, ..., `classesN.dex`). Grepping only `classes.dex` for new symbols misses them. Always concatenate all dex blobs before grepping:

```bash
unzip -o -q app-debug.apk -d apk-extract
cat apk-extract/classes*.dex > all-dex.bin
strings all-dex.bin | grep -E "ImageViewer|toggleSelectAllVisible"
```

Kotlin class names get mangled in the bytecode but survive as **string constants** in the constant pool — grepping for the original identifier (`ImageViewer`, `toggleSelectAllVisible`) works because the source-level name appears in `Lcom/your/package/ImageViewer;` descriptors.

## 9. Permission auto-prompt pattern (first-launch + empty-state fallback)

A common Android failure: the app needs MANAGE_EXTERNAL_STORAGE (or any other special access) to do anything useful, but only asks for it when the user clicks a button. Result on first launch — empty dashboard, no files visible, no obvious next step, user thinks the app is broken.

**Two-part fix:**

**Part A — auto-prompt in `LaunchedEffect(Unit)` after the dashboard renders:**

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

The 400ms delay is important — without it the system dialog stacks before the user sees anything, looks like the app crashed into a permission popup. With it, they see the dashboard for a split second, then the prompt arrives.

**Part B — make the empty-state card actually actionable:**

```kotlin
@Composable
private fun EmptyFilesCard(
    needsStorageAccess: Boolean,
    onRequestAccess: () -> Unit,
) {
    NeumorphicSurface(modifier = Modifier.fillMaxWidth(), cornerRadius = 12.dp) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = if (needsStorageAccess) "Storage access required" else "No files found",
                style = MaterialTheme.typography.bodyMedium.copy(fontWeight = FontWeight.SemiBold),
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = if (needsStorageAccess) {
                    "FilesFlow needs permission to read your files before it can show anything. Tap below to open system settings, then enable Allow access to manage all files."
                } else {
                    "Try another category or search."
                },
                style = MaterialTheme.typography.labelSmall,
            )
            if (needsStorageAccess) {
                Spacer(modifier = Modifier.height(16.dp))
                Button(
                    onClick = onRequestAccess,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = FilesFlowPrimary,
                        contentColor = Color.White,
                    ),
                    shape = RoundedCornerShape(12.dp),
                ) {
                    Icon(Icons.Rounded.FolderOpen, contentDescription = null, modifier = Modifier.size(18.dp))
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Grant storage access", fontWeight = FontWeight.SemiBold)
                }
            }
        }
    }
}
```

**Threading the access state through:** the composable that hosts the dashboard needs to know the current access state. Lift it to the top-level screen and pass `needsStorageAccess: Boolean` + `onRequestStorageAccess: () -> Unit` down through the empty-state composable. The parent's `DisposableEffect` on `Lifecycle.Event.ON_RESUME` already refreshes state when the user returns from system settings — combine that with `requestSystemAccess()` triggering re-launch, and the loop closes: dialog → settings → return → list populates.

**Why this matters:** a static "Grant storage access or try another category" text-only empty state is a dead end. Users tap nothing, close the app, leave a 1-star review. A working button + auto-prompt on first launch means the user only ever sees the permission flow once, then the app just works.

## 10. Programmatic PIL pipeline for analyzing reference images when vision_analyze is offline

`vision_analyze` returns empty or unhelpful descriptions on some sessions (model without vision, transient failure). For analyzing a user-supplied reference image (color palette, bbox of the mark, circle radius, proportions), use PIL directly — no LLM needed.

```python
from PIL import Image
from collections import Counter

img = Image.open(USER_IMAGE).convert("RGB")
w, h = img.size

# 1. Color palette — top 15 colors in 5px grid samples
sample = []
for y in range(0, h, 5):
    for x in range(0, w, 5):
        sample.append(img.getpixel((x, y)))
ctr = Counter(sample)
for col, cnt in ctr.most_common(15):
    print(f"  #{col[0]:02X}{col[1]:02X}{col[2]:02X}  count={cnt}")

# 2. Find mark bbox (replace `is_mark` predicate with your color rule)
def is_gray_mark(p):
    r, g, b = p
    return max(p) - min(p) < 30 and sum(p) < 350

mark = [(x, y) for y in range(h) for x in range(w) if is_gray_mark(img.getpixel((x, y)))]
xs, ys = [p[0] for p in mark], [p[1] for p in mark]
print(f"mark bbox: x={min(xs)}-{max(xs)} y={min(ys)}-{max(ys)}")
print(f"mark width % of canvas: {(max(xs)-min(xs))/w*100:.1f}%")

# 3. Find background extent (e.g. where the cream circle ends on a white-corner image)
def is_beige(p):
    r, g, b = p
    # tighter: exclude pure white by requiring (r - b) >= 15
    return r >= 240 and g >= 220 and b >= 200 and r - b >= 15 and r > 250
# Walk rows/cols finding leftmost/rightmost beige — gives circle radius and padding
```

Combine with **section 3** (ASCII structural preview) to see what the image actually looks like. Two patterns together replace `vision_analyze` for almost all "what is this image" diagnostic questions on raster inputs.

**Caveat — even with perfect metrics, do not recreate the icon procedurally.** Use the user's raster directly per section 1. The PIL analysis is for verification (after the build) and for understanding WHY the user wants a specific layout, not for regenerating it. Procedural recreation drifts from the source on stroke widths, antialiasing, tab proportions, and exact shade — the user notices.

## References

- `references/adaptive-icon-density-sizes.md` — exact pixel sizes for every Android density (mdpi through xxxhdpi) and the standard launcher icon padding rules.
- `references/gradle-ci-fixes.md` — known `gradle.properties` lines that break on Linux CI runners, with the minimal commit that fixes each.
- `references/launcher-icon-from-reference-image.md` — PIL pipeline for scaling a user-supplied icon image into all 5 density PNGs + adaptive drawables, with the duplicate-resource and edge-to-edge-bg pitfalls.
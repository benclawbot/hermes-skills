---
name: hyperframes-pitfalls
description: HyperFrames gotchas learned the hard way on this machine. Load before authoring any multi-scene HyperFrames composition or running a render. Covers the linter's "root composition" trap, the data-duration overlap rule, the working scene-stacking pattern, render-time gotchas (screenshot-mode slowdown, chrome-headless-shell install), and the WCAG / font warnings to ignore vs fix. Source — live rendering session that produced crypto-crash.mp4.
---

# HyperFrames Pitfalls (this machine)

Lessons from the first real render at `~/Projects/hyperframes/crypto-crash.mp4` (15s, 5 beats). Apply these BEFORE writing the HTML or the linter / renderer will fight you.

## Render environment

- **CLI installed globally:** `hyperframes@0.6.69` at `~/.local/lib/nodejs/node-v22.22.2-linux-x64/bin/hyperframes`
- **System Chromium falls back to screenshot mode** because `HeadlessExperimental.beginFrame` is unavailable in `/usr/bin/chromium-browser`. A 15s composition takes ~8 minutes. To get the optimized path (~2 min):
  ```bash
  npx @puppeteer/browsers install chrome-headless-shell
  ```
- **`hyperframes init` interactive prompt** — always pass `--yes` for non-interactive use:
  ```bash
  npx hyperframes init my-video --yes
  ```
- **System font stack warning is cosmetic** — `-apple-system, "Helvetica Neue"` triggers `font_family_without_font_face` warnings. The render still works and falls back to a generic. Ignore unless typography is critical.

## Linter traps (read this first)

### Decorative divs OUTSIDE the composition root = lint error

The linter walks the DOM and treats ANY div as a potential root composition. A bare `<div class="bg-glow"></div>` next to `<div data-composition-id="main">` produces:

```
✗ root_missing_composition_id [bgGlow]
✗ root_missing_dimensions [bgGlow]
```

**Fix:** move decoratives INSIDE the `data-composition-id` div, and mark them with `data-layout-ignore`:

```html
<div data-composition-id="main" data-width="1920" data-height="1080">
  <div class="bg-glow" data-layout-ignore></div>
  <!-- ...clips... -->
</div>
```

The composition root also needs `position: relative` if you have `position: absolute` decoratives inside it.

### `data-duration` must NOT extend past the next beat's `data-start` on the same track

If beat 1 clips run `data-start="0" data-duration="3"` and beat 2 starts at `2.5s` on the same `data-track-index`, you get:

```
✗ overlapping_clips_same_track
```

**Fix:** set each beat clip duration to end exactly at the next beat start. Beat 1 clips at 0-2.5s get `data-duration="2.5"`, beat 2 at 2.5-5s gets `data-duration="2.5"`, etc. Touching is fine, overlapping is not.

### Same-track tracks get dense warnings at 5+ elements

`timeline_track_too_dense: Track 1 has 5 timed elements` — move coherent scene groups into sub-compositions with `data-composition-src` and mount from the parent. Cosmetic for short videos, mandatory for production scale.

## Scene-stacking pattern (the one that actually works)

**DO NOT** try to toggle scene-level `opacity`, `visibility`, or `class` from the GSAP timeline. All three approaches (`tl.set opacity`, `tl.set visibility`, `className: "+=active"`) caused silent regressions where 1-2 beats rendered empty while the BG glow and ticker still showed. The framework seek-and-snapshot renderer does not always re-evaluate the wrapper CSS state correctly.

**Use z-index stacking with inner `gsap.from` tweens:**

```css
.scene-content {
  position: absolute;
  top: 0; left: 0;
  width: 100%;
  height: 100%;
  padding: 120px 160px;
  box-sizing: border-box;
}
#scene-1 { z-index: 11; }
#scene-2 { z-index: 12; }
#scene-3 { z-index: 13; }
#scene-4 { z-index: 14; }
#scene-5 { z-index: 15; }
```

```html
<div id="scene-1" class="scene-content" data-layout-ignore>
  <div id="b1-title" class="clip" data-start="0" data-duration="2.5" data-track-index="1">
    <div class="headline">Crypto.</div>
  </div>
</div>
<!-- repeat for scene-2, scene-3, ... -->
```

```js
// NO scene-level tl.set / tl.to. Just inner gsap.from for entrances.
// Each later scene z-index covers the prior one automatically.
tl.from("#b1-title", { y: 60, opacity: 0, duration: 0.7, ease: "expo.out" }, 0.4);
tl.from("#b2-title", { y: 50, opacity: 0, duration: 0.6, ease: "power2.out" }, 2.8);
```

Why this works: `gsap.from` tweens compute the correct opacity and y at any seek time (renderer seeks the timeline). Earlier scene inner elements stay at their `from` initial state (opacity 0) until their entrance tween fires. Later scene higher z-index covers earlier scenes that have not been tweened in yet. No wrapper-level state to go wrong.

## WCAG contrast gotchas

- **Ambient ticker / decorative text** — `validate` will flag anything below 4.5:1. Muted gray for ambient text needs to be at least `#8a8fa3` at the rendered size to pass. If you do not care about strict compliance, run `validate` with `--no-contrast` and skip.
- **`validate` runs headless Chrome** — uses system Chrome as fallback, same screenshot-mode slowness.

## Layout quirks

- **`.scene-content` with `display: flex; flex-direction: column; justify-content: center`** fills the scene. Use `padding: 120px 160px` (not absolute positioning) to push content inward.
- **Reserve `position: absolute` for decoratives** (glows, ticker, charts). Content containers overflow when content is taller than the remaining space.
- **Headline font size:** 180px fits 2 lines in 1080px canvas with 120px padding. 220px pushes 2-line content off-frame.
- **Use `font-variant-numeric: tabular-nums`** on price/stat numbers — keeps digits from jittering during renders.

## Render time expectations (screenshot mode)

| Duration | Approx render time |
| -------- | ------------------ |
| 5s       | ~3 min             |
| 10s      | ~5 min             |
| 15s      | ~8 min             |
| 30s      | ~16 min            |

For batch renders or 30s+ pieces, install `chrome-headless-shell` first. With the optimized path it is ~2x faster.

## Project layout on disk

- **Test project:** `~/Projects/hyperframes/demo/`
- **Outputs:** `~/Projects/hyperframes/*.mp4` (rendered videos)
- **Frame extraction for QA:** `ffmpeg -y -i in.mp4 -ss <time> -frames:v 1 -vf "scale=960:-1" out.png` — pull frames at the midpoint of each beat
- **Skills:** `~/.hermes/skills/hyperframes*/` (15 skills, symlinked from `~/.agents/skills/`)

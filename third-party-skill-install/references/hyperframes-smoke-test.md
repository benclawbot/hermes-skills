# HyperFrames — End-to-End Smoke Test

The concrete install + render flow that proves a HyperFrames install actually works on this machine. Run after `npx skills add heygen-com/hyperframes -y -g`.

## Prerequisites (verify before installing)

```bash
node --version              # need >= 22
ffmpeg -version | head -1   # any modern FFmpeg works
which ffmpeg                # must be on PATH
```

HyperFrames renders through headless Chrome. Two paths:
- **Optimized:** `npx @puppeteer/browsers install chrome-headless-shell` (~150MB, supports `HeadlessExperimental.beginFrame`)
- **Fallback:** system Chromium — works but ~2x slower (screenshot mode)

The skill bundle itself doesn't install either; you choose.

## Steps

```bash
# 1. Install the skill bundle (non-interactive)
npx skills add heygen-com/hyperframes -y -g
ls ~/.agents/skills/ | grep hyper      # expect 10+ entries
ls ~/.hermes/skills/ | grep hyper      # confirm Hermes symlinks (or your agent of choice)

# 2. Install the bundled CLI (not done by `npx skills add`)
npm install -g hyperframes
hyperframes --version                 # expect 0.6.x

# 3. Scaffold a test project
mkdir -p ~/Projects/hyperframes && cd ~/Projects/hyperframes
hyperframes init demo --yes
cd demo

# 4. Write a minimal composition to demo/index.html
#    (Use the pattern from the `hyperframes` skill: a top-level div with
#     data-composition-id, paused GSAP timeline registered on window.__timelines,
#     .clip class on timed elements, data-start/data-duration/data-track-index.)
#    A 5-second title-card composition is enough to verify the pipeline.

# 5. Lint, validate, render
npx hyperframes lint       # expect 0 errors (1 warning about system fonts is fine)
npx hyperframes validate   # expect "No console errors · N text elements pass WCAG AA"
npx hyperframes render --output ../test-render.mp4

# 6. Verify the MP4 is real (NEVER skip this)
ls -la ../test-render.mp4
ffprobe -v error -show_entries format=duration,size,bit_rate \
        -show_entries stream=codec_name,width,height,r_frame_rate \
        -of default=nw=1 ../test-render.mp4
# Expect: h264, 1920x1080 (or your data-width/height), 30fps,
#         duration matches data-duration, size > 100KB

# 7. Optional: extract a frame for visual verification
ffmpeg -y -i ../test-render.mp4 -ss 2.0 -frames:v 1 ../preview.png
```

## Verified-good output signature

A successful 5-second 1920×1080 composition on this machine (Linux 7.0.0, Node 22.22.2, FFmpeg 8.0.1, system Chromium fallback):

- **File:** `test-render.mp4`, ~250KB
- **Codec:** H.264 (`avc1`)
- **Resolution:** 1920×1080
- **Frame rate:** 30fps
- **Duration:** 5.000s (matches `data-duration` exactly — proves the deterministic seek worked)
- **Wall time:** ~50s in screenshot mode, ~25s expected with `chrome-headless-shell`

## Warnings that are safe to ignore (smoke-test only)

- `HeadlessExperimental.beginFrame unavailable in this Chromium build; falling back to screenshot mode.` — fix with `chrome-headless-shell` install, but not blocking
- `browserGpuMode auto → software (WebGL unavailable)` — fine unless your composition needs WebGL
- `[non-blocking] Failed to load resource: 404` for the dev-server favicon — cosmetic
- `font_family_without_font_face` lint warning on `-apple-system` / `Helvetica Neue` — renders use generic fallback, but works

## Warnings that are NOT safe to ignore

- `0 error(s), 0 warning(s)` is good. Any error in `lint` or `validate` blocks render.
- `No console errors` in validate is the bar. If it says console errors found, fix before rendering.
- Render exits 0 but `ffprobe` shows duration 0 or size < 10KB — the pipeline is broken, even though the CLI claimed success.

## Reference: minimal working composition

A 5-second title card that passes all checks. Drop into `demo/index.html` after `hyperframes init`:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body {
        margin: 0; width: 1920px; height: 1080px; overflow: hidden;
        background: #0a0a0f; color: #fff;
        font-family: -apple-system, "Helvetica Neue", Arial, sans-serif;
      }
      .scene-content {
        display: flex; flex-direction: column; justify-content: center;
        align-items: center; width: 100%; height: 100%; gap: 28px;
      }
      .title { font-size: 156px; font-weight: 800; }
    </style>
  </head>
  <body>
    <div data-composition-id="main" data-start="0" data-duration="5"
         data-width="1920" data-height="1080">
      <div class="scene-content">
        <h1 id="title" class="clip" data-start="0" data-duration="5" data-track-index="1">
          <div class="title">Hello Video</div>
        </h1>
      </div>
    </div>
    <script>
      window.__timelines = window.__timelines || {};
      const tl = gsap.timeline({ paused: true });
      tl.from("#title", { y: 80, opacity: 0, duration: 0.9, ease: "expo.out" }, 0.4);
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
```

This renders to a working MP4 with no media assets, proving the HTML→video pipeline end-to-end without needing video, audio, or external files.

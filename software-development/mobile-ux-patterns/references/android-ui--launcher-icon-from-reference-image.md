# Generating launcher icons from a user-supplied reference image

Recipe for when the user gives you a picture and says "use this as the launcher icon" (or "make it look like this"). Do NOT recreate from description — scale the user's raster directly.

## Pipeline

1. **Find the user's image.** It usually lives in `/home/thomas/.hermes/image_cache/img_<hash>.jpg`. Look for the most recent image after the user's "use this" message.

2. **Inspect it** with PIL — confirm it's a real icon (not a screenshot of the home screen), find the geometry (circle? rounded square? where does the mark sit?):

   ```python
   from PIL import Image
   img = Image.open(USER_IMAGE).convert("RGBA")
   w, h = img.size
   # Sample center, corners, edge midpoints to learn shape
   print("center:", img.getpixel((w//2, h//2)))
   print("TL/TR/BL/BR corners + top/bot/left/right edge midpoints")
   ```

3. **Decide: circle-on-square (transparent corners) vs full-bleed square.**
   - If reference is circle on white: circle stays as-is, replace white corners with transparent in PNG, AND set adaptive background drawable to the circle's fill color so the launcher BG doesn't show through.
   - If reference is full square: keep square, no transparency needed.

4. **Generate per-density PNGs** (mdpi=48, hdpi=72, xhdpi=96, xxhdpi=144, xxxhdpi=192):

   ```python
   DENSITIES = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}

   for density, size in DENSITIES.items():
       scaled = img.resize((size, size), Image.LANCZOS).convert("RGBA")
       pixels = scaled.load()
       # Make white corners transparent so launcher BG shows through (or matches)
       for y in range(size):
           for x in range(size):
               r, g, b, a = pixels[x, y]
               if r > 245 and g > 245 and b > 245:
                   pixels[x, y] = (0, 0, 0, 0)
       scaled.save(f"app/src/main/res/mipmap-{density}/ic_launcher.png")
       scaled.save(f"app/src/main/res/mipmap-{density}/ic_launcher_round.png")
   ```

5. **Adaptive icon XML drawables** (so Android 8.0+ uses vector):

   ```xml
   <!-- drawable/ic_launcher_background.xml — solid color matching the icon fill -->
   <vector xmlns:android="http://schemas.android.com/apk/res/android"
       android:width="108dp" android:height="108dp"
       android:viewportWidth="108" android:viewportHeight="108">
       <path android:fillColor="#FBECD9" android:pathData="M0,0h108v108h-108z" />
   </vector>
   ```

   ```xml
   <!-- drawable/ic_launcher_foreground.xml — the mark on transparent BG -->
   <vector xmlns:android="http://schemas.android.com/apk/res/android"
       android:width="108dp" android:height="108dp"
       android:viewportWidth="108" android:viewportHeight="108">
       <!-- mark paths here, e.g. folder body + tab -->
   </vector>
   ```

6. **mipmap-anydpi-v26/ic_launcher{,_round}.xml** — point to the drawables:

   ```xml
   <adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
       <background android:drawable="@drawable/ic_launcher_background" />
       <foreground android:drawable="@drawable/ic_launcher_foreground" />
   </adaptive-icon>
   ```

## Critical pitfalls

- **Don't ship BOTH `ic_launcher_foreground.xml` and `ic_launcher_foreground.png`** — the resource merger fails the build with `Error: Duplicate resources`. Pick one. Vector is preferred for adaptive icons.
- **NEVER recreate the icon procedurally, even when you've extracted the exact color/geometry.** This is the #1 way to burn 3+ design iterations. You extract metrics correctly (cream #FBECD9 background, gray #4E4F51 folder, 53% width, centered), procedurally draw it with PIL `rounded_rectangle`, and the result is *technically correct* but visually different — wrong stroke widths, wrong tab proportions, missing antialiasing nuance, slightly off shade. The user says "you didn't use my picture". Use their raster directly. The PIL analysis is for VERIFICATION, not regeneration.
- **For "edge-to-edge circle" appearance**, the background drawable color MUST match the icon's main fill color. Otherwise the launcher BG (often a dark theme color) bleeds through the transparent corners and creates a visible square frame.
- **Don't use adaptive foreground XML for legacy fallback.** Android 7 and below look up `mipmap-*dpi/ic_launcher.png` — keep the PNGs in all 5 densities.
- **The user's "reference" might be a wallpaper, not an icon.** Always check with PIL before scaling — sample corners and edges. If you find a phone home screen or random photo instead of a clean icon, ask the user for the actual icon before doing anything else. (Lesson: a previous attempt scaled a phone wallpaper as the launcher icon, wasted a build, user had to re-supply.)

## Quick verification after build

```bash
# Confirm the right assets shipped
unzip -l app-debug.apk | grep -E "ic_launcher"

# Check pixel sampling on the rendered PNG
python3 -c "
from PIL import Image
img = Image.open('app/src/main/res/mipmap-xxxhdpi/ic_launcher.png').convert('RGBA')
print('TL corner:', img.getpixel((0, 0)), '(should be transparent or BG color)')
print('Center:', img.getpixel((96, 96)), '(should be mark color)')
"

# Side-by-side comparison with the user's reference
python3 -c "
from PIL import Image
ref = Image.open(USER_IMAGE).convert('RGBA').resize((300, 300))
ours = Image.open('app/src/main/res/mipmap-xxxhdpi/ic_launcher.png').convert('RGBA').resize((300, 300))
side = Image.new('RGBA', (620, 320), (255, 255, 255, 255))
side.paste(ours, (10, 10), ours)
side.paste(ref, (310, 10), ref)
side.save('/tmp/icon_compare.png')
"
```

## Why this matters

The classic mistake (and how it played out in a real session): receive a reference image, run vision analysis that correctly extracts "circle, beige, gray folder, 53% width, centered", reconstruct from description with PIL primitives. Result: 4+ iterations of "no, not that size", "make the circle reach the edge", "you didn't use my picture". Each iteration burns the user's patience and your tokens. The shortcut is to scale the raster directly — once. If the user wants changes after that, edit the source image they gave you (or ask for a new one), don't redraw from metrics.
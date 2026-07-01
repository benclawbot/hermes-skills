# Adaptive launcher icon density sizes and padding rules

Exact pixel dimensions for Android launcher icon PNGs, plus the visual-fill rules that determine whether the mark looks correct on round vs square launchers.

## Per-density PNG sizes

| Density | Folder                  | Launcher PNG | Adaptive icon total |
|---------|-------------------------|--------------|---------------------|
| mdpi    | `mipmap-mdpi`           | 48×48        | 108×108 viewport    |
| hdpi    | `mipmap-hdpi`           | 72×72        | 108×108 viewport    |
| xhdpi   | `mipmap-xhdpi`          | 96×96        | 108×108 viewport    |
| xxhdpi  | `mipmap-xxhdpi`         | 144×144      | 108×108 viewport    |
| xxxhdpi | `mipmap-xxxhdpi`        | 192×192      | 108×108 viewport    |

Adaptive icons (`mipmap-anydpi-v26`) are density-independent — the same vector draws at any size.

## Adaptive icon safe zones

In the 108×108 viewport (units):

- **Inner safe zone:** 72×72 centered (the area every launcher guarantees is visible). Mark must fit inside this to never be clipped.
- **Outer zone:** 108×108 minus 18dp inset = 72×72 visible center. The remaining 18dp on each side may be clipped by the launcher's mask.
- **Round launcher:** clips to a circle of diameter 72 inside the 108 viewport — the outer corners of the square mark are invisible.

## Visual-fill rule of thumb

For a mark intended to look "edge-to-edge" on round launchers:

- **Foreground vector:** design the mark's bounding box to fill ~88×88 of the 108 viewport (i.e., 14% margin top/bottom/left/right). This bleeds slightly into the safe zone but reaches the round circumference cleanly.
- **Square launcher PNG:** leave ~16% margin so the launcher-applied squircle / rounded square doesn't pinch the corners.
- **Round launcher PNG:** push the mark to ~85–92% of the diameter. The circle's edge naturally crops the corners, so the mark can be larger than in the square version.

## Pitfall: bbox-center ≠ visual-center for asymmetric marks

A letter F (or any glyph where one stroke is dominant) looks unbalanced if you center on the dominant stroke alone. Compute the bounding box of the **entire mark** including arms, then translate so the bbox center sits on the canvas center. ASCII preview at 48×48 is the fastest way to spot this — bbox math alone misses thin tapered strokes.

## Pitfall: legacy PNG ≠ adaptive vector at the same size

Legacy `mipmap-xxxhdpi/ic_launcher_round.png` is a 192×192 raster with a hard alpha mask. Adaptive `mipmap-anydpi-v26/ic_launcher_round.xml` is the same XML body as the square variant — the launcher applies the round mask at runtime. Both must be regenerated when the brand changes; the adaptive XML alone isn't enough for Android 7 and below.

## Verifying "edge-to-edge" claims

When the user asks for "no margin" or "fills the space", pixel-bbox analysis on the rendered PNG is the ground truth:

```python
F_mask = (r<140) & (g<140) & (b<140) & (a>200)  # adjust thresholds to your mark color
ys, xs = np.where(F_mask)
print(f"bbox: x=[{xs.min()},{xs.max()}] y=[{ys.min()},{ys.max()}]")
print(f"fill ratio: width/canvas={(xs.max()-xs.min()+1)/W:.2%}")
```

For a launcher round PNG claiming "edge-to-edge", a fill ratio ≥ 80% on the diameter is a reasonable target. Below 70% and there's a visible margin.
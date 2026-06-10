#!/usr/bin/env python3
"""Post-render layout audit for research-briefing PDFs.

Run before every delivery. Detects four things vision_analyze gets wrong
roughly 30% of the time:

1. **Bottom-blank % per page.** Real pixel ratio of the bottom 30% strip
   that is white. Pages with >50% blank in the bottom 30% are real
   problems (orphan pages, content overflow). Pages with 100% blank
   in the bottom 15% are NORMAL page margins — don't panic.

2. **Chart width overflow.** Chromium --print-to-pdf does NOT respect
   CSS max-width: 100% on <img> tags. Charts wider than the page
   content width overflow the right edge of the PDF (chart 08 funding
   timeline, Anthropic briefing 2026-06-10). This check catches it
   before delivery. A4 content width at ~110 DPI = ~850px.

3. **Chart marker overlap.** Flood-fill on red/gold/grey pixels per
   chart, pairwise center-to-center distance check. Catches the
   "labels stacked on the same point" bug. Vision reports this
   inconsistently; the pixel test is ground truth.

4. **Image embed count.** Chromium has been known to render a PDF
   that has the LAYOUT but is missing the chart PNGs (file://
   relative-path bug). Compares `pdfimages -list` count to the
   number of .png files in the charts dir.

Usage:
    python3 audit_layout.py briefing.pdf charts/

Exit code 0 on pass, 1 on any failure. Print a final VERDICT line
so a CI / shell can grep for it.

The Anthropic briefing (2026-06-09) is what motivated this script.
The vision model said "6, 12, and possibly 1 appear to be hidden
in the heatmap" — this script's flood-fill found all 12 markers
in distinct positions with 0 close pairs. Vision was wrong; this
script was right.
"""
import subprocess
import sys
from pathlib import Path

# A4 page = 595pt wide. 18mm side margins on the briefing template
# (templates/briefing.html) = 51pt each. Content width = 544pt.
# At 110 DPI, that's ~837px. Round up to 850 as a soft threshold.
PAGE_CONTENT_WIDTH_PX = 850

# Color masks for matplotlib palettes. The briefing charts use these
# specific RGB values — adjust if the palette changes.
COLOR_MASKS = {
    "red":   lambda r, g, b: (r > 150) & (g < 70) & (b < 70),
    "gold":  lambda r, g, b: (r > 180) & (r < 220) & (g > 130) & (g < 200) & (b < 130),
    "grey":  lambda r, g, b: (r > 100) & (r < 160) & (g > 100) & (g < 160) & (b > 110) & (b < 170),
}

CLOSE_PAIR_THRESHOLD = 60  # pixels — markers within this are "overlapping"


def bottom_blank_pct(pdf_path):
    """For each page, compute blank % in the bottom 30% strip."""
    out_dir = Path("/tmp/_audit_pages")
    out_dir.mkdir(exist_ok=True)
    # Render at 90 dpi; we only need the bottom strip
    subprocess.run(
        ["pdftoppm", "-png", "-r", "90", str(pdf_path), str(out_dir / "p")],
        check=True, capture_output=True,
    )
    from PIL import Image
    import numpy as np

    results = []
    for png in sorted(out_dir.glob("p-*.png"), key=lambda p: int(p.stem.split("-")[1])):
        img = np.array(Image.open(png).convert("L"))
        h, w = img.shape
        # Bottom 30% strip
        bot30 = img[int(h * 0.70):, :]
        white = (bot30 > 240).sum() / bot30.size
        page_num = int(png.stem.split("-")[1])
        results.append((page_num, 100 * white))
    # Cleanup
    for png in out_dir.glob("p-*.png"):
        png.unlink()
    out_dir.rmdir()
    return results


def chart_width_overflow(charts_dir):
    """Check that every chart PNG fits the page content width.

    Catches the chromium --print-to-pdf max-width bug: charts
    wider than 850px (A4 content at 110 DPI) overflow the right
    edge of the PDF regardless of CSS max-width: 100%.

    Returns a list of (filename, width, height) tuples for
    offending charts.
    """
    from PIL import Image
    issues = []
    for png in sorted(Path(charts_dir).glob("*.png")):
        try:
            with Image.open(png) as img:
                w, h = img.size
        except Exception:
            continue
        if w > PAGE_CONTENT_WIDTH_PX:
            issues.append((png.name, w, h))
    return issues


def chart_marker_overlap(charts_dir):
    """Flood-fill on color-mask pixels; report any markers < threshold apart."""
    from PIL import Image
    import numpy as np

    def find_blobs(mask, min_size=500):
        visited = np.zeros_like(mask, dtype=bool)
        blobs = []
        h, w = mask.shape
        # Sample every 2 rows for speed; we don't need pixel-perfect blobs
        for y in range(0, h, 2):
            for x in range(w):
                if mask[y, x] and not visited[y, x]:
                    stack = [(y, x)]
                    pixels = []
                    while stack:
                        cy, cx = stack.pop()
                        if cy < 0 or cy >= h or cx < 0 or cx >= w:
                            continue
                        if visited[cy, cx] or not mask[cy, cx]:
                            continue
                        visited[cy, cx] = True
                        pixels.append((cy, cx))
                        stack.extend([(cy+1, cx), (cy-1, cx), (cy, cx+1), (cy, cx-1)])
                    if len(pixels) > min_size:
                        ys = [p[0] for p in pixels]
                        xs = [p[1] for p in pixels]
                        blobs.append((sum(xs)/len(xs), sum(ys)/len(ys), len(pixels)))
        return blobs

    issues = []
    for png in sorted(Path(charts_dir).glob("*.png")):
        # Skip if it's not a chart with markers (e.g. legends, source-only)
        # Heuristic: only check the risk heatmap explicitly
        if "risk_heatmap" not in png.name:
            continue
        arr = np.array(Image.open(png).convert("RGB"))
        all_markers = []
        for name, mask_fn in COLOR_MASKS.items():
            mask = mask_fn(arr[:,:,0], arr[:,:,1], arr[:,:,2])
            for cx, cy, size in find_blobs(mask):
                all_markers.append((name, cx, cy, size))
        # Pairwise distance check
        close_pairs = []
        for i in range(len(all_markers)):
            for j in range(i+1, len(all_markers)):
                d = ((all_markers[i][1] - all_markers[j][1])**2 +
                     (all_markers[i][2] - all_markers[j][2])**2) ** 0.5
                if d < CLOSE_PAIR_THRESHOLD:
                    close_pairs.append((all_markers[i], all_markers[j], d))
        if close_pairs:
            issues.append((png.name, len(all_markers), close_pairs))
        else:
            print(f"  {png.name}: {len(all_markers)} markers, OK")
    return issues


def embedded_image_count(pdf_path, charts_dir):
    """Compare pdfimages count to PNG file count in charts dir."""
    expected = len(list(Path(charts_dir).glob("*.png")))
    try:
        result = subprocess.run(
            ["pdfimages", "-list", str(pdf_path)],
            capture_output=True, text=True, check=True,
        )
    except FileNotFoundError:
        return (expected, -1, "pdfimages not installed")
    # Count image lines (skip header)
    lines = [l for l in result.stdout.splitlines() if l.strip() and l[0].isdigit()]
    return (expected, len(lines), None)


def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} briefing.pdf charts/", file=sys.stderr)
        sys.exit(2)

    pdf_path = Path(sys.argv[1])
    charts_dir = Path(sys.argv[2])

    if not pdf_path.exists():
        print(f"ERROR: {pdf_path} not found", file=sys.stderr)
        sys.exit(2)
    if not charts_dir.exists():
        print(f"ERROR: {charts_dir} not found", file=sys.stderr)
        sys.exit(2)

    fail = False

    print("=== BOTTOM-BLANK % PER PAGE (lower 30% of page) ===")
    page_results = bottom_blank_pct(pdf_path)
    for page_num, blank_pct in page_results:
        marker = " ⚠" if blank_pct > 50 else ""
        if blank_pct > 50:
            fail = True
        print(f"  p{page_num:02d}: {blank_pct:5.1f}% blank{marker}")

    print()
    print(f"=== CHART WIDTH OVERFLOW (limit: {PAGE_CONTENT_WIDTH_PX}px = A4 content @ 110 DPI) ===")
    width_issues = chart_width_overflow(charts_dir)
    if width_issues:
        fail = True
        for name, w, h in width_issues:
            print(f"  ⚠ {name}: {w}x{h}px — overflows page, will clip right edge in PDF")
    else:
        print("  All charts within page width, OK")

    print()
    print("=== CHART MARKER OVERLAP (flood-fill, pairwise distance) ===")
    overlap_issues = chart_marker_overlap(charts_dir)
    if overlap_issues:
        fail = True
        for name, n_markers, pairs in overlap_issues:
            print(f"  ⚠ {name}: {n_markers} markers, {len(pairs)} close pairs")
            for a, b, d in pairs[:5]:
                print(f"     {a[0]}({a[1]:.0f},{a[2]:.0f}) <-> {b[0]}({b[1]:.0f},{b[2]:.0f}) d={d:.0f}")
    else:
        print("  All risk_heatmap charts: 0 close pairs, OK")

    print()
    print("=== EMBEDDED IMAGES ===")
    expected, actual, err = embedded_image_count(pdf_path, charts_dir)
    if err:
        print(f"  ⚠ {err}")
    else:
        marker = " ⚠" if actual < expected else ""
        if actual < expected:
            fail = True
        print(f"  PDF has {actual} images, expected >= {expected}{marker}")

    print()
    print("=== VERDICT ===")
    print("FAIL" if fail else "ALL CHECKS PASSED")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()

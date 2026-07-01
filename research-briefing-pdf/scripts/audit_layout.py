#!/usr/bin/env python3
"""Lean post-render audit for research-briefing-pdf.

Detects two real bugs and nothing else:
  1. Last page has too much bottom whitespace (orphan-half-page).
  2. Chromium forgot to embed any of the chart PNGs (blank rectangles).

Usage:
  python3 audit_layout.py <briefing.pdf>

Exits 0 on pass, 1 on fail. Stdout is the verdict + page-by-page readings.

Why only these two? Single-flow pagination (no fixed-height page boxes)
already eliminates orphan-half pages and bottom-blank % false positives.
The audit exists to catch the one bug class that can still slip through:
a final page whose body content stops at y < 60%, leaving the bottom
40% as unused A4 — looks unfinished in print.
"""
from __future__ import annotations
import subprocess, sys
from pathlib import Path


def render_pages(pdf_path, out_dir):
    """pdftoppm at 110dpi to PNG, one per page."""
    out_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["pdftoppm", "-r", "110", "-png", str(pdf_path), str(out_dir / "page")],
        check=True, capture_output=True,
    )
    return sorted(out_dir.glob("page-*.png"))


def bottom_blank_pct(png_path):
    """Fraction of bottom 30% of page that has no ink.

    Cream paper is rgb(245, 241, 234). Anything significantly darker = ink.
    Counts pixels with min-channel < 230 in the bottom 30% band.
    """
    from PIL import Image
    img = Image.open(png_path).convert("RGB")
    w, h = img.size
    band_top = int(h * 0.70)
    band = img.crop((0, band_top, w, h))
    bw, bh = band.size
    px = band.load()
    ink = 0
    # Sample every 4th pixel for speed (still > 100k samples per band)
    for y in range(0, bh, 4):
        for x in range(0, bw, 4):
            r, g, b = px[x, y]
            if min(r, g, b) < 230:
                ink += 1
    samples = (bh // 4) * ((bw + 3) // 4)
    return 1.0 - (ink / max(samples, 1)), ink


def main():
    if len(sys.argv) < 2:
        print("usage: audit_layout.py <briefing.pdf>", file=sys.stderr)
        sys.exit(2)
    pdf_path = Path(sys.argv[1])
    if not pdf_path.exists():
        print(f"not found: {pdf_path}", file=sys.stderr)
        sys.exit(2)

    # 1. Confirm chart embeds via pdfimages.
    # pdfimages -list lines: data rows start with whitespace + page number;
    # the first non-data line is the dashed header. Detect by checking that
    # the first whitespace-delimited token is a digit (the page number).
    pi = subprocess.run(["pdfimages", "-list", str(pdf_path)],
                        capture_output=True, text=True)
    img_lines = [ln for ln in pi.stdout.splitlines()
                 if ln and ln.lstrip() and ln.lstrip().split()[0].isdigit()]
    n_images = len(img_lines)

    # 2. Render + scan bottom-blank
    tmp = Path("/tmp/audit_layout_" + pdf_path.stem)
    pages = render_pages(pdf_path, tmp)

    findings = []
    pass_flag = True

    if n_images == 0:
        findings.append(f"FAIL · no chart images embedded in PDF "
                        f"(chromium likely missing --allow-file-access-from-files)")
        pass_flag = False
    else:
        findings.append(f"OK   · {n_images} chart image(s) embedded")

    for p in pages:
        blank, ink = bottom_blank_pct(p)
        # Page number from filename: "page-3.png" → 3
        n = int(p.stem.split("-")[1])
        verdict = "OK  "
        # Last page with >40% blank in bottom 30% is an orphan-half.
        if n == len(pages) and blank > 0.40 and ink < 200:
            verdict = "FAIL"
            pass_flag = False
        # Non-last pages with >85% blank in bottom 30% = too much trailing space.
        elif n != len(pages) and blank > 0.85 and ink < 50:
            verdict = "WARN"
        findings.append(f"{verdict} · page {n}/{len(pages)}: "
                        f"bottom-30% blank = {blank*100:.1f}% (ink px: {ink})")

    print(f"\nAUDIT · {pdf_path.name}")
    for f in findings:
        print(f"  {f}")
    print(f"\n{'PASS' if pass_flag else 'FAIL'}")
    sys.exit(0 if pass_flag else 1)


if __name__ == "__main__":
    main()

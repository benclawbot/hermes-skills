# Crop Circle Cipher Investigation (May 2026)

## Source Images

- **Image 1 (crescent pattern):** `img_5f6644c1d897.jpg` — golden circles on olive green, diagonal background lines, decorative
- **Image 2 (spiral pattern):** `img_d733a1b1baa8.jpg` — white circles in logarithmic spiral on green textured background

## Image 2: Key Geometric Data

- **Dimensions:** 595×451 pixels
- **Center:** (297, 225)
- **Circle radii:** PERFECTLY LINEAR — 5, 10, 15, 20, 25... px increments (NOT Fibonacci)
- **Peak angles (30 samples):** 12, 45, 8, 30, 156, 120, 60, 168, 180, 30, 72, 84, 204, 228, 96, 120, 132, 180, 96, 24, 72, 36, 240, 228, 120, 144, 204, 216, 300, 60

## Decoding Attempts (ALL FAILED)

### Angular Gaps Sequence
`IKEEUEWEMWKGUOSCASKOQGCWOSOWIW` (from angular gaps between brightness peaks)

| Method | Result | Notes |
|--------|--------|-------|
| Caesar (all 25 shifts) | Gibberish | No English |
| Atbash | Gibberish | No English |
| Vigenere (KEY, CODE, CIPHER, CRYPTO, etc.) | Gibberish | No meaningful keys |
| Rail fence (2-7 rails) | Gibberish | No readable output |
| p² mod 26 | Gibberish | |
| 2p+3 mod 26 | Gibberish | |
| Position-based transforms | Gibberish | |
| Reversed + Caesar | Gibberish | |

### Other Methods

| Method | Result | Notes |
|--------|--------|-------|
| Binary→ASCII from angles | `:`, `?` fragments only | Non-printable bytes dominant |
| Musical note mapping (all 12 keys) | Various notes | Keys 6 & 12 → all C notes (convergent property) |
| GPS from letter sums | 51°9'13"N, 49°5'29"E | Kazakhstan/steppe — not meaningful for this test |
| Mathematical constants (Pi, e, Phi) | No match | Sequence didn't align |
| Base-N (6, 8, 12, 24 divisions) | Gibberish | |
| Fibonacci encoding | Not applicable | Radii are linear, not Fibonacci |

## Key Finding

**The spiral is NOT natural/Fibonacci.** Radii are perfectly linear (every 5px). This indicates deliberate geometric design — someone coded the measurements intentionally. But the encoding scheme is non-standard or obfuscated.

**Pattern evaluation:** Angular gap sequence `IKEEUEWEMWKGUOSCASKOQGCWOSOWIW` has letter frequency {W:5, E:4, O:4, S:3, K:3, I:2, C:2, G:2, U:2} — W most common. English E is most common, T second. This doesn't match English letter frequency, suggesting it's either encrypted or not English plaintext.

## What Would Crack This

1. **Known plaintext** — if this is from a verified crop circle with a published solution, test against that
2. **Custom cipher key** — without the key, many schemes can't be distinguished from random
3. **Physical measurement** — actual crop circle proportions in the field vs. photographed/screen representation may differ

## Files Used

- `/home/thomas/.hermes/cache/images/img_d733a1b1baa8.jpg`
- `/home/thomas/.hermes/cache/images/img_5f6644c1d897.jpg`

## Python Environment Note

System Python is externally managed. Use `/tmp/venv` for PIL:
```bash
cd /tmp && /tmp/venv/bin/python3
# Install: /tmp/venv/bin/pip install pillow
```
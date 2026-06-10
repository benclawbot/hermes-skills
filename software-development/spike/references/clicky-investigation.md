# Clicky Investigation — Full Codebase Reverse-Engineering

**Purpose:** Preserve the complete methodology and findings from the Clicky macOS → Windows port investigation. Used when the user says "go deep", "document everything", or "1:1 rewrite for Windows" — prevents re-reading every file in future sessions.

**Source investigation:** `farzaa/clicky` (macOS, ~7,637 lines Swift, 25 files) + `JaySmith502/clicky-win` (existing Windows port, 3,810 lines Python).

---

## Complete File Inventory (macOS original)

| File | Lines | Purpose |
|------|-------|---------|
| `CompanionManager.swift` | 1,026 | Central state machine, screen capture trigger, coordinate mapping, onboarding |
| `OverlayWindow.swift` | 881 | Per-display overlay, bezier arc flight, speech bubble, AVPlayer video |
| `DesignSystem.swift` | 880 | Full token palette, typography, animations, button styles, component specs |
| `BuddyDictationManager.swift` | 866 | AVAudioEngine pipeline, VAD/silence detection, keyterms propagation |
| `CompanionPanelView.swift` | 761 | SwiftUI panel, conversation history, onboarding, HLS video player |
| `AssemblyAIStreamingTranscriptionProvider.swift` | 478 | WebSocket streaming transcription |
| `ElementLocationDetector.swift` | 335 | `[POINT:x,y:label]` regex parsing, coordinate scaling |
| `OpenAIAudioTranscriptionProvider.swift` | 317 | Batch transcription via multipart form |
| `ClaudeAPI.swift` | 291 | Anthropic SSE streaming client, conversation history |
| `MenuBarPanelManager.swift` | 243 | NSStatusItem, nonactivatingPanel, click-outside monitor |
| `WindowPositionManager.swift` | 262 | AXUIElement window shrinking, multi-monitor |
| `GlobalPushToTalkShortcutMonitor.swift` | 132 | CGEvent tap for Ctrl+Option detection |
| `CompanionScreenCaptureUtility.swift` | 132 | ScreenCaptureKit wrapper, per-display JPEG |
| `ClickyAnalytics.swift` | 121 | PostHog events (13 event types) |
| `BuddyAudioConversionSupport.swift` | 108 | PCM16 conversion, WAV builder |
| `OpenAIAPI.swift` | 142 | OpenAI chat + vision API |
| `AppleSpeechTranscriptionProvider.swift` | 147 | On-device Apple Speech framework |
| `ElevenLabsTTSClient.swift` | 81 | ElevenLabs HTTP TTS |
| `AppBundleConfiguration.swift` | 28 | Info.plist reader |
| `leanring_buddyApp.swift` | 89 | App entry, Sparkle updater stub |

**Total: 7,637 lines across 20+ Swift files**

---

## Exact Technical Values (from macOS source)

### VAD Parameters (BuddyDictationManager.swift)
- Power history: **44 samples** rolling window
- Sample interval: **70ms** (`60.0 / 1000.0 * historySize`)
- Speech threshold: **-30 dB** (energy above this = speech)
- Silence threshold: **-50 dB** (energy below this = silence)
- Hold time: **400ms** (`silenceHoldDuration = 0.4`)
- Baseline: **0.02** (minimum threshold)

### Bezier Arc Flight Math (OverlayWindow.swift)
```swift
// Control point at 0.4× distance along line
let t = 0.4
controlPoint = CGPoint(
    x: start.x + (end.x - start.x) * t,
    y: start.y + (end.y - start.y) * t - arcHeight
)

// Smoothstep easing
let t_norm = t / totalDistance
let t_smooth = t_norm * t_norm * (3 - 2 * t_smooth)

// Arc height cap
let arcHeight = min(distance * 0.2, 80)

// Scale at apex: sin(t*π)*0.3 + 1.0 (peaks at 1.3×)
let scale = sin(progress * Double.pi) * 0.3 + 1.0

// Rotation: atan2(tangent) + 90°, default -35°
let angle = atan2(dy, dx) * 180 / .pi + 90
```

### State Machine States (CompanionManager.swift)
```
idle → listening → transcribing → processing → responding → idle
                ↓               ↓
             error            error
```

### Speech Bubble States (OverlayWindow.swift)
```
hidden → invisible → visible → streaming → fading → hidden
```

### Audio Level Boost Formula (CompanionManager.swift)
```swift
let boosted = power * 10.2
let smoothed = previous * 0.72 + boosted * 0.28
```

---

## [POINT] Coordinate Format

**Regex:** `\[POINT:(?:none|(\d+)\s*,\s*(\d+)(?::([^\]:\s][^\]:]*?))?(?::screen(\d+))?)\]\s*$`

**Components:**
- `x,y` — screenshot pixel coordinates (origin top-left)
- `label` — element description (optional)
- `screenN` — which monitor (1-indexed, optional)

**Mapping to screen coords:**
```python
real_x = screenshot.monitor_left + int(tag.x / screenshot.scale)
real_y = screenshot.monitor_top + int(tag.y / screenshot.scale)
```

---

## Design Tokens (DesignSystem.swift)

### Colors
```swift
// Surfaces
background = "#101212"
surface1 = "#18181B"
surface2 = "#232326"
surface3 = "#2C2C30"

// Text
textPrimary = "#FFFFFF"
textSecondary = "#A0A0A5"
textTertiary = "#555560"

// Accent
accentBlue = "#3380FF"
accentGreen = "#30D158"
accentYellow = "#FFD60A"
accentRed = "#FF453A"

// Overlay cursor
overlayCursorBlue = "#3380FF"
```

### Typography
```swift
fontSizeBody = 15
fontSizeCaption = 12
fontSizeHeading = 18
fontSizeSmall = 11
lineHeightBody = 22
lineHeightCaption = 16
```

### Spacing
```swift
spacingSmall = 4
spacingMedium = 8
spacingLarge = 16
spacingXLarge = 24
```

### Animation
```swift
appearDuration = 0.3  // ease-out
disappearDuration = 0.2  // ease-in
slideDuration = 0.4  // spring
```

---

## Windows Port: Locked Decisions

From user confirmation (May 2026):

1. **Voice service:** Python subprocess + WPF host. Setup.bat checks Python + installs deps.
2. **ElevenLabs:** Optional config field — Piper is default, ElevenLabs opt-in.
3. **MiniMax API key:** User inputs in onboarding panel (required).
4. **Offline:** No offline needed — cloud-only AI.
5. **Window shrinking:** Win32 `SetWindowPos` replicates macOS `AXUIElement` behavior exactly.
6. **Onboarding video:** Removed — text-only flow.

---

## Key Lesson

**Check for existing ports before building from scratch.**

The original request was "1:1 rewrite of Clicky for Windows." The agent spent ~20 minutes building a WPF port with critical gaps. An existing production-quality port (`clicky-win` by JaySmith502, PySide6, 3,810 lines) was significantly more complete — full CompanionManager, proper hotkey detection, streaming transcription, SSE parsing, waveform visualization, fly-to animation, multi-monitor support, test suite. The agent found it only after the user pointed it out.

**Pattern:** When the user wants a cross-platform rewrite, the investigation phase must include a check for existing ports on the target platform before committing to from-scratch implementation. Existing ports benefit from months of real-user bug reports and production hardening.

---

## Existing Port: clicky-win (JaySmith502)

**Repo:** `https://github.com/JaySmith502/clicky-win`

**Architecture:** Single-process Python (PySide6), no subprocess IPC overhead.

**File inventory (3,810 lines Python + Cloudflare Worker):**
```
companion_manager.py     (393) — state machine
companion_widget.py     (608) — cursor overlay + waveform
hotkey.py               (285) — pynput Ctrl+Alt global detection
transcription_client.py  (458) — AssemblyAI WebSocket streaming
llm_client.py           (184) — Anthropic SSE parser
screen_capture.py       (118) — mss multi-monitor
point_parser.py          (37) — [POINT] regex
point_mapper.py          (33) — screenshot→screen coords
design_system.py         (65) — colors/spacing/fonts
config.py               (102) — TOML config
```

**Improvements over macOS original:**
- Strict modifier-only hotkey (macOS version can accidentally trigger when typing Ctrl+Alt+key)
- 8-bar waveform vs macOS's 5-bar
- Cursor-monitor priority for multi-monitor capture
- Error flash animation with auto-reset

**Omissions vs macOS:**
- No onboarding video (HLS) or background music
- No PostHog analytics
- No FormSpark email submission
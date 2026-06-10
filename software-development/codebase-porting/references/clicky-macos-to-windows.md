# Clicky macOS → Windows Port Reference

## Source Code Inventory (25 files, 7,637 lines)

| File | Lines | Purpose |
|---|---|---|
| CompanionManager.swift | 1,026 | Central state machine, screen capture trigger, coordinate mapping, element pointing |
| OverlayWindow.swift | 881 | Per-display overlay, bezier arc cursor flight animation, speech bubble states |
| DesignSystem.swift | 880 | Design tokens, colors (#0A0A0F surface, #FAFAFA text), typography (15pt body), animations |
| BuddyDictationManager.swift | 866 | AVAudioEngine pipeline, VAD (-30dB speech/-50dB silence), keyterms propagation |
| CompanionPanelView.swift | 761 | SwiftUI panel UI, conversation history, onboarding (3 steps), HLS video player |
| AssemblyAIStreamingTranscriptionProvider.swift | 478 | WebSocket streaming, real-time transcript events |
| ElementLocationDetector.swift | 335 | [POINT:x,y:label] regex parsing, coordinate scaling screenshot→global |
| OpenAIAudioTranscriptionProvider.swift | 317 | Batch transcription, PCM16 conversion |
| ClaudeAPI.swift | 291 | Anthropic streaming, conversation history |
| WindowPositionManager.swift | 262 | AXUIElement API, multi-monitor frame handling |
| MenuBarPanelManager.swift | 243 | NSStatusItem, tray panel lifecycle |
| CompanionResponseOverlay.swift | 217 | Cursor-following streaming bubble, 60fps tracking, auto-hide at 6s |
| AppleSpeechTranscriptionProvider.swift | 147 | On-device Apple Speech, no API needed |
| OpenAIAPI.swift | 142 | OpenAI chat + vision |
| GlobalPushToTalkShortcutMonitor.swift | 132 | CGEvent tap Ctrl+Option |
| CompanionScreenCaptureUtility.swift | 132 | ScreenCaptureKit, per-display JPEG 0.8 quality |
| ClickyAnalytics.swift | 121 | PostHog events (13 event types) |
| BuddyAudioConversionSupport.swift | 108 | PCM16 conversion, WAV builder |
| BuddyTranscriptionProvider.swift | 100 | Provider factory, fallback chain |
| leanring_buddyApp.swift | 89 | App entry, menu bar setup |
| ElevenLabsTTSClient.swift | 81 | ElevenLabs HTTP streaming |
| AppBundleConfiguration.swift | 28 | Info.plist reader |

## Key Subsystem Details

### State Machine (CompanionManager)
States: off → idle → listening → transcribing → processing → responding → error
Transitions trigger screen capture (on → processing), element pointing (AI response with POINT tag).

### Bezier Arc Math (OverlayWindow)
```python
# Control point at 0.4× distance from start
t = 0.4
control = (start + (end - start) * t)
# Rotation angle from atan2 of delta
angle = atan2(end.y - start.y, end.x - start.x)
# Scale peaks at 1.3× at arc apex
```

### VAD Parameters (BuddyDictationManager)
- Speech threshold: -30dB
- Silence threshold: -50dB with 400ms hold
- Keyterms propagated to AssemblyAI as keyword_boost parameter

### Speech Bubble States
hidden → invisible → visible → streaming → fading → hidden
Auto-hide fires at 6s after streaming stops. Edge flip when cursor near screen boundary.

### Analytics Events (ClickyAnalytics)
`analytics_tracking`, `onboarding_started`, `onboarding_demo_triggered`, `push_to_talk_started`, `user_message_sent`, `ai_response_received`, `element_pointed`, `response_error`, `tts_error`, `tts_started`, `companion_opened`, `companion_closed`, `error_occurred`

## Windows Implementation (clicky-win)

### Architecture
- WPF C# host (`Clicky/`) + Python subprocess (`Clicky.VoiceService/`)
- IPC over stdin/stdout JSON
- Python: mss (screenshot), whisper (transcription), Piper/ElevenLabs (TTS)

### Key Files
- `ai_service.py` — provider/model architecture. Providers: `minimax` (base_url api.minimax.chat/v2/messages), `openai` (api.openai.com/v1/chat/completions). Model configurable. SSE parsing handles both OpenAI `choices[].message.content` and MiniMax v2 `output.text` formats.
- `main.py` — IPC command router. Actions: `start_recording`, `stop_recording`, `transcribe`, `capture_screenshot`, `analyze`, `speak`, `stop_speaking`, `set_api_key` (with provider/model), `set_config`, `configure_ai`
- `ConfigService.cs` — JSON at `~/.clicky/config.json`. Fields: `AiProvider`, `AiModel`, `MiniMaxApiKey`, `OpenAIApiKey`, `ElevenLabsApiKey`, `ElevenLabsVoiceId`, `TTSProvider`

### Windows API Equivalents
| macOS | Windows |
|---|---|
| AXUIElement SetWindowPos | Win32 SetWindowPos + GetWindowRect |
| CGEvent tap (Ctrl+Option) | SetWindowsHookEx (WH_KEYBOARD_LL) |
| NSStatusItem | NotifyIcon (System.Windows.Forms) |
| ScreenCaptureKit | mss.mss() + PIL |
| Apple Speech | Piper TTS + Windows SAPI |
| PostHog | Config-only (no analytics impl) |

## MiniMax API Details

### Request Format
```python
POST https://api.minimax.chat/v2/messages
Authorization: Bearer <key>
{"model": "MiniMax-M2.7", "messages": [...], "stream": False}
```

### Response Format (v2)
```json
{"output": {"text": "...", "finish_reason": "stop"}}
```
Extract via: `data["output"]["text"]` or iterate `data["output"]` list for `text` field.

### Available Models
- `MiniMax-M2.7` (default)
- `MiniMax-M2` 
- `MiniMax-M1.5`
Models can be specified via `AiModel` config field.

## Decisions Locked

1. MiniMax M2.7 primary AI, user provides API key via onboarding panel
2. OpenAI-compatible provider also available (gpt-4o, etc.)
3. ElevenLabs optional TTS, Piper default, pyttsx3 fallback
4. Window shrinking via Win32 SetWindowPos (not AXUIElement equivalent)
5. No onboarding video — text-only flow
6. Python setup check + auto-deps on first run
7. Provider/model configurable at runtime via `configure_ai` IPC action
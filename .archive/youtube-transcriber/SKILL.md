---
name: youtube-transcriber
description: Transcribe YouTube videos fast using yt-dlp + whisper. Extract clean text, no browser needed.
version: 1.0.0
---

# YouTube Transcriber

Transcribe any YouTube video in seconds — no browser, no manual downloading.

## Prerequisites

```bash
uv tool install yt-dlp
# whisper CLI must be available at: ~/Desktop/hermes-agent/.venv/bin/whisper
```

## Quick use

**1. Download auto-captions (fastest, en only):**
```bash
yt-dlp --write-auto-subs --sub-lang en --skip-download --convert-subs srt -o /tmp/yt_sub VIDEO_ID
```

**2. Clean the SRT (remove timestamps/dupes):**
```bash
cat /tmp/yt_sub.en.srt | grep -v "^[[:digit:]]\+$" | grep -v "^$" | grep -v "^00:" | tr '\r' ' ' | tr -s ' '
```

**3. Pipe to LLM for summary:**
```bash
curl -s --max-time 8 "https://hn.algolia.com/api/v1/search?query=..." | python3 -c "..."
```

## Full pipeline script

```bash
#!/bin/bash
# Usage: ./yt_transcribe.sh VIDEO_URL_OR_ID
VIDEO_ID=$(echo "$1" | sed 's/.*v=\([^&]*\).*/\1/')
OUTPUT="/tmp/yt_sub_$$.srt"
yt-dlp --write-auto-subs --sub-lang en --skip-download --convert-subs srt -o "$OUTPUT" "$VIDEO_ID" 2>/dev/null
cat "${OUTPUT%.srt}.en.srt" | grep -v "^[[:digit:]]\+$" | grep -v "^$" | grep -v "^00:" | tr '\r' ' ' | tr -s ' '
rm -f "${OUTPUT%.srt}.en.srt"
```

## Notes

- yt-dlp installed via `uv tool install yt-dlp`
- If no auto-captions available, fall back to whisper (slower — requires audio download + transcription)
- whisper at `~/Desktop/hermes-agent/.venv/bin/whisper` (not system whisper)

# Upload zone: ASR gap pitfall

When a UI design shows a file upload zone that accepts audio/video (`.mp4`, `.m4a`, `.mp3`, `.wav`) and says "drop your recording to generate X", but the backend has **no automatic speech recognition (ASR)** wired in, do NOT silently invent a transcription pipeline or claim the file "will be processed". Surface the gap and degrade gracefully.

## The trap

Designs frequently show a beautiful "Glisser-déposer" cloud-upload zone, and a user reasonably expects:
> drop a 200MB audio file → app transcribes it → app processes the text.

If the backend is text-only (just calls an LLM with a string), the agent that builds the front end will hit one of these failure modes:

1. **Invent a fake client-side transcription** — a hidden whisper.cpp / Web Speech API call that won't actually work for pre-recorded files. This *looks* complete in the demo and silently produces nothing.
2. **Silently drop the file** — accept the file, set `fileName` in state, do nothing with it, claim success. Worst outcome: user thinks it worked.
3. **Refuse to build** — push back that the backend needs ASR. Right instinct, but the user wanted a UI step and the gap is the implementer's problem, not theirs.

## The right pattern: degrade honestly

Accept the file, show the filename, then route to whatever the backend can actually do:

```tsx
const handleFiles = async (files: FileList | null) => {
  const file = files?.[0]
  if (!file) return
  if (file.size > 200 * 1024 * 1024) {
    setError('Fichier trop volumineux (max 200 Mo).')
    return
  }
  setFileName(file.name)

  // 1. Text-shaped files: read into the notes textarea directly
  const textExts = ['.txt', '.md', '.json', '.csv', '.srt', '.vtt']
  if (textExts.some(ext => file.name.toLowerCase().endsWith(ext)) || file.type.startsWith('text/')) {
    setRawNotes(prev => prev.trim() ? `${prev}\n\n${await file.text()}` : await file.text())
    return
  }

  // 2. Audio/video: backend can't transcribe → show a notice AND a paste zone
  setError(
    `Le fichier "${file.name}" a été reçu. ` +
    `Collez la transcription ci-dessous pour générer le compte rendu.`
  )
}
```

Then in the form, **always** include a `Notes brutes` textarea right next to the upload zone so the user has somewhere obvious to paste.

## What this looks like to the user

- They drop an `.mp4` → they see "File received. Paste the transcript to generate." (FR equivalent).
- They paste the text from a meeting tool they already use (Otter, Fireflies, Granola) → generation works.
- The UI never pretended to transcribe — it routed around the missing capability.

## Tell the user the real fix (one sentence)

After shipping the degraded UX, flag the backend gap:

> "Right now this routes around the missing ASR — if you want real audio transcription, the backend needs a Whisper / Gemini-audio call before `processMeetingNotes`. Want me to wire that next?"

That keeps the design deliverable shippable AND makes the missing capability visible.

## When this is NOT a pitfall

- The backend already has ASR (check `services/` and `api/` for `whisper`, `transcribe`, audio in prompts) → build the happy path directly.
- The design is for a mockup / spec only, not a real build → the spec can describe the ideal, and the implementer will hit the gap themselves.
- The user is in a different language than the design reference and explicitly says "translate only, don't change behavior" → keep the UX copy in the user's language but the same pattern.

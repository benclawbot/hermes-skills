# Image Gen Routing — Why Not the Chat LLM

Captured: 2026-06-05 (after Thomas asked "can image gen be done by MiniMax-M3?").

## The Trap

When a user has a working chat LLM (text + vision) and asks about image generation, the obvious wrong answer is "yes, just enable it on the main model." Text LLMs do not generate images — they have **vision** (image-to-text analysis) only. Suggesting model switching for image gen is a waste of time and tokens.

## The Right Architecture

Hermes has a separate `image_gen` toolset with pluggable providers. The main chat model is decoupled from the image generator. Configuration lives in two places:

1. `~/.hermes/config.yaml`:
   ```yaml
   image_gen:
     provider: pollinations   # or dalle, comfyui, sd, etc.
   ```

2. `~/.hermes/.env`:
   ```
   POLLINATIONS_API_KEY=your_key_here
   ```

Restart gateway to activate: `systemctl --user restart hermes-gateway`.

## Pollinations Details

- **Free tier** exists (rate-limited)
- **Full API key** in `.env` gives higher limits
- API: `https://image.pollinations.ai/prompt/<encoded>?width=&height=&seed=&model=`
- Returns a redirect to a PNG/JPG — cache `response.content`

## "system dependency not met" — False Positive

`hermes doctor` shows `⚠ image_gen (system dependency not met)` even when Pollinations is fully configured and the key is in `.env`. This is a check_fn artifact — Pollinations' availability check is misfiring. The toolset still works.

**Verification:**
```bash
grep -i pollinations ~/.hermes/.env        # key present
hermes config 2>&1 | grep image_gen         # provider set
# Test directly: send an image_gen tool call — if it returns an image, it's working.
```

## When to Add a New Provider

If Pollinations doesn't fit (rate limits, style needs, cost), the alternatives are:

- **DALL-E** (OpenAI) — paid, excellent prompt adherence
- **Stable Diffusion** via ComfyUI (local) — free, slow, full control
- **Midjourney** — no public API, skip
- **Flux** (via Replicate / Together) — good open model

See `hermes-agent` skill → `references/image-gen-providers.md` for the full plugin authoring interface if you need to add a new provider.

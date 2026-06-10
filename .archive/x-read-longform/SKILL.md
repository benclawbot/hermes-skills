---
name: x-read-longform
description: Extract the full text of an X/Twitter post when public endpoints truncate it. Use when given an x.com or twitter.com URL, when browser_navigate times out on x.com, when curl HTML / xurl / syndication API returns text ending mid-sentence, or when a quoted post's content is missing from the visible preview. Prefer Jina reader as the working fallback; only fall back to the GraphQL NoteTweet endpoint when you have authenticated API access.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [x, twitter, extract, social-media, jina, fallback]
---

# Reading long-form X/Twitter posts

Public-facing X endpoints truncate post bodies around 1–2 KB. For long-form posts (note tweets, threads with code), you have to escalate through a stack of fallbacks. The `xurl` skill handles posting and authenticated reads; this skill handles the unauthenticated read case where the public surface is broken.

## When to load

Trigger on any of:
- User pastes an `https://x.com/.../status/...` or `https://twitter.com/.../status/...` URL and asks for the content
- `browser_navigate` times out on `x.com`
- You fetched the HTML and the embedded JSON `text` field ends mid-sentence (e.g. `"...using deepseek. I ended up writing"`)
- The `xurl read POST_ID` call returns a short body for a long-form post
- The post is a `note_tweet` (the long-form variant X uses for posts over the 280/4k char limit)

## The escalation ladder

Always try them in order — cheapest first, escalate only when the previous returns incomplete text.

### 1. `xurl read POST_ID` (best for authenticated agents)

If `xurl` is installed and authenticated (per the `xurl` skill), this returns the full body including `note_tweet` text. Free, no rate limit problems, structured JSON.

```bash
xurl read 2050956678502420612
xurl read https://x.com/i/status/2050956678502420612
```

### 2. Syndication API (no auth, but truncates)

`https://cdn.syndication.twimg.com/tweet-result?id=POST_ID&lang=en&token=x`

Returns JSON with a `text` field, a `note_tweet.id` reference, and a `quoted_tweet` if the post quotes another. The `text` field is **truncated to ~280 chars** for long posts — that's the failure signal. If you get less than the visible post length, escalate.

```bash
curl -sL "https://cdn.syndication.twimg.com/tweet-result?id=2050956678502420612&lang=en&token=x" \
  -A "Mozilla/5.0" | python3 -m json.tool
```

Detection heuristic: if `text` doesn't end with a sentence terminator and `note_tweet.id` is present, you're truncated.

### 3. Jina reader (THE WORKING FALLBACK)

`https://r.jina.ai/<URL>` — third-party web reader that renders the post in full, including `note_tweet` content. Returns markdown with a `Title:`, `URL Source:`, and `Markdown Content:` block.

```bash
curl -sL "https://r.jina.ai/https://x.com/i/status/2050956678502420612" \
  -A "Mozilla/5.0" -o /tmp/post.txt
# Then strip the Jina wrapper to get clean text:
python3 -c "import re; print(re.search(r'Markdown Content:\n(.*?)(?:\nURL Source:|\Z)', open('/tmp/post.txt').read(), re.DOTALL).group(1).strip())"
```

This is the only unauthenticated method I have found that returns the full `note_tweet` body as of June 2026. Other readers I tested and confirmed broken:

- `xcancel.com` — 503 Service Unavailable
- `nitter.privacydev.net` — returns empty
- `allorigins.win` — 522 Connection Timeout
- Raw HTML page curl — the embedded JSON `text` field is truncated, and `note_tweet` body is in a separate API call that requires auth
- x.com GraphQL `NoteTweetRest` endpoint — 403 without an authenticated session token

### 4. Authenticated GraphQL (last resort, only when 1–3 fail)

```
POST https://x.com/i/api/graphql/1oVZOJ4a8OJClOjW0WxJdg/NoteTweetRest
```

Requires a `ct0` cookie and bearer token. Not realistic for an agent without the user's session. Skip unless the user explicitly says "use the API" and provides creds.

## Verification

After extracting, sanity-check the text:

- Length matches the post's apparent size (a long-form post is usually 4k–25k chars; a normal post is under 280)
- Text ends with a sentence terminator (`.`, `?`, `!`, `)`, `]`)
- No `[truncated]` markers (Jina doesn't add these; if you see them, the source truncated before Jina)
- For threads, the first post should reference the rest of the thread, or you need to fetch each `in_reply_to_status_id` recursively

## Pitfalls

- **Don't trust HTML `text` fields alone** — they truncate. The HTML serves a preview, not the full body.
- **`note_tweet` is a separate API call** — the HTML references it by ID but doesn't include the body inline. Without the reader fallback, you can't get it.
- **Jina is third-party and rate-limited** — for one-off reads it's reliable, but don't hammer it. Cache results to `/tmp` per the recipe above.
- **Twitter `x.com` requires JS to render** — `browser_navigate` works but is slow and prone to 60s timeouts on long threads. The terminal/curl path is much faster.
- **Syndication API "succeeds" with 200 status** even when truncated — the response itself looks fine. Always check the `text` length against your expectation.

## When NOT to use this skill

- You have `xurl` authenticated and the post isn't `note_tweet` long — use `xurl read` directly
- The user wants a thread, not a single post — this skill reads one post at a time; you need to walk `in_reply_to_status_id` manually
- The post is from a suspended/private account — neither Jina nor any public endpoint will have it
- You need real-time updates — public endpoints are eventually consistent (seconds to minutes behind)

## Related

- `xurl` — the official CLI for posting and authenticated reads
- This skill is the **read-side** counterpart to `xurl`'s write-side coverage

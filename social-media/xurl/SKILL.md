---
name: xurl
description: "X/Twitter via xurl CLI: post, search, DM, media, v2 API, and read long-form posts."
version: 1.2.0
author: xdevplatform + openclaw + Hermes Agent
license: MIT
platforms: [linux, macos]
prerequisites:
  commands: [xurl]
metadata:
  hermes:
    tags: [twitter, x, social-media, xurl, official-api, long-form, note-tweet, jina, syndication]
    homepage: https://github.com/xdevplatform/xurl
    upstream_skill: https://github.com/openclaw/openclaw/blob/main/skills/xurl/SKILL.md
---

# xurl — X (Twitter) API via the Official CLI

`xurl` is the X developer platform's official CLI for the X API. It supports shortcut commands for common actions AND raw curl-style access to any v2 endpoint. All commands return JSON to stdout.

Use this skill for:
- posting, replying, quoting, deleting posts
- searching posts and reading timelines/mentions
- liking, reposting, bookmarking
- following, unfollowing, blocking, muting
- direct messages
- media uploads (images and video)
- raw access to any X API v2 endpoint
- multi-app / multi-account workflows

This skill replaces the older `xitter` skill (which wrapped a third-party Python CLI). `xurl` is maintained by the X developer platform team, supports OAuth 2.0 PKCE with auto-refresh, and covers a substantially larger API surface.

## When xurl Is Not Installed or Not Authenticated

`xurl` is the preferred path, but two situations force fallback to public endpoints:

1. **`xurl` binary not installed** — `command -v xurl` returns empty. Agent runs in an environment where xurl was never installed (e.g. new machine, minimal container, or someone uninstalled it).
2. **Auth not set up** — `xurl auth status` shows no apps with oauth2 tokens, or token-expired errors on every call. The user hasn't completed the one-time setup in the next section.

**Fallback ladder for read operations:**

| Need | Best fallback | When to use |
|---|---|---|
| Read a single post (non-`note_tweet`) | `curl https://cdn.syndication.twimg.com/tweet-result?id=POST_ID&lang=en&token=0 -A "Mozilla/5.0"` | Fastest, returns full JSON including engagement counts. Truncates at ~280 chars for `note_tweet` posts. |
| Read a user profile + recent posts | `curl https://r.jina.ai/https://x.com/<handle> -A "Mozilla/5.0"` | Renders profile + first 7–10 posts as markdown. Best for "who is this person / what's their vibe" queries. |
| Read a long-form `note_tweet` (4k–25k chars) | Same as above, Jina reader. | Only Jina reliably returns full `note_tweet` body. See `x-read-longform` skill for the full ladder. |
| Search posts | `curl https://r.jina.ai/https://x.com/search?q=...&src=typed_query` | Returns first page of search results as markdown. |
| Post, reply, like, follow, DM | None — must use xurl or browser automation. | Without auth there is no write path. Tell the user to run `xurl auth oauth2 --app <app> <handle>` outside the agent session. |

**Critical rule:** When falling back to public endpoints, do NOT auto-install xurl or attempt OAuth setup. These actions need user interaction (browser, credential paste). The right move is to use the fallback, complete the task, and mention in the final reply that xurl could be installed for richer access in future sessions.

**Don't try to scrape x.com HTML** — it requires JS rendering, the embedded JSON `text` field truncates `note_tweet` posts, and the auth wall is opaque. Always use the syndication API or Jina.

See `x-read-longform` for the full read-side ladder including a verification recipe for completeness checks.

---

## Secret Safety (MANDATORY)

Critical rules when operating inside an agent/LLM session:

- **Never** read, print, parse, summarize, upload, or send `~/.xurl` to LLM context.
- **Never** ask the user to paste credentials/tokens into chat.
- The user must fill `~/.xurl` with secrets manually on their own machine. In Docker, this must be the `~` seen by Hermes tool subprocesses; see the Docker note below.
- **Never** recommend or execute auth commands with inline secrets in agent sessions.
- **Never** use `--verbose` / `-v` in agent sessions — it can expose auth headers/tokens.
- To verify credentials exist, only use: `xurl auth status`.

Forbidden flags in agent commands (they accept inline secrets):
`--bearer-token`, `--consumer-key`, `--consumer-secret`, `--access-token`, `--token-secret`, `--client-id`, `--client-secret`

App credential registration and credential rotation must be done by the user manually, outside the agent session. After credentials are registered, the user authenticates with `xurl auth oauth2` — also outside the agent session. Tokens persist to `~/.xurl` in YAML. Each app has isolated tokens. OAuth 2.0 tokens auto-refresh.

---

## Installation

Pick ONE method. On Linux, the shell script or `go install` are the easiest.

```bash
# Shell script (installs to ~/.local/bin, no sudo, works on Linux + macOS)
curl -fsSL https://raw.githubusercontent.com/xdevplatform/xurl/main/install.sh | bash

# Homebrew (macOS)
brew install --cask xdevplatform/tap/xurl

# npm
npm install -g @xdevplatform/xurl

# Go
go install github.com/xdevplatform/xurl@latest
```

Verify:

```bash
xurl --help
xurl auth status
```

If `xurl` is installed but `auth status` shows no apps or tokens, the user needs to complete auth manually — see the next section.

---

## One-Time User Setup (user runs these outside the agent)

These steps must be performed by the user directly, NOT by the agent, because they involve pasting secrets. Direct the user to this block; do not execute it for them.

1. Create or open an app at https://developer.x.com/en/portal/dashboard
2. Set the redirect URI to `http://localhost:8080/callback`
3. Copy the app's Client ID and Client Secret
4. Register the app locally (user runs this):
   ```bash
   xurl auth apps add my-app --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
   ```
5. Authenticate (specify `--app` to bind the token to your app):
   ```bash
   xurl auth oauth2 --app my-app
   ```
   (This opens a browser for the OAuth 2.0 PKCE flow.)

   If X returns a `UsernameNotFound` error or 403 on the post-OAuth `/2/users/me` lookup, pass your handle explicitly (xurl v1.1.0+):
   ```bash
   xurl auth oauth2 --app my-app YOUR_USERNAME
   ```
   This binds the token to your handle and skips the broken `/2/users/me` call.
6. Set the app as default so all commands use it:
   ```bash
   xurl auth default my-app
   ```
7. Verify:
   ```bash
   xurl auth status
   xurl whoami
   ```

After this, the agent can use any command below without further setup. OAuth 2.0 tokens auto-refresh.

> **Common pitfall:** If you omit `--app my-app` from `xurl auth oauth2`, the OAuth token is saved to the built-in `default` app profile — which has no client-id or client-secret. Commands will fail with auth errors even though the OAuth flow appeared to succeed. If you hit this, re-run `xurl auth oauth2 --app my-app` and `xurl auth default my-app`.

> **Docker HOME pitfall:** In the official Hermes Docker layout, `/opt/data` is `HERMES_HOME`, but Hermes tool subprocesses use `/opt/data/home` as `HOME`. That means `~/.xurl` resolves to `/opt/data/home/.xurl` for Hermes-run `xurl` commands, not `/opt/data/.xurl`. Run the user setup with the same HOME:
> ```bash
> HOME=/opt/data/home xurl auth apps add my-app --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
> HOME=/opt/data/home xurl auth oauth2 --app my-app YOUR_USERNAME
> HOME=/opt/data/home xurl auth default my-app YOUR_USERNAME
> HOME=/opt/data/home xurl auth status
> ```
> If `HOME=/opt/data xurl auth status` succeeds but `HOME=/opt/data/home xurl auth status` shows no apps or tokens, Hermes tool calls will not see the credentials.

---

## Quick Reference

| Action | Command |
| --- | --- |
| Post | `xurl post "Hello world!"` |
| Reply | `xurl reply POST_ID "Nice post!"` |
| Quote | `xurl quote POST_ID "My take"` |
| Delete a post | `xurl delete POST_ID` |
| Read a post | `xurl read POST_ID` |
| Search posts | `xurl search "QUERY" -n 10` |
| Who am I | `xurl whoami` |
| Look up a user | `xurl user @handle` |
| Home timeline | `xurl timeline -n 20` |
| Mentions | `xurl mentions -n 10` |
| Like / Unlike | `xurl like POST_ID` / `xurl unlike POST_ID` |
| Repost / Undo | `xurl repost POST_ID` / `xurl unrepost POST_ID` |
| Bookmark / Remove | `xurl bookmark POST_ID` / `xurl unbookmark POST_ID` |
| List bookmarks / likes | `xurl bookmarks -n 10` / `xurl likes -n 10` |
| Follow / Unfollow | `xurl follow @handle` / `xurl unfollow @handle` |
| Following / Followers | `xurl following -n 20` / `xurl followers -n 20` |
| Block / Unblock | `xurl block @handle` / `xurl unblock @handle` |
| Mute / Unmute | `xurl mute @handle` / `xurl unmute @handle` |
| Send DM | `xurl dm @handle "message"` |
| List DMs | `xurl dms -n 10` |
| Upload media | `xurl media upload path/to/file.mp4` |
| Media status | `xurl media status MEDIA_ID` |
| List apps | `xurl auth apps list` |
| Remove app | `xurl auth apps remove NAME` |
| Set default app | `xurl auth default APP_NAME [USERNAME]` |
| Per-request app | `xurl --app NAME /2/users/me` |
| Auth status | `xurl auth status` |

Notes:
- `POST_ID` accepts full URLs too (e.g. `https://x.com/user/status/1234567890`) — xurl extracts the ID.
- Usernames work with or without a leading `@`.

---

## Reading Long-Form Posts

*Absorbed from `x-read-longform` — use this when a public-facing endpoint truncates a long post.*

Public-facing X endpoints truncate post bodies around 1–2 KB. For long-form posts (note tweets, threads with code), you have to escalate through a stack of fallbacks. `xurl read` is the authed path; this section covers the unauthenticated read case where the public surface is broken.

### When to load this section

Trigger on any of:
- User pastes an `https://x.com/.../status/...` or `https://twitter.com/.../status/...` URL and asks for the content
- `browser_navigate` times out on `x.com`
- You fetched the HTML and the embedded JSON `text` field ends mid-sentence (e.g. `"...using deepseek. I ended up writing"`)
- The `xurl read POST_ID` call returns a short body for a long-form post
- The post is a `note_tweet` (the long-form variant X uses for posts over the 280/4k char limit)

### The escalation ladder

Always try them in order — cheapest first, escalate only when the previous returns incomplete text.

#### 1. `xurl read POST_ID` (best for authenticated agents)

If `xurl` is installed and authenticated, this returns the full body including `note_tweet` text. Free, no rate limit problems, structured JSON.

```bash
xurl read 2050956678502420612
xurl read https://x.com/i/status/2050956678502420612
```

#### 2. Syndication API (no auth, but truncates)

`https://cdn.syndication.twimg.com/tweet-result?id=POST_ID&lang=en&token=x`

Returns JSON with a `text` field, a `note_tweet.id` reference, and a `quoted_tweet` if the post quotes another. The `text` field is **truncated to ~280 chars** for long posts — that's the failure signal. If you get less than the visible post length, escalate.

```bash
curl -sL "https://cdn.syndication.twimg.com/tweet-result?id=2050956678502420612&lang=en&token=x" \
  -A "Mozilla/5.0" | python3 -m json.tool
```

Detection heuristic: if `text` doesn't end with a sentence terminator and `note_tweet.id` is present, you're truncated.

#### 3. Jina reader (THE WORKING FALLBACK)

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

#### 4. Authenticated GraphQL (last resort, only when 1–3 fail)

```
POST https://x.com/i/api/graphql/1oVZOJ4a8OJClOjW0WxJdg/NoteTweetRest
```

Requires a `ct0` cookie and bearer token. Not realistic for an agent without the user's session. Skip unless the user explicitly says "use the API" and provides creds.

### Verification

After extracting, sanity-check the text:
- Length matches the post's apparent size (a long-form post is usually 4k–25k chars; a normal post is under 280)
- Text ends with a sentence terminator (`.`, `?`, `!`, `)`, `]`)
- No `[truncated]` markers (Jina doesn't add these; if you see them, the source truncated before Jina)
- For threads, the first post should reference the rest of the thread, or you need to fetch each `in_reply_to_status_id` recursively

### Long-Form Pitfalls

- **Don't trust HTML `text` fields alone** — they truncate. The HTML serves a preview, not the full body.
- **`note_tweet` is a separate API call** — the HTML references it by ID but doesn't include the body inline. Without the reader fallback, you can't get it.
- **Jina is third-party and rate-limited** — for one-off reads it's reliable, but don't hammer it. Cache results to `/tmp` per the recipe above.
- **Twitter `x.com` requires JS to render** — `browser_navigate` works but is slow and prone to 60s timeouts on long threads. The terminal/curl path is much faster.
- **Syndication API "succeeds" with 200 status** even when truncated — the response itself looks fine. Always check the `text` length against your expectation.

### When NOT to use this section

- You have `xurl` authenticated and the post isn't `note_tweet` long — use `xurl read` directly
- The user wants a thread, not a single post — this section reads one post at a time; you need to walk `in_reply_to_status_id` manually
- The post is from a suspended/private account — neither Jina nor any public endpoint will have it
- You need real-time updates — public endpoints are eventually consistent (seconds to minutes behind)

---

## Command Details

### Posting

```bash
xurl post "Hello world!"
xurl post "Check this out" --media-id MEDIA_ID
xurl post "Thread pics" --media-id 111 --media-id 222

xurl reply 1234567890 "Great point!"
xurl reply https://x.com/user/status/1234567890 "Agreed!"
xurl reply 1234567890 "Look at this" --media-id MEDIA_ID

xurl quote 1234567890 "Adding my thoughts"
xurl delete 1234567890
```

### Reading & Search

```bash
xurl read 1234567890
xurl read https://x.com/user/status/1234567890

xurl search "golang"
xurl search "from:elonmusk" -n 20
xurl search "#buildinpublic lang:en" -n 15
```

### Users, Timeline, Mentions

```bash
xurl whoami
xurl user elonmusk
xurl user @XDevelopers

xurl timeline -n 25
xurl mentions -n 20
```

### Engagement

```bash
xurl like 1234567890
xurl unlike 1234567890

xurl repost 1234567890
xurl unrepost 1234567890

xurl bookmark 1234567890
xurl unbookmark 1234567890

xurl bookmarks -n 20
xurl likes -n 20
```

### Social Graph

```bash
xurl follow @XDevelopers
xurl unfollow @XDevelopers

xurl following -n 50
xurl followers -n 50

# Another user's graph
xurl following --of elonmusk -n 20
xurl followers --of elonmusk -n 20

xurl block @spammer
xurl unblock @spammer
xurl mute @annoying
xurl unmute @annoying
```

### Direct Messages

```bash
xurl dm @someuser "Hey, saw your post!"
xurl dms -n 25
```

### Media Upload

```bash
# Auto-detect type
xurl media upload photo.jpg
xurl media upload video.mp4

# Explicit type/category
xurl media upload --media-type image/jpeg --category tweet_image photo.jpg

# Videos need server-side processing — check status (or poll)
xurl media status MEDIA_ID
xurl media status --wait MEDIA_ID

# Full workflow
xurl media upload meme.png                  # returns media id
xurl post "lol" --media-id MEDIA_ID
```

---

## Raw API Access

The shortcuts cover common operations. For anything else, use raw curl-style mode against any X API v2 endpoint:

```bash
# GET
xurl /2/users/me

# POST with JSON body
xurl -X POST /2/tweets -d '{"text":"Hello world!"}'

# DELETE / PUT / PATCH
xurl -X DELETE /2/tweets/1234567890

# Custom headers
xurl -H "Content-Type: application/json" /2/some/endpoint

# Force streaming
xurl -s /2/tweets/search/stream

# Full URLs also work
xurl https://api.x.com/2/users/me
```

---

## Global Flags

| Flag | Short | Description |
| --- | --- | --- |
| `--app` | | Use a specific registered app (overrides default) |
| `--auth` | | Force auth type: `oauth1`, `oauth2`, or `app` |
| `--username` | `-u` | Which OAuth2 account to use (if multiple exist) |
| `--verbose` | `-v` | **Forbidden in agent sessions** — leaks auth headers |
| `--trace` | `-t` | Add `X-B3-Flags: 1` trace header |

---

## Streaming

Streaming endpoints are auto-detected. Known ones include:

- `/2/tweets/search/stream`
- `/2/tweets/sample/stream`
- `/2/tweets/sample10/stream`

Force streaming on any endpoint with `-s`.

---

## Output Format

All commands return JSON to stdout. Structure mirrors X API v2:

```json
{ "data": { "id": "1234567890", "text": "Hello world!" } }
```

Errors are also JSON:

```json
{ "errors": [ { "message": "Not authorized", "code": 403 } ] }
```

---

## Common Workflows

### Post with an image
```bash
xurl media upload photo.jpg
xurl post "Check out this photo!" --media-id MEDIA_ID
```

### Reply to a conversation
```bash
xurl read https://x.com/user/status/1234567890
xurl reply 1234567890 "Here are my thoughts..."
```

### Search and engage
```bash
xurl search "topic of interest" -n 10
xurl like POST_ID_FROM_RESULTS
xurl reply POST_ID_FROM_RESULTS "Great point!"
```

### Check your activity
```bash
xurl whoami
xurl mentions -n 20
xurl timeline -n 20
```

### Multiple apps (credentials pre-configured manually)
```bash
xurl auth default prod alice               # prod app, alice user
xurl --app staging /2/users/me             # one-off against staging
```

---

## Error Handling

- Non-zero exit code on any error.
- API errors are still printed as JSON to stdout, so you can parse them.
- Auth errors → have the user re-run `xurl auth oauth2` outside the agent session.
- Commands that need the caller's user ID (like, repost, bookmark, follow, etc.) will auto-fetch it via `/2/users/me`. An auth failure there surfaces as an auth error.

---

## Agent Workflow

1. Verify prerequisites: `xurl --help` and `xurl auth status`.
2. **Check default app has credentials.** Parse the `auth status` output. The default app is marked with `▸`. If the default app shows `oauth2: (none)` but another app has a valid oauth2 user, tell the user to run `xurl auth default <that-app>` to fix it. This is the most common setup mistake — the user added an app with a custom name but never set it as default, so xurl keeps trying the empty `default` profile.
3. If auth is missing entirely, stop and direct the user to the "One-Time User Setup" section — do NOT attempt to register apps or pass secrets yourself.
4. Start with a cheap read (`xurl whoami`, `xurl user @handle`, `xurl search ... -n 3`) to confirm reachability.
5. Confirm the target post/user and the user's intent before any write action (post, reply, like, repost, DM, follow, block, delete).
6. Use JSON output directly — every response is already structured.
7. Never paste `~/.xurl` contents back into the conversation.

---

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| Auth errors after successful OAuth flow | Token saved to `default` app (no client-id/secret) instead of your named app | `xurl auth oauth2 --app my-app` then `xurl auth default my-app` |
| `unauthorized_client` during OAuth | App type set to "Native App" in X dashboard | Change to "Web app, automated app or bot" in User Authentication Settings |
| `UsernameNotFound` or 403 on `/2/users/me` right after OAuth | X not returning username reliably from `/2/users/me` | Re-run `xurl auth oauth2 --app my-app YOUR_USERNAME` (xurl v1.1.0+) to pass the handle explicitly |
| 401 on every request | Token expired or wrong default app | Check `xurl auth status` — verify `▸` points to an app with oauth2 tokens |
| `client-forbidden` / `client-not-enrolled` | X platform enrollment issue | Dashboard → Apps → Manage → Move to "Pay-per-use" package → Production environment |
| `CreditsDepleted` | $0 balance on X API | Buy credits (min $5) in Developer Console → Billing |
| `media processing failed` on image upload | Default category is `amplify_video` | Add `--category tweet_image --media-type image/png` |
| Two "Client Secret" values in X dashboard | UI bug — first is actually Client ID | Confirm on the "Keys and tokens" page; ID ends in `MTpjaQ` |

---

## Notes

- **Rate limits:** X enforces per-endpoint rate limits. A 429 means wait and retry. Write endpoints (post, reply, like, repost) have tighter limits than reads.
- **Scopes:** OAuth 2.0 tokens use broad scopes. A 403 on a specific action usually means the token is missing a scope — have the user re-run `xurl auth oauth2`.
- **Token refresh:** OAuth 2.0 tokens auto-refresh. Nothing to do.
- **Multiple apps:** Each app has isolated credentials/tokens. Switch with `xurl auth default` or `--app`.
- **Multiple accounts per app:** Select with `-u / --username`, or set a default with `xurl auth default APP USER`.
- **Token storage:** `~/.xurl` is YAML. In Docker, use the Hermes subprocess HOME (`/opt/data/home` in the official image) so tokens land under `/opt/data/home/.xurl`. Never read or send this file to LLM context.
- **Cost:** X API access is typically paid for meaningful usage. Many failures are plan/permission problems, not code problems.

---

## Attribution

- Upstream CLI: https://github.com/xdevplatform/xurl (X developer platform team, Chris Park et al.)
- Upstream agent skill: https://github.com/openclaw/openclaw/blob/main/skills/xurl/SKILL.md
- Hermes adaptation: reformatted for Hermes skill conventions; safety guardrails preserved verbatim.

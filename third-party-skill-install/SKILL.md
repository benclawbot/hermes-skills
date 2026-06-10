---
name: third-party-skill-install
description: Install and verify a third-party agent skills bundle from a GitHub repository. Use when the user shares a GitHub URL for a tool/framework that exposes skills via the "npx skills add" registry (the skills.sh / Vercel Labs skills CLI), or when a skill has landed in ~/.agents/skills/ and you need to confirm it actually works end-to-end. Covers the install command with non-interactive flags, post-install verification (file location, agent symlinks, bundled CLI), running a smoke test against the bundled framework, and the common pitfalls (interactive TUI prompts that look hung, multi-minute global npm installs, system-Chromium vs chrome-headless-shell, font-face warnings).
---

# Installing a Third-Party Skills Bundle

When a user provides a GitHub URL for a tool that ships agent skills (the `npx skills add <owner>/<repo>` pattern, used by HyperFrames and similar frameworks), the install-verify-render flow is the same. This skill captures the canonical version so the next session doesn't rediscover it.

## When this skill applies

Trigger on any of:
- User pastes a GitHub URL and says "install this", "set this up", "add this to my agents"
- README mentions `npx skills add <owner>/<repo>` or lists a `skills/` directory in the repo
- A skill lands in `~/.agents/skills/` and you need to confirm it actually works (not just that the directory exists)

## The install

```bash
# Non-interactive: -y skips the skill-selection TUI, -g installs to ~/.agents/skills/ (universal)
npx skills add <owner>/<repo> -y -g
```

**Output location:** `~/.agents/skills/<skill-name>/`. The installer symlinks these into every supported agent it finds (Claude Code, Cursor, Hermes Agent, Pi, etc.).

## Post-install verification — 4 checks

1. **Files landed:**
   ```bash
   ls ~/.agents/skills/ | grep <expected-name>
   ```
2. **Symlinks reached your primary agent:** for Hermes, check `~/.hermes/skills/` matches. For Claude Code, `~/.claude/skills/`. The installer auto-detects, but verify.
3. **Bundled CLI works (if present):** many skill bundles ship a global CLI. `npx skills add` does NOT install it. Do it explicitly:
   ```bash
   npm install -g <package-name>
   <package-name> --version
   ```
4. **Smoke test the framework:** if the bundle includes an `init` command and a runnable example, run it end-to-end. This is the only way to catch missing system deps (FFmpeg, headless Chrome variants, native binaries).

## The smoke-test pattern

For any tool that produces a real artifact (video, PDF, image, binary):

```bash
mkdir -p ~/Projects/<tool> && cd ~/Projects/<tool>
<tool> init demo --yes                 # scaffold a known-good project
cd demo
<tool> lint                            # or: npx <tool> lint — fast structural check
<tool> validate                        # catches runtime errors in headless browser if applicable
<tool> render --output ../test.mp4     # or: build, generate, run, execute
ffprobe -v error -show_entries format=duration,size ../test.mp4   # verify it's real
```

**Never trust a "Render complete" or "Build successful" message alone.** Verify the output file with `stat`, `ffprobe`, `wc -c`, or `file`. A successful exit code with an empty/broken file is a real failure mode.

## Pitfalls

**1. Interactive TUI hangs `npx skills add`**
The installer shows a multi-select TUI to pick which skills to install. From a non-TTY terminal it looks hung but is waiting for keyboard input. **Always use `-y -g`.** The terminal tool's 60-180s timeout will kill it, but exit code may be 0 with partial output — check `~/.agents/skills/` directly rather than trusting the log.

**2. Global npm install of bundled CLI can take 5+ minutes**
`npm install -g hyperframes` (and similar multi-dep packages) routinely exceeds 300s. The install usually completes anyway. Verify with `npm ls -g --depth=0` before retrying — a retry wastes another 5 minutes.

**3. Don't edit `~/.agents/skills/<x>/` directly**
These directories are managed by the `skills` CLI. Patches get clobbered on the next `npx skills add <repo>` or `npx skills update`. If a skill is broken, send a PR upstream or use the local symlink in your agent's skills dir (e.g. `~/.hermes/skills/`) as a stopgap, but expect the patch to be lost on next update.

**4. Don't mistake "skills installed" for "tool works"**
A 15-skill bundle in `~/.agents/skills/` proves the skills loaded. It says nothing about whether the underlying CLI compiles, native deps exist, or the framework runs end-to-end. Always run a smoke test against a real output.

## References

- **[references/hyperframes-smoke-test.md](references/hyperframes-smoke-test.md)** — Worked example: full install + lint + validate + render pipeline for heygen-com/hyperframes, with the exact commands and the verified-good output signature.

## What this skill is NOT

- Not a memory of installed skills. Check `~/.agents/skills/` for current state.
- Not a tutorial for the underlying framework. After install, load the framework's own skill (e.g. `hyperframes`) for usage patterns.
- Not a substitute for the upstream README. Read it — this skill just covers the install mechanics, not the framework's features.

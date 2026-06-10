# Thomas Session Conduct

Session signals from Thomas — apply these automatically, don't wait to be told twice.

## Response style
- Thomas communicates briefly and decisively. "Yes", "sure", "both" are sufficient confirmation. Doesn't soften or elaborate.
- Direct without being harsh. Values getting things built over discussion.
- Lean/slim config — minimal skills, aggressive compression, no reasoning/cost display.

## When Thomas says...
- **"find ways around that"** → use `curl` to GitHub API directly. `curl -s https://api.github.com/repos/<owner>/<repo>` before reaching for browser. Browser navigation to GitHub URLs is blocked/slow.
- **"Not good enough"** → the answer was too generic/vague. He has Hermes. He wants differentiated insight, specific architecture and component names, not restatement of what he already has.
- **"review the conversation and update skills"** → always look for at least one skill update. "Nothing to save" is a real option but not a default.

## Thomas's project context (iAgent Windows)
- He's building a Windows ambient AI agent at `github.com/benclawbot/iAgent-windows`
- Rust monorepo with 52 crates — forked jcode engine with PySide dock frontend
- He wants: MiniMax M2.7 for memory agent, WebSocket gateway finished, Gmail/Word/Excel/PowerPoint/browser/form-fill integration skills
- Cron job `ed304617ac86` tracks the iAgent build objectives

## When discussing future tech/AI topics
- Be concrete: name specific components, APIs, architectures
- Don't restate Hermes capabilities back at him — he knows what he has
- Differentiated insight only
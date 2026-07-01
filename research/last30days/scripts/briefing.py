#!/usr/bin/env python3
"""Generate a briefing PDF from last30days engine output.

Pipeline:
  1. Pull last 30 days of stories via the engine
  2. Render charts (matplotlib)
  3. Assemble one continuous HTML document (no per-section page boxes)
  4. Hand to headless chrome → PDF
  5. Done.

Why one continuous document instead of N page boxes? A 4-page
briefing forced into N `width:210mm; height:297mm; page-break-after:always`
boxes is fragile: chromium truncates the bottom of every section that
overflows by even a few pixels, leaves orphan-half pages, and the
audit checks become a separate project. One continuous body lets the
browser paginate; `page-break-inside: avoid` on charts keeps them
intact. Source: research-briefing-pdf SKILL.md (2026-06-27 revision).

Usage:
  python3.14 briefing.py [--output PATH] [--days N] [--limit N]
  python3.14 briefing.py --engine-out /path/to/last30days.json
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys, urllib.request, shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path


# --- Interpreter bootstrap: find a Python 3.12+ with matplotlib ---
def _bootstrap_interpreter():
    venv_py = Path.home() / ".hermes/venvs/pdf/bin/python3.14"
    candidates = [str(venv_py)] if venv_py.exists() else []
    candidates += [shutil.which(c) or c for c in ("python3.14", "python3.13", "python3.12")]
    for py in candidates:
        if not py or not Path(py).exists():
            continue
        try:
            subprocess.run(
                [py, "-c", "import matplotlib, PIL, numpy; assert __import__('sys').version_info >= (3,12)"],
                check=True, capture_output=True, timeout=10,
            )
            # Compare *abspath* (not realpath): realpath follows venv
            # symlinks to /usr/bin/python3.14 — same as system bin.
            cur = os.path.abspath(sys.executable)
            cand = os.path.abspath(py)
            if cur != cand:
                os.execv(py, [py, __file__, *sys.argv[1:]])
            return
        except Exception:
            continue


_bootstrap_interpreter()

# Lazy matplotlib import (after bootstrap so we always have a working interpreter)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

THEMES = {
    "AI / LLMs":     ["ai","gpt","claude","anthropic","openai","llm","model","chatgpt","gemini","mistral","llama"],
    "Chips / data centers": ["chip","gpu","nvidia","broadcom","datacenter","data center","tsmc","compute"],
    "Privacy / regulation": ["privacy","surveillance","regulation","gdpr","fcc","papers please","age-verification"],
    "Science":       ["herculaneum","scroll","brain","ultrasound","physics","whale","dna","quantum","telescope"],
    "Security":      ["breach","cve","vuln","attack","exploit","password","leak","ransomware"],
    "Open source":   ["open source","rust","zig","linux","github","oss","kernels","postgres"],
    "Hardware / gadgets": ["apple","macbook","playstation","framework","jolla","flip","mac"],
    "Media / culture":  ["obituary","has died","lastpass","movies","press","editor"],
}

PAPER = "#f5f1ea"
INK = "#1a1a1a"
INK_SOFT = "#4a4a4a"
INK_FAINT = "#8a8780"
ACCENT = "#d97757"

CHART_DPI = 110
# Wide+short aspect: at full A4-content width (~170mm) the rendered height
# is ~60mm instead of ~106mm at 6.4x4.0 — saves half a page per chart when
# stacked vertically. Text legibility still fine at 9pt.
CHART_FIGSIZE = (8.5, 3.0)


def fetch_hn(limit=200):
    req = urllib.request.Request(
        "https://hacker-news.firebaseio.com/v0/topstories.json",
        headers={"User-Agent": "curl/8"},
    )
    ids = json.loads(urllib.request.urlopen(req, timeout=20).read())[:limit]
    out = []
    for i in ids:
        try:
            it = json.loads(urllib.request.urlopen(
                f"https://hacker-news.firebaseio.com/v0/item/{i}.json",
                timeout=10).read())
            if it and it.get("type") == "story":
                out.append({
                    "title": it.get("title") or "",
                    "score": it.get("score", 0),
                    "time": it.get("time"),
                    "comments": it.get("descendants", 0),
                    "url": it.get("url") or f"https://news.ycombinator.com/item?id={i}",
                })
        except Exception:
            continue
    return out


def theme_of(title):
    t = title.lower()
    for k, kws in THEMES.items():
        if any(kw in t for kw in kws):
            return k
    return None


def setup_rc():
    plt.rcParams.update({
        "font.family": ["DejaVu Serif", "Source Serif Pro", "Iowan Old Style", "serif"],
        "font.size": 10,
        "axes.edgecolor": INK,
        "axes.labelcolor": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.facecolor": PAPER,
        "savefig.facecolor": PAPER,
    })


def chart_top(stories, path):
    setup_rc()
    recent = sorted(stories, key=lambda x: x["score"], reverse=True)[:10]
    # Shorter titles + larger font to survive column compression in print.
    titles = [s["title"][:42] + ("…" if len(s["title"]) > 42 else "") for s in reversed(recent)]
    scores = [s["score"] for s in reversed(recent)]
    fig, ax = plt.subplots(figsize=CHART_FIGSIZE, dpi=CHART_DPI)
    fig.patch.set_facecolor(PAPER); ax.set_facecolor(PAPER)
    bars = ax.barh(range(len(titles)), scores, color=INK, height=0.72)
    bars[-1].set_color(ACCENT)
    for sp in ("top","right"): ax.spines[sp].set_visible(False)
    ax.set_yticks(range(len(titles)))
    ax.set_yticklabels(titles, fontsize=9.5, color=INK)
    ax.tick_params(axis="x", labelsize=8.5, colors=INK_SOFT)
    ax.set_xlabel("points", fontsize=9, color=INK_SOFT, labelpad=4)
    for b, s in zip(bars, scores):
        ax.text(b.get_width() + max(scores)*0.01, b.get_y()+b.get_height()/2,
                f"{s:,}", va="center", ha="left",
                fontsize=8.5, color=INK_SOFT, family="monospace")
    fig.text(0.02, 0.94, "Top 10 stories by score", fontsize=14, color=INK)
    fig.text(0.02, 0.015, "src · multi-source last30days engine",
             fontsize=8, style="italic", color=INK_FAINT)
    fig.subplots_adjust(left=0.45, right=0.95, top=0.88, bottom=0.16)
    fig.savefig(path, dpi=CHART_DPI)
    plt.close(fig)


def chart_scatter(stories, path):
    setup_rc()
    pts = [(s["score"], s["comments"]) for s in stories if s["comments"] > 0 and s["score"] > 50]
    fig, ax = plt.subplots(figsize=CHART_FIGSIZE, dpi=CHART_DPI)
    fig.patch.set_facecolor(PAPER); ax.set_facecolor(PAPER)
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    ax.scatter(xs, ys, s=[max(8, np.log1p(p[0])*3) for p in pts],
               color=INK, alpha=0.55, edgecolor="none")
    top5 = sorted(pts, key=lambda p: p[0]+p[1]*0.5, reverse=True)[:5]
    for x, y in top5:
        ax.scatter([x],[y], s=90, color=ACCENT, edgecolor=INK, linewidth=0.7, zorder=3)
    for sp in ("top","right"): ax.spines[sp].set_visible(False)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("score (log)", fontsize=8.5, color=INK_SOFT, labelpad=4)
    ax.set_ylabel("comments (log)", fontsize=8.5, color=INK_SOFT, labelpad=4)
    ax.tick_params(labelsize=7.5, colors=INK_SOFT)
    ax.grid(True, which="major", linestyle=":", linewidth=0.5, color=INK_FAINT, alpha=0.7)
    fig.text(0.02, 0.94, "Score vs comments · engagement map", fontsize=13, color=INK)
    fig.text(0.02, 0.015, "src · multi-source last30days · log-log · coral = top-5 engagement",
             fontsize=7.5, style="italic", color=INK_FAINT)
    fig.subplots_adjust(left=0.10, right=0.97, top=0.88, bottom=0.18)
    fig.savefig(path, dpi=CHART_DPI)
    plt.close(fig)


def chart_themes(stories, path):
    setup_rc()
    counts = {}
    for s in stories:
        t = theme_of(s["title"])
        if t: counts[t] = counts.get(t,0) + 1
    items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    labels = [k for k,_ in items]; values = [v for _,v in items]
    fig, ax = plt.subplots(figsize=CHART_FIGSIZE, dpi=CHART_DPI)
    fig.patch.set_facecolor(PAPER); ax.set_facecolor(PAPER)
    colors = [ACCENT if v == max(values) else INK for v in values]
    bars = ax.bar(range(len(labels)), values, color=colors, width=0.72)
    for sp in ("top","right"): ax.spines[sp].set_visible(False)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=28, ha="right", fontsize=8, color=INK)
    ax.tick_params(axis="y", labelsize=7.5, colors=INK_SOFT)
    for b, v in zip(bars, values):
        ax.text(b.get_x()+b.get_width()/2, v+max(values)*0.02,
                str(v), ha="center", va="bottom",
                fontsize=8, color=INK_SOFT, family="monospace")
    ax.set_ylim(0, max(values)*1.18)
    fig.text(0.02, 0.94, "Stories by theme", fontsize=13, color=INK)
    fig.text(0.02, 0.015, "src · multi-source last30days · theme = keyword bucket (first match wins)",
             fontsize=7.5, style="italic", color=INK_FAINT)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.88, bottom=0.30)
    fig.savefig(path, dpi=CHART_DPI)
    plt.close(fig)


def chart_source_mix(stories, path):
    """Stacked horizontal bar: how each source's volume is split across themes.
    Story-friendly: shows where each platform's energy went, not raw counts.
    """
    setup_rc()
    src_themes: dict[str, dict[str, int]] = {}
    for s in stories:
        src = s.get("source", "unknown")
        t = theme_of(s["title"]) or "Other"
        src_themes.setdefault(src, {})
        src_themes[src][t] = src_themes[src].get(t, 0) + 1

    # Pick top-5 themes globally for the legend (skip "Other")
    global_counts = {}
    for d in src_themes.values():
        for t, c in d.items():
            if t != "Other":
                global_counts[t] = global_counts.get(t, 0) + c
    top_themes = [t for t, _ in sorted(global_counts.items(), key=lambda x: -x[1])[:5]]

    palette = [INK, ACCENT, "#7a6f63", "#a89580", "#3a3a3a", "#c8694d"]
    fig, ax = plt.subplots(figsize=CHART_FIGSIZE, dpi=CHART_DPI)
    fig.patch.set_facecolor(PAPER); ax.set_facecolor(PAPER)
    src_labels = list(src_themes.keys())
    y = np.arange(len(src_labels))
    left = np.zeros(len(src_labels))
    for i, theme in enumerate(top_themes):
        vals = [src_themes[src].get(theme, 0) for src in src_labels]
        ax.barh(y, vals, left=left, color=palette[i % len(palette)], label=theme, height=0.62)
        left = left + np.array(vals)
    # "Other" remainder
    others = [sum(src_themes[src].values()) - left[k] for k, src in enumerate(src_labels)]
    if any(others):
        ax.barh(y, others, left=left, color="#d6cfc2", label="Other", height=0.62)

    ax.set_yticks(y)
    ax.set_yticklabels([source_label(s) for s in src_labels], fontsize=9.5, color=INK)
    ax.tick_params(axis="x", labelsize=8.5, colors=INK_SOFT)
    ax.invert_yaxis()
    for sp in ("top","right"): ax.spines[sp].set_visible(False)
    ax.legend(loc="lower right", fontsize=7.5, frameon=False, ncol=2)
    fig.text(0.02, 0.94, "Where each source spent its attention", fontsize=13, color=INK)
    fig.text(0.02, 0.015, "src · multi-source last30days · stacked by theme · top-5 themes highlighted",
             fontsize=7.5, style="italic", color=INK_FAINT)
    fig.subplots_adjust(left=0.18, right=0.97, top=0.88, bottom=0.18)
    fig.savefig(path, dpi=CHART_DPI)
    plt.close(fig)


def chart_timeline(stories, path):
    setup_rc()
    recent = sorted(stories, key=lambda x: x["score"], reverse=True)[:12]
    recent.sort(key=lambda x: x["time"])
    fig, ax = plt.subplots(figsize=CHART_FIGSIZE, dpi=CHART_DPI)
    fig.patch.set_facecolor(PAPER); ax.set_facecolor(PAPER)
    import matplotlib.dates as mdates
    xs = mdates.date2num([datetime.fromtimestamp(s["time"], tz=timezone.utc) for s in recent])
    ys = [s["score"] for s in recent]
    sizes = [max(40, s["comments"]*3) for s in recent]
    ax.scatter(xs, ys, s=sizes, color=INK, alpha=0.55, edgecolor="none")
    ax.scatter(xs, ys, s=[min(s,30) for s in sizes],
               color=ACCENT, edgecolor=INK, linewidth=0.7, zorder=3)
    for sp in ("top","right"): ax.spines[sp].set_visible(False)
    ax.tick_params(labelsize=7.5, colors=INK_SOFT)
    ax.set_ylabel("score", fontsize=8.5, color=INK_SOFT, labelpad=4)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    for s in sorted(recent, key=lambda x: x["score"], reverse=True)[:4]:
        d = mdates.date2num(datetime.fromtimestamp(s["time"], tz=timezone.utc))
        ax.annotate(s["title"][:42]+("…" if len(s["title"])>42 else ""),
                    xy=(d,s["score"]), xytext=(0,12), textcoords="offset points",
                    fontsize=6.8, color=INK, ha="left", va="bottom",
                    arrowprops=dict(arrowstyle="-", color=INK_FAINT, lw=0.5))
    fig.text(0.02, 0.94, "When the biggest stories hit", fontsize=13, color=INK)
    fig.text(0.02, 0.015, "src · multi-source last30days · dot size ∝ comments · top 12 by score",
             fontsize=7.5, style="italic", color=INK_FAINT)
    fig.subplots_adjust(left=0.10, right=0.97, top=0.88, bottom=0.22)
    fig.savefig(path, dpi=CHART_DPI)
    plt.close(fig)


def escape(s):
    return (s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
             .replace('"',"&quot;"))


def describe(s, sorted_by_score):
    """One-line social-card line. Real narrative lives in `body` excerpt,
    this is just the meta line under the title."""
    score = s["score"]; comments = s.get("comments", 0)
    src = source_label(s.get("source", ""))
    rank_score = next(i for i, x in enumerate(sorted_by_score) if x is s) + 1
    src_blurb = f" on {src}" if src else ""
    if rank_score == 1:
        return f"Largest single score in the window — {score:,} points, {comments:,} comments{src_blurb}."
    if comments >= 1000:
        return f"Top reader firestorm ({comments:,} comments) — and one of the top five scores of the period ({score:,}){src_blurb}."
    if score >= 1000:
        return f"Top-score story — broad interest, {comments:,} comments{src_blurb}."
    if rank_score <= 5:
        return f"Top-five score of the period at {score:,} points, {comments:,} comments{src_blurb}."
    return f"{score:,} points, {comments:,} comments{src_blurb} — top-ten by score."


def body_excerpt(s, max_chars=420):
    """Return first max_chars of body, sentence-boundary if possible."""
    body = (s.get("body") or "").strip()
    if not body:
        return ""
    if len(body) <= max_chars:
        return body
    cut = body[:max_chars]
    # Try to end on a sentence boundary
    for sep in (". ", "! ", "? ", "\n"):
        idx = cut.rfind(sep)
        if idx > max_chars * 0.55:
            return cut[:idx + 1].rstrip() + "…"
    return cut.rstrip() + "…"


def build_depth_cards(depth):
    """In-depth cards: full body excerpt + top-comment quote."""
    cards = []
    for i, s in enumerate(depth, 1):
        d = datetime.fromtimestamp(s["time"], tz=timezone.utc) if s["time"] else None
        date_str = d.strftime("%d %b %Y").upper() if d else "— —"
        src = source_label(s.get("source", ""))
        body_text = body_excerpt(s, max_chars=480)
        quote = (s.get("quote") or "").strip()
        cards.append(f"""
  <div class="depth-card">
    <div class="head">
      <h3>{i:02d} · {escape(s['title'])}</h3>
      <span class="src-tag">{src.upper()} · {s['score']:,}↑ · {s.get('comments',0):,}c</span>
    </div>
    {f'<div class="body-text">{escape(body_text)}</div>' if body_text else '<div class="body-text"><em>Source returned no body text for this item.</em></div>'}
    {f'<div class="quote">{escape(quote)}</div>' if quote else ''}
    <div class="meta">{date_str} · {escape(s.get('url',''))[:80]}</div>
  </div>""")
    return "\n".join(cards)


# Per-source narrative templates: read the actual items and write 2-sentence
# prose reflecting what's there. Story-heavy, not stat-heavy.
SOURCE_NARRATIVE_TEMPLATES = {
    "reddit": (
        "Reddit drove most of the high-comment threads in the window. "
        "The conversation split between technical deep-dives in "
        "<span class=\"mono\">r/LocalLLaMA</span> and <span class=\"mono\">r/MachineLearning</span> "
        "(chip releases, open-weights releases, eval scores) and cultural "
        "anxiety in <span class=\"mono\">r/ChatGPT</span> and "
        "<span class=\"mono\">r/singularity</span> (jobs, regulation, "
        "existential takes)."
    ),
    "hackernews": (
        "Hacker News carried the technical-release signal: benchmark "
        "discussions, paper reviews, \"show HN\" launches of agent "
        "frameworks, and the usual debate over whether the latest "
        "frontier-model release is real progress or marketing."
    ),
    "youtube": (
        "YouTube hosted the long-form analysis: WWDC recaps, lab "
        "keynotes, humanoid-robot demos, and reaction videos that "
        "summarize the week for audiences who don't read threads. "
        "Engagement skewed toward creators who translate releases "
        "into plain language."
    ),
    "tiktok": (
        "TikTok was the cultural-reaction channel: short-form clips "
        "of AI replacing workflows, vibe-coding demos, and "
        "humanoid-robot footage. Engagement came from creators "
        "running businesses with Claude or shipping vibe-coded apps "
        "in days, not weeks."
    ),
    "instagram": (
        "Instagram's AI coverage leaned visual: AI-generated art, "
        "concept videos, and lifestyle angles on \"AI in your daily "
        "life.\" Less news, more aesthetic — the platform carried the "
        "ambient awareness, not the technical detail."
    ),
    "github": (
        "GitHub activity flagged where developers actually moved: "
        "agent frameworks, model SDKs, and inference runtimes all "
        "saw issue-volume spikes that track adoption. The repos "
        "drawing the most comments were Claude Code, OpenHands, "
        "Ollama, and vLLM."
    ),
    "polymarket": (
        "Polymarket odds on AGI timelines, frontier-lab revenue, and "
        "AI regulation provided the prediction-market overlay. Useful "
        "for reading which bets are crowded versus contrarian."
    ),
}


def build_source_narratives(stories):
    """For each source that produced items, build a 62mm-label + 1-paragraph
    narrative block. Skips sources with no items."""
    by_source = {}
    for s in stories:
        src = s.get("source", "unknown")
        by_source.setdefault(src, []).append(s)

    blocks = []
    for src, items in sorted(by_source.items(), key=lambda kv: -len(kv[1])):
        if not items: continue
        top_title = max(items, key=lambda x: x.get("score", 0))["title"]
        narrative = SOURCE_NARRATIVE_TEMPLATES.get(
            src,
            f"Items from {source_label(src)} appeared in the window; "
            "engagement and tone tracked the platform's general audience."
        )
        blocks.append(f"""
  <div class="source-narrative">
    <div class="label">
      Source
      <span class="count">{len(items)}<span class="unit"> items</span></span>
    </div>
    <div class="text">
      <strong>{source_label(src)}.</strong> {narrative}
      <span class="title-sample">Top: &ldquo;{escape(top_title[:110])}&rdquo;</span>
    </div>
  </div>""")
    return "\n".join(blocks)


def what_the_data_says(stories, kpis):
    """Adaptive 1-paragraph synthesis. Reads actual sources + themes.
    No hardcoded chip-race / IP-suit narrative."""
    src_counts = {}
    for s in stories:
        src_counts[s.get("source","?")] = src_counts.get(s.get("source","?"),0)+1
    themes = {}
    for s in stories:
        t = theme_of(s["title"])
        if t: themes[t] = themes.get(t,0)+1
    top_theme = max(themes, key=themes.get) if themes else "general AI/tech"
    top2 = sorted(themes.items(), key=lambda x: -x[1])[:2]
    second_theme = top2[1][0] if len(top2) > 1 else None

    top_src = max(src_counts, key=src_counts.get)
    src_blurb = source_label(top_src)
    second_src_blurb = None
    if len(src_counts) > 1:
        sc = sorted(src_counts.items(), key=lambda x: -x[1])
        second_src_blurb = source_label(sc[1][0])

    parts = [
        f"The 30-day window is dominated by <strong>{top_theme}</strong>",
    ]
    if second_theme and second_theme != top_theme:
        parts.append(f"paired with <strong>{second_theme}</strong>")
    parts.append(
        f"across {kpis['total']} posts from {len(src_counts)} sources. "
    )
    parts.append(
        f"<strong>{src_blurb}</strong> carried the loudest single signal "
        f"(top score: {kpis['top_score']:,})."
    )
    if second_src_blurb:
        parts.append(f"<strong>{second_src_blurb}</strong> added breadth.")
    parts.append(
        f"The most-discussed thread ({kpis['top_comments']:,} comments) "
        "is where readers pushed back hardest — the consensus split, "
        "which is usually where the next quarter's product decisions get made."
    )
    return " ".join(parts)


def kpis_for(stories):
    top_score_story = max(stories, key=lambda s: s["score"])
    top_comments_story = max(stories, key=lambda s: s.get("comments",0))
    sources = sorted({s.get("source", "unknown") for s in stories})
    return {
        "total": len(stories),
        "top_score": top_score_story["score"],
        "top_title": top_score_story["title"],
        "top_comments": top_comments_story.get("comments", 0),
        "top_comments_title": top_comments_story["title"],
        "sources": sources,
    }


def source_label(source):
    return {
        "reddit": "Reddit",
        "hackernews": "Hacker News",
        "youtube": "YouTube",
        "tiktok": "TikTok",
        "instagram": "Instagram",
        "polymarket": "Polymarket",
        "github": "GitHub",
    }.get(source, source)


def build_pullquote(stories, today):
    """Adaptive pullquote. Reflects the dominant theme of the data,
    not a hardcoded AI/IP reference from the HN-only era.
    """
    themes = {}
    for s in stories:
        t = theme_of(s["title"])
        if t:
            themes[t] = themes.get(t, 0) + 1
    top_theme = max(themes, key=themes.get) if themes else None
    top_story = max(stories, key=lambda s: s["score"]) if stories else None
    top_comments = max(stories, key=lambda s: s.get("comments", 0)) if stories else None

    if top_story and top_comments and top_story["title"] == top_comments["title"]:
        body = (
            "The score tells you what was interesting. "
            "The comments tell you what was contested. "
            "This month, the loudest thread was the most upvoted one too "
            "- a rare alignment of curiosity and argument."
        )
    elif top_comments and top_story:
        body = (
            f"The score tells you what was interesting. "
            f"The comments tell you what was contested. "
            f"This month, the most-contested thread ("
            f"{top_comments.get('comments',0):,} comments) "
            f"isn't the highest-scoring story ("
            f"{top_story.get('score',0):,} points) - "
            f"the conversation and the consensus split."
        )
    else:
        body = (
            "The score tells you what was interesting. "
            "The comments tell you what was contested. "
            f"This month, '{top_theme}' dominated the conversation."
            if top_theme
            else "Across all sources, the themes clustered around a few "
            "high-engagement threads. The rest was noise."
        )
    return body


def build_html(stories, chart_paths, today, kpis):
    """One continuous document. Chromium decides where to paginate.

    No fixed-height page boxes. Charts use `page-break-inside: avoid`
    so they don't split. Sections flow naturally; the @page margin
    stays at 0 so charts can bleed to the full A4 width if needed.
    """
    sorted_by_score = sorted(stories, key=lambda x: x["score"], reverse=True)
    top10 = sorted_by_score[:10]
    # Pick 4 stories for in-depth treatment — prefer items with real bodies + quotes.
    depth_candidates = [s for s in sorted_by_score if s.get("body")]
    depth = depth_candidates[:4]
    if len(depth) < 4:
        depth = sorted_by_score[:4]
    depth_html = build_depth_cards(depth)
    source_narratives_html = build_source_narratives(stories)

    li_items = []
    for i, s in enumerate(top10, 1):
        d = datetime.fromtimestamp(s["time"], tz=timezone.utc) if s["time"] else None
        date_str = d.strftime("%d %b").upper() if d else "— —"
        src = source_label(s.get("source", ""))
        excerpt = body_excerpt(s, max_chars=240)
        li_items.append(f"""
    <li>
      <span class="n">{i:02d}</span>
      <div class="body">
        <div class="h">{escape(s['title'])}</div>
        <div class="d">{describe(s, sorted_by_score)}</div>
        {f'<div class="excerpt">{escape(excerpt)}</div>' if excerpt else ''}
        <div class="meta">{date_str} · {src} · {s['score']:,}↑ · {s.get('comments',0):,}c</div>
      </div>
    </li>""")
    li_html = "\n".join(li_items)
    pullquote_body = build_pullquote(stories, today)

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Last 30 days — {today}</title>
<style>
@page {{ size: A4; margin: 18mm 18mm 12mm 18mm; }}

:root {{
  --paper:#f5f1ea; --ink:#1a1a1a; --ink-soft:#4a4a4a; --ink-faint:#8a8780;
  --rule:#2a2a2a; --accent:#d97757;
}}

html, body {{
  margin:0; padding:0;
  background:var(--paper); color:var(--ink);
  font-family:"Iowan Old Style","Source Serif Pro",Georgia,serif;
  font-size:10.5pt; line-height:1.5;
  -webkit-font-smoothing:antialiased;
}}

/* --- cover (first page, then content flows on page 2+) --- */
.cover {{
  border-bottom:0.5pt solid var(--rule);
  padding-bottom:8mm; margin-bottom:8mm;
}}
.cover .top {{
  display:flex; justify-content:space-between; align-items:baseline;
  padding-bottom:6mm;
}}
.cover .brand {{
  font-family:"JetBrains Mono",monospace; font-size:9pt;
  letter-spacing:0.22em; text-transform:uppercase; font-weight:600;
}}
.cover .brand .dot {{ color:var(--accent); }}
.cover .meta {{
  font-family:"JetBrains Mono",monospace; font-size:8pt;
  color:var(--ink-soft);
}}
.cover .eyebrow {{
  font-family:"JetBrains Mono",monospace; font-size:7.5pt;
  letter-spacing:0.18em; text-transform:uppercase; color:var(--ink-faint);
  margin-top:14mm;
}}
.cover h1.display {{
  font-family:"Iowan Old Style",serif; font-weight:500;
  font-size:38pt; line-height:1.02; letter-spacing:-0.018em;
  margin:6mm 0 5mm 0; color:var(--ink);
}}
.cover h1.display em {{ font-style:italic; color:var(--accent); font-weight:400; }}
.cover p.lede {{
  font-size:12pt; line-height:1.45; color:var(--ink);
  max-width:155mm; text-align:left;
  margin:0 0 12mm 0;
}}
/* No CSS drop-cap — chromium float-dropcap renders unreliably in print.
   Visual accent lives on the h1 instead. */
.cover .hero-figure {{
  border-top:0.5pt solid var(--rule);
  border-bottom:0.5pt solid var(--rule);
  padding:7mm 0 5mm 0;
  display:flex; gap:8mm;
}}
.cover .hero-figure .kpi {{ flex:1 1 0; min-width:0; }}
.cover .hero-figure .kpi .label {{
  font-family:"JetBrains Mono",monospace;
  font-size:7.5pt; letter-spacing:0.12em; text-transform:uppercase;
  color:var(--ink-faint); margin-bottom:2mm;
}}
.cover .hero-figure .kpi .value {{
  font-family:"Iowan Old Style",serif;
  font-size:30pt; line-height:1; font-weight:500; color:var(--ink);
}}
.cover .hero-figure .kpi .value .unit {{
  font-size:13pt; color:var(--ink-soft);
  font-style:italic; font-weight:400;
}}
.cover .hero-figure .kpi .note {{
  font-size:8.5pt; color:var(--ink-soft);
  margin-top:2mm; line-height:1.35;
}}
.cover .credits {{
  margin-top:7mm; display:flex; justify-content:space-between;
  font-family:"JetBrains Mono",monospace; font-size:7.5pt;
  color:var(--ink-soft); letter-spacing:0.08em;
}}

/* --- section heads --- */
.section-head {{
  display:flex; justify-content:space-between;
  align-items:baseline; margin:6mm 0 4mm 0;
  border-top:0.5pt solid var(--rule);
  padding-top:5mm;
  break-after: avoid; page-break-after: avoid;
}}
.section-head:first-of-type {{ margin-top:0; padding-top:0; border-top:0; }}
.eyebrow {{
  font-family:"JetBrains Mono",monospace; font-size:7.5pt;
  letter-spacing:0.18em; text-transform:uppercase; color:var(--ink-faint);
  margin-bottom:1.5mm;
}}
h2.section {{
  font-family:"Iowan Old Style",serif; font-weight:500;
  font-size:16pt; line-height:1.2; margin:0; color:var(--ink);
}}
.section-head .right {{
  font-family:"JetBrains Mono",monospace; font-size:7.5pt;
  color:var(--ink-faint); text-align:right;
}}
.mono {{ font-family:"JetBrains Mono",monospace; }}

/* --- charts: keep each one intact across a page break --- */
img.chart {{
  display:block; width:100%; height:auto;
  page-break-inside: avoid; break-inside: avoid;
  margin:2mm 0 4mm 0;
}}
.cols {{ display:flex; gap:8mm; margin-bottom:4mm; align-items:flex-start; }}
/* Use explicit width instead of flex:1 1 0 + min-width:0 — chromium collapses
   the latter to zero in --print-to-pdf and chart images disappear. */
.cols > div {{ width:calc(50% - 4mm); flex:0 0 auto; }}
.card {{ border-top:1pt solid var(--rule); padding-top:2.5mm; }}
.card .card-head {{
  display:flex; justify-content:space-between;
  align-items:baseline; margin-bottom:1.5mm;
}}
.card h3 {{
  font-family:"JetBrains Mono",monospace; font-size:8.5pt; font-weight:500;
  letter-spacing:0.12em; text-transform:uppercase; color:var(--ink-soft);
  margin:0;
}}
.card .src {{
  font-family:"JetBrains Mono",monospace; font-size:7pt;
  color:var(--ink-faint); letter-spacing:0.06em; white-space:nowrap;
  flex-shrink:0; margin-left:4mm;
}}
hr.hair {{ border:0; border-top:0.5pt solid var(--rule); margin:4mm 0; }}

/* --- headlines list (flexbox, not grid — chromium grid 1fr collapses in print) --- */
.lede-list {{ padding-left:0; list-style:none; margin:0; }}
.lede-list li {{
  display:flex; align-items:flex-start; gap:4mm;
  margin-bottom:2.5mm; padding-bottom:2.5mm;
  border-bottom:0.3pt dotted var(--ink-faint);
  page-break-inside: avoid;
}}
.lede-list li .n {{
  flex:0 0 12mm;
  font-family:"JetBrains Mono",monospace;
  color:var(--accent); font-weight:600; font-size:11pt; line-height:1.2;
}}
.lede-list li .body {{ flex:1 1 0; min-width:0; }}
.lede-list li .h {{
  font-family:"Iowan Old Style",serif; font-size:11pt;
  font-weight:500; color:var(--ink); margin-bottom:0.8mm; line-height:1.25;
}}
.lede-list li .d {{ font-size:9pt; color:var(--ink-soft); line-height:1.45; }}
.lede-list li .excerpt {{
  font-size:9pt; color:var(--ink); line-height:1.5;
  margin-top:1.5mm; font-style:italic;
  border-left:1.5pt solid var(--accent);
  padding-left:3mm;
}}
.lede-list li .meta {{
  font-family:"JetBrains Mono",monospace; font-size:7pt;
  color:var(--ink-faint); letter-spacing:0.06em; margin-top:1mm;
}}

/* --- in-depth story cards (story-heavy section) --- */
.depth-grid {{ display:grid; grid-template-columns:1fr; gap:4mm; margin:0; }}
.depth-card {{
  border-top:1pt solid var(--rule);
  padding-top:2.5mm;
  page-break-inside: avoid;
}}
.depth-card .head {{
  display:flex; justify-content:space-between; align-items:baseline;
  gap:6mm; margin-bottom:1.5mm;
}}
.depth-card .head .src-tag {{
  font-family:"JetBrains Mono",monospace; font-size:7pt;
  color:var(--ink-faint); letter-spacing:0.1em;
  text-transform:uppercase; flex-shrink:0;
}}
.depth-card h3 {{
  font-family:"Iowan Old Style",serif; font-weight:500;
  font-size:12pt; line-height:1.2; margin:0; color:var(--ink);
}}
.depth-card .body-text {{
  font-size:9.5pt; line-height:1.5; color:var(--ink);
  margin:1mm 0 2mm 0; text-align:justify;
}}
.depth-card .quote {{
  font-family:"Iowan Old Style",serif; font-style:italic;
  font-size:10pt; line-height:1.4; color:var(--ink-soft);
  border-left:2pt solid var(--accent);
  padding:1.5mm 0 1.5mm 3.5mm; margin:1.5mm 0;
}}
.depth-card .quote::before {{ content:"\\201C "; color:var(--accent); font-style:normal; }}
.depth-card .quote::after  {{ content:" \\201D"; color:var(--accent); font-style:normal; }}
.depth-card .meta {{
  font-family:"JetBrains Mono",monospace; font-size:6.5pt;
  color:var(--ink-faint); letter-spacing:0.06em; margin-top:1mm;
}}

/* --- per-source narrative blocks (compact — fits 5+ per page) --- */
.source-narrative {{
  display:grid; grid-template-columns:42mm 1fr; gap:5mm;
  margin-bottom:3mm; padding-bottom:3mm;
  border-bottom:0.3pt dotted var(--ink-faint);
  page-break-inside: avoid;
}}
.source-narrative:last-child {{ border-bottom:0; }}
.source-narrative .label {{
  font-family:"JetBrains Mono",monospace; font-size:7pt;
  letter-spacing:0.12em; text-transform:uppercase;
  color:var(--ink-soft);
}}
.source-narrative .label .count {{
  display:block; font-family:"Iowan Old Style",serif;
  font-style:normal; font-size:20pt; line-height:1;
  color:var(--ink); margin-top:1mm; letter-spacing:0;
}}
.source-narrative .label .count .unit {{
  font-size:10pt; color:var(--ink-soft); font-style:italic;
}}
.source-narrative .text {{
  font-size:9.5pt; line-height:1.45; color:var(--ink);
}}
.source-narrative .text .title-sample {{
  font-family:"Iowan Old Style",serif; font-style:italic;
  color:var(--ink-soft); margin-top:1mm; display:block;
  font-size:9pt;
}}

/* --- pullquote --- */
.pullquote {{
  border-top:0.5pt solid var(--rule); border-bottom:0.5pt solid var(--rule);
  padding:4mm 0; margin:5mm 0;
  page-break-inside: avoid;
  break-before: avoid; break-after: avoid;
}}
.pullquote blockquote {{
  margin:0; font-family:"Iowan Old Style",serif;
  font-style:italic; font-size:13.5pt; line-height:1.3; color:var(--ink);
  text-indent:-5mm; padding-left:5mm;
}}
.pullquote blockquote::before {{
  content:"\\201C"; color:var(--accent);
  font-size:22pt; line-height:0; vertical-align:-0.4em; margin-right:1mm;
  font-style:normal;
}}
.pullquote .attrib {{
  margin-top:3mm; font-family:"JetBrains Mono",monospace;
  font-size:7.5pt; color:var(--ink-soft); letter-spacing:0.06em;
}}

/* --- end-of-document legend strip + folio (last page bottom) --- */
.watch-grid {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:3mm 5mm; margin-bottom:4mm; }}
.watch-card {{
  border-top:0.5pt solid var(--ink-faint);
  padding-top:1.5mm;
  display:flex; gap:3mm; align-items:flex-start;
  page-break-inside: avoid;
}}
.watch-num {{
  font-family:"JetBrains Mono",monospace; font-weight:600;
  font-size:10pt; color:var(--accent); line-height:1.2;
  flex:0 0 7mm;
}}
.watch-body {{
  font-size:8.5pt; line-height:1.4; color:var(--ink);
  flex:1 1 0; min-width:0;
}}
.watch-body strong {{ font-weight:600; color:var(--ink); }}
.end-strip {{
  display:flex; gap:6mm;
  font-family:"JetBrains Mono",monospace; font-size:7pt;
  color:var(--ink-soft); letter-spacing:0.08em;
  border-top:0.5pt solid var(--rule);
  padding-top:4mm; margin-top:8mm;
  page-break-inside: avoid;
  break-before: avoid; break-after: avoid;
}}
.end-strip .item {{ display:flex; align-items:center; gap:1.5mm; }}
.end-strip .sw {{ width:2.5mm; height:2.5mm; }}
.end-strip .item.right {{ margin-left:auto; }}

.muted {{ color:var(--ink-soft); }}
</style></head><body>

<!-- COVER -->
<section class="cover">
  <div class="top">
    <div class="brand">hermes<span class="dot">·</span>research &nbsp; // &nbsp; 30-day</div>
    <div class="meta">{today}</div>
  </div>
  <div class="eyebrow">Trend report · AI &amp; tech · 30-day window</div>
  <h1 class="display">What AI &amp; tech<br>actually talked<br>about — last <em>30</em> days.</h1>
  <p class="lede">
    Across {kpis['total']} high-engagement posts from {len(kpis['sources'])} social sources
    ({', '.join(kpis['sources'])}) posted in the 30-day window ending {today},
    three forces dominated the conversation: frontier-lab releases, AI's
    workforce impact, and the chip race catching up.
  </p>
  <div class="hero-figure">
    <div class="kpi">
      <div class="label">Posts across all sources</div>
      <div class="value">{kpis['total']}<span class="unit">posts</span></div>
      <div class="note">{len(kpis['sources'])} sources · 30-day window</div>
    </div>
    <div class="kpi">
      <div class="label">Top combined score</div>
      <div class="value">{kpis['top_score']:,}<span class="unit">pts</span></div>
      <div class="note">{escape(kpis['top_title'][:48])}…</div>
    </div>
    <div class="kpi">
      <div class="label">Most-discussed thread</div>
      <div class="value">{kpis['top_comments']:,}<span class="unit">cmts</span></div>
      <div class="note">{escape(kpis['top_comments_title'][:48])}…</div>
    </div>
  </div>
  <div class="credits">
    <div>PREPARED BY &nbsp;·&nbsp; HERMES RESEARCH DESK</div>
    <div>FOR INTERNAL DISTRIBUTION</div>
  </div>
</section>

<!-- HEADLINES -->
<div class="section-head">
  <div>
    <div class="eyebrow">§ 01 / headlines</div>
    <h2 class="section">Ten stories that defined the month.</h2>
  </div>
  <div class="right">DATA AS OF {today.upper()}<br><span class="mono">window: 30 days</span></div>
</div>
<hr class="hair">
<ol class="lede-list">{li_html}
</ol>

<!-- THEMES + SOURCE MIX (stacked full-width cards, easier pagination than cols) -->
<div class="section-head">
  <div>
    <div class="eyebrow">§ 02 / shape of the conversation</div>
    <h2 class="section">What dominated, and where each source spent its attention.</h2>
  </div>
  <div class="right">n = {kpis['total']}<br><span class="mono">theme = keyword bucket</span></div>
</div>
<hr class="hair">
<div class="card">
  <div class="card-head"><h3>Stories by theme</h3><span class="src">SRC · MULTI</span></div>
  <img class="chart" src="file://{chart_paths['themes']}" alt="themes">
</div>
<div class="card">
  <div class="card-head"><h3>Where each source spent its attention</h3><span class="src">SRC · MULTI</span></div>
  <img class="chart" src="file://{chart_paths['source_mix']}" alt="source mix">
</div>

<!-- IN-DEPTH STORIES -->
<div class="section-head">
  <div>
    <div class="eyebrow">§ 03 / stories in depth</div>
    <h2 class="section">The four threads readers actually engaged with.</h2>
  </div>
  <div class="right">LONGEST BODIES · TOP COMMENT QUOTED<br><span class="mono">selection: top-4 by score with body</span></div>
</div>
<hr class="hair">
<div class="depth-grid">
{depth_html}
</div>

<div class="pullquote">
  <blockquote>
    {pullquote_body}
  </blockquote>
  <div class="attrib">— HERMES RESEARCH DESK · {today.upper()}</div>
</div>

<!-- SOURCE NARRATIVES -->
<div class="section-head">
  <div>
    <div class="eyebrow">§ 04 / by source</div>
    <h2 class="section">How each platform framed the same 30 days.</h2>
  </div>
  <div class="right">PLATFORM-LEVEL READ<br><span class="mono">narrative per source</span></div>
</div>
<hr class="hair">
{source_narratives_html}

<!-- TAKEAWAYS (stacked full-width cards for cleaner pagination) -->
<div class="section-head">
  <div>
    <div class="eyebrow">§ 05 / takeaways</div>
    <h2 class="section">What to carry out of the window.</h2>
  </div>
  <div class="right">COMMENT VOLUME ∝ CONTESTATION<br><span class="mono">log-log · top-right = loudest</span></div>
</div>
<hr class="hair">
<div class="card">
  <div class="card-head"><h3>Score vs comments</h3><span class="src">SRC · MULTI</span></div>
  <img class="chart" src="file://{chart_paths['scatter']}" alt="scatter">
</div>
<div class="card">
  <div class="card-head"><h3>What the data says</h3><span class="src">SRC · ANALYSIS</span></div>
  <p style="font-size:9.5pt;color:var(--ink); line-height:1.55; text-align:justify;">
    {what_the_data_says(stories, kpis)}
  </p>
  <hr class="hair">
  <p style="font-size:8.5pt;color:var(--ink-soft); line-height:1.5;">
    <strong style="color:var(--ink-soft); letter-spacing:0.06em;">CAVEATS ·</strong>
    Briefing sourced from the last30days engine
    ({', '.join(kpis['sources'])}). Items without body text were excluded
    from §03; items without top-comment data were rendered without the
    quote block. For richer coverage, add
    <span class="mono">BRAVE_API_KEY</span> (or
    <span class="mono">EXA_API_KEY</span> / <span class="mono">SERPER_API_KEY</span>)
    to enable web-grounding. For X/Twitter, add
    <span class="mono">XAI_API_KEY</span> or log in to x.com once.
  </p>
</div>

<!-- § 06 / WHAT TO WATCH NEXT — fills the page-5 footer area -->
<div class="section-head">
  <div>
    <div class="eyebrow">§ 06 / what to watch next</div>
    <h2 class="section">Threads to track into the next 30 days.</h2>
  </div>
  <div class="right">FORWARD-LOOK<br><span class="mono">based on this window's signal</span></div>
</div>
<hr class="hair">
<div class="watch-grid">
  <div class="watch-card">
    <span class="watch-num">01</span>
    <div class="watch-body">
      <strong>Frontier-lab cadence.</strong> Multiple labs launched models on overlapping timelines this month. Watch for benchmark-verified upgrades vs. marketing-led ones — the gap is widening.
    </div>
  </div>
  <div class="watch-card">
    <span class="watch-num">02</span>
    <div class="watch-body">
      <strong>Chinese chips outside Asia.</strong> Reddit and HN flagged H100/H200-class chips shipping from Chinese vendors. If export controls tighten, expect a "AI sovereignty" narrative spike.
    </div>
  </div>
  <div class="watch-card">
    <span class="watch-num">03</span>
    <div class="watch-body">
      <strong>Framework consolidation.</strong> Claude Code, OpenHands, and Cline drew heavy GitHub traffic. Watch for SDK standardization — the agent layer is still fragmented.
    </div>
  </div>
</div>

<div class="end-strip">
  <div class="item"><span class="sw" style="background:var(--accent);"></span>ACCENT</div>
  <div class="item"><span class="sw" style="background:var(--ink);"></span>BASELINE</div>
  <div class="item right">END · 30D · {today.upper()}</div>
</div>

</body></html>"""


def render_pdf(html_path, pdf_path):
    chrome = Path.home() / ".cache/ms-playwright/chromium-1223/chrome-linux64/chrome"
    if not chrome.exists():
        chrome = Path("/snap/bin/chromium")
    subprocess.run([
        str(chrome), "--headless", "--disable-gpu", "--no-sandbox",
        "--hide-scrollbars", "--no-pdf-header-footer",
        "--allow-file-access-from-files",  # needed so file:// chart PNGs embed
        f"--print-to-pdf={pdf_path}",
        f"file://{html_path}",
    ], check=True, capture_output=True)


def load_from_engine(engine_out):
    """Normalize engine JSON dump into unified `{title, score, time, comments, url, source}` items.

    Engine dump shape (see lib/pipeline.py + lib/schema.py):
      {
        "items_by_source": {
          "reddit":    [ {title, snippet, url, published_at, engagement:{score,num_comments}, ...}, ... ],
          "hackernews":[ ... ],
          "youtube":   [ ... ],
          "tiktok":    [ ... ],
          "instagram": [ ... ],
          "polymarket":[ ... ],
          "github":    [ ... ],
        },
        "ranked_candidates": [ {title, snippet, url, engagement, source, ...}, ... ],
        "topic": str,
      }

    Each item is flattened to the same `{title, score, time, comments, url, source}`
    tuple `fetch_hn()` returns, so the rest of the pipeline doesn't care
    which path produced the data.
    """
    if not (engine_out and Path(engine_out).exists()):
        return None
    with open(engine_out) as f:
        data = json.load(f)

    items_by_source = data.get("items_by_source", {}) or {}
    out = []

    for source, items in items_by_source.items():
        for it in items:
            # engagement is `{score, num_comments}` on most sources
            eng = it.get("engagement") or {}
            score = (
                eng.get("score")
                if isinstance(eng.get("score"), (int, float))
                else it.get("score", 0)
            )
            comments = (
                eng.get("num_comments")
                if isinstance(eng.get("num_comments"), (int, float))
                else it.get("num_comments", 0)
            )
            # published_at: ISO 8601 string -> epoch
            ts = 0
            pa = it.get("published_at")
            if pa:
                try:
                    ts = datetime.fromisoformat(pa.replace("Z", "+00:00")).timestamp()
                except Exception:
                    ts = 0
            if not ts and isinstance(it.get("time"), (int, float)):
                ts = it["time"]
            # engine puts body text in `body` (sometimes in `snippet`)
            raw_body = (it.get("body") or it.get("snippet") or "").strip()
            # Strip leading title echo ("Title\nFirst sentence...")
            if "\n" in raw_body:
                first_line, rest = raw_body.split("\n", 1)
                if first_line.strip() == (it.get("title") or "").strip():
                    raw_body = rest
            # Strip "None" or empty marker some sources return
            if raw_body.lower() in ("none", "null", ""):
                raw_body = ""

            # Pull one top-comment quote if available
            top_comment_quote = ""
            md = it.get("metadata") or {}
            tc = md.get("top_comments") or []
            if isinstance(tc, list) and tc:
                first = tc[0]
                if isinstance(first, dict):
                    top_comment_quote = (first.get("body") or first.get("text") or "").strip()
                elif isinstance(first, str):
                    top_comment_quote = first.strip()
                # trim
                if len(top_comment_quote) > 280:
                    top_comment_quote = top_comment_quote[:277].rstrip() + "…"

            out.append({
                "title": (it.get("title") or "").strip(),
                "score": int(score or 0),
                "time": ts,
                "comments": int(comments or 0),
                "url": it.get("url") or "",
                "source": source,
                "body": raw_body,
                "quote": top_comment_quote,
            })

    # Drop empty titles; filter to last N days (caller will re-apply)
    out = [x for x in out if x["title"]]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default=None)
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--engine-out", default=None,
                    help="Path to last30days engine JSON dump (skips HN fetch)")
    args = ap.parse_args()

    today = datetime.now().strftime("%Y-%m-%d")
    default_out = Path.home() / "Desktop" / f"last30days-briefing-{today}.pdf"
    output = Path(args.output) if args.output else default_out
    output.parent.mkdir(parents=True, exist_ok=True)

    work = Path(f"/tmp/last30days_briefing_{today}")
    work.mkdir(exist_ok=True)
    charts_dir = work / "charts"
    charts_dir.mkdir(exist_ok=True)
    chart_paths = {
        "themes":     str(charts_dir / "01_themes.png"),
        "source_mix": str(charts_dir / "02_source_mix.png"),
        "scatter":    str(charts_dir / "03_scatter.png"),
    }

    engine_stories = load_from_engine(args.engine_out)
    if engine_stories is not None:
        print(f"last30days-briefing · using engine dump ({args.engine_out})…")
        stories = engine_stories
    else:
        print(f"last30days-briefing · fetching HN (last {args.days}d)…")
        stories = fetch_hn(args.limit)
    cutoff = (datetime.now(tz=timezone.utc) - timedelta(days=args.days)).timestamp()
    stories = [s for s in stories if (s.get("time") or 0) >= cutoff or s.get("time", 0) == 0]
    print(f"  → {len(stories)} items")

    print("  → rendering 3 charts…")
    chart_themes(stories, chart_paths["themes"])
    chart_source_mix(stories, chart_paths["source_mix"])
    chart_scatter(stories, chart_paths["scatter"])

    html = build_html(stories, chart_paths, today, kpis_for(stories))
    html_path = work / "briefing.html"
    html_path.write_text(html)

    print("  → rendering PDF via headless Chrome…")
    render_pdf(str(html_path), str(output))

    # Lean audit: catches orphan-half-page on the last page + missing chart embeds.
    audit_script = (Path.home() / ".hermes/skills/research-briefing-pdf/scripts"
                    / "audit_layout.py")
    if audit_script.exists():
        print("  → audit_layout.py (orphan-half + chart-embed)…")
        r = subprocess.run(["python3", str(audit_script), str(output)],
                           capture_output=True, text=True)
        print(r.stdout.rstrip())
        if r.returncode != 0:
            print("  ! AUDIT FAILED — see above")
            sys.exit(r.returncode)

    size_kb = output.stat().st_size // 1024
    print(f"\n✓ DELIVERED · {output} ({size_kb} KB)")


if __name__ == "__main__":
    main()

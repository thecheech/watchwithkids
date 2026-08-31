#!/usr/bin/env python3
"""Build web/data/*.js payloads, static show + episode pages, and SEO/agent files."""

from __future__ import annotations

import html
import json
import os
import re
import shutil
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
DATA = WEB / "data"
EP_ROOT = WEB / "ep"
LLM_ROOT = WEB / "llms"
DATA.mkdir(exist_ok=True)

# Canonical origin. watchwiththekids.com is aliased in Vercel but NOT registered yet,
# so canonicals point at the live vercel.app host until DNS actually resolves.
SITE = os.environ.get("WWTK_SITE", "https://watchwithkids.vercel.app").rstrip("/")
BRAND = "Watch With The Kids"
TAGLINE = "You kids — your rules!"

READY = [
    "friends",
    "seinfeld",
    "spongebob",
    "the-office",
    "how-i-met-your-mother",
    "big-bang-theory",
    "young-sheldon",
    "malcolm-in-the-middle",
    "rick-and-morty",
    "family-guy",
    "south-park",
    "futurama",
]

SHOW_PAGE = {
    "friends": {"name": "Friends", "h1": 'Friends <span class="pop">🍿</span>'},
    "seinfeld": {"name": "Seinfeld", "h1": 'Seinfeld <span class="pop">🥨</span>'},
    "spongebob": {
        "name": "SpongeBob SquarePants",
        "h1": 'SpongeBob <span class="pop">🍍</span>',
    },
    "the-office": {"name": "The Office", "h1": 'The Office <span class="pop">📎</span>'},
    "how-i-met-your-mother": {
        "name": "How I Met Your Mother",
        "h1": 'How I Met Your Mother <span class="pop">☂️</span>',
    },
    "big-bang-theory": {
        "name": "The Big Bang Theory",
        "h1": 'The Big Bang Theory <span class="pop">🔬</span>',
    },
    "young-sheldon": {"name": "Young Sheldon", "h1": 'Young Sheldon <span class="pop">🧪</span>'},
    "malcolm-in-the-middle": {
        "name": "Malcolm in the Middle",
        "h1": 'Malcolm in the Middle <span class="pop">🛼</span>',
    },
    "rick-and-morty": {"name": "Rick and Morty", "h1": 'Rick and Morty <span class="pop">🌀</span>'},
    "family-guy": {"name": "Family Guy", "h1": 'Family Guy <span class="pop">🐶</span>'},
    "south-park": {"name": "South Park", "h1": 'South Park <span class="pop">🏔️</span>'},
    "futurama": {"name": "Futurama", "h1": 'Futurama <span class="pop">🚀</span>'},
}

BUCKET_BADGE = {
    "safe": ("bucket-pill safe", "✅ All clear"),
    "maybe": ("bucket-pill maybe", "🤔 Gray area"),
    "skip": ("bucket-pill skip", "🚫 Hard pass"),
}

FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com" />\n'
    '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />\n'
    '  <link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@450;600;700'
    '&family=Nunito:wght@500;700;800&display=swap" rel="stylesheet" />'
)


# ── helpers ───────────────────────────────────────────────────────────────────


def esc(value) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def safe_code(code: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", str(code)).strip("-") or "ep"


def clean_title(title: str) -> str:
    return re.sub(r"\s+", " ", str(title or "")).strip()


def bucket_of(ep: dict) -> str:
    overall = int(ep.get("overall") or 1)
    if overall <= 2:
        return "safe"
    if overall == 3:
        return "maybe"
    return "skip"


def ep_label(ep: dict) -> str:
    num = str(ep.get("episode", "")).lstrip("0") or str(ep.get("episode", ""))
    if str(ep.get("season")) == "0":
        return f"Ep {num}"
    return f"S{ep.get('season')} E{num}"


def signal_of(value: int) -> str:
    if value >= 4:
        return "stop"
    if value == 3:
        return "caution"
    return "go"


def details_of(ep: dict) -> list[dict]:
    themes = ep.get("themes") or {}
    detail = themes.get("watch_detail") or []
    if detail:
        return detail
    return [{"theme": t, "how": "", "count": 1, "instances": []} for t in themes.get("watch") or []]


def render_instance(inst: dict) -> str:
    """Quotes get quote marks; descriptions stay plain prose."""
    text = (inst.get("text") or "").strip()
    if not text:
        return ""
    if inst.get("kind") == "quote":
        speaker = (inst.get("speaker") or "").strip()
        quoted = f"\u201c{text}\u201d"
        return f"{speaker}: {quoted}" if speaker else quoted
    return text


def instance_html(inst: dict) -> str:
    text = (inst.get("text") or "").strip()
    if not text:
        return ""
    if inst.get("kind") == "quote":
        speaker = (inst.get("speaker") or "").strip()
        who = f'<span class="instance-speaker">{esc(speaker)}</span> ' if speaker else ""
        return (
            f'<li class="instance instance-quote">{who}'
            f"<q>{esc(text)}</q></li>"
        )
    return f'<li class="instance instance-note">{esc(text)}</li>'


def theme_sentence(ep: dict) -> str:
    """Plain-language sentence used for meta descriptions and agent text."""
    parts = []
    for d in details_of(ep):
        count = int(d.get("count") or 1)
        parts.append(f"{d['theme']} ({count})" if count > 1 else d["theme"])
    return ", ".join(parts)


def meta_description(show_name: str, ep: dict) -> str:
    label = ep_label(ep)
    verdict = ep.get("verdict") or ""
    themes = theme_sentence(ep)
    base = (
        f"Is {show_name} {label} “{clean_title(ep['title'])}” OK for kids? "
        f"Overall {ep.get('overall')}/5 — {verdict}. "
        f"Violence {ep.get('violence')}/5, sex {ep.get('sex')}/5, language {ep.get('language')}/5."
    )
    if themes:
        base += f" Watch for: {themes}."
    return re.sub(r"\s+", " ", base)[:300]


# ── data payloads ─────────────────────────────────────────────────────────────


def slim_detail(detail: dict, *, with_instances: bool) -> dict:
    instances = detail.get("instances") or []
    head = instances[0] if instances else None
    out = {
        "theme": detail.get("theme"),
        "how": detail.get("how") or (render_instance(head) if head else ""),
        "count": int(detail.get("count") or len(instances) or 1),
    }
    if head:
        out["kind"] = head.get("kind")
        out["speaker"] = head.get("speaker")
        out["text"] = head.get("text")
    if with_instances:
        out["instances"] = instances
    return out


def slim(ratings: dict, show_id: str, *, with_instances: bool = False) -> dict:
    episodes = []
    for e in ratings["episodes"]:
        themes = e.get("themes") or {"fine": [], "watch": [], "watch_detail": []}
        episodes.append(
            {
                "season": e["season"],
                "episode": e["episode"],
                "code": e["code"],
                "title": e["title"],
                "index_title": e.get("index_title") or e["title"],
                "summary": e.get("summary"),
                "violence": e["violence"],
                "sex": e["sex"],
                "language": e["language"],
                "overall": e["overall"],
                "verdict": e["verdict"],
                "themes": {
                    "fine": themes.get("fine") or [],
                    "watch": themes.get("watch") or [],
                    "watch_detail": [
                        slim_detail(d, with_instances=with_instances)
                        for d in themes.get("watch_detail") or []
                    ],
                    "notes_extra": themes.get("notes_extra") or [],
                },
                "examples": e.get("examples") or [],
                "notes": e.get("notes"),
            }
        )
    return {
        "show": ratings["show"],
        "show_id": ratings.get("show_id") or show_id,
        "scale": ratings["scale"],
        "disclaimer": ratings["disclaimer"],
        "count": ratings["count"],
        "episodes": episodes,
    }


# ── episode pages (statically rendered for SEO + agents) ──────────────────────


def score_block_html(emoji: str, label: str, value: int) -> str:
    signal = signal_of(int(value))
    tip = f"{label} {value}/5"
    return f"""
        <div class="score-block" data-tip="{esc(tip)}">
          <span class="score-label">{emoji} {label}</span>
          <div class="semaphore signal-{signal} intensity-{value}" role="img" aria-label="{esc(tip)}">
            <span class="sem-housing">
              <i class="lamp stop"></i>
              <i class="lamp caution"></i>
              <i class="lamp go"></i>
            </span>
            <span class="sem-hover">{value}/5</span>
          </div>
        </div>"""


def fit_meter_html(ep: dict) -> str:
    overall = int(ep.get("overall") or 1)
    fit = ((overall - 1) / 4) * 0.84 + 0.08
    signal = signal_of(overall)
    readout = (
        "Mostly appropriate"
        if overall <= 2
        else "Mixed — preview first"
        if overall == 3
        else "Leans inappropriate"
    )
    themes = ep.get("themes") or {}
    fine_n = len(themes.get("fine") or [])
    watch_n = len(themes.get("watch") or [])
    total = fine_n + watch_n
    watch_share = (watch_n / total) if total else fit
    return f"""
        <div class="fit-meter signal-{signal}" style="--fit:{fit:.3f}; --watch:{watch_share:.3f}" role="img" aria-label="{esc(readout)}">
          <div class="fit-meter-top">
            <span class="fit-meter-kicker">Kid fit</span>
            <span class="fit-meter-readout">{esc(readout)}</span>
          </div>
          <div class="fit-track">
            <span class="fit-gradient" aria-hidden="true"></span>
            <span class="fit-balance" aria-hidden="true"></span>
            <span class="fit-marker" aria-hidden="true">
              <span class="fit-marker-dot"></span>
              <span class="fit-marker-score">{overall}/5</span>
            </span>
          </div>
          <div class="fit-ends">
            <span>Appropriate</span>
            <span>Inappropriate</span>
          </div>
        </div>"""


def watch_blocks_html(ep: dict, show_name: str) -> str:
    details = details_of(ep)
    if not details:
        return (
            '<p class="no-themes">No watch-for themes were flagged in this episode — '
            "nothing adult stood out in the transcript.</p>"
        )
    blocks = []
    for d in details:
        instances = d.get("instances") or []
        count = int(d.get("count") or len(instances) or 1)
        shown = len(instances)
        label = "1 moment" if count == 1 else f"{count} moments"
        extra = ""
        if count > shown:
            extra = (
                f'<li class="instance instance-more">…and {count - shown} more '
                f"mentions of this theme in the episode.</li>"
            )
        items = "".join(instance_html(i) for i in instances) or (
            f'<li class="instance instance-note">{esc(d.get("how") or "Flagged in this episode.")}</li>'
        )
        blocks.append(
            f"""
        <section class="theme-block">
          <h3 class="theme-block-head">
            <span class="theme-name">{esc(d["theme"])}</span>
            <span class="theme-count">{esc(label)}</span>
          </h3>
          <p class="theme-block-intro">How <strong>{esc(d["theme"])}</strong> shows up in
            {esc(show_name)} {esc(ep_label(ep))}:</p>
          <ul class="instance-list">{items}{extra}</ul>
        </section>"""
        )
    return "".join(blocks)


def episode_prose(show_name: str, ep: dict) -> str:
    """Indexable plain-English rundown — the bit crawlers and LLMs actually read."""
    label = ep_label(ep)
    title = clean_title(ep["title"])
    details = details_of(ep)
    total = sum(int(d.get("count") or 1) for d in details)
    if details:
        listed = "; ".join(
            f"{d['theme']} ({int(d.get('count') or 1)})" for d in details
        )
        theme_line = (
            f"Across the episode we counted <strong>{total}</strong> flagged moments in "
            f"<strong>{len(details)}</strong> themes: {esc(listed)}."
        )
    else:
        theme_line = "We found no flagged adult themes in this episode."
    summary = f" {esc(ep['summary'])}" if ep.get("summary") else ""
    return f"""
        <p>{esc(show_name)} {esc(label)}, “{esc(title)}”, scores
          <strong>{ep["violence"]}/5 for violence</strong>,
          <strong>{ep["sex"]}/5 for sex</strong> and
          <strong>{ep["language"]}/5 for language</strong>, for an overall kid-rating of
          <strong>{ep["overall"]}/5 — {esc(ep.get("verdict") or "")}</strong>.{summary}</p>
        <p>{theme_line} Every moment below is either a direct quote from the episode transcript or a
          short description of what happens on screen, so you can decide before you press play.</p>"""


def episode_jsonld(show_id: str, show_name: str, ep: dict, url: str) -> str:
    title = clean_title(ep["title"])
    graph = [
        {
            "@type": "TVEpisode",
            "@id": f"{url}#episode",
            "url": url,
            "name": title,
            "episodeNumber": str(ep.get("episode")),
            "partOfSeries": {
                "@type": "TVSeries",
                "name": show_name,
                "url": f"{SITE}/{show_id}.html",
            },
            "partOfSeason": {
                "@type": "TVSeason",
                "seasonNumber": str(ep.get("season")),
            },
            "description": meta_description(show_name, ep),
            "contentRating": ep.get("verdict") or "",
            "keywords": ", ".join(d["theme"] for d in details_of(ep)),
        },
        {
            "@type": "Review",
            "@id": f"{url}#review",
            "url": url,
            "name": f"Is {show_name} {ep_label(ep)} OK for kids?",
            "itemReviewed": {"@id": f"{url}#episode"},
            "reviewBody": re.sub(r"<[^>]+>", "", episode_prose(show_name, ep)).strip(),
            "reviewRating": {
                "@type": "Rating",
                "ratingValue": ep.get("overall"),
                "bestRating": 5,
                "worstRating": 1,
                "alternateName": ep.get("verdict") or "",
            },
            "author": {"@type": "Organization", "name": BRAND, "url": SITE},
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Shows", "item": f"{SITE}/"},
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": show_name,
                    "item": f"{SITE}/{show_id}.html",
                },
                {"@type": "ListItem", "position": 3, "name": f"{ep_label(ep)} {title}", "item": url},
            ],
        },
    ]
    payload = {"@context": "https://schema.org", "@graph": graph}
    return json.dumps(payload, ensure_ascii=False)


def write_episode_pages(show_id: str, payload: dict) -> int:
    out_dir = EP_ROOT / show_id
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    eps = payload["episodes"]
    show_name = payload["show"]
    n = 0
    for i, ep in enumerate(eps):
        code = safe_code(ep["code"])
        prev_code = safe_code(eps[i - 1]["code"]) if i > 0 else None
        next_code = safe_code(eps[i + 1]["code"]) if i + 1 < len(eps) else None
        title = clean_title(ep["title"])
        label = ep_label(ep)
        url = f"{SITE}/ep/{show_id}/{code}.html"
        bkey = bucket_of(ep)
        badge_cls, badge_text = BUCKET_BADGE[bkey]
        desc = meta_description(show_name, ep)
        page_title = f"{show_name} {label}: {title} — Parents Guide"

        boot = {
            "show": show_name,
            "show_id": show_id,
            "code": ep["code"],
            "season": ep["season"],
            "episode": ep["episode"],
            "title": title,
            "overall": ep["overall"],
        }

        prev_link = (
            f'<a class="ep-page-link" href="./{prev_code}.html" rel="prev">← Prev</a>'
            if prev_code
            else '<span class="ep-page-link is-disabled">← Prev</span>'
        )
        next_link = (
            f'<a class="ep-page-link" href="./{next_code}.html" rel="next">Next →</a>'
            if next_code
            else '<span class="ep-page-link is-disabled">Next →</span>'
        )
        notes = f'<p class="notes">📝 {esc(ep["notes"])}</p>' if ep.get("notes") else ""
        summary = f'<p class="summary">{esc(ep["summary"])}</p>' if ep.get("summary") else ""

        html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{esc(page_title)}</title>
  <meta name="description" content="{esc(desc)}" />
  <link rel="canonical" href="{esc(url)}" />
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large" />
  <meta property="og:type" content="video.episode" />
  <meta property="og:site_name" content="{esc(BRAND)}" />
  <meta property="og:title" content="{esc(page_title)}" />
  <meta property="og:description" content="{esc(desc)}" />
  <meta property="og:url" content="{esc(url)}" />
  <meta property="og:image" content="{SITE}/covers/{show_id}.jpg" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{esc(page_title)}" />
  <meta name="twitter:description" content="{esc(desc)}" />
  {FONTS}
  <link rel="stylesheet" href="../../friends.css" />
  <script type="application/ld+json">{episode_jsonld(show_id, show_name, ep, url)}</script>
</head>
<body class="ep-page">
  <div class="confetti" aria-hidden="true"></div>
  <div id="episode-root">
    <nav class="topnav wrap ep-nav" aria-label="Breadcrumb">
      <a class="back-home" href="../../{esc(show_id)}.html">← {esc(show_name)}</a>
      <a class="back-home subtle" href="../../index.html">All shows</a>
    </nav>

    <header class="ep-hero wrap">
      <div class="ep-hero-card">
        <div class="ep-hero-cover">
          <img src="../../covers/{esc(show_id)}.jpg" alt="{esc(show_name)} cover art" width="1920" height="1080" />
        </div>
        <div class="ep-hero-body">
          <div class="ep-meta">
            <span class="badge">🎞️ {esc(label)}</span>
            <span class="{badge_cls}">{esc(badge_text)}</span>
          </div>
          <p class="ep-show">{esc(show_name)}</p>
          <h1>{esc(title)}</h1>
          {summary}
          {fit_meter_html(ep)}
        </div>
      </div>
    </header>

    <main class="wrap ep-main">
      <section class="ep-panel">
        <h2 class="ep-section-title">Content guide</h2>
        <div class="scores ep-scores" aria-label="Traffic-light content guide">
          {score_block_html("👊", "Violence", ep["violence"])}
          {score_block_html("💋", "Sex", ep["sex"])}
          {score_block_html("🙊", "Language", ep["language"])}
          {score_block_html("⭐", "Overall", ep["overall"])}
        </div>
        <p class="verdict-line">{esc(ep.get("verdict") or "")}</p>
        <div class="ep-prose">{episode_prose(show_name, ep)}</div>
      </section>

      <section class="ep-panel">
        <h2 class="ep-section-title">Watch for — every moment, theme by theme</h2>
        {watch_blocks_html(ep, show_name)}
        {notes}
      </section>

      <footer class="ep-actions">
        <div class="ep-pager">
          {prev_link}
          {next_link}
        </div>
        <button
          type="button"
          class="report-trigger ep-report"
          data-code="{esc(ep["code"])}"
          data-season="{esc(ep["season"])}"
          data-episode="{esc(ep["episode"])}"
          data-title="{esc(title)}"
          data-overall="{ep["overall"]}"
        >
          <svg class="report-ico" width="14" height="14" viewBox="0 0 16 16" aria-hidden="true" fill="none">
            <path d="M3.5 2.5v11M3.5 3.2h7.2c.7 0 1.1.8.7 1.4l-1.1 1.7c-.2.3-.2.7 0 1l1.1 1.7c.4.6 0 1.4-.7 1.4H3.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>Report mistake</span>
        </button>
      </footer>

      <p class="ep-foot-note">{esc(BRAND)} · {esc(TAGLINE)} · Informal parent guidance, not an official rating.</p>
    </main>
  </div>
  <script>window.EP_PAGE = {json.dumps(boot, ensure_ascii=False)};</script>
  <script src="../../episode.js"></script>
</body>
</html>
"""
        (out_dir / f"{code}.html").write_text(html_doc)
        n += 1
    return n


# ── show pages ────────────────────────────────────────────────────────────────


def episode_index_html(show_id: str, payload: dict) -> str:
    rows = []
    for ep in payload["episodes"]:
        code = safe_code(ep["code"])
        themes = theme_sentence(ep) or "no adult themes flagged"
        rows.append(
            f'<li class="ep-index-row"><a href="ep/{esc(show_id)}/{esc(code)}.html">'
            f'<span class="ep-index-code">{esc(ep_label(ep))}</span> '
            f'<span class="ep-index-title">{esc(clean_title(ep["title"]))}</span></a> '
            f'<span class="ep-index-meta">Overall {ep["overall"]}/5 · {esc(ep.get("verdict") or "")} · '
            f"Watch for: {esc(themes)}</span></li>"
        )
    return "\n      ".join(rows)


def show_jsonld(show_id: str, payload: dict, mix: dict) -> str:
    url = f"{SITE}/{show_id}.html"
    episodes = payload["episodes"]
    graph = [
        {
            "@type": "TVSeries",
            "@id": f"{url}#series",
            "name": payload["show"],
            "url": url,
            "numberOfEpisodes": len(episodes),
            "image": f"{SITE}/covers/{show_id}.jpg",
            "description": (
                f"Parent guide to every {payload['show']} episode: violence, sex and language "
                f"scored 1–5 with the exact moments quoted."
            ),
        },
        {
            "@type": "ItemList",
            "name": f"{payload['show']} episodes rated for kids",
            "numberOfItems": len(episodes),
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": i + 1,
                    "url": f"{SITE}/ep/{show_id}/{safe_code(ep['code'])}.html",
                    "name": f"{ep_label(ep)} {clean_title(ep['title'])}",
                }
                for i, ep in enumerate(episodes[:200])
            ],
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Shows", "item": f"{SITE}/"},
                {"@type": "ListItem", "position": 2, "name": payload["show"], "item": url},
            ],
        },
        {
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": f"Is {payload['show']} OK for kids?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": (
                            f"Of {mix['total']} {payload['show']} episodes we rated, {mix['safe']} are "
                            f"all clear (overall 1–2/5), {mix['maybe']} are gray area (3/5) and "
                            f"{mix['skip']} are a hard pass (4–5/5). Every episode page lists the exact "
                            f"moments — quoted from the transcript — behind the score."
                        ),
                    },
                },
                {
                    "@type": "Question",
                    "name": f"How is each {payload['show']} episode rated?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": (
                            "Each episode is scored 1–5 for violence, sex and language. The overall "
                            "score is the highest of the three. Themes such as Sex & hookups, Swearing, "
                            "Alcohol / Drugs or Racism are listed with a count of how many times they "
                            "occur and the quotes or scene descriptions behind them."
                        ),
                    },
                },
            ],
        },
    ]
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)


def write_show_html(show_id: str, payload: dict, mix: dict) -> None:
    meta = SHOW_PAGE.get(show_id, {"name": payload["show"], "h1": payload["show"]})
    name = meta["name"]
    url = f"{SITE}/{show_id}.html"
    total = mix["total"] or 1
    desc = (
        f"Is {name} OK for kids? All {mix['total']} episodes rated 1–5 for violence, sex and "
        f"language — {round(100 * mix['safe'] / total)}% all clear, "
        f"{round(100 * mix['maybe'] / total)}% gray area, "
        f"{round(100 * mix['skip'] / total)}% hard pass, with the exact moments quoted."
    )
    page_title = f"{name} Parents Guide — Every Episode Rated for Kids"

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{esc(page_title)}</title>
  <meta name="description" content="{esc(desc)}" />
  <link rel="canonical" href="{esc(url)}" />
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large" />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="{esc(BRAND)}" />
  <meta property="og:title" content="{esc(page_title)}" />
  <meta property="og:description" content="{esc(desc)}" />
  <meta property="og:url" content="{esc(url)}" />
  <meta property="og:image" content="{SITE}/covers/{show_id}.jpg" />
  <meta name="twitter:card" content="summary_large_image" />
  {FONTS}
  <link rel="stylesheet" href="friends.css" />
  <script type="application/ld+json">{show_jsonld(show_id, payload, mix)}</script>
</head>
<body>
  <div class="confetti" aria-hidden="true"></div>

  <nav class="topnav wrap">
    <a class="back-home" href="index.html">← All shows</a>
  </nav>

  <header class="hero">
    <div class="wrap hero-inner">
      <div class="hero-copy">
        <h1>{meta["h1"]}</h1>
        <p class="tagline">
          Three buckets. One question: <strong>can the kids watch this?</strong>
        </p>
        <div class="hero-pills" aria-hidden="true">
          <span>✅ all clear</span>
          <span>🤔 gray area</span>
          <span>🚫 hard pass</span>
        </div>
      </div>
      <aside class="hero-card">
        <div class="hero-cover">
          <img src="covers/{show_id}.jpg" alt="{esc(name)}" width="1920" height="1080" />
        </div>
        <p class="disclaimer" id="disclaimer"></p>
      </aside>
    </div>
  </header>

  <section class="wrap vibe-row" role="tablist" aria-label="Kid-safety buckets">
    <button type="button" class="vibe-btn is-active" data-bucket="all" id="bucket-all">
      <span class="vibe-emoji">✨</span>
      <span class="vibe-label">Show all</span>
      <span class="vibe-count" data-count-for="all">—</span>
    </button>
    <button type="button" class="vibe-btn vibe-safe" data-bucket="safe" id="bucket-safe">
      <span class="vibe-emoji">✅</span>
      <span class="vibe-label">All clear</span>
      <span class="vibe-sub">Pretty safe with kids</span>
      <span class="vibe-count" data-count-for="safe">—</span>
    </button>
    <button type="button" class="vibe-btn vibe-maybe" data-bucket="maybe" id="bucket-maybe">
      <span class="vibe-emoji">🤔</span>
      <span class="vibe-label">Gray area</span>
      <span class="vibe-sub">Your call — preview first</span>
      <span class="vibe-count" data-count-for="maybe">—</span>
    </button>
    <button type="button" class="vibe-btn vibe-skip" data-bucket="skip" id="bucket-skip">
      <span class="vibe-emoji">🚫</span>
      <span class="vibe-label">Hard pass</span>
      <span class="vibe-sub">Skip for little ones</span>
      <span class="vibe-count" data-count-for="skip">—</span>
    </button>
  </section>

  <section class="wrap controls-bar">
    <label class="field">
      <span>🎬 Season</span>
      <select id="season">
        <option value="all">All seasons ✨</option>
      </select>
    </label>
    <label class="field grow">
      <span>🔎 Search</span>
      <input id="q" type="search" placeholder="Search titles or themes…" autocomplete="off" />
    </label>
    <label class="field">
      <span>🔀 Sort</span>
      <select id="sort">
        <option value="air">Air order</option>
        <option value="themes">Most watch-fors first</option>
        <option value="overall-asc">Safest first 🏅</option>
        <option value="overall-desc">Spiciest first 🌶️</option>
        <option value="sex-desc">Most 💋 first</option>
        <option value="language-desc">Most 🙊 first</option>
        <option value="violence-desc">Most 👊 first</option>
      </select>
    </label>
  </section>

  <section class="wrap theme-filter-bar" aria-label="Watch-for theme filters">
    <div class="theme-filter-head">
      <div>
        <h2 class="theme-filter-title">Watch for</h2>
        <p class="theme-filter-sub">Filter by the flags parents actually care about.</p>
      </div>
      <button type="button" class="theme-clear" id="theme-clear" hidden>Clear themes</button>
    </div>
    <div class="theme-chips" id="theme-chips" role="group" aria-label="Themes to watch for"></div>
  </section>

  <section class="wrap legend">
    <div class="legend-scale" aria-label="Traffic-light guide">
      <span class="sem-legend">
        <span class="mini-sem" aria-hidden="true">
          <i class="lamp stop"></i><i class="lamp caution"></i><i class="lamp go on"></i>
        </span>
        Go
      </span>
      <span class="sem-legend">
        <span class="mini-sem" aria-hidden="true">
          <i class="lamp stop"></i><i class="lamp caution on"></i><i class="lamp go"></i>
        </span>
        Caution
      </span>
      <span class="sem-legend">
        <span class="mini-sem" aria-hidden="true">
          <i class="lamp stop on"></i><i class="lamp caution"></i><i class="lamp go"></i>
        </span>
        Stop — inappropriate
      </span>
    </div>
    <p class="bucket-hint" id="bucket-hint">Tap a bucket above to filter fast.</p>
    <p id="stats" class="stats"></p>
  </section>

  <main class="wrap">
    <div id="list" class="episode-list"></div>
    <p id="empty" class="empty hidden">🫠 Nothing matched. Loosen the filters and try again!</p>
  </main>

  <section class="wrap seo-copy">
    <h2>Is {esc(name)} OK to watch with the kids?</h2>
    <p>
      We rated all <strong>{mix["total"]}</strong> episodes of {esc(name)} for violence, sex and
      language on a 1–5 scale. <strong>{mix["safe"]}</strong> episodes come out all clear (overall
      1–2/5), <strong>{mix["maybe"]}</strong> land in the gray area (3/5) and
      <strong>{mix["skip"]}</strong> are a hard pass for little kids (4–5/5).
    </p>
    <p>
      Each episode page lists every watch-for theme — Sex &amp; hookups, Nudity &amp; bodies,
      Porn / strippers, Swearing, Violence &amp; death, Affairs / cheating, Suicide / self-harm,
      Alcohol / Drugs, Gay / Lesbian, Fat-shaming, Slut-shaming and Racism — with a count of how
      many times it comes up and the exact quote or scene description behind each mention.
    </p>
  </section>

  <section class="wrap ep-index" aria-label="All {esc(name)} episodes">
    <h2>All {esc(name)} episodes</h2>
    <ul class="ep-index-list">
      {episode_index_html(show_id, payload)}
    </ul>
  </section>

  <footer class="wrap site-footer">
    <p>Made for family couch debates · <strong>watchwiththekids.com</strong> · {esc(TAGLINE)}</p>
  </footer>

  <script src="data/{show_id}.js"></script>
  <script src="show.js"></script>
</body>
</html>
"""
    out = WEB / f"{show_id}.html"
    out.write_text(html_doc)
    print(f"Wrote {out}")


# ── agent / SEO files ─────────────────────────────────────────────────────────


def write_agent_index(show_id: str, payload: dict, mix: dict) -> Path:
    LLM_ROOT.mkdir(exist_ok=True)
    name = payload["show"]
    lines = [
        f"# {name} — parent guide ({mix['total']} episodes)",
        "",
        f"Source: {SITE}/{show_id}.html",
        f"Scoring: violence, sex and language each 1–5; overall = the highest of the three.",
        f"Buckets: {mix['safe']} all clear (1–2), {mix['maybe']} gray area (3), "
        f"{mix['skip']} hard pass (4–5).",
        "",
    ]
    for ep in payload["episodes"]:
        code = safe_code(ep["code"])
        lines.append(f"## {ep_label(ep)} — {clean_title(ep['title'])}")
        lines.append(f"URL: {SITE}/ep/{show_id}/{code}.html")
        lines.append(
            f"Scores: violence {ep['violence']}/5, sex {ep['sex']}/5, "
            f"language {ep['language']}/5, overall {ep['overall']}/5 ({ep.get('verdict') or ''})"
        )
        if ep.get("summary"):
            lines.append(f"Summary: {ep['summary']}")
        details = details_of(ep)
        if not details:
            lines.append("Watch for: nothing flagged.")
        else:
            lines.append("Watch for:")
            for d in details:
                count = int(d.get("count") or 1)
                lines.append(f"- {d['theme']} — {count} moment(s)")
                for inst in d.get("instances") or []:
                    rendered = render_instance(inst)
                    if rendered:
                        lines.append(f"  - {rendered}")
        lines.append("")
    out = LLM_ROOT / f"{show_id}.md"
    out.write_text("\n".join(lines))
    return out


def write_llms_txt(shows: list[dict], mixes: dict[str, dict]) -> None:
    lines = [
        f"# {BRAND}",
        "",
        f"> {SITE} — a parent guide to TV episodes. Every episode is scored 1–5 for violence, "
        "sex and language, and every flagged theme lists how many times it occurs plus the exact "
        "quote or scene description behind it.",
        "",
        "## How the ratings work",
        "",
        "- Scores: violence, sex and language, each 1 (none) to 5 (heavy).",
        "- Overall = the highest of the three scores.",
        "- Buckets: 1–2 = all clear, 3 = gray area, 4–5 = hard pass for little kids.",
        "- Watch-for themes: Sex & hookups, Nudity & bodies, Porn / strippers, Swearing, "
        "Violence & death, Affairs / cheating, Suicide / self-harm, Alcohol / Drugs, "
        "Gay / Lesbian, Fat-shaming, Slut-shaming, Racism.",
        "- Each theme on an episode page shows every occurrence: quotes appear in quote marks, "
        "everything else is a short description of what happens.",
        "",
        "## Shows rated",
        "",
    ]
    for s in shows:
        sid = s["id"]
        if sid not in mixes:
            continue
        mix = mixes[sid]
        total = mix["total"] or 1
        lines.append(
            f"- [{s['name']}]({SITE}/{sid}.html): {mix['total']} episodes — "
            f"{round(100 * mix['safe'] / total)}% all clear, "
            f"{round(100 * mix['maybe'] / total)}% gray area, "
            f"{round(100 * mix['skip'] / total)}% hard pass. "
            f"Full text index: [{sid}.md]({SITE}/llms/{sid}.md)"
        )
    lines += [
        "",
        "## Machine-readable data",
        "",
        f"- [Sitemap]({SITE}/sitemap.xml): every show and episode page.",
        f"- [Show catalogue JSON]({SITE}/shows.json): shows, covers and rating mix.",
        "- Per-show ratings JSON: " + f"{SITE}/data/<show-id>.js (window.RATINGS payload).",
        "",
        "## Notes",
        "",
        "- This is informal parental guidance, not an official rating body.",
        "- Strong profanity is masked in quotes; slurs are replaced with [racial slur].",
        f"- {TAGLINE}",
        "",
    ]
    (WEB / "llms.txt").write_text("\n".join(lines))
    (WEB / "llm.txt").write_text(
        f"# {BRAND}\n\nSee {SITE}/llms.txt for the full agent index.\n"
    )


NUMBER_WORDS = {
    1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six",
    7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten", 11: "Eleven", 12: "Twelve",
}


def _replace_block(text: str, marker: str, body: str) -> str:
    start, end = f"<!-- SEO:{marker}:START -->", f"<!-- SEO:{marker}:END -->"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if not pattern.search(text):
        return text
    return pattern.sub(f"{start}{body}{end}", text)


def update_index_html(shows: list[dict], mixes: dict[str, dict]) -> None:
    """Keep the homepage's crawlable show list, count line and JSON-LD in sync."""
    path = WEB / "index.html"
    if not path.exists():
        return
    live = [s for s in shows if s["id"] in mixes]
    total_eps = sum(mixes[s["id"]]["total"] for s in live)
    word = NUMBER_WORDS.get(len(live), str(len(live)))

    count_line = (
        f"{word} shows live · {total_eps:,} episodes rated for violence, sex and language."
    )

    rows = []
    for s in live:
        mix = mixes[s["id"]]
        total = mix["total"] or 1
        rows.append(
            f'<li><a href="{esc(s["id"])}.html"><strong>{esc(s["name"])}</strong></a> — '
            f'{mix["total"]} episodes rated: {round(100 * mix["safe"] / total)}% all clear, '
            f'{round(100 * mix["maybe"] / total)}% gray area, '
            f'{round(100 * mix["skip"] / total)}% hard pass.</li>'
        )
    shows_block = f"""
  <section class="wrap seo-copy" aria-label="Shows rated">
    <h2>Every show we've rated</h2>
    <p>
      {esc(BRAND)} scores each episode 1–5 for <strong>violence</strong>, <strong>sex</strong> and
      <strong>language</strong>. The overall score is the highest of the three: 1–2 is all clear,
      3 is a gray area, 4–5 is a hard pass for little kids. Every flagged theme — Sex &amp; hookups,
      Nudity &amp; bodies, Porn / strippers, Swearing, Violence &amp; death, Affairs / cheating,
      Suicide / self-harm, Alcohol / Drugs, Gay / Lesbian, Fat-shaming, Slut-shaming and Racism —
      is listed with how many times it comes up and the exact quote or scene behind it.
    </p>
    <ul class="seo-show-list">
      {"".join(rows)}
    </ul>
    <p>Agents and LLMs: see <a href="llms.txt">llms.txt</a> for a machine-readable index.</p>
  </section>
"""

    jsonld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": f"{SITE}/#website",
                "url": f"{SITE}/",
                "name": BRAND,
                "description": (
                    "Parent guide to TV episodes — violence, sex and language scored 1–5 with "
                    "every flagged moment quoted."
                ),
                "publisher": {"@id": f"{SITE}/#org"},
            },
            {
                "@type": "Organization",
                "@id": f"{SITE}/#org",
                "name": BRAND,
                "url": f"{SITE}/",
                "slogan": TAGLINE,
            },
            {
                "@type": "ItemList",
                "name": "Shows rated for kids",
                "numberOfItems": len(live),
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": i + 1,
                        "name": s["name"],
                        "url": f"{SITE}/{s['id']}.html",
                    }
                    for i, s in enumerate(live)
                ],
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": "How do you decide if an episode is OK for kids?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": (
                                "Each episode is scored 1–5 for violence, sex and language from its "
                                "transcript. The overall score is the highest of the three. Episodes "
                                "scoring 1–2 are all clear, 3 is a gray area worth previewing, and "
                                "4–5 is a hard pass for little kids."
                            ),
                        },
                    },
                    {
                        "@type": "Question",
                        "name": "Do you show what actually happens in the episode?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": (
                                "Yes. Every episode page lists each flagged theme, how many times it "
                                "occurs, and the moments behind it — direct quotes in quote marks, or "
                                "a short description of the scene where there is no line to quote."
                            ),
                        },
                    },
                ],
            },
        ],
    }
    script = (
        '\n  <script type="application/ld+json">'
        + json.dumps(jsonld, ensure_ascii=False)
        + "</script>\n  "
    )

    text = path.read_text()
    # Hand-written head tags carry absolute URLs — keep them on the current origin.
    text = re.sub(r"https://(?:watchwiththekids\.com|watchwithkids\.vercel\.app)", SITE, text)
    text = _replace_block(text, "LIVECOUNT", count_line)
    text = _replace_block(text, "SHOWS", shows_block)
    text = _replace_block(text, "JSONLD", script)
    path.write_text(text)
    print(f"Updated index.html ({len(live)} live shows, {total_eps} episodes)")


def write_robots() -> None:
    (WEB / "robots.txt").write_text(
        "\n".join(
            [
                "User-agent: *",
                "Allow: /",
                "",
                "# AI / agent crawlers are welcome — the ratings are meant to be quoted.",
                "User-agent: GPTBot",
                "Allow: /",
                "",
                "User-agent: OAI-SearchBot",
                "Allow: /",
                "",
                "User-agent: ChatGPT-User",
                "Allow: /",
                "",
                "User-agent: ClaudeBot",
                "Allow: /",
                "",
                "User-agent: Claude-Web",
                "Allow: /",
                "",
                "User-agent: PerplexityBot",
                "Allow: /",
                "",
                "User-agent: Google-Extended",
                "Allow: /",
                "",
                "User-agent: Applebot-Extended",
                "Allow: /",
                "",
                f"Sitemap: {SITE}/sitemap.xml",
                "",
            ]
        )
    )


def write_sitemap(urls: list[tuple[str, str]]) -> None:
    today = date.today().isoformat()
    body = "\n".join(
        f"  <url><loc>{esc(loc)}</loc><lastmod>{today}</lastmod>"
        f"<changefreq>monthly</changefreq><priority>{prio}</priority></url>"
        for loc, prio in urls
    )
    (WEB / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n"
        "</urlset>\n"
    )


# ── orchestration ─────────────────────────────────────────────────────────────


def episode_mix(episodes: list[dict]) -> dict:
    safe = maybe = skip = 0
    for e in episodes:
        o = int(e.get("overall") or 1)
        if o <= 2:
            safe += 1
        elif o == 3:
            maybe += 1
        else:
            skip += 1
    return {"safe": safe, "maybe": maybe, "skip": skip, "total": safe + maybe + skip}


def build_show(show_id: str, src: Path, sitemap: list[tuple[str, str]]) -> dict:
    ratings = json.loads(src.read_text())
    listing = slim(ratings, show_id, with_instances=False)
    full = slim(ratings, show_id, with_instances=True)
    mix = episode_mix(listing["episodes"])

    out = DATA / f"{show_id}.js"
    out.write_text("window.RATINGS = " + json.dumps(listing, ensure_ascii=False) + ";\n")
    if show_id == "friends":
        (WEB / "data.js").write_text(out.read_text())

    write_show_html(show_id, listing, mix)
    n = write_episode_pages(show_id, full)
    write_agent_index(show_id, full, mix)

    sitemap.append((f"{SITE}/{show_id}.html", "0.9"))
    for ep in listing["episodes"]:
        sitemap.append((f"{SITE}/ep/{show_id}/{safe_code(ep['code'])}.html", "0.7"))

    print(f"Wrote {out} ({listing['count']} episodes) + {n} episode pages + llms/{show_id}.md")
    return mix


def main() -> None:
    mixes: dict[str, dict] = {}
    sitemap: list[tuple[str, str]] = [(f"{SITE}/", "1.0")]

    if LLM_ROOT.exists():
        shutil.rmtree(LLM_ROOT)

    ratings_dir = ROOT / "ratings"
    for show_id in READY:
        src = ROOT / "ratings.json" if show_id == "friends" else ratings_dir / f"{show_id}.json"
        if src.exists():
            mixes[show_id] = build_show(show_id, src, sitemap)

    shows_path = WEB / "shows.json"
    shows = json.loads(shows_path.read_text())
    for s in shows:
        s["ready"] = s["id"] in mixes
        s["href"] = f"{s['id']}.html" if s["ready"] else None
        if s["id"] in mixes:
            s["mix"] = mixes[s["id"]]
        else:
            s.pop("mix", None)
    shows_path.write_text(json.dumps(shows, indent=2, ensure_ascii=False) + "\n")
    (WEB / "shows.js").write_text("window.SHOWS = " + json.dumps(shows, ensure_ascii=False) + ";\n")

    sitemap.append((f"{SITE}/llms.txt", "0.5"))
    for show_id in mixes:
        sitemap.append((f"{SITE}/llms/{show_id}.md", "0.4"))

    write_sitemap(sitemap)
    write_robots()
    write_llms_txt(shows, mixes)
    update_index_html(shows, mixes)

    print(f"Updated shows.js ready flags: {sorted(mixes)}")
    print(f"Sitemap: {len(sitemap)} URLs · robots.txt · llms.txt · llms/*.md")


if __name__ == "__main__":
    main()

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
from urllib.parse import quote_plus

from catalog import dedupe_codes

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
DATA = WEB / "data"
EP_ROOT = WEB / "ep"
LLM_ROOT = WEB / "llms"
DATA.mkdir(exist_ok=True)

SITE = os.environ.get("WWTK_SITE", "https://watchwiththekids.com").rstrip("/")
BRAND = "Watch With The Kids"
TAGLINE = "You kids — your rules!"

READY = [
    "friends",
    "seinfeld",
    "spongebob",
    "bluey",
    "phineas-and-ferb",
    "avatar",
    "gravity-falls",
    "adventure-time",
    "steven-universe",
    "full-house",
    "the-office",
    "how-i-met-your-mother",
    "big-bang-theory",
    "young-sheldon",
    "malcolm-in-the-middle",
    "rick-and-morty",
    "family-guy",
    "south-park",
    "futurama",
    "parks-and-recreation",
    "modern-family",
    "fresh-prince",
    "brooklyn-nine-nine",
    "bobs-burgers",
    "simpsons",
    "wednesday",
    "kpop-demon-hunters",
    "stranger-things",
    "legend-of-korra",
    "clone-wars",
    "owl-house",
    "amphibia",
    "pokemon",
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
    "parks-and-recreation": {
        "name": "Parks and Recreation",
        "h1": 'Parks and Recreation <span class="pop">🏞️</span>',
    },
    "modern-family": {
        "name": "Modern Family",
        "h1": 'Modern Family <span class="pop">🏡</span>',
    },
    "bluey": {"name": "Bluey", "h1": 'Bluey <span class="pop">🐶</span>'},
    "phineas-and-ferb": {
        "name": "Phineas and Ferb",
        "h1": 'Phineas and Ferb <span class="pop">🎢</span>',
    },
    "avatar": {
        "name": "Avatar: The Last Airbender",
        "h1": 'Avatar: The Last Airbender <span class="pop">🌊</span>',
    },
    "gravity-falls": {
        "name": "Gravity Falls",
        "h1": 'Gravity Falls <span class="pop">🌲</span>',
    },
    "adventure-time": {
        "name": "Adventure Time",
        "h1": 'Adventure Time <span class="pop">🗡️</span>',
    },
    "steven-universe": {
        "name": "Steven Universe",
        "h1": 'Steven Universe <span class="pop">💎</span>',
    },
    "full-house": {"name": "Full House", "h1": 'Full House <span class="pop">🏠</span>'},
    "wednesday": {"name": "Wednesday", "h1": 'Wednesday <span class="pop">🖤</span>'},
    "kpop-demon-hunters": {
        "name": "KPop Demon Hunters",
        "h1": 'KPop Demon Hunters <span class="pop">🎤</span>',
    },
    "fresh-prince": {
        "name": "The Fresh Prince of Bel-Air",
        "h1": 'Fresh Prince <span class="pop">👑</span>',
    },
    "brooklyn-nine-nine": {
        "name": "Brooklyn Nine-Nine",
        "h1": 'Brooklyn Nine-Nine <span class="pop">🚓</span>',
    },
    "bobs-burgers": {
        "name": "Bob's Burgers",
        "h1": "Bob's Burgers <span class=\"pop\">🍔</span>",
    },
    "simpsons": {
        "name": "The Simpsons",
        "h1": 'The Simpsons <span class="pop">🍩</span>',
    },
    "stranger-things": {
        "name": "Stranger Things",
        "h1": 'Stranger Things <span class="pop">🔦</span>',
    },
    "legend-of-korra": {
        "name": "The Legend of Korra",
        "h1": 'Legend of Korra <span class="pop">🌊</span>',
    },
    "clone-wars": {
        "name": "Star Wars: The Clone Wars",
        "h1": 'The Clone Wars <span class="pop">⚔️</span>',
    },
    "owl-house": {
        "name": "The Owl House",
        "h1": 'The Owl House <span class="pop">🦉</span>',
    },
    "amphibia": {
        "name": "Amphibia",
        "h1": 'Amphibia <span class="pop">🐸</span>',
    },
    "pokemon": {
        "name": "Pokémon: Indigo League",
        "h1": 'Pokémon <span class="pop">⚡</span>',
    },
}

BUCKET_BADGE = {
    "safe": ("bucket-pill safe", "✅ All clear"),
    "maybe": ("bucket-pill maybe", "🤔 Gray area"),
    "skip": ("bucket-pill skip", "🚫 Hard pass"),
}

FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com" />\n'
    '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />\n'
    '  <link rel="preconnect" href="https://static.tvmaze.com" />\n'
    '  <link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@450;600;700'
    '&family=Nunito:wght@500;700;800&display=swap" rel="stylesheet" />'
)

STILLS_PATH = ROOT / "stills.json"
_STILLS: dict | None = None

WATCH_LINKS = json.loads((ROOT / "watch_links.json").read_text()) if (ROOT / "watch_links.json").exists() else {}


# ── helpers ───────────────────────────────────────────────────────────────────


def esc(value) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def ep_count(n: int) -> str:
    """'1 episode' / '16 episodes' — films and one-off specials read wrong otherwise."""
    return f"{n} episode" if int(n) == 1 else f"{n} episodes"


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


def clip_meta(text: str, limit: int = 155) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    cut = text[: limit - 1]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(".,;:—–-") + "…"


def display_title(title: str) -> str:
    """Drop scraper prefixes like 'Series 06 Episode 09 –' so titles match search queries."""
    t = clean_title(title)
    t = re.sub(r"^Series\s+\d+\s+Episode\s+\d+\s*[–—:-]\s*", "", t, flags=re.I)
    t = re.sub(r"^[A-Za-z'& ]+\s\d{3,4}\s*[–—:-]\s*", "", t)
    t = re.sub(r"^\d{3,4}\s*[–—:-]\s*", "", t)
    return t.strip() or clean_title(title)


def season_label(season, show_id: str | None = None) -> str:
    raw = str(season)
    if raw == "0" and show_id in {"kpop-demon-hunters"}:
        return "Movie"
    if raw == "0":
        return "Specials"
    return f"Season {raw.lstrip('0') or raw}"


def extra_head(image_url: str) -> str:
    return (
        f'  <meta property="og:image:width" content="1920" />\n'
        f'  <meta property="og:image:height" content="1080" />\n'
        f'  <meta property="og:locale" content="en_US" />\n'
        f'  <meta name="twitter:image" content="{esc(image_url)}" />\n'
        f'  <link rel="icon" href="/favicon.svg" type="image/svg+xml" />\n'
        f'  <link rel="icon" href="/favicon.ico" sizes="any" />\n'
        f'  <link rel="apple-touch-icon" href="/apple-touch-icon.png" />\n'
        f'  <meta name="theme-color" content="#14101c" />\n'
    )


def site_footer(prefix: str = "") -> str:
    return f"""  <footer class="wrap site-footer">
    <p>
      <a href="{prefix}index.html">{esc(BRAND)}</a>
      · <a href="{prefix}guides/index.html">What to watch</a>
      · <a href="{prefix}about.html">How we rate</a>
      · {esc(TAGLINE)}
    </p>
  </footer>"""


def faq_html(items: list[tuple[str, str]]) -> str:
    blocks = []
    for q, a in items:
        blocks.append(
            f'    <details class="faq-item">\n'
            f"      <summary>{esc(q)}</summary>\n"
            f"      <p>{a}</p>\n"
            f"    </details>"
        )
    return (
        '  <section class="wrap seo-copy faq" aria-label="Frequently asked questions">\n'
        "    <h2>Common questions</h2>\n"
        + "\n".join(blocks)
        + "\n  </section>"
    )


def faq_jsonld(items: list[tuple[str, str]]) -> dict:
    return {
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)},
            }
            for q, a in items
        ],
    }


def home_faqs() -> list[tuple[str, str]]:
    return [
        (
            "How do you decide if an episode is OK for kids?",
            "Each episode is scored 1–5 for <strong>violence</strong>, <strong>sex</strong> and "
            "<strong>language</strong> from its transcript. The overall score is the highest of "
            "the three. 1–2 is all clear, 3 is a gray area worth previewing, and 4–5 is a hard "
            "pass for little kids.",
        ),
        (
            "Do you show what actually happens in the episode?",
            "Yes. Every episode page lists each flagged theme, how many times it occurs, and the "
            "moments behind it — direct quotes, or a short description of the scene when there "
            "is no line to quote.",
        ),
        (
            "Where should I start if I just want something safe tonight?",
            'Open <a href="guides/index.html">What to watch</a> — each show has a list of the '
            "safest episodes and the ones to skip, built from the same 1–5 scores.",
        ),
    ]


def show_faqs(show_id: str, name: str, mix: dict) -> list[tuple[str, str]]:
    return [
        (
            f"Is {name} OK for kids?",
            f"We rated {ep_count(mix['total'])} of {esc(name)}: <strong>{mix['safe']}</strong> "
            f"all clear (overall 1–2/5), <strong>{mix['maybe']}</strong> gray area (3/5) and "
            f"<strong>{mix['skip']}</strong> a hard pass (4–5/5). Every episode page lists "
            "the exact moments behind the score.",
        ),
        (
            f"How is each {name} episode rated?",
            "Each episode is scored 1–5 for violence, sex and language. The overall score is the "
            "highest of the three. Themes such as Sex &amp; hookups, Swearing, Alcohol / Drugs or "
            "Racism are listed with a count and the quotes or scene descriptions behind them.",
        ),
        (
            f"Which {name} episodes are safest to watch with kids?",
            f'See the <a href="guides/{esc(show_id)}.html">What to watch in {esc(name)}</a> list — '
            "safest episodes first, then the hard-pass list so you can skip them.",
        ),
        (
            f"Where can I watch {name}?",
            f"Try streaming {esc(name)} on Netflix, HBO or Disney+ — catalogs differ by country. "
            "To buy a season or box set, use Amazon, Apple TV or Google Play.",
        ),
    ]


def meta_description(show_name: str, ep: dict) -> str:
    label = ep_label(ep)
    title = display_title(ep["title"])
    verdict = ep.get("verdict") or ""
    themes = theme_sentence(ep)
    base = (
        f"Is {show_name} {label} OK for kids? {title}. "
        f"Overall {ep.get('overall')}/5 — {verdict}. "
        f"Violence {ep.get('violence')}/5, sex {ep.get('sex')}/5, language {ep.get('language')}/5."
    )
    if themes:
        base += f" Watch for: {themes}."
    return clip_meta(base)


def _affiliate_url(raw) -> str | None:
    if not raw:
        return None
    if isinstance(raw, str):
        return raw
    if isinstance(raw, dict):
        return raw.get("url") or None
    return None


def outbound_href(link: dict) -> str:
    """Prefer an affiliate URL when one is set; otherwise the plain outbound."""
    return _affiliate_url(link.get("affiliate")) or link["url"]


def outbound_rel(link: dict) -> str:
    rel = "noopener noreferrer"
    if _affiliate_url(link.get("affiliate")):
        rel += " sponsored"
    return rel


def stream_links_for(show_id: str, show_name: str) -> dict | None:
    aff = (WATCH_LINKS.get("affiliates") or {}).get(show_id) or {}
    official = (WATCH_LINKS.get("official") or {}).get(show_id)
    deep = (WATCH_LINKS.get("stream") or {}).get(show_id) or {}
    q = quote_plus(show_name)

    def chip(provider: str, name: str, url: str, note: str = "") -> dict:
        link = {"id": provider, "name": name, "url": url}
        if note:
            link["note"] = note
        tagged = _affiliate_url(aff.get(provider))
        if tagged:
            link["affiliate"] = {"url": tagged}
        return link

    netflix_url = deep.get("netflix") or f"https://www.netflix.com/search?q={q}"
    hbo_url = deep.get("hbo") or f"https://www.hbomax.com/?q={q}"
    disney_url = deep.get("disney") or f"https://www.disneyplus.com/search?q={q}"

    official_name = (official or {}).get("name") or ""
    official_url = (official or {}).get("url") or ""
    extra = None
    if official_url:
        lowered = official_name.lower()
        if "disney" in lowered:
            disney_url = official_url
        elif "netflix" in lowered:
            netflix_url = official_url
        elif "hbo" in lowered or lowered == "max":
            hbo_url = official_url
        else:
            extra = chip("official", official_name, official_url)

    watch = [
        chip("netflix", "Netflix", netflix_url),
        chip("hbo", "HBO", hbo_url),
        chip("disney", "Disney+", disney_url),
    ]
    if extra:
        watch.append(extra)

    q_buy = quote_plus(f"{show_name} complete series")
    buy = [
        chip("amazon", "Amazon", f"https://www.amazon.com/s?k={q_buy}"),
        chip("apple", "Apple TV", f"https://tv.apple.com/search?term={q}"),
        chip("google", "Google Play", f"https://play.google.com/store/search?q={q}&c=movies"),
    ]
    return {"watch": watch, "buy": buy}


LOGO_ONLY_PROVIDERS = frozenset({"netflix", "hbo", "disney", "amazon", "apple", "google"})


def stream_icon_html(provider: str, *, prefix: str = "") -> str:
    """Brand wordmark as <img> — sized in CSS per provider."""
    icons = {
        "netflix": "netflix.svg",
        "hbo": "hbo.svg",
        "disney": "disney.svg",
        "amazon": "amazon.svg",
        "apple": "apple.svg",
        "google": "google.svg",
        "official": "official.svg",
    }
    file = icons.get(provider) or icons["official"]
    return (
        f'<img class="watch-logo" src="{prefix}icons/{file}" alt="" '
        f'loading="lazy" decoding="async" />'
    )


def stream_chip_html(link: dict, *, prefix: str = "") -> str:
    note = (
        f' <span class="watch-chip-note">{esc(link["note"])}</span>' if link.get("note") else ""
    )
    aria = link["name"]
    if link.get("note"):
        aria = f"{link['name']} — {link['note']}"
    aria += " (opens in a new tab)"
    icon = stream_icon_html(link["id"], prefix=prefix)
    name_html = (
        ""
        if link["id"] in LOGO_ONLY_PROVIDERS
        else f'<span class="watch-chip-name">{esc(link["name"])}</span>'
    )
    return (
        f'<a class="watch-chip" data-provider="{esc(link["id"])}" href="{esc(outbound_href(link))}" '
        f'target="_blank" rel="{esc(outbound_rel(link))}" aria-label="{esc(aria)}">'
        f"{icon}{name_html}{note}"
        f'<span class="watch-ext" aria-hidden="true">↗</span></a>'
    )


def stream_box_html(show_id: str, show_name: str, *, prefix: str = "") -> str:
    data = stream_links_for(show_id, show_name)
    if not data:
        return ""
    watch_chips = "".join(stream_chip_html(link, prefix=prefix) for link in data["watch"])
    buy_chips = "".join(stream_chip_html(link, prefix=prefix) for link in data["buy"])
    has_aff = any(
        _affiliate_url(link.get("affiliate")) for link in data["watch"] + data["buy"]
    )
    disclose = (
        '<p class="watch-disclose">Some links may earn us a commission — same price to you.</p>'
        if has_aff
        else ""
    )
    return f"""
  <section class="wrap watch-box" aria-label="Where to watch or buy {esc(show_name)}">
    <div class="watch-col">
      <h2 class="watch-heading">📺 Where to watch</h2>
      <p class="watch-sub">Netflix, HBO or Disney+ — catalogs differ by country.</p>
      <div class="watch-chips">{watch_chips}</div>
    </div>
    <div class="watch-col">
      <h2 class="watch-heading">🛒 Where to buy</h2>
      <p class="watch-sub">Digital seasons or a box set to keep.</p>
      <div class="watch-chips">{buy_chips}</div>
    </div>
    {disclose}
  </section>
"""


def watch_action(show_id: str, show_name: str) -> dict | None:
    data = stream_links_for(show_id, show_name)
    if not data or not data["watch"]:
        return None
    return {"@type": "WatchAction", "target": outbound_href(data["watch"][0])}


# ── data payloads ─────────────────────────────────────────────────────────────


# Show cards page through this many moments per theme; episode pages keep all.
LISTING_INSTANCE_CAP = 5


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
    shown = instances if with_instances else instances[:LISTING_INSTANCE_CAP]
    if shown and (with_instances or len(shown) > 1):
        out["instances"] = [
            {
                "kind": inst.get("kind"),
                "speaker": inst.get("speaker"),
                "text": inst.get("text"),
            }
            for inst in shown
        ]
    return out


def load_stills() -> dict:
    global _STILLS
    if _STILLS is None:
        _STILLS = json.loads(STILLS_PATH.read_text()) if STILLS_PATH.exists() else {}
    return _STILLS


def stills_for(show_id: str) -> dict:
    return load_stills().get(show_id) or {}


def attach_still(row: dict, show_id: str) -> dict:
    still = stills_for(show_id).get(str(row["code"]))
    if not still:
        return row
    medium = still.get("medium") or still.get("original")
    original = still.get("original") or still.get("medium")
    if medium:
        row["still"] = medium
    if original and original != medium:
        row["stillFull"] = original
    return row


def cover_url(show_id: str, ep: dict | None = None, *, prefix: str = "") -> str:
    if ep:
        still = ep.get("stillFull") or ep.get("still")
        if still:
            return still
    return f"{prefix}covers/{show_id}.jpg"


def og_image_url(show_id: str, ep: dict | None = None) -> str:
    if ep:
        still = ep.get("stillFull") or ep.get("still")
        if still:
            return still
    return f"{SITE}/covers/{show_id}.jpg"


def slim(ratings: dict, show_id: str, *, with_instances: bool = False) -> dict:
    episodes = []
    for e in ratings["episodes"]:
        themes = e.get("themes") or {"fine": [], "watch": [], "watch_detail": []}
        episodes.append(
            attach_still(
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
                    "why": e.get("why"),
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
                },
                show_id,
            )
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
    title = display_title(ep["title"])
    graph = [
        {
            "@type": "TVEpisode",
            "@id": f"{url}#episode",
            "url": url,
            "name": display_title(title),
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
            **(
                {"potentialAction": watch_action(show_id, show_name)}
                if watch_action(show_id, show_name)
                else {}
            ),
        },
        {
            "@type": "Review",
            "@id": f"{url}#review",
            "url": url,
            "name": f"Is {show_name} {ep_label(ep)} OK for kids?",
            "itemReviewed": {"@id": f"{url}#episode"},
            "reviewBody": re.sub(r"<[^>]+>", "", episode_prose(show_name, ep)).strip(),
            # overall is an unsafety score (5 = hard pass). Schema.org stars
            # read as quality, so publish the inverted kid-fit score instead.
            "reviewRating": {
                "@type": "Rating",
                "ratingValue": max(1, 6 - int(ep.get("overall") or 1)),
                "bestRating": 5,
                "worstRating": 1,
                "alternateName": ep.get("verdict") or "",
                "description": "Kid-fit score (5 = all clear, 1 = hard pass)",
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
    stream_box = stream_box_html(show_id, show_name, prefix="../../")
    n = 0
    for i, ep in enumerate(eps):
        code = safe_code(ep["code"])
        prev_code = safe_code(eps[i - 1]["code"]) if i > 0 else None
        next_code = safe_code(eps[i + 1]["code"]) if i + 1 < len(eps) else None
        title = display_title(ep["title"])
        label = ep_label(ep)
        url = f"{SITE}/ep/{show_id}/{code}.html"
        bkey = bucket_of(ep)
        badge_cls, badge_text = BUCKET_BADGE[bkey]
        desc = meta_description(show_name, ep)
        page_title = f"Is {show_name} {label} OK for Kids?"
        if len(page_title) + len(title) < 66:
            page_title = f"{page_title} {title}"

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
        hero_src = cover_url(show_id, ep, prefix="../../")
        hero_og = og_image_url(show_id, ep)
        hero_alt = title if ep.get("still") or ep.get("stillFull") else f"{show_name} cover art"

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
  <meta property="og:image" content="{esc(hero_og)}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{esc(page_title)}" />
  <meta name="twitter:description" content="{esc(desc)}" />
{extra_head(hero_og)}  {FONTS}
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
          <img src="{esc(hero_src)}" alt="{esc(hero_alt)}" width="1280" height="720" loading="eager" decoding="async" referrerpolicy="no-referrer" />
        </div>
        <div class="ep-hero-body">
          <div class="ep-meta">
            <span class="badge">🎞️ {esc(label)}</span>
            <span class="{badge_cls}">{esc(badge_text)}</span>
          </div>
          <p class="ep-show">{esc(show_name)}</p>
          <p class="ep-kicker">Is {esc(show_name)} {esc(label)} OK for kids?</p>
          <h1>{esc(title)}</h1>
          {summary}
          {fit_meter_html(ep)}
        </div>
      </div>
    </header>
{stream_box}
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

      <p class="ep-related">
        <a href="../../guides/{esc(show_id)}.html">What to watch in {esc(show_name)}</a>
        · <a href="../../guides/{esc(show_id)}-season-{esc(ep.get("season"))}.html">{esc(season_label(ep.get("season"), show_id))} guide</a>
      </p>
      <p class="ep-foot-note">{esc(BRAND)} · {esc(TAGLINE)} · Informal parent guidance, not an official rating.</p>
    </main>
{site_footer("../../")}
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
            f'<span class="ep-index-title">{esc(display_title(ep["title"]))}</span></a> '
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
            **(
                {"potentialAction": watch_action(show_id, payload["show"])}
                if watch_action(show_id, payload["show"])
                else {}
            ),
        },
        {
            "@type": "ItemList",
            "name": f"{payload['show']} seasons rated for kids",
            "numberOfItems": len({str(ep.get("season")) for ep in episodes}),
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": i + 1,
                    "url": f"{SITE}/guides/{show_id}-season-{season}.html",
                    "name": f"Is {payload['show']} {season_label(season, show_id)} OK for kids?",
                }
                for i, season in enumerate(
                    sorted(
                        {str(ep.get("season")) for ep in episodes},
                        key=lambda s: int(s) if str(s).isdigit() else 99,
                    )
                )
            ],
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Shows", "item": f"{SITE}/"},
                {"@type": "ListItem", "position": 2, "name": payload["show"], "item": url},
            ],
        },
        faq_jsonld(show_faqs(show_id, payload["show"], mix)),
    ]
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)


def write_show_html(show_id: str, payload: dict, mix: dict) -> None:
    meta = SHOW_PAGE.get(show_id, {"name": payload["show"], "h1": payload["show"]})
    name = meta["name"]
    url = f"{SITE}/{show_id}.html"
    total = mix["total"] or 1
    desc = clip_meta(
        f"Is {name} OK for kids? {'All ' if mix['total'] != 1 else ''}{ep_count(mix['total'])} rated 1–5 for violence, sex and "
        f"language — {round(100 * mix['safe'] / total)}% all clear, "
        f"{round(100 * mix['maybe'] / total)}% gray area, "
        f"{round(100 * mix['skip'] / total)}% hard pass, with the exact moments quoted."
    )
    page_title = f"Is {name} OK for Kids? Episode Parents Guide"

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
  <meta name="twitter:title" content="{esc(page_title)}" />
  <meta name="twitter:description" content="{esc(desc)}" />
{extra_head(f"{SITE}/covers/{show_id}.jpg")}  {FONTS}
  <link rel="stylesheet" href="friends.css" />
  <script type="application/ld+json">{show_jsonld(show_id, payload, mix)}</script>
</head>
<body>
  <div class="confetti" aria-hidden="true"></div>

  <nav class="topnav wrap">
    <a class="back-home" href="index.html">← All shows</a>
    <a class="back-home subtle" href="guides/{esc(show_id)}.html">What to watch</a>
  </nav>

  <header class="hero">
    <div class="wrap hero-inner">
      <div class="hero-copy">
        <h1>Is {esc(name)} OK for kids?</h1>
        <p class="tagline">
          {meta["h1"]} — every episode scored so you can decide
          <strong>before you press play</strong>.
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
{stream_box_html(show_id, name)}
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
      We rated {"all " if mix["total"] != 1 else ""}<strong>{ep_count(mix["total"])}</strong> of {esc(name)} for violence, sex and
      language on a 1–5 scale: <strong>{mix["safe"]}</strong> all clear (overall
      1–2/5), <strong>{mix["maybe"]}</strong> in the gray area (3/5) and
      <strong>{mix["skip"]}</strong> a hard pass for little kids (4–5/5).
    </p>
    <p>
      Each episode page lists every watch-for theme — Sex &amp; hookups, Nudity &amp; bodies,
      Porn / strippers, Swearing, Violence &amp; death, Affairs / cheating, Suicide / self-harm,
      Alcohol / Drugs, Gay / Lesbian, Fat-shaming, Slut-shaming and Racism — with a count of how
      many times it comes up and the exact quote or scene description behind each mention.
      Start with the <a href="guides/{esc(show_id)}.html">safest {esc(name)} episodes</a> if you
      want something tonight.
    </p>
    <p>
      Ready to press play? Stream on <strong>Netflix</strong>, <strong>HBO</strong> or
      <strong>Disney+</strong>, or buy from Amazon, Apple TV and Google Play.
    </p>
  </section>
{faq_html(show_faqs(show_id, name, mix))}

  <section class="wrap ep-index" aria-label="All {esc(name)} episodes">
    <h2>All {esc(name)} episodes</h2>
    <ul class="ep-index-list">
      {episode_index_html(show_id, payload)}
    </ul>
  </section>

{site_footer()}

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
            f"- [{s['name']}]({SITE}/{sid}.html): {ep_count(mix['total'])} — "
            f"{round(100 * mix['safe'] / total)}% all clear, "
            f"{round(100 * mix['maybe'] / total)}% gray area, "
            f"{round(100 * mix['skip'] / total)}% hard pass. "
            f"Full text index: [{sid}.md]({SITE}/llms/{sid}.md)"
        )
    lines += [
        "",
        "## Machine-readable data",
        "",
        f"- [What to watch]({SITE}/guides/): safest episodes and skip lists per show.",
        f"- [How we rate]({SITE}/about.html): scoring method and disclaimer.",
        f"- [Show catalogue JSON]({SITE}/shows.json): shows, covers and rating mix.",
        "- Per-show ratings JSON: " + f"{SITE}/data/<show-id>.js (window.RATINGS payload).",
        "",
        "## Notes",
        "",
        "- This is informal parental guidance, not an official rating body.",
        "- Quotes are shown verbatim from the transcript, including profanity and slurs.",
        f"- {TAGLINE}",
        "",
    ]
    (WEB / "llms.txt").write_text("\n".join(lines))
    (WEB / "llm.txt").write_text(
        f"# {BRAND}\n\nSee {SITE}/llms.txt for the full agent index.\n"
    )


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

    rows = []
    for s in live:
        mix = mixes[s["id"]]
        total = mix["total"] or 1
        rows.append(
            f'<li><a href="{esc(s["id"])}.html"><strong>{esc(s["name"])}</strong></a> — '
            f'{ep_count(mix["total"])} rated: {round(100 * mix["safe"] / total)}% all clear, '
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
      Start with <a href="guides/index.html">what to watch tonight</a> if you want the safest
      episodes first.
    </p>
    <ul class="seo-show-list">
      {"".join(rows)}
    </ul>
    <p>Agents and LLMs: see <a href="llms.txt">llms.txt</a> for a machine-readable index.</p>
  </section>
{faq_html(home_faqs())}
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
                "logo": f"{SITE}/icon-192.png",
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
            faq_jsonld(home_faqs()),
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
    text = _replace_block(text, "SHOWS", shows_block)
    text = _replace_block(text, "JSONLD", script)
    path.write_text(text)
    print(f"Updated index.html ({len(live)} live shows, {total_eps} episodes)")


def _pick_episodes(episodes: list[dict], bucket: str, limit: int) -> list[dict]:
    if bucket == "safe":
        pool = [e for e in episodes if int(e.get("overall") or 1) <= 2]
        pool.sort(key=lambda e: (int(e["overall"]), str(e.get("season")), str(e.get("episode"))))
    elif bucket == "skip":
        pool = [e for e in episodes if int(e.get("overall") or 1) >= 4]
        pool.sort(
            key=lambda e: (
                -int(e["overall"]),
                -len(details_of(e)),
                str(e.get("season")),
            )
        )
    else:
        pool = [e for e in episodes if int(e.get("overall") or 1) == 3]
        pool.sort(key=lambda e: (str(e.get("season")), str(e.get("episode"))))
    return pool[:limit]


GUIDE_SCORE_PILL = {
    "safe": ("ep-card-score safe", "✅ All clear"),
    "maybe": ("ep-card-score maybe", "🤔 Gray area"),
    "skip": ("ep-card-score skip", "🚫 Hard pass"),
}


def _ep_card_html(show_id: str, ep: dict) -> str:
    code = safe_code(ep["code"])
    bkey = bucket_of(ep)
    pill_cls, pill_text = GUIDE_SCORE_PILL[bkey]
    thumb = ""
    if ep.get("still"):
        thumb = (
            f'<span class="ep-card-still"><img src="{esc(ep["still"])}" alt="" '
            f'width="480" height="270" loading="lazy" decoding="async" '
            f'referrerpolicy="no-referrer" /></span>'
        )
    themes = [d["theme"] for d in details_of(ep)]
    if themes:
        chips = "".join(f'<span class="ep-theme-chip">{esc(t)}</span>' for t in themes[:3])
        if len(themes) > 3:
            chips += f'<span class="ep-theme-chip more">+{len(themes) - 3} more</span>'
        sub = f'<span class="ep-card-themes">{chips}</span>'
    elif ep.get("why"):
        sub = f'<span class="ep-card-why">{esc(clip_meta(ep["why"], 120))}</span>'
    elif bkey == "safe":
        sub = '<span class="ep-card-why">Nothing adult flagged in the transcript.</span>'
    else:
        sub = ""
    return (
        f'<li><a class="ep-card" href="../ep/{esc(show_id)}/{esc(code)}.html">'
        f"{thumb}"
        f'<span class="ep-card-main">'
        f'<span class="ep-card-top"><span class="ep-card-code">{esc(ep_label(ep))}</span>'
        f'<span class="ep-card-title">{esc(display_title(ep["title"]))}</span></span>'
        f"{sub}"
        f"</span>"
        f'<span class="{pill_cls}">{pill_text} · {ep["overall"]}/5</span>'
        f"</a></li>"
    )


def _ep_rows_html(show_id: str, episodes: list[dict]) -> str:
    if not episodes:
        return '<p class="ep-cards-empty">None in this bucket.</p>'
    rows = "\n      ".join(_ep_card_html(show_id, ep) for ep in episodes)
    return f'<ul class="ep-cards">\n      {rows}\n    </ul>'


def _static_page(
    *,
    url: str,
    title: str,
    desc: str,
    image: str,
    css_href: str,
    jsonld: dict,
    body: str,
    prefix: str,
) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(desc)}" />
  <link rel="canonical" href="{esc(url)}" />
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large" />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="{esc(BRAND)}" />
  <meta property="og:title" content="{esc(title)}" />
  <meta property="og:description" content="{esc(desc)}" />
  <meta property="og:url" content="{esc(url)}" />
  <meta property="og:image" content="{esc(image)}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{esc(title)}" />
  <meta name="twitter:description" content="{esc(desc)}" />
{extra_head(image)}  {FONTS}
  <link rel="stylesheet" href="{css_href}" />
  <script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>
</head>
<body>
  <div class="confetti" aria-hidden="true"></div>
{body}
{site_footer(prefix)}
</body>
</html>
"""


def write_about_page() -> None:
    url = f"{SITE}/about.html"
    title = "How We Rate TV for Kids"
    desc = clip_meta(
        "Watch With The Kids scores every episode 1–5 for violence, sex and language from the "
        "transcript, then quotes the exact moments so parents can decide before play."
    )
    themes = [
        "Sex & hookups",
        "Nudity & bodies",
        "Porn / strippers",
        "Swearing",
        "Violence & death",
        "Affairs / cheating",
        "Suicide / self-harm",
        "Alcohol / Drugs",
        "Gay / Lesbian",
        "Fat-shaming",
        "Slut-shaming",
        "Racism",
    ]
    theme_chips = "".join(f'<li><span class="about-theme">{esc(t)}</span></li>' for t in themes)

    def dots(n: int) -> str:
        bits = []
        for i in range(1, 6):
            cls = "on go" if i <= 2 else "on caution" if i == 3 else "on stop"
            bits.append(f'<i class="{cls}"></i>' if i <= n else "<i></i>")
        return "".join(bits)

    body = f"""  <nav class="topnav wrap">
    <a class="back-home" href="index.html">← All shows</a>
    <a class="back-home subtle" href="guides/index.html">What to watch</a>
  </nav>
  <header class="hero">
    <div class="wrap hero-inner">
      <div class="hero-copy">
        <p class="eyebrow">The method behind every episode page</p>
        <h1>How we rate TV for kids</h1>
        <p class="tagline">
          Informal parent guidance — not an official ratings board. {esc(TAGLINE)}
        </p>
        <div class="hero-pills">
          <span>✅ 1–2 all clear</span>
          <span>🤔 3 gray area</span>
          <span>🚫 4–5 hard pass</span>
        </div>
      </div>
      <aside class="hero-card about-demo" aria-hidden="true">
        <p class="about-demo-kicker">Example episode</p>
        <div class="about-demo-row">
          <span>Violence</span>
          <span class="about-dots">{dots(3)}</span>
          <b>3</b>
        </div>
        <div class="about-demo-row">
          <span>Sex</span>
          <span class="about-dots">{dots(2)}</span>
          <b>2</b>
        </div>
        <div class="about-demo-row">
          <span>Language</span>
          <span class="about-dots">{dots(4)}</span>
          <b>4</b>
        </div>
        <div class="about-demo-overall">
          <span>Overall = the highest</span>
          <strong>4</strong>
          <span class="bucket-pill skip">🚫 Hard pass</span>
        </div>
      </aside>
    </div>
  </header>
  <main class="wrap about-page">
    <p class="about-lead">
      Every episode gets three scores: <strong>violence</strong>, <strong>sex</strong> and
      <strong>language</strong>, each from 1 (none) to 5 (heavy). The overall kid-rating is the
      <strong>highest of the three</strong>, so one spicy category is enough to bump the episode.
    </p>
    <section class="about-buckets" aria-label="The 1–5 scale">
      <article class="about-bucket safe">
        <span class="about-bucket-emoji" aria-hidden="true">✅</span>
        <p class="about-bucket-range">1–2</p>
        <h2>All clear</h2>
        <p>Fine for most family couches.</p>
      </article>
      <article class="about-bucket maybe">
        <span class="about-bucket-emoji" aria-hidden="true">🤔</span>
        <p class="about-bucket-range">3</p>
        <h2>Gray area</h2>
        <p>Preview first — fine for older kids depending on your rules.</p>
      </article>
      <article class="about-bucket skip">
        <span class="about-bucket-emoji" aria-hidden="true">🚫</span>
        <p class="about-bucket-range">4–5</p>
        <h2>Hard pass</h2>
        <p>Too spicy for little kids.</p>
      </article>
    </section>
    <section class="about-section">
      <h2>What we flag</h2>
      <p>
        Each theme lists how many times it comes up and the quote or scene behind it —
        shown verbatim from the transcript, including profanity and slurs.
      </p>
      <ul class="about-themes">
        {theme_chips}
      </ul>
    </section>
    <section class="about-section">
      <h2>Where the data comes from</h2>
      <div class="about-steps">
        <article>
          <span aria-hidden="true">📜</span>
          <h3>Transcripts</h3>
          <p>Keyword signals plus curated overrides, scored episode by episode.</p>
        </article>
        <article>
          <span aria-hidden="true">📈</span>
          <h3>Highest wins</h3>
          <p>Overall is the max of violence, sex and language — not an average.</p>
        </article>
        <article>
          <span aria-hidden="true">💬</span>
          <h3>Quoted moments</h3>
          <p>A screening aid, not a substitute for watching with your own kids.</p>
        </article>
      </div>
    </section>
    <a class="about-cta" href="guides/index.html">
      <span class="about-cta-stack" aria-hidden="true">
        <img src="covers/spongebob.jpg" alt="" width="320" height="180" />
        <img src="covers/young-sheldon.jpg" alt="" width="320" height="180" />
        <img src="covers/seinfeld.jpg" alt="" width="320" height="180" />
        <img src="covers/big-bang-theory.jpg" alt="" width="320" height="180" />
      </span>
      <span class="about-cta-copy">
        <span class="about-cta-kicker">Ready to pick an episode</span>
        <strong>See what to watch tonight</strong>
        <span class="about-cta-sub">Safest episodes first. Skip lists for the spicy ones.</span>
        <span class="about-cta-btn">Open the guides →</span>
      </span>
    </a>
  </main>"""
    jsonld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "AboutPage",
                "url": url,
                "name": title,
                "description": desc,
                "isPartOf": {"@id": f"{SITE}/#website"},
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Shows", "item": f"{SITE}/"},
                    {"@type": "ListItem", "position": 2, "name": "How we rate", "item": url},
                ],
            },
        ],
    }
    (WEB / "about.html").write_text(
        _static_page(
            url=url,
            title=title,
            desc=desc,
            image=f"{SITE}/covers/friends.jpg",
            css_href="friends.css",
            jsonld=jsonld,
            body=body,
            prefix="",
        )
    )


def _mix_pcts(mix: dict) -> tuple[int, int, int]:
    total = mix["total"] or 1
    safe_pct = round(100 * mix["safe"] / total)
    maybe_pct = round(100 * mix["maybe"] / total)
    skip_pct = max(0, 100 - safe_pct - maybe_pct)
    if safe_pct + maybe_pct > 100:
        maybe_pct = max(0, 100 - safe_pct)
        skip_pct = 0
    return safe_pct, maybe_pct, skip_pct


def write_guides_hub(shows: list[dict], mixes: dict[str, dict]) -> None:
    url = f"{SITE}/guides/"
    title = "What to Watch With Kids Tonight"
    desc = clip_meta(
        "Safest episodes to watch with kids — and the ones to skip — across Friends, The Office, "
        "SpongeBob, Seinfeld and more, scored 1–5 for violence, sex and language."
    )
    ranked = sorted(
        (s for s in shows if s["id"] in mixes),
        key=lambda s: (
            -mixes[s["id"]]["safe"] / (mixes[s["id"]]["total"] or 1),
            -mixes[s["id"]]["safe"],
            s["name"],
        ),
    )

    def group_of(sid: str) -> str:
        mix = mixes[sid]
        total = mix["total"] or 1
        if mix["safe"] / total >= 0.5:
            return "safe"
        if mix["skip"] / total >= 0.7:
            return "skip"
        return "maybe"

    def card_html(s: dict, *, eager: bool) -> str:
        sid = s["id"]
        mix = mixes[sid]
        safe_pct, maybe_pct, skip_pct = _mix_pcts(mix)
        total = mix["total"] or 1
        if mix["safe"] / total >= 0.5:
            badge = '<span class="guide-badge safe">Kid-friendlier</span>'
            stat = f'{mix["safe"]} of {mix["total"]} episodes are all clear'
        elif mix["skip"] / total >= 0.7:
            badge = '<span class="guide-badge skip">Mostly skip</span>'
            stat = (
                f'Only {mix["safe"]} of {mix["total"]} episodes are all clear'
                if mix["safe"]
                else "No all-clear episodes — after-bedtime territory"
            )
        else:
            badge = '<span class="guide-badge maybe">Preview first</span>'
            stat = (
                f'{mix["safe"]} of {mix["total"]} episodes are all clear'
                if mix["safe"]
                else "No all-clear episodes — preview every one"
            )
        return (
            f'<li><a class="guide-card" href="{esc(sid)}.html">'
            f'<span class="guide-cover">'
            f'<img src="../covers/{esc(sid)}.jpg" alt="" width="640" height="360" '
            f'loading="{"eager" if eager else "lazy"}" /></span>'
            f'<span class="guide-body">'
            f"{badge}"
            f"<h2>{esc(s['name'])}</h2>"
            f'<p class="guide-stat">{esc(stat)}</p>'
            f'<span class="guide-mix" aria-hidden="true">'
            f'<span class="guide-seg safe" style="flex-grow:{safe_pct}"></span>'
            f'<span class="guide-seg maybe" style="flex-grow:{maybe_pct}"></span>'
            f'<span class="guide-seg skip" style="flex-grow:{skip_pct}"></span>'
            f"</span>"
            f'<p class="guide-legend"><strong>{safe_pct}%</strong> all clear · '
            f"{maybe_pct}% gray · {skip_pct}% skip</p>"
            f'<span class="guide-cta">See the safest episodes →</span>'
            f"</span></a></li>"
        )

    groups = [
        (
            "safe",
            "🛋️",
            "Easy wins",
            "Most episodes are all clear — pick almost anything and relax.",
        ),
        (
            "maybe",
            "🤔",
            "Depends on the episode",
            "Some gentle ones, some spicy ones — check the list before play.",
        ),
        (
            "skip",
            "🚫",
            "Mostly not for little kids",
            "A few episodes work; the rest are for after bedtime.",
        ),
    ]
    sections = []
    eager_budget = 4
    n_cards = 0
    for key, emoji, heading, sub in groups:
        members = [s for s in ranked if group_of(s["id"]) == key]
        if not members:
            continue
        cards = []
        for s in members:
            cards.append(card_html(s, eager=eager_budget > 0))
            eager_budget -= 1
        n_cards += len(cards)
        sections.append(
            f'    <section class="guide-group" aria-label="{esc(heading)}">\n'
            f'      <header class="guide-group-head {key}">\n'
            f'        <span class="guide-section-emoji" aria-hidden="true">{emoji}</span>\n'
            f'        <div class="guide-section-copy">\n'
            f"          <h2>{esc(heading)}</h2>\n"
            f"          <p>{esc(sub)}</p>\n"
            f"        </div>\n"
            f'        <span class="guide-section-count">{len(members)} shows</span>\n'
            f"      </header>\n"
            f'      <ul class="guide-grid">\n        {"".join(cards)}\n      </ul>\n'
            f"    </section>"
        )
    stack = "".join(
        f'<img src="../covers/{esc(s["id"])}.jpg" alt="" width="480" height="270" />'
        for s in ranked[:4]
    )
    body = f"""  <nav class="topnav wrap">
    <a class="back-home" href="../index.html">← All shows</a>
    <a class="back-home subtle" href="../about.html">How we rate</a>
  </nav>
  <header class="hero">
    <div class="wrap hero-inner">
      <div class="hero-copy">
        <p class="eyebrow">Safest episodes · Skip lists</p>
        <h1>What to watch with the kids</h1>
        <p class="tagline">Every episode scored 1–5 for violence, sex and language. Pick a show — the safest episodes are listed first.</p>
        <div class="hero-pills">
          <span>✅ Safest first</span>
          <span>🤔 Gray area</span>
          <span>🚫 Hard pass</span>
        </div>
      </div>
      <aside class="hero-card" aria-hidden="true">
        <div class="guide-hero-covers">{stack}</div>
      </aside>
    </div>
  </header>
  <main class="wrap guide-sections">
{chr(10).join(sections)}
  </main>"""
    jsonld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "CollectionPage",
                "url": url,
                "name": title,
                "description": desc,
            },
            {
                "@type": "ItemList",
                "name": "What to watch guides",
                "numberOfItems": n_cards,
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": i + 1,
                        "name": s["name"],
                        "url": f"{SITE}/guides/{s['id']}.html",
                    }
                    for i, s in enumerate(ranked)
                ],
            },
        ],
    }
    out_dir = WEB / "guides"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "index.html").write_text(
        _static_page(
            url=url,
            title=title,
            desc=desc,
            image=f"{SITE}/covers/friends.jpg",
            css_href="../friends.css",
            jsonld=jsonld,
            body=body,
            prefix="../",
        )
    )


def write_show_guide(show_id: str, payload: dict, mix: dict) -> list[tuple[str, str]]:
    name = payload["show"]
    eps = payload["episodes"]
    url = f"{SITE}/guides/{show_id}.html"
    title = f"What to Watch in {name} With Kids"
    desc = clip_meta(
        f"Safest {name} episodes for kids, plus the hard-pass list. "
        f"{mix['safe']} all clear, {mix['maybe']} gray area, {mix['skip']} skip — scored 1–5."
    )
    safe = _pick_episodes(eps, "safe", 25)
    skip = _pick_episodes(eps, "skip", 15)
    maybe = _pick_episodes(eps, "maybe", 8)
    seasons = sorted(
        {str(ep.get("season")) for ep in eps},
        key=lambda s: int(s) if s.isdigit() else 99,
    )
    season_links = " · ".join(
        f'<a href="{esc(show_id)}-season-{esc(season)}.html">{esc(season_label(season, show_id))}</a>'
        for season in seasons
    )
    if mix["safe"] == 0:
        safe_intro = (
            f"None of the {mix['total']} {esc(name)} episodes we rated land in the all-clear "
            "bucket (overall 1–2/5). If you still want to try, preview a gray-area episode first."
        )
    else:
        safe_intro = (
            f"{mix['safe']} of {mix['total']} {esc(name)} episodes score all-clear. "
            "These are the gentlest to start with."
        )
    skip_intro = (
        f"{mix['skip']} episodes are a hard pass for little kids (overall 4–5/5). "
        "The spiciest are listed below."
        if mix["skip"]
        else f"No {esc(name)} episodes scored a hard pass."
    )
    body = f"""  <nav class="topnav wrap">
    <a class="back-home" href="../{esc(show_id)}.html">← {esc(name)}</a>
    <a class="back-home subtle" href="index.html">All guides</a>
  </nav>
  <header class="hero">
    <div class="wrap hero-inner">
      <div class="hero-copy">
        <p class="eyebrow">{mix["total"]} episodes rated 1–5</p>
        <h1>What to watch in {esc(name)} with kids</h1>
        <p class="tagline">
          Start with an all-clear episode, or check the skip list before movie night.
        </p>
        <div class="hero-pills" aria-hidden="true">
          <span>✅ {mix["safe"]} all clear</span>
          <span>🤔 {mix["maybe"]} gray area</span>
          <span>🚫 {mix["skip"]} hard pass</span>
        </div>
        <p class="season-jump">By season: {season_links}</p>
      </div>
      <aside class="hero-card">
        <div class="hero-cover">
          <img src="../covers/{esc(show_id)}.jpg" alt="{esc(name)} cover art" width="1920" height="1080" />
        </div>
        <p class="disclaimer"><a href="../{esc(show_id)}.html">Browse every {esc(name)} episode →</a></p>
      </aside>
    </div>
  </header>
  <main class="wrap guide-sections">
    <section class="guide-section" aria-label="Safest {esc(name)} episodes">
      <header class="guide-section-head safe">
        <span class="guide-section-emoji" aria-hidden="true">✅</span>
        <div class="guide-section-copy">
          <h2>Start here — safest {esc(name)} episodes</h2>
          <p>{safe_intro}</p>
        </div>
        <span class="guide-section-count">{mix["safe"]}</span>
      </header>
      {_ep_rows_html(show_id, safe)}
    </section>
    <section class="guide-section" aria-label="Gray-area {esc(name)} episodes">
      <header class="guide-section-head maybe">
        <span class="guide-section-emoji" aria-hidden="true">🤔</span>
        <div class="guide-section-copy">
          <h2>Gray area — preview first</h2>
          <p>Overall 3/5. Fine for some families, not for others — read the flags before play.</p>
        </div>
        <span class="guide-section-count">{mix["maybe"]}</span>
      </header>
      {_ep_rows_html(show_id, maybe)}
    </section>
    <section class="guide-section" aria-label="{esc(name)} episodes to skip">
      <header class="guide-section-head skip">
        <span class="guide-section-emoji" aria-hidden="true">🚫</span>
        <div class="guide-section-copy">
          <h2>{esc(name)} episodes to skip with little kids</h2>
          <p>{skip_intro}</p>
        </div>
        <span class="guide-section-count">{mix["skip"]}</span>
      </header>
      {_ep_rows_html(show_id, skip)}
    </section>
  </main>"""
    jsonld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "ItemList",
                "name": title,
                "url": url,
                "description": desc,
                "numberOfItems": len(safe),
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": i + 1,
                        "url": f"{SITE}/ep/{show_id}/{safe_code(ep['code'])}.html",
                        "name": f"{ep_label(ep)} {display_title(ep['title'])}",
                    }
                    for i, ep in enumerate(safe)
                ],
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Shows", "item": f"{SITE}/"},
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": name,
                        "item": f"{SITE}/{show_id}.html",
                    },
                    {"@type": "ListItem", "position": 3, "name": "What to watch", "item": url},
                ],
            },
            faq_jsonld(
                [
                    (
                        f"Which {name} episodes are OK for kids?",
                        f"{mix['safe']} of {mix['total']} score all-clear (1–2/5). "
                        f"{mix['skip']} are a hard pass (4–5/5).",
                    ),
                    (
                        f"Is {name} OK for kids overall?",
                        f"It depends on the episode. {round(100 * mix['safe'] / (mix['total'] or 1))}% "
                        "are all clear; check the lists on this page before you press play.",
                    ),
                ]
            ),
        ],
    }
    (WEB / "guides" / f"{show_id}.html").write_text(
        _static_page(
            url=url,
            title=title,
            desc=desc,
            image=f"{SITE}/covers/{show_id}.jpg",
            css_href="../friends.css",
            jsonld=jsonld,
            body=body,
            prefix="../",
        )
    )
    urls = [(url, "0.85")]
    urls.extend(write_season_guides(show_id, payload, mix))
    return urls


def write_season_guides(show_id: str, payload: dict, mix: dict) -> list[tuple[str, str]]:
    name = payload["show"]
    grouped: dict[str, list[dict]] = {}
    for ep in payload["episodes"]:
        grouped.setdefault(str(ep.get("season")), []).append(ep)
    urls: list[tuple[str, str]] = []
    (WEB / "guides").mkdir(exist_ok=True)
    for season, eps in grouped.items():
        smix = episode_mix(eps)
        label = season_label(season, show_id)
        url = f"{SITE}/guides/{show_id}-season-{season}.html"
        title = f"Is {name} {label} OK for Kids?"
        total = smix["total"] or 1
        desc = clip_meta(
            f"Is {name} {label} OK for kids? {smix['total']} episodes rated: "
            f"{smix['safe']} all clear, {smix['maybe']} gray area, {smix['skip']} hard pass."
        )
        body = f"""  <nav class="topnav wrap">
    <a class="back-home" href="{esc(show_id)}.html">← What to watch in {esc(name)}</a>
    <a class="back-home subtle" href="../{esc(show_id)}.html">{esc(name)} all episodes</a>
  </nav>
  <header class="hero">
    <div class="wrap hero-inner">
      <div class="hero-copy">
        <h1>Is {esc(name)} {esc(label)} OK for kids?</h1>
        <p class="tagline">
          {smix["safe"]} all clear · {smix["maybe"]} gray area · {smix["skip"]} hard pass
          across {smix["total"]} episodes.
        </p>
      </div>
    </div>
  </header>
  <main class="wrap">
    <section class="wrap seo-copy">
      <p>
        {esc(label)} of {esc(name)} is
        {round(100 * smix["safe"] / total)}% all clear,
        {round(100 * smix["maybe"] / total)}% gray area and
        {round(100 * smix["skip"] / total)}% a hard pass for little kids.
        Open an episode for the quoted moments.
      </p>
    </section>
    {_ep_rows_html(show_id, eps)}
  </main>"""
        jsonld = {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "TVSeason",
                    "name": f"{name} {label}",
                    "url": url,
                    "seasonNumber": season,
                    "numberOfEpisodes": len(eps),
                    "partOfSeries": {
                        "@type": "TVSeries",
                        "name": name,
                        "url": f"{SITE}/{show_id}.html",
                    },
                    "description": desc,
                },
                {
                    "@type": "ItemList",
                    "name": f"{name} {label} episodes rated for kids",
                    "numberOfItems": len(eps),
                    "itemListElement": [
                        {
                            "@type": "ListItem",
                            "position": i + 1,
                            "url": f"{SITE}/ep/{show_id}/{safe_code(ep['code'])}.html",
                            "name": f"{ep_label(ep)} {display_title(ep['title'])}",
                        }
                        for i, ep in enumerate(eps)
                    ],
                },
                {
                    "@type": "BreadcrumbList",
                    "itemListElement": [
                        {"@type": "ListItem", "position": 1, "name": "Shows", "item": f"{SITE}/"},
                        {
                            "@type": "ListItem",
                            "position": 2,
                            "name": name,
                            "item": f"{SITE}/{show_id}.html",
                        },
                        {
                            "@type": "ListItem",
                            "position": 3,
                            "name": "What to watch",
                            "item": f"{SITE}/guides/{show_id}.html",
                        },
                        {"@type": "ListItem", "position": 4, "name": label, "item": url},
                    ],
                },
            ],
        }
        (WEB / "guides" / f"{show_id}-season-{season}.html").write_text(
            _static_page(
                url=url,
                title=title,
                desc=desc,
                image=f"{SITE}/covers/{show_id}.jpg",
                css_href="../friends.css",
                jsonld=jsonld,
                body=body,
                prefix="../",
            )
        )
        urls.append((url, "0.8"))
    return urls


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
    seen: set[str] = set()
    unique: list[tuple[str, str]] = []
    for loc, prio in urls:
        if loc in seen:
            continue
        seen.add(loc)
        unique.append((loc, prio))
    body = "\n".join(
        f"  <url><loc>{esc(loc)}</loc><lastmod>{today}</lastmod>"
        f"<changefreq>monthly</changefreq><priority>{prio}</priority></url>"
        for loc, prio in unique
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


def build_show(show_id: str, src: Path, sitemap: list[tuple[str, str]]) -> tuple[dict, dict]:
    ratings = json.loads(src.read_text())
    listing = slim(ratings, show_id, with_instances=False)
    full = slim(ratings, show_id, with_instances=True)
    # Guarantee unique episode page codes even if a ratings JSON still has collisions.
    listing["episodes"] = dedupe_codes(listing["episodes"])
    full["episodes"] = dedupe_codes(full["episodes"])
    listing["count"] = len(listing["episodes"])
    full["count"] = len(full["episodes"])
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
    return mix, listing


def main() -> None:
    mixes: dict[str, dict] = {}
    payloads: dict[str, dict] = {}
    sitemap: list[tuple[str, str]] = [(f"{SITE}/", "1.0")]

    if LLM_ROOT.exists():
        shutil.rmtree(LLM_ROOT)
    guides_dir = WEB / "guides"
    if guides_dir.exists():
        shutil.rmtree(guides_dir)
    guides_dir.mkdir()

    ratings_dir = ROOT / "ratings"
    for show_id in READY:
        src = ROOT / "ratings.json" if show_id == "friends" else ratings_dir / f"{show_id}.json"
        if src.exists():
            mix, listing = build_show(show_id, src, sitemap)
            mixes[show_id] = mix
            payloads[show_id] = listing

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

    write_about_page()
    sitemap.append((f"{SITE}/about.html", "0.6"))
    write_guides_hub(shows, mixes)
    sitemap.append((f"{SITE}/guides/", "0.8"))
    for show_id, payload in payloads.items():
        sitemap.extend(write_show_guide(show_id, payload, mixes[show_id]))

    sitemap.append((f"{SITE}/llms.txt", "0.5"))
    for show_id in mixes:
        sitemap.append((f"{SITE}/llms/{show_id}.md", "0.4"))

    write_sitemap(sitemap)
    write_robots()
    write_llms_txt(shows, mixes)
    update_index_html(shows, mixes)

    print(f"Updated shows.js ready flags: {sorted(mixes)}")
    print(f"Sitemap: {len(sitemap)} URLs · robots.txt · llms.txt · llms/*.md · guides + about")


if __name__ == "__main__":
    main()

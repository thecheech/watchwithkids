#!/usr/bin/env python3
"""Build web/data/*.js rating payloads, show HTML pages, ready flags."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
DATA = WEB / "data"
EP_ROOT = WEB / "ep"
DATA.mkdir(exist_ok=True)

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
    "friends": {
        "name": "Friends",
        "h1": 'Friends <span class="pop">🍿</span>',
    },
    "seinfeld": {
        "name": "Seinfeld",
        "h1": 'Seinfeld <span class="pop">🥨</span>',
    },
    "spongebob": {
        "name": "SpongeBob SquarePants",
        "h1": 'SpongeBob <span class="pop">🍍</span>',
    },
    "the-office": {
        "name": "The Office",
        "h1": 'The Office <span class="pop">📎</span>',
    },
    "how-i-met-your-mother": {
        "name": "How I Met Your Mother",
        "h1": 'How I Met Your Mother <span class="pop">☂️</span>',
    },
    "big-bang-theory": {
        "name": "The Big Bang Theory",
        "h1": 'The Big Bang Theory <span class="pop">🔬</span>',
    },
    "young-sheldon": {
        "name": "Young Sheldon",
        "h1": 'Young Sheldon <span class="pop">🧪</span>',
    },
    "malcolm-in-the-middle": {
        "name": "Malcolm in the Middle",
        "h1": 'Malcolm in the Middle <span class="pop">🛼</span>',
    },
    "rick-and-morty": {
        "name": "Rick and Morty",
        "h1": 'Rick and Morty <span class="pop">🌀</span>',
    },
    "family-guy": {
        "name": "Family Guy",
        "h1": 'Family Guy <span class="pop">🐶</span>',
    },
    "south-park": {
        "name": "South Park",
        "h1": 'South Park <span class="pop">🏔️</span>',
    },
    "futurama": {
        "name": "Futurama",
        "h1": 'Futurama <span class="pop">🚀</span>',
    },
}


def slim(ratings: dict, show_id: str) -> dict:
    return {
        "show": ratings["show"],
        "show_id": ratings.get("show_id") or show_id,
        "scale": ratings["scale"],
        "disclaimer": ratings["disclaimer"],
        "count": ratings["count"],
        "episodes": [
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
                "themes": e.get("themes")
                or {
                    "fine": [],
                    "watch": list(e.get("examples") or []),
                    "watch_detail": [],
                },
                "examples": e["examples"],
                "notes": e.get("notes"),
            }
            for e in ratings["episodes"]
        ],
    }


def safe_code(code: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", str(code)).strip("-") or "ep"


def write_episode_pages(show_id: str, payload: dict) -> int:
    """Write one static HTML page per episode under web/ep/<show>/<code>.html."""
    out_dir = EP_ROOT / show_id
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    eps = payload["episodes"]
    show_name = payload["show"]
    cover = f"../../covers/{show_id}.jpg"
    n = 0
    for i, ep in enumerate(eps):
        code = safe_code(ep["code"])
        prev_code = safe_code(eps[i - 1]["code"]) if i > 0 else None
        next_code = safe_code(eps[i + 1]["code"]) if i + 1 < len(eps) else None
        boot = {
            "show": show_name,
            "show_id": show_id,
            "cover": cover,
            "episode": ep,
            "prev": prev_code,
            "next": next_code,
        }
        title = re.sub(r"\s+", " ", ep["title"]).strip()
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title} · {show_name} · Watch With The Kids</title>
  <meta name="description" content="Kid-watch guide for {show_name}: {title}" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@450;600;700&family=Nunito:wght@500;700;800&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="../../friends.css" />
</head>
<body class="ep-page">
  <div class="confetti" aria-hidden="true"></div>
  <div id="episode-root"></div>
  <script>window.EP_PAGE = {json.dumps(boot, ensure_ascii=False)};</script>
  <script src="../../episode.js"></script>
</body>
</html>
"""
        (out_dir / f"{code}.html").write_text(html)
        n += 1
    return n


def write_show_html(show_id: str, name: str) -> None:
    meta = SHOW_PAGE.get(show_id, {"name": name, "h1": name})
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{meta["name"]} · Watch With The Kids</title>
  <meta name="description" content="Is this {meta["name"]} episode safe to watch with the kids?" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@450;600;700&family=Nunito:wght@500;700;800&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="friends.css" />
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
          <img src="covers/{show_id}.jpg" alt="{meta["name"]}" width="1920" height="1080" />
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

  <footer class="wrap site-footer">
    <p>Made for family couch debates · <strong>watchwiththekids.com</strong> · You kids — your rules!</p>
  </footer>

  <script src="data/{show_id}.js"></script>
  <script src="show.js"></script>
</body>
</html>
"""
    out = WEB / f"{show_id}.html"
    out.write_text(html)
    print(f"Wrote {out}")


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


def build_show(show_id: str, src: Path) -> dict:
    ratings = json.loads(src.read_text())
    payload = slim(ratings, show_id)
    out = DATA / f"{show_id}.js"
    out.write_text(
        "window.RATINGS = " + json.dumps(payload, ensure_ascii=False) + ";\n"
    )
    if show_id == "friends":
        (WEB / "data.js").write_text(out.read_text())
    write_show_html(show_id, payload["show"])
    n = write_episode_pages(show_id, payload)
    print(f"Wrote {out} ({payload['count']} episodes) + {n} episode pages")
    return episode_mix(payload["episodes"])


def main() -> None:
    mixes: dict[str, dict] = {}
    friends_src = ROOT / "ratings.json"
    if friends_src.exists():
        mixes["friends"] = build_show("friends", friends_src)

    ratings_dir = ROOT / "ratings"
    for show_id in READY:
        if show_id == "friends":
            continue
        src = ratings_dir / f"{show_id}.json"
        if src.exists():
            mixes[show_id] = build_show(show_id, src)

    # If a show was already built earlier in another process, still attach mixes from files
    for show_id in READY:
        if show_id in mixes:
            continue
        src = (
            ROOT / "ratings.json"
            if show_id == "friends"
            else ratings_dir / f"{show_id}.json"
        )
        if src.exists():
            mixes[show_id] = episode_mix(json.loads(src.read_text())["episodes"])

    shows_path = WEB / "shows.json"
    shows = json.loads(shows_path.read_text())
    for s in shows:
        s["ready"] = s["id"] in READY
        s["href"] = f"{s['id']}.html" if s["ready"] else None
        if s["id"] in mixes:
            s["mix"] = mixes[s["id"]]
        else:
            s.pop("mix", None)
    shows_path.write_text(json.dumps(shows, indent=2, ensure_ascii=False) + "\n")
    (WEB / "shows.js").write_text(
        "window.SHOWS = " + json.dumps(shows, ensure_ascii=False) + ";\n"
    )
    print("Updated shows.js ready flags:", READY)


if __name__ == "__main__":
    main()

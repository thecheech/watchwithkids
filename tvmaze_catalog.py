"""Align scraped transcripts with TVmaze broadcast order.

Fandom wikis dump games, shorts, podcasts and commentary into the same bucket.
TVMaze season/episode numbers are the canonical filter for shows parents search.
"""

from __future__ import annotations

import html
import json
import re
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UA = "WatchWithTheKids/1.0 (+https://watchwiththekids.com; catalog)"
PAUSE = 0.45

# Per-show title aliases when wiki labels differ from TVmaze.
TITLE_ALIASES: dict[str, dict[str, str]] = {
    "gravity-falls": {
        "northwest mansion mystery": "northwest mansion noir",
        "dungeons dungeons and more dungeons": "dungeons dungeons more dungeons",
        "weirdmageddon 1 xpcveaoqfoxso": "weirdmageddon 1",
        "weirdmageddon 1": "weirdmageddon 1",
        "weirdmageddon 2 escape from reality": "weirdmageddon 2 escape from reality",
        "weirdmageddon 3 take back the falls": "weirdmageddon 3 take back the falls",
    },
    "avatar": {
        "jet episode": "jet",
        "lake laogai episode": "lake laogai",
        "the tales of ba sing se": "tales of ba sing se",
        "the avatar and the firelord": "the avatar and the fire lord",
    },
    "clone-wars": {
        "condition unknown": "the unknown",
    },
    "pokemon": {
        "haunter vs kadabra": "haunter versus kadabra",
        "volcanic panic": "vocanic panic",
        "it s mr mime time": "it s mr mimie time",
    },
    "big-bang-theory": {
        "pilot episode": "pilot",
        "the middle earth paradigm": "the middle earth paradigm",
    },
    "seinfeld": {
        # Transcript index uses the working title; TVMaze uses the broadcast name.
        "the seinfeld chronicles": "good news bad news",
        "seinfeld chronicles": "good news bad news",
    },
}

# Drop these TVmaze rows even when they have season/episode numbers.
MAZE_SKIP_PATTERNS: dict[str, list[str]] = {
    "stranger-things": [r"beyond stranger things"],
    "clone-wars": [r"gallery", r"documentary"],
}

# Only ingest these TVmaze seasons (Indigo League = Pokémon S1).
MAZE_MAX_SEASON: dict[str, int] = {
    "pokemon": 1,
}


def norm_title(value: str | None) -> str:
    t = html.unescape(str(value or ""))
    t = t.replace("'", "'").replace("'", "'")
    t = re.sub(r"^transcript:\s*", "", t, flags=re.I)
    t = re.sub(r"\([^)]*\)", " ", t)
    t = re.sub(r"^\d+\.\s*", "", t)
    t = t.replace("&", " and ")
    t = re.sub(r"[^a-z0-9]+", " ", t.lower())
    return re.sub(r"\s+", " ", t).strip()


# bigbangtrans / similar: "Series 01 Episode 08 – The Grasshopper Experiment"
_SERIES_EP_PREFIX = re.compile(
    r"^series\s+\d+\s+episode\s+\d+\s*[-–—:.·]?\s*",
    re.I,
)


def maze_episode_title(name: str) -> str:
    """TVMaze often prefixes book/chapter labels — keep the episode title parents search."""
    t = html.unescape(str(name or "")).strip()
    t = _SERIES_EP_PREFIX.sub("", t)
    if " - " in t:
        t = t.rsplit(" - ", 1)[-1].strip()
    if " – " in t:
        t = t.rsplit(" – ", 1)[-1].strip()
    t = re.sub(
        r"^chapter\s+(?:one|two|three|four|five|six|seven|eight|nine|ten|"
        r"eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|"
        r"eighteen|nineteen|twenty|twenty-one|twenty-two|\d+)\s*:\s*",
        "",
        t,
        flags=re.I,
    )
    t = re.sub(r"^episode\s+\d+\s*:\s*", "", t, flags=re.I)
    # "Pilot Episode" on bigbangtrans → TVMaze "Pilot"
    t = re.sub(r"\s+episode$", "", t, flags=re.I)
    return t.strip()


def title_keys(show_id: str, title: str) -> list[str]:
    """Alternate normalized keys for wiki/TVmaze title mismatches."""
    keys: list[str] = []
    seen: set[str] = set()

    def add(value: str) -> None:
        key = _alias(show_id, value)
        if key and key not in seen:
            seen.add(key)
            keys.append(key)

    raw = html.unescape(str(title or "")).strip()
    cleaned = maze_episode_title(raw)
    add(raw)
    add(cleaned)
    add(_SERIES_EP_PREFIX.sub("", raw).strip())
    add(re.sub(r"\s*\([^)]*\)", "", raw))
    add(re.sub(r"\s*\([^)]*\)", "", cleaned))

    if ":" in raw:
        left, right = raw.split(":", 1)
        # Skip generic labels like "Chapter One" — they collide across seasons.
        for part in (right.strip(), left.strip(), f"{right.strip()} {left.strip()}"):
            if part and not re.match(r"^(chapter|book|part|episode|season)\b", part, re.I):
                add(part)

    # "Weirdmageddon (1)" -> "Weirdmageddon 1"
    add(re.sub(r"\((\d+)\)", r" \1", raw))
    add(re.sub(r"\((\d+)\)", r" \1", cleaned))

    # "Civil Wars, Part 1" -> "Civil Wars 1"
    add(re.sub(r"\bpart\s+(\d+)\b", r"\1", raw, flags=re.I))
    add(re.sub(r"\bpart\s+(\d+)\b", r"\1", cleaned, flags=re.I))

    # Combined broadcasts: "Holocron Heist / Cargo of Doom" matches either half.
    for source in (raw, cleaned):
        if "/" in source:
            for chunk in source.split("/"):
                chunk = re.sub(r"^\d+\.\s*", "", chunk.strip())
                chunk = _SERIES_EP_PREFIX.sub("", chunk).strip()
                if chunk:
                    add(chunk)

    return keys


def fetch_json(url: str) -> object:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def maze_episodes(maze_id: int, *, specials: bool = False) -> list[dict]:
    flag = "1" if specials else "0"
    url = f"https://api.tvmaze.com/shows/{maze_id}/episodes?specials={flag}"
    data = fetch_json(url)
    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected TVMaze payload for show {maze_id}")
    return data


def maze_show(maze_id: int) -> dict:
    data = fetch_json(f"https://api.tvmaze.com/shows/{maze_id}")
    if not isinstance(data, dict):
        raise RuntimeError(f"Unexpected TVMaze show payload for {maze_id}")
    return data


def _maze_row_ok(show_id: str, row: dict) -> bool:
    name = str(row.get("name") or "")
    if row.get("season") is None or row.get("number") is None:
        return False
    max_season = MAZE_MAX_SEASON.get(show_id)
    if max_season is not None and int(row["season"]) > max_season:
        return False
    for pat in MAZE_SKIP_PATTERNS.get(show_id, []):
        if re.search(pat, name, re.I):
            return False
    return True


def canon_rows(show_id: str, maze_id: int) -> list[dict]:
    rows = [r for r in maze_episodes(maze_id) if _maze_row_ok(show_id, r)]
    rows.sort(key=lambda r: (r.get("season") or 0, r.get("number") or 0))
    return rows


def _alias(show_id: str, title: str) -> str:
    key = norm_title(title)
    return TITLE_ALIASES.get(show_id, {}).get(key, key)


def index_transcripts(show_id: str, raw: list[dict]) -> dict[str, dict]:
    """Map normalized title -> raw transcript index row."""
    out: dict[str, dict] = {}
    for row in raw:
        title = row.get("title") or row.get("index_title") or ""
        if re.search(r"\bcommentary\b", title, re.I):
            continue
        for key in title_keys(show_id, title):
            if key not in out:
                out[key] = row
    return out


def match_to_maze(
    show_id: str,
    maze_id: int,
    raw: list[dict],
) -> tuple[list[dict], list[str], list[str]]:
    """
    Return (matched episodes, unmatched maze titles, unused transcript titles).

    Each matched row gets season/episode/code/title from TVmaze plus file/url from
    the transcript index.
    """
    canon = canon_rows(show_id, maze_id)
    by_title = index_transcripts(show_id, raw)
    used_keys: set[str] = set()
    matched: list[dict] = []
    missing: list[str] = []

    for row in canon:
        maze_name = str(row.get("name") or "")
        short_name = maze_episode_title(maze_name)
        src = None
        for key in title_keys(show_id, short_name) + title_keys(show_id, maze_name):
            src = by_title.get(key)
            if src:
                break
        if not src:
            missing.append(maze_name)
            continue
        used_keys.add(_alias(show_id, src.get("title") or src.get("index_title") or ""))
        season = int(row["season"])
        number = int(row["number"])
        ep_field = str(number).zfill(2)
        matched.append(
            {
                **src,
                "season": season,
                "episode": number,
                "code": f"{season:02d}{ep_field}",
                "title": short_name,
                "index_title": src.get("title") or src.get("index_title") or short_name,
                "maze_id": row.get("id"),
                "airdate": row.get("airdate"),
            }
        )

    unused = [
        str(r.get("title") or r.get("index_title") or "")
        for r in raw
        if _alias(show_id, r.get("title") or r.get("index_title") or "") not in used_keys
    ]
    return matched, missing, unused


def load_maze_map(shows_path: Path | None = None) -> dict[str, int]:
    path = shows_path or ROOT / "web" / "shows.json"
    catalog = json.loads(path.read_text())
    return {s["id"]: int(s["mazeId"]) for s in catalog if s.get("id") and s.get("mazeId")}


def filter_transcript_index(show_id: str, maze_id: int, raw: list[dict]) -> list[dict]:
    matched, missing, unused = match_to_maze(show_id, maze_id, raw)
    if missing:
        print(f"[{show_id}] missing transcripts for {len(missing)} TVmaze episodes", flush=True)
        for name in missing[:8]:
            print(f"  - {name}", flush=True)
        if len(missing) > 8:
            print(f"  ... +{len(missing) - 8} more", flush=True)
    if unused:
        print(f"[{show_id}] dropped {len(unused)} non-canon wiki rows", flush=True)
    return matched

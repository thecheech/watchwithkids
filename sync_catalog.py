#!/usr/bin/env python3
"""Align wiki-scraped episode lists with TVMaze season/episode order.

Run before rate_show for fandom-wiki shows whose scrape index is alphabetical:
  python3 sync_catalog.py bluey gravity-falls spongebob ...
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from catalog import clean_episode_title, episode_code, is_real_episode
from enrich_summaries import maze_episodes, title_keys
from shows_meta import MOVIE_SHOWS

ROOT = Path(__file__).resolve().parent
SHOWS_PATH = ROOT / "web" / "shows.json"

# Wiki dumps that need TVMaze broadcast order (not Springfield / dataset scrapes).
WIKI_SHOWS = [
    "bluey",
    "gravity-falls",
    "phineas-and-ferb",
    "adventure-time",
    "steven-universe",
    "spongebob",
]


def episodes_path(show_id: str) -> Path:
    return ROOT / "transcripts" / show_id / "episodes.json"


def load_maze_map() -> dict[str, int]:
    catalog = json.loads(SHOWS_PATH.read_text())
    return {s["id"]: int(s["mazeId"]) for s in catalog if s.get("id") and s.get("mazeId")}


def index_maze_eps(maze: list[dict]) -> dict[str, dict]:
    by_title: dict[str, dict] = {}
    for ep in maze:
        for key in title_keys(ep.get("name")):
            by_title.setdefault(key, ep)
    return by_title


def match_maze_ep(raw: dict, by_title: dict[str, dict]) -> dict | None:
    for field in ("title", "index_title"):
        for key in title_keys(clean_episode_title(raw.get(field) or "", raw.get("index_title") or "")):
            hit = by_title.get(key)
            if hit:
                return hit
    return None


def episode_sort_key(ep: dict) -> tuple:
    """Sort key for proper episode ordering (numeric with optional letter suffix)."""
    season = int(ep["season"])
    episode = ep.get("episode")
    
    if isinstance(episode, int):
        return (season, episode, "")
    
    ep_str = str(episode)
    match = re.match(r"^(\d+)([a-z]*)$", ep_str, re.I)
    if match:
        num, letter = match.groups()
        return (season, int(num), letter.lower())
    
    return (season, 999999, ep_str)


def sync_show(show_id: str, maze_id: int, *, dry_run: bool) -> dict:
    path = episodes_path(show_id)
    if not path.exists():
        raise FileNotFoundError(path)

    raw_eps = json.loads(path.read_text())
    maze = maze_episodes(maze_id)
    by_title = index_maze_eps(maze)

    kept: list[dict] = []
    matched = dropped = 0
    for raw in raw_eps:
        title = clean_episode_title(raw.get("title") or "", raw.get("index_title") or "")
        maze_ep = match_maze_ep(raw, by_title)
        if maze_ep and maze_ep.get("season") is not None and maze_ep.get("number") is not None:
            season = int(maze_ep["season"])
            episode = int(maze_ep["number"])
            code = episode_code(season, episode)
            entry = {
                **raw,
                "title": title,
                "season": season,
                "episode": episode,
                "code": code,
            }
            if is_real_episode(show_id, title, season):
                kept.append(entry)
                matched += 1
            else:
                dropped += 1
            continue

        # No TVMaze match — keep only if it already has broadcast numbers and passes hygiene.
        season = raw.get("season")
        episode = raw.get("episode")
        if season is not None and str(season) not in ("0", "None", "") and is_real_episode(show_id, title, season):
            code = raw.get("code") or episode_code(season, episode)
            kept.append({**raw, "title": title, "code": code})
            continue
        dropped += 1

    kept.sort(key=episode_sort_key)

    if not dry_run:
        path.write_text(json.dumps(kept, indent=2, ensure_ascii=False) + "\n")

    return {
        "show": show_id,
        "before": len(raw_eps),
        "after": len(kept),
        "matched": matched,
        "dropped": dropped,
        "maze_eps": len(maze),
    }


def fix_movie(show_id: str, *, dry_run: bool) -> dict:
    """Movies are one entry with season 0, not Season 1 Episode 1."""
    path = episodes_path(show_id)
    if not path.exists():
        return {"show": show_id, "skipped": "no episodes.json"}
    raw = json.loads(path.read_text())
    if len(raw) != 1:
        return {"show": show_id, "skipped": f"expected 1 entry, got {len(raw)}"}
    ep = raw[0]
    title = clean_episode_title(ep.get("title") or show_id)
    fixed = {
        **ep,
        "title": title,
        "season": 0,
        "episode": 1,
        "code": "0001",
    }
    if not dry_run:
        path.write_text(json.dumps([fixed], indent=2, ensure_ascii=False) + "\n")
    return {"show": show_id, "movie": title}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("shows", nargs="*", help="Show ids (default: all wiki shows + movies)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    show_ids = args.shows or WIKI_SHOWS + sorted(MOVIE_SHOWS)
    maze_ids = load_maze_map()
    rows = []

    for i, show_id in enumerate(show_ids):
        if i:
            time.sleep(0.6)
        if show_id in MOVIE_SHOWS:
            row = fix_movie(show_id, dry_run=args.dry_run)
            rows.append(row)
            print(f"{show_id:24} movie -> season 0{'  [dry-run]' if args.dry_run else ''}")
            continue
        maze_id = maze_ids.get(show_id)
        if not maze_id:
            print(f"skip {show_id}: no mazeId", file=sys.stderr)
            continue
        try:
            row = sync_show(show_id, maze_id, dry_run=args.dry_run)
        except (OSError, RuntimeError, FileNotFoundError) as err:
            print(f"FAIL {show_id}: {err}", file=sys.stderr)
            continue
        rows.append(row)
        print(
            f"{row['show']:24} {row['before']:4} -> {row['after']:4} "
            f"(matched {row['matched']}, dropped {row['dropped']})"
            f"{'  [dry-run]' if args.dry_run else ''}"
        )

    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Attach concise TVMaze episode summaries to ratings JSON files."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SHOWS_PATH = ROOT / "web" / "shows.json"
UA = "WatchWithTheKids/1.0 (+https://watchwiththekids.com)"
FALLBACK_PREFIX = "Episode: "

# Friends lives at the repo root for the original build path, and also under ratings/.
FRIENDS_PATHS = (ROOT / "ratings.json", ROOT / "ratings" / "friends.json")


def strip_summary(s: str | None) -> str | None:
    if not s:
        return None
    t = re.sub(r"<[^>]+>", "", s)
    t = html.unescape(t).strip()
    t = re.sub(r"\s+", " ", t)
    return t or None


def parse_episode_nums(ep_field) -> list[int]:
    if ep_field is None or not re.search(r"\d", str(ep_field)):
        return []
    # Lettered wiki segments like 29a are not TVmaze episode numbers.
    if re.search(r"[A-Za-z]", str(ep_field)):
        return []
    nums: list[int] = []
    for part in re.split(r"[-–,/]", str(ep_field)):
        m = re.match(r"^(\d+)$", part.strip())
        if m:
            nums.append(int(m.group(1)))
    return nums


def season_allows_numeric(episodes: list[dict], season) -> bool:
    """True when this season's episode field is 1..N, not a running production number."""
    nums: list[int] = []
    for e in episodes:
        if e.get("season") != season:
            continue
        ep = str(e.get("episode", ""))
        if re.search(r"[A-Za-z]", ep):
            continue
        nums.extend(parse_episode_nums(ep))
    if not nums:
        return False
    return min(nums) <= 1 and max(nums) <= 40


def norm_title(s: str | None) -> str:
    t = html.unescape(str(s or "")).lower()
    t = t.replace("’", "'").replace("‘", "'")
    t = re.sub(r"^series\s+\d+\s+episode\s+\d+\s*[–\-:]+\s*", "", t)
    t = re.sub(r"^\d+\.\s*", "", t)
    t = re.sub(r"\([^)]*uncut[^)]*\)", "", t)
    t = re.sub(r"\([^)]*a\.?k\.?a\.?[^)]*\)", "", t)
    t = re.sub(r"\(\s*part\s*(\d+)\s*\)", r" \1", t)
    t = re.sub(r",\s*part\s*(\d+)\s*$", r" \1", t)
    t = re.sub(r"\(\s*(\d+)\s*\)", r" \1", t)
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def compact_title(s: str | None) -> str:
    return re.sub(r"\s+", "", norm_title(s))


def is_real_summary(s: str | None) -> bool:
    if not s or not str(s).strip():
        return False
    return not str(s).strip().startswith(FALLBACK_PREFIX)


def fetch_json(url: str) -> object:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def maze_episodes(maze_id: int) -> list[dict]:
    url = f"https://api.tvmaze.com/shows/{maze_id}/episodes?specials=1"
    data = fetch_json(url)
    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected TVMaze payload for show {maze_id}")
    return data


def title_keys(name: str | None) -> list[str]:
    keys: list[str] = []
    raw = html.unescape(str(name or ""))
    chunks = re.split(r"\s*[/;]\s*", raw)
    seen: set[str] = set()
    for cand in [raw, *chunks]:
        n = norm_title(cand)
        c = compact_title(cand)
        for key in (n, c):
            if key and key not in seen:
                seen.add(key)
                keys.append(key)
    return keys


def index_maze(maze: list[dict]) -> tuple[dict[tuple[int, int], str], dict[str, str]]:
    by_sn: dict[tuple[int, int], str] = {}
    by_title: dict[str, str] = {}
    for e in maze:
        summary = strip_summary(e.get("summary"))
        if not summary:
            continue
        season = e.get("season")
        number = e.get("number")
        if season is not None and number is not None:
            by_sn[(int(season), int(number))] = summary
        for key in title_keys(e.get("name")):
            by_title.setdefault(key, summary)
            base = re.sub(r" \d+$", "", key)
            if base and base != key:
                prev = by_title.get(base)
                if not prev:
                    by_title[base] = summary
                elif prev != summary and summary not in prev:
                    by_title[base] = f"{prev} {summary}"
    return by_sn, by_title


def lookup_summary(
    ep: dict,
    episodes: list[dict],
    by_sn: dict[tuple[int, int], str],
    by_title: dict[str, str],
) -> str | None:
    for raw in (ep.get("title"), ep.get("index_title")):
        for key in title_keys(raw):
            if key in by_title:
                return by_title[key]

    if not season_allows_numeric(episodes, ep.get("season")):
        return None
    try:
        season_n = int(ep.get("season"))
    except (TypeError, ValueError):
        return None
    parts: list[str] = []
    seen: set[str] = set()
    for n in parse_episode_nums(ep.get("episode")):
        s = by_sn.get((season_n, n))
        if s and s not in seen:
            seen.add(s)
            parts.append(s)
    return " ".join(parts) if parts else None


def ratings_path_for(show_id: str) -> Path:
    # ratings.json is where rate_episodes.py writes Friends, so it is the source of
    # truth; ratings/friends.json is only kept in sync as a convenience copy.
    if show_id == "friends":
        return ROOT / "ratings.json"
    return ROOT / "ratings" / f"{show_id}.json"


def load_maze_map(shows: list[dict]) -> dict[str, int]:
    return {s["id"]: int(s["mazeId"]) for s in shows if s.get("id") and s.get("mazeId")}


def enrich_show(show_id: str, maze_id: int, *, dry_run: bool, force: bool) -> dict:
    path = ratings_path_for(show_id)
    extra_paths: list[Path] = []
    if show_id == "friends":
        extra_paths = [p for p in FRIENDS_PATHS if p != path and p.exists()]
    if not path.exists():
        raise FileNotFoundError(f"No ratings file for {show_id}: {path}")

    ratings = json.loads(path.read_text())
    maze = maze_episodes(maze_id)
    by_sn, by_title = index_maze(maze)

    attached = kept = missing_maze = 0
    episodes = ratings["episodes"]
    for e in episodes:
        existing = e.get("summary")
        found = lookup_summary(e, episodes, by_sn, by_title)
        if found:
            if force or not is_real_summary(existing):
                e["summary"] = found
                attached += 1
            else:
                kept += 1
            continue
        missing_maze += 1
        if is_real_summary(existing) and not force:
            kept += 1
        elif existing and str(existing).startswith(FALLBACK_PREFIX):
            # Drop title-echo fallbacks; a missing plot is better than a fake one.
            e["summary"] = None

    if not dry_run:
        text = json.dumps(ratings, indent=2, ensure_ascii=False) + "\n"
        path.write_text(text)
        for extra in extra_paths:
            extra.write_text(text)

    return {
        "show": show_id,
        "episodes": len(ratings["episodes"]),
        "maze_eps": len(maze),
        "attached": attached,
        "kept": kept,
        "unmatched": missing_maze,
        "path": str(path.relative_to(ROOT)),
    }


def discover_shows(requested: list[str]) -> list[str]:
    if requested:
        return requested
    shows = []
    if (ROOT / "ratings" / "friends.json").exists() or (ROOT / "ratings.json").exists():
        shows.append("friends")
    for p in sorted((ROOT / "ratings").glob("*.json")):
        if p.stem != "friends":
            shows.append(p.stem)
    return shows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("shows", nargs="*", help="Show ids (default: every ratings JSON)")
    parser.add_argument("--dry-run", action="store_true", help="Print stats without writing files")
    parser.add_argument("--force", action="store_true", help="Overwrite existing real summaries")
    args = parser.parse_args()

    catalog = json.loads(SHOWS_PATH.read_text())
    maze_ids = load_maze_map(catalog)
    show_ids = discover_shows(args.shows)

    rows = []
    for i, show_id in enumerate(show_ids):
        maze_id = maze_ids.get(show_id)
        if not maze_id:
            print(f"skip {show_id}: no mazeId in shows.json", file=sys.stderr)
            continue
        if i:
            time.sleep(0.6)
        try:
            row = enrich_show(show_id, maze_id, dry_run=args.dry_run, force=args.force)
        except (urllib.error.URLError, TimeoutError, RuntimeError, FileNotFoundError) as err:
            print(f"FAIL {show_id}: {err}", file=sys.stderr)
            continue
        rows.append(row)
        print(
            f"{row['show']:24} eps={row['episodes']:4} maze={row['maze_eps']:4} "
            f"attached={row['attached']:4} kept={row['kept']:4} "
            f"unmatched={row['unmatched']:4}"
            f"{'  [dry-run]' if args.dry_run else ''}"
        )

    if not rows:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

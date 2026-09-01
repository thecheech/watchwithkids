#!/usr/bin/env python3
"""Pull per-episode stills from TVMaze (same source as show covers).

Writes stills.json: { show_id: { code: { medium, original } } }.
build_web.py merges these into the listing payload and episode pages.

TVMaze asks for a contactable User-Agent. No API key.
"""

from __future__ import annotations

import html
import json
import re
import time
import unicodedata
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TVMAZE = "https://api.tvmaze.com"
UA = "WatchWithKids/1.0 (+https://watchwiththekids.com; stills)"
PAUSE = 0.45

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
    "parks-and-recreation",
    "modern-family",
    "wednesday",
    "avatar",
    "gravity-falls",
    "stranger-things",
    "legend-of-korra",
    "clone-wars",
    "owl-house",
    "amphibia",
    "pokemon",
]


def get_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read())


def parse_episode_nums(ep_field) -> list[int]:
    if ep_field is None or not re.search(r"\d", str(ep_field)):
        return []
    nums: list[int] = []
    for part in re.split(r"[-–,/]", str(ep_field)):
        m = re.match(r"^(\d+)", part.strip())
        if m:
            nums.append(int(m.group(1)))
    return nums


def norm_title(value: str | None) -> str:
    t = unicodedata.normalize("NFKD", html.unescape(str(value or "")))
    t = t.lower()
    t = re.sub(r"\([^)]*\)", " ", t)
    t = re.sub(r"\bpart\s*\d+\b", " ", t)
    t = re.sub(r"^\d+[a-z]?\s+", " ", t)
    t = re.sub(r"[^a-z0-9]+", " ", t)
    t = re.sub(r"\b(the|a|an|episode|series|one|with|where)\b", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def still_of(maze_ep: dict) -> dict | None:
    image = maze_ep.get("image") or {}
    medium = image.get("medium")
    original = image.get("original")
    if not medium and not original:
        return None
    return {"medium": medium or original, "original": original or medium}


def load_ratings(show_id: str) -> dict:
    path = ROOT / "ratings.json" if show_id == "friends" else ROOT / "ratings" / f"{show_id}.json"
    return json.loads(path.read_text())


def match_stills(ours: list[dict], maze_eps: list[dict]) -> tuple[dict[str, dict], int]:
    by_sn: dict[tuple[int, int], dict] = {}
    by_title: dict[str, dict] = {}
    maze_by_season: dict[int, list[dict]] = defaultdict(list)
    for maze in maze_eps:
        number = maze.get("number")
        season = maze.get("season")
        if season is None:
            continue
        maze_by_season[int(season)].append(maze)
        if number is not None:
            by_sn[(int(season), int(number))] = maze
        title = norm_title(maze.get("name"))
        if title and title not in by_title:
            by_title[title] = maze

    matched: dict[str, dict] = {}
    matched_maze_ids: set[int] = set()

    def take(ours_ep: dict, maze: dict) -> None:
        still = still_of(maze)
        if not still:
            return
        matched[str(ours_ep["code"])] = still
        maze_id = maze.get("id")
        if isinstance(maze_id, int):
            matched_maze_ids.add(maze_id)

    for ep in ours:
        code = str(ep["code"])
        season = int(ep["season"])
        found = None
        nums = parse_episode_nums(ep.get("episode"))
        # Prefer in-season numbers (skip production codes like Seinfeld 206).
        for n in nums:
            if n > 40:
                continue
            found = by_sn.get((season, n))
            if found:
                break
        if not found:
            title = norm_title(ep.get("title") or ep.get("index_title"))
            found = by_title.get(title) if title else None
        if found:
            take(ep, found)

    # Last pass: same-count leftover zip inside a season (Seinfeld production numbers).
    leftover_ours: dict[int, list[dict]] = defaultdict(list)
    for ep in ours:
        if str(ep["code"]) not in matched:
            leftover_ours[int(ep["season"])].append(ep)

    for season, ours_left in leftover_ours.items():
        maze_left = [
            m
            for m in maze_by_season.get(season, [])
            if m.get("id") not in matched_maze_ids and still_of(m)
        ]
        if not ours_left or len(ours_left) != len(maze_left):
            continue
        ours_left.sort(
            key=lambda e: parse_episode_nums(e.get("episode")) or [0]
        )
        maze_left.sort(key=lambda m: (m.get("number") is None, m.get("number") or 0))
        for ep, maze in zip(ours_left, maze_left):
            take(ep, maze)

    return matched, len(ours) - len(matched)


def main() -> None:
    shows = json.loads((ROOT / "web" / "shows.json").read_text())
    maze_ids = {s["id"]: s["mazeId"] for s in shows if s.get("mazeId")}
    out: dict[str, dict] = {}

    for show_id in READY:
        maze_id = maze_ids.get(show_id)
        ratings_path = (
            ROOT / "ratings.json" if show_id == "friends" else ROOT / "ratings" / f"{show_id}.json"
        )
        if not maze_id or not ratings_path.exists():
            print(f"{show_id}: skip (no mazeId or ratings)")
            continue
        ours = load_ratings(show_id)["episodes"]
        maze_eps = get_json(f"{TVMAZE}/shows/{maze_id}/episodes")
        matched, miss = match_stills(ours, maze_eps)
        out[show_id] = matched
        print(
            f"{show_id:24} {len(matched):4}/{len(ours):4} stills"
            f"{'' if miss == 0 else f'  ({miss} unmatched)'}"
        )
        time.sleep(PAUSE)

    dest = ROOT / "stills.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(v) for v in out.values())
    print(f"Wrote {dest} ({total} episode stills)")


if __name__ == "__main__":
    main()

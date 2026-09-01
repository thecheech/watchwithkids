#!/usr/bin/env python3
"""Fill known incomplete-season holes by fetching missing episodes from TVmaze.

Episodes without transcripts get default ratings (sex=2, language=2, violence=1, overall=2).
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from tvmaze_catalog import maze_episodes
from shows_meta import episode_age, meta_for

ROOT = Path(__file__).resolve().parent
RATINGS_DIR = ROOT / "ratings"


def default_rating_for_show(show_id: str) -> dict:
    """Default rating for episodes without transcripts."""
    o = 2
    age = episode_age(show_id, o)
    return {
        "violence": 1,
        "sex": 2,
        "language": 2,
        "overall": o,
        "age": age,
        "verdict": f"Mild — okay from about {age}+",
        "why": "No transcript available — default moderate rating applied.",
        "themes": {"fine": [], "watch": ["Default rating (no transcript)"], "watch_detail": []},
        "examples": [],
        "notes": "No transcript available",
        "flags": [],
        "source": "tvmaze-only",
    }


def fetch_maze_episodes_for_season(maze_id: int, season: int) -> list[dict]:
    """Fetch all episodes for a specific season from TVmaze."""
    all_eps = maze_episodes(maze_id)
    return [ep for ep in all_eps if ep.get("season") == season]


def fill_holes(show_id: str, maze_id: int, target_seasons: list[int]) -> dict:
    """Add missing episodes from TVmaze for specified seasons."""
    ratings_path = RATINGS_DIR / f"{show_id}.json"
    if not ratings_path.exists():
        raise FileNotFoundError(f"No ratings file: {ratings_path}")
    
    ratings_data = json.loads(ratings_path.read_text())
    episodes = ratings_data["episodes"]
    
    # Index existing episodes by (season, episode)
    existing = {(ep["season"], ep["episode"]): ep for ep in episodes}
    
    # Fetch maze episodes for target seasons
    added = 0
    for season in target_seasons:
        maze_eps = fetch_maze_episodes_for_season(maze_id, season)
        for maze_ep in maze_eps:
            s = maze_ep["season"]
            e = maze_ep["number"]
            key = (s, e)
            
            if key in existing:
                continue
            
            # Add new episode with default rating
            code = f"{s:02d}{e:02d}"
            title = maze_ep.get("name", f"Episode {e}")
            default = default_rating_for_show(show_id)
            
            new_ep = {
                "season": s,
                "episode": e,
                "code": code,
                "title": title,
                "index_title": title,
                "url": None,
                "file": None,
                "summary": maze_ep.get("summary", "").replace("<p>", "").replace("</p>", "").strip() if maze_ep.get("summary") else None,
                **default,
            }
            episodes.append(new_ep)
            added += 1
    
    # Sort episodes by season and episode
    episodes.sort(key=lambda ep: (ep["season"], ep["episode"]))
    ratings_data["episodes"] = episodes
    ratings_data["count"] = len(episodes)
    
    # Write updated ratings
    ratings_path.write_text(json.dumps(ratings_data, indent=2, ensure_ascii=False) + "\n")
    
    return {
        "show": show_id,
        "added": added,
        "total": len(episodes),
    }


def main() -> None:
    # Configuration: (show_id, maze_id, seasons_to_fill)
    tasks = [
        ("rick-and-morty", 216, [8]),  # Rick S8 needs 9 more episodes
        ("brooklyn-nine-nine", 49, [7, 8]),  # B99 S7 incomplete + S8 missing
        ("full-house", 1251, [6, 7, 8]),  # Full House S6-S8 missing
        ("simpsons", 83, [26]),  # Simpsons S26 incomplete (stop at S26 for now)
        ("futurama", 538, [7, 8, 9, 10]),  # Futurama S7 holes + S8-S10 missing
    ]
    
    print("Filling season holes from TVmaze...")
    print("=" * 60)
    
    for i, (show_id, maze_id, seasons) in enumerate(tasks):
        if i > 0:
            time.sleep(0.5)  # Be nice to TVmaze API
        
        try:
            result = fill_holes(show_id, maze_id, seasons)
            print(f"{result['show']:24} added={result['added']:3} total={result['total']:4}")
        except Exception as err:
            print(f"FAIL {show_id}: {err}")
            continue
    
    print("=" * 60)
    print("Done! Run build_web.py to regenerate HTML for affected shows.")


if __name__ == "__main__":
    main()

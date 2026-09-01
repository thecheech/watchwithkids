#!/usr/bin/env python3
"""Fix episode ordering in ratings JSON files - sort by season/episode number, not alphabetically."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def episode_sort_key(ep: dict) -> tuple:
    """Sort key for proper episode ordering (numeric with optional letter suffix)."""
    season = int(ep.get("season", 0))
    episode = ep.get("episode")
    
    if isinstance(episode, int):
        return (season, episode, "")
    
    ep_str = str(episode)
    match = re.match(r"^(\d+)([a-z]*)$", ep_str, re.I)
    if match:
        num, letter = match.groups()
        return (season, int(num), letter.lower())
    
    return (season, 999999, ep_str)


def fix_show_order(show_id: str, *, dry_run: bool = False) -> dict:
    """Re-sort episodes in a ratings JSON file by proper broadcast order."""
    ratings_path = ROOT / "ratings" / f"{show_id}.json"
    if not ratings_path.exists():
        return {"show": show_id, "error": "file not found"}
    
    data = json.loads(ratings_path.read_text())
    episodes = data.get("episodes", [])
    
    if not episodes:
        return {"show": show_id, "skipped": "no episodes"}
    
    # Get first few episodes before and after sorting to show the change
    before_preview = [(e.get("season"), e.get("episode"), e.get("title")) for e in episodes[:5]]
    
    # Sort episodes by proper broadcast order
    episodes_sorted = sorted(episodes, key=episode_sort_key)
    
    after_preview = [(e.get("season"), e.get("episode"), e.get("title")) for e in episodes_sorted[:5]]
    
    # Check if order actually changed
    if before_preview == after_preview:
        return {"show": show_id, "status": "already correct", "count": len(episodes)}
    
    # Update the data
    data["episodes"] = episodes_sorted
    data["count"] = len(episodes_sorted)
    
    if not dry_run:
        ratings_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    
    return {
        "show": show_id,
        "status": "fixed" if not dry_run else "would fix",
        "count": len(episodes),
        "before": before_preview,
        "after": after_preview,
    }


def main() -> None:
    import sys
    
    shows = [
        "bluey",
        "phineas-and-ferb",
        "avatar",
        "gravity-falls",
        "adventure-time",
        "steven-universe",
        "spongebob",
    ]
    
    dry_run = "--dry-run" in sys.argv
    
    for show_id in shows:
        result = fix_show_order(show_id, dry_run=dry_run)
        
        if result.get("error"):
            print(f"❌ {show_id}: {result['error']}")
        elif result.get("status") == "already correct":
            print(f"✓ {show_id}: already in correct order ({result['count']} episodes)")
        elif result.get("status") == "skipped":
            print(f"⊘ {show_id}: {result['skipped']}")
        else:
            print(f"{'🔄' if dry_run else '✓'} {show_id}: {result['status']} ({result['count']} episodes)")
            print(f"  Before: S{result['before'][0][0]}E{result['before'][0][1]} {result['before'][0][2]}")
            print(f"  After:  S{result['after'][0][0]}E{result['after'][0][1]} {result['after'][0][2]}")


if __name__ == "__main__":
    main()

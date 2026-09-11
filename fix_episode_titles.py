#!/usr/bin/env python3
"""Fix episode title defects in ratings/*.json files."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Apply the same clean_episode_title logic from catalog.py
_NUM_PREFIX = re.compile(
    r"^\s*(?:"
    r"s?\d{1,2}[ex]\d{1,3}"  # S01E06 / 1x06
    r"|\d{3,4}"  # production code 206
    r"|[A-Z]{2,4}\d{2,3}"  # production code CHE01, AABF05, etc
    r")\s*(?:[-–—:.]\s*|\s+)",
    re.I,
)

TITLE_OVERRIDES = {
    "modern-family": {
        "0914": "Written in the Stars",
    },
}


def clean_title_prefix(title: str) -> str:
    """Remove episode number and production code prefixes like '1. CHE01 - '"""
    t = title.strip()
    # First pass: remove leading episode numbers like "1. " or "14. "
    t = re.sub(r"^\s*\d+\.\s+", "", t)
    # Second pass: remove production codes like CHE01, AABF05, etc
    t = _NUM_PREFIX.sub("", t)
    return t.strip()


def fix_show_titles(show_id: str) -> dict:
    """Fix titles in a show's ratings file."""
    path = ROOT / "ratings" / f"{show_id}.json"
    if not path.exists():
        return {"show_id": show_id, "error": "ratings file not found"}
    
    data = json.loads(path.read_text())
    changes = []
    
    for episode in data["episodes"]:
        code = episode["code"]
        old_title = episode["title"]
        old_index = episode["index_title"]
        
        # Apply override if exists
        if show_id in TITLE_OVERRIDES and code in TITLE_OVERRIDES[show_id]:
            new_title = TITLE_OVERRIDES[show_id][code]
            new_index = new_title
        else:
            # Clean the title
            new_title = clean_title_prefix(old_title)
            new_index = clean_title_prefix(old_index)
        
        if new_title != old_title or new_index != old_index:
            changes.append({
                "season": episode["season"],
                "episode": episode["episode"],
                "code": code,
                "old_title": old_title,
                "new_title": new_title,
                "old_index": old_index,
                "new_index": new_index,
            })
            episode["title"] = new_title
            episode["index_title"] = new_index
    
    if changes:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    
    return {"show_id": show_id, "changes": len(changes), "details": changes}


def scan_all_titles() -> dict:
    """Scan all READY show ratings for title defects."""
    issues = {}
    
    for ratings_file in sorted((ROOT / "ratings").glob("*.json")):
        show_id = ratings_file.stem
        data = json.loads(ratings_file.read_text())
        show_issues = []
        
        # Group by season for duplicate detection
        by_season = {}
        for ep in data["episodes"]:
            season = ep["season"]
            if season not in by_season:
                by_season[season] = []
            by_season[season].append(ep)
        
        # Check for duplicates within each season
        for season, eps in by_season.items():
            titles = [e["title"] for e in eps]
            dupes = [t for t, cnt in Counter(titles).items() if cnt > 1]
            if dupes:
                for title in dupes:
                    matching = [e for e in eps if e["title"] == title]
                    show_issues.append({
                        "type": "duplicate_title",
                        "season": season,
                        "title": title,
                        "episodes": [{"episode": e["episode"], "code": e["code"]} for e in matching],
                    })
        
        # Check for empty or placeholder titles
        for ep in data["episodes"]:
            title = ep["title"].strip()
            if not title or title.lower() in ["untitled", "tba", "tbd", "unknown"]:
                show_issues.append({
                    "type": "empty_or_placeholder",
                    "season": ep["season"],
                    "episode": ep["episode"],
                    "code": ep["code"],
                    "title": ep["title"],
                })
            
            # Check for code-like prefixes that weren't cleaned
            if re.match(r"^\d+\.", title):
                show_issues.append({
                    "type": "number_prefix",
                    "season": ep["season"],
                    "episode": ep["episode"],
                    "code": ep["code"],
                    "title": title,
                })
            
            if re.search(r"^[A-Z]{2,4}\d{2,}", title, re.I):
                show_issues.append({
                    "type": "production_code_prefix",
                    "season": ep["season"],
                    "episode": ep["episode"],
                    "code": ep["code"],
                    "title": title,
                })
        
        if show_issues:
            issues[show_id] = show_issues
    
    return issues


def main():
    import sys
    
    if len(sys.argv) > 1:
        # Fix specific shows
        for show_id in sys.argv[1:]:
            if show_id == "--scan":
                print("Scanning all shows for title issues...")
                issues = scan_all_titles()
                if issues:
                    print("\nFound issues in:")
                    for show_id, show_issues in issues.items():
                        print(f"\n{show_id}: {len(show_issues)} issues")
                        for issue in show_issues[:5]:  # Show first 5
                            print(f"  {issue}")
                        if len(show_issues) > 5:
                            print(f"  ... and {len(show_issues) - 5} more")
                else:
                    print("No title issues found!")
            else:
                result = fix_show_titles(show_id)
                print(json.dumps(result, indent=2))
    else:
        print("Usage: python3 fix_episode_titles.py <show-id> [<show-id> ...]")
        print("       python3 fix_episode_titles.py --scan")


if __name__ == "__main__":
    main()

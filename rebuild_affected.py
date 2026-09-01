#!/usr/bin/env python3
"""Rebuild web payloads and pages for specific shows only."""

from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).parent))
from build_web import build_show, READY, ROOT

AFFECTED_SHOWS = ["rick-and-morty", "brooklyn-nine-nine", "full-house", "simpsons", "futurama"]

def main():
    print("Rebuilding affected shows...")
    print("=" * 60)
    
    sitemap = []
    ratings_dir = ROOT / "ratings"
    
    for show_id in AFFECTED_SHOWS:
        if show_id not in READY:
            print(f"Skip {show_id}: not in READY")
            continue
        
        src = ratings_dir / f"{show_id}.json"
        if not src.exists():
            print(f"Skip {show_id}: no ratings file")
            continue
        
        try:
            mix, payload = build_show(show_id, src, sitemap)
            print(f"✓ {show_id:24} {len(payload['episodes'])} episodes")
        except Exception as err:
            print(f"✗ {show_id:24} FAILED: {err}")
    
    print("=" * 60)
    print("Done!")

if __name__ == "__main__":
    main()

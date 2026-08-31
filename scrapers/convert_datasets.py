#!/usr/bin/env python3
"""Convert GitHub transcript datasets into per-episode text files.

- The Office (US): brianbuie/the-office JSON (every line, grouped by scene)
- The Simpsons: TidyTuesday CSVs (script lines + episodes + characters)

Reads raw files from /tmp, writes transcripts/<show>/ + episodes.csv/json.
"""

import csv
import json
from collections import defaultdict

from common import slugify, write_episode, write_index

OFFICE_JSON = "/tmp/the-office.json"
SIMPSONS_DIR = "/tmp"


def convert_office() -> None:
    show = "the-office"
    episodes = json.load(open(OFFICE_JSON, encoding="utf-8"))
    results = []
    for ep in episodes:
        season, number, title = ep["season"], ep["episode"], ep["title"]
        parts = []
        for scene in ep["scenes"]:
            parts.append("\n".join(f"{l['character']}: {l['line']}" for l in scene))
        text = "\n\n".join(p for p in parts if p.strip())
        if len(text.split()) < 50:
            continue
        url = "https://github.com/brianbuie/the-office"
        fname = f"s{season:02d}e{number:02d}-{slugify(title)}.txt"
        file = write_episode(show, fname, title, url, text)
        results.append({"season": season, "episode": number, "title": title,
                        "words": len(text.split()), "url": url, "file": file})
    results.sort(key=lambda e: (e["season"], e["episode"]))
    write_index(show, results)
    print(f"[{show}] saved {len(results)} episodes")


def convert_simpsons() -> None:
    show = "simpsons"
    episodes = {}
    with open(f"{SIMPSONS_DIR}/simpsons_episodes_full.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            episodes[row["id"]] = row

    lines_by_ep: dict[str, list[dict]] = defaultdict(list)
    with open(f"{SIMPSONS_DIR}/simpsons_script_lines.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            lines_by_ep[row["episode_id"]].append(row)

    url = "https://github.com/rfordatascience/tidytuesday/tree/main/data/2025/2025-02-04"
    results = []
    for ep_id, lines in lines_by_ep.items():
        ep = episodes.get(ep_id)
        if not ep or not ep.get("season"):
            continue
        season, number, title = int(ep["season"]), int(ep["number_in_season"]), ep["title"]
        lines = [r for r in lines if (r.get("number") or "").isdigit()]
        lines.sort(key=lambda r: int(r["number"]))
        out, last_loc = [], None
        for r in lines:
            loc = (r.get("raw_location_text") or "").strip()
            if loc and loc != last_loc:
                out.append(f"[{loc.title()}]")
                last_loc = loc
            raw = (r.get("raw_text") or "").strip()
            if raw:
                out.append(raw)
        text = "\n".join(out)
        if len(text.split()) < 50:
            continue
        fname = f"s{season:02d}e{number:02d}-{slugify(title)}.txt"
        file = write_episode(show, fname, title, url, text)
        results.append({"season": season, "episode": number, "title": title,
                        "words": len(text.split()), "url": url, "file": file})
    results.sort(key=lambda e: (e["season"], e["episode"]))
    write_index(show, results)
    print(f"[{show}] saved {len(results)} episodes")


if __name__ == "__main__":
    convert_office()
    convert_simpsons()

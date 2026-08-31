#!/usr/bin/env python3
"""Attach concise TVMaze episode summaries to ratings.json."""

from __future__ import annotations

import html
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TVMAZE = "https://api.tvmaze.com/singlesearch/shows?q=friends&embed=episodes"


def strip_summary(s: str | None) -> str | None:
    if not s:
        return None
    t = re.sub(r"<[^>]+>", "", s)
    t = html.unescape(t).strip()
    t = re.sub(r"\s+", " ", t)
    return t or None


def parse_episode_nums(ep_field: str) -> list[int]:
    if not ep_field or not re.search(r"\d", ep_field):
        return []
    nums: list[int] = []
    for part in re.split(r"[-–,/]", str(ep_field)):
        m = re.match(r"^(\d+)", part.strip())
        if m:
            nums.append(int(m.group(1)))
    return nums


def main() -> None:
    ratings = json.loads((ROOT / "ratings.json").read_text())
    show = json.loads(urllib.request.urlopen(TVMAZE, timeout=30).read())
    maze = show["_embedded"]["episodes"]
    by_sn = {
        (e["season"], e["number"]): strip_summary(e.get("summary"))
        for e in maze
        if e.get("number") is not None
    }

    missing = 0
    for e in ratings["episodes"]:
        parts: list[str] = []
        for n in parse_episode_nums(str(e["episode"])):
            s = by_sn.get((e["season"], n))
            if s:
                parts.append(s)
        uniq: list[str] = []
        seen: set[str] = set()
        for p in parts:
            if p not in seen:
                seen.add(p)
                uniq.append(p)
        if uniq:
            e["summary"] = " ".join(uniq)
        else:
            missing += 1
            title = re.sub(r"\s+", " ", e["title"]).strip()
            e["summary"] = f"Episode: {title}."

        # Only soft-label truly quiet episodes — never wipe real content notes / trope flags.
        flags = e.get("flags") or []
        themes = e.get("themes") or {"fine": [], "watch": []}
        has_watch = bool(themes.get("watch"))
        has_real_notes = any(
            x
            and not x.startswith("Mostly mild sitcom")
            and not x.startswith("No heavy sex")
            and not x.startswith("Friend-group")
            and not x.startswith("Apartment")
            and not x.startswith("Mostly kid-ok")
            and not x.startswith("Nothing standout")
            and not x.startswith("Almost no physical")
            and not x.startswith("Typical light")
            for x in (e.get("examples") or [])
        )
        if e["overall"] <= 2 and not flags and not has_watch and not has_real_notes:
            e["themes"] = {
                "fine": [
                    "Friend-group hangouts",
                    "Mostly mild sitcom banter — dating jokes stay light",
                ],
                "watch": [],
            }
            e["examples"] = e["themes"]["fine"]

    (ROOT / "ratings.json").write_text(
        json.dumps(ratings, indent=2, ensure_ascii=False) + "\n"
    )
    print(f"Summaries attached ({missing} fallbacks)")


if __name__ == "__main__":
    main()

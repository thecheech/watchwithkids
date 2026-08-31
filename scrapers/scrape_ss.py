#!/usr/bin/env python3
"""Scrape episode scripts from springfieldspringfield.co.uk.

Usage: python3 scrape_ss.py <show-slug> <site-slug> [--seasons 11,12] [--append]
Example: python3 scrape_ss.py modern-family modern-family
"""

from __future__ import annotations

import re
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

from common import TRANSCRIPTS, fetch, html_to_text, slugify, write_episode, write_index

BASE = "https://www.springfieldspringfield.co.uk/"
DELAY = 0.15

SEASON_RE = re.compile(r"episode_scripts\.php\?tv-show=[^&\"]+&season=(\d+)")
EPISODE_RE = re.compile(
    r'href="view_episode_scripts\.php\?tv-show=[^&"]+&amp;episode=(s(\d+)e(\d+))"[^>]*>([^<]*)</a>'
    r"|"
    r'href="view_episode_scripts\.php\?tv-show=[^&"]+&episode=(s(\d+)e(\d+))"[^>]*>([^<]*)</a>',
    re.I,
)
CONTAINER_RE = re.compile(
    r'<div class="scrolling-script-container[^"]*">(.*?)</div>', re.S | re.I
)


def get(url: str) -> str:
    time.sleep(DELAY)
    return fetch(url)


def episode_list(show_slug: str, only_seasons: set[int] | None = None) -> list[dict]:
    show_page = get(f"{BASE}episode_scripts.php?tv-show={show_slug}")
    seasons = sorted({int(s) for s in SEASON_RE.findall(show_page)})
    if only_seasons:
        seasons = [s for s in seasons if s in only_seasons]
    episodes = []
    for season in seasons:
        page = get(f"{BASE}episode_scripts.php?tv-show={show_slug}&season={season}")
        for m in EPISODE_RE.finditer(page):
            code, s, e = m.group(1) or m.group(5), m.group(2) or m.group(6), m.group(3) or m.group(7)
            title = (m.group(4) or m.group(8) or "").strip()
            episodes.append({
                "season": int(s), "episode": int(e), "code": code.lower(),
                "title": title,
                "url": f"{BASE}view_episode_scripts.php?tv-show={show_slug}&episode={code.lower()}",
            })
    seen, unique = set(), []
    for ep in episodes:
        if ep["code"] not in seen:
            seen.add(ep["code"])
            unique.append(ep)
    return unique


def scrape_episode(show: str, ep: dict) -> dict:
    page = get(ep["url"])
    m = CONTAINER_RE.search(page)
    if not m:
        raise ValueError("no script container")
    text = html_to_text(m.group(1))
    lines = text.splitlines()
    while lines and lines[0].strip().isdigit():
        lines.pop(0)
    text = "\n".join(lines).strip()
    if len(text.split()) < 50:
        raise ValueError("too short")
    title = re.sub(r"^\d+\.\s*", "", ep["title"]) or ep["code"]
    fname = f"{ep['code']}-{slugify(title)}.txt"
    ep["file"] = write_episode(show, fname, title, ep["url"], text)
    ep["words"] = len(text.split())
    return ep


def scrape_show(show: str, site_slug: str, only_seasons: set[int] | None = None,
                append: bool = False) -> None:
    episodes = episode_list(site_slug, only_seasons)
    print(f"[{show}] {len(episodes)} episodes listed", flush=True)

    results, failures = [], []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(scrape_episode, show, ep): ep for ep in episodes}
        for i, fut in enumerate(as_completed(futures), 1):
            try:
                results.append(fut.result())
            except Exception as exc:
                failures.append((futures[fut]["code"], str(exc)))
            if i % 50 == 0 or i == len(episodes):
                print(f"[{show}] {i}/{len(episodes)}", flush=True)

    results.sort(key=lambda e: (e["season"], e["episode"]))
    index = [
        {"season": e["season"], "episode": e["episode"], "title": e["title"],
         "words": e["words"], "url": e["url"], "file": e["file"]}
        for e in results
    ]
    if append:
        import json
        existing_path = TRANSCRIPTS / show / "episodes.json"
        if existing_path.exists():
            index = json.loads(existing_path.read_text()) + index
            index.sort(key=lambda e: (e["season"], e["episode"]))
    write_index(show, index)
    print(f"[{show}] saved {len(results)} episodes, {len(failures)} failures", flush=True)
    for code, err in failures[:10]:
        print(f"[{show}] FAIL {code}: {err[:100]}", flush=True)


if __name__ == "__main__":
    args = sys.argv[1:]
    seasons = None
    append = "--append" in args
    if append:
        args.remove("--append")
    if "--seasons" in args:
        i = args.index("--seasons")
        seasons = {int(s) for s in args[i + 1].split(",")}
        args = args[:i] + args[i + 2:]
    scrape_show(args[0], args[1], seasons, append)

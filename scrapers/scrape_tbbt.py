#!/usr/bin/env python3
"""Scrape The Big Bang Theory transcripts via the WordPress.com REST API."""

import html
import re

from common import fetch_json, html_to_text, slugify, write_episode, write_index

API = "https://public-api.wordpress.com/wp/v2/sites/bigbangtrans.wordpress.com/pages"
SHOW = "big-bang-theory"
SLUG_RE = re.compile(r"series-(\d+)-episode-(\d+)-(.+)")


def all_pages() -> list[dict]:
    pages, page = [], 1
    while True:
        data = fetch_json(f"{API}?per_page=100&page={page}&_fields=slug,title,content")
        if not data:
            return pages
        pages.extend(data)
        if len(data) < 100:
            return pages
        page += 1


def main() -> None:
    results, failures = [], []
    for p in all_pages():
        m = SLUG_RE.match(p["slug"])
        if not m:
            continue
        season, episode = int(m.group(1)), int(m.group(2))
        title = html.unescape(p["title"]["rendered"]).replace("\xa0", " ").strip()
        text = html_to_text(p["content"]["rendered"])
        if len(text.split()) < 50:
            failures.append(p["slug"])
            continue
        url = f"https://bigbangtrans.wordpress.com/{p['slug']}/"
        fname = f"s{season:02d}e{episode:02d}-{slugify(m.group(3))}.txt"
        file = write_episode(SHOW, fname, title, url, text)
        results.append({
            "season": season, "episode": episode, "title": title,
            "words": len(text.split()), "url": url, "file": file,
        })

    results.sort(key=lambda e: (e["season"], e["episode"]))
    write_index(SHOW, results)
    print(f"[{SHOW}] saved {len(results)} episodes, {len(failures)} failures")
    for f in failures[:10]:
        print(f"[{SHOW}] FAIL {f}")


if __name__ == "__main__":
    main()

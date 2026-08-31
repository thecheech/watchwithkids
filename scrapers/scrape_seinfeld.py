#!/usr/bin/env python3
"""Scrape all Seinfeld transcripts from seinfeldscripts.com."""

import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from common import fetch, html_to_text, slugify, write_episode, write_index

BASE = "https://www.seinfeldscripts.com/"
INDEX = BASE + "seinfeld-scripts.html"
SHOW = "seinfeld"

EP_RE = re.compile(
    r'<li class="ei-ep" data-season="(?P<season>\d+)" data-number="(?P<number>\d+)"[^>]*>'
    r'<a href="(?P<href>[^"]+)"[^>]*>(?P<title>[^<]+)</a>',
    re.I,
)


def scrape_episode(ep: dict) -> dict:
    page = fetch(ep["url"])
    page = re.sub(r"<!--\s*BeginAd.*?EndAd\s*-->", "", page, flags=re.S | re.I)
    page = re.sub(r"<table\b.*?</table>", "", page, flags=re.S | re.I)
    blocks = re.findall(r"<p[^>]*>(.*?)</p>", page, re.S | re.I)
    lines = []
    for b in blocks:
        t = html_to_text(b)
        if t and "Gift Guide" not in t:
            lines.append(t)
    text = "\n\n".join(lines)
    if len(text.split()) < 50:
        raise ValueError("too short")
    ep["words"] = len(text.split())
    fname = f"s{ep['season']:02d}e{ep['episode']:02d}-{slugify(ep['title'])}.txt"
    ep["file"] = write_episode(SHOW, fname, ep["title"], ep["url"], text)
    return ep


def main() -> None:
    index = fetch(INDEX)
    episodes = [
        {
            "season": int(m.group("season")),
            "episode": int(m.group("number")),
            "title": m.group("title").strip(),
            "url": BASE + m.group("href"),
        }
        for m in EP_RE.finditer(index)
    ]
    print(f"[{SHOW}] {len(episodes)} episodes in index", flush=True)

    results, failures = [], []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(scrape_episode, ep): ep for ep in episodes}
        for i, fut in enumerate(as_completed(futures), 1):
            try:
                results.append(fut.result())
            except Exception as exc:
                failures.append((futures[fut]["url"], str(exc)))
            if i % 25 == 0 or i == len(episodes):
                print(f"[{SHOW}] {i}/{len(episodes)}", flush=True)

    results.sort(key=lambda e: (e["season"], e["episode"]))
    for e in results:
        e.pop("text", None)
    write_index(SHOW, [
        {"season": e["season"], "episode": e["episode"], "title": e["title"],
         "words": e["words"], "url": e["url"], "file": e["file"]}
        for e in results
    ])
    print(f"[{SHOW}] saved {len(results)} episodes, {len(failures)} failures")
    for url, err in failures[:10]:
        print(f"[{SHOW}] FAIL {url}: {err[:120]}")


if __name__ == "__main__":
    main()

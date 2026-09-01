#!/usr/bin/env python3
"""Scrape Pokémon: The Beginning (Indigo League) transcripts from pokemon.fandom.com.

Transcripts live at "TB<nnn>: <title>/Transcript/International" subpages, so the
generic category scraper can't see them. Enumerate via allpages prefix instead.
"""

from __future__ import annotations

import re
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import common
from common import html_to_text, write_episode, write_index

API = "https://pokemon.fandom.com/api.php"
SHOW = "pokemon"
DELAY = 0.15


def api_get(params: dict) -> dict:
    time.sleep(DELAY)
    url = f"{API}?{urllib.parse.urlencode({**params, 'format': 'json'})}"
    return common.fetch_json(url)


def list_tb_transcripts() -> list[str]:
    titles: list[str] = []
    for prefix in ("TB0", "TB1"):
        cont: dict = {}
        while True:
            data = api_get({
                "action": "query", "list": "allpages",
                "apprefix": prefix, "aplimit": "500", **cont,
            })
            titles.extend(
                p["title"] for p in data.get("query", {}).get("allpages", [])
                if p["title"].endswith("/Transcript/International")
            )
            if "continue" not in data:
                break
            cont = data["continue"]
    return sorted(set(titles))


def parse_tb(title: str) -> tuple[int, str] | None:
    m = re.match(r"TB(\d+):\s*(.+?)/Transcript/International$", title)
    if not m:
        return None
    return int(m.group(1)), m.group(2).strip()


def fetch_transcript(title: str) -> tuple[str, str]:
    data = api_get({"action": "parse", "page": title, "prop": "text",
                    "redirects": "1", "format": "json"})
    parse = data.get("parse", {})
    return parse.get("title", title), html_to_text(parse.get("text", {}).get("*", ""))


def main() -> None:
    pages = [p for p in (parse_tb(t) for t in list_tb_transcripts()) if p]
    print(f"[{SHOW}] {len(pages)} TB transcript pages", flush=True)

    results, failures = [], []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {}
        for num, ep_title in pages:
            page = f"TB{num:03d}: {ep_title}/Transcript/International"
            futures[pool.submit(fetch_transcript, page)] = (num, ep_title, page)
        for i, fut in enumerate(as_completed(futures), 1):
            num, ep_title, page = futures[fut]
            try:
                _, text = fut.result()
                if len(text.split()) < 50:
                    failures.append({"title": page, "error": "too short"})
                    continue
                url = "https://pokemon.fandom.com/wiki/" + urllib.parse.quote(page.replace(" ", "_"))
                fname = f"tb{num:03d}-{common.slugify(ep_title, maxlen=100)}.txt"
                file = write_episode(SHOW, fname, ep_title, url, text)
                results.append({
                    "title": ep_title, "words": len(text.split()),
                    "url": url, "file": file, "tb": num,
                })
            except Exception as exc:
                failures.append({"title": page, "error": str(exc)})
            if i % 20 == 0 or i == len(pages):
                print(f"[{SHOW}] {i}/{len(pages)}", flush=True)

    results.sort(key=lambda e: e["tb"])
    write_index(SHOW, results)
    print(f"[{SHOW}] saved {len(results)} episodes, {len(failures)} failures", flush=True)
    for f_ in failures[:10]:
        print(f"[{SHOW}] FAIL {f_['title']}: {f_['error'][:120]}", flush=True)


if __name__ == "__main__":
    main()

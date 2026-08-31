#!/usr/bin/env python3
"""Generic MediaWiki transcript scraper (Fandom wikis + theinfosphere.org).

Lists all pages in Category:Transcripts, fetches rendered HTML via action=parse,
converts to plain text, writes transcripts/<show>/<slug>.txt + episodes.csv/json.

Usage: python3 scrape_wiki.py <show-slug> <api-url> [--skip PREFIX]... [--categories "Cat A|Cat B"]

Example: python3 scrape_wiki.py avatar https://avatar.fandom.com/api.php
"""

from __future__ import annotations

import re
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

import common
from common import html_to_text, slugify, write_episode, write_index

DELAY = 0.12


def api_get(api: str, params: dict) -> dict:
    time.sleep(DELAY)
    return common.fetch_json(f"{api}?{urllib.parse.urlencode(params)}")


def list_transcript_pages(api: str, categories: list[str]) -> list[str]:
    titles = []
    for category in categories:
        cont = {}
        while True:
            data = api_get(api, {
                "action": "query", "list": "categorymembers", "cmtitle": category,
                "cmtype": "page", "cmlimit": "500", "format": "json", **cont,
            })
            titles.extend(m["title"] for m in data.get("query", {}).get("categorymembers", []))
            if "continue" not in data:
                break
            cont = data["continue"]
    return titles


def keep_title(title: str, skip_prefixes: tuple[str, ...]) -> bool:
    if skip_prefixes and title.startswith(skip_prefixes):
        return False
    if title.startswith("Transcript:"):
        return True
    return ":" not in title.split("/")[0]


def clean_title(title: str) -> str:
    t = re.sub(r"^Transcript:", "", title)
    t = re.sub(r"/[Tt]ranscript$", "", t)
    t = re.sub(r"/[Ss]cript$", "", t)
    return t.strip()


def fetch_transcript(api: str, title: str) -> tuple[str, str]:
    data = api_get(api, {"action": "parse", "page": title, "prop": "text",
                         "redirects": "1", "format": "json"})
    parse = data.get("parse", {})
    return clean_title(parse.get("title", title)), html_to_text(parse.get("text", {}).get("*", ""))


def page_url(api: str, title: str) -> str:
    base = re.sub(r"/api\.php$", "/wiki/", api)
    return base + urllib.parse.quote(title.replace(" ", "_"))


def scrape_show(show: str, api: str, skip_prefixes: tuple[str, ...] = (),
                categories: list[str] | None = None) -> None:
    titles = sorted({t for t in list_transcript_pages(api, categories or ["Category:Transcripts"])
                     if keep_title(t, skip_prefixes)})
    print(f"[{show}] {len(titles)} transcript pages", flush=True)

    results, failures = [], []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(fetch_transcript, api, t): t for t in titles}
        for i, fut in enumerate(as_completed(futures), 1):
            t = futures[fut]
            try:
                clean, text = fut.result()
                if len(text.split()) < 50:
                    failures.append({"title": t, "error": "too short"})
                    continue
                url = page_url(api, t)
                file = write_episode(show, f"{slugify(clean, maxlen=120)}.txt", clean, url, text)
                results.append({"title": clean, "words": len(text.split()), "url": url, "file": file})
            except Exception as exc:
                failures.append({"title": t, "error": str(exc)})
            if i % 50 == 0 or i == len(titles):
                print(f"[{show}] {i}/{len(titles)}", flush=True)

    results.sort(key=lambda e: e["title"].lower())
    write_index(show, results)
    print(f"[{show}] saved {len(results)} episodes, {len(failures)} failures", flush=True)
    for f_ in failures[:10]:
        print(f"[{show}] FAIL {f_['title']}: {f_['error'][:120]}", flush=True)


if __name__ == "__main__":
    args = sys.argv[1:]
    categories = []
    if "--categories" in args:
        i = args.index("--categories")
        categories = args[i + 1].split("|")
        args = args[:i] + args[i + 2:]
    scrape_show(args[0], args[1], tuple(args[2:]), categories or None)

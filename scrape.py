#!/usr/bin/env python3
"""Scrape all Friends episode transcripts from edersoncorbari.github.io/friends."""

import csv
import html
import json
import re
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BASE = "https://edersoncorbari.github.io"
INDEX_URL = f"{BASE}/friends/"
OUT_DIR = Path(__file__).parent / "transcripts"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) watchwithkids-scraper/1.0"

LINK_RE = re.compile(
    r'<li><a href="(?P<href>/friends-scripts/season/(?P<code>[0-9]{4}(?:-[0-9]{4})?|07outtakes)\.html)"[^>]*>(?P<label>[^<]+)</a></li>'
)


def fetch(url: str, retries: int = 3) -> str:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2 * (attempt + 1))
    raise RuntimeError("unreachable")


def html_to_text(fragment: str) -> str:
    fragment = re.sub(r"(?i)<\s*(br|/p|/div|/h1|hr)[^>]*>", "\n", fragment)
    fragment = re.sub(r"<[^>]+>", "", fragment)
    text = html.unescape(fragment).replace("\xa0", " ")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    out: list[str] = []
    for line in lines:
        if line or (out and out[-1]):
            out.append(line)
    return "\n".join(out).strip()


def parse_index(page: str) -> list[dict]:
    episodes = []
    for m in LINK_RE.finditer(page):
        code = m.group("code")
        season = 7 if code == "07outtakes" else int(code[:2])
        episodes.append(
            {
                "season": season,
                "code": code,
                "index_title": html.unescape(m.group("label")).strip(),
                "url": BASE + m.group("href"),
            }
        )
    return episodes


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return re.sub(r"-{2,}", "-", slug)[:80]


def scrape_episode(ep: dict) -> dict:
    page = fetch(ep["url"])
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", page, re.S | re.I)
    ep["title"] = html_to_text(h1.group(1)) if h1 else ep["index_title"]
    body = re.search(r"<body[^>]*>(.*)</body>", page, re.S | re.I)
    ep["text"] = html_to_text(body.group(1) if body else page)

    if ep["code"] == "07outtakes":
        ep["episode"] = "special"
    else:
        nums = re.findall(r"\d+", ep["code"])
        first = nums[0]
        ep["episode"] = f"{int(first[2:]):02d}" if len(nums) == 1 else f"{int(first[2:]):02d}-{int(nums[1][2:]):02d}"
    ep["season_code"] = f"s{ep['season']:02d}"
    ep["episode_code"] = f"e{ep['episode']}"

    season_dir = OUT_DIR / f"season-{ep['season']:02d}"
    season_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{ep['season_code']}{ep['episode_code']}-{slugify(ep['index_title'])}.txt"
    path = season_dir / filename
    header = f"{ep['title']}\n{ep['index_title']} | {ep['url']}\n{'=' * 60}\n\n"
    path.write_text(header + ep["text"] + "\n", encoding="utf-8")
    ep["file"] = str(path.relative_to(OUT_DIR.parent))
    ep["words"] = len(ep["text"].split())
    return ep


def main() -> None:
    index_page = fetch(INDEX_URL)
    episodes = parse_index(index_page)
    print(f"Found {len(episodes)} transcript pages")

    results, failures = [], []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(scrape_episode, ep): ep for ep in episodes}
        for i, fut in enumerate(as_completed(futures), 1):
            ep = futures[fut]
            try:
                results.append(fut.result())
            except Exception as exc:
                failures.append({"code": ep["code"], "url": ep["url"], "error": str(exc)})
            if i % 25 == 0 or i == len(episodes):
                print(f"  {i}/{len(episodes)} done")

    results.sort(key=lambda e: e["code"])
    root = Path(__file__).parent

    with (root / "episodes.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["season", "episode", "code", "index_title", "title", "words", "url", "file"]
        )
        writer.writeheader()
        for e in results:
            writer.writerow({k: e[k] for k in writer.fieldnames})

    with (root / "episodes.json").open("w", encoding="utf-8") as f:
        json.dump(
            [
                {k: e[k] for k in ("season", "episode", "code", "index_title", "title", "words", "url", "file")}
                for e in results
            ],
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"Saved {len(results)} transcripts, index in episodes.csv / episodes.json")
    if failures:
        print(f"FAILURES ({len(failures)}):")
        for f_ in failures:
            print(f"  {f_['code']}: {f_['error']}")


if __name__ == "__main__":
    main()

"""Shared helpers for transcript scrapers."""

import csv
import html
import json
import re
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRANSCRIPTS = ROOT / "transcripts"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) watchwithkids-scraper/1.0"}


def fetch(url: str, retries: int = 3, timeout: int = 60) -> str:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2 * (attempt + 1))
    raise RuntimeError("unreachable")


def fetch_json(url: str, retries: int = 3) -> dict:
    return json.loads(fetch(url, retries=retries))


def html_to_text(fragment: str) -> str:
    fragment = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", "", fragment)
    fragment = re.sub(r"(?i)<\s*(br|/p|/div|/li|/dd|/dt|/dl|/h[1-6]|/tr|hr)[^>]*>", "\n", fragment)
    fragment = re.sub(r"<[^>]+>", "", fragment)
    text = html.unescape(fragment).replace("\xa0", " ").replace("\ufeff", "")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    out: list[str] = []
    for line in lines:
        if line or (out and out[-1]):
            out.append(line)
    return "\n".join(out).strip()


def slugify(title: str, maxlen: int = 80) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return re.sub(r"-{2,}", "-", slug)[:maxlen].strip("-") or "episode"


def write_episode(show: str, filename: str, title: str, url: str, text: str) -> str:
    show_dir = TRANSCRIPTS / show
    show_dir.mkdir(parents=True, exist_ok=True)
    path = show_dir / filename
    header = f"{title}\n{show} | {url}\n{'=' * 60}\n\n"
    path.write_text(header + text.strip() + "\n", encoding="utf-8")
    return str(path.relative_to(ROOT))


def write_index(show: str, episodes: list[dict]) -> None:
    show_dir = TRANSCRIPTS / show
    show_dir.mkdir(parents=True, exist_ok=True)
    fieldnames = list(episodes[0].keys()) if episodes else ["title", "words", "url", "file"]
    with (show_dir / "episodes.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for e in episodes:
            writer.writerow({k: e.get(k, "") for k in fieldnames})
    with (show_dir / "episodes.json").open("w", encoding="utf-8") as f:
        json.dump(episodes, f, indent=2, ensure_ascii=False)

"""Catalog hygiene: clean scraped titles and keep only real broadcast episodes.

Transcript sources are scraper dumps. Fandom wikis mix video games, marathons and
crossovers into the episode list; script sites leave numbering, series banners and
mis-decoded curly quotes in the title. Both make an episode count look invented, so
they are cleaned before anything is rated.
"""

from __future__ import annotations

import re
import unicodedata

from shows_meta import CANON_ONLY, NON_EPISODE_PATTERNS

_NON_EPISODE = [re.compile(p, re.I) for p in NON_EPISODE_PATTERNS]

# Mis-decoded UTF-8 that survived the scrape (cp1252 read as latin-1, or lost bytes).
MOJIBAKE = {
    "\ufffd": "'",
    "â€™": "'",
    "â€˜": "'",
    "â€œ": "“",
    "â€\x9d": "”",
    "â€“": "–",
    "â€”": "—",
    "â€¦": "…",
    "Â": "",
}

_SERIES_BANNER = re.compile(r"^\s*(?:friends|seinfeld|the office)\s*[\r\n]+", re.I)
# Production codes like 206 or S01E06 — not bare "10" in "10 & 1 Toilets".
_NUM_PREFIX = re.compile(
    r"^\s*(?:"
    r"s?\d{1,2}[ex]\d{1,3}"  # S01E06 / 1x06
    r"|\d{3,4}"  # production code 206
    r")\s*(?:[-–—:.]\s*|\s+)",
    re.I,
)
_WIKI_SUFFIX = re.compile(r"\s*\((?:episode|transcript|short|script)\)\s*$", re.I)
_DATE_SHORT = re.compile(r"^\d{1,2}-\d{1,2}$")
_SERIES_EP_PREFIX = re.compile(r"^series\s+\d+\s+episode\s+\d+\s*[-–—:]?\s*", re.I)
_RANGE_PREFIX = re.compile(r"^\s*\d{3,4}\s*[-–—]\s*\d{3,4}\s*[-–—:]?\s*")
_TRAILING_NOTE = re.compile(r"\s*\((?:\d+(?:st|nd|rd|th)\s+episode|part\s+\d+\s+of\s+\d+)\)\s*$", re.I)


def fix_mojibake(text: str) -> str:
    out = text
    for bad, good in MOJIBAKE.items():
        out = out.replace(bad, good)
    # Anything still un-decodable becomes an apostrophe rather than a black diamond.
    out = "".join(ch for ch in out if unicodedata.category(ch) != "Cc" or ch in "\n\t")
    return out


def clean_episode_title(title: str, fallback: str = "") -> str:
    """Strip scraper banners, numbering and mojibake from a scraped episode title."""
    t = fix_mojibake(str(title or ""))
    t = _SERIES_BANNER.sub("", t)
    t = re.sub(r"\s+", " ", t).strip()
    t = _SERIES_EP_PREFIX.sub("", t)
    t = _RANGE_PREFIX.sub("", t)
    t = _NUM_PREFIX.sub("", t)
    t = _WIKI_SUFFIX.sub("", t)
    t = _TRAILING_NOTE.sub("", t)
    t = t.strip(" -–—:·")

    if not t and fallback:
        return clean_episode_title(fallback)
    if not t:
        return "Untitled"

    # "the one with the lottery" → "The One With the Lottery"
    if t.islower() or t.isupper():
        small = {"a", "an", "and", "the", "of", "in", "on", "with", "to", "for", "at", "by"}
        words = t.lower().split()
        t = " ".join(
            w.capitalize() if i == 0 or w not in small else w for i, w in enumerate(words)
        )
    return t


def is_real_episode(show_id: str, title: str, season) -> bool:
    """False for video games, marathons, award shorts and other wiki filler."""
    text = str(title or "")
    if _DATE_SHORT.match(text.strip()):
        return False
    if any(p.search(text) for p in _NON_EPISODE):
        return False
    if show_id not in CANON_ONLY:
        return True
    if str(season) in ("0", "None", ""):
        return False
    return True


def episode_code(season, episode) -> str:
    """Broadcast code from season + episode number (letter segments preserved)."""
    ep = str(episode)
    if ep.isdigit():
        ep = ep.zfill(2)
    return f"{int(season):02d}{ep}"


def dedupe_codes(episodes: list[dict]) -> list[dict]:
    """
    Guarantee one page per episode.

    Scraped codes collide (two season-1 entries both landing on `0111a`), which
    silently overwrote episode pages and inflated the episode count.
    """
    seen: dict[str, int] = {}
    out = []
    for ep in episodes:
        code = str(ep.get("code") or "")
        if code in seen:
            seen[code] += 1
            ep = {**ep, "code": f"{code}-{seen[code]}"}
        else:
            seen[code] = 1
        out.append(ep)
    return out

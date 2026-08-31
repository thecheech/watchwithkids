#!/usr/bin/env python3
"""Build SHOWS.md — master index of all shows in transcripts/."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRANSCRIPTS = ROOT / "transcripts"

DISPLAY = {
    "friends": ("Friends", "edersoncorbari.github.io/friends"),
    "adventure-time": ("Adventure Time", "adventuretime.fandom.com"),
    "avatar": ("Avatar: The Last Airbender", "avatar.fandom.com"),
    "big-bang-theory": ("The Big Bang Theory", "bigbangtrans.wordpress.com + springfieldspringfield (S11-12)"),
    "bluey": ("Bluey", "blueypedia.fandom.com"),
    "bobs-burgers": ("Bob's Burgers", "springfieldspringfield.co.uk"),
    "brooklyn-nine-nine": ("Brooklyn Nine-Nine", "springfieldspringfield.co.uk"),
    "family-guy": ("Family Guy", "springfieldspringfield.co.uk"),
    "fresh-prince": ("The Fresh Prince of Bel-Air", "springfieldspringfield.co.uk"),
    "full-house": ("Full House", "springfieldspringfield.co.uk"),
    "futurama": ("Futurama", "theinfosphere.org"),
    "gravity-falls": ("Gravity Falls", "gravityfalls.fandom.com"),
    "how-i-met-your-mother": ("How I Met Your Mother", "springfieldspringfield.co.uk"),
    "malcolm-in-the-middle": ("Malcolm in the Middle", "springfieldspringfield.co.uk"),
    "modern-family": ("Modern Family", "springfieldspringfield.co.uk"),
    "parks-and-recreation": ("Parks and Recreation", "springfieldspringfield.co.uk"),
    "phineas-and-ferb": ("Phineas and Ferb", "phineasandferb.fandom.com"),
    "rick-and-morty": ("Rick and Morty", "springfieldspringfield.co.uk"),
    "seinfeld": ("Seinfeld", "seinfeldscripts.com"),
    "simpsons": ("The Simpsons", "Todd Schneider dataset (via GitHub)"),
    "south-park": ("South Park", "springfieldspringfield.co.uk"),
    "spongebob": ("SpongeBob SquarePants", "spongebob.fandom.com"),
    "steven-universe": ("Steven Universe", "steven-universe.fandom.com"),
    "the-office": ("The Office (US)", "brianbuie/the-office (GitHub)"),
    "young-sheldon": ("Young Sheldon", "springfieldspringfield.co.uk"),
}


def friends_index() -> dict:
    data = json.loads((ROOT / "episodes.json").read_text())
    return {
        "episodes": len(data),
        "seasons": len({e["season"] for e in data}),
        "words": sum(e.get("words", 0) for e in data),
    }


def main() -> None:
    rows = []
    friends = friends_index()
    rows.append(("friends", *DISPLAY["friends"], friends["seasons"], friends["episodes"], friends["words"]))

    for show_dir in sorted(TRANSCRIPTS.iterdir()):
        if not show_dir.is_dir() or show_dir.name.startswith("season-"):
            continue
        idx = show_dir / "episodes.json"
        if not idx.exists():
            continue
        data = json.loads(idx.read_text())
        seasons = {e["season"] for e in data if e.get("season")}
        words = sum(e.get("words", 0) for e in data)
        name, source = DISPLAY.get(show_dir.name, (show_dir.name, "?"))
        rows.append((show_dir.name, name, source, len(seasons), len(data), words))

    lines = [
        "# watchwithkids — shows",
        "",
        "Plain-text episode transcripts. Each show lives in `transcripts/<show>/` with its own",
        "`episodes.csv` / `episodes.json` index (Friends is at `transcripts/season-XX/` with the",
        "index at the project root for compatibility with the web app).",
        "",
        "| Show | Seasons | Transcript files | Words | Source |",
        "|------|---------|------------------|-------|--------|",
    ]
    total_eps = total_words = 0
    for slug, name, source, seasons, eps, words in sorted(rows, key=lambda r: r[1].lower()):
        link = "episodes.json" if slug == "friends" else f"transcripts/{slug}/"
        lines.append(f"| [{name}]({link}) | {seasons or '—'} | {eps} | {words:,} | {source} |")
        total_eps += eps
        total_words += words
    lines += [
        "",
        f"**Total: {len(rows)} shows, {total_eps:,} transcripts, {total_words:,} words.**",
        "",
        "Notes:",
        "- Friends: 228 files covering all 236 episodes (double episodes combined) + S7 outtakes special.",
        "- Seinfeld: 176/179 — the 3 clip-show specials have no script by design.",
        "- The Big Bang Theory: S1-10 from bigbangtrans (transcribed), S11-12 from springfieldspringfield (subtitle-derived).",
        "- The Simpsons: 564 episodes with script data (subtitle/script-line dataset, 1989-2016 era).",
        "- springfieldspringfield sources are subtitle-derived: dialogue without speaker names.",
        "- Fandom/Infosphere sources are fan transcripts with speaker names and scene directions.",
        "",
        "Scrapers live in `scrapers/` (`scrape_wiki.py` for MediaWiki/Fandom, `scrape_ss.py` for",
        "springfieldspringfield, `scrape_tbbt.py`, `scrape_seinfeld.py`, `convert_datasets.py`).",
        "Rebuild this file with `python3 scrapers/build_shows_index.py`.",
    ]
    (ROOT / "SHOWS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:30]))
    print(f"... ({len(rows)} shows)")


if __name__ == "__main__":
    main()

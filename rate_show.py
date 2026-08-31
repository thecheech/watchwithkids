#!/usr/bin/env python3
"""Rate any show folder under transcripts/ for kid-watchability."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path

from themes import build_themes, themes_as_examples

ROOT = Path(__file__).resolve().parent

SCALE = {
    "violence": "Physical harm, fights, scary injury, weapons (slapstick counts lightly).",
    "sex": "Sex talk, innuendo, affairs, nudity jokes, strippers, pregnancy/sex plots.",
    "language": "Swears, crude insults, sexual slang (damn/hell mild; stronger words higher).",
}

SEX_PATTERNS = [
    (r"\bsex\b", 3),
    (r"\bsexy\b", 1),
    (r"\bnaked\b", 2),
    (r"\bnude\b", 2),
    (r"\bunderwear\b", 1),
    (r"\bbra\b", 1),
    (r"\bpanties\b", 2),
    (r"\bcondom\b", 3),
    (r"\borgasm\b", 4),
    (r"\bhorny\b", 3),
    (r"\bvirgin\b", 2),
    (r"\bsleep(?:ing|s)? with\b", 3),
    (r"\bmake(?:s|ing)? out\b", 2),
    (r"\bhook(?:ed|ing)? up\b", 3),
    (r"\bstripper\b", 3),
    (r"\bstrip club\b", 3),
    (r"\bporn\b", 4),
    (r"\bpregnant\b", 1),
    (r"\baffair\b", 2),
    (r"\bthreesome\b", 4),
    (r"\bbreast(?:s)?\b", 2),
    (r"\bnipple\b", 3),
    (r"\bpenis\b", 4),
    (r"\bvagina\b", 4),
    (r"\bprostitut", 4),
    (r"\bmasturbat", 4),
    (r"\bviagra\b", 3),
]
LANG_PATTERNS = [
    (r"\bfuck", 5),
    (r"\bshit\b", 4),
    (r"\bbitch\b", 3),
    (r"\basshole\b", 3),
    (r"\bbastard\b", 2),
    (r"\bdamn\b", 1),
    (r"\bhell\b", 1),
    (r"\bass\b", 2),
    (r"\bcrap\b", 1),
    (r"\bscrew(?:ed|ing)?\b", 2),
    (r"\bsucks\b", 1),
    (r"\bpiss", 2),
    (r"\bwhore\b", 3),
    (r"\bslut\b", 3),
    (r"\bdick\b", 3),
    (r"\bcock\b", 4),
]
VIOL_PATTERNS = [
    (r"\bkill(?:s|ed|ing)?\b", 1),
    (r"\bmurder", 2),
    (r"\bgun\b", 2),
    (r"\bshoot(?:s|ing|shot)?\b", 2),
    (r"\bstab", 2),
    (r"\bblood\b", 1),
    (r"\bfight(?:s|ing)?\b", 1),
    (r"\bpunch(?:es|ed|ing)?\b", 2),
    (r"\bbeat(?:s|en|ing)? up\b", 2),
    (r"\battac", 1),
    (r"\bsuicide\b", 3),
    (r"\bexplod", 1),
    (r"\bdeath\b", 1),
    (r"\bdie[sd]?\b", 1),
]

# Show-agnostic high-signal floors
TROPE_RULES = [
    (
        "porn_plot",
        r"\bfree porn\b|\bporn channel\b|\bwatching porn\b|\bphone sex\b",
        5,
        "Porn / adult-channel plot.",
    ),
    (
        "stripper_plot",
        r"\bstripper\b|\bstrip club\b|\blap dance\b",
        4,
        "Stripper / strip-club plot.",
    ),
    (
        "explicit_body",
        r"\b(penis|vagina|orgasm|threesome|masturbat)\b",
        4,
        "Explicit sexual body / sex-act language.",
    ),
    (
        "kiss_bribe",
        r"kiss for (one|a|1|two) minutes?",
        4,
        "Kiss used as a bribe / performance.",
    ),
]

# Milder cartoon violence for kids animation
KIDS_SHOW_IDS = {"spongebob", "bluey", "phineas-and-ferb", "adventure-time", "avatar", "gravity-falls", "steven-universe"}

SHOW_META = {
    "seinfeld": {"name": "Seinfeld", "maze": "Seinfeld"},
    "spongebob": {"name": "SpongeBob SquarePants", "maze": "SpongeBob SquarePants"},
    "the-office": {"name": "The Office", "maze": "The Office"},
    "friends": {"name": "Friends", "maze": "Friends"},
    "how-i-met-your-mother": {
        "name": "How I Met Your Mother",
        "maze": "How I Met Your Mother",
    },
    "big-bang-theory": {
        "name": "The Big Bang Theory",
        "maze": "The Big Bang Theory",
    },
    "young-sheldon": {"name": "Young Sheldon", "maze": "Young Sheldon"},
    "malcolm-in-the-middle": {
        "name": "Malcolm in the Middle",
        "maze": "Malcolm in the Middle",
    },
    "rick-and-morty": {"name": "Rick and Morty", "maze": "Rick and Morty"},
    "family-guy": {"name": "Family Guy", "maze": "Family Guy"},
    "south-park": {"name": "South Park", "maze": "South Park"},
    "futurama": {"name": "Futurama", "maze": "Futurama"},
}


def score_from_hits(weighted_hits: int, tiers: list[tuple[int, int]]) -> int:
    score = 1
    for threshold, value in tiers:
        if weighted_hits >= threshold:
            score = value
    return score


def find_line(body: str, pat: str) -> str | None:
    for line in body.splitlines():
        if re.search(pat, line, re.I):
            cleaned = " ".join(line.split())
            if 12 < len(cleaned) < 160:
                return cleaned
    return None


def apply_tropes(body: str) -> dict:
    lower = body.lower()
    flags, min_sex = [], 1
    for name, pat, floor, _note in TROPE_RULES:
        if re.search(pat, lower, re.S):
            flags.append(name)
            min_sex = max(min_sex, floor)
    return {"flags": flags, "min_sex": min_sex}


def analyze_text(text: str, show_id: str) -> dict:
    body = text.split("=" * 20, 1)[-1] if "=" * 10 in text else text
    lower = body.lower()

    sex_weight = 0
    sex_hits = []
    for pat, w in SEX_PATTERNS:
        found = re.findall(pat, lower)
        if found:
            sex_hits.append((pat, len(found), w))
            sex_weight += len(found) * w

    lang_weight = 0
    for pat, w in LANG_PATTERNS:
        found = re.findall(pat, lower)
        if found:
            lang_weight += len(found) * w

    viol_weight = 0
    for pat, w in VIOL_PATTERNS:
        found = re.findall(pat, lower)
        if found:
            viol_weight += len(found) * w

    # Kids shows: cartoon violence is expected — softer curve
    if show_id in KIDS_SHOW_IDS:
        sex = score_from_hits(sex_weight, [(0, 1), (4, 2), (12, 3), (25, 4), (40, 5)])
        language = score_from_hits(lang_weight, [(0, 1), (3, 2), (8, 3), (16, 4), (30, 5)])
        violence = score_from_hits(viol_weight, [(0, 1), (8, 2), (20, 3), (40, 4), (70, 5)])
        violence = min(violence, 3)
    else:
        sex = score_from_hits(sex_weight, [(0, 1), (3, 2), (8, 3), (18, 4), (35, 5)])
        language = score_from_hits(lang_weight, [(0, 1), (2, 2), (6, 3), (14, 4), (28, 5)])
        violence = score_from_hits(viol_weight, [(0, 1), (3, 2), (8, 3), (16, 4), (28, 5)])
        violence = min(violence, 3)

    tropes = apply_tropes(body)
    sex = max(sex, tropes["min_sex"])

    themes = build_themes(
        body=body,
        show_id=show_id,
        sex=sex,
        language=language,
        violence=violence,
        flags=tropes["flags"],
    )

    return {
        "sex": sex,
        "language": language,
        "violence": violence,
        "themes": themes,
        "examples": themes_as_examples(themes),
        "flags": tropes["flags"],
    }


def verdict(score: int) -> str:
    return {
        1: "Usually fine",
        2: "Mild — okay for many kids with a parent",
        3: "Moderate — better for older kids / preteens",
        4: "Strong — skip for little kids",
        5: "Heavy — not kid-friendly",
    }[score]


def load_episodes(show_id: str) -> list[dict]:
    if show_id == "friends":
        return json.loads((ROOT / "episodes.json").read_text())
    path = ROOT / "transcripts" / show_id / "episodes.json"
    return json.loads(path.read_text())


def normalize_ep(show_id: str, raw: dict, idx: int) -> dict:
    season = raw.get("season")
    episode = raw.get("episode")
    title = raw.get("title") or "Untitled"
    file_rel = raw.get("file")
    if show_id == "friends":
        return {
            "season": raw["season"],
            "episode": raw["episode"],
            "code": raw.get("code") or f"{raw['season']:02d}{raw['episode']}",
            "title": raw["title"],
            "index_title": raw.get("index_title") or raw["title"],
            "url": raw.get("url"),
            "file": raw["file"],
        }

    # SpongeBob / wiki dumps often lack season numbers — parse from transcript header if possible
    if season is None and file_rel:
        text = (ROOT / file_rel).read_text(errors="replace")[:2500]
        m = re.search(r"Season\s*[№No.#:]*\s*(\d+)", text, re.I)
        if m:
            season = int(m.group(1))
        m2 = re.search(r"Episode\s*[№No.#:]*\s*([0-9]+[a-z]?)", text, re.I)
        if m2 and episode is None:
            episode = m2.group(1)

    if season is None:
        season = 0
    if episode is None:
        episode = idx + 1

    code = f"{int(season):02d}{str(episode).zfill(2) if str(episode).isdigit() else episode}"
    return {
        "season": int(season) if str(season).isdigit() else season,
        "episode": episode,
        "code": code,
        "title": title,
        "index_title": title,
        "url": raw.get("url"),
        "file": file_rel,
    }


def rate_show(show_id: str) -> dict:
    meta = SHOW_META.get(show_id, {"name": show_id})
    raw_eps = load_episodes(show_id)
    ratings = []
    for i, raw in enumerate(raw_eps):
        ep = normalize_ep(show_id, raw, i)
        path = ROOT / ep["file"]
        text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
        h = analyze_text(text, show_id) if text else {
            "sex": 2,
            "language": 2,
            "violence": 1,
            "themes": {"fine": [], "watch": []},
            "examples": [],
            "flags": [],
        }
        o = max(h["violence"], h["sex"], h["language"])
        ratings.append({
            "season": ep["season"],
            "episode": ep["episode"],
            "code": ep["code"],
            "title": ep["title"],
            "index_title": ep["index_title"],
            "url": ep.get("url"),
            "file": ep["file"],
            "summary": None,
            "violence": h["violence"],
            "sex": h["sex"],
            "language": h["language"],
            "overall": o,
            "verdict": verdict(o),
            "themes": h["themes"],
            "examples": h["examples"],
            "notes": None,
            "flags": h["flags"],
            "source": "heuristic",
        })

    out = {
        "show": meta["name"],
        "show_id": show_id,
        "scale": {
            "min": 1,
            "max": 5,
            "meaning": SCALE,
            "labels": {
                "1": "None / fine",
                "2": "Mild",
                "3": "Moderate",
                "4": "Strong",
                "5": "Heavy",
            },
        },
        "disclaimer": (
            "Informal parental guidance from transcript signals — "
            "not an official rating. Taste varies by family."
        ),
        "count": len(ratings),
        "episodes": ratings,
    }

    out_dir = ROOT / "ratings"
    out_dir.mkdir(exist_ok=True)
    (out_dir / f"{show_id}.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")

    with (out_dir / f"{show_id}.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["season", "episode", "code", "title", "violence", "sex", "language", "overall", "verdict", "example_1"])
        for r in ratings:
            ex = (r["examples"] or [""])[0]
            w.writerow([r["season"], r["episode"], r["code"], r["title"], r["violence"], r["sex"], r["language"], r["overall"], r["verdict"], ex])

    dist = Counter(r["overall"] for r in ratings)
    print(f"{show_id}: {len(ratings)} eps → ratings/{show_id}.json  dist={dict(sorted(dist.items()))}")
    return out


def main() -> None:
    import sys
    shows = sys.argv[1:] or ["seinfeld", "spongebob", "the-office"]
    for s in shows:
        rate_show(s)


if __name__ == "__main__":
    main()

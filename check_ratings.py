#!/usr/bin/env python3
"""Acceptance tests for the taxonomy and classifier.

Run after re-rating and before building:  python3 check_ratings.py
Exit code is non-zero if any rule regressed.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from shows_meta import episode_age, meta_for
from themes import CANONICAL_WATCH, OPT_IN_THEMES, THEME_GROUP

ROOT = Path(__file__).resolve().parent
RETIRED = {"Gay / Lesbian", "Violence & death", "Alcohol / Drugs", "Racism", "Porn / strippers"}

failures: list[str] = []
checks = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global checks
    checks += 1
    if not ok:
        failures.append(f"{name}{f' — {detail}' if detail else ''}")


def load(show_id: str) -> dict | None:
    path = ROOT / "ratings.json" if show_id == "friends" else ROOT / "ratings" / f"{show_id}.json"
    return json.loads(path.read_text()) if path.exists() else None


def episode(data: dict, code: str) -> dict | None:
    return next((e for e in data["episodes"] if str(e["code"]) == code), None)


def theme(ep: dict, name: str) -> dict | None:
    return next(
        (d for d in ep["themes"].get("watch_detail") or [] if d["theme"] == name), None
    )


def instances(ep: dict) -> list[tuple[str, str]]:
    out = []
    for d in ep["themes"].get("watch_detail") or []:
        for inst in d.get("instances") or []:
            out.append((d["theme"], inst.get("text") or ""))
    return out


# ── taxonomy ──────────────────────────────────────────────────────────────────

check("Retired labels are gone from the default list", not (RETIRED & set(CANONICAL_WATCH)))
check("LGBTQ themes is opt-in only", "LGBTQ themes" not in CANONICAL_WATCH)
check("LGBTQ themes is not in a scored group", THEME_GROUP["LGBTQ themes"] == "optin")
check(
    "Homophobic jokes sit under bias, not sex",
    THEME_GROUP["Homophobic jokes"] == "bias",
)

# ── per-show rules ────────────────────────────────────────────────────────────

friends = load("friends")
if friends:
    pilot = episode(friends, "0101")
    check("Friends pilot exists", pilot is not None)
    if pilot:
        alcohol = theme(pilot, "Alcohol & drugs")
        n = alcohol["count"] if alcohol else 0
        check("Friends S1E1 alcohol moments <= 2", n <= 2, f"got {n}")
        wine = [t for t, txt in instances(pilot) if "wine guy" in txt.lower()]
        check("Friends S1E1 does not read 'Wine Guy' as drinking", not wine, str(wine[:3]))
        check(
            "Friends S1E1 Carol is not a default watch-for",
            not any(d["theme"] in OPT_IN_THEMES for d in pilot["themes"]["watch_detail"]),
        )

    for ep in friends["episodes"]:
        got = {d["theme"] for d in ep["themes"].get("watch_detail") or []}
        bad = got & RETIRED
        if bad:
            check(f"Friends {ep['code']} uses current labels", False, str(bad))
            break
    else:
        check("Friends uses current labels throughout", True)

    dirty = [e["title"] for e in friends["episodes"] if "\ufffd" in e["title"] or "\n" in e["title"]]
    check("Friends titles are clean", not dirty, str(dirty[:3]))
    numbered = [e["title"] for e in friends["episodes"] if e["title"][:3].isdigit()]
    check("Friends titles have no leading episode numbers", not numbered, str(numbered[:3]))

spongebob = load("spongebob")
if spongebob:
    lgbtq = [
        e["code"]
        for e in spongebob["episodes"]
        if any(d["theme"] in OPT_IN_THEMES for d in e["themes"].get("watch_detail") or [])
    ]
    check("SpongeBob has zero LGBTQ flags in default watch-fors", not lgbtq, str(lgbtq[:5]))

    pilot = next((e for e in spongebob["episodes"] if e["title"].startswith("Help Wanted")), None)
    if pilot:
        check("SpongeBob pilot violence is slapstick (1)", pilot["violence"] == 1, str(pilot["violence"]))
    hot = [e["code"] for e in spongebob["episodes"] if e["violence"] > 3]
    check("No SpongeBob episode is rated adult-level violence", not hot, f"{len(hot)} over")
    gray = [e for e in spongebob["episodes"] if e["violence"] > 2]
    check(
        "SpongeBob violence is slapstick almost everywhere",
        len(gray) / max(len(spongebob["episodes"]), 1) < 0.02,
        f"{len(gray)} of {len(spongebob['episodes'])}",
    )

    codes = [str(e["code"]) for e in spongebob["episodes"]]
    check("SpongeBob episode codes are unique", len(codes) == len(set(codes)))
    junk = [
        e["title"]
        for e in spongebob["episodes"]
        if "kids' choice" in e["title"].lower() or "marathon" in e["title"].lower()
    ]
    check("SpongeBob catalog holds no award shorts or marathons", not junk, str(junk[:3]))

rm = load("rick-and-morty")
if rm:
    pilot = episode(rm, "0101")
    if pilot:
        seen: dict[str, list[str]] = {}
        for t, txt in instances(pilot):
            seen.setdefault(txt.strip().lower(), []).append(t)
        shared = {txt: ts for txt, ts in seen.items() if len(set(ts)) > 1}
        check(
            "Rick and Morty S1E1 never files one quote under several themes",
            not shared,
            str(list(shared.values())[:2]),
        )

# ── classifier false positives ────────────────────────────────────────────────

def instance_texts(ep: dict | None) -> list[str]:
    if not ep:
        return []
    out: list[str] = []
    for detail in ep["themes"].get("watch_detail") or []:
        for inst in detail.get("instances") or []:
            out.append(inst.get("text") or "")
    return out


def no_phrase(ep: dict | None, phrase: str) -> bool:
    needle = phrase.lower()
    return not any(needle in t.lower() for t in instance_texts(ep))


phineas = load("phineas-and-ferb")
if phineas:
    chip = next((e for e in phineas["episodes"] if "chip to the vet" in e["title"].lower()), None)
    check("Phineas chipping gun is not Violence", no_phrase(chip, "chipping gun"))

seinfeld = load("seinfeld")
if seinfeld:
    pilot = episode(seinfeld, "0101")
    check("Seinfeld pilot murder investigation is not Violence", no_phrase(pilot, "murder investigation"))

parks = load("parks-and-recreation")
if parks:
    pilot = episode(parks, "0101")
    check("Parks pilot bigger guns is not Violence", no_phrase(pilot, "bigger gun"))

kpop = load("kpop-demon-hunters")
if kpop:
    movie = kpop["episodes"][0] if kpop["episodes"] else None
    check("KPop blood idiom is not Violence", no_phrase(movie, "blood and tears"))
    check("KPop bleeding lyric is not Violence", no_phrase(movie, "bleeding isn't in my blood"))
    if movie:
        check("KPop is season 0 movie slot", str(movie.get("season")) == "0", str(movie.get("season")))

full_house = load("full-house")
if full_house:
    pilot = episode(full_house, "0101")
    if pilot:
        check(
            "Full House pilot score has evidence or stays at 1",
            pilot["overall"] <= 1 or bool(pilot["themes"].get("watch_detail")),
            f"overall={pilot['overall']}",
        )

# ── kids catalog air order ────────────────────────────────────────────────────

bluey = load("bluey")
if bluey:
    army = next((e for e in bluey["episodes"] if e["title"] == "Army"), None)
    if army:
        check("Bluey Army is S2E16 not wiki-alpha Ep 1", army["season"] == 2 and army["episode"] == 16, str(army))
    first = min(
        bluey["episodes"],
        key=lambda e: (int(e["season"]), int(e["episode"]) if str(e["episode"]).isdigit() else e["episode"]),
    )
    check("Bluey air order starts at S1E2 Hospital", first["title"] == "Hospital", first["title"])

gravity = load("gravity-falls")
if gravity:
    first = min(
        gravity["episodes"],
        key=lambda e: (int(e["season"]), int(e["episode"]) if str(e["episode"]).isdigit() else e["episode"]),
    )
    check(
        "Gravity Falls S1E1 is Tourist Trapped",
        "tourist trapped" in first["title"].lower(),
        first["title"],
    )
    junk = [e["title"] for e in gravity["episodes"] if re.match(r"^\d{1,2}-\d{1,2}$", e["title"])]
    check("Gravity Falls has no date-code cryptogram junk", not junk, str(junk[:3]))

if spongebob:
    first = min(
        spongebob["episodes"],
        key=lambda e: (int(e["season"]), int(e["episode"]) if str(e["episode"]).isdigit() else e["episode"]),
    )
    check("SpongeBob S1E1 is Help Wanted", first["title"] == "Help Wanted", first["title"])


for show_id in [
    "friends", "seinfeld", "spongebob", "the-office", "how-i-met-your-mother",
    "big-bang-theory", "young-sheldon", "malcolm-in-the-middle", "rick-and-morty",
    "family-guy", "south-park", "futurama", "parks-and-recreation", "modern-family",
]:
    data = load(show_id)
    if not data:
        continue
    floor = meta_for(show_id)["floor"]
    bad_age = [e["code"] for e in data["episodes"] if e.get("age", 0) < floor]
    check(f"{show_id}: no episode is rated below the show floor", not bad_age, str(bad_age[:3]))

    dupes = [
        e["code"]
        for e in data["episodes"]
        if len({d["theme"] for d in e["themes"].get("watch_detail") or []})
        != len(e["themes"].get("watch_detail") or [])
    ]
    check(f"{show_id}: one block per theme", not dupes, str(dupes[:3]))

    missing_mode = [
        e["code"]
        for e in data["episodes"]
        for d in e["themes"].get("watch_detail") or []
        for inst in d.get("instances") or []
        if not inst.get("mode") or not inst.get("intensity")
    ]
    check(
        f"{show_id}: every moment carries mode + intensity",
        not missing_mode,
        str(missing_mode[:3]),
    )

    check(
        f"{show_id}: episode age matches its score",
        all(e.get("age") == episode_age(show_id, e["overall"]) for e in data["episodes"]),
    )


print(f"{checks - len(failures)}/{checks} checks passed")
for f in failures:
    print(f"  FAIL  {f}")
sys.exit(1 if failures else 0)

"""Per-show editorial metadata: audience shelf, age bands, catalog hygiene rules.

Age bands are editorial calls, not model output. `age` is the headline band for the
series as a whole; `floor` is the youngest age a genuinely mild episode of that show
suits. An episode band is never below the show's floor, so a 1/5 South Park episode
still reads "14+" rather than "6+".
"""

from __future__ import annotations

# shelf: "kids"    — made for children
#        "rewatch" — adult sitcoms parents rewatch with older kids in the room
#        "adult"   — adult animation, rated so you know which episodes are roughest
SHOWS = {
    "friends": {
        "name": "Friends",
        "shelf": "rewatch",
        "age": 13,
        "floor": 10,
        "format": "live-action sitcom",
        "note": "Dating and hookup talk is constant; the violence is slapstick.",
    },
    "seinfeld": {
        "name": "Seinfeld",
        "shelf": "rewatch",
        "age": 13,
        "floor": 10,
        "format": "live-action sitcom",
        "note": "Adult premises played dry — most of it goes over younger heads.",
    },
    "the-office": {
        "name": "The Office",
        "shelf": "rewatch",
        "age": 13,
        "floor": 10,
        "format": "live-action sitcom",
        "note": "Workplace cringe, sexual-harassment jokes, occasional crude bits.",
    },
    "parks-and-recreation": {
        "name": "Parks and Recreation",
        "shelf": "rewatch",
        "age": 12,
        "floor": 10,
        "format": "live-action sitcom",
        "note": "Gentler than most workplace sitcoms; innuendo is the main thing.",
    },
    "how-i-met-your-mother": {
        "name": "How I Met Your Mother",
        "shelf": "rewatch",
        "age": 14,
        "floor": 12,
        "format": "live-action sitcom",
        "note": "Built around casual sex and bar life more than any show on this shelf.",
    },
    "big-bang-theory": {
        "name": "The Big Bang Theory",
        "shelf": "rewatch",
        "age": 12,
        "floor": 10,
        "format": "live-action sitcom",
        "note": "More innuendo than the science jokes suggest, but rarely explicit.",
    },
    "modern-family": {
        "name": "Modern Family",
        "shelf": "rewatch",
        "age": 11,
        "floor": 9,
        "format": "live-action sitcom",
        "note": "Family-first; adult plots are talked around rather than shown.",
    },
    "malcolm-in-the-middle": {
        "name": "Malcolm in the Middle",
        "shelf": "rewatch",
        "age": 11,
        "floor": 9,
        "format": "live-action sitcom",
        "note": "Chaotic family comedy with rough sibling behaviour to talk about.",
    },
    "young-sheldon": {
        "name": "Young Sheldon",
        "shelf": "rewatch",
        "age": 10,
        "floor": 8,
        "format": "live-action sitcom",
        "note": "The mildest of the rewatch shelf — occasional grown-up subplots.",
    },
    "futurama": {
        "name": "Futurama",
        "shelf": "rewatch",
        "age": 13,
        "floor": 11,
        "format": "adult animation",
        "note": "Cartoon sci-fi, but written for adults — crude gags and dark jokes.",
    },
    "spongebob": {
        "name": "SpongeBob SquarePants",
        "shelf": "kids",
        "age": 6,
        "floor": 6,
        "format": "kids animation",
        "note": "Made for children. Slapstick and name-calling are the usual flags.",
    },
    "rick-and-morty": {
        "name": "Rick and Morty",
        "shelf": "adult",
        "age": 16,
        "floor": 14,
        "format": "adult animation",
        "note": "TV-MA. Rated here so you know which episodes are roughest, not because it is kids TV.",
    },
    "family-guy": {
        "name": "Family Guy",
        "shelf": "adult",
        "age": 16,
        "floor": 14,
        "format": "adult animation",
        "note": "TV-MA. Rated here so you know which episodes are roughest, not because it is kids TV.",
    },
    "south-park": {
        "name": "South Park",
        "shelf": "adult",
        "age": 16,
        "floor": 14,
        "format": "adult animation",
        "note": "TV-MA. Rated here so you know which episodes are roughest, not because it is kids TV.",
    },
    "wednesday": {
        "name": "Wednesday",
        "shelf": "rewatch",
        "age": 14,
        "floor": 11,
        "format": "live-action fantasy",
        "note": "Macabre boarding-school mystery — murder, monsters and deadpan dark humor.",
    },
    "kpop-demon-hunters": {
        "name": "KPop Demon Hunters",
        "shelf": "kids",
        "age": 8,
        "floor": 8,
        "format": "animated movie",
        "note": "Animated movie — demon battles throughout; the villain preys on shame and fear.",
    },
    # Not yet rated — used for the "coming soon" shelves so the homepage can still
    # sort them into the right audience.
    "bluey": {"name": "Bluey", "shelf": "kids", "age": 4, "floor": 4, "format": "kids animation"},
    "phineas-and-ferb": {
        "name": "Phineas and Ferb", "shelf": "kids", "age": 6, "floor": 6,
        "format": "kids animation",
    },
    "gravity-falls": {
        "name": "Gravity Falls", "shelf": "kids", "age": 8, "floor": 8,
        "format": "kids animation",
    },
    "adventure-time": {
        "name": "Adventure Time", "shelf": "kids", "age": 8, "floor": 7,
        "format": "kids animation",
    },
    "steven-universe": {
        "name": "Steven Universe", "shelf": "kids", "age": 7, "floor": 7,
        "format": "kids animation",
    },
    "avatar": {
        "name": "Avatar: The Last Airbender", "shelf": "kids", "age": 8, "floor": 8,
        "format": "kids animation",
    },
    "full-house": {
        "name": "Full House", "shelf": "kids", "age": 7, "floor": 7,
        "format": "live-action sitcom",
    },
    "fresh-prince": {
        "name": "The Fresh Prince of Bel-Air", "shelf": "rewatch", "age": 11, "floor": 9,
        "format": "live-action sitcom",
    },
    "brooklyn-nine-nine": {
        "name": "Brooklyn Nine-Nine", "shelf": "rewatch", "age": 13, "floor": 11,
        "format": "live-action sitcom",
    },
    "simpsons": {
        "name": "The Simpsons", "shelf": "rewatch", "age": 10, "floor": 9,
        "format": "animation",
    },
    "bobs-burgers": {
        "name": "Bob's Burgers", "shelf": "rewatch", "age": 11, "floor": 9,
        "format": "animation",
    },
}

SHELVES = {
    "rewatch": {
        "title": "Rewatch with the kids",
        "blurb": "Adult sitcoms you already love, episode by episode, so you know what lands "
        "in front of a 10–16-year-old.",
    },
    "kids": {
        "title": "Made for kids",
        "blurb": "Shows written for children. We flag the odd rough episode so you can skip it.",
    },
    "adult": {
        "title": "Adult cartoons",
        "blurb": "TV-MA. Rated so you know which episodes are especially rough — not because "
        "this is kids TV.",
    },
}

SHELF_ORDER = ["rewatch", "kids", "adult"]

# Overall score → the youngest age that score alone suggests.
SCORE_AGE = {1: 6, 2: 8, 3: 10, 4: 13, 5: 16}

DEFAULT_META = {
    "shelf": "rewatch",
    "age": 13,
    "floor": 10,
    "format": "sitcom",
    "note": "",
}


def meta_for(show_id: str) -> dict:
    return {**DEFAULT_META, "name": show_id, **SHOWS.get(show_id, {})}


def shelf_of(show_id: str) -> str:
    return meta_for(show_id)["shelf"]


def show_age(show_id: str) -> int:
    return int(meta_for(show_id)["age"])


def episode_age(show_id: str, overall: int) -> int:
    """'Best for about X+' for a single episode, never below the show's floor."""
    meta = meta_for(show_id)
    return max(int(meta["floor"]), SCORE_AGE.get(int(overall), 13))


def age_label(age: int) -> str:
    return f"{int(age)}+"


def bucket_for_age(show_id: str, overall: int, household_age: int | None = None) -> str:
    """Traffic-light bucket. With no household age this is relative to the show's own floor."""
    ep_age = episode_age(show_id, overall)
    target = household_age if household_age else meta_for(show_id)["floor"]
    if ep_age <= target:
        return "safe"
    if ep_age <= target + 2:
        return "maybe"
    return "skip"


# ── catalog hygiene ───────────────────────────────────────────────────────────

# Titles that are not broadcast episodes: video games, marathons, award-show shorts,
# behind-the-scenes filler and crossovers from other series. Applied to shows whose
# transcript source is a fandom wiki dump.
NON_EPISODE_PATTERNS = [
    r"\bkids'? choice awards?\b",
    r"\bmarathon\b",
    r"\bbehind the (?:scenes|pantis)\b",
    r"\b(?:game boy advance|home console|nintendo|playstation|xbox|video game)\b",
    r"\blivestream\b",
    r"\b(?:trailer|teaser|promo|commercial|advert)\b",
    r"\bsneak peek\b",
    r"\b(?:music video|theme song|opening)\b",
    r"\bchuckie finster\b",  # Rugrats crossover filler
    r"\bpanel\b",
    r"\bcomic[- ]con\b",
    r"\binterview\b",
    r"\bcompilation\b",
    r"\bshort film\b",
    r"\bstage show\b",
    r"\bthe patrick star show\b",
    r"\bkamp koral\b",
]

# Shows where season 0 / unnumbered entries are wiki noise rather than real specials.
CANON_ONLY = {"spongebob"}

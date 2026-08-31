"""Parent-facing theme summaries — short closed vocabulary + per-episode 'how'."""

from __future__ import annotations

import re

# Closed list used in UI filters (keep short).
CANONICAL_WATCH = [
    "Sex & hookups",
    "Nudity & bodies",
    "Porn / strippers",
    "Swearing",
    "Violence & death",
    "Affairs / cheating",
    "Suicide / self-harm",
    "Alcohol / Drugs",
    "Gay / Lesbian",
    "Fat-shaming",
    "Slut-shaming",
    "Racism",
]

# (pattern, canonical label, severity 1–5)
SEX_THEMES = [
    (r"\bporn\b|\bphone sex\b", "Porn / strippers", 5),
    (r"\bstripper\b|\bstrip club\b|\blap dance\b", "Porn / strippers", 4),
    (r"\b(orgasm|threesome|masturbat)\b", "Sex & hookups", 5),
    (r"\b(penis|vagina|nipple)\b", "Nudity & bodies", 4),
    (r"\bprostitut", "Sex & hookups", 4),
    (r"\bwhore\b|\bslut\b|\bskank\b|\btramp\b", "Slut-shaming", 4),
    (r"\bcondom\b|\bviagra\b|\bimpoten|\bsperm\b|\binsemination\b", "Sex & hookups", 3),
    (r"\bsleep(?:ing|s)? with\b|\bhook(?:ed|ing)? up\b|\bhave sex\b|\bhad sex\b", "Sex & hookups", 3),
    (r"\bhorny\b|\bvirgin\b", "Sex & hookups", 3),
    (r"\baffair\b|\bcheat(?:s|ing|ed)?\b|\bon a break\b", "Affairs / cheating", 3),
    (r"\bmake(?:s|ing)? out\b|\bkiss(?:es|ed|ing)?\b", "Sex & hookups", 2),
    (r"\bnaked\b|\bnude\b", "Nudity & bodies", 2),
    (r"\bunderwear\b|\bbra\b|\bpanties\b", "Nudity & bodies", 2),
    (r"\bbreast(?:s|feeding)?\b", "Nudity & bodies", 2),
    (r"\bsexy\b|\bsex\b", "Sex & hookups", 2),
]

IDENTITY_THEMES = [
    (r"\blesbian\b|\bgay\b|\bhomosexual\b|\bqueer\b|\bbisexual\b|\bcoming out\b|\bsame[- ]sex\b", "Gay / Lesbian", 2),
    (r"\bdrag queen\b|\bin drag\b|\bdrag show\b|\btrans(?:gender|vestite)\b", "Gay / Lesbian", 2),
]

SUBSTANCE_THEMES = [
    (r"\bcocaine\b|\bheroin\b|\bmeth(?:amphetamine)?\b|\becstasy\b|\bacid trip\b", "Alcohol / Drugs", 4),
    (
        r"\bmarijuana\b|\bweed\b|\bstoned\b|\bpothead\b|\bsmok\w*\s+(?:a\s+)?(?:pot|joint|weed)\b"
        r"|\bpot brownies?\b|\bdrug dealer\b|\bgetting high\b|\bhigh as a kite\b",
        "Alcohol / Drugs",
        3,
    ),
    (r"\bdrunk\b|\bdrunken\b|\bhangover\b|\bbooze\b|\bwasted\b|\bintoxicated\b", "Alcohol / Drugs", 2),
    (r"\bbeer\b|\bwine\b|\bvodka\b|\btequila\b|\bwhiskey\b|\bchampagne\b|\bcocktail\b|\bmargarita\b", "Alcohol / Drugs", 2),
    (r"\bdrinking\b|\bgot drunk\b|\bget drunk\b|\bshots? of (?:vodka|tequila|whiskey|rum)\b", "Alcohol / Drugs", 2),
]

HARM_THEMES = [
    (r"\bfat (?:monica|girl|chick|ass|pig|suit)\b|\bfatty\b|\bobese\b|\byou'?re fat\b|\bso fat\b|\blose weight\b|\blard\b", "Fat-shaming", 3),
    (r"\bfat\b.{0,20}\b(joke|laugh|mock|tease|insult|call)", "Fat-shaming", 2),
    (r"\b(big|huge) (?:cow|pig|whale)\b|\bcow\b.{0,12}\bfat\b", "Fat-shaming", 3),
    (r"\bskank\b|\btramp\b|\beasy\b.{0,12}(?:girl|woman)|sleeps? around\b|\bloose\b.{0,10}(?:girl|woman)", "Slut-shaming", 3),
    (r"\bslut[- ]?sham", "Slut-shaming", 4),
    (r"\bracis(?:t|m)\b|\bbigot(?:ed|ry)?\b|\bxenophob", "Racism", 4),
    (r"\bblackface\b|\byellowface\b|\bbrownface\b", "Racism", 5),
    (r"\bnigg(?:er|a)\b|\bchink\b|\bspic\b|\bkike\b|\bwetto?back\b|\bgook\b", "Racism", 5),
    (r"\ball .+ look alike\b|\bchinese (?:fire drill|accent)\b|\bching chong\b", "Racism", 4),
]

LANG_THEMES = [
    (r"\bfuck", "Swearing", 5),
    (r"\bshit\b|\basshole\b|\bbitch\b|\bdick\b|\bcock\b", "Swearing", 3),
    (r"\bass\b|\bpiss|\bscrew(?:ed|ing)?\b|\bbastard\b", "Swearing", 2),
    (r"\bdamn\b|\bhell\b|\bcrap\b", "Swearing", 1),
]

VIOL_THEMES = [
    (
        r"\bsuicid|\bself[- ]harm\b|\boverdos|\bslit (?:his|her|my|their) wrists\b"
        r"|\bhang(?:ed|ing)? (?:him|her|my|them)self\b|\btake (?:his|her|my) own life\b",
        "Suicide / self-harm",
        4,
    ),
    (r"\bmurder|\bstab(?:s|bed|bing)?\b|\bgun\b|\bshot (?:him|her|them|dead|in the)\b", "Violence & death", 3),
    (r"\bblood\b(?!\s*(?:sugar|pressure|test|type|bank|drive|work))", "Violence & death", 3),
    (
        r"\bpunch(?:es|ed|ing)?\b|\bbeat(?:s|en|ing)? (?:him|her|them|up)\b|\bfist ?fight\b"
        r"|\bslapp(?:ed|ing)\b|\bget(?:s|ting)? in a fight\b|\bbar fight\b",
        "Violence & death",
        2,
    ),
]

ALL_THEME_PATTERNS = SEX_THEMES + IDENTITY_THEMES + SUBSTANCE_THEMES + HARM_THEMES + LANG_THEMES + VIOL_THEMES

FLAG_THEMES = {
    "porn_plot": ("Porn / strippers", 5),
    "stripper_plot": ("Porn / strippers", 4),
    "explicit_body": ("Nudity & bodies", 4),
    "kiss_bribe": ("Sex & hookups", 4),
    "girl_girl_kiss_offer": ("Sex & hookups", 4),
}

FLAG_HOW = {
    "porn_plot": "Porn / adult-channel plot is part of this episode.",
    "stripper_plot": "Stripper or strip-club material shows up in the plot.",
    "explicit_body": "Explicit body / sex-act language appears in dialogue.",
    "kiss_bribe": "A kiss is used as a bribe or performance gag.",
    "girl_girl_kiss_offer": "Main-cast women kissing is used as a sitcom gag.",
}

FALLBACK_HOW = {
    "Sex & hookups": "Sexual jokes, hookups, or dating-sex talk.",
    "Nudity & bodies": "Nudity jokes or body-focused comedy.",
    "Porn / strippers": "Porn, strippers, or adult-entertainment plot.",
    "Swearing": "Swear words show up in the dialogue.",
    "Violence & death": "Fighting, weapons, or death talk.",
    "Affairs / cheating": "Cheating, affairs, or break-related betrayal.",
    "Suicide / self-harm": "Suicide or self-harm is mentioned.",
    "Alcohol / Drugs": "Drinking, drunkenness, or drug references.",
    "Gay / Lesbian": "Gay / lesbian identity or queer-coded jokes.",
    "Fat-shaming": "Fat jokes or body-shaming comedy.",
    "Slut-shaming": "Slut-shaming or ‘promiscuous’ insult comedy.",
    "Racism": "Racist language, stereotypes, or racial mockery.",
}

BLURB_HINTS = [
    (r"porn|phone.?sex|adult.?channel", "Porn / strippers"),
    (r"stripper|strip.?club|lap dance", "Porn / strippers"),
    (r"suicid", "Suicide / self-harm"),
    (r"lesbian|gay|queer|homosexual|bisexual|coming out|drag|showgirl", "Gay / Lesbian"),
    (r"drunk|drinking|beer|wine|vodka|tequila|whiskey|champagne|booze|hangover|marijuana|weed|\bpot\b|cocaine|drugs?|stoned|dealer", "Alcohol / Drugs"),
    (r"fat monica|fat suit|fat joke|body image|you'?re fat|fatty", "Fat-shaming"),
    (r"slut|whore|skank|tramp|slut[- ]?sham|sleeps? around", "Slut-shaming"),
    (r"racis|bigot|blackface|racial slur|xenophob", "Racism"),
    (r"affair|cheat|on a break|sleep(?:ing|s)? with|hook(?:ed|ing)? up|\bsex\b|hook ?up|virgin|horny|make.?out|kiss|condom|viagra|sperm|inseminat", "Sex & hookups"),
    (r"naked|nude|underwear|breast|butt|body|anatomy|nipple", "Nudity & bodies"),
    (r"gun|stab|murder|fight|cage.?fight|mma|blood|kill", "Violence & death"),
    (r"swear|fuck|shit|damn|hell|language", "Swearing"),
]

FINE_BY_SHOW = {
    "friends": ["Friend-group hangouts", "Apartment / coffee-shop comedy"],
    "seinfeld": ["Observational New York comedy", "Friend-group hangouts"],
    "the-office": ["Workplace comedy", "Awkward office humor"],
    "spongebob": ["Cartoon slapstick", "Kid-adventure silliness"],
    "how-i-met-your-mother": ["Friend-group hangouts", "Bar / apartment sitcom banter"],
    "big-bang-theory": ["Nerd / science humor", "Friend-group hangouts"],
    "young-sheldon": ["Family sitcom", "Science / school humor"],
    "malcolm-in-the-middle": ["Family sitcom chaos", "Sibling comedy"],
    "rick-and-morty": ["Sci-fi adventure comedy", "Dimension-hopping hijinks"],
    "family-guy": ["Cutaway gag comedy", "Animated family satire"],
    "south-park": ["Animated satire", "Town-wide misadventures"],
    "futurama": ["Sci-fi sitcom", "Future delivery-crew adventures"],
}


def _uniq(items: list[str], limit: int = 8) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in items:
        k = x.lower().strip()
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(x.strip())
        if len(out) >= limit:
            break
    return out


def map_blurb_to_themes(blurb: str) -> list[str]:
    lower = blurb.lower()
    hits = []
    for pat, label in BLURB_HINTS:
        if re.search(pat, lower):
            hits.append(label)
    return _uniq(hits, limit=4)


MAX_INSTANCES = 15
MAX_TEXT = 220

SPEAKER_RE = re.compile(r"^([A-Z][A-Za-z0-9.'\- ]{1,22}?)\s*:\s*(.+)$", re.S)
SLUR_RE = re.compile(r"\bnigg(?:er|a)s?\b|\bchinks?\b|\bkikes?\b|\bgooks?\b|\bwett?backs?\b", re.I)

# Mask hard profanity but keep the evidence readable for parents.
PROFANITY_MASKS = [
    (re.compile(r"\bfuck(\w*)", re.I), lambda m: "f***" + m.group(1)),
    (re.compile(r"\bshit(\w*)", re.I), lambda m: "sh*t" + m.group(1)),
    (re.compile(r"\bass ?hole(\w*)", re.I), lambda m: "a**hole" + m.group(1)),
    (re.compile(r"\bcunt(\w*)", re.I), lambda m: "c**t" + m.group(1)),
]

# Wiki / metadata cruft that shows up in scraped fandom transcripts.
JUNK_LINE_RE = re.compile(
    r"^(episode|season|airdate|transcript|gallery|credits|general|u\.s\.|running time|previous|next|"
    r"written by|transcribed by|additional transcribing|copyright|note)\b|№",
    re.I,
)


def _mask(text: str) -> str:
    out = SLUR_RE.sub("[racial slur]", text)
    for pattern, repl in PROFANITY_MASKS:
        out = pattern.sub(repl, out)
    return out


def _shorten(text: str, max_len: int = MAX_TEXT) -> str:
    if len(text) <= max_len:
        return text
    cut = text[: max_len - 1]
    # Prefer a clean break at the last sentence or word boundary
    for sep in (". ", "! ", "? ", " "):
        idx = cut.rfind(sep)
        if idx > max_len * 0.6:
            cut = cut[: idx + (len(sep) - 1)]
            break
    return cut.rstrip(" ,;:-") + "…"


def transcript_units(body: str) -> list[dict]:
    """
    Split a transcript into dialogue / stage-direction units.

    kind "quote" → spoken line (render inside quote marks)
    kind "scene" → stage direction describing what happens
    kind "line"  → other narrative prose
    """
    units: list[dict] = []
    for block in re.split(r"\n\s*\n", body):
        text = re.sub(r"\s+", " ", block).strip()
        if not text or text.startswith("=" * 6):
            continue
        if len(text) < 12 or " " not in text:
            continue
        if JUNK_LINE_RE.search(text):
            continue

        scene = False
        if text.startswith("[") and text.endswith("]"):
            text, scene = text[1:-1].strip(), True
        elif text.startswith("(") and text.endswith(")"):
            text, scene = text[1:-1].strip(), True
        elif re.match(r"^scene\s*:", text, re.I):
            text, scene = re.sub(r"^scene\s*:\s*", "", text, flags=re.I), True

        if scene:
            units.append({"kind": "scene", "speaker": None, "text": text})
            continue

        m = SPEAKER_RE.match(text)
        if m and not m.group(1).lower().startswith(("http", "www")):
            speaker = m.group(1).strip()
            said = m.group(2).strip()
            if len(said) >= 8:
                units.append({"kind": "quote", "speaker": speaker, "text": said})
                continue

        units.append({"kind": "line", "speaker": None, "text": text})
    return units


def _instance_from_unit(unit: dict) -> dict | None:
    text = _mask(unit["text"]).strip(" -–—")
    if len(text) < 12:
        return None
    text = _shorten(text)
    if unit["kind"] == "quote":
        return {"kind": "quote", "speaker": unit["speaker"], "text": text}
    return {"kind": "note", "speaker": None, "text": text}


def collect_theme_instances(
    body: str, flags: list[str] | None = None
) -> dict[str, dict]:
    """
    label -> {sev, count, instances: [{kind, speaker, text}, …]}

    Every place a theme shows up in the episode, most severe first.
    """
    found: dict[str, dict] = {}

    for unit in transcript_units(body):
        lower = unit["text"].lower()
        for pattern, label, sev in ALL_THEME_PATTERNS:
            if label not in CANONICAL_WATCH:
                continue
            if not re.search(pattern, lower):
                continue
            inst = _instance_from_unit(unit)
            if not inst:
                continue
            bucket = found.setdefault(label, {"sev": 0, "seen": set(), "items": []})
            key = re.sub(r"[^a-z0-9]+", "", inst["text"].lower())[:90]
            if key in bucket["seen"]:
                # Same line, weaker pattern — keep the highest severity we saw
                bucket["sev"] = max(bucket["sev"], sev)
                continue
            bucket["seen"].add(key)
            bucket["sev"] = max(bucket["sev"], sev)
            bucket["items"].append({**inst, "sev": sev})

    for name in flags or []:
        if name not in FLAG_THEMES:
            continue
        label, sev = FLAG_THEMES[name]
        how = FLAG_HOW.get(name, "")
        if not how:
            continue
        bucket = found.setdefault(label, {"sev": 0, "seen": set(), "items": []})
        bucket["sev"] = max(bucket["sev"], sev)
        bucket["items"].insert(
            0, {"kind": "note", "speaker": None, "text": how, "sev": sev, "curated": True}
        )

    out: dict[str, dict] = {}
    for label, bucket in found.items():
        items = sorted(
            bucket["items"],
            key=lambda x: (not x.get("curated"), -x["sev"]),
        )
        out[label] = {
            "sev": bucket["sev"],
            "count": len(items),
            "instances": items[:MAX_INSTANCES],
        }
    return out


def collect_theme_hits(body: str, flags: list[str] | None = None) -> dict[str, dict]:
    """Back-compat shim: label -> {sev, how} using the top instance."""
    return {
        label: {"sev": data["sev"], "how": data["instances"][0]["text"] if data["instances"] else ""}
        for label, data in collect_theme_instances(body, flags).items()
    }


def render_instance(inst: dict) -> str:
    """Plain-text rendering: quotes get quote marks, notes stay prose."""
    text = (inst.get("text") or "").strip()
    if not text:
        return ""
    if inst.get("kind") == "quote":
        speaker = (inst.get("speaker") or "").strip()
        quoted = f"\u201c{text}\u201d"
        return f"{speaker}: {quoted}" if speaker else quoted
    return text


def fine_themes_for(
    show_id: str | None,
    *,
    sex: int,
    language: int,
    violence: int,
    watch: list[str],
) -> list[str]:
    fine = list(FINE_BY_SHOW.get(show_id or "", ["Light comedy tone"]))
    overall = max(sex, language, violence)
    if overall <= 2 and not watch:
        fine.append("Nothing standout adult — fine for many kid couch nights")
    elif overall <= 2:
        fine.append("Mostly kid-ok if you skip past the mild bits below")
    return _uniq(fine, limit=3)


def build_themes(
    *,
    body: str = "",
    show_id: str | None = None,
    sex: int = 1,
    language: int = 1,
    violence: int = 1,
    flags: list[str] | None = None,
    override_examples: list[str] | None = None,
) -> dict:
    """
    watch: canonical labels (filters)
    watch_detail: [{theme, how, count, instances}] — every place it shows up here
    notes_extra: curated override blurbs
    """
    hits = collect_theme_instances(body, flags)

    # Curated override blurbs lead the list for this theme
    if override_examples:
        for blurb in override_examples:
            note = {
                "kind": "note",
                "speaker": None,
                "text": blurb.strip(),
                "sev": 5,
                "curated": True,
            }
            for label in map_blurb_to_themes(blurb):
                bucket = hits.setdefault(label, {"sev": 3, "count": 0, "instances": []})
                bucket["instances"].insert(0, note)
                bucket["count"] += 1
                bucket["instances"] = bucket["instances"][:MAX_INSTANCES]

    watch = list(hits.keys())

    if language <= 1 and watch == ["Swearing"]:
        watch = []
        hits.pop("Swearing", None)

    if sex >= 4 and not any(t in watch for t in ("Sex & hookups", "Porn / strippers", "Nudity & bodies")):
        watch.append("Sex & hookups")
    if language >= 4 and "Swearing" not in watch:
        watch.append("Swearing")
    if violence >= 3 and not any(t in watch for t in ("Violence & death", "Suicide / self-harm")):
        watch.append("Violence & death")

    watch = [t for t in CANONICAL_WATCH if t in watch]

    watch_detail = []
    for theme in watch:
        data = hits.get(theme) or {}
        instances = list(data.get("instances") or [])
        if not instances:
            instances = [
                {
                    "kind": "note",
                    "speaker": None,
                    "text": FALLBACK_HOW.get(theme, "Flagged in this episode."),
                }
            ]
        instances = [
            {k: v for k, v in inst.items() if k in ("kind", "speaker", "text")}
            for inst in instances
        ]
        count = max(int(data.get("count") or 0), len(instances))
        watch_detail.append(
            {
                "theme": theme,
                "how": render_instance(instances[0]),
                "count": count,
                "instances": instances,
            }
        )

    fine = fine_themes_for(show_id, sex=sex, language=language, violence=violence, watch=watch)
    notes_extra = _uniq(list(override_examples or []), limit=3)

    if not watch and not fine:
        fine = ["Typical light comedy — nothing standout"]

    return {
        "fine": fine,
        "watch": watch,
        "watch_detail": watch_detail,
        "notes_extra": notes_extra,
    }


def themes_as_examples(themes: dict) -> list[str]:
    """Episode bullets: Theme — how it shows up."""
    details = themes.get("watch_detail") or []
    if details:
        return [f"{d['theme']} — {d['how']}" for d in details][:6]
    return _uniq((themes.get("notes_extra") or []) + (themes.get("watch") or []), limit=5)

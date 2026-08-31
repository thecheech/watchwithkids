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
    (r"\bdrag\b|\btrans(?:gender|vestite)?\b|\bshowgirl\b", "Gay / Lesbian", 2),
]

SUBSTANCE_THEMES = [
    (r"\bcocaine\b|\bheroin\b|\bmeth\b|\becstasy\b|\bls?d\b", "Alcohol / Drugs", 4),
    (r"\bmarijuana\b|\bweed\b|\bpot\b|\bjoint\b|\bstoned\b|\bdealer\b", "Alcohol / Drugs", 3),
    (r"\bdrunk\b|\bdrunken\b|\bhangover\b|\bbooze\b|\bwasted\b|\bintoxicated\b", "Alcohol / Drugs", 2),
    (r"\bbeer\b|\bwine\b|\bvodka\b|\btequila\b|\bwhiskey\b|\bchampagne\b|\bcocktail\b|\bmargarita\b", "Alcohol / Drugs", 2),
    (r"\bdrinking\b|\bgot drunk\b|\bget drunk\b|\bshots?\b of\b", "Alcohol / Drugs", 2),
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
    (r"\bsuicide\b|\bkill(?:s|ed|ing)? (?:my|him|her|them|myself|yourself)\b", "Suicide / self-harm", 4),
    (r"\bsuicide\b", "Suicide / self-harm", 4),
    (r"\bmurder|\bstab|\bgun\b|\bshoot(?:s|ing|shot)?\b|\bblood\b", "Violence & death", 3),
    (r"\bpunch(?:es|ed|ing)?\b|\bbeat(?:s|en|ing)? up\b|\bfight(?:s|ing)?\b", "Violence & death", 2),
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


def _clean_snip(line: str, *, max_len: int = 108) -> str:
    t = re.sub(r"\[.*?\]", "", line)
    t = re.sub(r"\s+", " ", t).strip(" -–—:\t")
    # Soften raw swear dumps for the UI
    if re.search(r"\bfuck|\bshit\b|\basshole\b|\bnigg", t, re.I):
        return ""
    if len(t) > max_len:
        t = t[: max_len - 1].rstrip() + "…"
    return t


def _find_line(body: str, pat: str) -> str | None:
    for line in body.splitlines():
        if re.search(pat, line, re.I):
            cleaned = _clean_snip(line)
            if 16 <= len(cleaned) <= 140:
                return cleaned
    return None


def collect_theme_hits(body: str, flags: list[str] | None = None) -> dict[str, dict]:
    """
    label -> {sev, how, pat}
    Prefer a concrete dialogue snip; else flag how; else fallback later.
    """
    lower = body.lower()
    best: dict[str, dict] = {}

    for pat, label, sev in ALL_THEME_PATTERNS:
        if label not in CANONICAL_WATCH:
            continue
        if not re.search(pat, lower):
            continue
        prev = best.get(label)
        snip = _find_line(body, pat)
        how = snip or ""
        if not prev or sev > prev["sev"] or (sev == prev["sev"] and how and not prev["how"]):
            best[label] = {"sev": sev, "how": how, "pat": pat}

    for name in flags or []:
        if name not in FLAG_THEMES:
            continue
        label, sev = FLAG_THEMES[name]
        how = FLAG_HOW.get(name, "")
        prev = best.get(label)
        if not prev or sev > prev["sev"] or (sev == prev["sev"] and how and not prev["how"]):
            best[label] = {"sev": sev, "how": how, "pat": name}

    return best


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
    watch_detail: [{theme, how}] — how this theme shows up in THIS episode
    notes_extra: curated override blurbs
    """
    hits = collect_theme_hits(body, flags)
    how_by: dict[str, str] = {label: data["how"] for label, data in hits.items() if data.get("how")}

    # Curated override blurbs win as the episode-specific "how"
    if override_examples:
        for blurb in override_examples:
            for label in map_blurb_to_themes(blurb):
                # Prefer curated prose over transcript snips
                how_by[label] = blurb.strip()
                if label not in hits:
                    hits[label] = {"sev": 3, "how": blurb.strip(), "pat": "override"}

    watch = list(hits.keys())

    if language <= 1 and watch == ["Swearing"]:
        watch = []
        how_by.pop("Swearing", None)

    if sex >= 4 and not any(t in watch for t in ("Sex & hookups", "Porn / strippers", "Nudity & bodies")):
        watch.append("Sex & hookups")
    if language >= 4 and "Swearing" not in watch:
        watch.append("Swearing")
    if violence >= 3 and not any(t in watch for t in ("Violence & death", "Suicide / self-harm")):
        watch.append("Violence & death")

    watch = [t for t in CANONICAL_WATCH if t in watch]

    watch_detail = []
    for theme in watch:
        how = (how_by.get(theme) or "").strip()
        if not how:
            how = FALLBACK_HOW.get(theme, "Flagged in this episode.")
        # Keep how readable and parent-facing
        if len(how) > 140:
            how = how[:137].rstrip() + "…"
        watch_detail.append({"theme": theme, "how": how})

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

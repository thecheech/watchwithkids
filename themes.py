"""Parent-facing theme taxonomy and the evidence engine behind every flag.

Design rules (v2):

* One moment, one primary theme. A single line cannot be counted as Sex *and*
  Nudity *and* Swearing *and* Affairs.
* Every moment carries intensity (1 joke / 2 moderate / 3 explicit), mode
  (dialogue / on-screen / implied) and a rough position in the episode.
* Identity is not a hazard. Being gay is not a content warning; a homophobic
  joke is, and it lives under Bias & slurs. Households that want a heads-up on
  LGBTQ storylines can opt in — it never feeds a score.
* Repeated hits on the same trigger word collapse, so a nickname like
  "Paul the Wine Guy" cannot become six drinking references.
"""

from __future__ import annotations

import re

# ── taxonomy ──────────────────────────────────────────────────────────────────

# group -> the 1–5 dimension it can influence (None = informational only)
GROUPS = {
    "sex": {"label": "Sex & relationships", "dimension": "sex"},
    "violence": {"label": "Violence & harm", "dimension": "violence"},
    "language": {"label": "Language", "dimension": "language"},
    "substances": {"label": "Alcohol & drugs", "dimension": None},
    "bias": {"label": "Bias & slurs", "dimension": None},
    "optin": {"label": "Heads-up topics", "dimension": None},
}

GROUP_ORDER = ["sex", "violence", "language", "substances", "bias", "optin"]

# label -> group. Order here is the display order inside a group.
THEME_GROUP = {
    "Sex & hookups": "sex",
    "Nudity & bodies": "sex",
    "Porn / strippers / sex work": "sex",
    "Affairs / cheating": "sex",
    "Violence & injury": "violence",
    "Suicide & self-harm": "violence",
    "Swearing": "language",
    "Alcohol & drugs": "substances",
    "Racism & slurs": "bias",
    "Homophobic jokes": "bias",
    "Fat-shaming": "bias",
    "Slut-shaming": "bias",
    "LGBTQ themes": "optin",
}

# Off unless a household turns them on. Never counted in any score.
OPT_IN_THEMES = ["LGBTQ themes"]

# Scored / shown by default.
CANONICAL_WATCH = [t for t in THEME_GROUP if t not in OPT_IN_THEMES]

ALL_THEMES = list(THEME_GROUP)

THEME_BLURB = {
    "Sex & hookups": "Sex talk, innuendo, hookups and dating-sex plots.",
    "Nudity & bodies": "Nudity, body parts or undressing — as a joke or on screen.",
    "Porn / strippers / sex work": "Porn, strip clubs or sex work in the plot.",
    "Affairs / cheating": "Cheating, affairs and betrayal storylines.",
    "Violence & injury": "Fighting, weapons, injury or death.",
    "Suicide & self-harm": "Suicide or self-harm is raised.",
    "Swearing": "Swear words in the dialogue.",
    "Alcohol & drugs": "Drinking, drunkenness or drug references.",
    "Racism & slurs": "Racist language, stereotypes or racial mockery.",
    "Homophobic jokes": "Someone's orientation is used as the punchline or an insult.",
    "Fat-shaming": "Weight used as an insult or a running joke.",
    "Slut-shaming": "Shaming someone as ‘promiscuous’.",
    "LGBTQ themes": "A gay, lesbian, bi or trans character or storyline appears. "
    "Representation, not a content warning — shown only because you asked for it.",
}

# Renames applied to anything still carrying the v1 vocabulary.
LEGACY_RENAMES = {
    "Violence & death": "Violence & injury",
    "Suicide / self-harm": "Suicide & self-harm",
    "Alcohol / Drugs": "Alcohol & drugs",
    "Porn / strippers": "Porn / strippers / sex work",
    "Racism": "Racism & slurs",
    "Gay / Lesbian": "LGBTQ themes",
}


def canonical_label(label: str) -> str:
    return LEGACY_RENAMES.get(label, label)


def group_of(label: str) -> str:
    return THEME_GROUP.get(canonical_label(label), "sex")


def dimension_of(label: str) -> str | None:
    return GROUPS[group_of(label)]["dimension"]


# ── patterns ──────────────────────────────────────────────────────────────────
# (pattern, canonical label, severity 1–5). Severity maps to intensity:
# 1–2 = joke / passing mention, 3 = moderate, 4–5 = explicit.

SEX_THEMES = [
    (r"\bporn(?:o|ography)?\b|\bphone sex\b|\badult (?:film|movie|channel)\b", "Porn / strippers / sex work", 5),
    (r"\bstrippers?\b|\bstrip club\b|\blap dance\b|\bescort service\b", "Porn / strippers / sex work", 4),
    (r"\bprostitut\w*\b|\bhooker\b|\bsex worker\b", "Porn / strippers / sex work", 4),
    (r"\b(?:orgasm\w*|threesome|masturbat\w*)\b", "Sex & hookups", 5),
    (r"\b(?:penis|vagina|nipples?|genitals?)\b", "Nudity & bodies", 4),
    (r"\bcondoms?\b|\bviagra\b|\bimpotent\w*\b|\bsperm\b|\binsemination\b", "Sex & hookups", 3),
    (r"\bsleep(?:ing|s)? with\b|\bhook(?:ed|ing)? up\b|\bhave sex\b|\bhad sex\b|\bone[- ]night stand\b", "Sex & hookups", 3),
    (r"\bhorny\b|\bvirgin(?:ity)?\b|\bforeplay\b", "Sex & hookups", 3),
    (r"\baffairs?\b|\bcheat(?:s|ing|ed)? on\b|\bunfaithful\b|\bon a break\b", "Affairs / cheating", 3),
    (r"\bnaked\b|\bnude\b|\bskinny[- ]dip\w*\b", "Nudity & bodies", 2),
    (r"\bunderwear\b|\bpanties\b|\bthong\b|\bbra\b", "Nudity & bodies", 2),
    (r"\bbreasts?\b|\bboobs?\b|\bcleavage\b", "Nudity & bodies", 2),
    (r"\bmake(?:s|ing)? out\b|\bmakeout\b", "Sex & hookups", 2),
    (r"\bsexual\w*\b|\bsexy\b|\bsex\b", "Sex & hookups", 2),
]

# Homophobic punchlines and slurs. The harm is the joke, not the person.
BIAS_IDENTITY_THEMES = [
    (r"\bfag(?:got)?s?\b|\bdykes?\b|\bhomos?\b(?!\s*sapien)", "Homophobic jokes", 4),
    (r"\bthat'?s (?:so |totally |really )?gay\b|\bno homo\b|\bso gay\b", "Homophobic jokes", 3),
    (
        r"\bwish (?:i|he|she|we) (?:was|were) a lesbian\b"
        r"|\b(?:turn(?:ed|ing)?|made) (?:him|her|me|you) gay\b"
        r"|\bnot that there'?s anything wrong with that\b",
        "Homophobic jokes",
        2,
    ),
]

# Opt-in only. Representation, never scored.
IDENTITY_THEMES = [
    (
        r"\blesbians?\b|\bgay\b|\bhomosexual\w*\b|\bbisexual\b|\bcoming out\b"
        r"|\bsame[- ]sex\b|\btrans(?:gender)?\b|\bnon[- ]binary\b|\bdrag queen\b",
        "LGBTQ themes",
        1,
    ),
]

SUBSTANCE_THEMES = [
    (r"\bcocaine\b|\bheroin\b|\bmeth(?:amphetamine)?\b|\becstasy\b|\bacid trip\b|\bcrack pipe\b", "Alcohol & drugs", 4),
    (
        r"\bmarijuana\b|\bweed\b|\bstoned\b|\bpothead\b|\bsmok\w*\s+(?:a\s+)?(?:pot|joint|weed)\b"
        r"|\bpot brownies?\b|\bdrug dealer\b|\bgetting high\b|\bhigh as a kite\b",
        "Alcohol & drugs",
        3,
    ),
    (r"\bdrunk\w*\b|\bhungover\b|\bhangover\b|\bbooze\b|\bwasted\b|\bintoxicated\b|\bblackout drunk\b", "Alcohol & drugs", 2),
    (r"\bbeers?\b|\bwine\b|\bvodka\b|\btequila\b|\bwhiskey\b|\bchampagne\b|\bcocktails?\b|\bmargaritas?\b", "Alcohol & drugs", 1),
    (r"\bshots? of (?:vodka|tequila|whiskey|rum)\b|\bget(?:ting)? drunk\b", "Alcohol & drugs", 2),
]

HARM_THEMES = [
    (r"\bfat (?:girl|chick|ass|pig|suit)\b|\bfatty\b|\byou'?re fat\b|\bso fat\b|\blose weight\b|\blard[- ]?ass\b", "Fat-shaming", 3),
    (r"\bfat\b.{0,20}\b(?:joke|laugh|mock|tease|insult)\w*\b", "Fat-shaming", 2),
    (r"\b(?:big|huge) (?:cow|pig|whale)\b", "Fat-shaming", 3),
    (r"\bslut[- ]?sham\w*\b", "Slut-shaming", 4),
    (r"\bwhores?\b|\bsluts?\b|\bskanks?\b|\btramps?\b", "Slut-shaming", 3),
    (r"\bsleeps? around\b|\beasy\b.{0,12}(?:girl|woman)\b", "Slut-shaming", 3),
    (r"\bnigg(?:er|a)s?\b|\bchinks?\b|\bspics?\b|\bkikes?\b|\bwett?backs?\b|\bgooks?\b", "Racism & slurs", 5),
    (r"\bblackface\b|\byellowface\b|\bbrownface\b", "Racism & slurs", 5),
    (r"\bracis(?:t|m)\b|\bbigot(?:ed|ry)?\b|\bxenophob\w*\b", "Racism & slurs", 4),
    (r"\ball .{0,12}look alike\b|\bchinese (?:fire drill|accent)\b|\bching chong\b", "Racism & slurs", 4),
]

LANG_THEMES = [
    (r"\bfuck\w*\b|\bcunt\w*\b|\bmotherfucker\b", "Swearing", 5),
    (r"\bshit\w*\b|\bassholes?\b|\bbitch\w*\b|\bdicks?\b|\bcocks?\b|\bprick\b", "Swearing", 3),
    (r"\bpiss\w*\b|\bbastards?\b|\bscrew(?:ed|ing) you\b|\bdouchebag\b", "Swearing", 2),
    (r"\bdamn\b|\bhell\b|\bcrap\b|\bsucks\b", "Swearing", 1),
]

VIOL_THEMES = [
    (
        r"\bsuicid\w*\b|\bself[- ]harm\w*\b|\boverdos\w*\b|\bslit (?:his|her|my|their) wrists\b"
        r"|\bhang(?:ed|ing)? (?:him|her|my|them)self\b|\btake (?:his|her|my) own life\b"
        r"|\bkill(?:ed)? (?:him|her|my)self\b",
        "Suicide & self-harm",
        4,
    ),
    (r"\bmurder\w*\b|\bstab(?:s|bed|bing)?\b|\bshot (?:him|her|them|dead|in the)\b|\bcorpse\b", "Violence & injury", 4),
    (r"\bguns?\b|\bpistol\b|\brifle\b|\bshotgun\b|\bknife\b", "Violence & injury", 3),
    (r"\bblood\w*\b(?!\s*(?:sugar|pressure|test|type|bank|drive|work))|\bgore\b", "Violence & injury", 3),
    (
        r"\bpunch(?:es|ed|ing)?\b|\bbeat(?:s|en|ing)? (?:him|her|them|up)\b|\bfist ?fight\b"
        r"|\bslapp(?:ed|ing)\b|\bbar fight\b|\bstrangl\w*\b",
        "Violence & injury",
        2,
    ),
]

ALL_THEME_PATTERNS = (
    SEX_THEMES
    + BIAS_IDENTITY_THEMES
    + IDENTITY_THEMES
    + SUBSTANCE_THEMES
    + HARM_THEMES
    + LANG_THEMES
    + VIOL_THEMES
)

_COMPILED = [(re.compile(p, re.I), label, sev) for p, label, sev in ALL_THEME_PATTERNS]

# Contexts where a keyword is not the thing it looks like. Checked against the
# matched phrase plus a little surrounding text.
THEME_EXCLUSIONS = {
    "Alcohol & drugs": [
        r"\bwine\s+(?:guy|country|glass|list|cellar|tasting room)\b",
        r"\bthe\s+wine\s+guy\b",
        r"\bbeer\s+(?:belly|goggles|league)\b",
        r"\bchampagne\s+(?:colou?r|toast to)\b",
        r"\broot beer\b",
        r"\bginger beer\b",
    ],
    "Sex & hookups": [
        r"\bopposite sex\b",
        r"\bsame[- ]sex\b",
        r"\bsex of the baby\b",
        r"\bthe sex\b(?=\s+of)",
        r"\bsexy\s+(?:new\s+)?(?:hair|shoes|car|dress)\b",
        # Animal name, not the reproductive cell.
        r"\bsperm\s+whale\b",
        # Literal sleep, not sex.
        r"\b(?:go(?:es|ing)?|went|fall(?:s|en|ing)?|fallen)\s+(?:to\s+)?sleep\s+with\b",
        r"\bsleep(?:ing|s)?\s+with\s+(?:everyone|everybody|the\s+(?:fishes|lights|door))\b",
        r"\bput(?:s|ting)?\s+(?:\w+\s+){0,3}to\s+sleep\b",
        # "make out what swam into our casting nets" — figure out, not hook up.
        r"\bmake\s+out\s+(?:what|the|a|an|how|if|whether|who|where|when|why)\b",
    ],
    "Nudity & bodies": [
        r"\bnaked eye\b",
        r"\bnaked truth\b",
        r"\bbra(?:ss|vo|ve|in|nch|nd)\b",
        r"\bchicken breasts?\b",
        r"\bbreast (?:cancer|milk)\b",
        # Laundry / clothing props — not an undressing beat.
        r"\btighty\s+whiteys?\b",
        r"\b(?:dirty|clean(?:ing)?|wash(?:ing|ed)?|missing|lost|favorite|lucky)\s+"
        r"(?:\w+\s+){0,2}underwear\b",
        r"\bunderwear\s+(?:repair|drawer|line|thieves|division|flyers?|over|thieves)\b",
        r"\b(?:pair of|change of)\s+(?:\w+\s+){0,2}underwear\b",
        r"\bmissing:\s*underwear\b",
        r"\blost underwear\b",
    ],
    "Swearing": [
        # Proper names / titles that contain a swear-looking token.
        r"\bdopey\s+dick\b",
        r"\bmoby\s+dick\b",
        r"\bdick\s+tracy\b",
        r"\bdick\s+van\s+dyke\b",
        r"\bdick\s+clark\b",
        r"\bdick\s+cheney\b",
        r"\b(?:mr|mrs|ms|mister|captain|dr)\.?\s+dick\b",
    ],
    "Affairs / cheating": [
        r"\bfamily\s+affair\b",
    ],
    "Violence & injury": [
        r"\bkill(?:ing)? (?:time|the lights|it)\b",
        r"\bblood (?:orange|relative|brother|sister|line|lines)\b",
        r"\bbloodlines?\b",
        r"\bgun (?:show|shy|it)\b",
        r"\bstab (?:at it|in the dark)\b",
        r"\bpunch(?:ed|ing)? (?:line|card|bowl|bag)\b",
        # Props, not weapons.
        r"\b(?:finger|tattoo|glue|nail|staple|water|squirt|pop|potato|grease|spray|t[- ]?shirt|chipping)\s+gun\b",
        r"\bgun\s+(?:it|for it)\b",
        r"\bjumping the gun\b",
        r"\bbigger\s+guns?\b",
        r"\bchipping\s+gun\b",
        r"\bmurder\s+of\s+crows\b",
        r"\bmurder\s+investigation\b",
        r"\bbleeding\s+isn'?t\s+in\s+my\s+blood\b",
        r"\bblood and tears\b",
        r"\bknife (?:and fork|through butter|pleat)\b",
        r"\bbutter knife\b",
    ],
    "Homophobic jokes": [
        r"\bgay (?:marriage|rights|pride|couple|community|bar|wedding)\b",
    ],
    # "I wanna kill myself" is a sitcom groan, not a disclosure.
    "Suicide & self-harm": [
        r"\b(?:wanna|want(?:s|ed)? to|could|gonna|going to|just about|makes? (?:me|him|her) (?:wanna|want to))"
        r"\s+(?:just\s+)?kill\s+(?:my|him|her|them)self\b",
        r"\bkill\s+(?:my|him|her)self\b\s*(?:laughing|with embarrassment)",
        r"\bsuicide (?:squeeze|pass|mission|watch list)\b",
    ],
    "Racism & slurs": [
        r"\bracist\b(?=\s+(?:is|are)\s+wrong)",
        # Transcript typo: "gook luck" = "good luck" (Friends S2 E4).
        r"\bgook\s+luck\b",
        # Meta-discussion — calling someone racist or talking about racist jokes, not slurs.
        r"\bkind of a racist\b",
        r"\bracist jokes?\b",
        r"\bracial slur\b",
        r"\bMr\. Bigot\b",
    ],
}

_COMPILED_EXCLUSIONS = {
    label: [re.compile(p, re.I) for p in pats] for label, pats in THEME_EXCLUSIONS.items()
}

# Scrub before keyword-weight scoring so "Dopey Dick" cannot inflate language 1–5.
FALSE_SWEAR_NAME_RES = [
    re.compile(p, re.I) for p in THEME_EXCLUSIONS.get("Swearing", [])
]

# Same idea for sex-weight scoring (sperm whale, "goes to sleep with…").
FALSE_SEX_PHRASE_RES = [
    re.compile(p, re.I) for p in THEME_EXCLUSIONS.get("Sex & hookups", [])
]

FALSE_VIOL_PHRASE_RES = [
    re.compile(p, re.I) for p in THEME_EXCLUSIONS.get("Violence & injury", [])
]

FALSE_AFFAIR_PHRASE_RES = [
    re.compile(p, re.I) for p in THEME_EXCLUSIONS.get("Affairs / cheating", [])
]

# On kids animation, bare clothing words are costume gags unless undress language is nearby.
MILD_BODY_TRIGGERS = {"underwear", "bra", "panties", "thong", "breasts", "boobs", "cleavage"}
REAL_UNDRESS_RE = re.compile(
    r"\b(?:naked|nude|topless|pants-?less|exposed|genitals?|streak(?:er|ing)?)\b", re.I
)


def scrub_false_swear_names(text: str) -> str:
    """Replace proper-name 'Dick' phrases so LANG_PATTERNS cannot score them as swears."""
    out = text
    for pattern in FALSE_SWEAR_NAME_RES:
        out = pattern.sub("name", out)
    return out


def scrub_false_sex_phrases(text: str) -> str:
    """Neutralize known non-sexual phrases before SEX_PATTERNS weight counting."""
    out = text
    for pattern in FALSE_SEX_PHRASE_RES:
        out = pattern.sub(" ", out)
    return out


def scrub_false_viol_phrases(text: str) -> str:
    """Neutralize idioms and prop names before VIOL_PATTERNS weight counting."""
    out = text
    for pattern in FALSE_VIOL_PHRASE_RES:
        out = pattern.sub(" ", out)
    for pattern in FALSE_AFFAIR_PHRASE_RES:
        out = pattern.sub(" ", out)
    return out


def scrub_rating_false_positives(text: str) -> str:
    """Apply all keyword-score scrubs used by the raters."""
    return scrub_false_viol_phrases(scrub_false_sex_phrases(scrub_false_swear_names(text)))

# Curated plot flags raise a floor even when the transcript is thin.
FLAG_THEMES = {
    "porn_plot": ("Porn / strippers / sex work", 5),
    "stripper_plot": ("Porn / strippers / sex work", 4),
    "explicit_body": ("Nudity & bodies", 4),
    "kiss_bribe": ("Sex & hookups", 3),
    "girl_girl_kiss_offer": ("Sex & hookups", 3),
}

FLAG_HOW = {
    "porn_plot": "Porn / adult-channel plot is part of this episode.",
    "stripper_plot": "Stripper or strip-club material shows up in the plot.",
    "explicit_body": "Explicit body / sex-act language appears in dialogue.",
    "kiss_bribe": "A kiss is used as a bribe or performance gag.",
    "girl_girl_kiss_offer": "Main-cast women kissing is used as a sitcom gag.",
}

# Curated blurbs → themes. Identity words route to the opt-in theme only.
BLURB_HINTS = [
    (r"porn|phone.?sex|adult.?channel", "Porn / strippers / sex work"),
    (r"stripper|strip.?club|lap dance|sex work", "Porn / strippers / sex work"),
    (r"suicid|self.?harm", "Suicide & self-harm"),
    (r"lesbian|gay|queer|homosexual|bisexual|coming out|drag queen|same.?sex", "LGBTQ themes"),
    (
        r"drunk|drinking|beer|wine|vodka|tequila|whiskey|champagne|booze|hangover|marijuana"
        r"|weed|cocaine|drugs?|stoned|dealer",
        "Alcohol & drugs",
    ),
    (r"fat monica|fat suit|fat joke|you'?re fat|fatty", "Fat-shaming"),
    (r"slut|whore|skank|tramp|sleeps? around", "Slut-shaming"),
    (r"racis|bigot|blackface|racial slur|xenophob", "Racism & slurs"),
    (r"affair|cheat(?:s|ing|ed)? on|on a break", "Affairs / cheating"),
    (
        r"sleep(?:ing|s)? with|hook(?:ed|ing)? up|\bsex\b|virgin|horny|make.?out|condom"
        r"|viagra|sperm|inseminat",
        "Sex & hookups",
    ),
    (r"naked|nude|underwear|breast|nipple|topless", "Nudity & bodies"),
    (r"gun|stab|murder|fist.?fight|blood|kill", "Violence & injury"),
    (r"swear|f\*\*\*|profanit|language", "Swearing"),
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
    "parks-and-recreation": ["Workplace comedy", "Small-town government hijinks"],
    "modern-family": ["Family sitcom", "Mockumentary family chaos"],
}

# Kids animation: slapstick is the genre, not a warning sign.
SLAPSTICK_SHOWS = {
    "spongebob",
    "bluey",
    "phineas-and-ferb",
    "adventure-time",
    "gravity-falls",
    "steven-universe",
    "avatar",
}


# ── text handling ─────────────────────────────────────────────────────────────

MAX_INSTANCES = 12
MAX_PER_TRIGGER = 2
MAX_TEXT = 220

SPEAKER_RE = re.compile(r"^([A-Z][A-Za-z0-9.'\- ]{1,22}?)\s*:\s*(.+)$", re.S)

JUNK_LINE_RE = re.compile(
    r"^(episode|season|airdate|transcript|gallery|credits|general|u\.s\.|running time|previous|next|"
    r"written by|transcribed by|additional transcribing|copyright|note)\b|"
    r"season\s+\d+\s+episode\s+\d+|№",
    re.I,
)

_DENSE_CUE_MIN = 8


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
    hits = [label for pat, label in BLURB_HINTS if re.search(pat, lower)]
    return _uniq(hits, limit=3)


def _shorten(text: str, max_len: int = MAX_TEXT) -> str:
    if len(text) <= max_len:
        return text
    cut = text[: max_len - 1]
    for sep in (". ", "! ", "? ", " "):
        idx = cut.rfind(sep)
        if idx > max_len * 0.6:
            cut = cut[: idx + (len(sep) - 1)]
            break
    return cut.rstrip(" ,;:-") + "…"


def _window_around(text: str, start: int, end: int, max_len: int = MAX_TEXT) -> str:
    """Keep the matching phrase in view instead of truncating from the start."""
    if len(text) <= max_len:
        return text
    left = text.rfind(". ", 0, start)
    left = 0 if left < 0 else left + 2
    right = len(text)
    for i in range(end, len(text)):
        if text[i] in ".!?" and (i + 1 == len(text) or text[i + 1].isspace()):
            right = i + 1
            break
    snippet = text[left:right].strip()
    if len(snippet) <= max_len:
        return snippet
    pad = max(48, (max_len - max(end - start, 1)) // 2)
    a = max(left, start - pad)
    b = min(right, end + pad)
    if a > left:
        sp = text.find(" ", a, start)
        if sp != -1:
            a = sp + 1
    if b < right:
        sp = text.rfind(" ", end, b)
        if sp != -1:
            b = sp
    snippet = text[a:b].strip()
    if a > left:
        snippet = "…" + snippet
    if b < right:
        snippet = snippet.rstrip(" ,;:.-") + "…"
    return snippet


def _raw_blocks(body: str) -> list[tuple[str, bool]]:
    """(text, is_cue). Subtitle dumps arrive as one long run of single-line cues."""
    blocks: list[tuple[str, bool]] = []
    for para in re.split(r"\n\s*\n", body):
        lines = [ln.strip() for ln in para.splitlines() if ln.strip()]
        if len(lines) >= _DENSE_CUE_MIN:
            blocks.extend((ln, True) for ln in lines)
        elif para.strip():
            blocks.append((para, False))
    return blocks


def transcript_units(body: str) -> list[dict]:
    """
    Split a transcript into dialogue / stage-direction units.

    kind "quote" → spoken line with a named speaker
    kind "cue"   → subtitle line: spoken, but nobody is credited
    kind "scene" → stage direction describing what happens
    kind "line"  → other narrative prose
    """
    units: list[dict] = []
    for block, is_cue in _raw_blocks(body):
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

        units.append({"kind": "cue" if is_cue else "line", "speaker": None, "text": text})
    return units


# ── evidence engine ───────────────────────────────────────────────────────────

MODE_BY_KIND = {"quote": "dialogue", "cue": "dialogue", "scene": "on-screen", "line": "implied"}


def intensity_of(sev: int) -> int:
    """5-point pattern severity → the 3-point intensity parents actually read."""
    if sev >= 4:
        return 3
    if sev == 3:
        return 2
    return 1


INTENSITY_LABEL = {1: "joke or passing mention", 2: "moderate", 3: "explicit"}


def _position(index: int, total: int) -> str:
    if total <= 1:
        return "mid"
    share = index / (total - 1)
    if share < 0.34:
        return "early"
    if share < 0.67:
        return "mid"
    return "late"


def _excluded(label: str, unit_text: str, start: int, end: int) -> bool:
    patterns = _COMPILED_EXCLUSIONS.get(label)
    if not patterns:
        return False
    window = unit_text[max(0, start - 30) : min(len(unit_text), end + 30)]
    return any(p.search(window) for p in patterns)


def _trigger_key(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", "", text.lower()).strip()


def _unit_moment(unit: dict, match: re.Match, label: str, sev: int, at: str) -> dict | None:
    raw = unit["text"]
    if len(raw) > MAX_TEXT:
        raw = _window_around(raw, match.start(), match.end())
    text = _shorten(raw.strip(" -–—"))
    if len(text) < 12:
        return None
    kind = "quote" if unit["kind"] in ("quote", "cue") else "note"
    return {
        "theme": label,
        "group": group_of(label),
        "kind": kind,
        "speaker": unit["speaker"] if kind == "quote" else None,
        "text": text,
        "mode": MODE_BY_KIND.get(unit["kind"], "implied"),
        "intensity": intensity_of(sev),
        "at": at,
        "trigger": _trigger_key(match.group(0)),
        "sev": sev,
    }


def _themes_for_unit(unit: dict) -> list[tuple[re.Match, str, int]]:
    """
    Every distinct piece of evidence in one unit, at most one theme each.

    The strongest match wins the line. A second theme is only allowed when it sits
    on a different, non-overlapping span *and* is moderate or worse — so a single
    clipped line can never be filed under four themes at once.
    """
    text = unit["text"]
    found: list[tuple[re.Match, str, int]] = []
    for pattern, label, sev in _COMPILED:
        m = pattern.search(text)
        if not m or _excluded(label, text, m.start(), m.end()):
            continue
        found.append((m, label, sev))
    if not found:
        return []

    found.sort(key=lambda x: (-x[2], -(x[0].end() - x[0].start())))
    primary = found[0]
    picked = [primary]
    used_groups = {group_of(primary[1])}
    p_start, p_end = primary[0].span()

    for m, label, sev in found[1:]:
        if len(picked) >= 2:
            break
        if sev < 3 or group_of(label) in used_groups:
            continue
        if not (m.end() <= p_start or m.start() >= p_end):
            continue
        picked.append((m, label, sev))
        used_groups.add(group_of(label))
    return picked


# In kids animation a chase, a bonk or a cartoon weapon is the genre, not a warning.
# Only these read as real harm.
SERIOUS_VIOLENCE_RE = re.compile(
    r"murder|stab|corpse|blood|gore|axe|strangl|shot|suicid|self.?harm", re.I
)


def collect_moments(
    body: str, flags: list[str] | None = None, show_id: str | None = None
) -> list[dict]:
    """Ordered list of every distinct flagged moment in the episode."""
    slapstick = show_id in SLAPSTICK_SHOWS
    units = transcript_units(body)
    total = len(units)
    moments: list[dict] = []
    seen_text: dict[str, set[str]] = {}
    trigger_counts: dict[tuple[str, str], int] = {}
    per_theme: dict[str, int] = {}

    for i, unit in enumerate(units):
        at = _position(i, total)
        for match, label, sev in _themes_for_unit(unit):
            moment = _unit_moment(unit, match, label, sev, at)
            if not moment:
                continue
            if (
                slapstick
                and label == "Violence & injury"
                and not SERIOUS_VIOLENCE_RE.search(moment["trigger"])
            ):
                moment["intensity"] = max(1, moment["intensity"] - 1)

            # Kids cartoons: "underwear" laundry gags are not a nudity warning.
            if (
                slapstick
                and label == "Nudity & bodies"
                and moment["trigger"] in MILD_BODY_TRIGGERS
                and not REAL_UNDRESS_RE.search(unit["text"])
            ):
                continue

            text_key = re.sub(r"[^a-z0-9]+", "", moment["text"].lower())[:90]
            seen = seen_text.setdefault(label, set())
            if text_key in seen:
                continue

            trig_key = (label, moment["trigger"])
            if trigger_counts.get(trig_key, 0) >= MAX_PER_TRIGGER:
                continue
            if per_theme.get(label, 0) >= MAX_INSTANCES:
                continue

            seen.add(text_key)
            trigger_counts[trig_key] = trigger_counts.get(trig_key, 0) + 1
            per_theme[label] = per_theme.get(label, 0) + 1
            moments.append(moment)

    for name in flags or []:
        if name not in FLAG_THEMES:
            continue
        label, sev = FLAG_THEMES[name]
        how = FLAG_HOW.get(name)
        if not how:
            continue
        moments.insert(
            0,
            {
                "theme": label,
                "group": group_of(label),
                "kind": "note",
                "speaker": None,
                "text": how,
                "mode": "implied",
                "intensity": intensity_of(sev),
                "at": "mid",
                "trigger": name,
                "sev": sev,
                "curated": True,
            },
        )
    return moments


def evidence_caps(moments: list[dict]) -> dict[str, int]:
    """
    Ceiling each 1–5 dimension can reach given what we actually found.

    Six mild wine jokes cannot add up to a 4. An explicit on-screen beat can.
    """
    # No moment we can point at means no score to defend: the dimension stays at 1.
    caps = {"sex": 1, "violence": 1, "language": 1}
    by_dim: dict[str, list[dict]] = {"sex": [], "violence": [], "language": []}
    for m in moments:
        dim = GROUPS[m["group"]]["dimension"]
        if dim:
            by_dim[dim].append(m)

    for dim, items in by_dim.items():
        if not items:
            continue
        top = max(m["intensity"] for m in items)
        triggers = {m["trigger"] for m in items}
        onscreen_strong = any(m["intensity"] >= 3 and m["mode"] == "on-screen" for m in items)
        explicit = [m for m in items if m["intensity"] >= 3]

        if top <= 1:
            cap = 2
        elif top == 2:
            cap = 4 if len(triggers) >= 5 else 3
        else:
            cap = 5 if (onscreen_strong or len(explicit) >= 3) else 4
        caps[dim] = cap
    return caps


# ── assembly ──────────────────────────────────────────────────────────────────


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


def _detail_from_moments(theme: str, moments: list[dict]) -> dict:
    # Strongest moment leads so the headline is the thing a parent would object to;
    # ties stay in transcript order.
    ordered = sorted(moments, key=lambda m: (not m.get("curated"), -m["intensity"]))
    instances = [
        {
            "kind": m["kind"],
            "speaker": m.get("speaker"),
            "text": m["text"],
            "mode": m["mode"],
            "intensity": m["intensity"],
            "at": m["at"],
        }
        for m in ordered
    ]
    top = max(m["intensity"] for m in moments)
    modes = {m["mode"] for m in moments}
    return {
        "theme": theme,
        "group": group_of(theme),
        "how": render_instance(instances[0]),
        "count": len(instances),
        "intensity": top,
        "mode": "on-screen" if "on-screen" in modes else ("dialogue" if "dialogue" in modes else "implied"),
        "instances": instances,
    }


def build_themes(
    *,
    body: str = "",
    show_id: str | None = None,
    sex: int = 1,
    language: int = 1,
    violence: int = 1,
    flags: list[str] | None = None,
    override_examples: list[str] | None = None,
    moments: list[dict] | None = None,
) -> dict:
    """
    watch          — default themes, in group order (drives filters and scores)
    watch_detail   — [{theme, group, intensity, mode, count, instances}]
    optional       — opt-in themes (LGBTQ storylines); never scored, hidden by default
    """
    if moments is None:
        moments = collect_moments(body, flags)

    grouped: dict[str, list[dict]] = {}
    for m in moments:
        grouped.setdefault(m["theme"], []).append(m)

    # damn / hell / crap on their own is sitcom texture, not a parent warning
    swearing = grouped.get("Swearing")
    if swearing and all(m["intensity"] <= 1 for m in swearing):
        grouped.pop("Swearing")

    # A curated blurb leads its theme, but identity blurbs only ever reach the opt-in shelf.
    for blurb in override_examples or []:
        note = {
            "theme": None,
            "kind": "note",
            "speaker": None,
            "text": blurb.strip(),
            "mode": "implied",
            "intensity": 2,
            "at": "mid",
            "trigger": "curated",
            "sev": 3,
            "curated": True,
        }
        for label in map_blurb_to_themes(blurb):
            bucket = grouped.setdefault(label, [])
            bucket.insert(0, {**note, "theme": label, "group": group_of(label)})
            del bucket[MAX_INSTANCES:]

    watch = [t for t in CANONICAL_WATCH if t in grouped]
    optional = [t for t in OPT_IN_THEMES if t in grouped]

    # Score floors can surface a theme the transcript never spelled out.
    def ensure(theme: str, condition: bool) -> None:
        if condition and theme not in watch:
            grouped.setdefault(
                theme,
                [
                    {
                        "theme": theme,
                        "group": group_of(theme),
                        "kind": "note",
                        "speaker": None,
                        "text": THEME_BLURB[theme],
                        "mode": "implied",
                        "intensity": 2,
                        "at": "mid",
                        "trigger": "score-floor",
                        "sev": 3,
                    }
                ],
            )
            watch.append(theme)

    ensure(
        "Sex & hookups",
        sex >= 4 and not any(group_of(t) == "sex" for t in watch),
    )
    ensure("Swearing", language >= 4 and "Swearing" not in watch)
    ensure(
        "Violence & injury",
        violence >= 4 and not any(group_of(t) == "violence" for t in watch),
    )

    watch = [t for t in CANONICAL_WATCH if t in watch]

    watch_detail = [_detail_from_moments(t, grouped[t]) for t in watch]
    optional_detail = [_detail_from_moments(t, grouped[t]) for t in optional]

    fine = fine_themes_for(show_id, sex=sex, language=language, violence=violence, watch=watch)
    notes_extra = _uniq(list(override_examples or []), limit=3)
    if not watch and not fine:
        fine = ["Typical light comedy — nothing standout"]

    return {
        "fine": fine,
        "watch": watch,
        "watch_detail": watch_detail,
        "optional": optional,
        "optional_detail": optional_detail,
        "notes_extra": notes_extra,
    }


def themes_as_examples(themes: dict) -> list[str]:
    """Episode bullets: Theme — how it shows up."""
    details = themes.get("watch_detail") or []
    if details:
        return [f"{d['theme']} — {d['how']}" for d in details][:6]
    return _uniq((themes.get("notes_extra") or []) + (themes.get("watch") or []), limit=5)


def why_this_score(show_id: str | None, scores: dict, themes: dict) -> str:
    """One line a parent can read instead of trusting the number blind."""
    details = sorted(
        themes.get("watch_detail") or [],
        key=lambda d: (-int(d.get("intensity") or 1), -int(d.get("count") or 1)),
    )
    overall = int(scores.get("overall") or 1)
    if not details:
        return "Nothing adult stood out in the transcript, so this scores at the bottom of the scale."

    lead = details[0]
    mode = {
        "on-screen": "shown on screen",
        "dialogue": "in dialogue",
        "implied": "implied",
    }[lead.get("mode", "dialogue")]
    strength = INTENSITY_LABEL[int(lead.get("intensity") or 1)]
    driver = f"{lead['theme'].lower()} ({strength}, {mode})"

    if overall <= 2:
        return f"Scores low: the strongest thing we found is {driver}."
    if overall == 3:
        return f"Sits in the gray area mainly on {driver}."
    if len(details) > 1:
        second = details[1]["theme"].lower()
        return f"Driven by {driver}, with {second} alongside it."
    return f"Driven by {driver}."

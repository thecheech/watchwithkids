"""Common Sense Media-style Parents Need to Know copy — per episode."""

from __future__ import annotations

import re

from shows_meta import episode_age, meta_for
from themes import THEME_BLURB, group_of, severity_tier

# Short phrases for the one-line tagline (CSM-style subtitle).
THEME_TAG = {
    "Sex & hookups": "sex talk",
    "Nudity & bodies": "nudity",
    "Porn / strippers / sex work": "strip-club and porn references",
    "Affairs / cheating": "affairs and cheating",
    "Violence & injury": "violence",
    "Suicide & self-harm": "suicide references",
    "Swearing": "language",
    "Alcohol & drugs": "drinking",
    "Racism & slurs": "racist language",
    "Homophobic jokes": "homophobic jokes",
    "Fat-shaming": "fat-shaming",
    "Sexual insults": "sexual insults",
    "LGBTQ themes": "LGBTQ characters and storylines",
}

# Score-driven tagline fallbacks when no theme detail is present.
SCORE_TAG = {
    "violence": {2: "mild violence", 3: "violence", 4: "strong violence", 5: "heavy violence"},
    "sex": {2: "mild sexual content", 3: "sex talk", 4: "strong sexual content", 5: "heavy sexual content"},
    "language": {2: "mild language", 3: "language", 4: "strong language", 5: "heavy language"},
}


def _ep_label(ep: dict) -> str:
    num = str(ep.get("episode", "")).lstrip("0") or str(ep.get("episode", ""))
    if str(ep.get("season")) == "0":
        return f"Ep {num}"
    return f"S{ep.get('season')} E{num}"


def _watch_details(ep: dict) -> list[dict]:
    themes = ep.get("themes") or {}
    detail = themes.get("watch_detail") or []
    if detail:
        return [d for d in detail if d and d.get("theme")]
    return [
        {"theme": t, "how": "", "count": 1, "instances": [], "severity": 2}
        for t in themes.get("watch") or []
        if t
    ]


def _detail_rank(d: dict) -> tuple:
    sev = int(d.get("severity") or severity_tier(int(d.get("intensity") or 1)))
    return (-sev, -int(d.get("count") or 1), d.get("theme") or "")


def _sorted_details(ep: dict) -> list[dict]:
    return sorted(_watch_details(ep), key=_detail_rank)


def _clip(text: str, max_len: int = 110) -> str:
    text = re.sub(r"\s+", " ", (text or "").strip()).rstrip(".")
    if len(text) <= max_len:
        return text
    cut = text[: max_len - 1].rsplit(" ", 1)[0]
    return (cut or text[: max_len - 1]) + "…"


def _detail_example(d: dict) -> str:
    for inst in d.get("instances") or []:
        text = (inst.get("text") or "").strip()
        if not text:
            continue
        text = _clip(text, 90)
        if inst.get("kind") == "quote" and inst.get("speaker"):
            return f'{inst["speaker"]} says, "{text}"'
        return text
    how = (d.get("how") or "").strip()
    if how:
        return _clip(how, 90)
    return THEME_BLURB.get(d.get("theme") or "", "")


def _join_examples(details: list[dict], limit: int = 2) -> str:
    bits = []
    for d in details:
        ex = _detail_example(d)
        if ex and ex not in bits:
            bits.append(ex)
        if len(bits) >= limit:
            break
    if not bits:
        return ""
    if len(bits) == 1:
        return bits[0]
    return f"{bits[0]}; {bits[1]}"


def _age_for(show_id: str, ep: dict) -> int:
    if ep.get("age") is not None:
        return int(ep["age"])
    return episode_age(show_id, int(ep.get("overall") or 1))


def _tagline_phrases(ep: dict, details: list[dict]) -> list[str]:
    phrases: list[str] = []
    seen: set[str] = set()

    def add(phrase: str) -> None:
        key = phrase.lower()
        if key not in seen:
            seen.add(key)
            phrases.append(phrase)

    for d in _sorted_details(ep):
        theme = d.get("theme") or ""
        tag = THEME_TAG.get(theme)
        if tag:
            if theme == "Violence & injury" and int(ep.get("violence") or 1) >= 4:
                add("bloody violence")
            else:
                add(tag)
        if len(phrases) >= 3:
            return phrases[:3]

    for dim in ("language", "violence", "sex"):
        score = int(ep.get(dim) or 1)
        if score >= 2:
            add(SCORE_TAG[dim].get(score, SCORE_TAG[dim][3]))
        if len(phrases) >= 3:
            break

    return phrases[:3]


def pnk_tagline(show_id: str, ep: dict) -> str:
    meta = meta_for(show_id)
    fmt = meta.get("format") or "TV episode"
    details = _watch_details(ep)
    phrases = _tagline_phrases(ep, details)
    if not phrases:
        return f"Mostly mild {fmt}."
    lead = ", ".join(phrases[:3])
    lead = lead[0].upper() + lead[1:]
    return f"{lead} in {fmt}."


def _violence_sentence(ep: dict, details: list[dict]) -> str:
    score = int(ep.get("violence") or 1)
    v_details = [d for d in details if group_of(d.get("theme") or "") == "violence"]
    suicide = [d for d in v_details if d.get("theme") == "Suicide & self-harm"]
    injury = [d for d in v_details if d.get("theme") != "Suicide & self-harm"]
    parts: list[str] = []

    if suicide:
        ex = _join_examples(suicide)
        if ex:
            parts.append(f"Suicide or self-harm is raised — for example, {ex}.")
        else:
            parts.append("Suicide or self-harm is raised in the dialogue.")

    if injury:
        examples = _join_examples(injury)
        if score >= 4:
            lead = "Violence is strong in this episode"
        elif score >= 3:
            lead = "Violence includes"
        else:
            lead = "Violence is mild but includes"
        if examples:
            if lead.endswith("includes"):
                parts.append(f"{lead} {examples}.")
            else:
                parts.append(f"{lead} — for example, {examples}.")
        else:
            themes = ", ".join(d["theme"].lower() for d in injury[:2])
            parts.append(f"{lead} {themes}.")

    if not parts and score >= 2:
        parts.append("Some mild violence appears in this episode.")

    return " ".join(parts)


def _sex_sentence(ep: dict, details: list[dict]) -> str:
    score = int(ep.get("sex") or 1)
    s_details = [d for d in details if group_of(d.get("theme") or "") == "sex"]
    if score < 2 and not s_details:
        return ""
    examples = _join_examples(s_details)
    if score >= 4:
        lead = "Sexual content is explicit"
    elif score >= 3:
        lead = "Sexual content includes"
    elif s_details:
        lead = "Sexual content is mild but includes"
    else:
        lead = "Some mild sexual content appears"
    if examples:
        if lead.endswith("includes"):
            return f"{lead} {examples}."
        return f"{lead} — for example, {examples}."
    if s_details:
        themes = ", ".join(d["theme"].lower() for d in s_details[:2])
        return f"{lead}: {themes}."
    return f"{lead}."


def _language_sentence(ep: dict, details: list[dict]) -> str:
    score = int(ep.get("language") or 1)
    if score < 2:
        return ""
    swearing = [d for d in details if d.get("theme") == "Swearing"]
    examples = _join_examples(swearing, limit=1)
    if score >= 4:
        base = "Language includes strong swearing"
    elif score >= 3:
        base = "Language isn't constant, but you can expect swearing"
    else:
        base = "Some mild language appears"
    if examples:
        return f"{base} — for example, {examples}."
    if score >= 3:
        return f"{base}, including stronger words."
    return f"{base} in the dialogue."


def _other_sentences(details: list[dict]) -> list[str]:
    covered = {"sex", "violence", "language"}
    out: list[str] = []
    for d in sorted(details, key=_detail_rank):
        theme = d.get("theme") or ""
        grp = group_of(theme)
        if grp in covered:
            continue
        ex = _detail_example(d)
        if grp == "substances":
            out.append(
                f"Characters drink or talk about alcohol and drugs{f' — {ex}' if ex else ''}."
            )
        elif grp == "bias":
            out.append(
                f"This episode includes {theme.lower()}{f' — for example, {ex}' if ex else ''}."
            )
        elif grp == "optin":
            out.append(
                f"This episode includes {theme.lower()}{f' ({ex})' if ex else ''}."
            )
        if len(out) >= 2:
            break
    return out


def pnk_body(show_name: str, show_id: str, ep: dict) -> str:
    meta = meta_for(show_id)
    label = _ep_label(ep)
    title = (ep.get("title") or "").strip()
    fmt = meta.get("format") or "TV episode"
    details = _watch_details(ep)

    opener = (
        f"Parents need to know that {show_name} {label}, \"{title}\", "
        f"is a {fmt} episode"
    )
    note = (meta.get("note") or "").strip()
    if note:
        note_text = note[0].lower() + note[1:] if note else note
        opener += f". The series is known for {note_text.rstrip('.')}"
    opener += "."

    if not details and int(ep.get("overall") or 1) <= 2:
        return (
            f"{opener} Our transcript scan didn't flag adult themes in this one — "
            "it's one of the milder entries in the series."
        )

    parts = [opener]
    why = (ep.get("why") or "").strip()
    if why and details:
        parts.append(why.rstrip(".") + ".")

    for fn in (_violence_sentence, _sex_sentence, _language_sentence):
        sent = fn(ep, details)
        if sent:
            parts.append(sent)

    parts.extend(_other_sentences(details))

    if not details:
        parts.append(
            "Our transcript scan didn't flag specific adult themes, "
            "but the content scores above still apply."
        )
    else:
        parts.append(
            "Every flagged moment below is a direct quote from the transcript "
            "or a short description of what happens on screen."
        )

    return " ".join(parts)


def pnk_content(show_name: str, show_id: str, ep: dict) -> dict:
    """Plain-text Parents Need to Know fields for one episode."""
    age = _age_for(show_id, ep)
    return {
        "age": age,
        "tagline": pnk_tagline(show_id, ep),
        "body": pnk_body(show_name, show_id, ep),
    }

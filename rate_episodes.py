#!/usr/bin/env python3
"""Rate each Friends episode for kid-watchability: violence, sex, language (1-5)."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from catalog import clean_episode_title, dedupe_codes
from shows_meta import episode_age, meta_for
from themes import (
    build_themes,
    collect_moments,
    evidence_caps,
    scrub_rating_false_positives,
    themes_as_examples,
    why_this_score,
)

ROOT = Path(__file__).resolve().parent
EPISODES = json.loads((ROOT / "episodes.json").read_text())
SHOW_ID = "friends"

# 1 = fine / none · 2 = mild · 3 = moderate · 4 = strong · 5 = heavy for this show
SCALE = {
    "violence": "Physical harm, fights, scary injury, weapons (slapstick counts lightly).",
    "sex": "Sex talk, innuendo, affairs, nudity jokes, strippers, pregnancy/sex plots.",
    "language": "Swears, crude insults, sexual slang (damn/hell mild; stronger words higher).",
}

# Episode-code overrides: explicit examples parents care about.
# Scores here win over heuristics when set.
OVERRIDES: dict[str, dict] = {
    "0101": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Opening banter: Monica says the dinner is 'not having sex.'",
            "Chandler's naked cafeteria dream / phone-in-crotch joke.",
            "Ross and Carol's marriage ending; lesbian reveal is handled lightly but is adult relationship material.",
        ],
    },
    "0102": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Carol's pregnancy from Ross; custody/relationship conflict.",
            "Rachel and Barry's leftover wedding/affair context.",
        ],
    },
    "0106": {
        "sex": 4,
        "language": 2,
        "violence": 1,
        "examples": [
            "Joey's underwear modeling / 'day of the butt' body-objectifying plot.",
            "Joey sleeps with an actress then discovers she's married.",
        ],
    },
    "0107": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Rachel and Italian neighbor almost kiss during blackout flirtation.",
        ],
    },
    "0109": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Underpants-on-the-head running gag; Monica dates a younger guy jokes.",
        ],
    },
    "0112": {
        "sex": 4,
        "language": 2,
        "violence": 1,
        "examples": [
            "Rachel finds Barry and Mindy in her bed (affair reveal).",
            "Heavy dating/sex-adjacent relationship comedy throughout.",
        ],
    },
    "0115": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Joey wears all of Chandler's clothes as a bet; intimacy/roommate boundary jokes.",
        ],
    },
    "0123": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Rachel almost boards the plane for Italy with Paolo; romantic climax of S1.",
        ],
    },
    "0124": {
        "sex": 4,
        "language": 2,
        "violence": 1,
        "examples": [
            "Ross and Rachel almost get together; airport chase romance peak.",
            "Sexual tension is the A-plot.",
        ],
    },
    "0202": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Breastfeeding / milk jokes around Carol and Susan's baby.",
        ],
    },
    "0204": {
        "sex": 5,
        "language": 3,
        "violence": 1,
        "examples": [
            "Phoebe reveals she is married; husband is gay — adult marriage/sexuality plot.",
            "Dialogue includes porn-video and explicit sex references.",
        ],
    },
    "0203": {
        "sex": 3,
        "language": 2,
        "violence": 2,
        "examples": [
            "Joey in a 'period' movie role; mild crude jokes.",
        ],
    },
    "0207": {
        "sex": 4,
        "language": 2,
        "violence": 1,
        "examples": [
            "Ross and Rachel sleep together for the first time (morning-after episode).",
        ],
    },
    "0208": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "List of Rachel's flaws; relationship fallout after first night together.",
        ],
    },
    "0209": {
        "sex": 4,
        "language": 3,
        "violence": 1,
        "examples": [
            "Phoebe's fake name / 'Regina Phalange' doctor flirting; sexual innuendo with patient roleplay vibe.",
            "Chandler and Janice sex life jokes.",
        ],
    },
    "0212-0213": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Super Bowl party; Eddie's creepy roommate energy.",
            "Romantic tension and adult party drinking.",
        ],
    },
    "0214": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Joey dates a student; age-gap dating discomfort.",
        ],
    },
    "0218": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Dr. Green and Rachel's dad conflict; adult relationship stress.",
        ],
    },
    "0223": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Richard proposes waiting on kids; Monica/Richard breakup (adult themes).",
        ],
    },
    "0224": {
        "sex": 4,
        "language": 2,
        "violence": 1,
        "examples": [
            "Monica and Richard's age-gap relationship ends; sexual history implied.",
            "Ross sees Rachel kiss in the next beat setup.",
        ],
    },
    "0301": {
        "sex": 4,
        "language": 2,
        "violence": 1,
        "examples": [
            "Ross sees Rachel kissing Mark — jealousy/affair anxiety drives the hour.",
        ],
    },
    "0302": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Ross and Rachel officially break up; 'we were on a break' begins.",
        ],
    },
    "0304": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Phoebe finds out her mother killed herself (heavy emotional content; not sex/violence).",
        ],
        "notes": "Grief/suicide mention — flag for sensitive kids even if sex/violence scores are moderate.",
    },
    "0309": {
        "sex": 4,
        "language": 3,
        "violence": 1,
        "examples": [
            "Ross sleeps with Chloe the copy-shop woman while 'on a break.'",
        ],
    },
    "0311": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Rachel learns about Chloe; confrontation after the affair.",
        ],
    },
    "0312": {
        "sex": 4,
        "language": 2,
        "violence": 1,
        "examples": [
            "All-out Ross/Rachel fight over the break and Chloe.",
        ],
    },
    "0315": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Ross dates a woman who looks like Rachel; rebound dating comedy.",
        ],
    },
    "0316": {
        "sex": 3,
        "language": 2,
        "violence": 2,
        "examples": [
            "Chandler and Joey fight over a girl; competitive dating.",
        ],
    },
    "0321": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Pete proposes to Monica; adult relationship pressure.",
        ],
    },
    "0322": {
        "sex": 2,
        "language": 2,
        "violence": 3,
        "examples": [
            "Pete's cage-fighting / MMA plot — sport violence on screen.",
        ],
    },
    "0325": {
        "sex": 4,
        "language": 2,
        "violence": 1,
        "examples": [
            "Monica and Richard almost reconnect; sexual tension returns.",
            "Ross's relationship with Bonnie (bald girlfriend) jokes.",
        ],
    },
    "0408": {
        "sex": 4,
        "language": 3,
        "violence": 1,
        "examples": [
            "Chandler and Kathy: Joey's girlfriend kiss / cheating triangle.",
        ],
    },
    "0409": {
        "sex": 4,
        "language": 2,
        "violence": 1,
        "examples": [
            "Chandler sleeps with Kathy after the triangle blows up.",
        ],
    },
    "0411": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Phoebe carries her brother's triplets — pregnancy is medical/adult.",
        ],
    },
    "0412": {
        "sex": 4,
        "language": 3,
        "violence": 1,
        "examples": [
            "Everyone finds out Monica and Chandler are secretly sleeping together.",
        ],
    },
    "0413": {
        "sex": 4,
        "language": 2,
        "violence": 1,
        "examples": [
            "Chandler spirals after thinking Kathy is sleeping with her co-star.",
            "Ross jokes about 'cookies and porn' while his mom visits.",
        ],
    },
    "0414": {
        "sex": 5,
        "language": 3,
        "violence": 2,
        "examples": [
            "Joey's bachelor-party / strip-club day after a dirty movie role.",
            "Multiple strippers; 'get drunk and go to a strip club' is the plot.",
        ],
    },
    "0415": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Joey's porn-adjacent 'Days of Our Lives' storyline vibes; adult soap plots.",
        ],
    },
    "0417": {
        "sex": 5,
        "language": 2,
        "violence": 1,
        "examples": [
            "Central joke: free porn channel they can't (won't) turn off.",
            "Phone-sex / porn-addiction comedy throughout.",
        ],
    },
    "0418": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Rachel's messy romantic jealousy around Joshua.",
        ],
    },
    "0419": {
        "sex": 4,
        "language": 2,
        "violence": 1,
        "examples": [
            "Monica and Rachel offer to kiss each other for one minute so the guys will give back the apartment.",
            "Time-lapse beat: the guys take the deal — 'Totally worth it!' / 'That was one good minute!'",
            "Classic male-gaze 'girls kissing' sitcom gag; not the whole episode, but a clear adult beat.",
        ],
    },
    "0420": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Joey in a European art film with a nude actress — nudity/sex-work adjacent jokes.",
        ],
    },
    "0422": {
        "sex": 5,
        "language": 3,
        "violence": 1,
        "examples": [
            "Joey hires a stripper for Ross's bachelor party; stripper chaos.",
            "Stripper plot dominates the episode.",
        ],
    },
    "0423": {
        "sex": 4,
        "language": 2,
        "violence": 1,
        "examples": [
            "London wedding; Monica and Chandler hook up (secret affair starts).",
            "Ross's wedding drunkenness and cold feet.",
        ],
    },
    "0501": {
        "sex": 4,
        "language": 3,
        "violence": 1,
        "examples": [
            "Ross says Emily's name at the altar — wedding disaster.",
            "Monica/Chandler continue secret sex relationship.",
        ],
    },
    "0502": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Aftermath of the wedding; Monica/Chandler hide the affair.",
        ],
    },
    "0503": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Everyone learns Monica and Chandler are together.",
        ],
    },
    "0508": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Thanksgiving flashbacks include Monica's fat suit and Chandler's insult that shapes her life — body image, not sex.",
        ],
    },
    "0509": {
        "sex": 4,
        "language": 2,
        "violence": 1,
        "examples": [
            "Ross and Emily's annulment; romantic/sexual relationship bureaucracy.",
        ],
    },
    "0512": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Chandler's dad Bob/Helena — drag & Las Vegas showgirl parent; queer/adult nightlife jokes.",
        ],
    },
    "0514": {
        "sex": 4,
        "language": 3,
        "violence": 1,
        "examples": [
            "Rachel writes a steamy letter to Ross; sexual fantasy content read aloud.",
        ],
    },
    "0516": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Rachel and Ralph Lauren guy; dating comedy.",
        ],
    },
    "0518": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Rachel and Joey's kiss setup begins (later payoff).",
        ],
    },
    "0520": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Joey and Katie Holmes character — dating a younger actress jokes.",
        ],
    },
    "0521": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Andie MacDowell arc; Ross's rebound dating.",
        ],
    },
    "0523": {
        "sex": 4,
        "language": 3,
        "violence": 1,
        "examples": [
            "Las Vegas: Ross and Rachel drunkenly marry.",
            "Strip-club / casino adult party atmosphere.",
        ],
    },
    "0601": {
        "sex": 4,
        "language": 2,
        "violence": 1,
        "examples": [
            "Ross and Rachel wake up married in Vegas — sex/alcohol implication.",
        ],
    },
    "0605": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Joey's 'hot' apartment neighbor / seduction attempts.",
        ],
    },
    "0607": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Paul the wine guy / Rachel's dating; impotence jokes in related arcs nearby seasons.",
        ],
    },
    "0608": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Monica's parents learn about Chandler; adult partnership talk.",
        ],
    },
    "0609": {
        "sex": 2,
        "language": 2,
        "violence": 2,
        "examples": [
            "Ross's sandwich rage — workplace anger meltdown (comic, not graphic).",
        ],
    },
    "0614": {
        "sex": 4,
        "language": 2,
        "violence": 1,
        "examples": [
            "Adult sexuality jokes run through side plots (high sex-term density in dialogue).",
            "Joey/Thanksgiving turkey slapstick is mild by comparison.",
        ],
    },
    "0615-0616": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Proposal episode — romantic climax; adult commitment themes.",
        ],
    },
    "0618": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Ralph Lauren underwear campaign; body/sex-appeal comedy.",
        ],
    },
    "0619": {
        "sex": 4,
        "language": 2,
        "violence": 1,
        "examples": [
            "Joey and Rachel almost kiss; sexual tension becomes explicit plot.",
        ],
    },
    "0624": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Monica and Chandler's wedding plans; binge drinking at bachelor/ette setups later.",
        ],
    },
    "0702": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Rachel's sister Jill flirts with Ross — inappropriate attraction jokes.",
        ],
    },
    "0705": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Phoebe runs / stalking-adjacent crush comedy with police officer.",
        ],
    },
    "0708": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Rachel's sister Amy; family dysfunction, pregnancy jokes later seasons.",
        ],
    },
    "0712": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Chandler's stripper bachelor surprise; strip-club energy.",
        ],
    },
    "0715": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Joey and Rachel's kiss (they act on attraction).",
        ],
    },
    "0716": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Fallout of Joey/Rachel kiss; adult romantic conflict.",
        ],
    },
    "0719": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Chandler's missing stripper 'party favor' confusion — stripper hired for party.",
        ],
    },
    "0722": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Chandler's dad in Vegas-style showgirl costume at wedding events.",
        ],
    },
    "0723": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Wedding; Rachel learns she's pregnant (sex consequence becomes season arc).",
        ],
    },
    "0801": {
        "sex": 4,
        "language": 2,
        "violence": 1,
        "examples": [
            "Who is the father? Rachel's pregnancy reveal — sex as central plot.",
        ],
    },
    "0802": {
        "sex": 4,
        "language": 2,
        "violence": 1,
        "examples": [
            "Ross is the father; flashbacks to the night they slept together.",
        ],
    },
    "0804": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Video of childbirth class / pregnancy body humor.",
        ],
    },
    "0806": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Halloween pregnancy costumes; body jokes.",
        ],
    },
    "0807": {
        "sex": 4,
        "language": 2,
        "violence": 1,
        "examples": [
            "Couple may have had sex on a table Monica and Chandler buy — gross-out sex joke.",
            "Pregnancy / stain misunderstandings.",
        ],
    },
    "0808": {
        "sex": 5,
        "language": 3,
        "violence": 1,
        "examples": [
            "Chandler's bachelor-party stripper (elderly stripper gag).",
            "Stripper stays in their lives; sex-work comedy is the A-plot.",
        ],
    },
    "0809": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Rachel's baby shower; pregnancy intimacy discussion.",
        ],
    },
    "0814": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Monica and Chandler try to conceive — timed sex schedule comedy.",
        ],
    },
    "0815": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "More trying-to-get-pregnant sex scheduling.",
        ],
    },
    "0818": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Birthing video / graphic birth discussion for Rachel.",
        ],
    },
    "0821": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Phoebe and Mike romance; adult dating.",
        ],
    },
    "0823": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Rachel gives birth — labor scenes, medical intimacy.",
        ],
    },
    "0901": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Joey tells Rachel he loves her in the hospital — romantic intensity postpartum.",
        ],
    },
    "0902": {
        "sex": 4,
        "language": 2,
        "violence": 1,
        "examples": [
            "Ross and Charlie (grad student) — professor/student attraction begins later; early S9 dating.",
        ],
    },
    "0907": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Emma's first Christmas; mostly mild — babysitter panic.",
        ],
    },
    "0908": {
        "sex": 4,
        "language": 3,
        "violence": 1,
        "examples": [
            "Rachel and Joey become a couple — sex implied as relationship starts.",
        ],
    },
    "0909": {
        "sex": 4,
        "language": 2,
        "violence": 1,
        "examples": [
            "Phoebe finds Mike and David triangle; romantic/sexual choice plot.",
        ],
    },
    "0911": {
        "sex": 4,
        "language": 3,
        "violence": 1,
        "examples": [
            "Rachel and Joey try to tell Ross; sexual relationship secrecy.",
        ],
    },
    "0913": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Monica's 'hot' pot dealer cousin? Actually massage/donor arcs nearby — check donor episode.",
        ],
    },
    "0916": {
        "sex": 4,
        "language": 2,
        "violence": 1,
        "examples": [
            "Sperm donor / fertility clinic — explicit reproduction talk for Monica/Chandler.",
        ],
    },
    "0918": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Lottery ticket / roommate stress — milder.",
        ],
    },
    "0919": {
        "sex": 4,
        "language": 2,
        "violence": 1,
        "examples": [
            "Rachel and Joey's relationship awkwardness around Ross; intimacy comedy.",
        ],
    },
    "0920": {
        "sex": 4,
        "language": 3,
        "violence": 1,
        "examples": [
            "Joey and Rachel break up after realizing it doesn't work — sex/romance heavy.",
        ],
    },
    "0921": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Charlie and Ross; professor dating a student (power-dynamic concern).",
        ],
    },
    "0922": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Phoebe's wedding planning; adult commitment.",
        ],
    },
    "0923-0924": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Phoebe and Mike marry in the street; Charlie/Joey/Ross romantic reshuffle.",
        ],
    },
    "1001": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Ross and Charlie continue; Joey dates Charlie — romantic musical chairs.",
        ],
    },
    "1002": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Ross's paleontology grant / Charlie intimacy.",
        ],
    },
    "1003": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Joey's agent / sex-comedy side plots typical late series.",
        ],
    },
    "1005": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Phoebe's police officer husband jokes; mild.",
        ],
    },
    "1007": {
        "sex": 2,
        "language": 2,
        "violence": 1,
        "examples": [
            "Book of recipes / Thanksgiving — among the milder late episodes.",
        ],
    },
    "1008": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Late-series dating and infertility stress for Monica/Chandler.",
        ],
    },
    "1009": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Ross and Charlie break up; Rachel considers Paris.",
        ],
    },
    "1011": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Surrogate/adoption agency interviews — adult family planning.",
        ],
    },
    "1013": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Monica and Chandler get the adoption call.",
        ],
    },
    "1014": {
        "sex": 4,
        "language": 2,
        "violence": 1,
        "examples": [
            "Rachel and Ross sleep together before she leaves for Paris (implied).",
        ],
    },
    "1015": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Estelle dies; Joey's agent funeral — mortality, mild.",
        ],
    },
    "1016": {
        "sex": 3,
        "language": 2,
        "violence": 1,
        "examples": [
            "Rachel's goodbye party; romantic unresolved tension.",
        ],
    },
    "1017-1018": {
        "sex": 4,
        "language": 2,
        "violence": 1,
        "examples": [
            "Series finale: Ross and Rachel get back together; adoption delivery room.",
            "Emotional adult romance climax — fine for many teens, intense for little kids.",
        ],
    },
}

# Heuristic lexicons (case-insensitive word-ish matches).
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
    (r"\bpregnancy\b", 1),
    (r"\bsperm\b", 3),
    (r"\binsemination\b", 3),
    (r"\bfertility\b", 2),
    (r"\baffair\b", 2),
    (r"\bthreesome\b", 4),
    (r"\bbreast(?:s|feeding)?\b", 2),
    (r"\bnipple\b", 3),
    (r"\bpenis\b", 4),
    (r"\bvagina\b", 4),
    (r"\bprostitut", 4),
    (r"\bviagra\b", 3),
    (r"\bimpoten", 3),
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
    (r"\bbeat(?:s|en|ing)?\b", 1),
    (r"\battack", 1),
    (r"\bwrestl", 1),
    (r"\bcage\b", 1),
    (r"\bsuicide\b", 3),
    (r"\bhit(?:s|ting)?\b", 1),
]

# Targeted tropes: raise a floor for specific adult beats WITHOUT blanket-flagging
# every kiss / dating joke. Keep patterns narrow — prefer misses over mass false positives.
TROPE_RULES: list[tuple[str, str, int, str]] = [
    (
        "girl_girl_kiss_offer",
        # Only clear spectacle / offer / on-the-lips beats — not cheek kisses or loose nearby names.
        r"(rachel|monica|phoebe) and i will kiss|"
        r"(rachel|monica|phoebe) and (rachel|monica|phoebe) will kiss|"
        r"kiss(?:es|ed|ing)? (?:her |rachel |monica |phoebe )?on the lips|"
        r"\((?:suddenly,? )?(?:phoebe|rachel|monica) leans in and kisses (?:her|rachel|monica|phoebe)",
        4,
        "Main-cast women kissing each other (sitcom gag / spectacle).",
    ),
    (
        "kiss_bribe",
        r"kiss for (one|a|1|two) minutes?|"
        r"as a thank you,\s*(rachel|monica|phoebe) and i will kiss|"
        r"as a thank you.{0,40}kiss for",
        4,
        "Kiss used as a bribe / performance (not a normal couple kiss).",
    ),
    (
        "porn_plot",
        r"\bfree porn\b|\bporn channel\b|\bwatching porn\b|\bgot (?:the )?free porn\b|\bphone sex\b",
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
        r"\b(penis|vagina|orgasm|threesome)\b",
        4,
        "Explicit sexual body / sex-act language.",
    ),
]


def find_line(body: str, pat: str) -> str | None:
    for line in body.splitlines():
        if re.search(pat, line, re.I):
            cleaned = " ".join(line.split())
            if 12 < len(cleaned) < 160:
                return cleaned
    return None


def apply_tropes(body: str) -> dict:
    """Catch specific adult sitcom tropes that keyword counts miss."""
    lower = body.lower()
    flags: list[str] = []
    min_sex = 1
    for name, pat, floor, _note in TROPE_RULES:
        if re.search(pat, lower, re.S):
            flags.append(name)
            min_sex = max(min_sex, floor)
    return {"flags": flags, "min_sex": min_sex}


def clamp(n: int, lo: int = 1, hi: int = 5) -> int:
    return max(lo, min(hi, n))


def score_from_hits(weighted_hits: int, tiers: list[tuple[int, int]]) -> int:
    """Map weighted hit count to 1-5 using (min_hits, score) tiers ascending."""
    score = 1
    for threshold, value in tiers:
        if weighted_hits >= threshold:
            score = value
    return score


def analyze_text(text: str) -> dict:
    body = text.split("=" * 20, 1)[-1]
    lower = scrub_rating_false_positives(body.lower())

    sex_hits = []
    sex_weight = 0
    for pat, w in SEX_PATTERNS:
        found = re.findall(pat, lower)
        if found:
            sex_hits.append((pat, len(found), w))
            sex_weight += len(found) * w

    lang_hits = []
    lang_weight = 0
    for pat, w in LANG_PATTERNS:
        found = re.findall(pat, lower)
        if found:
            lang_hits.append((pat, len(found), w))
            lang_weight += len(found) * w

    viol_hits = []
    viol_weight = 0
    for pat, w in VIOL_PATTERNS:
        found = re.findall(pat, lower)
        if found:
            viol_hits.append((pat, len(found), w))
            viol_weight += len(found) * w

    sex = score_from_hits(sex_weight, [(0, 1), (3, 2), (8, 3), (18, 4), (35, 5)])
    language = score_from_hits(lang_weight, [(0, 1), (2, 2), (6, 3), (14, 4), (28, 5)])
    violence = score_from_hits(viol_weight, [(0, 1), (3, 2), (8, 3), (16, 4), (28, 5)])

    # Cap sitcom violence — Friends almost never exceeds 3 unless fight-sports plot.
    violence = min(violence, 3)

    tropes = apply_tropes(body)
    sex = max(sex, tropes["min_sex"])

    # Keyword counts propose; the evidence decides. Without a moment intense enough
    # to justify it, a dimension cannot climb into the 4–5 band.
    moments = collect_moments(body, tropes["flags"])
    caps = evidence_caps(moments)
    sex = max(1, min(sex, caps["sex"]))
    language = max(1, min(language, caps["language"]))
    violence = max(1, min(violence, caps["violence"]))

    themes = build_themes(
        show_id=SHOW_ID,
        sex=sex,
        language=language,
        violence=violence,
        moments=moments,
    )

    return {
        "sex": sex,
        "language": language,
        "violence": violence,
        "themes": themes,
        "moments": moments,
        "examples": themes_as_examples(themes),
        "flags": tropes["flags"],
        "signals": {
            "sex_weight": sex_weight,
            "language_weight": lang_weight,
            "violence_weight": viol_weight,
            "evidence_caps": caps,
            "sex_terms": [(p, c) for p, c, _ in sex_hits[:8]],
            "language_terms": [(p, c) for p, c, _ in lang_hits[:8]],
            "tropes": tropes["flags"],
        },
    }


def overall(v: int, s: int, lang: int) -> int:
    return max(v, s, lang)


def verdict(score: int, age: int) -> str:
    """Age-relative, so 'hard pass' never lands on a show nobody claimed was kids TV."""
    return {
        1: f"Usually fine — about {age}+",
        2: f"Mild — okay from about {age}+",
        3: f"Preview first — about {age}+",
        4: f"Skip for under {age}",
        5: f"Heavy — skip for under {age}",
    }[score]


def rate_episode(ep: dict) -> dict:
    path = ROOT / ep["file"]
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    heuristic = analyze_text(text) if text else {
        "sex": 2,
        "language": 2,
        "violence": 1,
        "themes": {"fine": [], "watch": [], "watch_detail": []},
        "moments": [],
        "examples": [],
        "flags": [],
        "signals": {},
    }

    code = ep["code"]
    over = OVERRIDES.get(code, {})

    # Overrides win when present; tropes still enforce a floor under heuristics.
    sex = over.get("sex", heuristic["sex"])
    language = over.get("language", heuristic["language"])
    violence = over.get("violence", heuristic["violence"])

    flags = list(heuristic.get("flags") or [])
    themes = build_themes(
        show_id=SHOW_ID,
        sex=sex,
        language=language,
        violence=violence,
        moments=list(heuristic.get("moments") or []),
        override_examples=list(over.get("examples") or []) or None,
    )
    # Prefer curated blurbs for detail bullets; chips still use themes.watch only
    examples = themes_as_examples(themes)
    if over.get("examples"):
        examples = list(over["examples"])[:4]

    o = overall(violence, sex, language)
    age = episode_age(SHOW_ID, o)
    source = "override+heuristic" if over else "heuristic"
    if flags and not over:
        source = "trope+heuristic"

    return {
        "season": ep["season"],
        "episode": ep["episode"],
        "code": code,
        "title": clean_episode_title(ep["title"], ep.get("index_title") or ""),
        "index_title": ep["index_title"],
        "url": ep["url"],
        "file": ep["file"],
        "violence": violence,
        "sex": sex,
        "language": language,
        "overall": o,
        "age": age,
        "verdict": verdict(o, age),
        "why": why_this_score(
            SHOW_ID,
            {"violence": violence, "sex": sex, "language": language, "overall": o},
            themes,
        ),
        "themes": themes,
        "examples": examples,
        "notes": over.get("notes"),
        "flags": flags,
        "source": source,
        "signals": heuristic.get("signals", {}),
    }


def main() -> None:
    ratings = dedupe_codes([rate_episode(ep) for ep in EPISODES])
    show_meta = meta_for(SHOW_ID)
    out = {
        "show": "Friends",
        "show_id": SHOW_ID,
        "shelf": show_meta["shelf"],
        "age": show_meta["age"],
        "age_floor": show_meta["floor"],
        "audience_note": show_meta.get("note", ""),
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
            "Informal parental guidance from transcript signals + known plot points — "
            "not an official rating. Taste varies by family."
        ),
        "count": len(ratings),
        "episodes": ratings,
    }
    (ROOT / "ratings.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")

    # Compact CSV for spreadsheets
    import csv

    with (ROOT / "ratings.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "season",
                "episode",
                "code",
                "title",
                "violence",
                "sex",
                "language",
                "overall",
                "age",
                "verdict",
                "example_1",
                "example_2",
                "example_3",
            ]
        )
        for r in ratings:
            ex = r["examples"] + ["", "", ""]
            w.writerow(
                [
                    r["season"],
                    r["episode"],
                    r["code"],
                    r["title"],
                    r["violence"],
                    r["sex"],
                    r["language"],
                    r["overall"],
                    r["age"],
                    r["verdict"],
                    ex[0],
                    ex[1],
                    ex[2],
                ]
            )

    dist = Counter(r["overall"] for r in ratings)
    print(f"Rated {len(ratings)} episodes → ratings.json, ratings.csv")
    print("Overall distribution:", dict(sorted(dist.items())))
    print(
        "Averages — "
        f"V={sum(r['violence'] for r in ratings)/len(ratings):.2f} "
        f"S={sum(r['sex'] for r in ratings)/len(ratings):.2f} "
        f"L={sum(r['language'] for r in ratings)/len(ratings):.2f}"
    )


if __name__ == "__main__":
    main()

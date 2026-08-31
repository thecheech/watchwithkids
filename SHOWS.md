# watchwithkids — shows

Plain-text episode transcripts. Each show lives in `transcripts/<show>/` with its own
`episodes.csv` / `episodes.json` index (Friends is at `transcripts/season-XX/` with the
index at the project root for compatibility with the web app).

| Show | Seasons | Transcript files | Words | Source |
|------|---------|------------------|-------|--------|
| [Adventure Time](transcripts/adventure-time/) | — | 305 | 642,234 | adventuretime.fandom.com |
| [Avatar: The Last Airbender](transcripts/avatar/) | — | 62 | 575,385 | avatar.fandom.com |
| [Bluey](transcripts/bluey/) | — | 154 | 420,719 | blueypedia.fandom.com |
| [Bob's Burgers](transcripts/bobs-burgers/) | 16 | 312 | 1,268,805 | springfieldspringfield.co.uk |
| [Brooklyn Nine-Nine](transcripts/brooklyn-nine-nine/) | 7 | 135 | 534,115 | springfieldspringfield.co.uk |
| [Family Guy](transcripts/family-guy/) | 24 | 456 | 1,429,993 | springfieldspringfield.co.uk |
| [Friends](episodes.json) | 10 | 228 | 879,510 | edersoncorbari.github.io/friends |
| [Full House](transcripts/full-house/) | 5 | 120 | 320,151 | springfieldspringfield.co.uk |
| [Futurama](transcripts/futurama/) | 11 | 141 | 852,953 | theinfosphere.org |
| [Gravity Falls](transcripts/gravity-falls/) | — | 63 | 212,804 | gravityfalls.fandom.com |
| [How I Met Your Mother](transcripts/how-i-met-your-mother/) | 9 | 208 | 625,893 | springfieldspringfield.co.uk |
| [kpop-demon-hunters](transcripts/kpop-demon-hunters/) | 1 | 1 | 10,082 | ? |
| [Malcolm in the Middle](transcripts/malcolm-in-the-middle/) | 7 | 151 | 422,764 | springfieldspringfield.co.uk |
| [Modern Family](transcripts/modern-family/) | 11 | 246 | 920,793 | springfieldspringfield.co.uk |
| [Parks and Recreation](transcripts/parks-and-recreation/) | 7 | 122 | 425,996 | springfieldspringfield.co.uk |
| [Phineas and Ferb](transcripts/phineas-and-ferb/) | — | 267 | 1,085,650 | phineasandferb.fandom.com |
| [Rick and Morty](transcripts/rick-and-morty/) | 9 | 82 | 273,333 | springfieldspringfield.co.uk |
| [Seinfeld](transcripts/seinfeld/) | 9 | 176 | 754,339 | seinfeldscripts.com |
| [South Park](transcripts/south-park/) | 28 | 335 | 1,075,300 | springfieldspringfield.co.uk |
| [SpongeBob SquarePants](transcripts/spongebob/) | — | 1060 | 2,241,402 | spongebob.fandom.com |
| [Steven Universe](transcripts/steven-universe/) | — | 191 | 568,804 | steven-universe.fandom.com |
| [The Big Bang Theory](transcripts/big-bang-theory/) | 12 | 279 | 795,605 | bigbangtrans.wordpress.com + springfieldspringfield (S11-12) |
| [The Fresh Prince of Bel-Air](transcripts/fresh-prince/) | 6 | 148 | 378,300 | springfieldspringfield.co.uk |
| [The Office (US)](transcripts/the-office/) | 9 | 186 | 677,992 | brianbuie/the-office (GitHub) |
| [The Simpsons](transcripts/simpsons/) | 26 | 564 | 1,883,638 | Todd Schneider dataset (via GitHub) |
| [wednesday](transcripts/wednesday/) | 2 | 16 | 73,731 | ? |
| [Young Sheldon](transcripts/young-sheldon/) | 7 | 141 | 370,387 | springfieldspringfield.co.uk |

**Total: 27 shows, 6,149 transcripts, 19,720,678 words.**

Notes:
- Friends: 228 files covering all 236 episodes (double episodes combined) + S7 outtakes special.
- Seinfeld: 176/179 — the 3 clip-show specials have no script by design.
- The Big Bang Theory: S1-10 from bigbangtrans (transcribed), S11-12 from springfieldspringfield (subtitle-derived).
- The Simpsons: 564 episodes with script data (subtitle/script-line dataset, 1989-2016 era).
- springfieldspringfield sources are subtitle-derived: dialogue without speaker names.
- Fandom/Infosphere sources are fan transcripts with speaker names and scene directions.

Scrapers live in `scrapers/` (`scrape_wiki.py` for MediaWiki/Fandom, `scrape_ss.py` for
springfieldspringfield, `scrape_tbbt.py`, `scrape_seinfeld.py`, `convert_datasets.py`).
Rebuild this file with `python3 scrapers/build_shows_index.py`.

# watchwithkids 🍿

Parental screening guide for TV shows: every episode scored **1–5** on
**violence**, **sex**, and **language**, with exact moments quoted — so you can decide before you press play.

**Live:** https://watchwiththekids.com/

## Quick start (local)

```bash
python3 build_web.py       # rebuild all show pages
python3 -m http.server 8765 --directory web
```

Open http://localhost:8765

## Adding a new show

See **[ADD_SHOW.md](ADD_SHOW.md)** for the complete guide.

**TL;DR:** Once you have transcripts and metadata:

```bash
python3 rate_show.py <show-id>    # generate ratings
python3 build_web.py              # build web pages
```

## Deploy

Only the `web/` folder is deployed (no transcripts):

```bash
python3 build_web.py
cd web && vercel --prod --yes
```

## Score scale

| Score | Meaning |
|------:|---------|
| 1 😇 | Chill |
| 2 🙂 | Mild |
| 3 😐 | Parent nearby |
| 4 😬 | Spicy |
| 5 🚫 | Nope |

**Overall** = max(violence, sex, language).

## Files

| Path | Role |
|------|------|
| `episodes.json` / `.csv` | Episode index |
| `rate_episodes.py` | Heuristic scan + curated overrides → ratings |
| `ratings.json` / `.csv` | Full scores + examples |
| `web/` | Browse UI (what ships to Vercel) |
| `transcripts/` | Local-only; used for rating signals, **not deployed** |
| `scrape.py` | Optional re-scrape of the public transcript index |

## Notes

- Ratings are informal (transcript keywords + known plot points), not an official board rating.
- Edit `OVERRIDES` in `rate_episodes.py` when you disagree, then rebuild + redeploy.

# watchwithkids 🍿

Parental screening guide for *Friends*: every episode scored **1–5** on
**violence**, **sex**, and **language**, with short examples — plus a fun
webpage to browse and filter.

**Live:** https://watchwithkids.vercel.app

## Quick start (local)

```bash
python3 rate_episodes.py   # rebuild ratings.json / ratings.csv
python3 build_web.py       # embed scores into web/data.js
python3 -m http.server 8765 --directory web
```

Open http://localhost:8765

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

# Add one show (hourly batch)

Source of truth for order/status: `batch/queue.json`.

Each scheduled run does **exactly one** show: the first entry with `"status": "pending"` (or continue `"in_progress"` if a prior run crashed mid-flight). Do not start a second show in the same run.

## Per-show checklist

### 0. Claim the show
1. Open `batch/queue.json`.
2. Pick the first `pending` (or unfinished `in_progress`) item.
3. Set `"status": "in_progress"` and save.
4. Confirm `id` / `ssSlug` / wiki URL still resolve (SS 404 → search alternate slug; wiki missing → try SS).

### 1. Scrape transcripts
```bash
cd /Users/kobykarp/projects/watchwithkids   # or repo root in cloud

# Springfield (most live-action / adult animation):
python3 scrapers/scrape_ss.py <id> <ssSlug>

# Fandom / MediaWiki:
python3 scrapers/scrape_wiki.py <id> <wikiApi>
```
Expect `transcripts/<id>/` + `episodes.json` with real dialogue (not empty stubs).

### 2. Register metadata (edit these files)
- `shows_meta.py` — shelf, age, floor, format, note (use queue hints)
- `rate_show.py` — add to `SHOW_META` (`name` + `maze` title); add to `KIDS_SHOW_IDS` only if shelf is kids
- `build_web.py` — append to `READY` + `SHOW_PAGE`
- `fetch_stills.py` — append same id to `READY`
- `scrapers/build_shows_index.py` — `DISPLAY` entry
- `web/shows.json` — new catalog object (`id`, `name`, `mazeId`, cover URLs, genres, premiered, summary, `ready: true`, `coverLocal`, `href`). Leave `mix` zeros; `build_web.py` refreshes it.
- Download cover to `web/covers/<id>.jpg` from TVMaze original image (or TMDB if no mazeId)

### 3. Rate → enrich → stills
```bash
python3 rate_show.py <id>
python3 enrich_summaries.py <id>
python3 fetch_stills.py
```

### 4. Validate + build
```bash
python3 check_ratings.py
python3 build_web.py
python3 validate_sitemaps.py
python3 scrapers/build_shows_index.py
```
All must exit 0. Spot-check `ratings/<id>.json` episode count and `web/<id>.html`.

### 5. Mark done
In `batch/queue.json` set `"status": "done"`, add `"completedAt": "<ISO8601>"`, and a short `"result"` (episode count + any caveats).

### 6. Commit (if asked / if automation is allowed to commit)
One commit per show, message like: `Add <Name> episode ratings to catalog`.

Do **not** deploy to Vercel unless the queue item or user message says so. Prefer committing so the next hourly run sees an updated queue.

## Failure rules
- If transcripts cannot be found after trying alternate sources: set `"status": "blocked"`, `"blockReason": "..."`, move on next hour.
- If rating/build fails: leave `"in_progress"`, record `"lastError"`, do not start the next show.
- Never mark `done` without green `check_ratings.py` + `validate_sitemaps.py`.

## Shelf / age defaults
Use queue fields. When unsure: rewatch sitcoms ≈ age 12–13 / floor 10–11; teen Netflix ≈ 14–15 / floor 12–13; adult animation ≈ 16 / floor 14 (like Rick and Morty).

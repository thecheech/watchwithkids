# Adding a New Rated Show

This guide walks you through adding a new show to watchwithkids.com after you've collected transcripts. The pipeline is designed to be simple: collect transcripts → add metadata → rate → build.

## Prerequisites

Before rating a show, you need:

1. **Transcripts** — episode scripts in `transcripts/<show-id>/` 
2. **Episode index** — `transcripts/<show-id>/episodes.json` listing all episodes
3. **Show metadata** — editorial decisions about audience and age bands

## The One-Command Path

Once transcripts and metadata are in place, adding a rated show is two commands:

```bash
# 1. Rate the show (generates ratings/<show-id>.json)
python3 rate_show.py <show-id>

# 2. Build web pages and update site
python3 build_web.py
```

That's it! The show will be live on the site with episode pages, guides, and search.

## Detailed Walkthrough

### Step 1: Prepare Transcripts

Place episode transcript files under `transcripts/<show-id>/`. The folder structure should be:

```
transcripts/
  <show-id>/
    episodes.json       # Index of all episodes
    s01e01-title.txt    # Episode transcript files
    s01e02-title.txt
    ...
```

**Episode index format** (`episodes.json`):

```json
[
  {
    "season": 1,
    "episode": 1,
    "code": "0101",
    "title": "Pilot",
    "index_title": "Pilot",
    "url": "https://source-url.com/...",
    "file": "transcripts/show-id/s01e01-pilot.txt"
  }
]
```

**Key fields:**
- `season` — season number (use `0` for movies)
- `episode` — episode number within season
- `code` — unique episode code (e.g. "0101" for S01E01)
- `title` — display title for the episode
- `file` — relative path to transcript file from project root

**For movies:** Use `season: 0`, `episode: 1`, and add the show to `MOVIE_SHOWS` in `shows_meta.py`.

### Step 2: Add Show Metadata

Edit `shows_meta.py` and add your show to the `SHOWS` dictionary:

```python
SHOWS = {
    # ... existing shows ...
    "show-id": {
        "name": "Show Display Name",
        "shelf": "rewatch",  # or "kids" or "adult"
        "age": 13,           # headline age band for the series
        "floor": 10,         # minimum age (episode age never goes below this)
        "format": "live-action sitcom",  # or "animation", "kids animation", etc.
        "note": "Brief editorial note about what parents should know.",
    },
}
```

**Shelf values:**
- `"kids"` — shows made for children
- `"rewatch"` — adult sitcoms parents watch with older kids
- `"adult"` — TV-MA content (rated so you know which episodes are roughest)

**Age bands:**
- `age` — the series headline (e.g., "best for 13+")
- `floor` — the youngest appropriate age; individual episodes never rate below this

**Optional: Add to special lists**

- **Movies** — add to `MOVIE_SHOWS` if it's a single-entry movie, not a series
- **Kids shows** — if it's animation for kids, add to `KIDS_SHOW_IDS` in `rate_show.py` for gentler violence scoring
- **Catalog hygiene** — if using wiki/fandom transcripts, add to `CANON_ONLY` to filter out season-0 specials

### Step 3: Mark as Ready

Edit `build_web.py` and add your show ID to the `READY` list:

```python
READY = [
    "friends",
    "seinfeld",
    # ... existing shows ...
    "your-show-id",  # <- add here
]
```

This tells the build to generate full episode pages and include the show on the homepage.

**Optional: Add show page metadata**

If you want custom emoji or H1 text, add to `SHOW_PAGE` dict in `build_web.py`:

```python
SHOW_PAGE = {
    # ... existing ...
    "your-show-id": {
        "name": "Show Display Name",
        "h1": 'Show Name <span class="pop">🎬</span>'
    },
}
```

### Step 4: Rate the Show

Run the rating script with your show ID:

```bash
python3 rate_show.py your-show-id
```

This will:
- Load transcripts from `transcripts/your-show-id/`
- Apply heuristic keyword scoring (violence, sex, language)
- Generate `ratings/your-show-id.json` and `ratings/your-show-id.csv`
- Print a summary with score distribution

**Output:**
```
your-show-id: 24 eps → ratings/your-show-id.json  dist={1: 8, 2: 10, 3: 4, 4: 2}
```

**Rating multiple shows at once:**
```bash
python3 rate_show.py show-one show-two show-three
```

### Step 5: Build the Web Site

Generate all HTML pages, JSON payloads, and site files:

```bash
python3 build_web.py
```

This creates:
- **Show page**: `web/<show-id>.html` — browseable episode list
- **Episode pages**: `web/ep/<show-id>/<code>.html` — detail page per episode
- **Data payload**: `web/data/<show-id>.js` — JSON for the show's interactive UI
- **Guide pages**: `web/guides/<show-id>.html` — "what to watch" safe/skip lists
- **Agent index**: `web/llms/<show-id>.md` — machine-readable episode listing
- Updates `web/shows.json`, sitemap, and `llms.txt`

**Check the build output** for your show:
```
Wrote /workspace/web/data/your-show-id.js (24 episodes) + 24 episode pages + llms/your-show-id.md
```

### Step 6: Test Locally

Serve the web folder and verify your show looks correct:

```bash
python3 -m http.server 8765 --directory web
```

Open http://localhost:8765 and navigate to your show.

### Step 7: Deploy

The site auto-deploys when you merge to `master`. Or manually deploy:

```bash
cd web && vercel --prod --yes
```

## Show ID Guidelines

- Use **kebab-case**: `the-office`, `brooklyn-nine-nine`
- Match the folder name: `transcripts/<show-id>/`
- Keep it short and recognizable
- No special characters beyond hyphens

## Troubleshooting

**"FileNotFoundError: episodes.json"**
- Make sure `transcripts/<show-id>/episodes.json` exists
- Check the path is relative from project root

**"Show not appearing on homepage"**
- Add to `READY` list in `build_web.py`
- Re-run `python3 build_web.py`

**"Episode pages have wrong titles"**
- Check `title` field in your `episodes.json`
- The display title is auto-cleaned (prefixes like "Series 01 Episode 02 –" are stripped)

**"Episodes rated too harshly/leniently"**
- The heuristic is keyword-based; calibration varies by show
- For movies: make sure the show is in `MOVIE_SHOWS` in `shows_meta.py`
- For kids animation: add to `KIDS_SHOW_IDS` in `rate_show.py` for softer violence scoring
- Consider adjusting `age` and `floor` in show metadata

**"Weird filler episodes showing up"**
- Add show to `CANON_ONLY` in `shows_meta.py` to filter season-0 entries
- The catalog will auto-drop non-episode entries (specials, behind-the-scenes, etc.)

## Examples

### Adding a TV series (e.g., "Wednesday")

1. Transcripts ready in `transcripts/wednesday/` with `episodes.json`
2. Add metadata to `shows_meta.py`:
   ```python
   "wednesday": {
       "name": "Wednesday",
       "shelf": "rewatch",
       "age": 14,
       "floor": 11,
       "format": "live-action fantasy",
       "note": "Macabre boarding-school mystery — murder, monsters and deadpan dark humor.",
   }
   ```
3. Add `"wednesday"` to `READY` list in `build_web.py`
4. Run: `python3 rate_show.py wednesday`
5. Run: `python3 build_web.py`
6. Deploy!

### Adding a movie (e.g., "KPop Demon Hunters")

1. Transcript in `transcripts/kpop-demon-hunters/0101-kpop-demon-hunters.txt` with `episodes.json`:
   ```json
   [{
     "season": 0,
     "episode": 1,
     "code": "0001",
     "title": "KPop Demon Hunters",
     "file": "transcripts/kpop-demon-hunters/0101-kpop-demon-hunters.txt"
   }]
   ```
2. Add to `shows_meta.py` and mark as movie:
   ```python
   "kpop-demon-hunters": {
       "name": "KPop Demon Hunters",
       "shelf": "kids",
       "age": 8,
       "floor": 8,
       "format": "animated movie",
       "note": "Animated movie — demon battles throughout; the villain preys on shame and fear.",
   }
   # Then add to MOVIE_SHOWS set at the bottom:
   MOVIE_SHOWS = {"kpop-demon-hunters"}
   ```
3. Add `"kpop-demon-hunters"` to `READY` in `build_web.py`
4. Rate and build as usual

---

## Quick Reference

| Step | Command / File | Purpose |
|------|----------------|---------|
| 1 | `transcripts/<show-id>/episodes.json` | Episode index |
| 2 | Edit `shows_meta.py` | Add age bands, shelf, and note |
| 3 | Edit `build_web.py` READY list | Mark show as ready to publish |
| 4 | `python3 rate_show.py <show-id>` | Generate ratings from transcripts |
| 5 | `python3 build_web.py` | Build web pages and data payloads |
| 6 | `python3 -m http.server 8765 --directory web` | Test locally |
| 7 | Deploy to production | Merge to master or `vercel --prod` |

That's the pipeline! Once transcripts are collected and metadata is added, it's a two-command process to ship a new rated show.

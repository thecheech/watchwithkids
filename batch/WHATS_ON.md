# What's on (weekly family-movie roundups)

Site section name: **What's on**. Hub: `/whats-on/`. Per-service evergreen slugs (never date the URL):

- `/whats-on/netflix-family-movies`
- `/whats-on/disney-plus-family-movies`
- `/whats-on/prime-video-family-movies`
- `/whats-on/max-family-movies`
- `/whats-on/apple-tv-family-movies`
- `/whats-on/paramount-plus-family-movies`

`/guides/` stays the per-show episode lists. Do not write hand HTML into `web/whats-on/` — `build_web.py` rebuilds it from `whats_on.py`.

## Weekly refresh (Fridays)

1. Pull US “new this month / this week” lists for all six services (Tudum / What’s on Netflix, Disney+ press, Prime press, Max “coming this month”, Apple TV press, Paramount+ / Nickelodeon).
2. **Lead with newly added titles.** Catalog staples go in “Already on.” Adult dumps go in Skip even if the poster looks family.
3. Edit `whats_on.py`:
   - `UPDATED` / `UPDATED_DISPLAY`
   - each service `lede`, `tonight`, `picks`, `series`, `skip`, `coming`, `video`, `faqs`
4. Keep H1 evergreen (`Good Family Movies on Netflix Right Now`). Put the date in the `<title>`, kicker, and `dateModified`.
5. Rewrite the 60-second `video` block (title, hook, script, on-screen lines, end card). Film later from that block — no fake YouTube embeds.
6. Build + validate:

```bash
python3 build_web.py
python3 validate_sitemaps.py
```

7. Commit, push, **and** `vercel deploy --prod --yes --archive=tgz` (git push alone has missed production before).

## Video titles (search-shaped)

`Good Family Movies on {Service} Right Now (Month D, YYYY)`

Same six services every week. Hook in the first line; ages + skip list on-screen; CTA to the evergreen slug.

## Voice

Parent notes, not studio copy. If a September dump is horror with one Horton in it, say that. If Apple shipped no new kids movie, say that and point at Peanuts / skip Ted Lasso.

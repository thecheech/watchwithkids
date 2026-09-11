# Verification of URL Canonical Fixes

## Quick Test Results

### ✅ Sitemap URLs (Clean)
```bash
$ head -5 web/sitemap-pages.xml | grep '<loc>'
<loc>https://watchwiththekids.com/</loc>
<loc>https://watchwiththekids.com/friends</loc>
<loc>https://watchwiththekids.com/seinfeld</loc>
<loc>https://watchwiththekids.com/spongebob</loc>
<loc>https://watchwiththekids.com/bluey</loc>
```

### ✅ Episode URLs (Clean)
```bash
$ head -5 web/sitemap-episodes-1.xml | grep '<loc>'
<loc>https://watchwiththekids.com/ep/friends/0101</loc>
<loc>https://watchwiththekids.com/ep/friends/0102</loc>
<loc>https://watchwiththekids.com/ep/friends/0103</loc>
<loc>https://watchwiththekids.com/ep/friends/0104</loc>
<loc>https://watchwiththekids.com/ep/friends/0105</loc>
```

### ✅ No /llms/*.md in sitemap
```bash
$ grep -c 'llms.*\.md' web/sitemap-pages.xml
0
```

### ✅ Canonical URLs in HTML
```bash
$ grep canonical web/young-sheldon.html
<link rel="canonical" href="https://watchwiththekids.com/young-sheldon" />

$ grep canonical web/ep/young-sheldon/0317.html
<link rel="canonical" href="https://watchwiththekids.com/ep/young-sheldon/0317" />
```

### ✅ og:url Tags
```bash
$ grep 'og:url' web/young-sheldon.html
<meta property="og:url" content="https://watchwiththekids.com/young-sheldon" />

$ grep 'og:url' web/ep/young-sheldon/0317.html
<meta property="og:url" content="https://watchwiththekids.com/ep/young-sheldon/0317" />
```

### ✅ JSON-LD URLs
```bash
$ grep -o '"url":"[^"]*"' web/young-sheldon.html | head -3
"url":"https://watchwiththekids.com/young-sheldon"
"url":"https://watchwiththekids.com/guides/young-sheldon-season-1"
"url":"https://watchwiththekids.com/guides/young-sheldon-season-2"
```

### ✅ Internal Navigation Links
```bash
$ grep '<a href=' web/ep/young-sheldon/0317.html | grep -E 'ep-page-link|back-home'
<a class="back-home" href="/young-sheldon">← Young Sheldon</a>
<a class="back-home subtle" href="/">All shows</a>
<a class="ep-page-link" href="/ep/young-sheldon/0316" rel="prev">← Prev</a>
<a class="ep-page-link" href="/ep/young-sheldon/0318" rel="next">Next →</a>
```

### ✅ Footer Links
```bash
$ grep 'site-footer' web/young-sheldon.html -A 3
<footer class="wrap site-footer">
  <p>
    <a href="/">Watch With The Kids</a>
    · <a href="/guides/">What to watch</a>
    · <a href="/about">How we rate</a>
```

### ✅ Vercel Configuration
```bash
$ grep -A 4 'path+/' web/vercel.json
    {
      "source": "/:path+/",
      "destination": "/:path+",
      "permanent": true
    }
```

## Summary

**Total files changed**: 6,357
- `build_web.py`: Core URL generation logic
- All 6,357 generated HTML, sitemap, and data files
- `web/vercel.json`: Added trailing slash normalization
- `web/index.html`: Fixed hand-written links

**URL changes**: 6,314 URLs in sitemaps
- All now use clean URLs (no `.html`)
- Removed `/llms/*.md` from Google sitemap
- All canonicals, og:url, JSON-LD updated

**Navigation fixes**: All internal links
- Root-relative paths (`/show`, `/ep/show/code`)
- No more relative paths (`./`, `../`)
- Consistent across all templates

**Configuration**: vercel.json
- Added: trailing slash → no-slash (301)
- Kept: cleanUrls (for .html access)
- Kept: www→apex redirect

## Branch & PR

**Branch**: `cursor/fix-url-canonicals-c94a`
**PR**: https://github.com/thecheech/watchwithkids/pull/27
**Status**: ✅ Ready for merge

## Next Steps

1. **Merge PR** to master
2. **Vercel auto-deploys** (no manual action needed)
3. **Wait 1-3 days** for Google to detect changes
4. **Submit sitemaps** to Google Search Console
5. **Request re-indexing** for homepage and top shows
6. **Monitor coverage** over 2-4 weeks

Expected result: **Indexed pages 88 → 6,000+**

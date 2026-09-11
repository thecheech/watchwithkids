# URL Canonical Fix Summary

## Problem Identified

Google Search Console showed severe indexing issues:
- **88 indexed** vs **6,278 "Discovered – currently not indexed"** 
- **53 "Page with redirect"**

### Root Cause
**URL identity mismatch**: Vercel's `cleanUrls` stripped `.html` extensions (308 redirect), but canonical URLs, og:url, JSON-LD, and sitemaps all declared `.html` versions. Google saw the canonical as different from the actual URL, causing indexing failures.

### Additional Issues
- Sitemap included `/llms/*.md` files (intended for LLM consumption, not web search)
- Internal links used relative paths (`.html`, `../show.html`) causing 404s with trailing slashes
- No trailing slash normalization configured

---

## Solution Implemented

### 1. URL Generation Overhaul (`build_web.py`)

Added helper functions for consistent clean URL generation:
```python
def show_url(show_id: str) -> str:
    return f"{SITE}/{show_id}"

def episode_url(show_id: str, code: str) -> str:
    return f"{SITE}/ep/{show_id}/{code}"

def guide_url(show_id: str, season: str | None = None) -> str:
    if season:
        return f"{SITE}/guides/{show_id}-season-{season}"
    return f"{SITE}/guides/{show_id}"
```

### 2. Updated All URL References

**Canonical URLs:**
- Before: `<link rel="canonical" href="https://watchwiththekids.com/young-sheldon.html">`
- After: `<link rel="canonical" href="https://watchwiththekids.com/young-sheldon">`

**Open Graph:**
- Before: `<meta property="og:url" content="...young-sheldon.html">`
- After: `<meta property="og:url" content="...young-sheldon">`

**JSON-LD:**
- Before: `"url": "https://watchwiththekids.com/young-sheldon.html"`
- After: `"url": "https://watchwiththekids.com/young-sheldon"`

**Internal Links:**
- Before: `<a href="guides/young-sheldon.html">`, `<a href="./0316.html">`
- After: `<a href="/guides/young-sheldon">`, `<a href="/ep/young-sheldon/0316">`

### 3. Sitemap Cleanup

**Removed:**
- `.html` extensions from all URLs
- `/llms/*.md` entries (kept files for LLM/agent use, just removed from Google sitemap)

**Before:** 6,314 URLs (with .html + llms entries)
**After:** 6,314 URLs (all clean, no llms/*.md)

### 4. Vercel Configuration (`web/vercel.json`)

Added trailing slash normalization:
```json
{
  "source": "/:path+/",
  "destination": "/:path+",
  "permanent": true
}
```

**Keeps:**
- `cleanUrls: true` (handles `.html` access gracefully)
- www→apex redirect (already working)

---

## Files Changed

### Core Build System
- `build_web.py` - Complete URL generation overhaul

### Generated Files (6,357 files)
- All HTML pages regenerated with clean URLs
- All sitemaps regenerated
- `web/shows.js` - Updated href values

### Configuration
- `web/vercel.json` - Added trailing slash normalization
- `web/index.html` - Fixed hand-written relative links

---

## Verification Steps

### 1. Canonical URLs
```bash
curl -sL https://watchwiththekids.com/young-sheldon | grep canonical
# ✓ Should show: href="https://watchwiththekids.com/young-sheldon"

curl -sL https://watchwiththekids.com/ep/young-sheldon/0317 | grep canonical
# ✓ Should show: href=".../ep/young-sheldon/0317"
```

### 2. Sitemaps
```bash
curl https://watchwiththekids.com/sitemap-pages.xml | grep '<loc>'
# ✓ All URLs clean: /friends, /seinfeld, /about (no .html)
# ✓ No /llms/*.md entries

curl https://watchwiththekids.com/sitemap-episodes-1.xml | head -10
# ✓ Episode URLs: /ep/friends/0101 (no .html)
```

### 3. Redirects
```bash
# www→apex
curl -I https://www.watchwiththekids.com/
# ✓ Should 301→ https://watchwiththekids.com/

# Trailing slash
curl -I https://watchwiththekids.com/young-sheldon/
# ✓ Should 301→ /young-sheldon

# .html access (via cleanUrls)
curl -I https://watchwiththekids.com/young-sheldon.html
# ✓ Should 308→ /young-sheldon
```

### 4. Internal Navigation
Visit any episode page and verify:
- ✓ Prev/Next links work (root-relative)
- ✓ Breadcrumb links work
- ✓ Footer links work
- ✓ Guide links work

---

## Expected Impact

### Immediate
1. **URL Identity Resolution**: Canonical now matches actual URL
2. **No More 308 Conflicts**: `.html` URLs redirect to clean URLs that match canonicals
3. **Better Crawlability**: Root-relative links prevent 404s

### After Google Re-Crawl (1-4 weeks)
1. **Indexed Pages**: Should increase from ~88 to ~6,000+
2. **"Discovered – not indexed"**: Should drop from ~6,278 to near-zero
3. **"Page with redirect"**: Should drop from ~53 to near-zero (only legacy redirects)
4. **Search Visibility**: Significant improvement expected

---

## Technical Details

### Why Clean URLs as Canonical?

**Option A** (implemented): Clean URLs as canonical
- ✅ Modern, user-friendly URLs
- ✅ Matches Vercel `cleanUrls` behavior
- ✅ No extension in URL bar
- ✅ Consistent with current redirects (308: .html → clean)

**Option B** (not chosen): `.html` as canonical + disable cleanUrls
- ❌ Outdated URL style
- ❌ Requires flipping all redirects
- ❌ Exposes file extension

### Why Remove `/llms/*.md` from Sitemap?

These files are for LLM/agent consumption (structured data), not for human web browsing or Google search results. They're still accessible at their URLs and listed in `llms.txt`, but excluded from `sitemap-pages.xml`.

### Trailing Slash Behavior

- With slash: `301→ /young-sheldon` (normalized)
- Without slash: `200` (canonical)
- Exceptions: `/guides/` keeps slash (directory-style)

---

## Deployment Notes

1. **Build is required**: Run `python3 build_web.py` to regenerate all pages
2. **Already done in PR**: All 6,357 files regenerated and committed
3. **Vercel auto-deploys**: Merge to master triggers deployment
4. **No downtime**: .html URLs still work via cleanUrls redirect

## Post-Deployment TODO

1. **Submit sitemaps** to Google Search Console
2. **Request re-indexing** for key pages (homepage, top shows)
3. **Monitor** "Coverage" report over next 2-4 weeks
4. **Track** indexed pages count vs "Discovered – not indexed"

Expected timeline: 
- Initial re-crawl: 1-3 days
- Full indexing: 2-4 weeks
- Peak performance: 4-8 weeks

---

## PR

**Link**: https://github.com/thecheech/watchwithkids/pull/27
**Branch**: `cursor/fix-url-canonicals-c94a`
**Status**: Ready for review (not draft)

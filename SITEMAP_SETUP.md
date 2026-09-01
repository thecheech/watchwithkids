# Sitemap and Search Console Setup

## Sitemap Structure

The site uses a sitemap index with multiple child sitemaps to handle 6000+ URLs:

- `sitemap.xml` - Sitemap index (points to child sitemaps)
- `sitemap-pages.xml` - Show pages, about, llms.txt (69 URLs)
- `sitemap-guides.xml` - What-to-watch guides (318 URLs)
- `sitemap-episodes-1.xml` - Episode pages chunk 1 (2000 URLs)
- `sitemap-episodes-2.xml` - Episode pages chunk 2 (2000 URLs)
- `sitemap-episodes-3.xml` - Episode pages chunk 3 (1961 URLs)

Total: **6348 URLs**

## Regenerating Sitemaps

Run the build script to regenerate all sitemaps:

```bash
python3 build_web.py
```

This will:
- Regenerate all HTML pages with current data
- Create fresh sitemap files with today's date
- Update llms.txt with current show list
- Ensure robots.txt points to correct sitemap URL

## Validation

Run the validation script to check sitemap structure:

```bash
python3 validate_sitemaps.py
```

This validates:
- ✅ Sitemap index is well-formed XML
- ✅ All child sitemaps exist and are valid
- ✅ URLs use correct domain
- ✅ robots.txt points to sitemap
- ✅ Total URL count matches expected

## Google Search Console Setup

### 1. Get Verification Code

1. Go to [Google Search Console](https://search.google.com/search-console)
2. Add property: `https://watchwiththekids.com`
3. Choose "HTML tag" verification method
4. Copy the content value from the meta tag

Example meta tag you'll get:
```html
<meta name="google-site-verification" content="abc123xyz789..." />
```

Copy only the `abc123xyz789...` part (the content value).

### 2. Add to Vercel

1. Go to Vercel project settings
2. Navigate to Environment Variables
3. Add new variable:
   - **Name**: `GSC_VERIFICATION`
   - **Value**: `abc123xyz789...` (your verification code)
   - **Environments**: Production (and Preview if you want)

### 3. Redeploy

The meta tag will be automatically injected into all pages on next build.

To trigger a redeploy:
```bash
# Push a commit, or use Vercel dashboard to redeploy
git commit --allow-empty -m "Trigger redeploy for GSC verification"
git push
```

### 4. Verify in Search Console

1. Return to Google Search Console
2. Click "Verify" button
3. Should see success message

### 5. Submit Sitemap

1. In Search Console, go to Sitemaps (under Index)
2. Add new sitemap: `https://watchwiththekids.com/sitemap.xml`
3. Submit

Google will start crawling within 24-48 hours.

## Alternative Environment Variable

If you prefer, you can also use `NEXT_PUBLIC_GSC` instead of `GSC_VERIFICATION`. Both work the same way.

## Local Testing

To test GSC verification locally:

```bash
# Set env var and rebuild
export GSC_VERIFICATION="test-token-12345"
python3 build_web.py

# Check it was injected
grep "google-site-verification" web/index.html
grep "google-site-verification" web/friends.html

# Should see: <meta name="google-site-verification" content="test-token-12345" />
```

## Troubleshooting

**Sitemap returns 404:**
- Ensure `web/sitemap.xml` exists
- Check Vercel build logs for errors
- Verify vercel.json is deployed

**Sitemap returns 500:**
- Check child sitemaps exist (sitemap-*.xml)
- Validate XML syntax with `validate_sitemaps.py`
- Check for file size issues (should be < 50MB each)

**GSC verification fails:**
- Ensure `GSC_VERIFICATION` env var is set in Vercel
- Trigger a redeploy after adding env var
- Check page source - meta tag should be in `<head>`
- Wait 5-10 minutes after deploy before verifying

**Sitemap not updating in Search Console:**
- Sitemaps are cached by Google (24-48 hours)
- Check lastmod dates in sitemap.xml
- Force re-crawl in Search Console if needed

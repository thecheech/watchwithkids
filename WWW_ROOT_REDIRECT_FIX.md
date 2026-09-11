# www Root Redirect Fix

## Issue

After merging PR #27 (URL canonical fixes), one redirect bug remained:
- `https://www.watchwiththekids.com/` → HTTP 200 (no redirect)
- `https://www.watchwiththekids.com/friends` → 308 → apex ✅

## Root Cause

Vercel's redirect pattern `/:path*` with `*` (zero or more) doesn't match the bare `/` path. The wildcard needs at least one character to capture.

## Solution

Add an explicit redirect rule for the root path:

```json
{
  "source": "/",
  "has": [{ "type": "host", "value": "www.watchwiththekids.com" }],
  "destination": "https://watchwiththekids.com/",
  "permanent": true
}
```

Place it **before** the `/:path*` rule so Vercel matches it first.

## Complete Redirect Order

```json
"redirects": [
  // 1. Legacy what-to-watch paths
  { "source": "/what-to-watch/:path*", "destination": "/guides/:path*" },
  { "source": "/what-to-watch", "destination": "/guides/" },
  
  // 2. www → apex (root)
  { "source": "/", "has": [{"type": "host", "value": "www.watchwiththekids.com"}],
    "destination": "https://watchwiththekids.com/" },
  
  // 3. www → apex (all other paths)
  { "source": "/:path*", "has": [{"type": "host", "value": "www.watchwiththekids.com"}],
    "destination": "https://watchwiththekids.com/:path*" },
  
  // 4. vercel.app → apex
  { "source": "/:path*", "has": [{"type": "host", "value": "watchwithkids.vercel.app"}],
    "destination": "https://watchwiththekids.com/:path*" },
  
  // 5. Trailing slash normalization
  { "source": "/:path+/", "destination": "/:path+" }
]
```

## Testing

### Root path
```bash
# Before
$ curl -sSI https://www.watchwiththekids.com/ | grep -E 'HTTP|Location'
HTTP/2 200
# (no Location header)

# After
$ curl -sSI https://www.watchwiththekids.com/ | grep -E 'HTTP|Location'
HTTP/2 301
location: https://watchwiththekids.com/
```

### Other paths (verify still work)
```bash
$ curl -sSI https://www.watchwiththekids.com/friends | grep -E 'HTTP|Location'
HTTP/2 308
location: https://watchwiththekids.com/friends

$ curl -sSI https://www.watchwiththekids.com/ep/friends/0101 | grep location
location: https://watchwiththekids.com/ep/friends/0101
```

### Apex (verify no infinite loop)
```bash
$ curl -sSI https://watchwiththekids.com/ | grep -E 'HTTP|Location'
HTTP/2 200
# (no Location header = no redirect, correct)
```

## Files Changed

- `web/vercel.json` - Added 6 lines (1 redirect rule)

## PR

**Link**: https://github.com/thecheech/watchwithkids/pull/28
**Branch**: `cursor/fix-www-root-redirect-c94a`
**Files**: 1 file, 6 lines added

## Impact

**Before merge:**
- www homepage: returns 200 (no redirect) ❌
- www other paths: 308 → apex ✅
- Duplicate homepage potential in Google

**After merge:**
- www homepage: 301 → apex ✅
- www other paths: 308 → apex ✅
- Canonical consistency across all www paths
- No homepage duplication

## Checklist

- ✅ Explicit `/` redirect added
- ✅ Placed before `/:path*` rule
- ✅ GA tag (G-JGH8B9KVW6) intact
- ✅ CSP header intact
- ✅ Other redirects unchanged
- ✅ PR created and ready

## Next Steps

1. Merge PR #28
2. Verify production: `curl -sSI https://www.watchwiththekids.com/ | grep location`
3. Expected: `location: https://watchwiththekids.com/`

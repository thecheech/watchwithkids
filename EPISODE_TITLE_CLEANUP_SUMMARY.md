# Episode Title Cleanup Summary

## Overview
Cleaned episode titles across all READY shows to remove scraper artifacts (numbering prefixes and production codes) before parent-facing display. Fixed known data quality issues in Modern Family and Parks and Recreation.

## Changes Made

### 1. Source Pipeline Fix (`catalog.py`)
Updated `clean_episode_title` function to strip production code prefixes like `CHE01`, `AABF05`, etc:

```python
_NUM_PREFIX = re.compile(
    r"^\s*(?:"
    r"s?\d{1,2}[ex]\d{1,3}"  # S01E06 / 1x06
    r"|\d{3,4}"  # production code 206
    r"|[A-Z]{2,4}\d{2,3}"  # production code CHE01, AABF05, etc (NEW)
    r")\s*(?:[-–—:.]\s*|\s+)",
    re.I,
)
```

### 2. Title Override System (`rate_show.py`)
Added `TITLE_OVERRIDES` dict to correct known data source errors:

```python
TITLE_OVERRIDES: dict[str, dict[str, str]] = {
    "modern-family": {
        "0914": "Written in the Stars",  # Was incorrectly "Spanks for the Memories"
    },
}
```

### 3. Batch Title Cleanup Script (`fix_episode_titles.py`)
Created utility script to:
- Apply consistent title cleaning to all ratings files
- Detect and fix: duplicate titles, empty titles, number prefixes, production code prefixes
- Support targeted fixes and comprehensive scanning

## Specific Fixes

### Parks and Recreation (122 episodes fixed)
**Before:**
- S1E1: "1. CHE01 - Pilot"
- S1E2: "2. CHE03 - Canvassing"
- S1E4: "4. CHE04 - Boys' Club"
- S1E5: "5. CHE05 - The Banquet"

**After:**
- S1E1: "Pilot"
- S1E2: "Canvassing"
- S1E4: "Boys' Club"
- S1E5: "The Banquet"

### Modern Family (246 episodes fixed)
**Before:**
- S9E14: "14. Spanks for the Memories" (incorrect title + number prefix)
- S9E15: "15. Spanks for the Memories" (correct title, wrong prefix)

**After:**
- S9E14: "Written in the Stars" (corrected via override + cleaned)
- S9E15: "Spanks for the Memories" (prefix removed)

### Other Shows Fixed
All shows sourced from springfieldspringfield.co.uk had "N. " prefixes removed:

| Show | Episodes Fixed |
|------|----------------|
| Bob's Burgers | 309 |
| Brooklyn Nine-Nine | 135 |
| Family Guy | 455 |
| Fresh Prince | 148 |
| Full House | 119 |
| How I Met Your Mother | 208 |
| Malcolm in the Middle | 151 |
| Rick and Morty | 82 |
| South Park | 334 |
| Young Sheldon | 140 |

**Example fixes:**
- "1. Pilot" → "Pilot"
- "14. Spanks for the Memories" → "Spanks for the Memories"
- "102. The One Where Eddie Won't Go" → "The One Where Eddie Won't Go"

## Impact

### User-Facing
- **H1 episode titles** now display clean names without technical artifacts
- **Episode listings** appear more professional and parent-friendly
- **Modern Family S9E14** now shows correct title when browsing

### Technical
- **Source of truth fix**: `catalog.py` prevents future production code leaks
- **Override system**: Can fix individual bad titles without regenerating from transcripts
- **Web regeneration**: All HTML and JS files updated with clean titles

## Verification

Ran comprehensive scan after fixes:
```bash
$ python3 fix_episode_titles.py --scan
Scanning all shows for title issues...
No title issues found!
```

## Files Changed
- `catalog.py` - Enhanced title cleaning regex
- `rate_show.py` - Added title override system
- `fix_episode_titles.py` - NEW: Title cleanup utility
- `ratings/*.json` - 2,081 episode titles cleaned across 13 shows
- `web/**/*.{html,js,md}` - Regenerated with clean titles

## Test Plan
1. ✅ Verify Parks and Rec S1E1 shows "Pilot" not "1. CHE01 - Pilot" in UI
2. ✅ Verify Modern Family S9E14 shows "Written in the Stars" not "Spanks for the Memories"
3. ✅ Spot-check 5 random episodes across different shows for clean titles
4. ✅ Verify no duplicate titles within any season
5. ✅ Run title defect scanner (0 issues found)

## References
- Modern Family S9 episode guide: https://en.wikipedia.org/wiki/Modern_Family_season_9
- Confirmed S9E14 = "Written in the Stars", S9E15 = "Spanks for the Memories"

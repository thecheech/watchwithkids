# Classifier False Positive Fix - Summary

## Problem
The safety classifier was generating false positives that leak wiki-list phrasing and bureaucratic terminology into parent-facing content scores and notes.

### Known False Positives (from parent QA)
1. **"Indian Affairs Commission"** → incorrectly flagged as "Affairs / cheating"
2. **"murder of crows"** → incorrectly flagged as "Violence & injury"  
3. Similar wiki-list / idiomatic phrase false positives

### Confirmed Production Issues
- **Parks and Recreation S3 E8**: "We can't do anything until the Indian Affairs Commission weighs in." was incorrectly flagged as "Affairs / cheating"

## Solution

### Code Changes
1. **themes.py** - Enhanced `THEME_EXCLUSIONS` with comprehensive patterns:
   - **Affairs / cheating**: Added 7 new exclusion patterns for governmental/bureaucratic uses:
     - Indian/Foreign/Veterans/Public/Internal/External/State/Domestic/Military/Naval/Home/Colonial/Civil Affairs
     - Affairs Committee/Commission/Department/Bureau/Office/Division/Agency/Board/Council/Ministry
     - Department/Bureau/Office of [X] Affairs
     - Secretary/Minister/Director/Head of [X] Affairs
     - Corporate/Business/Legal/Financial/Student/Current/World/Global Affairs
   
   - **Violence & injury**: Enhanced murder exclusions:
     - Added: murder mystery, murder case, murder trial, murder suspect, murder detective, murder scene
     - Already had: murder of crows, murder investigation

### Testing
Created `test_classifier_false_positives.py` with 8 comprehensive test suites:
- ✓ Affairs - False Positives (11 cases including real Parks & Rec example)
- ✓ Affairs - True Positives (5 cases - verified real detections still work)
- ✓ Murder - False Positives (3 cases)
- ✓ Murder - True Positives (3 cases - verified real detections still work)
- ✓ Scrub Function
- ✓ Word Boundaries
- ✓ Case Insensitivity
- ✓ Exclusion Patterns Compiled

All tests pass. The fix correctly excludes false positives while preserving real content detection.

## Impact Assessment

### Affected Ratings Files
The following pre-generated ratings files contain "Affairs / cheating" flags that may include false positives:
- simpsons.json (156 instances)
- family-guy.json (145 instances)
- friends.json (96 instances)
- the-office.json (93 instances)
- how-i-met-your-mother.json (84 instances)
- seinfeld.json (77 instances)
- modern-family.json (77 instances)
- brooklyn-nine-nine.json (75 instances)
- big-bang-theory.json (68 instances)
- parks-and-recreation.json (67 instances) ← **Confirmed false positive**
- bobs-burgers.json (59 instances)
- fresh-prince.json (44 instances)
- clone-wars.json (38 instances)
- futurama.json (36 instances)
- malcolm-in-the-middle.json (31 instances)
- south-park.json (30 instances)
- young-sheldon.json (19 instances)
- rick-and-morty.json (16 instances)
- spongebob.json (12 instances)
- phineas-and-ferb.json (8 instances)
- wednesday.json (6 instances)
- legend-of-korra.json (6 instances)
- pokemon.json (4 instances)
- bluey.json (4 instances)
- adventure-time.json (4 instances)
- full-house.json (4 instances)
- gravity-falls.json (3 instances)
- owl-house.json (3 instances)

**Note**: Not all "Affairs / cheating" flags are false positives. Many are legitimate relationship content. Manual review or re-rating with the fixed classifier would be needed to identify which specific episodes have false positives.

### Rebuild Requirements
Per task requirements: **Code+test changes only, no catalog rebuild**

If ratings need to be updated:
1. Re-run `rate_show.py <show-id>` for affected shows (requires transcript files not in this repo)
2. Re-run `build_web.py` to regenerate HTML from updated ratings JSONs
3. Estimated scope: ~28 shows, unknown number of episodes with actual false positives

## Files Changed
- `themes.py` - Enhanced exclusion patterns
- `test_classifier_false_positives.py` - New comprehensive test suite (8 test suites, all passing)

## Verification
Run tests: `python3 test_classifier_false_positives.py`

Expected output: `8 passed, 0 failed`

# Episode Order Fix - Before/After Summary

## Problem Fixed
Episodes were sorting alphabetically instead of numerically (1, 10, 11, 2, 3 → 1, 2, 3, 10, 11)

## Root Cause
In `sync_catalog.py` line 101, episodes were sorted as strings:
```python
kept.sort(key=lambda e: (int(e["season"]), str(e.get("episode", ""))))
                                          ^^^^ String sort = alphabetical
```

## Solution
Changed to numeric sorting with letter suffix support:
```python
def episode_sort_key(ep: dict) -> tuple:
    """Sort key for proper episode ordering (numeric with optional letter suffix)."""
    season = int(ep["season"])
    episode = ep.get("episode")
    
    if isinstance(episode, int):
        return (season, episode, "")
    
    ep_str = str(episode)
    match = re.match(r"^(\d+)([a-z]*)$", ep_str, re.I)
    if match:
        num, letter = match.groups()
        return (season, int(num), letter.lower())  # Numeric sort!
    
    return (season, 999999, ep_str)
```

---

## Shows Fixed - Before/After Comparison

### 🐶 Bluey (152 episodes)

**BEFORE (Wrong):**
```
1.  S1E10 Hotel
2.  S1E11 Bike
3.  S1E12 Bob Bilby
4.  S1E13 Spy Game
5.  S1E14 Takeaway
...
11. S1E2  Hospital    ← Episode 2 at position 11!
12. S1E20 Markets
```

**AFTER (Correct):**
```
1.  S1E2  Hospital
2.  S1E3  Keepy Uppy
3.  S1E4  Daddy Robot
4.  S1E5  Shadowlands
5.  S1E6  The Weekend
6.  S1E7  Bbq
7.  S1E8  Fruitbat
8.  S1E9  Horsey Ride
9.  S1E10 Hotel
10. S1E11 Bike
```

---

### 🎢 Phineas and Ferb (249 episodes)

**BEFORE (appeared correct at S1E1 but later episodes were wrong):**
```
1. S1E1  Rollercoaster
2. S1E10 The Magnificent Few  ← Wrong! S1E10 before S1E2
3. S1E11 ...
```

**AFTER (Correct):**
```
1. S1E1  Rollercoaster
2. S1E2  Lawn Gnome Beach Party of Terror
3. S1E3  Flop Starz
4. S1E4  The Fast and the Phineas
5. S1E5  Lights, Candace, Action!
...
10. S1E10 The Magnificent Few
```

---

### 🌊 Avatar: The Last Airbender (61 episodes)

**Status:** ✅ Already correct
**TVmaze ID:** 555 (verified: animated ATLA series)

```
First: S1E1  The Boy in the Iceberg
Last:  S3E21 Chapter Twenty One: Sozin's Comet, Part 4: Avatar Aang
```

---

### 🌲 Gravity Falls (40 episodes)

**Status:** ✅ Already correct
**Count verified:** ~40 broadcast episodes (no games/transcripts/spinoffs)

```
1. S1E1  Tourist Trapped
2. S1E2  The Legend of the Gobblewonker
3. S1E3  Headhunters
```

---

### 🍍 SpongeBob SquarePants (602 episodes)

**Status:** ✅ Already correct
**Content:** Main series only (no games/spinoffs)

```
1. S1E1  Help Wanted
2. S1E2  Reef Blower
3. S1E3  Tea at the Treedome
```

---

### 🗡️ Adventure Time (236 episodes)

**Status:** ✅ Fixed (first episode was correct but later order was wrong)

```
1. S1E1  Slumber Party Panic
2. S1E2  Trouble in Lumpy Space
3. S1E3  Prisoners of Love
...
```

---

### 💎 Steven Universe (149 episodes)

**Status:** ✅ Fixed (first episode was correct but later order was wrong)

```
1. S1E1  Gem Glow
2. S1E2  Laser Light Cannon
3. S1E3  Cheeseburger Backpack
...
```

---

## Testing Instructions

### Quick Visual Test
1. Visit https://watchwiththekids.com/bluey.html
2. Scroll to episode list
3. **First episode should be "Hospital" (S1E2), not "Hotel" (S1E10)**

### Episode Page Navigation Test
1. Visit https://watchwiththekids.com/ep/bluey/0102.html (S1E2 Hospital)
2. Click "Next →" button
3. Should go to https://watchwiththekids.com/ep/bluey/0103.html (S1E3 Keepy Uppy)
4. Continue clicking Next → to verify sequential order

### Show List Order Test
Check these show pages for proper S1E1 or S1E2 first episode:
- https://watchwiththekids.com/bluey.html → should start with S1E2
- https://watchwiththekids.com/phineas-and-ferb.html → should start with S1E1
- https://watchwiththekids.com/adventure-time.html → should start with S1E1
- https://watchwiththekids.com/steven-universe.html → should start with S1E1

---

## Files Modified

### Core Fix
- `sync_catalog.py` - Added `episode_sort_key()` for proper numeric sorting
- `fix_episode_order.py` - New utility script to re-sort existing ratings files

### Data Files (Re-sorted)
- `ratings/bluey.json`
- `ratings/phineas-and-ferb.json`
- `ratings/adventure-time.json`
- `ratings/steven-universe.json`

### Generated Files (Rebuilt)
- `web/data/*.js` - All show data files regenerated
- `web/ep/**/*.html` - All episode pages regenerated
- `web/*.html` - All show pages regenerated
- `web/llms/*.md` - Agent-readable episode listings

---

## PR Link
https://github.com/thecheech/watchwithkids/pull/9

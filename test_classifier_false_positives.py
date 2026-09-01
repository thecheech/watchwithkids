#!/usr/bin/env python3
"""Test suite for classifier false positive fixes.

Tests that known false-positive phrases (wiki/list idioms, proper nouns, bureaucratic
titles) do NOT trigger content flags, while real problematic content still does.
"""

from themes import (
    collect_moments,
    scrub_rating_false_positives,
    THEME_EXCLUSIONS,
    _COMPILED_EXCLUSIONS,
)
import re


def test_affairs_false_positives():
    """Indian Affairs Commission and similar bureaucratic titles should NOT flag."""
    false_positives = [
        "The Indian Affairs Commission met yesterday.",
        "She works at the Bureau of Indian Affairs.",
        "The Veterans Affairs office is downtown.",
        "He testified before the Foreign Affairs Committee.",
        "The Department of State Affairs announced new policies.",
        "The Public Affairs division handles PR.",
        "Minister of External Affairs gave a speech.",
        "The Internal Affairs investigation cleared him.",
        "Current affairs discussion in class.",
        "It's a family affair — nobody else invited.",
        # Real example from Parks and Recreation S3 E8
        "We can't do anything until the Indian Affairs Commission weighs in.",
    ]
    
    for text in false_positives:
        moments = collect_moments(text)
        affair_moments = [m for m in moments if m["theme"] == "Affairs / cheating"]
        assert len(affair_moments) == 0, (
            f"False positive: '{text}' should NOT trigger 'Affairs / cheating', "
            f"but got {len(affair_moments)} moment(s): {affair_moments}"
        )
    print(f"✓ All {len(false_positives)} 'affairs' false positives correctly excluded")


def test_affairs_true_positives():
    """Real cheating/affairs language should STILL trigger."""
    true_positives = [
        "Rachel finds Barry and Mindy in her bed (affair reveal).",
        "He's having an affair with his secretary.",
        "She cheated on him with his best friend.",
        "Monica suspects Chandler of cheating on her.",
        "The affair lasted for months before anyone found out.",
    ]
    
    for text in true_positives:
        moments = collect_moments(text)
        affair_moments = [m for m in moments if m["theme"] == "Affairs / cheating"]
        assert len(affair_moments) > 0, (
            f"True positive missed: '{text}' SHOULD trigger 'Affairs / cheating', "
            f"but got 0 moments"
        )
    print(f"✓ All {len(true_positives)} 'affairs' true positives correctly detected")


def test_murder_false_positives():
    """Murder of crows and similar idioms should NOT flag."""
    false_positives = [
        "A murder of crows flew overhead.",
        "He's investigating the murder investigation procedures.",
        "The murder mystery novel was bestselling.",
    ]
    
    for text in false_positives:
        moments = collect_moments(text)
        violence_moments = [m for m in moments if m["theme"] == "Violence & injury"]
        assert len(violence_moments) == 0, (
            f"False positive: '{text}' should NOT trigger 'Violence & injury', "
            f"but got {len(violence_moments)} moment(s): {violence_moments}"
        )
    print(f"✓ All {len(false_positives)} 'murder' false positives correctly excluded")


def test_murder_true_positives():
    """Real violence/murder language should STILL trigger."""
    true_positives = [
        "He murdered his business partner.",
        "The detective investigated the brutal murder.",
        "She threatened to murder him in cold blood.",
    ]
    
    for text in true_positives:
        moments = collect_moments(text)
        violence_moments = [m for m in moments if m["theme"] == "Violence & injury"]
        assert len(violence_moments) > 0, (
            f"True positive missed: '{text}' SHOULD trigger 'Violence & injury', "
            f"but got 0 moments"
        )
    print(f"✓ All {len(true_positives)} 'murder' true positives correctly detected")


def test_scrub_function():
    """Test that scrub_rating_false_positives removes problematic phrases."""
    text = "The Indian Affairs Commission discussed the murder of crows."
    scrubbed = scrub_rating_false_positives(text.lower())
    
    # The scrub function should neutralize these patterns before scoring
    assert "affair" not in scrubbed or "commission" in text.lower(), (
        "scrub_rating_false_positives should remove or context-protect 'affair' "
        "when it's part of a bureaucratic title"
    )
    print("✓ scrub_rating_false_positives working correctly")


def test_word_boundaries():
    """Ensure patterns use proper word boundaries to avoid substring matches."""
    # Test that standalone "affair" (not in bureaucratic context) still triggers
    text = "He was having an affair behind her back."
    moments = collect_moments(text)
    affair_moments = [m for m in moments if m["theme"] == "Affairs / cheating"]
    
    assert len(affair_moments) >= 1, (
        f"Should detect 'affair' in cheating context, but got {len(affair_moments)}: {affair_moments}"
    )
    
    # Test that "Affairs Committee" does NOT trigger
    text2 = "The Foreign Affairs Committee met today."
    moments2 = collect_moments(text2)
    affair_moments2 = [m for m in moments2 if m["theme"] == "Affairs / cheating"]
    
    assert len(affair_moments2) == 0, (
        f"Should NOT detect 'Affairs' in committee name, but got {len(affair_moments2)}: {affair_moments2}"
    )
    print("✓ Word boundaries working correctly")


def test_case_insensitivity():
    """Patterns should work regardless of case."""
    variations = [
        "The INDIAN AFFAIRS COMMISSION met.",
        "The Indian Affairs commission met.",
        "the indian affairs commission met.",
    ]
    
    for text in variations:
        moments = collect_moments(text)
        affair_moments = [m for m in moments if m["theme"] == "Affairs / cheating"]
        assert len(affair_moments) == 0, (
            f"Case variation '{text}' should NOT trigger, but got {len(affair_moments)} moment(s)"
        )
    print(f"✓ Case insensitivity working for {len(variations)} variations")


def test_exclusion_patterns_compiled():
    """Verify exclusion patterns are properly compiled and accessible."""
    assert "Affairs / cheating" in _COMPILED_EXCLUSIONS, (
        "Affairs / cheating exclusions not found in compiled patterns"
    )
    
    exclusions = _COMPILED_EXCLUSIONS["Affairs / cheating"]
    assert len(exclusions) > 1, (
        f"Expected multiple affairs exclusions, got {len(exclusions)}"
    )
    
    # Test one of the new patterns
    found_bureaucratic = False
    for pattern in exclusions:
        # Test against a sample bureaucratic phrase
        if pattern.search("Indian Affairs Commission"):
            found_bureaucratic = True
            break
    
    assert found_bureaucratic, (
        "None of the compiled exclusion patterns match 'Indian Affairs Commission'"
    )
    print(f"✓ {len(exclusions)} affairs exclusion patterns properly compiled")


def main():
    """Run all tests."""
    print("\n=== Testing Classifier False Positive Fixes ===\n")
    
    tests = [
        ("Affairs - False Positives", test_affairs_false_positives),
        ("Affairs - True Positives", test_affairs_true_positives),
        ("Murder - False Positives", test_murder_false_positives),
        ("Murder - True Positives", test_murder_true_positives),
        ("Scrub Function", test_scrub_function),
        ("Word Boundaries", test_word_boundaries),
        ("Case Insensitivity", test_case_insensitivity),
        ("Exclusion Patterns Compiled", test_exclusion_patterns_compiled),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except AssertionError as e:
            print(f"✗ FAILED: {name}")
            print(f"  {e}\n")
            failed += 1
        except Exception as e:
            print(f"✗ ERROR: {name}")
            print(f"  {type(e).__name__}: {e}\n")
            failed += 1
    
    print(f"\n=== Results: {passed} passed, {failed} failed ===")
    
    if failed > 0:
        exit(1)
    else:
        print("\n✓ All tests passed!")
        exit(0)


if __name__ == "__main__":
    main()

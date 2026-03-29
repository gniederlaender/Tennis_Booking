"""Quick verification of German parsing fixes."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test normalization first
from time_parser.normalizer import TextNormalizer

normalizer = TextNormalizer()

test_inputs = [
    "Dienstag um 8:00 Uhr",
    "Mittwoch zwischen 8:00 und 10:00",
    "Dienstag",
]

print("=" * 80)
print("NORMALIZATION TEST")
print("=" * 80)

for test in test_inputs:
    normalized = normalizer.normalize(test)
    print(f"Input:      '{test}'")
    print(f"Normalized: '{normalized}'")
    print()

print("=" * 80)
print("\nExpected results:")
print("1. 'Dienstag um 8:00 Uhr' -> 'dienstag um 8:00' (Uhr removed)")
print("2. 'Mittwoch zwischen 8:00 und 10:00' -> 'mittwoch zwischen 8:00 und 10:00'")
print("3. 'Dienstag' -> 'dienstag'")
print()

# Now test if patterns would match
import re

print("=" * 80)
print("PATTERN MATCHING TEST")
print("=" * 80)

# Test the um pattern
test_text = "dienstag um 8:00"
at_pattern = r'(?:um|at)\s+(\d{1,2}):?(\d{2})?'
match = re.search(at_pattern, test_text)
print(f"Text: '{test_text}'")
print(f"Pattern: {at_pattern}")
print(f"Match: {match}")
if match:
    print(f"Groups: {match.groups()}")
print()

# Test zwischen pattern
test_text = "mittwoch zwischen 8:00 und 10:00"
between_pattern = r'zwischen\s+(\d{1,2}):?(\d{2})?\s+und\s+(\d{1,2}):?(\d{2})?'
match = re.search(between_pattern, test_text)
print(f"Text: '{test_text}'")
print(f"Pattern: {between_pattern}")
print(f"Match: {match}")
if match:
    print(f"Groups: {match.groups()}")
print()

# Test weekday detection
from time_parser.keywords import WEEKDAYS_DE

test_text = "dienstag"
print(f"Text: '{test_text}'")
print(f"WEEKDAYS_DE: {WEEKDAYS_DE}")
print(f"'dienstag' in WEEKDAYS_DE: {'dienstag' in WEEKDAYS_DE}")
print(f"'dienstag' in text: {'dienstag' in test_text}")
print()

print("=" * 80)

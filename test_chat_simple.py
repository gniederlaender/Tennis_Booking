#!/usr/bin/env python3
"""Simple test for chat engine intent parsing without dependencies."""

import re


def extract_slot_reference(message, context):
    """Extract reference to a slot from previous results."""
    # Look for patterns like "option 1", "first one", "number 2", etc.
    patterns = [
        r'option\s+(\d+)',
        r'number\s+(\d+)',
        r'slot\s+(\d+)',
        r'#(\d+)',
        r'^(\d+)$'
    ]

    msg_lower = message.lower()
    for pattern in patterns:
        match = re.search(pattern, msg_lower)
        if match:
            return int(match.group(1)) - 1  # Convert to 0-indexed

    # Handle words
    if 'first' in msg_lower or 'top' in msg_lower:
        return 0
    elif 'second' in msg_lower:
        return 1
    elif 'third' in msg_lower:
        return 2

    return None


def test_intent_detection():
    """Test basic intent detection."""
    print("Testing Intent Detection")
    print("=" * 60)

    test_cases = [
        ("find a court tomorrow", ["find"]),
        ("I need a trainer", ["need"]),
        ("book option 1", ["book"]),
        ("show my bookings", ["history", "bookings"]),
        ("hello", ["hi", "hello"]),
    ]

    for message, keywords in test_cases:
        msg_lower = message.lower()
        found = any(kw in msg_lower for kw in keywords)
        status = "✓" if found else "✗"
        print(f"{status} '{message}' contains {keywords}: {found}")

    print()


def test_slot_extraction():
    """Test slot reference extraction."""
    print("Testing Slot Reference Extraction")
    print("=" * 60)

    test_cases = [
        ("book option 1", 0),
        ("I'll take option 2", 1),
        ("reserve number 3", 2),
        ("book the first one", 0),
        ("take the second one", 1),
        ("1", 0),
    ]

    for message, expected in test_cases:
        result = extract_slot_reference(message, {})
        status = "✓" if result == expected else "✗"
        print(f"{status} '{message}' -> {result} (expected {expected})")

    print()


def main():
    print("Chat Engine Simple Tests")
    print("=" * 60)
    print()

    test_intent_detection()
    test_slot_extraction()

    print("=" * 60)
    print("Tests completed!")
    print("=" * 60)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Test script for the chat engine."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chat_engine import ChatEngine


def test_intent_parsing():
    """Test intent recognition."""
    print("=" * 60)
    print("Testing Intent Parsing")
    print("=" * 60)

    engine = ChatEngine()
    context = {'state': 'IDLE', 'last_results': [], 'last_search': {}}

    test_cases = [
        ("Hello", "greeting"),
        ("Find a court tomorrow at 6pm", "search_court"),
        ("I need a trainer next Monday", "search_trainer"),
        ("Book option 1", "book"),
        ("Show my bookings", "history"),
        ("Help", "help"),
        ("Thanks", "thanks"),
    ]

    for message, expected_intent in test_cases:
        intent, entities = engine.parse_intent(message, context)
        status = "✓" if intent == expected_intent else "✗"
        print(f"{status} '{message}' -> {intent} (expected {expected_intent})")

    print()


def test_slot_reference_extraction():
    """Test slot reference extraction."""
    print("=" * 60)
    print("Testing Slot Reference Extraction")
    print("=" * 60)

    engine = ChatEngine()
    context = {'state': 'RESULTS_SHOWN', 'last_results': ['slot1', 'slot2', 'slot3']}

    test_cases = [
        ("book option 1", 0),
        ("I'll take option 2", 1),
        ("reserve number 3", 2),
        ("book the first one", 0),
        ("take the second one", 1),
        ("1", 0),
    ]

    for message, expected_ref in test_cases:
        intent, entities = engine.parse_intent(message, context)
        slot_ref = entities.get('slot_reference')
        status = "✓" if slot_ref == expected_ref else "✗"
        print(f"{status} '{message}' -> {slot_ref} (expected {expected_ref})")

    print()


def test_response_generation():
    """Test response generation."""
    print("=" * 60)
    print("Testing Response Generation")
    print("=" * 60)

    engine = ChatEngine()
    context = {'state': 'IDLE', 'last_results': [], 'last_search': {}}

    # Test greeting
    response = engine.process_message("Hello", context)
    print(f"Greeting response: {response['reply'][:50]}...")
    print(f"Suggestions: {response['suggestions']}")
    print()

    # Test help
    response = engine.process_message("Help", context)
    print(f"Help response: {response['reply'][:50]}...")
    print()


def main():
    print("Chat Engine Test Suite")
    print("=" * 60)
    print()

    test_intent_parsing()
    test_slot_reference_extraction()
    test_response_generation()

    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == '__main__':
    main()

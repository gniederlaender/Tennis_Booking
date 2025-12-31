#!/usr/bin/env python3
"""
Tennis Court Booking Finder - CLI Application
Checks availability across multiple booking portals in Vienna.
"""

import sys
from datetime import datetime
from timeframe_parser import TimeframeParser
from scrapers_v2 import scrape_all_portals
from preference_engine import PreferenceEngine
from config import MAX_RESULTS


def display_results(slots, preferred_slot=None):
    """Display available slots in a formatted table."""
    if not slots:
        print("\nNo available slots found for the specified timeframe.")
        return

    print(f"\n{'='*80}")
    print(f"Found {len(slots)} available slot(s)")
    print(f"{'='*80}\n")

    # Sort by datetime
    slots.sort(key=lambda x: (x.get('date', ''), x.get('time', '')))

    for i, slot in enumerate(slots[:MAX_RESULTS], 1):
        is_preferred = preferred_slot and slot == preferred_slot

        prefix = ">>> PREFERRED >>> " if is_preferred else ""

        print(f"{prefix}[{i}] {slot.get('venue', 'Unknown Venue')}")
        print(f"    Date: {slot.get('date', 'N/A')} ({slot.get('day_of_week', 'N/A')})")
        print(f"    Time: {slot.get('time', 'N/A')}")

        if slot.get('court_name'):
            print(f"    Court: {slot['court_name']}")
        elif slot.get('court_type'):
            print(f"    Court: {slot['court_type']}")

        if slot.get('price'):
            print(f"    Price: {slot['price']}")

        if slot.get('location'):
            print(f"    Location: {slot['location']}")

        if slot.get('indoor_outdoor'):
            print(f"    Type: {slot['indoor_outdoor']}")

        print()

    if len(slots) > MAX_RESULTS:
        print(f"(Showing top {MAX_RESULTS} of {len(slots)} results)")


def prompt_user_selection(slots):
    """Prompt user to select a slot and optionally book it."""
    if not slots:
        return None, False

    try:
        print("\nOptions:")
        print("  - Enter slot number (1-{}) to select/book".format(min(len(slots), MAX_RESULTS)))
        print("  - Enter 'n' to skip")
        print("> ", end='')

        choice = input().strip().lower()

        if choice == 'n' or choice == '':
            return None, False

        try:
            slot_num = int(choice)
            if 1 <= slot_num <= min(len(slots), MAX_RESULTS):
                selected_slot = slots[slot_num - 1]

                # Ask if user wants to book
                print(f"\nSelected: {selected_slot.get('court_name')} at {selected_slot.get('time')}")
                print("Would you like to book this slot? (yes/no): ", end='')
                book_choice = input().strip().lower()

                should_book = book_choice in ['yes', 'y']
                return selected_slot, should_book
            else:
                print("Invalid slot number.")
                return None, False
        except ValueError:
            print("Invalid input.")
            return None, False
    except EOFError:
        # Handle non-interactive mode
        print("\n(Non-interactive mode - skipping selection)")
        return None, False


def main():
    """Main CLI application."""
    print("="*80)
    print("Tennis Court Booking Finder - Vienna")
    print("="*80)

    # Get user input
    if len(sys.argv) > 1:
        # Timeframe provided as command-line argument
        timeframe_text = ' '.join(sys.argv[1:])
    else:
        # Interactive mode
        print("\nEnter timeframe (e.g., 'next Monday 6-8pm', '7.1.2026 between 15:00 and 18:00'):")
        timeframe_text = input("> ").strip()

    if not timeframe_text:
        print("Error: No timeframe provided.")
        sys.exit(1)

    print(f"\nParsing: '{timeframe_text}'")

    # Parse timeframe
    parser = TimeframeParser()
    try:
        timeframe = parser.parse(timeframe_text)
        date = timeframe['date']
        start_time = timeframe['start_time']
        end_time = timeframe['end_time']

        print(f"Searching for: {date.strftime('%Y-%m-%d')} ({date.strftime('%A')})")
        print(f"Time range: {start_time} - {end_time}")
    except Exception as e:
        print(f"Error parsing timeframe: {e}")
        sys.exit(1)

    # Scrape portals
    print("\nSearching booking portals...")
    try:
        slots = scrape_all_portals(date, start_time, end_time)
    except Exception as e:
        print(f"Error during scraping: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Load preference engine
    pref_engine = PreferenceEngine()

    # Get preferred slot if we have confidence
    preferred_slot = None
    if pref_engine.has_confidence():
        preferred_slot = pref_engine.get_preferred_slot(slots)
        if preferred_slot:
            print("\n" + pref_engine.get_preference_summary())

    # Display results
    display_results(slots, preferred_slot)

    # Prompt for user selection and booking
    selected_slot, should_book = prompt_user_selection(slots)

    if selected_slot:
        # Log selection for preference learning
        pref_engine.log_selection(selected_slot)
        print("✓ Selection logged for preference learning")

        # Book if requested
        if should_book:
            print("\nAttempting to book...")
            from booking import book_court

            success, message = book_court(selected_slot)

            if success:
                print(f"✓ {message}")
                print("Booking recorded in booking_history.json")
            else:
                print(f"✗ Booking failed: {message}")
        else:
            print("(Booking skipped)")

    print("\nDone!")


if __name__ == "__main__":
    main()

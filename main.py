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
    """Prompt user to select a slot for booking (logs preference)."""
    if not slots:
        return None

    try:
        print("\nWould you like to mark any slot as your choice? (for preference learning)")
        print("Enter slot number (1-{}), or 'n' to skip: ".format(min(len(slots), MAX_RESULTS)), end='')

        choice = input().strip().lower()

        if choice == 'n' or choice == '':
            return None

        try:
            slot_num = int(choice)
            if 1 <= slot_num <= min(len(slots), MAX_RESULTS):
                return slots[slot_num - 1]
            else:
                print("Invalid slot number.")
                return None
        except ValueError:
            print("Invalid input.")
            return None
    except EOFError:
        # Handle non-interactive mode
        print("\n(Non-interactive mode - skipping selection)")
        return None


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

    # Prompt for user selection (for learning)
    selected_slot = prompt_user_selection(slots)
    if selected_slot:
        pref_engine.log_selection(selected_slot)
        print("Selection logged for preference learning. Thank you!")

    print("\nDone!")


if __name__ == "__main__":
    main()

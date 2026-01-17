#!/usr/bin/env python3
"""Test booking for Platz 5 on January 21, 2026 at 10:00."""

import sys
import json
import requests
from bs4 import BeautifulSoup
from booking import DasSpielBooker

def get_square_id_for_platz5(date='2026-01-21'):
    """Fetch the square_id for Platz 5 from the calendar."""
    url = f"https://reservierung.dasspiel.at/?date={date}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        print(f"Fetching calendar data for {date}...")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract calendar data from meta tag
        calendar_meta = soup.find('meta', {'id': 'transfer-data-calendar'})
        if calendar_meta and calendar_meta.get('data-content'):
            calendar_json = calendar_meta['data-content']
            # Decode HTML entities
            calendar_json = calendar_json.replace('&quot;', '"')
            calendar_data = json.loads(calendar_json)

            print(f"Found {len(calendar_data)} courts")

            # Find Platz 5
            for court in calendar_data:
                court_name = court.get('name', '')
                print(f"  - {court_name}")

                if 'Platz 5' in court_name or 'PLATZ 5' in court_name:
                    square_id = court.get('uuid', '')
                    print(f"\nFound Platz 5: {court_name}")
                    print(f"Square ID: {square_id}")
                    return square_id, court_name

            print("\nPlatz 5 not found in calendar data")
            return None, None
        else:
            print("Could not find calendar data in page")
            return None, None

    except Exception as e:
        print(f"Error fetching calendar data: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def main():
    """Main test function."""
    print("=" * 70)
    print("BOOKING TEST: Platz 5 on January 21, 2026 at 10:00")
    print("=" * 70)

    # Step 1: Get square_id for Platz 5
    square_id, court_name = get_square_id_for_platz5('2026-01-21')

    if not square_id:
        print("\nERROR: Could not get square_id for Platz 5")
        return 1

    # Step 2: Prepare booking slot
    slot = {
        'venue': 'Das Spiel (Tenniszentrum Arsenal)',
        'court_name': court_name,
        'date': '2026-01-21',
        'time': '10:00',
        'square_id': square_id,
        'price': '26.00'
    }

    print("\n" + "=" * 70)
    print("BOOKING DETAILS")
    print("=" * 70)
    print(f"Court: {slot['court_name']}")
    print(f"Date: {slot['date']}")
    print(f"Time: {slot['time']}")
    print(f"Square ID: {slot['square_id']}")
    print("=" * 70)

    # Step 3: Execute booking
    print("\nInitiating booking...")
    booker = DasSpielBooker()
    success, message = booker.book_slot(slot)

    print("\n" + "=" * 70)
    print("BOOKING RESULT")
    print("=" * 70)
    print(f"Status: {'SUCCESS' if success else 'FAILED'}")
    print(f"Message: {message}")
    print("=" * 70)

    if success:
        print("\n✓ Booking completed successfully!")
        return 0
    else:
        print("\n✗ Booking failed!")
        return 1


if __name__ == '__main__':
    sys.exit(main())

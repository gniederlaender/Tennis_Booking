#!/usr/bin/env python3
"""
Simple booking test for Platz 5 on January 21, 2026 at 10:00.
This version manually specifies the square_id.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from booking import DasSpielBooker


def main():
    """Main test function."""
    print("=" * 70)
    print("BOOKING TEST: Platz 5 HALLE on January 21, 2026 at 10:00")
    print("=" * 70)

    # Manual entry - we need to get the square_id from the calendar first
    # Based on the spec, square_id for Platz 3 is 9892e07c-3d52-437a-94db-d474c640b2fa
    # We need to find Platz 5's square_id by inspecting the calendar page

    print("\nNOTE: This test requires the square_id for Platz 5.")
    print("First, let's login and check if we can get square IDs...")

    booker = DasSpielBooker()

    # Test login
    print("\nTesting login...")
    success, message = booker.login()

    if not success:
        print(f"Login failed: {message}")
        return 1

    print(f"Login successful! CSRF token: {booker.csrf_token[:20]}...")

    # Now we need to get the calendar data to extract square_ids
    print("\nFetching calendar data for 2026-01-21...")

    import requests
    url = f"{booker.URL}?date=2026-01-21"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }

    try:
        response = booker.session.get(url, headers=headers, timeout=10)

        # Look for Platz 5 UUID in the page source
        page_source = response.text

        # The calendar data is embedded in a meta tag as JSON
        # Let's extract all UUIDs and court names
        import re
        import json

        # Find the calendar data meta tag
        meta_pattern = r'<meta[^>]+id="transfer-data-calendar"[^>]+data-content="([^"]+)"'
        match = re.search(meta_pattern, page_source)

        if match:
            # Decode HTML entities
            calendar_json = match.group(1).replace('&quot;', '"')
            calendar_data = json.loads(calendar_json)

            print(f"\nFound {len(calendar_data)} courts in calendar:")

            platz5_square_id = None
            for court in calendar_data:
                court_name = court.get('name', 'Unknown')
                square_id = court.get('uuid', '')
                print(f"  - {court_name}: {square_id}")

                if 'Platz 5' in court_name or 'PLATZ 5' in court_name:
                    platz5_square_id = square_id
                    print(f"\n>>> Found Platz 5! Square ID: {square_id}")

            if not platz5_square_id:
                print("\nERROR: Could not find Platz 5 in calendar data")
                return 1

            # Now book it!
            slot = {
                'venue': 'Das Spiel (Tenniszentrum Arsenal)',
                'court_name': 'Platz 5 HALLE',
                'date': '2026-01-21',
                'time': '10:00',
                'square_id': platz5_square_id,
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

            print("\nInitiating booking...")
            success, message = booker.book_slot_api(slot)

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
                print("\nTrying Selenium fallback...")
                success, message = booker.book_slot_selenium(slot)
                print(f"\nSelenium result: {'SUCCESS' if success else 'FAILED'}")
                print(f"Message: {message}")
                return 0 if success else 1
        else:
            print("\nERROR: Could not find calendar data in page")
            return 1

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

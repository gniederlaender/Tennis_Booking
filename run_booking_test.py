#!/usr/bin/env python3
"""Run booking test for Platz 5 on 2026-01-21 at 10:00."""

if __name__ == '__main__':
    import sys
    import os

    # Add current directory to path
    sys.path.insert(0, '/opt/Tennis_Booking')
    sys.path.insert(0, '/opt/Tennis_Booking/venv/lib/python3.12/site-packages')

    # Now import our modules
    from booking import DasSpielBooker
    import requests
    import json
    import re

    print("=" * 70)
    print("BOOKING TEST: Platz 5 on January 21, 2026 at 10:00")
    print("=" * 70)

    booker = DasSpielBooker()

    # Step 1: Login
    print("\n[1/4] Testing login...")
    success, message = booker.login()

    if not success:
        print(f"ERROR: Login failed: {message}")
        sys.exit(1)

    print(f"SUCCESS: {message}")
    print(f"CSRF Token: {booker.csrf_token[:20]}..." if booker.csrf_token else "No token")

    # Step 2: Get calendar data
    print("\n[2/4] Fetching calendar data for 2026-01-21...")

    url = f"{booker.URL}?date=2026-01-21"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }

    try:
        response = booker.session.get(url, headers=headers, timeout=10)
        page_source = response.text

        # Find the calendar data meta tag
        meta_pattern = r'<meta[^>]+id="transfer-data-calendar"[^>]+data-content="([^"]+)"'
        match = re.search(meta_pattern, page_source)

        if not match:
            print("ERROR: Could not find calendar data in page")
            sys.exit(1)

        # Decode HTML entities
        calendar_json = match.group(1).replace('&quot;', '"')
        calendar_data = json.loads(calendar_json)

        print(f"SUCCESS: Found {len(calendar_data)} courts")

        # Step 3: Find Platz 5
        print("\n[3/4] Locating Platz 5...")

        platz5_square_id = None
        platz5_name = None

        for court in calendar_data:
            court_name = court.get('name', 'Unknown')
            square_id = court.get('uuid', '')

            if 'Platz 5' in court_name or 'PLATZ 5' in court_name.upper():
                platz5_square_id = square_id
                platz5_name = court_name
                print(f"SUCCESS: Found {court_name}")
                print(f"Square ID: {square_id}")
                break

        if not platz5_square_id:
            print("ERROR: Platz 5 not found in calendar")
            print("\nAvailable courts:")
            for court in calendar_data:
                print(f"  - {court.get('name', 'Unknown')}")
            sys.exit(1)

        # Step 4: Book it!
        print("\n[4/4] Initiating booking...")
        print("-" * 70)

        slot = {
            'venue': 'Das Spiel (Tenniszentrum Arsenal)',
            'court_name': platz5_name,
            'date': '2026-01-21',
            'time': '10:00',
            'square_id': platz5_square_id,
            'price': '26.00'
        }

        print(f"Court: {slot['court_name']}")
        print(f"Date: {slot['date']}")
        print(f"Time: {slot['time']}")
        print(f"Square ID: {slot['square_id']}")
        print("-" * 70)

        success, message = booker.book_slot_api(slot)

        print("\n" + "=" * 70)
        print("BOOKING RESULT")
        print("=" * 70)
        print(f"Status: {'✓ SUCCESS' if success else '✗ FAILED'}")
        print(f"Message: {message}")
        print("=" * 70)

        if not success:
            print("\nAttempting Selenium fallback...")
            success2, message2 = booker.book_slot_selenium(slot)
            print(f"Selenium result: {'✓ SUCCESS' if success2 else '✗ FAILED'}")
            print(f"Message: {message2}")
            sys.exit(0 if success2 else 1)

        sys.exit(0)

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

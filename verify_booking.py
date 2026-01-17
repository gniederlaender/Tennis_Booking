#!/usr/bin/env python3
"""Verify that the booking appears on the calendar."""

if __name__ == '__main__':
    import sys
    import os
    sys.path.insert(0, '/opt/Tennis_Booking')
    sys.path.insert(0, '/opt/Tennis_Booking/venv/lib/python3.12/site-packages')

    from booking import DasSpielBooker
    import json
    import re

    print("=" * 70)
    print("VERIFICATION: Checking calendar for booking on 2026-01-21")
    print("=" * 70)

    booker = DasSpielBooker()

    # Login
    success, message = booker.login()
    if not success:
        print(f"Login failed: {message}")
        sys.exit(1)

    print(f"Logged in successfully")

    # Get calendar
    url = f"{booker.URL}?date=2026-01-21"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }

    response = booker.session.get(url, headers=headers, timeout=10)
    page_source = response.text

    # Find calendar data
    meta_pattern = r'<meta[^>]+id="transfer-data-calendar"[^>]+data-content="([^"]+)"'
    match = re.search(meta_pattern, page_source)

    if not match:
        print("ERROR: Could not find calendar data")
        sys.exit(1)

    calendar_json = match.group(1).replace('&quot;', '"')
    calendar_data = json.loads(calendar_json)

    # Find Platz 5 and check its rentals
    for court in calendar_data:
        court_name = court.get('name', 'Unknown')

        if 'Platz 5' in court_name or 'PLATZ 5' in court_name.upper():
            print(f"\nFound: {court_name}")
            rentals = court.get('rentals', [])

            print(f"Total rentals on this court: {len(rentals)}")

            if rentals:
                print("\nRentals:")
                for rental in rentals:
                    time_start = rental.get('time_start', 'Unknown')
                    time_end = rental.get('time_end', 'Unknown')
                    is_own = rental.get('is_own_booking', False)
                    print(f"  {time_start} - {time_end} {'(YOUR BOOKING)' if is_own else ''}")

                # Check for 10:00 booking
                for rental in rentals:
                    if rental.get('time_start', '').startswith('10:00'):
                        print("\n" + "=" * 70)
                        print("✓ BOOKING CONFIRMED!")
                        print(f"Your booking is visible on the calendar:")
                        print(f"  Court: {court_name}")
                        print(f"  Time: {rental.get('time_start')} - {rental.get('time_end')}")
                        print(f"  Is your booking: {rental.get('is_own_booking', False)}")
                        print("=" * 70)
                        sys.exit(0)
            else:
                print("No rentals found on Platz 5")
                break

    print("\nWARNING: Could not find the 10:00 booking in the calendar.")
    print("This might be a delay in the system updating.")
    print("Please check the website manually to confirm.")
    sys.exit(1)

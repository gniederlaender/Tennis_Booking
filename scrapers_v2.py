"""Web scrapers for tennis court booking portals - Version 2."""

import json
import re
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup


class DasSpielScraperV2:
    """Scraper for reservierung.dasspiel.at using requests."""

    URL = "https://reservierung.dasspiel.at/"

    def scrape(self, date, start_time, end_time):
        """Scrape Das Spiel booking portal."""
        results = []

        try:
            # Fetch with date parameter to get booking data
            url_with_date = f"{self.URL}?date={date.strftime('%Y-%m-%d')}"
            print(f"Fetching {url_with_date}...")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url_with_date, headers=headers, timeout=10)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract calendar data from meta tag
            calendar_meta = soup.find('meta', {'id': 'transfer-data-calendar'})
            if calendar_meta and calendar_meta.get('data-content'):
                calendar_json = calendar_meta['data-content']
                # Decode HTML entities
                calendar_json = calendar_json.replace('&quot;', '"')
                calendar_data = json.loads(calendar_json)

                print(f"Found {len(calendar_data)} courts")

                # Process each court
                for court in calendar_data:
                    court_name = court.get('name', 'Unknown')
                    time_start = court.get('time_start', '07:00:00')
                    time_end = court.get('time_end', '22:00:00')
                    timeblock = court.get('timeblock', 60)  # minutes
                    rentals = court.get('rentals', [])

                    # Build set of booked time slots from rentals
                    booked_times = set()
                    for rental in rentals:
                        rental_start = rental.get('time_start', '')
                        rental_end = rental.get('time_end', '')
                        # Add all hours in this rental period
                        if rental_start and rental_end:
                            start_hour = int(rental_start.split(':')[0])
                            end_hour = int(rental_end.split(':')[0])
                            for hour in range(start_hour, end_hour):
                                booked_times.add(f"{hour:02d}:00")

                    # Generate available slots (only free ones)
                    slots = self._generate_available_slots(
                        court_name,
                        date,
                        start_time,
                        end_time,
                        time_start,
                        time_end,
                        timeblock,
                        booked_times
                    )
                    results.extend(slots)

            print(f"Total available FREE slots found: {len(results)}")

        except Exception as e:
            print(f"Error scraping Das Spiel: {e}")
            import traceback
            traceback.print_exc()

        return results


    def _generate_available_slots(self, court_name, date, user_start, user_end,
                                   court_start, court_end, timeblock, booked_times):
        """Generate available time slots for a court."""
        slots = []

        # Parse times
        user_start_hour, user_start_min = map(int, user_start.split(':'))
        user_end_hour, user_end_min = map(int, user_end.split(':'))
        court_start_hour = int(court_start.split(':')[0])
        court_end_hour = int(court_end.split(':')[0])

        # Create time range for the day
        current = datetime.combine(date, datetime.min.time()).replace(
            hour=max(user_start_hour, court_start_hour),
            minute=user_start_min if user_start_hour >= court_start_hour else 0
        )

        end_datetime = datetime.combine(date, datetime.min.time()).replace(
            hour=min(user_end_hour, court_end_hour),
            minute=user_end_min if user_end_hour <= court_end_hour else 0
        )

        while current < end_datetime:
            time_str = current.strftime('%H:%M')

            # Check if this slot is not booked
            if time_str not in booked_times:
                slot = {
                    'venue': 'Tenniszentrum Arsenal (Das Spiel)',
                    'date': date.strftime('%Y-%m-%d'),
                    'day_of_week': date.strftime('%A'),
                    'time': time_str,
                    'court_name': court_name,
                    'court_type': 'Indoor' if 'HALLE' in court_name.upper() else 'Outdoor',
                    'indoor_outdoor': 'Indoor' if 'HALLE' in court_name.upper() else 'Outdoor',
                    'duration': f"{timeblock} min",
                    'location': 'Arsenal, Wien',
                    'price': 'N/A',  # Price info not in the data
                }
                slots.append(slot)

            current += timedelta(minutes=timeblock)

        return slots


class PostSVScraperV2:
    """Scraper for buchen.postsv-wien.at using requests."""

    URL = "https://buchen.postsv-wien.at/tennis.html"
    LOGIN_URL = "https://buchen.postsv-wien.at/login-tennis.html"

    def __init__(self):
        self.session = requests.Session()
        self.credentials = self._load_credentials()

    def _load_credentials(self):
        """Load credentials from credentials.json if available."""
        import os
        cred_file = 'credentials.json'
        if os.path.exists(cred_file):
            try:
                with open(cred_file, 'r') as f:
                    data = json.load(f)
                    return data.get('postsv', {})
            except:
                pass
        return {}

    def _login(self):
        """Attempt to login to Post SV Wien."""
        if not self.credentials.get('username') or not self.credentials.get('password'):
            return False

        try:
            print(f"Attempting login with provided credentials...")

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            # Get login page first to extract form data
            response = self.session.get(self.LOGIN_URL, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find login form
            form = soup.find('form', id='tl_login')
            if not form:
                print("Could not find login form")
                return False

            # Prepare login data
            login_data = {
                'FORM_SUBMIT': 'tl_login',
                'username': self.credentials['username'],
                'password': self.credentials['password']
            }

            # Submit login (add Referer header required by Contao CMS)
            headers['Referer'] = self.LOGIN_URL
            response = self.session.post(self.LOGIN_URL, data=login_data, headers=headers, timeout=10, allow_redirects=True)

            # Check if login was successful
            if 'login' not in response.url.lower() and response.status_code == 200:
                print("Login successful!")
                return True
            else:
                print("Login failed - check credentials")
                return False

        except Exception as e:
            print(f"Login error: {e}")
            return False

    def scrape(self, date, start_time, end_time):
        """Scrape Post SV Wien booking portal."""
        results = []

        try:
            print(f"Fetching {self.URL}...")
            print("Note: This portal requires login for full access.")

            # Try to login if credentials are available
            if self.credentials:
                if self._login():
                    # Fetch the booking page for the specific date
                    date_str = date.strftime('%Y%m%d')
                    date_url = f"{self.URL}?day={date_str}"

                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Referer': self.URL
                    }
                    response = self.session.get(date_url, headers=headers, timeout=10)

                    if response.status_code == 200 and 'login' not in response.url.lower():
                        print(f"Successfully fetched booking page for {date.strftime('%Y-%m-%d')}")

                        # Parse the booking table
                        soup = BeautifulSoup(response.content, 'html.parser')

                        # Find all scroll tables
                        tables = soup.find_all('table', class_='scroll-table')

                        for table in tables:
                            # Find all rows with court names
                            all_rows = table.find_all('tr')

                            for row in all_rows:
                                # Find court name in this row
                                court_cell = row.find('td', class_='ressourcename')
                                if not court_cell:
                                    continue

                                court_name = court_cell.get_text().strip()

                                # Find all cells in this row
                                cells = row.find_all('td', class_='reservationcell')

                                for cell in cells:
                                    # Check if cell is free (available)
                                    if 'free' in cell.get('class', []):
                                        # Find the booking link
                                        link = cell.find('a', class_='reservationlink')

                                        if link:
                                            # Extract time from href (format: time=SECONDS)
                                            href = link.get('href', '')
                                            time_match = re.search(r'time=(\d+)', href)

                                            if time_match:
                                                seconds = int(time_match.group(1))
                                                hours = seconds // 3600
                                                minutes = (seconds % 3600) // 60
                                                time_str = f"{hours:02d}:{minutes:02d}"

                                                # Filter by user's requested timeframe
                                                if self._is_in_timeframe(time_str, start_time, end_time):
                                                    # Extract price from title
                                                    title = link.get('title', '')
                                                    price_match = re.search(r'€\s*([\d,]+)', title)
                                                    price = price_match.group(1) if price_match else 'N/A'

                                                    slot = {
                                                        'venue': 'Post SV Wien',
                                                        'date': date.strftime('%Y-%m-%d'),
                                                        'day_of_week': date.strftime('%A'),
                                                        'time': time_str,
                                                        'court_name': court_name,
                                                        'court_type': 'Tennis',
                                                        'indoor_outdoor': 'Mixed',  # Post SV has both
                                                        'duration': '60 min',
                                                        'location': 'Post SV Wien, Roggendorfgasse 2',
                                                        'price': f"€ {price}",
                                                        'booking_link': href,  # Store for booking
                                                    }
                                                    results.append(slot)

                        print(f"Found {len(results)} slots in requested timeframe")
                    else:
                        print("Could not access booking page after login")
                else:
                    print("Login failed - cannot retrieve bookings")
            else:
                print("No credentials found (create credentials.json from credentials.json.example)")
                print("Cannot check availability without authentication")

        except Exception as e:
            print(f"Error scraping Post SV Wien: {e}")
            import traceback
            traceback.print_exc()

        return results

    def _is_in_timeframe(self, time_str, start_time, end_time):
        """Check if a time is within the requested timeframe."""
        try:
            time_hour, time_min = map(int, time_str.split(':'))
            start_hour, start_min = map(int, start_time.split(':'))
            end_hour, end_min = map(int, end_time.split(':'))

            time_minutes = time_hour * 60 + time_min
            start_minutes = start_hour * 60 + start_min
            end_minutes = end_hour * 60 + end_min

            return start_minutes <= time_minutes < end_minutes
        except:
            return False


def scrape_all_portals(date, start_time, end_time, locations=None):
    """Scrape all configured portals and return combined results."""
    all_results = []

    # Default to both locations if not specified
    if locations is None:
        locations = {'arsenal': True, 'postsv': True}

    # Das Spiel (Arsenal)
    if locations.get('arsenal', True):
        print("\n" + "="*60)
        print("Scraping Das Spiel (Tenniszentrum Arsenal)...")
        print("="*60)
        dasspiel = DasSpielScraperV2()
        dasspiel_results = dasspiel.scrape(date, start_time, end_time)
        all_results.extend(dasspiel_results)
        print(f"Found {len(dasspiel_results)} slots from Das Spiel\n")
    else:
        print("\n" + "="*60)
        print("Skipping Das Spiel (Arsenal) - not selected")
        print("="*60)

    # Post SV
    if locations.get('postsv', True):
        print("\n" + "="*60)
        print("Scraping Post SV Wien...")
        print("="*60)
        postsv = PostSVScraperV2()
        postsv_results = postsv.scrape(date, start_time, end_time)
        all_results.extend(postsv_results)
        print(f"Found {len(postsv_results)} slots from Post SV Wien\n")
    else:
        print("\n" + "="*60)
        print("Skipping Post SV Wien - not selected")
        print("="*60)

    return all_results

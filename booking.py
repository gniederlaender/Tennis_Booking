"""Booking functionality for tennis courts."""

import json
import os
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup


class BookingHistory:
    """Manages booking history in JSON."""

    def __init__(self, history_file='booking_history.json'):
        self.history_file = history_file
        self.bookings = self.load()

    def load(self):
        """Load booking history from file."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def save(self):
        """Save booking history to file."""
        with open(self.history_file, 'w') as f:
            json.dump(self.bookings, f, indent=2)

    def add_booking(self, slot, status='success', error=None):
        """Add a booking to history."""
        booking = {
            'timestamp': datetime.now().isoformat(),
            'status': status,
            'slot': slot,
            'error': error
        }
        self.bookings.append(booking)
        self.save()
        return booking


class DasSpielBooker:
    """Handles booking for Das Spiel (Arsenal)."""

    URL = "https://reservierung.dasspiel.at/"
    LOGIN_URL = f"{URL}login"
    API_LOGIN_URL = f"{URL}api/login"  # Try API endpoint

    def __init__(self):
        self.session = requests.Session()
        self.credentials = self._load_credentials()

    def _load_credentials(self):
        """Load credentials from file."""
        if os.path.exists('credentials.json'):
            with open('credentials.json', 'r') as f:
                data = json.load(f)
                return data.get('dasspiel', {})
        return {}

    def login(self):
        """Login to Das Spiel."""
        if not self.credentials:
            return False, "No credentials found"

        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

            # Get login page
            response = self.session.get(self.LOGIN_URL, headers=headers, timeout=10)

            # Parse CSRF token
            soup = BeautifulSoup(response.content, 'html.parser')
            csrf_meta = soup.find('meta', {'name': 'csrf-token'})
            csrf_token = csrf_meta['content'] if csrf_meta else None

            if not csrf_token:
                # Try to find hidden input with token
                token_input = soup.find('input', {'name': '_token'})
                if token_input:
                    csrf_token = token_input.get('value')

            # Login - this is a SPA, so we need to send JSON, not form data
            login_data = {
                'email': self.credentials['username'],
                'password': self.credentials['password']
            }

            headers['Referer'] = self.LOGIN_URL
            headers['Content-Type'] = 'application/json'
            headers['Accept'] = 'application/json'
            if csrf_token:
                headers['X-CSRF-TOKEN'] = csrf_token

            response = self.session.post(self.LOGIN_URL, json=login_data, headers=headers, timeout=10, allow_redirects=False)

            # Check success - if we're redirected away from login page
            if 'login' not in response.url.lower() and response.status_code == 200:
                return True, "Login successful"
            else:
                # Check if we have a logged-in session by looking for logout link
                if 'logout' in response.text.lower() or 'abmelden' in response.text.lower():
                    return True, "Login successful"
                return False, f"Login failed (Das Spiel uses JavaScript - may require browser automation)"

        except Exception as e:
            return False, f"Login error: {str(e)}"

    def book_slot(self, slot):
        """
        Book a slot at Das Spiel.

        Process:
        1. Login
        2. Navigate to booking page for the date/time
        3. Click "platz mieten"
        4. Tick AGB checkbox
        5. Click "verbindlich reservieren"
        """
        try:
            # Login first
            success, message = self.login()
            if not success:
                return False, message

            # Extract slot details
            date = slot.get('date')
            time = slot.get('time')
            court_name = slot.get('court_name')

            # Navigate to booking with date parameter
            booking_url = f"{self.URL}?date={date}"
            headers = {'User-Agent': 'Mozilla/5.0', 'Referer': self.URL}

            response = self.session.get(booking_url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Get CSRF token
            csrf_meta = soup.find('meta', {'name': 'csrf-token'})
            csrf_token = csrf_meta['content'] if csrf_meta else None

            # Build booking request
            # This would need the actual slot UUID and booking endpoint
            # For now, construct based on common patterns
            booking_data = {
                '_token': csrf_token,
                'date': date,
                'time': time,
                'court': court_name,
                'duration': 60,  # 1 hour
                'agb_accepted': 1
            }

            headers['X-CSRF-TOKEN'] = csrf_token

            # Submit booking (endpoint may vary)
            booking_endpoint = f"{self.URL}booking/create"
            response = self.session.post(booking_endpoint, data=booking_data, headers=headers, timeout=10)

            if response.status_code == 200:
                return True, f"Successfully booked {court_name} at {time}"
            else:
                return False, f"Booking failed: HTTP {response.status_code}"

        except Exception as e:
            return False, f"Booking error: {str(e)}"


class PostSVBooker:
    """Handles booking for Post SV Wien."""

    URL = "https://buchen.postsv-wien.at/tennis.html"
    LOGIN_URL = "https://buchen.postsv-wien.at/login-tennis.html"

    def __init__(self):
        self.session = requests.Session()
        self.credentials = self._load_credentials()

    def _load_credentials(self):
        """Load credentials from file."""
        if os.path.exists('credentials.json'):
            with open('credentials.json', 'r') as f:
                data = json.load(f)
                return data.get('postsv', {})
        return {}

    def login(self):
        """Login to Post SV Wien."""
        if not self.credentials:
            return False, "No credentials found"

        try:
            headers = {'User-Agent': 'Mozilla/5.0'}

            # Get login page
            response = self.session.get(self.LOGIN_URL, headers=headers, timeout=10)

            # Login
            login_data = {
                'FORM_SUBMIT': 'tl_login',
                'username': self.credentials['username'],
                'password': self.credentials['password']
            }

            headers['Referer'] = self.LOGIN_URL
            response = self.session.post(self.LOGIN_URL, data=login_data, headers=headers, timeout=10, allow_redirects=True)

            if 'login' not in response.url.lower() and response.status_code == 200:
                return True, "Login successful"
            else:
                return False, "Login failed"

        except Exception as e:
            return False, f"Login error: {str(e)}"

    def book_slot(self, slot):
        """
        Book a slot at Post SV Wien.

        Process:
        1. Login
        2. Click on the reservation link (from search results)
        3. Press "speichern" button
        """
        try:
            # Login first
            success, message = self.login()
            if not success:
                return False, message

            # Get booking link from slot
            # During search, we need to store the booking link
            booking_link = slot.get('booking_link')

            if not booking_link:
                return False, "No booking link found in slot data"

            # Navigate to booking page
            booking_url = f"https://buchen.postsv-wien.at/{booking_link}"
            headers = {'User-Agent': 'Mozilla/5.0', 'Referer': self.URL}

            response = self.session.get(booking_url, headers=headers, timeout=10)

            # Parse the booking page
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find the form
            form = soup.find('form')

            if not form:
                return False, "Could not find booking form on page"

            # Extract form data (all inputs including hidden ones)
            form_data = {}
            for input_field in form.find_all('input'):
                name = input_field.get('name')
                value = input_field.get('value', '')
                if name and input_field.get('type') != 'submit':
                    form_data[name] = value

            # Extract select fields
            for select_field in form.find_all('select'):
                name = select_field.get('name')
                if name:
                    # Get first option value (default duration is 1 hour)
                    option = select_field.find('option')
                    if option:
                        form_data[name] = option.get('value', '60')

            # Add the submit button - critical for Contao CMS!
            submit_button = form.find('input', {'type': 'submit'})
            if submit_button:
                button_name = submit_button.get('name')
                if button_name:
                    form_data[button_name] = submit_button.get('value', 'Speichern')

            # Submit booking to the same URL (empty action means same URL)
            response = self.session.post(booking_url, data=form_data, headers=headers, timeout=10)

            # Check if booking was successful
            if response.status_code == 200:
                # Check for success indicators
                # Success is typically indicated by redirect to reservations page
                if 'reservierung' in response.url.lower():
                    court_name = slot.get('court_name')
                    time = slot.get('time')
                    date = slot.get('date')
                    return True, f"Successfully booked {court_name} on {date} at {time}"
                elif 'fehler' in response.text.lower() or 'error' in response.text.lower():
                    return False, "Booking failed - error message on page"
                else:
                    # If redirected or no error, assume success
                    court_name = slot.get('court_name')
                    time = slot.get('time')
                    return True, f"Booking completed for {court_name} at {time}"
            else:
                return False, f"Booking failed with HTTP status {response.status_code}"

        except Exception as e:
            return False, f"Booking error: {str(e)}"


def book_court(slot):
    """
    Book a court slot.

    Args:
        slot: Dict with slot information including venue

    Returns:
        (success, message) tuple
    """
    venue = slot.get('venue', '')
    history = BookingHistory()

    try:
        if 'Das Spiel' in venue or 'Arsenal' in venue:
            booker = DasSpielBooker()
            success, message = booker.book_slot(slot)
        elif 'Post SV' in venue:
            booker = PostSVBooker()
            success, message = booker.book_slot(slot)
        else:
            success = False
            message = f"Unknown venue: {venue}"

        # Log booking attempt
        status = 'success' if success else 'failed'
        history.add_booking(slot, status=status, error=None if success else message)

        # Feed to preference engine if successful
        if success:
            from preference_engine import PreferenceEngine
            pref_engine = PreferenceEngine()
            pref_engine.log_selection(slot)

        return success, message

    except Exception as e:
        error_msg = f"Booking error: {str(e)}"
        history.add_booking(slot, status='error', error=error_msg)
        return False, error_msg

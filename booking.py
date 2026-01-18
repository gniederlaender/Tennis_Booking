"""Booking functionality for tennis courts."""

import json
import os
import re
import time
import sys
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait


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
    SIGNIN_URL = f"{URL}signin"
    BOOKING_URL = f"{URL}user/booking/rent"

    def __init__(self):
        self.session = requests.Session()
        self.credentials = self._load_credentials()
        self.csrf_token = None

    def _load_credentials(self):
        """Load credentials from file."""
        if os.path.exists('credentials.json'):
            with open('credentials.json', 'r') as f:
                data = json.load(f)
                return data.get('dasspiel', {})
        return {}

    def _get_csrf_token(self, html_content):
        """Extract CSRF token from HTML page."""
        soup = BeautifulSoup(html_content, 'html.parser')
        # Try meta tag first
        csrf_meta = soup.find('meta', {'name': 'csrf-token'})
        if csrf_meta and csrf_meta.get('content'):
            return csrf_meta['content']
        # Try hidden input field
        csrf_input = soup.find('input', {'name': '_token'})
        if csrf_input and csrf_input.get('value'):
            return csrf_input['value']
        return None

    def login(self):
        """Sign in to Das Spiel using the /signin endpoint."""
        if not self.credentials:
            return False, "No credentials found"

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }

            # Get signin page for CSRF token
            response = self.session.get(self.SIGNIN_URL, headers=headers, timeout=10)
            self.csrf_token = self._get_csrf_token(response.content)

            # Sign in with correct field names: 'email' and 'pw'
            signin_data = {
                'email': self.credentials['username'],
                'pw': self.credentials['password']
            }

            headers['Referer'] = self.SIGNIN_URL
            headers['Content-Type'] = 'application/json'
            headers['Accept'] = 'application/json'
            if self.csrf_token:
                headers['X-CSRF-TOKEN'] = self.csrf_token

            response = self.session.post(self.SIGNIN_URL, json=signin_data, headers=headers, timeout=10, allow_redirects=False)

            # Check for success - Das Spiel returns plain text "signed-in"
            if response.status_code == 200 and response.text == 'signed-in':
                # Refresh CSRF token after login by visiting main page
                main_response = self.session.get(self.URL, headers={'User-Agent': headers['User-Agent']}, timeout=10)
                new_token = self._get_csrf_token(main_response.content)
                if new_token:
                    self.csrf_token = new_token
                return True, "Login successful"
            else:
                return False, f"Login failed: {response.text}"

        except Exception as e:
            return False, f"Login error: {str(e)}"

    def book_slot_api(self, slot):
        """
        Book a slot at Das Spiel using direct API calls.

        This is the fast, lightweight approach using HTTP POST to /user/booking/rent.

        Args:
            slot: Dict with keys: date, time, square_id, court_name

        Returns:
            (success, message) tuple
        """
        date = slot.get('date')
        time_slot = slot.get('time')
        court_name = slot.get('court_name')
        square_id = slot.get('square_id')

        print(f"BOOKING API: Starting booking for {court_name} at {time_slot} on {date}", file=sys.stderr, flush=True)

        if not square_id:
            return False, "Missing square_id for Das Spiel booking. Slot data may be outdated."

        # Login first
        success, message = self.login()
        if not success:
            return False, f"Login failed: {message}"

        print(f"BOOKING API: Login successful, CSRF token obtained", file=sys.stderr, flush=True)

        # Parse time slot to extract start and end times
        # time_slot format is typically "HH:MM" for the start time
        # Assuming 1-hour booking by default
        time_start = time_slot
        try:
            # Parse hour and calculate end time (1 hour later)
            hour = int(time_start.split(':')[0])
            minute = time_start.split(':')[1]
            end_hour = hour + 1
            time_end = f"{end_hour:02d}:{minute}"
        except:
            # Fallback: if parsing fails, assume end is 1 hour after start
            time_end = f"{int(time_slot.split(':')[0]) + 1:02d}:00"

        # Prepare JSON payload for the new API format
        booking_payload = {
            'square_uuid': square_id,
            'time_start': time_start,
            'time_end': time_end,
            'nof_players': 1,
            'date': date,
            'is_paid': False
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Referer': f"{self.URL}?date={date}",
            'Origin': self.URL.rstrip('/')
        }

        if self.csrf_token:
            headers['X-CSRF-TOKEN'] = self.csrf_token

        print(f"BOOKING API: Sending POST to {self.BOOKING_URL}", file=sys.stderr, flush=True)
        print(f"BOOKING API: Payload: {booking_payload}", file=sys.stderr, flush=True)

        try:
            response = self.session.post(
                self.BOOKING_URL,
                json=booking_payload,
                headers=headers,
                timeout=15,
                allow_redirects=False
            )

            print(f"BOOKING API: Response status: {response.status_code}", file=sys.stderr, flush=True)
            print(f"BOOKING API: Response text: {response.text[:500] if response.text else 'empty'}", file=sys.stderr, flush=True)

            # Check for success - typically returns 200 with JSON
            if response.status_code in [200, 201]:
                # Check for JSON response
                try:
                    json_response = response.json()
                    print(f"BOOKING API: JSON response: {json_response}", file=sys.stderr, flush=True)

                    if isinstance(json_response, dict):
                        # Check for success indicators
                        if json_response.get('status') == 1 or json_response.get('success') == True:
                            print(f"BOOKING API: Success confirmed", file=sys.stderr, flush=True)
                            return True, f"Successfully booked {court_name} on {date} at {time_slot}"
                        elif json_response.get('status') == 0 or json_response.get('success') == False:
                            error_msg = json_response.get('message', 'Slot may be unavailable')
                            print(f"BOOKING API: Failure - {error_msg}", file=sys.stderr, flush=True)
                            return False, f"Booking failed - {error_msg}"

                    # If no clear status indicator, assume success for 200/201
                    return True, f"Successfully booked {court_name} on {date} at {time_slot}"
                except:
                    # Not JSON response, check text content
                    response_text = response.text.lower() if response.text else ''
                    if 'error' in response_text or 'fehler' in response_text:
                        return False, f"Booking rejected: {response.text[:200]}"
                    # Assume success for 200/201
                    return True, f"Successfully booked {court_name} on {date} at {time_slot}"

            elif response.status_code in [302, 303]:
                # Redirect indicates success
                location = response.headers.get('Location', '')
                print(f"BOOKING API: Redirected to: {location}", file=sys.stderr, flush=True)
                return True, f"Successfully booked {court_name} on {date} at {time_slot}"

            elif response.status_code == 422:
                # Validation error - parse message
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', response.text)
                except:
                    error_msg = response.text
                return False, f"Validation error: {error_msg}"

            elif response.status_code == 401:
                return False, "Authentication failed - session may have expired"

            elif response.status_code == 403:
                return False, "Access denied - CSRF token may be invalid"

            else:
                return False, f"Booking failed with HTTP {response.status_code}: {response.text[:200]}"

        except requests.exceptions.Timeout:
            return False, "Booking request timed out"
        except Exception as e:
            return False, f"API booking error: {str(e)}"

    def book_slot_selenium(self, slot):
        """
        Book a slot at Das Spiel using Selenium browser automation.

        This is the fallback approach when API booking fails.
        Slower but more reliable for complex page interactions.

        Args:
            slot: Dict with keys: date, time, square_id, court_name

        Returns:
            (success, message) tuple
        """
        driver = None
        try:
            date = slot.get('date')
            time_slot = slot.get('time')
            court_name = slot.get('court_name')
            square_id = slot.get('square_id')

            print(f"BOOKING SELENIUM: Starting booking for {court_name} at {time_slot} on {date}", file=sys.stderr, flush=True)

            if not square_id:
                return False, "Missing square_id for Das Spiel booking."

            # Setup Firefox headless
            os.environ['MOZ_HEADLESS'] = '1'
            os.environ['MOZ_DISABLE_CONTENT_SANDBOX'] = '1'

            options = Options()
            options.add_argument('--headless')

            service = Service(
                executable_path='/usr/local/bin/geckodriver',
                log_output='geckodriver.log'
            )

            driver = webdriver.Firefox(service=service, options=options)
            driver.set_page_load_timeout(30)

            # Sign in
            driver.get(self.SIGNIN_URL)
            time.sleep(3)

            email_input = driver.find_element(By.CSS_SELECTOR, "input[type='email']")
            password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")

            email_input.send_keys(self.credentials['username'])
            password_input.send_keys(self.credentials['password'])

            submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_button.click()
            time.sleep(3)

            # Check if login was successful
            if 'signin' in driver.current_url.lower():
                driver.quit()
                return False, "Login failed - check credentials"

            # Navigate to calendar page
            calendar_url = f"{self.URL}?date={date}"
            driver.get(calendar_url)
            time.sleep(3)

            # Find and click the correct slot
            click_script = f"""
                var slots = document.querySelectorAll('a.square-free');
                for (var i = 0; i < slots.length; i++) {{
                    var slot = slots[i];
                    var onclick = slot.getAttribute('onclick') || '';
                    var href = slot.getAttribute('href') || '';
                    if (onclick.includes('{square_id}') || href.includes('{square_id}')) {{
                        slot.click();
                        return true;
                    }}
                }}
                return false;
            """

            clicked = driver.execute_script(click_script)
            if not clicked:
                driver.quit()
                return False, "Could not find time slot on calendar"

            time.sleep(2)

            # Click "Platz mieten" button
            buttons = driver.find_elements(By.TAG_NAME, "button")
            platz_mieten_btn = None
            for btn in buttons:
                if 'platz mieten' in btn.text.strip().lower():
                    platz_mieten_btn = btn
                    break

            if not platz_mieten_btn:
                driver.quit()
                return False, "Could not find 'Platz mieten' button"

            platz_mieten_btn.click()
            time.sleep(3)

            # Check AGB checkboxes
            checkboxes = driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            for cb in checkboxes:
                if not cb.is_selected():
                    try:
                        cb.click()
                    except:
                        cb_id = cb.get_attribute('id')
                        if cb_id:
                            try:
                                label = driver.find_element(By.CSS_SELECTOR, f"label[for='{cb_id}']")
                                label.click()
                            except:
                                pass
                    time.sleep(0.5)

            # Click confirmation button
            buttons = driver.find_elements(By.TAG_NAME, "button")
            confirm_btn = None
            for btn in buttons:
                btn_text = btn.text.lower()
                if 'verbindlich reservieren' in btn_text or 'reservieren' in btn_text:
                    confirm_btn = btn
                    break

            if not confirm_btn:
                driver.quit()
                return False, "Could not find confirmation button"

            confirm_btn.click()
            time.sleep(3)

            # Check for success
            page_source = driver.page_source
            driver.quit()

            if 'square-own-booking' in page_source or 'Ihre Buchung' in page_source:
                return True, f"Successfully booked {court_name} on {date} at {time_slot}"

            if any(ind in page_source.lower() for ind in ['erfolgreich', 'bestätigt', 'reserviert']):
                return True, f"Successfully booked {court_name} on {date} at {time_slot}"

            return True, f"Booking completed for {court_name} on {date} at {time_slot} (please verify)"

        except Exception as e:
            if driver:
                driver.quit()
            return False, f"Selenium booking error: {str(e)}"

    def book_slot(self, slot):
        """
        Book a slot at Das Spiel.

        Tries the fast API approach first, falls back to Selenium if needed.

        Args:
            slot: Dict with keys: date, time, square_id, court_name

        Returns:
            (success, message) tuple
        """
        # Try API approach first (fast, <1 second)
        print(f"BOOKING: Attempting API-based booking...", file=sys.stderr, flush=True)
        success, message = self.book_slot_api(slot)

        if success:
            return success, message

        # If API failed, check if it's a recoverable error
        print(f"BOOKING: API booking failed: {message}", file=sys.stderr, flush=True)

        # Don't retry with Selenium for certain errors
        non_retryable = ['Missing square_id', 'No credentials', 'Validation error']
        if any(err in message for err in non_retryable):
            return False, message

        # Fall back to Selenium approach
        print(f"BOOKING: Falling back to Selenium-based booking...", file=sys.stderr, flush=True)
        return self.book_slot_selenium(slot)


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

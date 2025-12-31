"""Booking functionality for tennis courts."""

import json
import os
import re
import time
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
        """Sign in to Das Spiel using the /signin endpoint."""
        if not self.credentials:
            return False, "No credentials found"

        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

            # Get signin page for CSRF token
            response = self.session.get(self.SIGNIN_URL, headers=headers, timeout=10)

            # Parse CSRF token
            soup = BeautifulSoup(response.content, 'html.parser')
            csrf_meta = soup.find('meta', {'name': 'csrf-token'})
            csrf_token = csrf_meta['content'] if csrf_meta else None

            # Sign in with correct field names: 'email' and 'pw'
            signin_data = {
                'email': self.credentials['username'],
                'pw': self.credentials['password']  # Note: 'pw' not 'password'
            }

            headers['Referer'] = self.SIGNIN_URL
            headers['Content-Type'] = 'application/json'
            headers['Accept'] = 'application/json'
            if csrf_token:
                headers['X-CSRF-TOKEN'] = csrf_token

            response = self.session.post(self.SIGNIN_URL, json=signin_data, headers=headers, timeout=10, allow_redirects=False)

            # Check for success - Das Spiel returns plain text "signed-in"
            if response.status_code == 200 and response.text == 'signed-in':
                return True, "Login successful"
            else:
                return False, f"Login failed: {response.text}"

        except Exception as e:
            return False, f"Login error: {str(e)}"

    def book_slot(self, slot):
        """
        Book a slot at Das Spiel using Selenium browser automation.

        Process:
        1. Start headless Firefox
        2. Sign in
        3. Navigate to calendar for the date
        4. Find and click the matching time slot
        5. Click "Platz mieten" button
        6. Check AGB checkbox
        7. Click "Verbindlich Reservieren"
        8. Verify success
        """
        driver = None
        try:
            # Extract slot details
            date = slot.get('date')
            time_slot = slot.get('time')
            court_name = slot.get('court_name')

            # Setup Firefox (using Bankcomparison working pattern)
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

            # Navigate to calendar
            calendar_url = f"{self.URL}?date={date}"
            driver.get(calendar_url)
            time.sleep(3)

            # Find all free slots
            free_slots = driver.find_elements(By.CSS_SELECTOR, "a.square-free")

            if not free_slots:
                driver.quit()
                return False, "No free slots available"

            # Try to find the slot matching the time
            target_slot = None
            for slot_elem in free_slots:
                slot_time = slot_elem.get_attribute('data-time')
                if slot_time and time_slot in slot_time:
                    target_slot = slot_elem
                    break

            # If no exact match, use first available
            if not target_slot:
                target_slot = free_slots[0]

            # Click on the slot
            target_slot.click()
            time.sleep(2)

            # Look for "Platz mieten" button
            buttons = driver.find_elements(By.TAG_NAME, "button")
            platz_mieten_btn = None
            for btn in buttons:
                if 'platz mieten' in btn.text.lower():
                    platz_mieten_btn = btn
                    break

            if not platz_mieten_btn:
                driver.quit()
                return False, "Could not find 'Platz mieten' button"

            # Click "Platz mieten"
            platz_mieten_btn.click()
            time.sleep(3)

            # Check AGB checkboxes
            checkboxes = driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            for cb in checkboxes:
                if not cb.is_selected():
                    try:
                        cb.click()
                    except:
                        # If checkbox not clickable, try label
                        cb_id = cb.get_attribute('id')
                        if cb_id:
                            try:
                                label = driver.find_element(By.CSS_SELECTOR, f"label[for='{cb_id}']")
                                label.click()
                            except:
                                pass
                    time.sleep(0.5)

            # Look for confirmation button
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

            # Click confirmation
            confirm_btn.click()
            time.sleep(3)

            # Check for success
            page_source = driver.page_source

            # Success indicator: slot now shows "Ihre Buchung" (Your booking)
            if 'square-own-booking' in page_source or 'Ihre Buchung' in page_source:
                driver.quit()
                return True, f"Successfully booked {court_name} on {date} at {time_slot}"

            # Check for other success indicators
            if any(indicator in page_source.lower() for indicator in ['erfolgreich', 'bestätigt', 'reserviert']):
                driver.quit()
                return True, f"Successfully booked {court_name} on {date} at {time_slot}"

            # If no clear success indicator, assume success (user will verify)
            driver.quit()
            return True, f"Booking completed for {court_name} on {date} at {time_slot} (please verify)"

        except Exception as e:
            if driver:
                driver.quit()
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

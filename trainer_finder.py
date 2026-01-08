"""Trainer finder module for Das Spiel tennis center."""

import json
import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class TrainerFinder:
    """Finds available trainers at Das Spiel tennis center."""

    BASE_URL = "https://reservierung.dasspiel.at"
    BOOKING_DATA_URL = f"{BASE_URL}/calendar/booking-data/"

    def __init__(self):
        """Initialize trainer finder with session and credentials."""
        self.session = requests.Session()
        self.credentials = self._load_credentials()
        self.token = None

    def _load_credentials(self) -> Dict:
        """Load credentials from credentials.json file."""
        if os.path.exists('credentials.json'):
            try:
                with open('credentials.json', 'r') as f:
                    data = json.load(f)
                    return data.get('dasspiel', {})
            except Exception as e:
                print(f"Error loading credentials: {e}")
        return {}

    def _get_auth_token(self) -> Optional[str]:
        """Authenticate and get auth token."""
        if not self.credentials:
            print("No credentials found for Das Spiel")
            return None

        try:
            signin_url = f"{self.BASE_URL}/signin"

            # Get CSRF token first
            response = self.session.get(signin_url, timeout=10)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            csrf_meta = soup.find('meta', {'name': 'csrf-token'})
            csrf_token = csrf_meta['content'] if csrf_meta else None

            # Sign in
            signin_data = {
                'email': self.credentials.get('username'),
                'pw': self.credentials.get('password')
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Referer': signin_url
            }

            if csrf_token:
                headers['X-CSRF-TOKEN'] = csrf_token

            response = self.session.post(
                signin_url,
                json=signin_data,
                headers=headers,
                timeout=10,
                allow_redirects=False
            )

            if response.status_code == 200 and response.text == 'signed-in':
                # Token is in cookies - extract it
                for cookie in self.session.cookies:
                    if 'token' in cookie.name.lower() or 'session' in cookie.name.lower():
                        self.token = cookie.value
                        return self.token
                # If no specific token cookie, just use session cookies
                return "authenticated"
            else:
                print(f"Authentication failed: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"Error during authentication: {e}")
            return None

    def _get_court_ids(self) -> List[str]:
        """Get list of court IDs from Das Spiel."""
        try:
            # Fetch the main page to get court data
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = self.session.get(self.BASE_URL, headers=headers, timeout=10)

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract calendar data from meta tag
            calendar_meta = soup.find('meta', {'id': 'transfer-data-calendar'})
            if calendar_meta and calendar_meta.get('data-content'):
                calendar_json = calendar_meta['data-content'].replace('&quot;', '"')
                calendar_data = json.loads(calendar_json)

                # Extract court IDs (UUIDs)
                court_ids = [court.get('uuid') for court in calendar_data if court.get('uuid')]
                return court_ids[:5]  # Limit to first 5 courts to avoid overloading

        except Exception as e:
            print(f"Error getting court IDs: {e}")

        # Return a default court ID from the example
        return ["3c3895e4-111f-4387-b815-7506ffe26607"]

    def find_trainers(
        self,
        date: datetime,
        start_time: str,
        end_time: str,
        trainer_name: Optional[str] = None
    ) -> List[Dict]:
        """
        Find available trainers for the given date and time range.

        Args:
            date: Date to search for trainers
            start_time: Start time (HH:MM format)
            end_time: End time (HH:MM format)
            trainer_name: Optional specific trainer name to filter by

        Returns:
            List of trainer availability slots
        """
        # Authenticate first
        if not self._get_auth_token():
            print("Authentication failed - cannot fetch trainer data")
            return []

        all_trainer_slots = []
        court_ids = self._get_court_ids()

        # Parse start and end times
        start_hour = int(start_time.split(':')[0])
        end_hour = int(end_time.split(':')[0])

        print(f"\nSearching for trainers on {date.strftime('%Y-%m-%d')} from {start_time} to {end_time}")
        print(f"Checking {len(court_ids)} courts...")

        # To avoid making too many requests, we'll check every 2 hours
        for hour in range(start_hour, end_hour, 2):
            time_str = f"{hour:02d}:00"

            for court_id in court_ids:
                try:
                    # Add small delay to avoid rate limiting
                    import time
                    time.sleep(0.3)

                    trainer_data = self._fetch_trainer_data(
                        date=date,
                        time_start=time_str,
                        court_id=court_id
                    )

                    if trainer_data:
                        # Filter by trainer name if specified
                        if trainer_name:
                            trainer_data = self._filter_by_trainer_name(trainer_data, trainer_name)

                        all_trainer_slots.extend(trainer_data)

                except Exception as e:
                    print(f"Error fetching trainer data for court {court_id} at {time_str}: {e}")
                    continue

        # Remove duplicates based on time_start, time_end, and trainer names
        unique_slots = self._deduplicate_slots(all_trainer_slots)

        print(f"Found {len(unique_slots)} unique trainer slots")
        return unique_slots

    def _fetch_trainer_data(
        self,
        date: datetime,
        time_start: str,
        court_id: str
    ) -> List[Dict]:
        """Fetch trainer data from the booking API."""
        try:
            params = {
                'date': date.strftime('%Y-%m-%d'),
                'time_start': time_start,
                'square_id': court_id,
                'is_half_hour': 0
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': self.BASE_URL,
                'Accept': 'application/json'
            }

            response = self.session.get(
                self.BOOKING_DATA_URL,
                params=params,
                headers=headers,
                timeout=10
            )

            if response.status_code != 200:
                return []

            data = response.json()

            # Check if request was successful
            if data.get('status') != 1:
                return []

            booking_data = data.get('data', {})
            trainer_data = booking_data.get('trainer_data', [])
            square_name = booking_data.get('square_name', 'Unknown Court')

            # Process trainer data
            processed_slots = []
            for slot in trainer_data:
                trainers_list = slot.get('trainers', [])
                if trainers_list:  # Only include if trainers are available
                    processed_slots.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'day_of_week': date.strftime('%A'),
                        'time_start': slot.get('time_start'),
                        'time_end': slot.get('time_end'),
                        'price': slot.get('price'),
                        'court_name': square_name,
                        'trainers': trainers_list,
                        'venue': 'Tenniszentrum Arsenal (Das Spiel)'
                    })

            return processed_slots

        except Exception as e:
            print(f"Error in _fetch_trainer_data: {e}")
            return []

    def _filter_by_trainer_name(self, trainer_slots: List[Dict], trainer_name: str) -> List[Dict]:
        """Filter trainer slots by specific trainer name."""
        filtered_slots = []
        trainer_name_lower = trainer_name.lower()

        for slot in trainer_slots:
            # Filter trainers list
            matching_trainers = [
                t for t in slot.get('trainers', [])
                if trainer_name_lower in t.get('name', '').lower()
            ]

            if matching_trainers:
                # Create new slot with filtered trainers
                filtered_slot = slot.copy()
                filtered_slot['trainers'] = matching_trainers
                filtered_slots.append(filtered_slot)

        return filtered_slots

    def _deduplicate_slots(self, slots: List[Dict]) -> List[Dict]:
        """Remove duplicate trainer slots."""
        seen = set()
        unique_slots = []

        for slot in slots:
            # Create a unique key based on time window
            key = (
                slot['time_start'],
                slot['time_end'],
                tuple(sorted([t['name'] for t in slot.get('trainers', [])]))
            )

            if key not in seen:
                seen.add(key)
                unique_slots.append(slot)

        return unique_slots


def find_trainers(date: datetime, start_time: str, end_time: str, trainer_name: Optional[str] = None) -> List[Dict]:
    """
    Convenience function to find available trainers.

    Args:
        date: Date to search
        start_time: Start time (HH:MM)
        end_time: End time (HH:MM)
        trainer_name: Optional trainer name filter

    Returns:
        List of available trainer slots
    """
    finder = TrainerFinder()
    return finder.find_trainers(date, start_time, end_time, trainer_name)

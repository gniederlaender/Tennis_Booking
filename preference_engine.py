"""Preference learning engine that learns from user selections."""

import json
import os
from datetime import datetime
from collections import Counter
from config import PREFERENCES_FILE, CONFIDENCE_THRESHOLD


class PreferenceEngine:
    """Learns and predicts user preferences for tennis court bookings."""

    def __init__(self, preferences_file=PREFERENCES_FILE):
        self.preferences_file = preferences_file
        self.selections = []
        self.load_preferences()

    def load_preferences(self):
        """Load user selection history from JSON file."""
        if os.path.exists(self.preferences_file):
            try:
                with open(self.preferences_file, 'r') as f:
                    data = json.load(f)
                    self.selections = data.get('selections', [])
            except Exception as e:
                print(f"Error loading preferences: {e}")
                self.selections = []
        else:
            self.selections = []

    def save_preferences(self):
        """Save user selection history to JSON file."""
        data = {
            'selections': self.selections,
            'last_updated': datetime.now().isoformat()
        }
        try:
            with open(self.preferences_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving preferences: {e}")

    def log_selection(self, slot):
        """
        Log a user's court selection.

        Args:
            slot: dict with venue, date, time, price, etc.
        """
        selection = {
            'timestamp': datetime.now().isoformat(),
            'venue': slot.get('venue'),
            'date': slot.get('date'),
            'time': slot.get('time'),
            'day_of_week': slot.get('day_of_week'),
            'time_of_day': self._categorize_time_of_day(slot.get('time')),
            'price': slot.get('price'),
            'court_type': slot.get('court_type'),
            'location': slot.get('location'),
            'indoor_outdoor': slot.get('indoor_outdoor')
        }

        self.selections.append(selection)
        self.save_preferences()

    def _categorize_time_of_day(self, time_str):
        """Categorize time into morning/afternoon/evening."""
        if not time_str:
            return 'unknown'

        try:
            hour = int(time_str.split(':')[0])
            if hour < 12:
                return 'morning'
            elif hour < 17:
                return 'afternoon'
            else:
                return 'evening'
        except:
            return 'unknown'

    def has_confidence(self):
        """Check if we have enough data to make confident predictions."""
        return len(self.selections) >= CONFIDENCE_THRESHOLD

    def get_preferred_slot(self, available_slots):
        """
        Predict the preferred slot from available options.

        Returns:
            dict with preferred slot or None if not confident
        """
        if not self.has_confidence() or not available_slots:
            return None

        # Calculate scores for each slot based on historical preferences
        scored_slots = []

        for slot in available_slots:
            score = self._calculate_preference_score(slot)
            scored_slots.append((score, slot))

        # Sort by score (highest first)
        scored_slots.sort(reverse=True, key=lambda x: x[0])

        # Return the top-scored slot
        return scored_slots[0][1] if scored_slots else None

    def _calculate_preference_score(self, slot):
        """Calculate preference score for a slot based on history."""
        score = 0.0

        # Extract preferences from history
        venue_counts = Counter(s['venue'] for s in self.selections if s.get('venue'))
        time_of_day_counts = Counter(s['time_of_day'] for s in self.selections if s.get('time_of_day'))
        day_of_week_counts = Counter(s['day_of_week'] for s in self.selections if s.get('day_of_week'))

        # Venue preference (weight: 3)
        if slot.get('venue') in venue_counts:
            venue_score = venue_counts[slot['venue']] / len(self.selections)
            score += venue_score * 3

        # Time of day preference (weight: 2)
        slot_time_category = self._categorize_time_of_day(slot.get('time'))
        if slot_time_category in time_of_day_counts:
            time_score = time_of_day_counts[slot_time_category] / len(self.selections)
            score += time_score * 2

        # Day of week preference (weight: 1.5)
        if slot.get('day_of_week') in day_of_week_counts:
            day_score = day_of_week_counts[slot['day_of_week']] / len(self.selections)
            score += day_score * 1.5

        # Price preference (weight: 1) - prefer similar prices
        avg_price = self._get_average_price()
        if avg_price and slot.get('price'):
            try:
                slot_price = float(slot['price'])
                price_diff = abs(slot_price - avg_price)
                # Lower difference = higher score
                price_score = max(0, 1 - (price_diff / avg_price))
                score += price_score
            except:
                pass

        return score

    def _get_average_price(self):
        """Calculate average price from selections."""
        prices = []
        for s in self.selections:
            if s.get('price'):
                try:
                    prices.append(float(s['price']))
                except:
                    pass

        return sum(prices) / len(prices) if prices else None

    def get_preference_summary(self):
        """Get a summary of learned preferences."""
        if not self.selections:
            return "No preferences learned yet."

        venue_counts = Counter(s['venue'] for s in self.selections if s.get('venue'))
        time_counts = Counter(s['time_of_day'] for s in self.selections if s.get('time_of_day'))
        day_counts = Counter(s['day_of_week'] for s in self.selections if s.get('day_of_week'))

        summary = f"Learned from {len(self.selections)} selections:\n"
        summary += f"  Favorite venues: {', '.join(v for v, _ in venue_counts.most_common(3))}\n"
        summary += f"  Preferred time: {', '.join(t for t, _ in time_counts.most_common(2))}\n"
        summary += f"  Preferred days: {', '.join(d for d, _ in day_counts.most_common(3))}\n"

        return summary

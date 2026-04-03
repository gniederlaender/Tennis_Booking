"""Natural language parser for timeframe specifications with German support."""

import re
from datetime import datetime, timedelta
import dateparser


class TimeframeParser:
    """Parses natural language timeframe specifications in German and English."""

    # German weekdays mapping
    GERMAN_WEEKDAYS = {
        'montag': 0, 'dienstag': 1, 'mittwoch': 2, 'donnerstag': 3,
        'freitag': 4, 'samstag': 5, 'sonntag': 6
    }

    # English weekdays mapping
    ENGLISH_WEEKDAYS = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6
    }

    # German relative date terms
    GERMAN_RELATIVE = {
        'heute': 0,
        'morgen': 1,
        'übermorgen': 2,
        'nächste woche': 7
    }

    # German time of day expressions
    GERMAN_TIME_WINDOWS = {
        'früh': ('07:00', '09:00'),
        'vormittag': ('09:00', '12:00'),
        'morgens': ('09:00', '12:00'),
        'mittag': ('12:00', '14:00'),
        'nachmittag': ('14:00', '18:00'),
        'abend': ('18:00', '21:00')
    }

    # English time of day expressions
    ENGLISH_TIME_WINDOWS = {
        'early': ('07:00', '09:00'),
        'morning': ('09:00', '12:00'),
        'noon': ('12:00', '14:00'),
        'afternoon': ('14:00', '18:00'),
        'evening': ('18:00', '21:00')
    }

    def __init__(self):
        self.today = datetime.now()

    def parse(self, text):
        """
        Parse natural language timeframe specification.

        Returns:
            dict with 'date', 'start_time', 'end_time'
        """
        text = text.lower().strip()

        # Normalize input
        text = self._normalize_input(text)

        # Try to extract date
        date_obj = self._extract_date(text)

        # Try to extract time range
        start_time, end_time = self._extract_time_range(text)

        return {
            'date': date_obj,
            'start_time': start_time,
            'end_time': end_time
        }

    def _normalize_input(self, text):
        """Normalize input text to handle mobile keyboard variations."""
        # Replace smart/curly quotes with straight quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        text = text.replace('„', '"').replace('"', '"')

        # Replace various dash characters with standard hyphen
        text = text.replace('–', '-')
        text = text.replace('—', '-')
        text = text.replace('−', '-')

        # Replace non-breaking spaces with regular spaces
        text = text.replace('\u00A0', ' ')
        text = text.replace('\u202F', ' ')

        # Normalize multiple spaces to single space
        text = re.sub(r'\s+', ' ', text)

        return text

    def _extract_date(self, text):
        """Extract date from text with German and English support."""

        # Check for explicit date formats first
        date_patterns = [
            r'(\d{1,2})[./](\d{1,2})[./](\d{4})',  # DD.MM.YYYY or DD/MM/YYYY
            r'(\d{4})-(\d{1,2})-(\d{1,2})'  # YYYY-MM-DD
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    if '/' in match.group(0) or '.' in match.group(0):
                        day, month, year = match.groups()
                        return datetime(int(year), int(month), int(day))
                    else:
                        year, month, day = match.groups()
                        return datetime(int(year), int(month), int(day))
                except ValueError:
                    pass

        # Check for German relative dates
        for term, days_ahead in self.GERMAN_RELATIVE.items():
            if term in text:
                return self.today + timedelta(days=days_ahead)

        # Check for English relative dates
        if 'today' in text:
            return self.today
        elif 'tomorrow' in text:
            return self.today + timedelta(days=1)
        elif 'next week' in text:
            return self.today + timedelta(days=7)

        # Check for German weekdays
        for weekday_name, weekday_num in self.GERMAN_WEEKDAYS.items():
            if weekday_name in text:
                days_ahead = weekday_num - self.today.weekday()
                if days_ahead <= 0:
                    if 'nächste' in text or 'nächster' in text or 'nächsten' in text:
                        days_ahead += 7
                    else:
                        days_ahead += 7  # Default to next week
                return self.today + timedelta(days=days_ahead)

        # Check for English weekdays
        for weekday_name, weekday_num in self.ENGLISH_WEEKDAYS.items():
            if weekday_name in text:
                days_ahead = weekday_num - self.today.weekday()
                if days_ahead <= 0:
                    if 'next' in text:
                        days_ahead += 7
                    else:
                        days_ahead += 7
                return self.today + timedelta(days=days_ahead)

        # Try dateparser as fallback with German and English support
        try:
            parsed_date = dateparser.parse(
                text,
                languages=['de', 'en'],
                settings={
                    'PREFER_DATES_FROM': 'future',
                    'RETURN_AS_TIMEZONE_AWARE': False,
                    'PREFER_LOCALE_DATE_ORDER': True
                }
            )
            if parsed_date:
                return parsed_date
        except:
            pass

        # Default to today if no date found
        return self.today

    def _extract_time_range(self, text):
        """Extract time range from text with German and English support."""

        # Check for German time windows
        for window_name, (start, end) in self.GERMAN_TIME_WINDOWS.items():
            if window_name in text:
                return (start, end)

        # Check for English time windows
        for window_name, (start, end) in self.ENGLISH_TIME_WINDOWS.items():
            if window_name in text:
                return (start, end)

        # Check for "at HH:MM" or "um HH:MM" pattern
        at_patterns = [
            r'\b(?:at|um)\s+(\d{1,2}):(\d{2})',
            r'\b(?:at|um)\s+(\d{1,2})\s*(?:uhr)?'
        ]

        for pattern in at_patterns:
            at_match = re.search(pattern, text)
            if at_match:
                hour = int(at_match.group(1))
                minute = at_match.group(2) if len(at_match.groups()) > 1 and at_match.group(2) else "00"
                start = f"{hour:02d}:{minute}"
                end_hour = (hour + 1) % 24
                end = f"{end_hour:02d}:{minute}"
                return (start, end)

        # Pattern for time ranges like "10-13", "15:00-18:00", "6pm-8pm"
        time_patterns = [
            # HH:MM-HH:MM (24-hour format)
            r'(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})',
            # H-H format (most common)
            r'(\d{1,2})\s*-\s*(\d{1,2})(?:\s*uhr)?',
            # H:MM pm/am - H:MM pm/am
            r'(\d{1,2}):(\d{2})\s*(pm|am)?\s*-\s*(\d{1,2}):(\d{2})\s*(pm|am)?'
        ]

        for pattern in time_patterns:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()

                # Handle different formats
                if len(groups) == 4 and groups[2] and groups[3]:
                    # HH:MM-HH:MM
                    start_hour, start_min, end_hour, end_min = groups
                    return (
                        f"{int(start_hour):02d}:{int(start_min):02d}",
                        f"{int(end_hour):02d}:{int(end_min):02d}"
                    )
                elif len(groups) == 2:
                    # Simple H-H format
                    start_hour = int(groups[0])
                    end_hour = int(groups[1])
                    return (
                        f"{start_hour:02d}:00",
                        f"{end_hour:02d}:00"
                    )
                elif len(groups) >= 6:
                    # H:MM am/pm - H:MM am/pm
                    start_hour = int(groups[0])
                    start_min = groups[1]
                    start_period = groups[2]
                    end_hour = int(groups[3])
                    end_min = groups[4]
                    end_period = groups[5]

                    if start_period == 'pm' and start_hour != 12:
                        start_hour += 12
                    if end_period == 'pm' and end_hour != 12:
                        end_hour += 12

                    return (
                        f"{start_hour:02d}:{start_min}",
                        f"{end_hour:02d}:{end_min}"
                    )

        # Check for "zwischen X und Y" (German) or "between X and Y" (English)
        between_pattern = r'(?:zwischen|between)\s+(\d{1,2}):?(\d{2})?\s+(?:und|and)\s+(\d{1,2}):?(\d{2})?'
        between_match = re.search(between_pattern, text)
        if between_match:
            groups = between_match.groups()
            start_hour = int(groups[0])
            start_min = groups[1] if groups[1] else "00"
            end_hour = int(groups[2])
            end_min = groups[3] if groups[3] else "00"

            return (
                f"{start_hour:02d}:{start_min}",
                f"{end_hour:02d}:{end_min}"
            )

        # Check for "ab HH:MM" or "from HH:MM" (open-ended)
        from_pattern = r'(?:ab|from)\s+(\d{1,2}):?(\d{2})?'
        from_match = re.search(from_pattern, text)
        if from_match:
            start_hour = int(from_match.group(1))
            start_min = from_match.group(2) if from_match.group(2) else "00"
            return (
                f"{start_hour:02d}:{start_min}",
                "21:00"  # Default end time
            )

        # Default time range (7am - 9pm)
        return ("07:00", "21:00")

    def format_datetime(self, date_obj, time_str):
        """Combine date and time into a datetime object."""
        hour, minute = map(int, time_str.split(':'))
        return date_obj.replace(hour=hour, minute=minute, second=0, microsecond=0)


if __name__ == "__main__":
    # Test the parser with German and English examples
    parser = TimeframeParser()

    test_cases = [
        # German examples
        "morgen zwischen 10 und 13",
        "nächsten Dienstag 18-20 Uhr",
        "Samstag Nachmittag",
        "heute ab 17 Uhr",
        "übermorgen früh",
        "Freitag 15:00-18:00",
        # English examples
        "next monday 6-8pm",
        "tomorrow 10:00-12:00",
        "friday evening",
        "today 9-11"
    ]

    for test in test_cases:
        result = parser.parse(test)
        print(f"Input: {test}")
        print(f"Date: {result['date'].strftime('%Y-%m-%d %A')}")
        print(f"Time: {result['start_time']} - {result['end_time']}")
        print()

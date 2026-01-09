"""Simple natural language parser for timeframe specifications."""

import re
from datetime import datetime, timedelta
from dateutil import parser as date_parser


class TimeframeParser:
    """Parses natural language timeframe specifications."""

    WEEKDAYS = {
        'monday': 0, 'mon': 0,
        'tuesday': 1, 'tue': 1,
        'wednesday': 2, 'wed': 2,
        'thursday': 3, 'thu': 3,
        'friday': 4, 'fri': 4,
        'saturday': 5, 'sat': 5,
        'sunday': 6, 'sun': 6
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

        # Normalize input to handle mobile keyboard smart characters
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
        text = text.replace('"', '"').replace('"', '"')  # Curly double quotes
        text = text.replace(''', "'").replace(''', "'")  # Curly single quotes
        text = text.replace('„', '"').replace('"', '"')  # German quotes

        # Replace various dash characters with standard hyphen
        text = text.replace('–', '-')  # En dash
        text = text.replace('—', '-')  # Em dash
        text = text.replace('−', '-')  # Minus sign

        # Replace non-breaking spaces with regular spaces
        text = text.replace('\u00A0', ' ')  # Non-breaking space
        text = text.replace('\u202F', ' ')  # Narrow no-break space

        # Normalize multiple spaces to single space
        import re
        text = re.sub(r'\s+', ' ', text)

        return text

    def _extract_date(self, text):
        """Extract date from text."""
        # Check for explicit date formats (DD.MM.YYYY, DD/MM/YYYY, YYYY-MM-DD)
        date_patterns = [
            r'(\d{1,2})[./](\d{1,2})[./](\d{4})',  # DD.MM.YYYY or DD/MM/YYYY
            r'(\d{4})-(\d{1,2})-(\d{1,2})'  # YYYY-MM-DD
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    if '/' in match.group(0) or '.' in match.group(0):
                        # DD.MM.YYYY or DD/MM/YYYY
                        day, month, year = match.groups()
                        return datetime(int(year), int(month), int(day))
                    else:
                        # YYYY-MM-DD
                        year, month, day = match.groups()
                        return datetime(int(year), int(month), int(day))
                except ValueError:
                    pass

        # Check for relative dates
        if 'today' in text:
            return self.today
        elif 'tomorrow' in text:
            return self.today + timedelta(days=1)
        elif 'next week' in text:
            return self.today + timedelta(days=7)

        # Check for specific weekday patterns
        for weekday_name, weekday_num in self.WEEKDAYS.items():
            if weekday_name in text:
                days_ahead = weekday_num - self.today.weekday()
                if days_ahead <= 0:  # Target day already happened this week
                    if 'next' in text:
                        days_ahead += 7
                    else:
                        days_ahead += 7  # Default to next week
                return self.today + timedelta(days=days_ahead)

        # Default to today if no date found
        return self.today

    def _extract_time_range(self, text):
        """Extract time range from text."""
        # Check for "at HH:MM" pattern first (specific single time)
        at_pattern = r'\bat\s+(\d{1,2}):(\d{2})'
        at_match = re.search(at_pattern, text)
        if at_match:
            hour = int(at_match.group(1))
            minute = at_match.group(2)
            start = f"{hour:02d}:{minute}"
            # For "at X", show X to X+1 hour
            end_hour = (hour + 1) % 24
            end = f"{end_hour:02d}:{minute}"
            return (start, end)

        # Pattern for time ranges like "6-8pm", "15:00-18:00", "6pm-8pm"
        time_patterns = [
            # HH:MM-HH:MM (24-hour format)
            r'(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})',
            # H-H with optional pm/am
            r'(\d{1,2})\s*-\s*(\d{1,2})\s*(pm|am)?',
            # H:MM pm/am - H:MM pm/am
            r'(\d{1,2}):(\d{2})\s*(pm|am)?\s*-\s*(\d{1,2}):(\d{2})\s*(pm|am)?'
        ]

        for pattern in time_patterns:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()

                # Handle different formats
                if ':' in match.group(0):
                    # HH:MM format
                    if len(groups) == 4 and groups[2] and groups[3]:
                        # HH:MM-HH:MM
                        start_hour, start_min, end_hour, end_min = groups
                        return (
                            f"{int(start_hour):02d}:{int(start_min):02d}",
                            f"{int(end_hour):02d}:{int(end_min):02d}"
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
                else:
                    # Simple H-H format
                    start_hour = int(groups[0])
                    end_hour = int(groups[1])
                    period = groups[2] if len(groups) > 2 else None

                    if period == 'pm':
                        if start_hour != 12:
                            start_hour += 12
                        if end_hour != 12:
                            end_hour += 12

                    return (
                        f"{start_hour:02d}:00",
                        f"{end_hour:02d}:00"
                    )

        # Check for "between X and Y" pattern
        between_match = re.search(r'between\s+(\d{1,2}):?(\d{2})?\s+and\s+(\d{1,2}):?(\d{2})?', text)
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

        # Default time range (9am - 9pm)
        return ("09:00", "21:00")

    def format_datetime(self, date_obj, time_str):
        """Combine date and time into a datetime object."""
        hour, minute = map(int, time_str.split(':'))
        return date_obj.replace(hour=hour, minute=minute, second=0, microsecond=0)


if __name__ == "__main__":
    # Test the parser
    parser = TimeframeParser()

    test_cases = [
        "next monday 6-8pm",
        "7.1.2026 between 15:00 and 18:00",
        "tomorrow 10:00-12:00",
        "friday evening 18-20",
        "today 9-11"
    ]

    for test in test_cases:
        result = parser.parse(test)
        print(f"Input: {test}")
        print(f"Result: {result}")
        print()

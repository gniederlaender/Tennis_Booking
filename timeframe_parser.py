"""Natural language parser for timeframe specifications with German support."""

import re
from datetime import datetime, timedelta
import dateparser


class TimeframeParser:
    """Parses natural language timeframe specifications in German and English."""

    # German weekdays mapping (full and abbreviated)
    GERMAN_WEEKDAYS = {
        'montag': 0, 'mo': 0,
        'dienstag': 1, 'di': 1,
        'mittwoch': 2, 'mi': 2,
        'donnerstag': 3, 'do': 3,
        'freitag': 4, 'fr': 4,
        'samstag': 5, 'sa': 5,
        'sonntag': 6, 'so': 6
    }

    # English weekdays mapping (full and abbreviated)
    ENGLISH_WEEKDAYS = {
        'monday': 0, 'mon': 0,
        'tuesday': 1, 'tue': 1, 'tues': 1,
        'wednesday': 2, 'wed': 2,
        'thursday': 3, 'thu': 3, 'thur': 3, 'thurs': 3,
        'friday': 4, 'fri': 4,
        'saturday': 5, 'sat': 5,
        'sunday': 6, 'sun': 6
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
        'früh': ('08:00', '10:00'),
        'vormittag': ('09:00', '12:00'),
        'morgens': ('08:00', '11:00'),
        'mittag': ('12:00', '14:00'),
        'nachmittag': ('14:00', '18:00'),
        'abend': ('18:00', '21:00')
    }

    # English time of day expressions
    ENGLISH_TIME_WINDOWS = {
        'early': ('08:00', '10:00'),
        'morning': ('08:00', '11:00'),
        'noon': ('12:00', '14:00'),
        'afternoon': ('14:00', '18:00'),
        'evening': ('18:00', '21:00')
    }

    # German month names
    GERMAN_MONTHS = {
        'januar': 1, 'jan': 1, 'jänner': 1,
        'februar': 2, 'feb': 2,
        'märz': 3, 'mar': 3, 'mär': 3,
        'april': 4, 'apr': 4,
        'mai': 5,
        'juni': 6, 'jun': 6,
        'juli': 7, 'jul': 7,
        'august': 8, 'aug': 8,
        'september': 9, 'sep': 9, 'sept': 9,
        'oktober': 10, 'okt': 10,
        'november': 11, 'nov': 11,
        'dezember': 12, 'dez': 12
    }

    # English month names
    ENGLISH_MONTHS = {
        'january': 1, 'jan': 1,
        'february': 2, 'feb': 2,
        'march': 3, 'mar': 3,
        'april': 4, 'apr': 4,
        'may': 5,
        'june': 6, 'jun': 6,
        'july': 7, 'jul': 7,
        'august': 8, 'aug': 8,
        'september': 9, 'sep': 9, 'sept': 9,
        'october': 10, 'oct': 10,
        'november': 11, 'nov': 11,
        'december': 12, 'dec': 12
    }

    def __init__(self):
        self.today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    def parse(self, text):
        """
        Parse natural language timeframe specification.

        Returns:
            dict with 'date', 'start_time', 'end_time'
        """
        text = text.lower().strip()

        # Normalize input
        text = self._normalize_input(text)

        # Try to extract time range first (before date parsing modifies text understanding)
        start_time, end_time = self._extract_time_range(text)

        # Try to extract date
        date_obj = self._extract_date(text)

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

        # Check for "in X Tagen/days" pattern first
        in_days_pattern = r'in\s+(\d+)\s+(?:tagen?|days?)'
        in_days_match = re.search(in_days_pattern, text)
        if in_days_match:
            days = int(in_days_match.group(1))
            return self.today + timedelta(days=days)

        # Check for ISO format YYYY-MM-DD
        iso_pattern = r'(\d{4})-(\d{1,2})-(\d{1,2})'
        iso_match = re.search(iso_pattern, text)
        if iso_match:
            try:
                year, month, day = iso_match.groups()
                return datetime(int(year), int(month), int(day))
            except ValueError:
                pass

        # Check for European date format DD.MM.YYYY or DD.MM.
        eu_full_pattern = r'(\d{1,2})\.(\d{1,2})\.(\d{4})'
        eu_full_match = re.search(eu_full_pattern, text)
        if eu_full_match:
            try:
                day, month, year = eu_full_match.groups()
                return datetime(int(year), int(month), int(day))
            except ValueError:
                pass

        # Check for European date format DD.MM. (without year)
        eu_short_pattern = r'(\d{1,2})\.(\d{1,2})\.'
        eu_short_match = re.search(eu_short_pattern, text)
        if eu_short_match:
            try:
                day, month = eu_short_match.groups()
                year = self.today.year
                target_date = datetime(year, int(month), int(day))
                # If date is in the past, assume next year
                if target_date < self.today:
                    target_date = datetime(year + 1, int(month), int(day))
                return target_date
            except ValueError:
                pass

        # Check for "DD. Month" or "DD Month" pattern (German/English)
        day_month_pattern = r'(\d{1,2})\.?\s*(' + '|'.join(
            list(self.GERMAN_MONTHS.keys()) + list(self.ENGLISH_MONTHS.keys())
        ) + r')\.?'
        day_month_match = re.search(day_month_pattern, text)
        if day_month_match:
            try:
                day = int(day_month_match.group(1))
                month_name = day_month_match.group(2)
                month = self.GERMAN_MONTHS.get(month_name) or self.ENGLISH_MONTHS.get(month_name)
                if month:
                    year = self.today.year
                    target_date = datetime(year, month, day)
                    if target_date < self.today:
                        target_date = datetime(year + 1, month, day)
                    return target_date
            except ValueError:
                pass

        # Check for "Month DD" or "Month DDth" pattern (English style)
        month_day_pattern = r'(' + '|'.join(self.ENGLISH_MONTHS.keys()) + r')\s+(\d{1,2})(?:st|nd|rd|th)?'
        month_day_match = re.search(month_day_pattern, text)
        if month_day_match:
            try:
                month_name = month_day_match.group(1)
                day = int(month_day_match.group(2))
                month = self.ENGLISH_MONTHS.get(month_name)
                if month:
                    year = self.today.year
                    target_date = datetime(year, month, day)
                    if target_date < self.today:
                        target_date = datetime(year + 1, month, day)
                    return target_date
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

        # Check for "übernächsten" (the one after next) - German
        if 'übernächste' in text:
            # Find the weekday and add 14 days offset
            for weekday_name, weekday_num in self.GERMAN_WEEKDAYS.items():
                if len(weekday_name) > 2 and weekday_name in text:  # Skip abbreviations
                    days_ahead = weekday_num - self.today.weekday()
                    if days_ahead <= 0:
                        days_ahead += 7
                    days_ahead += 7  # Add another week for "übernächsten"
                    return self.today + timedelta(days=days_ahead)

        # Check for German weekdays with word boundaries
        for weekday_name, weekday_num in sorted(self.GERMAN_WEEKDAYS.items(), key=lambda x: -len(x[0])):
            # Use word boundary check for short abbreviations
            if len(weekday_name) <= 2:
                pattern = r'\b' + weekday_name + r'\b'
                if re.search(pattern, text):
                    days_ahead = weekday_num - self.today.weekday()
                    if days_ahead <= 0:
                        days_ahead += 7
                    if 'nächste' in text or 'nächster' in text or 'nächsten' in text:
                        # "nächsten" means the coming one, which our logic already handles
                        pass
                    return self.today + timedelta(days=days_ahead)
            elif weekday_name in text:
                days_ahead = weekday_num - self.today.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                return self.today + timedelta(days=days_ahead)

        # Check for English weekdays with word boundaries
        for weekday_name, weekday_num in sorted(self.ENGLISH_WEEKDAYS.items(), key=lambda x: -len(x[0])):
            # Use word boundary check for short abbreviations
            if len(weekday_name) <= 3:
                pattern = r'\b' + weekday_name + r'\b'
                if re.search(pattern, text):
                    days_ahead = weekday_num - self.today.weekday()
                    if days_ahead <= 0:
                        days_ahead += 7
                    return self.today + timedelta(days=days_ahead)
            elif weekday_name in text:
                days_ahead = weekday_num - self.today.weekday()
                if days_ahead <= 0:
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
                    'PREFER_LOCALE_DATE_ORDER': True,
                    'DATE_ORDER': 'DMY'
                }
            )
            if parsed_date:
                return parsed_date.replace(hour=0, minute=0, second=0, microsecond=0)
        except:
            pass

        # Default to today if no date found
        return self.today

    def _extract_time_range(self, text):
        """Extract time range from text with German and English support."""

        # Check for explicit time with "um X Uhr" or "X Uhr" pattern (German)
        uhr_patterns = [
            r'(\d{1,2}):(\d{2})\s*uhr',  # 9:00 Uhr
            r'(\d{1,2})\s*uhr',  # 9 Uhr
            r'um\s+(\d{1,2}):(\d{2})',  # um 9:00
            r'um\s+(\d{1,2})(?:\s|$|[^:\d])',  # um 9
        ]

        for pattern in uhr_patterns:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                hour = int(groups[0])
                minute = groups[1] if len(groups) > 1 and groups[1] else "00"
                start = f"{hour:02d}:{minute}"
                end_hour = min(hour + 1, 21)  # Cap at 21:00
                end = f"{end_hour:02d}:{minute}"
                return (start, end)

        # Check for standalone HH:MM pattern (not part of date like YYYY-MM-DD)
        # This must come before other patterns to catch "9:00" without qualifiers
        standalone_time_pattern = r'(?<!\d[-.])(?<!\d)\b(\d{1,2}):(\d{2})\b(?!\s*[-.]?\d)'
        standalone_match = re.search(standalone_time_pattern, text)
        if standalone_match:
            hour = int(standalone_match.group(1))
            minute = standalone_match.group(2)
            # Validate it's a reasonable time (0-23 hours)
            if 0 <= hour <= 23:
                start = f"{hour:02d}:{minute}"
                end_hour = min(hour + 1, 21)
                end = f"{end_hour:02d}:{minute}"
                return (start, end)

        # Check for am/pm patterns (English)
        ampm_patterns = [
            r'(\d{1,2}):(\d{2})\s*(am|pm)',  # 9:00am
            r'(\d{1,2})\s*(am|pm)',  # 9am
            r'at\s+(\d{1,2}):(\d{2})\s*(am|pm)?',  # at 9:00 or at 9:00am
            r'at\s+(\d{1,2})\s*(am|pm)?(?:\s|$|[^:\d])',  # at 9 or at 9am
        ]

        for pattern in ampm_patterns:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                hour = int(groups[0])

                # Check if we have minutes
                if len(groups) > 1 and groups[1] and groups[1].isdigit():
                    minute = groups[1]
                    period = groups[2] if len(groups) > 2 else None
                else:
                    minute = "00"
                    period = groups[1] if len(groups) > 1 and groups[1] in ('am', 'pm') else None
                    if len(groups) > 2 and groups[2] in ('am', 'pm'):
                        period = groups[2]

                # Convert to 24-hour format
                if period == 'pm' and hour != 12:
                    hour += 12
                elif period == 'am' and hour == 12:
                    hour = 0

                start = f"{hour:02d}:{minute}"
                end_hour = min(hour + 1, 21)
                end = f"{end_hour:02d}:{minute}"
                return (start, end)

        # Check for "o'clock" pattern
        oclock_pattern = r"(\d{1,2})\s*(?:o'clock|oclock)"
        oclock_match = re.search(oclock_pattern, text)
        if oclock_match:
            hour = int(oclock_match.group(1))
            start = f"{hour:02d}:00"
            end_hour = min(hour + 1, 21)
            end = f"{end_hour:02d}:00"
            return (start, end)

        # Check for German time windows
        for window_name, (start, end) in self.GERMAN_TIME_WINDOWS.items():
            if window_name in text:
                return (start, end)

        # Check for English time windows
        for window_name, (start, end) in self.ENGLISH_TIME_WINDOWS.items():
            if window_name in text:
                return (start, end)

        # Pattern for time ranges like "10-13", "15:00-18:00", "6pm-8pm"
        time_range_patterns = [
            # HH:MM-HH:MM (24-hour format)
            r'(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})',
            # H am/pm - H am/pm
            r'(\d{1,2})\s*(am|pm)\s*-\s*(\d{1,2})\s*(am|pm)',
            # H-H format with optional "uhr"
            r'(\d{1,2})\s*-\s*(\d{1,2})(?:\s*uhr)?(?:\s|$)',
        ]

        for pattern in time_range_patterns:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()

                if len(groups) == 4 and groups[1] and groups[1].isdigit():
                    # HH:MM-HH:MM
                    start_hour, start_min, end_hour, end_min = groups
                    return (
                        f"{int(start_hour):02d}:{int(start_min):02d}",
                        f"{int(end_hour):02d}:{int(end_min):02d}"
                    )
                elif len(groups) == 4 and groups[1] in ('am', 'pm'):
                    # H am/pm - H am/pm
                    start_hour = int(groups[0])
                    start_period = groups[1]
                    end_hour = int(groups[2])
                    end_period = groups[3]

                    if start_period == 'pm' and start_hour != 12:
                        start_hour += 12
                    if end_period == 'pm' and end_hour != 12:
                        end_hour += 12

                    return (f"{start_hour:02d}:00", f"{end_hour:02d}:00")
                elif len(groups) == 2:
                    # Simple H-H format
                    start_hour = int(groups[0])
                    end_hour = int(groups[1])
                    return (f"{start_hour:02d}:00", f"{end_hour:02d}:00")

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

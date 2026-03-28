"""Core parser logic for converting natural language to TimeWindow objects."""

import re
from datetime import datetime, timedelta
from .normalizer import TextNormalizer
from .time_windows import TimeWindow, get_next_full_hour
from .keywords import (
    RELATIVE_DATES, WEEKDAYS_DE, WEEKDAYS_EN, TIME_WINDOWS,
    DEFAULT_TIME_WINDOW, ASAP_TRIGGERS, WEEKEND_TRIGGERS,
    THIS_MODIFIERS, NEXT_MODIFIERS
)


class TimeParser:
    """Parses natural language time expressions into TimeWindow objects."""

    def __init__(self):
        self.normalizer = TextNormalizer(max_distance=2)
        self.today = datetime.now()

    def parse(self, query):
        """
        Parse natural language query into TimeWindow objects.

        Args:
            query: Natural language time query

        Returns:
            Dictionary with:
                - success: bool
                - interpreted_as: str (human-readable interpretation)
                - confidence: float (0.0-1.0)
                - windows: list of TimeWindow dicts
                - corrections: dict of typo corrections
                - error: str (if success=False)
                - hint: str (if success=False)
        """
        # Normalize input
        normalized = self.normalizer.normalize(query)

        # Correct typos
        corrected, corrections = self.normalizer.correct_typos(normalized)

        # Parse date
        dates, date_confidence, date_desc = self._parse_date(corrected)

        if not dates:
            return {
                "success": False,
                "interpreted_as": None,
                "confidence": 0.0,
                "windows": [],
                "error": "Zeitangabe konnte nicht interpretiert werden.",
                "hint": "Beispiele: 'morgen früh', 'next Sunday afternoon', 'between 10 and 12'"
            }

        # Parse time range
        from_time, to_time, time_confidence, time_desc = self._parse_time_range(corrected)

        # Build time windows
        windows = []
        for date in dates:
            window = TimeWindow(date, from_time, to_time)
            windows.append(window.to_dict())

        # Calculate overall confidence
        confidence = self._calculate_confidence(
            date_confidence,
            time_confidence,
            len(corrections) > 0
        )

        # Build human-readable interpretation
        interpreted_as = f"{date_desc}, {time_desc}"

        return {
            "success": True,
            "interpreted_as": interpreted_as,
            "confidence": confidence,
            "windows": windows,
            "corrections": {
                "original": query,
                "normalized": corrected
            } if corrections else {}
        }

    def _parse_date(self, text):
        """
        Parse date from text.

        Returns:
            Tuple of (list of dates, confidence, description)
        """
        # Check for ASAP triggers
        for trigger in ASAP_TRIGGERS:
            if trigger in text:
                return ([self.today], 1.0, "so bald wie möglich")

        # Check for weekend triggers
        for trigger in WEEKEND_TRIGGERS:
            if trigger in text:
                # Find next Saturday and Sunday
                days_until_saturday = (5 - self.today.weekday()) % 7
                if days_until_saturday == 0:
                    days_until_saturday = 7
                saturday = self.today + timedelta(days=days_until_saturday)
                sunday = saturday + timedelta(days=1)
                return ([saturday, sunday], 0.99, "Wochenende")

        # Check for relative dates
        for keyword, offset in RELATIVE_DATES.items():
            if keyword in text:
                target_date = self.today + timedelta(days=offset)
                desc = keyword.capitalize()
                return ([target_date], 0.95, desc)

        # Check for weekdays
        has_next = any(mod in text for mod in NEXT_MODIFIERS)
        has_this = any(mod in text for mod in THIS_MODIFIERS)

        # Try German weekdays
        for idx, weekday in enumerate(WEEKDAYS_DE):
            if weekday in text:
                target_date = self._get_weekday_date(idx, has_next, has_this)
                desc = weekday.capitalize()
                if has_next:
                    desc = f"nächsten {desc}"
                elif has_this:
                    desc = f"diesen {desc}"
                return ([target_date], 0.95, desc)

        # Try English weekdays
        for idx, weekday in enumerate(WEEKDAYS_EN):
            if weekday in text:
                target_date = self._get_weekday_date(idx, has_next, has_this)
                desc = weekday.capitalize()
                if has_next:
                    desc = f"next {desc}"
                elif has_this:
                    desc = f"this {desc}"
                return ([target_date], 0.95, desc)

        # Check for explicit date formats
        date_result = self._parse_explicit_date(text)
        if date_result:
            return date_result

        # Default to today with lower confidence
        return ([self.today], 0.5, "heute")

    def _get_weekday_date(self, target_weekday, has_next, has_this):
        """
        Get date for a specific weekday.

        Args:
            target_weekday: Target weekday (0=Monday, 6=Sunday)
            has_next: Whether "next" modifier is present
            has_this: Whether "this" modifier is present

        Returns:
            datetime object
        """
        current_weekday = self.today.weekday()
        days_ahead = target_weekday - current_weekday

        if has_next:
            # "next Monday" = Monday in 7-13 days
            if days_ahead <= 0:
                days_ahead += 7
            else:
                days_ahead += 7
        elif has_this:
            # "this Monday" = upcoming Monday within 6 days
            if days_ahead <= 0:
                days_ahead += 7
        else:
            # Default behavior: upcoming occurrence
            if days_ahead <= 0:
                days_ahead += 7

        return self.today + timedelta(days=days_ahead)

    def _parse_explicit_date(self, text):
        """
        Parse explicit date formats (DD.MM.YYYY, YYYY-MM-DD, etc.).

        Returns:
            Tuple of (list of dates, confidence, description) or None
        """
        # Pattern: DD.MM.YYYY or DD/MM/YYYY
        pattern1 = r'(\d{1,2})[./](\d{1,2})[./](\d{4})'
        match = re.search(pattern1, text)
        if match:
            day, month, year = match.groups()
            try:
                date = datetime(int(year), int(month), int(day))
                desc = date.strftime("%d.%m.%Y")
                return ([date], 1.0, desc)
            except ValueError:
                pass

        # Pattern: YYYY-MM-DD
        pattern2 = r'(\d{4})-(\d{1,2})-(\d{1,2})'
        match = re.search(pattern2, text)
        if match:
            year, month, day = match.groups()
            try:
                date = datetime(int(year), int(month), int(day))
                desc = date.strftime("%Y-%m-%d")
                return ([date], 1.0, desc)
            except ValueError:
                pass

        return None

    def _parse_time_range(self, text):
        """
        Parse time range from text.

        Returns:
            Tuple of (from_time, to_time, confidence, description)
        """
        # Check for time-of-day keywords first
        for keyword, (from_time, to_time) in TIME_WINDOWS.items():
            if keyword in text:
                return (from_time, to_time, 1.0, keyword)

        # Check for "zwischen X und Y" / "between X and Y"
        between_pattern = r'zwischen\s+(\d{1,2}):?(\d{2})?\s+und\s+(\d{1,2}):?(\d{2})?'
        match = re.search(between_pattern, text)
        if not match:
            between_pattern = r'between\s+(\d{1,2}):?(\d{2})?\s+and\s+(\d{1,2}):?(\d{2})?'
            match = re.search(between_pattern, text)

        if match:
            groups = match.groups()
            from_hour = int(groups[0])
            from_min = groups[1] if groups[1] else "00"
            to_hour = int(groups[2])
            to_min = groups[3] if groups[3] else "00"

            from_time = f"{from_hour:02d}:{from_min}"
            to_time = f"{to_hour:02d}:{to_min}"
            desc = f"{from_time}–{to_time}"
            return (from_time, to_time, 1.0, desc)

        # Check for "um X" / "at X"
        at_pattern = r'(?:um|at)\s+(\d{1,2}):?(\d{2})?'
        match = re.search(at_pattern, text)
        if match:
            hour = int(match.group(1))
            minute = match.group(2) if match.group(2) else "00"
            from_time = f"{hour:02d}:{minute}"
            to_hour = (hour + 1) % 24
            to_time = f"{to_hour:02d}:{minute}"
            desc = f"um {from_time}"
            return (from_time, to_time, 0.95, desc)

        # Check for "von X bis Y" / "from X to Y"
        from_to_pattern = r'(?:von|from)\s+(\d{1,2}):?(\d{2})?\s+(?:bis|to)\s+(\d{1,2}):?(\d{2})?'
        match = re.search(from_to_pattern, text)
        if match:
            groups = match.groups()
            from_hour = int(groups[0])
            from_min = groups[1] if groups[1] else "00"
            to_hour = int(groups[2])
            to_min = groups[3] if groups[3] else "00"

            from_time = f"{from_hour:02d}:{from_min}"
            to_time = f"{to_hour:02d}:{to_min}"
            desc = f"{from_time}–{to_time}"
            return (from_time, to_time, 1.0, desc)

        # Check for time range with dash: "HH:MM-HH:MM" or "H-H"
        time_range_pattern = r'(\d{1,2}):?(\d{2})?\s*-\s*(\d{1,2}):?(\d{2})?'
        match = re.search(time_range_pattern, text)
        if match:
            groups = match.groups()
            from_hour = int(groups[0])
            from_min = groups[1] if groups[1] else "00"
            to_hour = int(groups[2])
            to_min = groups[3] if groups[3] else "00"

            from_time = f"{from_hour:02d}:{from_min}"
            to_time = f"{to_hour:02d}:{to_min}"
            desc = f"{from_time}–{to_time}"
            return (from_time, to_time, 1.0, desc)

        # For ASAP, use next full hour
        for trigger in ASAP_TRIGGERS:
            if trigger in text:
                from_time = get_next_full_hour()
                to_time = DEFAULT_TIME_WINDOW[1]
                desc = f"ab {from_time}"
                return (from_time, to_time, 0.9, desc)

        # Default time window
        from_time, to_time = DEFAULT_TIME_WINDOW
        desc = "ganzer Tag"
        return (from_time, to_time, 0.6, desc)

    def _calculate_confidence(self, date_conf, time_conf, has_corrections):
        """
        Calculate overall confidence score.

        Args:
            date_conf: Date parsing confidence (0.0-1.0)
            time_conf: Time parsing confidence (0.0-1.0)
            has_corrections: Whether typo corrections were made

        Returns:
            Overall confidence (0.0-1.0)
        """
        # Average of date and time confidence
        base_confidence = (date_conf + time_conf) / 2

        # Penalty for typo corrections
        if has_corrections:
            base_confidence -= 0.15

        # Ensure in valid range
        return max(0.0, min(1.0, base_confidence))

"""Time window definitions and helpers."""

from datetime import datetime, timedelta


class TimeWindow:
    """Represents a time window for court booking."""

    def __init__(self, date, from_time, to_time):
        """
        Initialize a time window.

        Args:
            date: datetime object for the date
            from_time: Start time string (HH:MM)
            to_time: End time string (HH:MM)
        """
        self.date = date
        self.from_time = from_time
        self.to_time = to_time

    def to_dict(self):
        """
        Convert to dictionary format for API response.

        Returns:
            Dictionary with date, day_name, from, to
        """
        # Get day name in German
        day_names_de = {
            0: "Montag",
            1: "Dienstag",
            2: "Mittwoch",
            3: "Donnerstag",
            4: "Freitag",
            5: "Samstag",
            6: "Sonntag"
        }

        return {
            "date": self.date.strftime("%Y-%m-%d"),
            "day_name": day_names_de[self.date.weekday()],
            "from": self.from_time,
            "to": self.to_time
        }

    def __repr__(self):
        return f"TimeWindow({self.date.strftime('%Y-%m-%d')}, {self.from_time}-{self.to_time})"


def get_next_full_hour():
    """
    Get the next full hour from now.

    Returns:
        Time string in HH:MM format
    """
    now = datetime.now()
    next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    return next_hour.strftime("%H:%M")


def parse_time_string(time_str):
    """
    Parse time string to ensure HH:MM format.

    Args:
        time_str: Time string (various formats accepted)

    Returns:
        Time in HH:MM format
    """
    if ':' in time_str:
        parts = time_str.split(':')
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
    else:
        hour = int(time_str)
        minute = 0

    return f"{hour:02d}:{minute:02d}"

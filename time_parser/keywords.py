"""Keyword dictionaries for German and English time expressions."""

# Relative date keywords - maps to days offset from today
RELATIVE_DATES = {
    "heute": 0,
    "today": 0,
    "morgen": 1,
    "tomorrow": 1,
    "übermorgen": 2,
    "day after tomorrow": 2,
}

# ASAP triggers - map to "today, next full hour"
ASAP_TRIGGERS = [
    "asap",
    "so bald wie möglich",
    "sofort",
    "jetzt",
    "now",
    "immediately"
]

# Weekend triggers - return 2 time windows (Saturday + Sunday)
WEEKEND_TRIGGERS = [
    "wochenende",
    "weekend",
    "this weekend",
    "am wochenende",
    "dieses wochenende"
]

# Weekday names (German)
WEEKDAYS_DE = [
    "montag",
    "dienstag",
    "mittwoch",
    "donnerstag",
    "freitag",
    "samstag",
    "sonntag"
]

# Weekday names (English)
WEEKDAYS_EN = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday"
]

# Combined weekdays for easy lookup
ALL_WEEKDAYS = WEEKDAYS_DE + WEEKDAYS_EN

# Time-of-day keywords (maps to (from_time, to_time))
TIME_WINDOWS = {
    # German
    "früh": ("07:00", "09:00"),
    "vormittag": ("09:00", "12:00"),
    "morgens": ("09:00", "12:00"),
    "mittag": ("12:00", "14:00"),
    "nachmittag": ("14:00", "18:00"),
    "abend": ("18:00", "21:00"),

    # English
    "early": ("07:00", "09:00"),
    "morning": ("09:00", "12:00"),
    "noon": ("12:00", "14:00"),
    "lunchtime": ("12:00", "14:00"),
    "afternoon": ("14:00", "18:00"),
    "evening": ("18:00", "21:00"),
}

# Default time window when no time keyword is found
DEFAULT_TIME_WINDOW = ("07:00", "21:00")

# Modifiers that affect weekday interpretation
THIS_MODIFIERS = ["diesen", "diese", "dieser", "this"]
NEXT_MODIFIERS = ["nächsten", "nächste", "nächster", "next"]

# All known keywords for typo correction
ALL_KEYWORDS = (
    list(RELATIVE_DATES.keys()) +
    ASAP_TRIGGERS +
    WEEKEND_TRIGGERS +
    ALL_WEEKDAYS +
    list(TIME_WINDOWS.keys()) +
    THIS_MODIFIERS +
    NEXT_MODIFIERS +
    ["zwischen", "between", "und", "and", "um", "at", "von", "from", "bis", "to", "uhr",
     "nach", "vor", "after", "before"]  # Add time range modifiers
)

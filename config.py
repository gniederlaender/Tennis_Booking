"""Configuration file for Tennis Court Booking application."""

# Booking portal URLs
PORTALS = {
    "dasspiel": {
        "name": "Tenniszentrum Arsenal (Das Spiel)",
        "url": "https://reservierung.dasspiel.at/"
    },
    "postsv": {
        "name": "Post SV Wien",
        "url": "https://buchen.postsv-wien.at/tennis.html"
    }
}

# User preferences file
PREFERENCES_FILE = "user_preferences.json"

# Result limits
MAX_RESULTS = 20

# Preference learning threshold (minimum selections before confident prediction)
CONFIDENCE_THRESHOLD = 5

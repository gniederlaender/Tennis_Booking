"""Configuration file for Tennis Court Booking application."""

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

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

# User preferences file (deprecated, kept for backward compatibility)
PREFERENCES_FILE = "user_preferences.json"

# Result limits
MAX_RESULTS = 20

# Preference learning threshold (minimum selections before confident prediction)
CONFIDENCE_THRESHOLD = 5

# Flask configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
FLASK_ENV = os.getenv('FLASK_ENV', 'development')

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///tennis_booking.db')
DATABASE_PATH = DATABASE_URL.replace('sqlite:///', '')

# Encryption key for portal credentials
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', '')

# Session configuration
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False') == 'True'
SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'True') == 'True'
SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
PERMANENT_SESSION_LIFETIME = timedelta(days=int(os.getenv('PERMANENT_SESSION_LIFETIME_DAYS', '7')))

# Rate limiting
MAX_LOGIN_ATTEMPTS = int(os.getenv('MAX_LOGIN_ATTEMPTS', '5'))
LOGIN_RATE_LIMIT_WINDOW = int(os.getenv('LOGIN_RATE_LIMIT_WINDOW', '900'))  # 15 minutes in seconds

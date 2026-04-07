#!/bin/bash
# Add a test newsletter subscriber
# Usage: ./cron/add_test_subscriber.sh your_email@example.com

if [ -z "$1" ]; then
    echo "Usage: $0 <email_address>"
    echo "Example: $0 test@example.com"
    exit 1
fi

EMAIL="$1"

cd /opt/Tennis_Booking
source venv/bin/activate

python3 << EOF
import sqlite3

db = sqlite3.connect('tennis_booking.db')
cursor = db.cursor()

# Check if user exists
cursor.execute('SELECT id, email, newsletter_active FROM users WHERE email = ?', ('$EMAIL',))
user = cursor.fetchone()

if not user:
    print(f"Error: User {user[1]} not found in database.")
    print("Please register the user first via the web interface.")
else:
    user_id, email, newsletter_active = user

    if newsletter_active:
        print(f"User {email} already has newsletter enabled.")
    else:
        # Enable newsletter with default settings (Friday evening)
        cursor.execute('''
            UPDATE users
            SET newsletter_active = 1,
                newsletter_weekday = 4,
                newsletter_timeblock = 'evening'
            WHERE id = ?
        ''', (user_id,))
        db.commit()
        print(f"✓ Newsletter enabled for {email}")
        print("  Preference: Friday Evening")
        print("  You can change this in the profile page.")

db.close()
EOF

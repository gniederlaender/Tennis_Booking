#!/bin/bash
# Test script to manually send newsletters
# Usage: ./cron/test_newsletter.sh

cd /opt/Tennis_Booking

echo "=========================================="
echo "Testing Newsletter Send"
echo "=========================================="
echo ""
echo "Checking for newsletter subscribers..."

# Show current subscribers
source venv/bin/activate
python3 << 'EOF'
import sqlite3
db = sqlite3.connect('tennis_booking.db')
cursor = db.cursor()
cursor.execute('''
    SELECT email, first_name, last_name, newsletter_weekday, newsletter_timeblock
    FROM users
    WHERE newsletter_active = 1
''')
subscribers = cursor.fetchall()
print(f"Found {len(subscribers)} active newsletter subscriber(s):")
for sub in subscribers:
    weekdays = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
    timeblocks = {'morning': 'Morgen', 'midday': 'Mittag', 'evening': 'Abend'}
    weekday_name = weekdays[sub[3]] if sub[3] is not None else 'N/A'
    timeblock_name = timeblocks.get(sub[4], 'N/A')
    print(f"  - {sub[0]} ({sub[1]} {sub[2]}) - {weekday_name} {timeblock_name}")
db.close()
EOF

echo ""
echo "=========================================="
echo "Sending newsletters now..."
echo "=========================================="
echo ""

# Run the newsletter script
python cron/send_newsletter.py

echo ""
echo "=========================================="
echo "Done! Check logs/newsletter.log for details"
echo "=========================================="

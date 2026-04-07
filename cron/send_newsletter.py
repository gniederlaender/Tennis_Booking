#!/usr/bin/env python3
"""
Weekly newsletter cron script.
Sends personalized availability emails to subscribed users.
"""

import sys
import os
from datetime import datetime, timedelta
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/newsletter.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

WEEKDAY_NAMES = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
TIMEBLOCK_NAMES = {
    'morning': 'Morgen (07:00 - 12:00 Uhr)',
    'midday': 'Mittag (12:00 - 17:00 Uhr)',
    'evening': 'Abend (17:00 - 22:00 Uhr)'
}

def get_newsletter_subscribers(db):
    """Get all users with active newsletter subscriptions."""
    cursor = db.cursor()
    cursor.execute('''
        SELECT id, email, first_name, last_name, newsletter_weekday, newsletter_timeblock
        FROM users
        WHERE newsletter_active = 1
        AND newsletter_weekday IS NOT NULL
        AND newsletter_timeblock IS NOT NULL
    ''')
    return cursor.fetchall()

def get_today_availability(db):
    """
    Get today's availability for all timeblocks.
    Returns dict with {morning, midday, evening} data including booked_since_morning.
    """
    cursor = db.cursor()
    today_weekday = datetime.now().weekday()

    # Get latest snapshots for today
    cursor.execute('''
        SELECT location, timeblock, available_slots
        FROM availability_snapshots
        WHERE DATE(captured_at) = DATE('now', 'localtime')
          AND weekday = ?
        ORDER BY captured_at DESC
    ''', (today_weekday,))

    snapshots = cursor.fetchall()

    # Get current availability (most recent per location/timeblock)
    current_data = {}
    seen = set()
    for location, timeblock, slots in snapshots:
        key = f"{location}_{timeblock}"
        if key not in seen:
            seen.add(key)
            if timeblock not in current_data:
                current_data[timeblock] = {'arsenal': 0, 'postsv': 0}
            current_data[timeblock][location] = slots

    # Get earliest morning snapshot for today to calculate "booked since morning"
    cursor.execute('''
        SELECT location, timeblock, available_slots, MIN(captured_at)
        FROM availability_snapshots
        WHERE DATE(captured_at) = DATE('now', 'localtime')
          AND weekday = ?
        GROUP BY location, timeblock
    ''', (today_weekday,))

    morning_snapshots = cursor.fetchall()
    morning_data = {}
    for location, timeblock, slots, _ in morning_snapshots:
        if timeblock not in morning_data:
            morning_data[timeblock] = {'arsenal': 0, 'postsv': 0}
        morning_data[timeblock][location] = slots

    # Build response data
    result = {}
    for timeblock in ['morning', 'midday', 'evening']:
        arsenal_current = current_data.get(timeblock, {}).get('arsenal', 0)
        postsv_current = current_data.get(timeblock, {}).get('postsv', 0)
        total_current = arsenal_current + postsv_current

        arsenal_morning = morning_data.get(timeblock, {}).get('arsenal', 0)
        postsv_morning = morning_data.get(timeblock, {}).get('postsv', 0)
        total_morning = arsenal_morning + postsv_morning

        booked_since_morning = max(0, total_morning - total_current)

        # Determine status
        if total_current >= 3:
            status = 'green'
        elif total_current >= 1:
            status = 'yellow'
        else:
            status = 'red'

        result[timeblock] = {
            'total': total_current,
            'arsenal': arsenal_current,
            'postsv': postsv_current,
            'booked_since_morning': booked_since_morning,
            'status': status
        }

    return result

def get_user_preference_availability(db, weekday, timeblock):
    """
    Get availability for user's preferred weekday/timeblock for next week.
    Returns {arsenal, postsv, total, booked_since_morning, status}
    """
    cursor = db.cursor()

    # Get latest snapshot for this weekday/timeblock
    cursor.execute('''
        SELECT location, available_slots
        FROM availability_snapshots
        WHERE weekday = ?
          AND timeblock = ?
          AND DATE(captured_at) = DATE('now', 'localtime')
        ORDER BY captured_at DESC
    ''', (weekday, timeblock))

    snapshots = cursor.fetchall()

    current_data = {'arsenal': 0, 'postsv': 0}
    seen = set()
    for location, slots in snapshots:
        if location not in seen:
            seen.add(location)
            current_data[location] = slots

    # Get morning snapshot
    cursor.execute('''
        SELECT location, available_slots, MIN(captured_at)
        FROM availability_snapshots
        WHERE weekday = ?
          AND timeblock = ?
          AND DATE(captured_at) = DATE('now', 'localtime')
        GROUP BY location
    ''', (weekday, timeblock))

    morning_snapshots = cursor.fetchall()
    morning_data = {'arsenal': 0, 'postsv': 0}
    for location, slots, _ in morning_snapshots:
        morning_data[location] = slots

    total_current = current_data['arsenal'] + current_data['postsv']
    total_morning = morning_data['arsenal'] + morning_data['postsv']
    booked_since_morning = max(0, total_morning - total_current)

    # Determine status
    if total_current >= 3:
        status = 'green'
    elif total_current >= 1:
        status = 'yellow'
    else:
        status = 'red'

    return {
        'arsenal': current_data['arsenal'],
        'postsv': current_data['postsv'],
        'total': total_current,
        'booked_since_morning': booked_since_morning,
        'status': status
    }

def render_email_template(user, today_data, preference_data, weekday_name, timeblock_name):
    """Render the newsletter email template."""
    # Read template
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'templates', 'email', 'newsletter.html'
    )

    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    # Simple template rendering (replace Jinja2 placeholders)
    user_name = user[2] if user[2] else user[1].split('@')[0]

    # Build today's availability rows
    timeblock_labels = {
        'morning': ('Morgen', '07:00 - 12:00 Uhr'),
        'midday': ('Mittag', '12:00 - 17:00 Uhr'),
        'evening': ('Abend', '17:00 - 22:00 Uhr')
    }

    today_rows = ''
    for timeblock_key in ['morning', 'midday', 'evening']:
        data = today_data.get(timeblock_key, {})
        label, hours = timeblock_labels[timeblock_key]

        # Status background color
        bg_color = {
            'green': 'rgba(76, 175, 80, 0.15)',
            'yellow': 'rgba(255, 193, 7, 0.15)',
            'red': 'rgba(244, 67, 54, 0.15)'
        }.get(data.get('status', 'red'), 'rgba(255, 255, 255, 0.3)')

        booked = data.get('booked_since_morning', 0)
        booked_display = f'<span style="font-size: 14px; font-weight: 600; color: #e74c3c;">-{booked}</span><div style="font-size: 9px; color: #8899a6; margin-top: 2px;">seit heute früh</div>' if booked > 0 else '<span style="font-size: 14px; font-weight: 600; color: #27ae60;">—</span><div style="font-size: 9px; color: #8899a6; margin-top: 2px;">keine Änderung</div>'

        today_rows += f'''
                                <tr>
                                    <td style="padding: 14px 10px; border-bottom: 1px solid #e0e0e0; color: #2c3e50; font-weight: 600;">
                                        {label}<br>
                                        <span style="font-size: 11px; font-weight: 400; color: #8899a6;">{hours}</span>
                                    </td>
                                    <td style="padding: 14px 10px; border-bottom: 1px solid #e0e0e0; text-align: center; background-color: {bg_color};">
                                        <div style="font-size: 22px; font-weight: 700; color: #2c3e50; line-height: 1;">{data.get('total', 0)}</div>
                                        <div style="font-size: 10px; color: #5a6c7d; margin-top: 3px;">Plätze frei</div>
                                    </td>
                                    <td style="padding: 14px 10px; border-bottom: 1px solid #e0e0e0; text-align: center;">
                                        {booked_display}
                                    </td>
                                </tr>
        '''

    # Build preference row style and data
    pref_bg_color = {
        'green': 'background-color: rgba(76, 175, 80, 0.15);',
        'yellow': 'background-color: rgba(255, 193, 7, 0.15);',
        'red': 'background-color: rgba(244, 67, 54, 0.15);'
    }.get(preference_data.get('status', 'red'), '')

    pref_booked = preference_data.get('booked_since_morning', 0)
    pref_booked_display = f'<span style="font-size: 14px; font-weight: 600; color: #e74c3c;">-{pref_booked}</span><div style="font-size: 9px; color: #8899a6; margin-top: 2px;">seit heute früh</div>' if pref_booked > 0 else '<span style="font-size: 14px; font-weight: 600; color: #27ae60;">—</span><div style="font-size: 9px; color: #8899a6; margin-top: 2px;">keine Änderung</div>'

    timeblock_hours_map = {
        'morning': '07:00 - 12:00 Uhr',
        'midday': '12:00 - 17:00 Uhr',
        'evening': '17:00 - 22:00 Uhr'
    }

    # Replace placeholders
    html = template.replace('{{ user_name }}', user_name)
    html = html.replace('{{ weekday_name }}', weekday_name)
    html = html.replace('{{ timeblock_name }}', timeblock_name)
    html = html.replace('{{ today_rows }}', today_rows)
    html = html.replace('{{ preference_row_style }}', pref_bg_color)
    html = html.replace('{{ preference_total }}', str(preference_data.get('total', 0)))
    html = html.replace('{{ preference_booked_display }}', pref_booked_display)
    html = html.replace('{{ timeblock_hours }}', timeblock_hours_map.get(user[5], ''))

    # Add URLs
    base_url = os.getenv('BASE_URL', 'http://localhost:5001')
    html = html.replace('{{ booking_url }}', f'{base_url}/search-page')
    html = html.replace('{{ settings_url }}', f'{base_url}/profile')
    html = html.replace('{{ unsubscribe_url }}', f'{base_url}/profile')

    return html

def send_email(to_email, subject, html_content):
    """Send an email via SMTP."""
    if not config.SMTP_HOST or not config.SMTP_USER:
        logger.warning("SMTP not configured, skipping email send")
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = config.SMTP_FROM
        msg['To'] = to_email

        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)

        # Connect to SMTP server
        if config.SMTP_USE_TLS:
            server = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT)
            server.starttls()
        else:
            server = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT)

        if config.SMTP_USER and config.SMTP_PASSWORD:
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)

        server.send_message(msg)
        server.quit()

        logger.info(f"Email sent successfully to {to_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False

def send_newsletters():
    """Main function to send newsletters to all subscribers."""
    logger.info("="*60)
    logger.info("Starting newsletter sending process")
    logger.info("="*60)

    try:
        db = sqlite3.connect(config.DATABASE_PATH)

        # Get all newsletter subscribers
        subscribers = get_newsletter_subscribers(db)
        logger.info(f"Found {len(subscribers)} newsletter subscribers")

        sent_count = 0
        failed_count = 0

        for user in subscribers:
            user_id, email, first_name, last_name, weekday, timeblock = user

            logger.info(f"Processing newsletter for {email}")

            try:
                # Get today's availability data
                today_data = get_today_availability(db)

                # Get user preference availability for next week
                preference_data = get_user_preference_availability(db, weekday, timeblock)

                weekday_name = WEEKDAY_NAMES[weekday]
                timeblock_name = TIMEBLOCK_NAMES[timeblock]

                # Render email
                html_content = render_email_template(
                    user,
                    today_data,
                    preference_data,
                    weekday_name,
                    timeblock_name
                )

                # Send email
                subject = f"Deine Tennis-Wochenvorschau: {weekday_name} {timeblock_name.split('(')[0].strip()}"

                if send_email(email, subject, html_content):
                    sent_count += 1
                else:
                    failed_count += 1

            except Exception as e:
                logger.error(f"Error processing newsletter for {email}: {e}")
                failed_count += 1

        db.close()

        logger.info("="*60)
        logger.info(f"Newsletter sending completed")
        logger.info(f"Sent: {sent_count}, Failed: {failed_count}")
        logger.info("="*60)

        return True

    except Exception as e:
        logger.error(f"Error in newsletter sending process: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == '__main__':
    success = send_newsletters()
    sys.exit(0 if success else 1)

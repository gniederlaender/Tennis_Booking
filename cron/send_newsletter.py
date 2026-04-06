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

def get_weekly_availability(db, weekday, timeblock):
    """
    Get availability for the next 4 occurrences of the specified weekday.
    Returns list of {date, arsenal, postsv, total, status_icon}
    """
    today = datetime.now().date()
    current_weekday = today.weekday()

    # Calculate dates for next 4 occurrences
    dates = []
    days_ahead = (weekday - current_weekday) % 7
    if days_ahead == 0:
        days_ahead = 7  # Start from next week if today is the target weekday

    for i in range(4):
        target_date = today + timedelta(days=days_ahead + (i * 7))
        dates.append(target_date)

    # Fetch availability for these dates
    availability_data = []

    for date in dates:
        cursor = db.cursor()

        # Get arsenal availability
        cursor.execute('''
            SELECT available_slots FROM availability_snapshots
            WHERE location = 'arsenal'
            AND weekday = ?
            AND timeblock = ?
            AND DATE(captured_at) = (
                SELECT MAX(DATE(captured_at))
                FROM availability_snapshots
            )
            ORDER BY captured_at DESC
            LIMIT 1
        ''', (weekday, timeblock))
        arsenal_row = cursor.fetchone()
        arsenal_slots = arsenal_row[0] if arsenal_row else 0

        # Get postsv availability
        cursor.execute('''
            SELECT available_slots FROM availability_snapshots
            WHERE location = 'postsv'
            AND weekday = ?
            AND timeblock = ?
            AND DATE(captured_at) = (
                SELECT MAX(DATE(captured_at))
                FROM availability_snapshots
            )
            ORDER BY captured_at DESC
            LIMIT 1
        ''', (weekday, timeblock))
        postsv_row = cursor.fetchone()
        postsv_slots = postsv_row[0] if postsv_row else 0

        total_slots = arsenal_slots + postsv_slots

        # Determine status icon
        if total_slots >= 3:
            status_icon = '🟢'
        elif total_slots >= 1:
            status_icon = '🟡'
        else:
            status_icon = '🔴'

        availability_data.append({
            'date': date,
            'date_formatted': date.strftime('%d.%m.%Y (%A)'),
            'arsenal': arsenal_slots,
            'postsv': postsv_slots,
            'total': total_slots,
            'status_icon': status_icon
        })

    return availability_data

def render_email_template(user, weekly_availability, weekday_name, timeblock_name):
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

    # Build availability rows
    availability_rows = ''
    for avail in weekly_availability:
        availability_rows += f'''
                                <tr>
                                    <td style="padding: 15px; border-bottom: 1px solid #e0e0e0; color: #2c3e50;">
                                        {avail['date_formatted']}
                                    </td>
                                    <td style="padding: 15px; border-bottom: 1px solid #e0e0e0; text-align: center; color: #5a6c7d;">
                                        {avail['arsenal']} Plätze
                                    </td>
                                    <td style="padding: 15px; border-bottom: 1px solid #e0e0e0; text-align: center; color: #5a6c7d;">
                                        {avail['postsv']} Plätze
                                    </td>
                                    <td style="padding: 15px; border-bottom: 1px solid #e0e0e0; text-align: center;">
                                        <span style="font-size: 20px;">{avail['status_icon']}</span>
                                    </td>
                                </tr>
        '''

    # Replace placeholders
    html = template.replace('{{ user_name }}', user_name)
    html = html.replace('{{ weekday_name }}', weekday_name)
    html = html.replace('{{ timeblock_name }}', timeblock_name)
    html = html.replace('{% for availability in weekly_availability %}', '')
    html = html.replace('{% endfor %}', '')
    html = html.replace('                                <tr>', availability_rows, 1)

    # Add URLs (replace with actual base URL from config if available)
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
                # Get availability data for this user's preferences
                weekly_availability = get_weekly_availability(db, weekday, timeblock)

                weekday_name = WEEKDAY_NAMES[weekday]
                timeblock_name = TIMEBLOCK_NAMES[timeblock]

                # Render email
                html_content = render_email_template(
                    user,
                    weekly_availability,
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

# Cron Setup Instructions

This document explains how to set up the automated cron jobs for the Tennis Booking Finder application.

## Overview

Two cron scripts are included:

1. **update_snapshots.py** - Runs hourly to scrape and store availability data
2. **send_newsletter.py** - Runs weekly (Monday 08:00) to send personalized newsletters

## Prerequisites

- Python 3.x installed
- Virtual environment activated
- SMTP credentials configured in `.env` file (for newsletter)

## Environment Variables

Add the following to your `.env` file:

```env
# SMTP Configuration (required for newsletter)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-smtp-password
SMTP_FROM=noreply@tennisfinder.at
SMTP_USE_TLS=True

# Newsletter Configuration
NEWSLETTER_SEND_DAY=monday
NEWSLETTER_SEND_TIME=08:00

# Optional: Base URL for email links
BASE_URL=https://your-domain.com
```

## Cron Configuration

### Option 1: Using crontab (Linux/Unix)

1. Open crontab editor:
   ```bash
   crontab -e
   ```

2. Add the following lines (adjust paths as needed):

   ```bash
   # Hourly snapshot update
   0 * * * * /opt/Tennis_Booking/venv/bin/python /opt/Tennis_Booking/cron/update_snapshots.py >> /opt/Tennis_Booking/logs/cron.log 2>&1

   # Weekly newsletter (Mondays at 08:00)
   0 8 * * 1 /opt/Tennis_Booking/venv/bin/python /opt/Tennis_Booking/cron/send_newsletter.py >> /opt/Tennis_Booking/logs/newsletter.log 2>&1
   ```

3. Save and exit

### Option 2: Using systemd timers (Linux)

1. Create timer units in `/etc/systemd/system/`:

   **tennis-snapshot.service**:
   ```ini
   [Unit]
   Description=Tennis Booking Snapshot Update

   [Service]
   Type=oneshot
   User=www-data
   WorkingDirectory=/opt/Tennis_Booking
   ExecStart=/opt/Tennis_Booking/venv/bin/python /opt/Tennis_Booking/cron/update_snapshots.py
   StandardOutput=append:/opt/Tennis_Booking/logs/cron.log
   StandardError=append:/opt/Tennis_Booking/logs/cron.log
   ```

   **tennis-snapshot.timer**:
   ```ini
   [Unit]
   Description=Run Tennis Snapshot Update Hourly

   [Timer]
   OnCalendar=hourly
   Persistent=true

   [Install]
   WantedBy=timers.target
   ```

   **tennis-newsletter.service**:
   ```ini
   [Unit]
   Description=Tennis Newsletter Sending

   [Service]
   Type=oneshot
   User=www-data
   WorkingDirectory=/opt/Tennis_Booking
   ExecStart=/opt/Tennis_Booking/venv/bin/python /opt/Tennis_Booking/cron/send_newsletter.py
   StandardOutput=append:/opt/Tennis_Booking/logs/newsletter.log
   StandardError=append:/opt/Tennis_Booking/logs/newsletter.log
   ```

   **tennis-newsletter.timer**:
   ```ini
   [Unit]
   Description=Run Tennis Newsletter Weekly (Monday 08:00)

   [Timer]
   OnCalendar=Mon *-*-* 08:00:00
   Persistent=true

   [Install]
   WantedBy=timers.target
   ```

2. Enable and start timers:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable tennis-snapshot.timer
   sudo systemctl enable tennis-newsletter.timer
   sudo systemctl start tennis-snapshot.timer
   sudo systemctl start tennis-newsletter.timer
   ```

3. Check timer status:
   ```bash
   sudo systemctl list-timers
   ```

## Manual Testing

Before setting up cron, test the scripts manually:

### Test Snapshot Update
```bash
cd /opt/Tennis_Booking
source venv/bin/activate
python cron/update_snapshots.py
```

Expected output:
- Scrapes both portals for the next 7 days
- Saves aggregated availability snapshots to database
- Logs success/errors to `logs/cron.log`

### Test Newsletter Sending
```bash
cd /opt/Tennis_Booking
source venv/bin/activate
python cron/send_newsletter.py
```

Expected output:
- Finds all users with active newsletter subscriptions
- Sends personalized emails with availability data
- Logs success/errors to `logs/newsletter.log`

## Monitoring

### Check Logs

```bash
# View snapshot update logs
tail -f /opt/Tennis_Booking/logs/cron.log

# View newsletter logs
tail -f /opt/Tennis_Booking/logs/newsletter.log
```

### Verify Database

```bash
# Check snapshot data
sqlite3 tennis_booking.db "SELECT COUNT(*) FROM availability_snapshots;"

# Check recent snapshots
sqlite3 tennis_booking.db "SELECT * FROM availability_snapshots ORDER BY captured_at DESC LIMIT 10;"

# Check newsletter subscribers
sqlite3 tennis_booking.db "SELECT email, newsletter_weekday, newsletter_timeblock FROM users WHERE newsletter_active = 1;"
```

## Troubleshooting

### Snapshot script fails

1. Check scraper dependencies are installed:
   ```bash
   pip install requests beautifulsoup4
   ```

2. Verify database permissions:
   ```bash
   ls -la tennis_booking.db
   ```

3. Test scrapers directly:
   ```bash
   python -c "from scrapers_v2 import scrape_all_portals; from datetime import datetime; print(scrape_all_portals(datetime.now(), '07:00', '22:00'))"
   ```

### Newsletter script fails

1. Verify SMTP credentials in `.env`

2. Test SMTP connection:
   ```bash
   python -c "import smtplib; import config; print(config.SMTP_HOST, config.SMTP_PORT)"
   ```

3. Check for newsletter subscribers:
   ```bash
   sqlite3 tennis_booking.db "SELECT * FROM users WHERE newsletter_active = 1;"
   ```

### Permission issues

Ensure cron user has write access to:
- `/opt/Tennis_Booking/logs/`
- `/opt/Tennis_Booking/tennis_booking.db`

```bash
sudo chown -R www-data:www-data /opt/Tennis_Booking
sudo chmod -R 755 /opt/Tennis_Booking
sudo chmod 664 /opt/Tennis_Booking/tennis_booking.db
```

## Cleanup

Old snapshots are automatically deleted after 30 days by the `update_snapshots.py` script.

To manually clean up old data:

```bash
sqlite3 tennis_booking.db "DELETE FROM availability_snapshots WHERE captured_at < datetime('now', '-30 days');"
```

#!/usr/bin/env python3
"""
Hourly cron script to update availability snapshots.
Scrapes both portals and stores aggregated availability data.
"""

import sys
import os
from datetime import datetime, timedelta
import sqlite3
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers_v2 import scrape_all_portals
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/cron.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_timeblock(hour):
    """Determine timeblock based on hour."""
    if 7 <= hour < 12:
        return 'morning'
    elif 12 <= hour < 17:
        return 'midday'
    elif 17 <= hour < 22:
        return 'evening'
    return None

def aggregate_slots_by_block(slots):
    """
    Aggregate slots by location, weekday, and timeblock.
    Returns dict: {(location, weekday, timeblock): count}
    """
    aggregated = {}

    for slot in slots:
        # Determine location
        venue = slot.get('venue', '')
        if 'Arsenal' in venue or 'Das Spiel' in venue:
            location = 'arsenal'
        elif 'Post SV' in venue:
            location = 'postsv'
        else:
            continue

        # Parse date and time
        try:
            date_str = slot.get('date')
            time_str = slot.get('time')

            if not date_str or not time_str:
                continue

            # Parse date to get weekday (0=Monday, 6=Sunday)
            date = datetime.strptime(date_str, '%Y-%m-%d')
            weekday = date.weekday()

            # Parse time to get hour
            hour = int(time_str.split(':')[0])
            timeblock = get_timeblock(hour)

            if timeblock is None:
                continue

            # Increment count for this combination
            key = (location, weekday, timeblock)
            aggregated[key] = aggregated.get(key, 0) + 1

        except (ValueError, AttributeError) as e:
            logger.warning(f"Error parsing slot: {e}")
            continue

    return aggregated

def save_snapshot(db, location, weekday, timeblock, available_slots):
    """Save a snapshot to the database."""
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO availability_snapshots
        (captured_at, location, weekday, timeblock, available_slots)
        VALUES (?, ?, ?, ?, ?)
    ''', (datetime.now().isoformat(), location, weekday, timeblock, available_slots))

def cleanup_old_snapshots(db, days=30):
    """Delete snapshots older than specified days."""
    cursor = db.cursor()
    cutoff = datetime.now() - timedelta(days=days)
    cursor.execute('''
        DELETE FROM availability_snapshots
        WHERE captured_at < ?
    ''', (cutoff.isoformat(),))
    deleted = cursor.rowcount
    if deleted > 0:
        logger.info(f"Cleaned up {deleted} old snapshots (older than {days} days)")

def update_snapshots():
    """Main function to update availability snapshots."""
    logger.info("="*60)
    logger.info("Starting availability snapshot update")
    logger.info("="*60)

    try:
        # Connect to database
        db = sqlite3.connect(config.DATABASE_PATH)

        # Calculate date range (today + next 7 days)
        start_date = datetime.now().date()
        total_slots_saved = 0

        # Scrape for the next 7 days
        for day_offset in range(7):
            date = start_date + timedelta(days=day_offset)

            logger.info(f"\nScraping for {date.strftime('%Y-%m-%d (%A)')}")

            # Scrape full day (7:00 to 22:00)
            slots = scrape_all_portals(
                date=date,
                start_time='07:00',
                end_time='22:00',
                locations={'arsenal': True, 'postsv': True}
            )

            logger.info(f"Found {len(slots)} total slots for {date}")

            # Aggregate by location, weekday, and timeblock
            aggregated = aggregate_slots_by_block(slots)

            # Save aggregated data
            for (location, weekday, timeblock), count in aggregated.items():
                save_snapshot(db, location, weekday, timeblock, count)
                total_slots_saved += 1
                logger.debug(
                    f"Saved: {location} - {['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][weekday]} "
                    f"{timeblock} - {count} slots"
                )

        # Commit all changes
        db.commit()
        logger.info(f"\nSuccessfully saved {total_slots_saved} snapshot entries")

        # Cleanup old snapshots
        cleanup_old_snapshots(db)
        db.commit()

        db.close()

        logger.info("="*60)
        logger.info("Snapshot update completed successfully")
        logger.info("="*60)

        return True

    except Exception as e:
        logger.error(f"Error updating snapshots: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == '__main__':
    success = update_snapshots()
    sys.exit(0 if success else 1)

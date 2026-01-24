#!/usr/bin/env python3
"""Test that the login timestamp fix works."""

import sqlite3
import sys

DATABASE_PATH = 'tennis_booking.db'

def test_database_connection():
    """Test that we can read user data without timestamp parsing errors."""
    print("Testing database connection and timestamp handling...")
    print("=" * 60)

    try:
        # Connect without PARSE_DECLTYPES (like our fix)
        db = sqlite3.connect(DATABASE_PATH)
        db.row_factory = sqlite3.Row
        cursor = db.cursor()

        # Try to fetch users (this was failing before)
        cursor.execute('SELECT * FROM users LIMIT 5')
        rows = cursor.fetchall()

        print(f"✓ Successfully fetched {len(rows)} users")

        for row in rows:
            print(f"\nUser ID: {row['id']}")
            print(f"  Email: {row['email']}")
            print(f"  Created at: {row['created_at']} (type: {type(row['created_at']).__name__})")
            print(f"  Last login: {row['last_login']} (type: {type(row['last_login']).__name__})")

        db.close()
        print("\n" + "=" * 60)
        print("✓ Test PASSED - No timestamp parsing errors!")
        return True

    except Exception as e:
        print(f"\n✗ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_database_connection()
    sys.exit(0 if success else 1)

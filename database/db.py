"""Database connection and initialization."""

import sqlite3
from flask import g
import config

def get_db():
    """Get database connection."""
    if 'db' not in g:
        # Don't use PARSE_DECLTYPES to avoid timestamp parsing errors
        # Timestamps will be returned as strings, which is safer
        g.db = sqlite3.connect(config.DATABASE_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """Close database connection."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize the database with schema."""
    db = sqlite3.connect(config.DATABASE_PATH)
    cursor = db.cursor()

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            email_verified BOOLEAN DEFAULT 0
        )
    ''')

    # Portal credentials table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portal_credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            portal_name VARCHAR(50) NOT NULL,
            username VARCHAR(255) NOT NULL,
            password_encrypted TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, portal_name)
        )
    ''')

    # Login attempts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email VARCHAR(255),
            ip_address VARCHAR(50),
            success BOOLEAN,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Availability snapshots table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS availability_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            location TEXT NOT NULL,
            weekday INTEGER NOT NULL,
            timeblock TEXT NOT NULL,
            available_slots INTEGER NOT NULL DEFAULT 0
        )
    ''')

    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_portal_credentials_user_id ON portal_credentials(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_login_attempts_email ON login_attempts(email)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_login_attempts_ip ON login_attempts(ip_address)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_login_attempts_timestamp ON login_attempts(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshots_location_weekday_timeblock ON availability_snapshots(location, weekday, timeblock)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshots_captured_at ON availability_snapshots(captured_at)')

    # Add newsletter fields to users table if they don't exist
    _add_column_if_not_exists(cursor, 'users', 'newsletter_active', 'BOOLEAN DEFAULT 0')
    _add_column_if_not_exists(cursor, 'users', 'newsletter_weekday', 'INTEGER')
    _add_column_if_not_exists(cursor, 'users', 'newsletter_timeblock', 'TEXT')

    db.commit()
    db.close()
    print("Database initialized successfully")

def _add_column_if_not_exists(cursor, table, column, column_type):
    """Add a column to a table if it doesn't exist."""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    if column not in columns:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
        print(f"Added column {column} to {table}")

if __name__ == '__main__':
    init_db()

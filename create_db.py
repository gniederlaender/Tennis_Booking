#!/usr/bin/env python3
"""Create database tables - standalone script that doesn't require Flask."""

import sqlite3
import os

# Get database path
DATABASE_PATH = 'tennis_booking.db'

def create_tables():
    """Create all required database tables."""

    print(f"Creating database: {DATABASE_PATH}")

    db = sqlite3.connect(DATABASE_PATH)
    cursor = db.cursor()

    # Users table
    print("Creating users table...")
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
    print("Creating portal_credentials table...")
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
    print("Creating login_attempts table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email VARCHAR(255),
            ip_address VARCHAR(50),
            success BOOLEAN,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create indexes
    print("Creating indexes...")
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_portal_credentials_user_id ON portal_credentials(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_login_attempts_email ON login_attempts(email)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_login_attempts_ip ON login_attempts(ip_address)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_login_attempts_timestamp ON login_attempts(timestamp)')

    db.commit()
    db.close()

    print("✓ Database created successfully!")
    print(f"✓ Database file: {os.path.abspath(DATABASE_PATH)}")

if __name__ == '__main__':
    create_tables()

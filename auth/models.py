"""Database models for authentication."""

from datetime import datetime
from database.db import get_db

class User:
    """User model."""

    def __init__(self, id=None, email=None, password_hash=None, first_name=None,
                 last_name=None, created_at=None, last_login=None, is_active=True,
                 email_verified=False):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.first_name = first_name
        self.last_name = last_name
        self.created_at = created_at
        self.last_login = last_login
        self.is_active = is_active
        self.email_verified = email_verified

    @staticmethod
    def get_by_id(user_id):
        """Get user by ID."""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        if row:
            return User(
                id=row['id'],
                email=row['email'],
                password_hash=row['password_hash'],
                first_name=row['first_name'],
                last_name=row['last_name'],
                created_at=row['created_at'],
                last_login=row['last_login'],
                is_active=row['is_active'],
                email_verified=row['email_verified']
            )
        return None

    @staticmethod
    def get_by_email(email):
        """Get user by email."""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        row = cursor.fetchone()
        if row:
            return User(
                id=row['id'],
                email=row['email'],
                password_hash=row['password_hash'],
                first_name=row['first_name'],
                last_name=row['last_name'],
                created_at=row['created_at'],
                last_login=row['last_login'],
                is_active=row['is_active'],
                email_verified=row['email_verified']
            )
        return None

    def save(self):
        """Save user to database."""
        db = get_db()
        cursor = db.cursor()
        if self.id:
            cursor.execute('''
                UPDATE users
                SET email = ?, password_hash = ?, first_name = ?, last_name = ?,
                    last_login = ?, is_active = ?, email_verified = ?
                WHERE id = ?
            ''', (self.email, self.password_hash, self.first_name, self.last_name,
                  self.last_login, self.is_active, self.email_verified, self.id))
        else:
            cursor.execute('''
                INSERT INTO users (email, password_hash, first_name, last_name, is_active, email_verified)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.email, self.password_hash, self.first_name, self.last_name,
                  self.is_active, self.email_verified))
            self.id = cursor.lastrowid
        db.commit()
        return self

    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login = datetime.now().isoformat()
        db = get_db()
        cursor = db.cursor()
        cursor.execute('UPDATE users SET last_login = ? WHERE id = ?',
                      (self.last_login, self.id))
        db.commit()

    def to_dict(self):
        """Convert user to dictionary."""
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'created_at': self.created_at,
            'last_login': self.last_login,
            'is_active': self.is_active,
            'email_verified': self.email_verified
        }


class PortalCredentials:
    """Portal credentials model."""

    def __init__(self, id=None, user_id=None, portal_name=None, username=None,
                 password_encrypted=None, created_at=None, updated_at=None):
        self.id = id
        self.user_id = user_id
        self.portal_name = portal_name
        self.username = username
        self.password_encrypted = password_encrypted
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def get_by_user_and_portal(user_id, portal_name):
        """Get credentials by user ID and portal name."""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT * FROM portal_credentials
            WHERE user_id = ? AND portal_name = ?
        ''', (user_id, portal_name))
        row = cursor.fetchone()
        if row:
            return PortalCredentials(
                id=row['id'],
                user_id=row['user_id'],
                portal_name=row['portal_name'],
                username=row['username'],
                password_encrypted=row['password_encrypted'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
        return None

    @staticmethod
    def get_all_by_user(user_id):
        """Get all portal credentials for a user."""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM portal_credentials WHERE user_id = ?', (user_id,))
        rows = cursor.fetchall()
        return [PortalCredentials(
            id=row['id'],
            user_id=row['user_id'],
            portal_name=row['portal_name'],
            username=row['username'],
            password_encrypted=row['password_encrypted'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        ) for row in rows]

    def save(self):
        """Save portal credentials to database."""
        db = get_db()
        cursor = db.cursor()
        if self.id:
            cursor.execute('''
                UPDATE portal_credentials
                SET username = ?, password_encrypted = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (self.username, self.password_encrypted, self.id))
        else:
            cursor.execute('''
                INSERT INTO portal_credentials (user_id, portal_name, username, password_encrypted)
                VALUES (?, ?, ?, ?)
            ''', (self.user_id, self.portal_name, self.username, self.password_encrypted))
            self.id = cursor.lastrowid
        db.commit()
        return self


class LoginAttempt:
    """Login attempt model for rate limiting."""

    @staticmethod
    def log_attempt(email, ip_address, success):
        """Log a login attempt."""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO login_attempts (email, ip_address, success)
            VALUES (?, ?, ?)
        ''', (email, ip_address, success))
        db.commit()

    @staticmethod
    def get_recent_failed_attempts(email, window_seconds):
        """Get number of recent failed login attempts."""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT COUNT(*) as count FROM login_attempts
            WHERE email = ? AND success = 0
            AND datetime(timestamp) > datetime('now', '-' || ? || ' seconds')
        ''', (email, window_seconds))
        row = cursor.fetchone()
        return row['count'] if row else 0

    @staticmethod
    def get_recent_failed_attempts_by_ip(ip_address, window_seconds):
        """Get number of recent failed login attempts by IP."""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT COUNT(*) as count FROM login_attempts
            WHERE ip_address = ? AND success = 0
            AND datetime(timestamp) > datetime('now', '-' || ? || ' seconds')
        ''', (ip_address, window_seconds))
        row = cursor.fetchone()
        return row['count'] if row else 0

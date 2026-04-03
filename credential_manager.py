"""Credential Manager for Portal Authentication.

Handles encrypted storage and retrieval of user credentials for tennis portals.
Uses Fernet encryption (AES-256) for secure storage.
"""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from auth.models import PortalCredentials
from database.db import get_db


class CredentialManager:
    """Manages encrypted portal credentials for users."""

    # Available portals
    PORTALS = {
        'arsenal': 'Das Spiel Arsenal',
        'postsv': 'Post SV Wien'
    }

    def __init__(self):
        """Initialize credential manager with encryption key."""
        self.encryption_key = self._get_encryption_key()
        self.fernet = Fernet(self.encryption_key)

    def _get_encryption_key(self):
        """Get or generate encryption key from environment."""
        key_env = os.getenv('CREDENTIAL_ENCRYPTION_KEY')

        if key_env:
            # Use provided key
            try:
                return base64.urlsafe_b64decode(key_env)
            except Exception:
                pass

        # Generate key from SECRET_KEY (fallback for development)
        import config
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'tennis_booking_salt',  # Fixed salt for deterministic key
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(config.SECRET_KEY.encode()))
        return key

    def encrypt_password(self, password):
        """Encrypt a password."""
        return self.fernet.encrypt(password.encode()).decode()

    def decrypt_password(self, encrypted_password):
        """Decrypt a password."""
        return self.fernet.decrypt(encrypted_password.encode()).decode()

    def save_credentials(self, user_id, portal_name, username, password):
        """Save or update portal credentials for a user."""
        if portal_name not in self.PORTALS:
            raise ValueError(f"Unknown portal: {portal_name}")

        # Encrypt password
        encrypted_password = self.encrypt_password(password)

        # Get existing credentials or create new
        creds = PortalCredentials.get_by_user_and_portal(user_id, portal_name)

        if creds:
            creds.username = username
            creds.password_encrypted = encrypted_password
        else:
            creds = PortalCredentials(
                user_id=user_id,
                portal_name=portal_name,
                username=username,
                password_encrypted=encrypted_password
            )

        creds.save()
        return True

    def get_credentials(self, user_id, portal_name):
        """Get decrypted credentials for a portal."""
        if portal_name not in self.PORTALS:
            return None

        creds = PortalCredentials.get_by_user_and_portal(user_id, portal_name)

        if not creds:
            return None

        return {
            'username': creds.username,
            'password': self.decrypt_password(creds.password_encrypted),
            'portal_name': portal_name
        }

    def get_all_credentials(self, user_id):
        """Get all portal credentials for a user (passwords decrypted)."""
        all_creds = PortalCredentials.get_all_by_user(user_id)

        result = []
        for cred in all_creds:
            result.append({
                'portal_name': cred.portal_name,
                'portal_display_name': self.PORTALS.get(cred.portal_name, cred.portal_name),
                'username': cred.username,
                'configured': True,
                'updated_at': cred.updated_at
            })

        return result

    def get_all_portals_status(self, user_id):
        """Get status of all portals (configured or not)."""
        configured_creds = PortalCredentials.get_all_by_user(user_id)
        configured_portals = {c.portal_name for c in configured_creds}

        result = []
        for portal_key, portal_name in self.PORTALS.items():
            if portal_key in configured_portals:
                cred = next(c for c in configured_creds if c.portal_name == portal_key)
                result.append({
                    'portal_key': portal_key,
                    'portal_name': portal_name,
                    'configured': True,
                    'username': cred.username,
                    'updated_at': cred.updated_at
                })
            else:
                result.append({
                    'portal_key': portal_key,
                    'portal_name': portal_name,
                    'configured': False,
                    'username': None,
                    'updated_at': None
                })

        return result

    def delete_credentials(self, user_id, portal_name):
        """Delete portal credentials for a user."""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            DELETE FROM portal_credentials
            WHERE user_id = ? AND portal_name = ?
        ''', (user_id, portal_name))
        db.commit()
        return True

    def verify_credentials(self, user_id, portal_name):
        """
        Verify if credentials are valid by attempting login.
        Returns (success, message).
        """
        creds = self.get_credentials(user_id, portal_name)

        if not creds:
            return False, "Keine Zugangsdaten hinterlegt"

        # TODO: Implement actual portal login verification
        # For now, just check if credentials exist
        return True, "Zugangsdaten hinterlegt"

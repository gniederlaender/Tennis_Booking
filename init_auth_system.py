#!/usr/bin/env python3
"""Initialize the authentication system - install dependencies and create database."""

import subprocess
import sys
import os

def main():
    print("Initializing authentication system...")

    # Install dependencies
    print("\n1. Installing dependencies...")
    try:
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-q',
            'python-dotenv', 'cryptography', 'email-validator', 'flask-login'
        ], check=True)
        print("✓ Dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False

    # Initialize database
    print("\n2. Initializing database...")
    try:
        from database.db import init_db
        init_db()
        print("✓ Database initialized")
    except Exception as e:
        print(f"✗ Failed to initialize database: {e}")
        return False

    print("\n✓ Authentication system initialized successfully!")
    print("\nNext steps:")
    print("1. Start the application: gunicorn app:app --bind 0.0.0.0:5001")
    print("2. Visit http://localhost:5001/auth/register to create an account")
    print("3. Login and start using the application")

    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

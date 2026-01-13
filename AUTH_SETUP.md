# Authentication System Setup - Phase 1

## Summary

This document describes the Phase 1 implementation of the registration and login functionality for the Tennis Court Booking Finder application.

## What Was Implemented

### 1. Database Layer
- SQLite database with three tables:
  - `users` - User accounts with email, password hash, and profile info
  - `portal_credentials` - Encrypted tennis portal credentials per user
  - `login_attempts` - Login attempt tracking for rate limiting
- Database initialization script: `create_db.py`

### 2. Authentication Module (`auth/`)
- `models.py` - User, PortalCredentials, and LoginAttempt models
- `auth_routes.py` - Registration, login, logout, and status endpoints
- `decorators.py` - @login_required decorator for protected routes
- `utils.py` - Password hashing, encryption, and validation utilities

### 3. User Interface
- `templates/login.html` - Login page with email and password
- `templates/register.html` - Registration page with password strength indicator
- `templates/index.html` - Updated with authentication check and user menu

### 4. Configuration
- Updated `config.py` with database and security settings
- `.env` file for environment variables (SECRET_KEY, ENCRYPTION_KEY, etc.)
- `.env.example` template for deployment

### 5. Security Features
- Password hashing using Werkzeug PBKDF2
- Rate limiting on login attempts (5 attempts per 15 minutes)
- Secure session cookies (httpOnly, sameSite)
- Email validation
- Password complexity requirements (8+ chars, uppercase, lowercase, number)

## Setup Instructions

### 1. Install Dependencies

```bash
./install_auth_deps.sh
```

Or manually:
```bash
venv/bin/pip install python-dotenv cryptography email-validator flask-login
```

### 2. Database Initialization

The database has already been created. If you need to recreate it:
```bash
python3 create_db.py
```

### 3. Restart Application

```bash
pm2 restart tennis-booking
```

Or manually:
```bash
venv/bin/gunicorn app:app --bind 0.0.0.0:5001 --workers 2 --timeout 120
```

### 4. First Time Usage

1. Visit http://localhost:5001/auth/register
2. Create your account with:
   - Email address
   - Password (min 8 chars, 1 uppercase, 1 lowercase, 1 number)
   - Optional: First and last name
3. You'll be automatically logged in after registration
4. Start using the tennis court finder

## API Endpoints

### Authentication Endpoints
- `POST /auth/register` - Create new user account
- `POST /auth/login` - Authenticate user
- `GET/POST /auth/logout` - End user session
- `GET /auth/status` - Check authentication status

### Protected Endpoints (Require Login)
- `GET /` - Main search page
- `POST /search` - Search courts/trainers
- `POST /book` - Book court
- `GET /health` - Health check (no auth required)

## Security Configuration

The following environment variables are configured in `.env`:

- `SECRET_KEY` - Flask session secret key
- `ENCRYPTION_KEY` - Fernet encryption key for portal credentials
- `SESSION_COOKIE_SECURE` - HTTPS-only cookies (set to True in production)
- `SESSION_COOKIE_HTTPONLY` - Prevent JavaScript access to cookies
- `SESSION_COOKIE_SAMESITE` - CSRF protection
- `MAX_LOGIN_ATTEMPTS` - Maximum failed login attempts (default: 5)
- `LOGIN_RATE_LIMIT_WINDOW` - Rate limit window in seconds (default: 900)

## Testing

### Manual Testing Checklist

1. **Registration Flow**
   - [ ] Visit /auth/register
   - [ ] Try weak password (should reject)
   - [ ] Try mismatched passwords (should reject)
   - [ ] Try invalid email (should reject)
   - [ ] Register with valid credentials (should succeed)
   - [ ] Try registering same email again (should reject)

2. **Login Flow**
   - [ ] Visit /auth/login
   - [ ] Try wrong password (should reject)
   - [ ] Try non-existent email (should reject)
   - [ ] Try 6 failed attempts (should rate limit)
   - [ ] Login with correct credentials (should succeed)
   - [ ] Verify redirect to home page

3. **Session Management**
   - [ ] After login, refresh page (should stay logged in)
   - [ ] Access protected page (should work)
   - [ ] Logout
   - [ ] Try to access protected page (should redirect to login)

4. **Authentication Check**
   - [ ] Visit / without login (should redirect to /auth/login)
   - [ ] Login and visit / (should show main page with user email)
   - [ ] User menu shows email address
   - [ ] Logout button works

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    email_verified BOOLEAN DEFAULT 0
);
```

### Portal Credentials Table
```sql
CREATE TABLE portal_credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    portal_name VARCHAR(50) NOT NULL,
    username VARCHAR(255) NOT NULL,
    password_encrypted TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, portal_name)
);
```

### Login Attempts Table
```sql
CREATE TABLE login_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255),
    ip_address VARCHAR(50),
    success BOOLEAN,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Files Created/Modified

### New Files
- `auth/__init__.py` - Auth package initialization
- `auth/models.py` - Database models
- `auth/auth_routes.py` - Authentication routes
- `auth/decorators.py` - Login required decorator
- `auth/utils.py` - Authentication utilities
- `database/__init__.py` - Database package initialization
- `database/db.py` - Database connection and initialization
- `templates/login.html` - Login page
- `templates/register.html` - Registration page
- `.env` - Environment variables (not in git)
- `.env.example` - Environment template
- `create_db.py` - Database creation script
- `install_auth_deps.sh` - Dependency installation script
- `init_auth_system.sh` - Full system initialization script
- `AUTH_SETUP.md` - This file

### Modified Files
- `app.py` - Added authentication integration
- `templates/index.html` - Added auth check and user menu
- `config.py` - Added database and security configuration
- `requirements.txt` - Added authentication dependencies
- `.gitignore` - Added database and .env exclusions

## Next Steps (Phase 2+)

Phase 1 is now complete. Future phases will add:

- **Phase 2**: Portal credentials management (profile page for users to add Das Spiel/Post SV credentials)
- **Phase 3**: User-specific preferences and booking history
- **Phase 4**: Security hardening (CSRF protection, account lockout)
- **Phase 5**: Enhanced features (email verification, password reset)

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'flask'"
**Solution**: Install dependencies: `./install_auth_deps.sh`

### Issue: "No such table: users"
**Solution**: Initialize database: `python3 create_db.py`

### Issue: "Invalid email or password" even with correct credentials
**Solution**: Check that you registered the account first. Passwords are case-sensitive.

### Issue: "Too many failed login attempts"
**Solution**: Wait 15 minutes or check the database to clear login_attempts table.

### Issue: Application won't start
**Solution**:
1. Check logs: `tail -f logs/error.log`
2. Verify .env file exists and has valid keys
3. Verify database exists: `ls -la tennis_booking.db`

## Support

For issues or questions, refer to:
- Main documentation: `README.md`
- Full specification: `REGISTRATION_LOGIN_SPECIFICATION.md`
- Git history: `git log`

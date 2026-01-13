# Registration and Login Functionality - Specification

## Document Overview
**Created:** 2026-01-13
**Version:** 1.0
**Status:** SPECIFICATION ONLY - NOT IMPLEMENTED
**Project:** Tennis Court Booking Finder - Vienna

---

## 1. Executive Summary

This specification defines a registration and login system for the Tennis Court Booking Finder application. The system will enable users to:
- Create personal accounts
- Authenticate securely
- Store their portal credentials (Das Spiel, Post SV Wien)
- Maintain personalized preferences and booking history
- Access the application from multiple devices

### Current State
The application currently:
- Stores portal credentials in a single `credentials.json` file (shared globally)
- Stores user preferences in `user_preferences.json` (single user)
- Stores booking history in `booking_history.json` (single user)
- Has no multi-user support
- Has no authentication layer

### Target State
After implementation:
- Multi-user support with individual accounts
- Secure authentication system
- User-specific credentials for tennis portals
- User-specific preferences and booking history
- Protected API endpoints

---

## 2. Technical Architecture

### 2.1 Technology Stack

**Backend:**
- Flask (already in use)
- SQLite database (lightweight, file-based, no additional infrastructure)
- SQLAlchemy ORM (optional, but recommended for cleaner code)
- Flask-Login (session management)
- Werkzeug (password hashing - already included with Flask)
- python-dotenv (for environment configuration)

**Frontend:**
- Existing HTML/CSS/JavaScript setup
- No framework needed (keep it simple)
- Session-based authentication (cookies)

**Security:**
- bcrypt or Werkzeug's generate_password_hash for password hashing
- Flask session cookies (httpOnly, secure flags)
- CSRF protection (Flask-WTF or manual implementation)
- Rate limiting for login attempts (optional but recommended)

### 2.2 Database Schema

```sql
-- Users table
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

-- Portal credentials table (encrypted storage)
CREATE TABLE portal_credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    portal_name VARCHAR(50) NOT NULL,  -- 'dasspiel' or 'postsv'
    username VARCHAR(255) NOT NULL,
    password_encrypted TEXT NOT NULL,  -- Encrypted, not hashed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, portal_name)
);

-- User preferences table (replaces user_preferences.json)
CREATE TABLE user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    preference_data TEXT NOT NULL,  -- JSON blob
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- User selections table (replaces selections in user_preferences.json)
CREATE TABLE user_selections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    venue VARCHAR(255),
    date DATE,
    time VARCHAR(10),
    day_of_week VARCHAR(20),
    time_of_day VARCHAR(20),
    price VARCHAR(50),
    court_type VARCHAR(50),
    location VARCHAR(255),
    indoor_outdoor VARCHAR(50),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Booking history table (replaces booking_history.json)
CREATE TABLE booking_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50),  -- 'success', 'failed', 'error'
    slot_data TEXT NOT NULL,  -- JSON blob with full slot details
    error_message TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Session tokens table (optional - for remember me functionality)
CREATE TABLE session_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Login attempts table (for rate limiting and security)
CREATE TABLE login_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255),
    ip_address VARCHAR(50),
    success BOOLEAN,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2.3 File Structure

```
Tennis_Booking/
├── app.py                          # Main Flask app (update)
├── main.py                         # CLI (update for user context)
├── auth/
│   ├── __init__.py
│   ├── models.py                   # Database models
│   ├── auth_routes.py              # Login/register/logout routes
│   ├── decorators.py               # @login_required decorator
│   └── utils.py                    # Password hashing, encryption
├── database/
│   ├── __init__.py
│   ├── db.py                       # Database connection and setup
│   └── migrations/                 # SQL migration scripts
├── templates/
│   ├── index.html                  # Update with login check
│   ├── login.html                  # New
│   ├── register.html               # New
│   ├── profile.html                # New (settings page)
│   └── base.html                   # New (base template)
├── static/
│   ├── css/
│   │   └── auth.css                # New
│   └── js/
│       └── auth.js                 # New
├── config.py                       # Update with DB config
├── requirements.txt                # Update with new dependencies
└── tennis_booking.db               # SQLite database file (gitignored)
```

---

## 3. User Flows

### 3.1 Registration Flow

**Endpoint:** `POST /auth/register`

**Steps:**
1. User visits `/register` page
2. User fills registration form:
   - Email (required, validated)
   - Password (required, min 8 chars, complexity rules)
   - Confirm password (required, must match)
   - First name (optional)
   - Last name (optional)
3. Frontend validates form
4. Submit to backend
5. Backend validation:
   - Email format valid
   - Email not already registered
   - Password meets complexity requirements
   - Passwords match
6. Create user account:
   - Hash password with bcrypt
   - Store in database
   - Create user_id
7. Send email verification (optional - phase 2)
8. Auto-login user (create session)
9. Redirect to profile setup page

**Validation Rules:**
- Email: Valid format, unique, max 255 chars
- Password: Min 8 characters, at least 1 uppercase, 1 lowercase, 1 number
- Names: Optional, max 100 chars each

**Error Handling:**
- Email already exists: "An account with this email already exists"
- Invalid email: "Please enter a valid email address"
- Password too weak: "Password must be at least 8 characters with uppercase, lowercase, and number"
- Passwords don't match: "Passwords do not match"
- Server error: "Registration failed. Please try again later"

### 3.2 Login Flow

**Endpoint:** `POST /auth/login`

**Steps:**
1. User visits `/login` page
2. User enters credentials:
   - Email
   - Password
   - Remember me (optional checkbox)
3. Frontend validates form (not empty)
4. Submit to backend
5. Backend validation:
   - Check rate limiting (max 5 attempts per 15 minutes)
   - Find user by email
   - Verify password hash
   - Check if account is active
6. Create session:
   - Set Flask session user_id
   - Update last_login timestamp
   - If "remember me": create long-lived session token
7. Log successful login attempt
8. Redirect to home page (/)

**Security Features:**
- Rate limiting: Max 5 failed attempts per IP per 15 minutes
- Log all login attempts (success and failure)
- Account lockout after 10 failed attempts in 1 hour (optional)
- Secure session cookies (httpOnly, secure, sameSite)

**Error Handling:**
- Invalid credentials: "Invalid email or password" (don't specify which)
- Account locked: "Too many failed login attempts. Please try again in 15 minutes"
- Account inactive: "Your account has been deactivated. Please contact support"
- Server error: "Login failed. Please try again later"

### 3.3 Logout Flow

**Endpoint:** `POST /auth/logout`

**Steps:**
1. User clicks logout button
2. Backend clears session
3. Delete remember-me token if exists
4. Redirect to login page

### 3.4 Profile/Settings Flow

**Endpoint:** `GET /profile`, `POST /profile/update`

**Steps:**
1. User navigates to profile page (protected route)
2. Display current settings:
   - User info (email, name)
   - Portal credentials section
   - Preference history stats
   - Booking history
3. User can update:
   - Name
   - Password (requires old password)
   - Portal credentials (Das Spiel, Post SV Wien)
4. Save changes to database

**Portal Credentials Section:**
- Two expandable panels: "Das Spiel Credentials" and "Post SV Wien Credentials"
- Each panel shows:
   - Username field
   - Password field (masked)
   - "Test Connection" button
   - Last updated timestamp
- Credentials are encrypted before storage

---

## 4. API Endpoints

### 4.1 Authentication Endpoints

```
POST   /auth/register         - Create new user account
POST   /auth/login            - Authenticate user
POST   /auth/logout           - End user session
GET    /auth/status           - Check if user is authenticated
POST   /auth/forgot-password  - Request password reset (phase 2)
POST   /auth/reset-password   - Reset password with token (phase 2)
```

### 4.2 Protected Endpoints (Require Login)

All existing endpoints become protected:
```
GET    /                      - Main search page (require auth)
POST   /search                - Search courts/trainers (require auth)
POST   /book                  - Book court (require auth)
GET    /health                - Health check (no auth required)
GET    /profile               - User profile page (require auth)
POST   /profile/update        - Update profile (require auth)
POST   /profile/credentials   - Update portal credentials (require auth)
GET    /profile/bookings      - Get booking history (require auth)
GET    /profile/preferences   - Get user preferences (require auth)
```

### 4.3 API Request/Response Examples

**Register:**
```json
// POST /auth/register
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "confirm_password": "SecurePass123",
  "first_name": "John",
  "last_name": "Doe"
}

// Response 201
{
  "success": true,
  "message": "Account created successfully",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

**Login:**
```json
// POST /auth/login
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "remember_me": true
}

// Response 200
{
  "success": true,
  "message": "Login successful",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John"
  }
}
```

**Update Portal Credentials:**
```json
// POST /profile/credentials
{
  "portal": "dasspiel",
  "username": "user@example.com",
  "password": "portal_password"
}

// Response 200
{
  "success": true,
  "message": "Credentials updated successfully",
  "portal": "dasspiel"
}
```

---

## 5. Security Considerations

### 5.1 Password Security
- Use bcrypt or Werkzeug's `generate_password_hash` with PBKDF2
- Never store plain text passwords
- Minimum password requirements enforced
- Password strength indicator on registration form

### 5.2 Portal Credentials Encryption
Portal credentials (Das Spiel, Post SV Wien) are different from user passwords:
- These need to be **encrypted** (not hashed) because we need to decrypt them to use them
- Use symmetric encryption (Fernet from cryptography library)
- Store encryption key in environment variable (not in code)
- Key should be unique per installation

Example:
```python
from cryptography.fernet import Fernet

# Generate key once and store in .env
# key = Fernet.generate_key()

def encrypt_password(plain_password, key):
    f = Fernet(key)
    return f.encrypt(plain_password.encode()).decode()

def decrypt_password(encrypted_password, key):
    f = Fernet(key)
    return f.decrypt(encrypted_password.encode()).decode()
```

### 5.3 Session Management
- Use Flask's built-in session management
- Set secure session configuration:
  ```python
  app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
  app.config['SESSION_COOKIE_HTTPONLY'] = True  # No JavaScript access
  app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
  app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
  ```

### 5.4 CSRF Protection
- Add CSRF tokens to all forms
- Validate tokens on POST requests
- Use Flask-WTF or manual implementation

### 5.5 Rate Limiting
- Limit login attempts: 5 per 15 minutes per IP
- Limit registration: 3 per hour per IP
- Use simple in-memory counter or database table

### 5.6 SQL Injection Prevention
- Use parameterized queries (SQLAlchemy ORM handles this)
- Never concatenate user input into SQL strings

### 5.7 XSS Prevention
- Escape all user input in templates (Jinja2 auto-escapes)
- Sanitize any user-generated content
- Set Content-Security-Policy headers

---

## 6. Data Migration Strategy

### 6.1 Migrating Existing Data

Current single-user data needs to be migrated:

**Step 1: Backup**
- Copy `credentials.json`, `user_preferences.json`, `booking_history.json`

**Step 2: Create Default User**
- Create migration script that:
  - Creates first user account (admin/default user)
  - Migrates existing credentials to that user
  - Migrates existing preferences to that user
  - Migrates existing booking history to that user

**Step 3: Update Code**
- Modify `booking.py` to load credentials per user
- Modify `preference_engine.py` to work per user
- Update all data access to be user-scoped

**Migration Script Example:**
```python
# migrate_to_multiuser.py
import json
from database.db import init_db
from auth.models import User, PortalCredentials
from auth.utils import hash_password, encrypt_password

def migrate():
    # Initialize database
    init_db()

    # Create default user
    default_user = User(
        email="admin@tennisbooking.local",
        password_hash=hash_password("changeme123"),
        first_name="Admin",
        is_active=True
    )
    db.session.add(default_user)
    db.session.commit()

    # Migrate credentials
    with open('credentials.json', 'r') as f:
        creds = json.load(f)

    for portal_name, portal_creds in creds.items():
        pc = PortalCredentials(
            user_id=default_user.id,
            portal_name=portal_name,
            username=portal_creds['username'],
            password_encrypted=encrypt_password(portal_creds['password'])
        )
        db.session.add(pc)

    # Migrate preferences
    with open('user_preferences.json', 'r') as f:
        prefs = json.load(f)

    for selection in prefs.get('selections', []):
        # Create UserSelection records
        pass

    # Migrate booking history
    with open('booking_history.json', 'r') as f:
        history = json.load(f)

    for booking in history:
        # Create BookingHistory records
        pass

    db.session.commit()
    print("Migration completed!")
```

---

## 7. UI/UX Design

### 7.1 Login Page (`/login`)

**Layout:**
```
+------------------------------------------+
|         🎾 Tennis Court Finder          |
+------------------------------------------+
|                                          |
|     +------------------------------+     |
|     |         Login                |     |
|     |                              |     |
|     | Email:                       |     |
|     | [___________________________]|     |
|     |                              |     |
|     | Password:                    |     |
|     | [___________________________]|     |
|     |                              |     |
|     | [ ] Remember me              |     |
|     |                              |     |
|     |        [Login Button]        |     |
|     |                              |     |
|     | Don't have an account?       |     |
|     | [Register here]              |     |
|     +------------------------------+     |
|                                          |
+------------------------------------------+
```

**Features:**
- Clean, minimal design matching existing UI
- Purple gradient background (consistent with index.html)
- White card with form
- Email and password fields
- Remember me checkbox
- Link to registration page
- Error messages display above form

### 7.2 Registration Page (`/register`)

**Layout:**
```
+------------------------------------------+
|         🎾 Tennis Court Finder          |
+------------------------------------------+
|                                          |
|     +------------------------------+     |
|     |      Create Account          |     |
|     |                              |     |
|     | Email:                       |     |
|     | [___________________________]|     |
|     |                              |     |
|     | Password:                    |     |
|     | [___________________________]|     |
|     | [Password strength: ----]    |     |
|     |                              |     |
|     | Confirm Password:            |     |
|     | [___________________________]|     |
|     |                              |     |
|     | First Name (optional):       |     |
|     | [___________________________]|     |
|     |                              |     |
|     | Last Name (optional):        |     |
|     | [___________________________]|     |
|     |                              |     |
|     |      [Register Button]       |     |
|     |                              |     |
|     | Already have an account?     |     |
|     | [Login here]                 |     |
|     +------------------------------+     |
|                                          |
+------------------------------------------+
```

**Features:**
- Password strength indicator
- Real-time validation feedback
- Link to login page
- Terms of service checkbox (optional)

### 7.3 Profile/Settings Page (`/profile`)

**Layout:**
```
+------------------------------------------+
|  🎾 Tennis Court Finder    [Logout]     |
+------------------------------------------+
|                                          |
|  Profile Settings                        |
|                                          |
|  +------------------------------------+  |
|  | Account Information                |  |
|  | Email: user@example.com            |  |
|  | Name: [John______] [Doe_________]  |  |
|  | Member since: Jan 13, 2026         |  |
|  | [Update Info]                      |  |
|  +------------------------------------+  |
|                                          |
|  +------------------------------------+  |
|  | Portal Credentials                 |  |
|  |                                    |  |
|  | Das Spiel (Arsenal)        [Edit]  |  |
|  | Status: ✓ Connected                |  |
|  |                                    |  |
|  | Post SV Wien               [Edit]  |  |
|  | Status: ✗ Not configured           |  |
|  +------------------------------------+  |
|                                          |
|  +------------------------------------+  |
|  | Preferences & History              |  |
|  | Total bookings: 5                  |  |
|  | Preferred venue: Arsenal           |  |
|  | Preferred time: Evening            |  |
|  | [View Full History]                |  |
|  +------------------------------------+  |
|                                          |
|  +------------------------------------+  |
|  | Security                           |  |
|  | [Change Password]                  |  |
|  | [Delete Account]                   |  |
|  +------------------------------------+  |
|                                          |
+------------------------------------------+
```

**Features:**
- Portal credentials management with edit modal
- Test connection button for each portal
- Booking statistics
- Password change form
- Account deletion (with confirmation)

### 7.4 Updated Main Page (`/`)

**Changes:**
- Add user menu in top-right corner:
  - Display: "👤 user@example.com ▼"
  - Dropdown: Profile, Logout
- No changes to search functionality
- All existing features remain the same

---

## 8. Configuration Management

### 8.1 Environment Variables

Create `.env` file (gitignored):
```
# Flask Configuration
SECRET_KEY=your-secret-key-here-change-in-production
FLASK_ENV=development

# Database
DATABASE_URL=sqlite:///tennis_booking.db

# Encryption
ENCRYPTION_KEY=your-fernet-key-here

# Security
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# Rate Limiting
MAX_LOGIN_ATTEMPTS=5
LOGIN_RATE_LIMIT_WINDOW=900  # 15 minutes in seconds

# Optional: Email (for password reset)
SMTP_SERVER=
SMTP_PORT=
SMTP_USERNAME=
SMTP_PASSWORD=
```

### 8.2 Config File Updates

Update `config.py`:
```python
import os
from dotenv import load_dotenv

load_dotenv()

# Existing config
MAX_RESULTS = 20
PREFERENCES_FILE = 'user_preferences.json'  # Deprecated, keep for migration
CONFIDENCE_THRESHOLD = 5

# New config
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///tennis_booking.db')
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')

# Security
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'True') == 'True'
SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'True') == 'True'
SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')

# Rate limiting
MAX_LOGIN_ATTEMPTS = int(os.getenv('MAX_LOGIN_ATTEMPTS', 5))
LOGIN_RATE_LIMIT_WINDOW = int(os.getenv('LOGIN_RATE_LIMIT_WINDOW', 900))
```

---

## 9. Implementation Phases

### Phase 1: Core Authentication (MVP)
**Priority: HIGH**
**Estimated effort: 2-3 days**

Tasks:
1. Set up database schema
2. Create User model
3. Implement registration endpoint
4. Implement login endpoint
5. Implement logout endpoint
6. Create @login_required decorator
7. Build login page UI
8. Build registration page UI
9. Update main page with authentication check
10. Create migration script for existing data

Deliverables:
- Users can register and login
- Sessions work correctly
- Existing data migrated to first user
- Main page requires authentication

### Phase 2: Portal Credentials Management
**Priority: HIGH**
**Estimated effort: 1-2 days**

Tasks:
1. Create PortalCredentials model
2. Implement encryption/decryption utilities
3. Create profile page UI
4. Implement credentials update endpoint
5. Update booking.py to load credentials per user
6. Add "Test Connection" functionality

Deliverables:
- Users can manage their portal credentials
- Bookings use user-specific credentials
- Credentials are encrypted at rest

### Phase 3: User-Specific Data
**Priority: MEDIUM**
**Estimated effort: 1-2 days**

Tasks:
1. Create UserSelections model
2. Create BookingHistory model
3. Update preference_engine.py for per-user preferences
4. Update booking history to be per-user
5. Add booking history view to profile page

Deliverables:
- Preferences are per-user
- Booking history is per-user
- Profile page shows user-specific data

### Phase 4: Security Hardening
**Priority: MEDIUM**
**Estimated effort: 1 day**

Tasks:
1. Implement rate limiting
2. Add CSRF protection
3. Implement login attempt logging
4. Add account lockout mechanism
5. Security audit and testing

Deliverables:
- Rate limiting active
- CSRF tokens on all forms
- Login attempts logged
- Account lockout works

### Phase 5: Enhanced Features (Optional)
**Priority: LOW**
**Estimated effort: 2-3 days**

Tasks:
1. Email verification
2. Password reset flow
3. Remember me functionality
4. Account deletion
5. Email notifications

Deliverables:
- Email verification works
- Password reset via email
- Remember me checkbox functional
- Users can delete accounts

---

## 10. Testing Strategy

### 10.1 Unit Tests

Test files to create:
- `tests/test_auth_models.py` - Test User model
- `tests/test_auth_utils.py` - Test password hashing, encryption
- `tests/test_auth_routes.py` - Test login/register/logout
- `tests/test_auth_decorators.py` - Test @login_required
- `tests/test_portal_credentials.py` - Test encryption/decryption

### 10.2 Integration Tests

- Test complete registration flow
- Test complete login flow
- Test booking with user-specific credentials
- Test preferences per user
- Test session management
- Test rate limiting

### 10.3 Security Tests

- Test password hashing (verify bcrypt is used)
- Test SQL injection attempts
- Test XSS attempts
- Test CSRF protection
- Test rate limiting
- Test session hijacking prevention

### 10.4 Manual Testing Checklist

- [ ] Register new user
- [ ] Login with correct credentials
- [ ] Login with incorrect credentials
- [ ] Logout
- [ ] Access protected page without login (should redirect)
- [ ] Update profile information
- [ ] Add Das Spiel credentials
- [ ] Add Post SV Wien credentials
- [ ] Book court with user credentials
- [ ] View booking history
- [ ] Check preferences are user-specific
- [ ] Test "Remember me" functionality
- [ ] Test password strength validator
- [ ] Test rate limiting (try 6 failed logins)

---

## 11. Rollout Strategy

### 11.1 Pre-Deployment

1. **Backup all data:**
   ```bash
   cp credentials.json credentials.json.backup
   cp user_preferences.json user_preferences.json.backup
   cp booking_history.json booking_history.json.backup
   ```

2. **Set up environment:**
   - Create `.env` file with all required variables
   - Generate encryption key: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
   - Set strong SECRET_KEY

3. **Database setup:**
   ```bash
   python database/init_db.py  # Create tables
   python migrate_to_multiuser.py  # Migrate existing data
   ```

### 11.2 Deployment

1. **Install new dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run migrations:**
   ```bash
   python database/init_db.py
   python migrate_to_multiuser.py
   ```

3. **Restart application:**
   ```bash
   pm2 restart tennis-booking
   ```

4. **Verify:**
   - Check logs for errors
   - Test login with migrated user
   - Test booking functionality
   - Test search functionality

### 11.3 Post-Deployment

1. **Monitor logs** for first 24 hours
2. **Test all critical flows** manually
3. **Get user feedback**
4. **Document any issues**

### 11.4 Rollback Plan

If issues occur:
1. Stop application
2. Restore database: `rm tennis_booking.db`
3. Restore backup data files
4. Revert code to previous version
5. Restart application

---

## 12. Dependencies Update

Add to `requirements.txt`:
```
python-dateutil==2.8.2
beautifulsoup4==4.12.2
requests==2.31.0
flask==3.0.0
gunicorn==23.0.0
selenium==4.16.0
webdriver-manager==4.0.1

# New dependencies for authentication
flask-login==0.6.3
python-dotenv==1.0.0
cryptography==41.0.7
email-validator==2.1.0  # For email validation
```

---

## 13. Known Limitations & Future Enhancements

### Limitations
- SQLite is single-threaded (consider PostgreSQL for production with many users)
- No email verification in Phase 1 (users can register with any email)
- No 2FA support
- No OAuth/social login
- No API rate limiting per user (only per IP)
- No user roles/permissions (all users have same access)

### Future Enhancements
- Multi-factor authentication (2FA)
- OAuth integration (Google, Facebook login)
- User roles (admin, regular user)
- Shared bookings (multiple users for one booking)
- Team accounts (multiple users under organization)
- API keys for programmatic access
- Mobile app with separate authentication
- Activity log (audit trail)
- Export user data (GDPR compliance)
- Dark mode preference per user

---

## 14. Security Checklist

Before going live:
- [ ] Change SECRET_KEY to strong random value
- [ ] Change default admin password
- [ ] Enable HTTPS (SESSION_COOKIE_SECURE=True)
- [ ] Set up CSRF protection
- [ ] Enable rate limiting
- [ ] Review all SQL queries for injection vulnerabilities
- [ ] Test XSS protection
- [ ] Verify passwords are hashed with bcrypt
- [ ] Verify portal credentials are encrypted
- [ ] Store encryption key securely (not in code)
- [ ] Add security headers (CSP, X-Frame-Options, etc.)
- [ ] Set up logging for security events
- [ ] Test session timeout
- [ ] Test account lockout
- [ ] Review error messages (don't leak sensitive info)
- [ ] Set up monitoring and alerting

---

## 15. Documentation Updates Needed

After implementation:
- Update README.md with authentication instructions
- Create USER_GUIDE.md with:
  - How to register
  - How to login
  - How to manage portal credentials
  - How to view booking history
- Create ADMIN_GUIDE.md with:
  - How to set up environment
  - How to migrate data
  - How to manage users (if admin features added)
- Update API documentation
- Create SECURITY.md with responsible disclosure policy

---

## 16. Open Questions & Decisions Needed

### Questions to resolve before implementation:

1. **Email Verification:**
   - Should we require email verification before allowing bookings?
   - Phase 1: No verification (accept any email)
   - Phase 2: Add verification

2. **Password Policy:**
   - Minimum 8 characters with uppercase, lowercase, number? ✓
   - Special characters required? (Recommendation: No, to keep it simple)
   - Maximum length? (Recommendation: 128 characters)

3. **Session Timeout:**
   - How long should sessions last? (Recommendation: 7 days)
   - Should we have different timeouts for "Remember me"? (Recommendation: 30 days)

4. **Multi-Device Access:**
   - Should one user be able to login from multiple devices? (Recommendation: Yes)
   - Should we show active sessions? (Recommendation: Phase 2)

5. **Account Deletion:**
   - Hard delete or soft delete? (Recommendation: Soft delete - set is_active=False)
   - What happens to booking history? (Recommendation: Keep for records)

6. **CLI Support:**
   - Should CLI (main.py) support multi-user? (Recommendation: No, CLI uses default user)
   - Or should CLI prompt for login? (Recommendation: Phase 2)

7. **Database Choice:**
   - Start with SQLite? ✓
   - When to migrate to PostgreSQL? (When reaching ~100 users or multiple instances)

---

## 17. Success Metrics

How to measure success of this feature:

- **Adoption Rate:** % of users who create accounts
- **Authentication Success:** % of login attempts that succeed
- **Credentials Management:** % of users who configure portal credentials
- **Booking Success:** % of bookings that succeed after authentication added
- **Security:** Number of security incidents (target: 0)
- **Performance:** Login response time (target: < 500ms)
- **User Satisfaction:** Feedback from users about authentication flow

---

## 18. Appendix

### A. Example Code Snippets

**Password Hashing:**
```python
from werkzeug.security import generate_password_hash, check_password_hash

# Hash password
password_hash = generate_password_hash(password, method='pbkdf2:sha256')

# Verify password
is_valid = check_password_hash(password_hash, password)
```

**Credentials Encryption:**
```python
from cryptography.fernet import Fernet
import os

ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY').encode()

def encrypt_credential(plaintext):
    f = Fernet(ENCRYPTION_KEY)
    return f.encrypt(plaintext.encode()).decode()

def decrypt_credential(encrypted):
    f = Fernet(ENCRYPTION_KEY)
    return f.decrypt(encrypted.encode()).decode()
```

**Login Required Decorator:**
```python
from functools import wraps
from flask import session, redirect, url_for

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function
```

### B. Database Indexes

For better performance, add these indexes:
```sql
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_portal_credentials_user_id ON portal_credentials(user_id);
CREATE INDEX idx_user_selections_user_id ON user_selections(user_id);
CREATE INDEX idx_booking_history_user_id ON booking_history(user_id);
CREATE INDEX idx_login_attempts_email ON login_attempts(email);
CREATE INDEX idx_login_attempts_ip ON login_attempts(ip_address);
CREATE INDEX idx_login_attempts_timestamp ON login_attempts(timestamp);
```

### C. Environment Setup Script

```bash
#!/bin/bash
# setup_auth.sh

echo "Setting up authentication system..."

# Create .env file
cat > .env << EOF
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
FLASK_ENV=production
DATABASE_URL=sqlite:///tennis_booking.db
ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
MAX_LOGIN_ATTEMPTS=5
LOGIN_RATE_LIMIT_WINDOW=900
EOF

echo ".env file created"

# Install dependencies
pip install flask-login python-dotenv cryptography email-validator

# Backup existing data
cp credentials.json credentials.json.backup
cp user_preferences.json user_preferences.json.backup
cp booking_history.json booking_history.json.backup

echo "Backups created"

# Initialize database
python database/init_db.py

echo "Database initialized"

# Run migration
python migrate_to_multiuser.py

echo "Data migrated"

echo "Setup complete! Default user created with email: admin@tennisbooking.local"
echo "Password: changeme123 (please change immediately)"
```

---

## 19. Feedback & Todo Integration

**Status:** OPEN - This specification is ready for review and implementation planning.

**Todo Item to Keep Open:**
```json
{
  "id": "task-20260113-registration-login-spec",
  "type": "feature",
  "status": "open",
  "priority": "medium",
  "title": "Create a specification for registration and login functionality",
  "description": "Create a specification for a registration and login flow. Do not implement anything in this session, just think about the specification, write it and append it to this todo. Keep the status of this Todo open, in order to be automatically implemented with the next run",
  "specification": "REGISTRATION_LOGIN_SPECIFICATION.md",
  "created_at": "2026-01-13",
  "next_steps": [
    "Review this specification document",
    "Validate approach and technical decisions",
    "Prioritize implementation phases",
    "Begin Phase 1 implementation in next session"
  ]
}
```

---

**End of Specification Document**

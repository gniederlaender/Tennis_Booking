# Tennis Booking Finder - Vienna

A comprehensive web application for searching, booking, and managing tennis court reservations across multiple venues in Vienna, Austria. Features natural language processing, AI-powered chat interface, automated booking, trainer search, personalized newsletters, and Claude AI integration via Model Context Protocol (MCP).

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Database Schema](#database-schema)
- [Architecture](#architecture)
- [API Endpoints](#api-endpoints)
- [Cron Jobs](#cron-jobs)
- [MCP Server Integration](#mcp-server-integration)
- [Development](#development)
- [Deployment](#deployment)

---

## Features

### Public Features
- **Live Availability Dashboard** - 7×3 matrix showing weekly court availability (weekday × timeblock)
- **Natural Language Search** - Search using phrases like "next Monday 6pm", "morgen abend", "between 10 and 12"
- **Multi-Venue Support** - Das Spiel Arsenal + Post SV Wien
- **Responsive Design** - Modern glassmorphism UI with smooth animations

### Authenticated Features
- **Automated Court Booking** - API-first approach with Selenium fallback
- **Trainer Search** - Find available tennis trainers at Das Spiel Arsenal
- **AI Chat Interface** - Conversational booking assistant with intent detection
- **Preference Learning** - AI recommendations based on booking history
- **Encrypted Credentials** - Secure storage of portal login credentials (AES-256 Fernet)
- **Personalized Newsletter** - Weekly email with availability forecast for your preferred time slots
- **Profile Management** - Customize newsletter preferences and account settings

### AI Integration
- **MCP Server** - Claude Desktop integration via Model Context Protocol
- **Time Parser API** - RESTful endpoint for natural language time parsing
- **Fuzzy Matching** - Typo correction with confidence scoring
- **Context-Aware Chat** - Multi-turn conversations with entity extraction

---

## Technology Stack

### Backend
- **Framework:** Flask 3.0.0 (Python)
- **Database:** SQLite with schema migrations
- **Authentication:** Flask-Login with bcrypt password hashing
- **Encryption:** Cryptography (Fernet) for credential storage
- **Web Scraping:** BeautifulSoup4, Requests, Selenium
- **Date Parsing:** dateparser with German locale support
- **Text Matching:** RapidFuzz for typo correction
- **Server:** Gunicorn WSGI server
- **Proxy:** Apache with mod_proxy

### Frontend
- **Templates:** Jinja2
- **Styling:** Custom CSS with glassmorphism design
- **JavaScript:** Vanilla JS for dynamic interactions
- **UI/UX:** Modern gradient backgrounds, smooth transitions

### Integration
- **MCP Server:** httpx, uvicorn, SSE transport
- **Email:** SMTP with HTML templates
- **Automation:** Cron jobs for snapshots and newsletters

---

## Installation

### Prerequisites
- Python 3.12+
- Apache web server (for production)
- SQLite 3

### Step 1: Clone and Setup Virtual Environment

```bash
cd /opt/Tennis_Booking
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Initialize Database

```bash
python database/db.py
```

### Step 4: Configure Environment Variables

```bash
cp .env.example .env
nano .env  # Edit with your configuration
```

### Step 5: Generate Encryption Key

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Add the generated key to `.env` as `ENCRYPTION_KEY`.

---

## Configuration

### Environment Variables (`.env`)

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here-change-in-production
FLASK_ENV=production
DATABASE_URL=sqlite:///tennis_booking.db

# Encryption Key for Portal Credentials
# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=your-fernet-encryption-key-here

# Session Configuration
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
PERMANENT_SESSION_LIFETIME_DAYS=7

# Rate Limiting
MAX_LOGIN_ATTEMPTS=5
LOGIN_RATE_LIMIT_WINDOW=900

# SMTP Configuration (for Newsletter)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=user@example.com
SMTP_PASSWORD=password
SMTP_FROM=noreply@tennisfinder.at
SMTP_USE_TLS=True

# Newsletter Configuration
NEWSLETTER_SEND_DAY=monday
NEWSLETTER_SEND_TIME=08:00

# MCP Server Configuration
MCP_SERVER_PORT=8765
MCP_API_KEY=optional-api-key
FLASK_API_BASE_URL=http://localhost:5001
```

### Portal Credentials (Optional)

For Post SV Wien scraping, create `credentials.json`:

```json
{
  "postsv": {
    "username": "your_email@example.com",
    "password": "your_password"
  },
  "arsenal": {
    "username": "your_email@example.com",
    "password": "your_password"
  }
}
```

**Note:** User-specific portal credentials are stored encrypted in the database. The `credentials.json` file is only used as a fallback.

---

## Usage

### Running the Application

#### Development Mode
```bash
python app.py
```

#### Production Mode (Gunicorn)
```bash
gunicorn --bind 127.0.0.1:5001 app:app
```

#### With Apache Proxy
See `APACHE_PROXY_SETUP.md` for detailed configuration.

### Natural Language Time Parsing Examples

The application supports both German and English:

- `"next Monday 6-8pm"`
- `"morgen 18-20 Uhr"`
- `"7.1.2026 between 15:00 and 18:00"`
- `"tomorrow evening"`
- `"nachmittag am Freitag"`
- `"ASAP"` (searches next 7 days)
- `"weekend"` (Saturday + Sunday)

### Chat Interface Examples

- "Find me a court tomorrow evening at Arsenal"
- "I need a trainer for Monday morning"
- "Book the first option"
- "Show me my booking history"
- "What times are available on Friday?"

---

## Database Schema

### Tables

#### `users`
User accounts and authentication.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-incrementing user ID |
| `email` | VARCHAR(255) UNIQUE | User email (login) |
| `password_hash` | VARCHAR(255) | Bcrypt hashed password |
| `first_name` | VARCHAR(100) | User's first name |
| `last_name` | VARCHAR(100) | User's last name |
| `created_at` | TIMESTAMP | Account creation timestamp |
| `last_login` | TIMESTAMP | Last successful login |
| `is_active` | BOOLEAN | Account active status (default: 1) |
| `email_verified` | BOOLEAN | Email verification status (default: 0) |
| `newsletter_active` | BOOLEAN | Newsletter subscription (default: 0) |
| `newsletter_weekday` | INTEGER | Preferred weekday (0=Mon, 6=Sun) |
| `newsletter_timeblock` | TEXT | Preferred timeblock (`morning`, `midday`, `evening`) |

#### `portal_credentials`
Encrypted portal login credentials per user.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-incrementing credential ID |
| `user_id` | INTEGER | Foreign key to users table |
| `portal_name` | VARCHAR(50) | Portal identifier (`arsenal`, `postsv`) |
| `username` | VARCHAR(255) | Portal username/email |
| `password_encrypted` | TEXT | Fernet-encrypted password |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |

**Constraints:**
- `FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE`
- `UNIQUE(user_id, portal_name)`

#### `login_attempts`
Login attempt tracking for rate limiting and security.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-incrementing attempt ID |
| `email` | VARCHAR(255) | Attempted email address |
| `ip_address` | VARCHAR(50) | Source IP address |
| `success` | BOOLEAN | Login success status |
| `timestamp` | TIMESTAMP | Attempt timestamp |

#### `availability_snapshots`
Hourly aggregated court availability data.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-incrementing snapshot ID |
| `captured_at` | TIMESTAMP | Snapshot capture time |
| `location` | TEXT | Venue identifier (`arsenal`, `postsv`) |
| `weekday` | INTEGER | Day of week (0=Monday, 6=Sunday) |
| `timeblock` | TEXT | Time period (`morning`, `midday`, `evening`) |
| `available_slots` | INTEGER | Number of available slots |

**Timeblock Definitions:**
- `morning`: 07:00 - 12:00
- `midday`: 12:00 - 17:00
- `evening`: 17:00 - 22:00

### Database Indexes

Performance indexes for common queries:

```sql
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_portal_credentials_user_id ON portal_credentials(user_id);
CREATE INDEX idx_login_attempts_email ON login_attempts(email);
CREATE INDEX idx_login_attempts_ip ON login_attempts(ip_address);
CREATE INDEX idx_login_attempts_timestamp ON login_attempts(timestamp);
CREATE INDEX idx_snapshots_location_weekday_timeblock ON availability_snapshots(location, weekday, timeblock);
CREATE INDEX idx_snapshots_captured_at ON availability_snapshots(captured_at);
```

---

## Architecture

### Project Structure

```
/opt/Tennis_Booking/
├── app.py                          # Main Flask application
├── config.py                       # Configuration management
├── requirements.txt                # Python dependencies
├── tennis_booking.db               # SQLite database
│
├── auth/                           # Authentication module
│   ├── __init__.py
│   ├── auth_routes.py              # Login/register/logout routes
│   ├── models.py                   # User and credential models
│   ├── utils.py                    # Auth helper functions
│   └── decorators.py               # Login required decorator
│
├── database/                       # Database layer
│   ├── db.py                       # DB connection and schema
│   └── migrations/                 # Schema migration scripts
│
├── cron/                           # Automated scripts
│   ├── update_snapshots.py         # Hourly availability scraper
│   └── send_newsletter.py          # Weekly newsletter sender
│
├── time_parser/                    # Enhanced time parsing module
│   ├── __init__.py
│   ├── parser.py                   # Core parsing with confidence scoring
│   ├── normalizer.py               # Text normalization & typo correction
│   ├── keywords.py                 # German/English keyword dictionaries
│   ├── time_windows.py             # TimeWindow data structure
│   ├── routes.py                   # Time parser API endpoints
│   └── README.md                   # Time parser documentation
│
├── templates/                      # Jinja2 HTML templates
│   ├── landing.html                # Public landing page + dashboard
│   ├── index.html                  # Authenticated search page
│   ├── chat.html                   # AI chat interface
│   ├── login.html                  # Login page
│   ├── register.html               # Registration page
│   ├── profile.html                # User profile + newsletter settings
│   ├── credentials.html            # Portal credentials management
│   └── email/
│       └── newsletter.html         # Weekly newsletter template
│
├── static/                         # Static assets
│   ├── css/                        # Stylesheets
│   └── js/                         # JavaScript files
│
├── logs/                           # Application logs
│   ├── cron.log                    # Snapshot update logs
│   └── newsletter.log              # Newsletter sending logs
│
├── booking.py                      # Booking automation (DasSpiel, PostSV)
├── scrapers_v2.py                  # Court availability scrapers
├── trainer_finder.py               # Trainer search functionality
├── chat_engine.py                  # Conversational AI engine
├── preference_engine.py            # ML preference learning
├── credential_manager.py           # Encrypted credential storage
├── timeframe_parser.py             # Legacy time parser
├── mcp_server.py                   # Model Context Protocol server
│
└── Documentation/
    ├── README.md                   # This file
    ├── spec.md                     # Technical specification
    ├── CRON_SETUP.md               # Cron job configuration guide
    ├── AUTH_SETUP.md               # Authentication setup guide
    ├── MCP_SERVER_README.md        # MCP server documentation
    ├── APACHE_PROXY_SETUP.md       # Apache proxy configuration
    └── [various other docs]
```

### Data Flow

#### Court Search Flow
```
User Input → Time Parser → Scrapers → Results → Chat Engine (optional) → Display
```

#### Booking Flow
```
User Selection → Credential Validation → Booking API → Selenium Fallback → Confirmation
```

#### Dashboard Flow
```
[Cron Hourly]
Scrapers → update_snapshots.py → availability_snapshots (DB)
                                         ↓
                              Flask Route /api/dashboard/availability
                                         ↓
                              landing.html (7×3 Matrix Display)
```

#### Newsletter Flow
```
[Cron Monday 08:00]
availability_snapshots (DB) + users (DB) → send_newsletter.py
                                                  ↓
                                       newsletter.html (Template)
                                                  ↓
                                         SMTP → User Email
```

---

## API Endpoints

### Public Endpoints

#### `GET /`
Landing page with live availability dashboard.

#### `GET /health`
Health check endpoint.

#### `POST /api/dashboard/availability`
Get aggregated availability matrix.

**Response:**
```json
{
  "data": {
    "0": {  // Monday
      "morning": {"slots": 5, "color": "green"},
      "midday": {"slots": 2, "color": "yellow"},
      "evening": {"slots": 0, "color": "red"}
    },
    // ... other weekdays
  },
  "lastUpdated": "2026-04-07T10:00:00"
}
```

### Authenticated Endpoints

#### `GET /search-page`
Render search interface (requires login).

#### `POST /search`
Search for courts or trainers.

**Request:**
```json
{
  "query": "next Monday evening",
  "search_type": "courts"  // or "trainers"
}
```

#### `POST /book`
Book a selected court slot.

**Request:**
```json
{
  "venue": "arsenal",
  "court_name": "Platz 1 HALLE",
  "date": "2026-04-14",
  "time": "18:00-19:00"
}
```

#### `GET /chat`
Render AI chat interface.

#### `POST /api/chat`
Send message to chat engine.

**Request:**
```json
{
  "message": "Find me a court tomorrow evening"
}
```

#### `GET /profile`
User profile and newsletter settings.

#### `POST /profile/newsletter`
Update newsletter preferences.

**Request:**
```json
{
  "active": true,
  "weekday": 4,  // Friday
  "timeblock": "evening"
}
```

### Authentication Endpoints

#### `POST /auth/register`
Register new user account.

#### `POST /auth/login`
Authenticate user (rate limited: 5 attempts per 15 min).

#### `GET /auth/logout`
End user session.

#### `GET /auth/status`
Check authentication status.

### Time Parser API

#### `POST /time-parser/parse`
Parse natural language time expressions.

**Request:**
```json
{
  "query": "morgen abend 18-20 Uhr"
}
```

**Response:**
```json
{
  "success": true,
  "interpretation": "Tomorrow evening 18:00-20:00",
  "dates": ["2026-04-08"],
  "time_from": "18:00",
  "time_to": "20:00",
  "confidence": 0.95
}
```

---

## Cron Jobs

### Hourly Snapshot Update

**Script:** `cron/update_snapshots.py`
**Schedule:** Every hour at :00
**Purpose:** Scrape both venues and update availability snapshots

```bash
0 * * * * /opt/Tennis_Booking/venv/bin/python /opt/Tennis_Booking/cron/update_snapshots.py >> /opt/Tennis_Booking/logs/cron.log 2>&1
```

**Features:**
- Scrapes Arsenal and Post SV for next 7 days
- Aggregates by location, weekday, and timeblock
- Auto-cleanup: Deletes snapshots older than 30 days
- Error logging and retry logic

### Weekly Newsletter

**Script:** `cron/send_newsletter.py`
**Schedule:** Monday 08:00
**Purpose:** Send personalized availability emails

```bash
0 8 * * 1 /opt/Tennis_Booking/venv/bin/python /opt/Tennis_Booking/cron/send_newsletter.py >> /opt/Tennis_Booking/logs/newsletter.log 2>&1
```

**Features:**
- Fetches users with active newsletter subscriptions
- Generates 4-week availability forecast
- Color-coded availability indicators
- Deep links to booking page
- Unsubscribe functionality

See `CRON_SETUP.md` for detailed installation instructions.

---

## MCP Server Integration

The Tennis Booking Finder includes a Model Context Protocol (MCP) server for integration with Claude Desktop and other AI applications.

### Features

**Three Tools Available:**

1. **`search_courts`** (Public - no auth required)
   - Search for available tennis courts
   - Parameters: date, time_from, time_to (optional), location (optional)

2. **`book_court`** (Authenticated - requires user token)
   - Book a specific court slot
   - Parameters: venue, court_name, date, time, user_token

3. **`find_trainers`** (Public - uses service account)
   - Search for available tennis trainers
   - Parameters: date (optional), specialization (optional)

### Running the MCP Server

```bash
# Standalone mode
python mcp_server.py

# As systemd service
sudo systemctl start tennis-mcp
sudo systemctl enable tennis-mcp
```

### Claude Desktop Configuration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "tennis-booking": {
      "command": "/opt/Tennis_Booking/venv/bin/python",
      "args": ["/opt/Tennis_Booking/mcp_server.py"],
      "env": {
        "MCP_SERVER_PORT": "8765",
        "FLASK_API_BASE_URL": "http://localhost:5001"
      }
    }
  }
}
```

See `MCP_SERVER_README.md` for complete documentation.

---

## Development

### Running Tests

```bash
# Time parser tests
python test_time_parser.py
python test_german_parsing.py

# Booking tests
python test_booking_integration.py

# Trainer search tests
python test_trainer_integration.py

# Route tests
python test_routes.py

# Chat engine tests
python test_chat_engine.py
```

### Debugging Scrapers

```bash
# Test Das Spiel scraper
python -c "from scrapers_v2 import scrape_das_spiel_arsenal; print(scrape_das_spiel_arsenal('2026-04-14'))"

# Test Post SV scraper
python -c "from scrapers_v2 import scrape_post_sv; print(scrape_post_sv('2026-04-14'))"
```

### Database Management

```bash
# Reinitialize database
python database/db.py

# View database schema
sqlite3 tennis_booking.db ".schema"

# Query availability snapshots
sqlite3 tennis_booking.db "SELECT * FROM availability_snapshots ORDER BY captured_at DESC LIMIT 10;"
```

### Local Development Server

```bash
# Run Flask development server
export FLASK_ENV=development
python app.py

# Run with debug mode
export FLASK_DEBUG=1
python app.py
```

---

## Deployment

### Production Checklist

- [ ] Set `FLASK_ENV=production` in `.env`
- [ ] Generate strong `SECRET_KEY` and `ENCRYPTION_KEY`
- [ ] Set `SESSION_COOKIE_SECURE=True` (requires HTTPS)
- [ ] Configure Apache reverse proxy (see `APACHE_PROXY_SETUP.md`)
- [ ] Setup Gunicorn systemd service
- [ ] Configure cron jobs for snapshots and newsletter
- [ ] Setup SSL certificate (Let's Encrypt recommended)
- [ ] Configure firewall (allow 80, 443, block 5001)
- [ ] Setup log rotation for `logs/` directory
- [ ] Configure SMTP for newsletter delivery
- [ ] Test MCP server integration (optional)

### Apache Configuration

```apache
<VirtualHost *:80>
    ServerName tennisfinder.example.com

    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:5001/
    ProxyPassReverse / http://127.0.0.1:5001/

    ErrorLog ${APACHE_LOG_DIR}/tennis-error.log
    CustomLog ${APACHE_LOG_DIR}/tennis-access.log combined
</VirtualHost>
```

### Gunicorn Service

```ini
[Unit]
Description=Tennis Booking Finder Gunicorn
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/Tennis_Booking
Environment="PATH=/opt/Tennis_Booking/venv/bin"
ExecStart=/opt/Tennis_Booking/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:5001 app:app

[Install]
WantedBy=multi-user.target
```

---

## Supported Venues

### Das Spiel (Tenniszentrum Arsenal)
- **URL:** https://reservierung.dasspiel.at/
- **Status:** Fully functional
- **Courts:** 6 indoor courts (Platz 1-6 HALLE)
- **Hours:** 07:00 - 22:00
- **Booking:** 60-minute slots

### Post SV Wien
- **URL:** https://buchen.postsv-wien.at/tennis.html
- **Status:** Requires authentication
- **Courts:** Multiple indoor/outdoor courts
- **Hours:** Variable by season

---

## Security Features

- **Password Hashing:** Bcrypt with work factor 12
- **Credential Encryption:** AES-256 via Fernet
- **Rate Limiting:** 5 login attempts per 15 minutes
- **CSRF Protection:** Token-based form validation
- **Session Security:** Secure, HttpOnly cookies
- **SQL Injection Prevention:** Parameterized queries
- **XSS Prevention:** Jinja2 auto-escaping

---

## Known Issues & Limitations

1. **Post SV Wien:** Requires authentication for availability checking
2. **Booking Success Rate:** Das Spiel API occasionally requires Selenium fallback
3. **Trainer Search:** Limited to Das Spiel Arsenal only
4. **Newsletter:** Requires SMTP configuration for email delivery
5. **MCP Server:** HTTP-only (no HTTPS support built-in)

---

## Roadmap

### Planned Features
- [ ] Mobile app (React Native)
- [ ] WhatsApp bot integration
- [ ] Automated rebooking for recurring slots
- [ ] Group booking coordination
- [ ] Court reviews and ratings
- [ ] Weather-based recommendations
- [ ] Push notifications for new availability
- [ ] Multi-language support (full English translation)

---

## Support

For issues, questions, or contributions:

1. Check existing documentation in `/opt/Tennis_Booking/`
2. Review logs in `logs/` directory
3. Verify environment variables in `.env`
4. Test individual components using test scripts
5. Check Apache/Gunicorn logs for deployment issues

---

## License

This is a personal utility tool for tennis court booking in Vienna, Austria.

---

## Credits

**Developed by:** Tennis Booking Finder Team
**Framework:** Flask (Pallets Projects)
**AI Integration:** Claude AI (Anthropic)
**Scraping:** BeautifulSoup4, Selenium
**Database:** SQLite

---

**Last Updated:** April 2026
**Version:** 2.0.0
**Status:** Production Ready

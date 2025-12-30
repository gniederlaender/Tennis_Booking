# Tennis Court Booking Finder - Vienna

A Python CLI application that checks tennis court availability across multiple booking portals in Vienna.

## Features

- ✅ Natural language timeframe parsing (e.g., "next Monday 6-8pm", "7.1.2026 between 15:00 and 18:00")
- ✅ Checks availability across multiple portals
- ✅ Preference learning system (logs your selections and learns your preferences)
- ✅ Smart recommendations based on your booking history
- ✅ Clean console output with detailed court information

## Current Status

### Working Portals

#### ✅ Das Spiel (Tenniszentrum Arsenal)
- **URL**: https://reservierung.dasspiel.at/
- **Status**: Fully functional
- **Authentication**: Not required for checking availability
- **Courts**: 6 indoor courts (Platz 1-6 HALLE) + 2 waitlist slots
- **Hours**: 07:00 - 22:00
- **Timeblock**: 60 minutes

### Partially Working Portals

#### ⚠️ Post SV Wien
- **URL**: https://buchen.postsv-wien.at/tennis.html
- **Status**: Requires authentication
- **Issue**: Portal requires login even for checking availability (not just booking)
- **Solution**: Credentials needed (see Configuration section below)

## Installation

1. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/Mac
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
./venv/bin/python main.py "7.1.2026 between 15:00 and 18:00"
```

### Example Timeframe Formats

- `"next Monday 6-8pm"`
- `"7.1.2026 between 15:00 and 18:00"`
- `"tomorrow 10:00-12:00"`
- `"friday evening 18-20"`
- `"today 9-11"`

### Interactive Mode

```bash
./venv/bin/python main.py
```

Then enter your timeframe when prompted.

## Configuration

### Post SV Wien Credentials (Optional)

To enable Post SV Wien scraping, create a `credentials.json` file:

1. Copy the example file:
```bash
cp credentials.json.example credentials.json
```

2. Edit `credentials.json` with your Post SV Wien login:
```json
{
  "postsv": {
    "username": "your_email@example.com",
    "password": "your_password"
  }
}
```

**Note**: Once credentials are configured, the scraper will attempt to login and save the logged-in page for further analysis.

## Example Output

```
================================================================================
Tennis Court Booking Finder - Vienna
================================================================================

Parsing: '7.1.2026 between 15:00 and 18:00'
Searching for: 2026-01-07 (Wednesday)
Time range: 15:00 - 18:00

Searching booking portals...

============================================================
Scraping Das Spiel (Tenniszentrum Arsenal)...
============================================================
Found 24 slots from Das Spiel

================================================================================
Found 24 available slot(s)
================================================================================

[1] Tenniszentrum Arsenal (Das Spiel)
    Date: 2026-01-07 (Wednesday)
    Time: 15:00
    Court: Platz 1 HALLE
    Location: Arsenal, Wien
    Type: Indoor

[2] Tenniszentrum Arsenal (Das Spiel)
    Date: 2026-01-07 (Wednesday)
    Time: 15:00
    Court: Platz 2 HALLE
    Location: Arsenal, Wien
    Type: Indoor

...
```

## Preference Learning

The application learns from your selections:

1. After displaying results, you'll be prompted to select a slot
2. Your choice is logged to `user_preferences.json`
3. After 5+ selections, the app will start showing a "PREFERRED" recommendation
4. Preferences are based on:
   - Venue preference (weight: 3x)
   - Time of day (morning/afternoon/evening) (weight: 2x)
   - Day of week (weight: 1.5x)
   - Price range (weight: 1x)

## Project Structure

```
Tennis_Booking/
├── main.py                      # CLI application entry point
├── timeframe_parser.py          # Natural language timeframe parser
├── scrapers_v2.py               # Web scrapers for both portals
├── preference_engine.py         # Preference learning system
├── config.py                    # Application configuration
├── requirements.txt             # Python dependencies
├── credentials.json.example     # Example credentials file
├── user_preferences.json        # User selection history (auto-created)
└── README.md                    # This file
```

## Development & Debugging

### Analysis Scripts

- `analyze_portals.py`: Analyzes portal structure and saves HTML
- `explore_postsv.py`: Explores Post SV Wien for public endpoints

### Testing

Test the parser:
```bash
./venv/bin/python timeframe_parser.py
```

## Known Issues & Limitations

1. **Post SV Wien Authentication**: Requires login credentials even for checking availability
2. **Price Information**: Not available from Das Spiel API
3. **Booking**: Currently only checks availability, booking functionality is not implemented (planned for v2)

## Roadmap (v2)

- [ ] Complete Post SV Wien integration (parse logged-in booking interface)
- [ ] Implement automatic booking functionality
- [ ] Add price information where available
- [ ] Support for additional portals
- [ ] Email notifications for available slots
- [ ] Web interface

## Technical Details

### Das Spiel Implementation

The Das Spiel scraper works by:
1. Fetching the main page HTML
2. Extracting calendar data from `meta[id="transfer-data-calendar"]` tag
3. Parsing the JSON court configuration
4. Attempting to fetch bookings from potential API endpoints
5. Generating available slots based on court schedules and bookings

### Post SV Wien Implementation

The Post SV Wien scraper:
1. Detects login requirement
2. Attempts login if credentials are provided
3. Saves logged-in page HTML for analysis
4. (TODO) Parse booking interface to extract available slots

## Support

For issues or questions about the application, please check:
- Ensure all dependencies are installed
- Verify credentials for Post SV Wien (if using)
- Check that portal URLs are still accessible

## License

This is a personal utility tool for checking tennis court availability in Vienna.

# Das Spiel Booking Implementation

## Summary

Successfully implemented automated booking for Das Spiel (Tenniszentrum Arsenal) using Selenium browser automation.

## Status

✅ **COMPLETE** - Das Spiel booking is now fully functional

### Test Results

- **Date**: 2025-12-31
- **Test Booking**: January 3, 2026, 07:00
- **Result**: ✅ SUCCESS - Booking confirmed
- **Confirmation**: User received confirmation email

## Implementation Details

### Technology Stack

- **Browser Automation**: Firefox + Selenium WebDriver
- **Driver**: Geckodriver v0.36.0 at `/usr/local/bin/geckodriver`
- **Mode**: Headless (runs in background without GUI)
- **Pattern Source**: Based on working `/opt/Bankcomparison` setup

### Booking Flow

1. **Start Firefox** - Headless mode with environment variables:
   - `MOZ_HEADLESS=1`
   - `MOZ_DISABLE_CONTENT_SANDBOX=1`

2. **Sign In** - Navigate to `https://reservierung.dasspiel.at/signin`
   - Fill email and password fields
   - Submit form
   - Wait for redirect

3. **Navigate to Calendar** - Load date with URL parameter: `?date=YYYY-MM-DD`

4. **Find Slot** - Locate free slots using CSS selector: `a.square-free`
   - Match time if specified
   - Click on target slot

5. **Click "Platz mieten"** - Find and click booking button

6. **Accept Terms** - Check all AGB checkboxes (2 checkboxes):
   - "Ich habe die AGB gelesen und akzeptiert"
   - "Ich habe die Regeln und Hinweise gelesen und akzeptiert"

7. **Confirm Booking** - Click "Verbindlich Reservieren" button

8. **Verify Success** - Check for indicators:
   - Slot changes to "Ihre Buchung" (Your booking)
   - CSS class changes to `square-own-booking`

## Files Modified

### `/opt/Tennis_Booking/booking.py`
- Updated imports to include Selenium
- Replaced `DasSpielBooker.book_slot()` with Selenium automation
- Keeps session-based login method for future use

### `/opt/Tennis_Booking/app.py`
- No changes needed - already integrated with booking.py

### `/opt/Tennis_Booking/requirements.txt`
- Added: `selenium==4.16.0`
- Added: `webdriver-manager==4.0.1` (for development)

## Test Files Created

1. **test_dasspiel_working_selenium.py** - Basic login and calendar test
2. **test_dasspiel_full_booking.py** - Slot click and button detection
3. **test_dasspiel_complete_booking.py** - Full end-to-end booking ✅
4. **test_booking_integration.py** - Integration test for booking.py API

## Web Interface

The Flask web app at `http://<server>/tennis/` now supports booking for both venues:

- ✅ **Post SV Wien** - Session-based booking (implemented earlier)
- ✅ **Das Spiel (Arsenal)** - Selenium-based booking (implemented now)

Users can:
1. Search for available slots with natural language
2. Click "Book Now" on any slot
3. System automatically handles the booking process
4. Receive confirmation

## Usage Example

### Python API

```python
from booking import DasSpielBooker

# Create test slot
slot = {
    'venue': 'Das Spiel (Tenniszentrum Arsenal)',
    'court_name': 'Platz 1 HALLE',
    'date': '2026-01-04',
    'time': '08:00',
    'price': 'N/A'
}

# Book it
booker = DasSpielBooker()
success, message = booker.book_slot(slot)
print(f"{'✓' if success else '✗'} {message}")
```

### Web Interface

1. Visit `http://<server>/tennis/`
2. Enter: "tomorrow at 5pm"
3. Click "Search"
4. Click "Book Now" on desired slot
5. Confirmation appears

## Important Notes

### Booking Constraints

- Bookings must be on or after **January 3, 2026** (per user requirement)
- Each booking takes ~15 seconds due to browser automation
- Headless mode means no visual feedback during booking

### Environment Variables

Required for Firefox to work in server environment:
- `MOZ_HEADLESS=1` - Run without display
- `MOZ_DISABLE_CONTENT_SANDBOX=1` - Disable sandboxing (permission fix)

### Success Verification

After booking, the calendar slot will show:
- Text: "Ihre Buchung" (Your booking)
- CSS class: `square-own-booking`
- Color changes to indicate owned booking

## Deployment

1. **PM2 Process**: `tennis-booking` (ID: 3)
   - Status: ✅ Online
   - Uptime: Restarted on 2025-12-31
   - Memory: ~22MB

2. **Restart Command**: `pm2 restart tennis-booking`

3. **Logs**:
   - Out: `logs/out.log`
   - Error: `logs/error.log`
   - Geckodriver: `geckodriver.log`

## Next Steps (Optional)

1. **Add notification system** - Email/SMS after successful booking
2. **Add scheduling** - Cron job for automatic bookings
3. **Add retry logic** - Handle intermittent failures
4. **Add booking history UI** - View past bookings in web interface
5. **Add cancellation** - Automated cancellation functionality

## Troubleshooting

### If booking fails:

1. Check geckodriver.log: `tail -50 geckodriver.log`
2. Check app logs: `pm2 logs tennis-booking --lines 50`
3. Run test: `./venv/bin/python test_dasspiel_complete_booking.py`
4. Check screenshots in `/tmp/complete_*.png`

### Common Issues:

- **"No free slots"** - Date/time fully booked
- **"Could not find button"** - Page structure changed, needs update
- **"Timeout"** - Slow connection, increase sleep times
- **"selenium.common.exceptions"** - Check Firefox/geckodriver compatibility

## Conclusion

Das Spiel booking automation is **fully functional** and tested. The system can now automatically book tennis courts at both supported venues in Vienna.

**Test Status**: ✅ Confirmed working - User received booking confirmation for Jan 3, 2026 @ 07:00

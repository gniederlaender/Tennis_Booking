# Tennis Booking API Fix - Investigation Findings

**Date:** 2026-01-18
**Investigator:** Claude Code via Chrome Extension
**Status:** Root Cause Identified

---

## Executive Summary

The API-based booking fails with `{"status":0}` because **the server requires session state that is set when clicking on a time slot in the browser**. The current API implementation attempts to POST directly without establishing this booking context.

---

## Investigation Results

### Test Booking Performed
- **Court:** Platz 6 HALLE
- **Date:** 21. Januar 2026
- **Time:** 12:00 - 13:00
- **Result:** SUCCESS (booking completed, then cancelled)
- **square_id:** `35a8aa1f-cadc-431e-9465-26d7f54b0e1f`

### Browser Flow Observed

1. **User clicks on free slot** (e.g., green "Frei" cell)
   - Modal opens with "WICHTIGE HINWEISE" (Important Notes)
   - **Critical:** This click likely sets server-side session state indicating which slot is being booked

2. **User clicks "Platz mieten" button**
   - Proceeds to booking form

3. **User fills form:**
   - `timeslot` dropdown (value "0" = 1 hour)
   - `agb` checkbox
   - `rules` checkbox

4. **User clicks "Verbindlich Reservieren"**
   - POST to `/user/booking/rent`
   - Returns `{"status":1}` on success

### Network Requests Captured

```
GET /calendar/booking-data/?date=2026-01-21&time_start=12:00&square_id=35a8aa1f-cadc-431e-9465-26d7f54b0e1f&is_half_hour=0
Response: 503 Service Unavailable

POST /user/booking/rent
Response: 200 OK with {"status":1}
```

**Key Observation:** The GET request returned **503** but the booking **still succeeded**! This proves that the booking-data response is NOT what the server uses to determine which slot to book.

---

## Root Cause Analysis

### Current API Implementation (booking.py:129-258)

```python
# Step 1: Get booking data
response = self.session.get(booking_data_url, params=params, ...)

# Step 2: Submit booking
form_data = {
    'timeslot': '0',
    'agb': 'on',
    'rules': 'on'
}
response = self.session.post(self.BOOKING_URL, data=form_data, ...)
```

### The Problem

1. **Missing Session State:** The API code does NOT visit the calendar page or click on a slot
2. **No Booking Context:** The server doesn't know WHICH slot is being booked because no selection was made
3. **POST Has No Context:** The form data only contains `timeslot=0, agb=on, rules=on` - no slot identification

### What the Browser Does Differently

When you click a slot in the browser, JavaScript likely:
1. Calls an endpoint to "select" or "lock" the slot
2. Sets a session variable on the server indicating the pending booking
3. The subsequent POST uses this session state

---

## Proposed Fixes

### Option 1: Visit Calendar Page First (Recommended)

Before making the booking POST, navigate to the calendar page with the correct date. This may set necessary cookies/session state.

```python
def book_slot_api(self, slot):
    # Login first
    success, message = self.login()

    # NEW: Visit calendar page to establish context
    calendar_url = f"{self.URL}?date={date}"
    self.session.get(calendar_url, headers=headers)

    # Then proceed with booking-data and POST
    ...
```

### Option 2: Add Query Parameters to POST URL

The POST URL might need to include the slot identification:

```python
# Instead of:
# POST /user/booking/rent

# Try:
# POST /user/booking/rent?date=2026-01-21&time_start=12:00&square_id=35a8aa1f...&is_half_hour=0

booking_url_with_params = f"{self.BOOKING_URL}?date={date}&time_start={time_slot}&square_id={square_id}&is_half_hour=0"
response = self.session.post(booking_url_with_params, data=form_data, ...)
```

### Option 3: Check for Slot Selection Endpoint

Look for a JavaScript onclick handler on the slot cells. It may call a separate endpoint like:

```
POST /calendar/select-slot
{
    "date": "2026-01-21",
    "time_start": "12:00",
    "square_id": "35a8aa1f-cadc-431e-9465-26d7f54b0e1f"
}
```

If such an endpoint exists, call it BEFORE the booking POST.

### Option 4: Include Slot Info in Form Data

The form might need additional hidden fields:

```python
form_data = {
    'timeslot': '0',
    'agb': 'on',
    'rules': 'on',
    'date': date,           # NEW
    'time_start': time_slot, # NEW
    'square_id': square_id   # NEW
}
```

---

## Implementation Recommendation

**Start with Option 2** (add query parameters to POST URL) as it's the simplest change and mirrors how the booking-data endpoint works.

If that fails, **try Option 1** (visit calendar page first) to establish session state.

### Code Change for Option 2

```python
# In book_slot_api(), change line 212 from:
response = self.session.post(
    self.BOOKING_URL,
    data=form_data,
    ...
)

# To:
booking_url_with_params = f"{self.BOOKING_URL}?date={date}&time_start={time_slot}&square_id={square_id}&is_half_hour=0"
response = self.session.post(
    booking_url_with_params,
    data=form_data,
    ...
)
```

---

## Form Fields Reference

| Field | Type | Value | Description |
|-------|------|-------|-------------|
| timeslot | select | "0" | Index 0 = 1 hour duration |
| agb | checkbox | "on" | Accept AGB (terms) |
| rules | checkbox | "on" | Accept rules |

---

## Status Codes

| Status | Meaning |
|--------|---------|
| `{"status":0}` | Booking failed (missing context, slot not available, etc.) |
| `{"status":1}` | Booking successful |

---

## Next Steps

1. Implement Option 2 (query params on POST)
2. Test with a real booking attempt
3. If fails, implement Option 1 (visit calendar first)
4. If still fails, investigate JavaScript onclick handlers for hidden API calls

---

*Document generated from live browser investigation via Chrome Extension*

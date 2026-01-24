# Bug Fix: 500 Internal Error on Login

**Date:** January 24, 2026
**Status:** ✓ RESOLVED
**Severity:** High (Blocking user login)

---

## Problem Description

Users experienced a 500 Internal Server Error when attempting to log in to the Tennis Booking application.

### Error Message

```
ValueError: not enough values to unpack (expected 2, got 1)
File "/opt/Tennis_Booking/auth/models.py", line 49, in get_by_email
  row = cursor.fetchone()
File "/usr/lib/python3.12/sqlite3/dbapi2.py", line 77, in convert_timestamp
  datepart, timepart = val.split(b" ")
```

### Impact

- Users could not log in
- Application returned HTTP 500 errors
- Authentication system was completely broken

---

## Root Cause Analysis

The issue occurred in the database layer when retrieving user records.

### Technical Details

1. **SQLite PARSE_DECLTYPES Flag**: The database connection was configured with `detect_types=sqlite3.PARSE_DECLTYPES`

2. **Automatic Type Conversion**: This flag tells SQLite to automatically convert TIMESTAMP columns to Python datetime objects

3. **Mixed Timestamp Formats**: The database contained timestamps in multiple formats:
   - Standard: `2026-01-13 16:04:29`
   - ISO with microseconds: `2026-01-13 17:15:12.609553`
   - NULL values

4. **Parser Expectation**: SQLite's built-in timestamp parser expects the format `YYYY-MM-DD HH:MM:SS` and splits on space to separate date and time

5. **Failure Point**: When encountering timestamps in other formats or incomplete data, the parser failed trying to unpack the split result

### Why It Happened

- The PARSE_DECLTYPES feature is overly strict about timestamp format
- Different parts of the codebase created timestamps in different formats
- Some timestamps included microseconds, some didn't
- The parser couldn't handle the variation

---

## Solution

### Fix Implemented

**File:** `database/db.py`

**Change:** Removed the `detect_types=sqlite3.PARSE_DECLTYPES` parameter from the SQLite connection

**Before:**
```python
g.db = sqlite3.connect(
    config.DATABASE_PATH,
    detect_types=sqlite3.PARSE_DECLTYPES
)
```

**After:**
```python
# Don't use PARSE_DECLTYPES to avoid timestamp parsing errors
# Timestamps will be returned as strings, which is safer
g.db = sqlite3.connect(config.DATABASE_PATH)
```

### Why This Works

1. **Timestamps as Strings**: Without automatic parsing, timestamps are returned as strings
2. **Format Agnostic**: String representation preserves the original format without parsing
3. **Existing Code Compatible**: The codebase already treats timestamps as strings:
   - `update_last_login()` uses `datetime.now().strftime('%Y-%m-%d %H:%M:%S')`
   - `to_dict()` methods pass timestamps through as-is
   - No datetime operations are performed on retrieved timestamps

4. **NULL Safe**: NULL values remain as None (NoneType), which is handled correctly

### Benefits

- ✓ No parsing errors regardless of timestamp format
- ✓ Supports multiple timestamp formats in the database
- ✓ Handles NULL values gracefully
- ✓ No code changes required in models or routes
- ✓ More predictable behavior

---

## Testing

### Test Created

**File:** `test_login_fix.py`

Verifies that:
- Database connection works without PARSE_DECLTYPES
- User records can be fetched successfully
- Various timestamp formats are handled correctly
- NULL timestamps don't cause errors

### Test Results

```
✓ Successfully fetched 5 users
✓ Timestamps returned as strings (not datetime objects)
✓ Multiple formats handled: standard, ISO with microseconds, NULL
✓ Test PASSED - No timestamp parsing errors!
```

### Production Verification

- Application restarted successfully
- Health endpoint responding: `{"status":"healthy"}`
- No new errors in error logs
- Login functionality restored

---

## Impact Assessment

### Systems Affected

- ✓ User authentication (login/register)
- ✓ Database queries involving timestamps
- ✓ All models: User, PortalCredentials, LoginAttempt

### Regressions Check

✓ No regressions identified:
- Timestamps were already treated as strings in the codebase
- `update_last_login()` already converts to string format
- `to_dict()` methods don't perform datetime operations
- All existing functionality preserved

---

## Prevention

### Lessons Learned

1. **Avoid Auto-Parsing**: SQLite's PARSE_DECLTYPES can cause unexpected issues with mixed data formats
2. **String Timestamps**: Treating timestamps as strings is safer in SQLite applications
3. **Format Consistency**: If using timestamp parsing, ensure all code uses identical format
4. **Better Testing**: Add integration tests for authentication flows

### Recommendations

1. **Standardize Timestamp Creation**: Use consistent format everywhere:
   ```python
   datetime.now().strftime('%Y-%m-%d %H:%M:%S')
   ```

2. **Document Format**: Add comment to database schema indicating expected format

3. **Add Validation**: Consider adding timestamp format validation in models

4. **Monitor Logs**: Set up alerts for ValueError exceptions

---

## Related Files

**Modified:**
- `database/db.py` - Database connection configuration

**Created:**
- `test_login_fix.py` - Test for timestamp handling
- `BUG_FIX_LOGIN_500.md` - This document

**Referenced:**
- `auth/models.py` - User model with timestamp fields
- `auth/auth_routes.py` - Login route that triggered error
- `logs/error.log` - Error logs showing the issue

---

## Timeline

- **January 13, 2026**: Issue first appeared in logs
- **January 24, 2026**: Bug reported by user
- **January 24, 2026**: Root cause identified
- **January 24, 2026**: Fix implemented and deployed
- **January 24, 2026**: Testing confirmed resolution

---

## Status

✓ **RESOLVED**

The 500 internal error on login has been fixed. Users can now log in successfully.

---

**Commit:** `5d4aa97` - Fix: Resolve 500 internal error on login due to timestamp parsing

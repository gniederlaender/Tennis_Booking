# Trainer Finder Feature

## Overview

Added trainer finder functionality to the Tennis Booking application, allowing users to search for available trainers at Das Spiel tennis center alongside court availability.

## Features Implemented

### 1. User Interface (templates/index.html)

- **Checkbox**: "Including trainer" option in the search form
- **Text Field**: Optional "Trainer name" field (appears when checkbox is enabled)
- **Trainer Display**: Separate section showing available trainers with:
  - Time slots (start - end time)
  - Pricing information
  - Court names
  - List of available trainers
  - Visual distinction with green background

### 2. Backend Module (trainer_finder.py)

New module providing:
- `TrainerFinder` class for querying Das Spiel API
- Authentication with Das Spiel booking system
- Trainer availability fetching across multiple courts
- Filtering by specific trainer name
- Deduplication of results
- Rate limiting (0.3s delay between requests) to prevent API abuse

#### Key Functions:

```python
find_trainers(date, start_time, end_time, trainer_name=None)
```

- Searches for trainer availability
- Returns list of trainer slots with details
- Optionally filters by trainer name

### 3. Flask Integration (app.py)

Updated `/search` endpoint to:
- Accept `includeTrainers` boolean parameter
- Accept optional `trainerName` string parameter
- Call trainer finder when requested
- Return trainer data in response

### 4. API Integration

Uses Das Spiel's booking-data API endpoint:
```
GET /calendar/booking-data/?date=YYYY-MM-DD&time_start=HH:MM&square_id=UUID&is_half_hour=0
```

Response includes `trainer_data` array with:
- `time_start`, `time_end`: Training session times
- `price`: Session cost in euros
- `trainers`: Array of available trainers with names, UUIDs, and training types

## Security & Performance

- **Authentication**: Uses existing Das Spiel credentials from credentials.json
- **Rate Limiting**: 0.3 second delay between API requests
- **Court Limiting**: Checks only first 5 courts to reduce load
- **Time Sampling**: Checks every 2 hours instead of every hour
- **Session Reuse**: Maintains authenticated session across requests
- **Deduplication**: Removes duplicate trainer slots

## Usage

1. Enter a timeframe (e.g., "13.1.2026 at 09:00")
2. Check the "Including trainer" box
3. Optionally enter a trainer name (e.g., "ROSSEN")
4. Click Search
5. View available courts AND trainer sessions

## Testing

Created test files:
- `test_trainer_finder.py`: Unit tests for trainer finder module
- `test_trainer_api_direct.py`: Direct API endpoint testing
- `test_trainer_integration.py`: Full integration test with Flask app

All tests pass successfully.

## Example Response

Trainer slot format:
```json
{
  "date": "2026-01-13",
  "day_of_week": "Tuesday",
  "time_start": "09:00",
  "time_end": "10:00",
  "price": 66,
  "court_name": "Platz 5 HALLE",
  "trainers": [
    {
      "name": "ROSSEN",
      "uuid": "b30f3a05-b860-42c9-87fe-91239b9a1d74",
      "training_types": [1, 2, 3]
    },
    {
      "name": "TOBIAS W.",
      "uuid": "bb25057b-6a78-4f44-8803-103b5f7d6560",
      "training_types": [1, 2, 3]
    }
  ],
  "venue": "Tenniszentrum Arsenal (Das Spiel)"
}
```

## Future Enhancements

Potential improvements (not implemented):
- Booking trainer sessions (currently only displays availability)
- Filter by training type
- Sort trainers by price or availability
- Cache trainer data to reduce API calls
- Support for other venues (currently Das Spiel only)

## Files Modified/Created

- `app.py`: Added trainer search handling
- `templates/index.html`: Added UI elements and trainer display
- `trainer_finder.py`: New module for trainer API integration
- `test_trainer_finder.py`: Unit tests
- `test_trainer_api_direct.py`: API tests
- `test_trainer_integration.py`: Integration tests

## Commit

Changes committed with message: "Add trainer finder functionality to Tennis Booking application"

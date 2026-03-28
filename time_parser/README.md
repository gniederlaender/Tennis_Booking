# Tennis Zeitparser

Natural language time parser for tennis court booking with German and English support.

## Features

- **Bilingual support**: German and English keywords
- **Relative dates**: morgen, übermorgen, tomorrow, next Monday, etc.
- **Time-of-day keywords**: früh, vormittag, nachmittag, abend, morning, afternoon, evening
- **Explicit times**: "um 10:00", "zwischen 10 und 13", "at 9am", "from 10 to 12"
- **Typo correction**: Levenshtein distance ≤ 2 for known keywords
- **Weekend support**: Returns 2 time windows for Saturday and Sunday
- **Confidence scoring**: 0.0-1.0 indicating parse confidence

## Installation

The module is already integrated into the Tennis Booking App. Dependencies:

```bash
pip install rapidfuzz==3.10.0 python-dateutil==2.8.2
```

## API Endpoint

### POST /api/parse-time

Parse natural language time query into structured TimeWindow objects.

**Request:**
```json
{
  "query": "morgen zwischen 10 und 13"
}
```

**Response (success):**
```json
{
  "success": true,
  "interpreted_as": "morgen, 10:00–13:00",
  "confidence": 0.95,
  "windows": [
    {
      "date": "2025-01-29",
      "day_name": "Mittwoch",
      "from": "10:00",
      "to": "13:00"
    }
  ],
  "corrections": {
    "original": "morgen zwischen 10 und 13",
    "normalized": "morgen zwischen 10 und 13"
  }
}
```

**Response (weekend - 2 windows):**
```json
{
  "success": true,
  "interpreted_as": "Wochenende, ganzer Tag",
  "confidence": 0.99,
  "windows": [
    {
      "date": "2025-02-01",
      "day_name": "Samstag",
      "from": "07:00",
      "to": "21:00"
    },
    {
      "date": "2025-02-02",
      "day_name": "Sonntag",
      "from": "07:00",
      "to": "21:00"
    }
  ],
  "corrections": {}
}
```

**Response (error):**
```json
{
  "success": false,
  "interpreted_as": null,
  "confidence": 0.0,
  "windows": [],
  "error": "Zeitangabe konnte nicht interpretiert werden.",
  "hint": "Beispiele: 'morgen früh', 'next Sunday afternoon', 'between 10 and 12'"
}
```

## Time Windows

| Keyword (DE) | Keyword (EN) | From | To |
|---|---|---|---|
| früh | early | 07:00 | 09:00 |
| vormittag, morgens | morning | 09:00 | 12:00 |
| mittag | noon, lunchtime | 12:00 | 14:00 |
| nachmittag | afternoon | 14:00 | 18:00 |
| abend | evening | 18:00 | 21:00 |
| *(default)* | *(default)* | 07:00 | 21:00 |

## Example Queries

### German
- "morgen früh" → Tomorrow, 07:00-09:00
- "übermorgen nachmittag" → Day after tomorrow, 14:00-18:00
- "nächsten Montag abend" → Next Monday, 18:00-21:00
- "am Wochenende" → This weekend (2 windows: Sat + Sun)
- "morgen zwischen 10 und 13" → Tomorrow, 10:00-13:00
- "heute um 15:00" → Today, 15:00-16:00
- "asap" → Today, from next full hour

### English
- "tomorrow morning" → Tomorrow, 09:00-12:00
- "next Sunday afternoon" → Next Sunday, 14:00-18:00
- "this weekend" → This weekend (2 windows: Sat + Sun)
- "between 10 and 12" → Today, 10:00-12:00
- "at 9am" → Today, 09:00-10:00

### Typo Correction
- "morgrn früh" → Corrected to "morgen früh"
- "Sontag" → Corrected to "Sonntag"
- "nachmitag" → Corrected to "nachmittag"

## Module Structure

```
time_parser/
├── __init__.py          # Package initialization
├── parser.py            # Core parsing logic
├── keywords.py          # DE/EN keyword dictionaries
├── normalizer.py        # Text normalization & typo correction
├── time_windows.py      # TimeWindow class & helpers
└── routes.py            # Flask Blueprint with /api/parse-time endpoint
```

## Usage in Code

```python
from time_parser import TimeParser

parser = TimeParser()
result = parser.parse("morgen früh")

print(result['interpreted_as'])  # "morgen, 07:00–09:00"
print(result['confidence'])       # 0.975
print(result['windows'])          # [{'date': '2025-01-29', ...}]
```

## Testing

Run the test script:

```bash
python test_time_parser.py
```

Or test via curl:

```bash
curl -X POST http://localhost:5001/api/parse-time \
  -H "Content-Type: application/json" \
  -d '{"query": "morgen früh"}'
```

## Confidence Scoring

| Situation | Base Score | Adjustments |
|---|---|---|
| Date + Time both recognized | 0.90-1.00 | - |
| Only date recognized | 0.70 | - |
| Typo corrections applied | - | -0.15 |
| Nothing recognized | 0.00 | - |

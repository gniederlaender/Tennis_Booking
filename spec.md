# Tennis Zeitparser — Technische Spezifikation

## 1. Projektübersicht

Der Tennis Zeitparser ist ein eigenständiges Backend-Modul (Microservice), das natürlichsprachliche Datums- und Zeitangaben in strukturierte `TimeWindow`-Objekte umwandelt. Er wird als REST-Endpoint in die bestehende Tennis Booking App unter `/opt/Tennis_Booking/` integriert und ersetzt bzw. erweitert die bisherige Sucheingabe um Natural Language Verständnis auf Deutsch und Englisch.

---

## 2. Zielgruppe & User Stories

- Als **Tennisspieler** möchte ich „morgen früh" oder „next Sunday afternoon" eingeben, damit ich nicht in einem Kalender nach exakten Uhrzeiten suchen muss.
- Als **Entwickler der Booking App** möchte ich einen sauberen API-Endpoint aufrufen, damit ich den Parser ohne Refactoring in die bestehende Suchlogik einbinden kann.
- Als **Betreiber der Booking App** möchte ich, dass Tippfehler wie „morgrn" oder „Sontag" korrekt interpretiert werden, damit Nutzer keine Fehlermeldungen erhalten.

---

## 3. Features & Scope

### Im Scope ✅
| Feature | Beschreibung |
|---|---|
| Relative Datumsbegriffe | „morgen", „übermorgen", „am Wochenende", „nächsten Montag", „tomorrow", „next Friday" |
| Tageszeit-Fenster | „früh", „vormittag", „mittag", „nachmittag", „abend" + englische Äquivalente |
| Explizite Uhrzeiten | „um 10:00", „zwischen 10 und 13", „at 9am", „from 10 to 12" |
| Tippfehler-Toleranz | Levenshtein-Distanz ≤ 2 auf bekannte Keywords |
| Zweisprachigkeit | Deutsch + Englisch, gemischt erlaubt |
| Confidence-Score | Gibt an wie sicher die Interpretation ist (0.0–1.0) |

### Nicht im Scope ❌
- Eigene UI / Demo-Screens
- Platztypfilter (Halle/Freiplatz)
- Spielerlevel-Erkennung
- Authentifizierung des Endpoints

---

## 4. Grenzfall-Definitionen (verbindlich)

### Tageszeiten-Fenster
| Keyword (DE) | Keyword (EN) | Von | Bis |
|---|---|---|---|
| früh | early | 07:00 | 09:00 |
| vormittag, morgens | morning | 09:00 | 12:00 |
| mittag | noon, lunchtime | 12:00 | 14:00 |
| nachmittag | afternoon | 14:00 | 18:00 |
| abend | evening | 18:00 | 21:00 |
| *(kein Tageszeit-Begriff)* | *(none)* | 07:00 | 21:00 |

### Relative Datumsbegriffe
| Eingabe | Regel |
|---|---|
| „morgen" / „tomorrow" | heute + 1 Tag |
| „übermorgen" / „day after tomorrow" | heute + 2 Tage |
| „heute" / „today" | aktuelles Datum, `from` = nächste volle Stunde |
| „so bald wie möglich" / „asap" | heute, `from` = nächste volle Stunde |
| „diesen Sonntag" / „this Sunday" | kommender Sonntag (≤ 6 Tage entfernt) |
| „nächsten Sonntag" / „next Sunday" | Sonntag in 7–13 Tagen |
| „am Wochenende" / „this weekend" | gibt **zwei** TimeWindow-Objekte zurück (Sa + So) |

### Tippfehler-Beispiele
| Eingabe | Korrektur |
|---|---|
| „morgrn" | „morgen" |
| „Sontag" | „Sonntag" |
| „nachmitag" | „nachmittag" |
| „tomorrw" | „tomorrow" |

---

## 5. Banking API Integration

> **Nicht anwendbar.** Dieses Modul interagiert nicht mit der Banking API. Es ist ein reiner Text-zu-Zeit-Konverter für die Tennis Booking App.

---

## 6. API-Spezifikation

### Endpoint

```
POST /api/parse-time
Content-Type: application/json
```

### Request

```json
{
  "query": "morgen zwischen 10 und 13"
}
```

### Response (Normalfall)

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

### Response (Wochenende → zwei Objekte)

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

### Response (nicht erkannt)

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

---

## 7. Technische Architektur

### Stack

- **Sprache:** Python 3.10+
- **Framework:** Flask (bereits in der Booking App vorhanden, wird wiederverwendet)
- **Abhängigkeiten:**
  - `flask` — HTTP-Endpoint
  - `python-dateutil` — robuste Datumsberechnung
  - `Levenshtein` (oder `rapidfuzz`) — Tippfehler-Korrektur

### Modulstruktur

```
/opt/Tennis_Booking/
└── time_parser/
    ├── __init__.py
    ├── parser.py          # Kernlogik: Text → TimeWindow
    ├── keywords.py        # DE/EN Keyword-Dictionaries
    ├── normalizer.py      # Tippfehler-Korrektur via Levenshtein
    ├── time_windows.py    # Tageszeit-Fenster Definitionen
    └── routes.py          # Flask Blueprint: POST /api/parse-time
```

### Datenfluss

```
User-Eingabe (Freitext)
        │
        ▼
[normalizer.py]
  Kleinschreibung, Strip, Levenshtein-Korrektur auf bekannte Keywords
        │
        ▼
[parser.py] – Regelbasierter Ablauf:
  1. Datum erkennen (relativ/absolut/Wochentag)
  2. Tageszeit-Begriff erkennen ODER Uhrzeiten extrahieren
  3. Zeitfenster berechnen (mit Grenzfall-Logik)
  4. Confidence berechnen (wie viele Tokens erkannt?)
        │
        ▼
[TimeWindow-Objekt(e)]
  { date, day_name, from, to }
        │
        ▼
[routes.py] – JSON Response an Booking App
        │
        ▼
Booking App verwendet date/from/to für Platzverfügbarkeits-Query
```

### Confidence-Berechnung (einfache Heuristik)

| Situation | Score |
|---|---|
| Datum + Zeitfenster beide erkannt | 0.90–1.00 |
| Nur Datum erkannt, kein Zeitbegriff | 0.70 |
| Datum via Tippfehler-Korrektur gefunden | −0.15 Abzug |
| Nichts erkannt | 0.00 |

---

## 8. Keyword-Dictionary (Auszug)

```python
# keywords.py

RELATIVE_DATES = {
    "heute": 0, "today": 0,
    "morgen": 1, "tomorrow": 1,
    "übermorgen": 2, "day after tomorrow": 2,
}

WEEKDAYS_DE = ["montag","dienstag","mittwoch","donnerstag","freitag","samstag","sonntag"]
WEEKDAYS_EN = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]

TIME_WINDOWS = {
    "früh":        ("07:00", "09:00"),
    "early":       ("07:00", "09:00"),
    "vormittag":   ("09:00", "12:00"),
    "morgens":     ("09:00", "12:00"),
    "morning":     ("09:00", "12:00"),
    "mittag":      ("12:00", "14:00"),
    "noon":        ("12:00", "14:00"),
    "lunchtime":   ("12:00", "14:00"),
    "nachmittag":  ("14:00", "18:00"),
    "afternoon":   ("14:00", "18:00"),
    "abend":       ("18:00", "21:00"),
    "evening":     ("18:00", "21:00"),
}

WEEKEND_TRIGGERS = ["wochenende", "weekend", "this weekend", "am wochenende"]
ASAP_TRIGGERS    = ["asap", "so bald wie möglich", "sofort", "jetzt"]
```

---

## 9. Deployment

| Parameter | Wert |
|---|---|
| **Installationspfad** | `/opt/Tennis_Booking/time_parser/` |
| **Einbindung** | Als Flask Blueprint in die bestehende `app.py` registrieren |
| **Endpoint** | `POST /api/parse-time` |
| **PM2 Prozessname** | Bestehender PM2-Prozess der Booking App — kein neuer Prozess nötig |
| **Neue Abhängigkeiten** | `pip install rapidfuzz python-dateutil` → in `requirements.txt` eintragen |

### Integration in bestehende `app.py`

```python
from time_parser.routes import time_parser_bp
app.register_blueprint(time_parser_bp)
```

---

## 10. Offene Punkte vor Entwicklungsstart

| # | Frage | Priorität |
|---|---|---|
| 1 | Welches Framework nutzt die bestehende Booking App? (Flask bestätigen) | 🔴 Hoch |
| 2 | Gibt es bereits eine Suchanfrage-Struktur die `date/from/to` erwartet? | 🔴 Hoch |
| 3 | Soll `interpreted_as` im UI der Booking App angezeigt werden? | 🟡 Mittel |
| 4 | Wie soll mit völlig unverständlichen Eingaben umgegangen werden? (Fallback auf Kalender-Picker?) | 🟡 Mittel |
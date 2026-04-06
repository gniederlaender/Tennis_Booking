# Tennis Booking Finder — Technische Spezifikation (Erweiterung)

## 1. Projektübersicht

Die bestehende Tennis Booking Finder App wird um drei miteinander verbundene Features erweitert: ein öffentliches Live-Dashboard auf der Landing Page, einen stündlichen Cron-Script zur Datenbeschaffung sowie einen personalisierten wöchentlichen Newsletter-Service. Diese drei Komponenten bilden eine kohärente Pipeline: der Cron-Script sammelt Daten, die sowohl das Dashboard als auch den Newsletter speisen.

---

## 2. Zielgruppe & User Stories

- Als **nicht eingeloggter Besucher** möchte ich auf der Landing Page sofort sehen, wann in dieser Woche Plätze verfügbar sind, damit ich entscheiden kann, ob sich eine Registrierung lohnt.
- Als **eingeloggter User** möchte ich meinen Lieblings-Wochentag und meine bevorzugte Tageszeit in meinem Profil hinterlegen, damit ich automatisch einen personalisierten Newsletter erhalte.
- Als **Newsletter-Abonnent** möchte ich jeden Montag um 08:00 Uhr eine Email erhalten, die mir die Verfügbarkeit für meinen Favoriten-Block in der kommenden Woche zeigt, damit ich rechtzeitig reservieren kann.
- Als **App-Betreiber** möchte ich, dass die Verfügbarkeitsdaten stündlich automatisch aktualisiert werden, damit Dashboard und Newsletter stets aktuelle Informationen liefern.

---

## 3. Features & Screens

### 3.1 Feature 1 — Öffentliches Live-Dashboard (`landing.html`)

**Beschreibung:** Erweiterung der bestehenden Landing Page um eine Verfügbarkeits-Matrix als zentrales Element oberhalb des Fold. Für nicht eingeloggte Besucher sichtbar — ohne Login-Pflicht.

**Layout: 7×3 Matrix**

| | Mo | Di | Mi | Do | Fr | Sa | So |
|---|---|---|---|---|---|---|---|
| Morgen (07–12 Uhr) | 🟢/🟡/🔴 | ... | | | | | |
| Mittag (12–17 Uhr) | | | | | | | |
| Abend (17–22 Uhr) | | | | | | | |

**Verhalten:**
- Jede Zelle zeigt eine **aggregierte Ampel** für beide Standorte (Arsenal + PostSV)
  - 🟢 Grün: Mindestens 3 freie Slots an diesem Block (beide Standorte kombiniert)
  - 🟡 Gelb: 1–2 freie Slots
  - 🔴 Rot: Keine Slots verfügbar
- **Hover/Tap** auf eine Zelle öffnet ein Tooltip: `Arsenal 🟢 3 frei / PostSV 🔴 voll`
- **Timestamp** prominent sichtbar: `Stand: Montag, 14. Juli 2025 — 10:00 Uhr`
- **Highlight-Banner** (optional, über der Matrix): `Heute Abend noch 4 Plätze frei bei Arsenal`
- Nicht eingeloggte User sehen **keine** konkreten Uhrzeiten oder Court-Details — das bleibt der Login-geschützten Ansicht vorbehalten (Conversion-Anreiz)

---

### 3.2 Feature 2 — Stündlicher Cron-Script (`cron/update_snapshots.py`)

**Beschreibung:** Ein neues Python-Script, das stündlich ausgeführt wird, beide Standorte über die bestehenden Scraper abfragt und den aktuellen Stand in der Datenbank speichert.

**Verhalten:**
- Nutzt direkt die bestehende `scrapers_v2.py` — kein doppelter Code
- Speichert pro Durchlauf einen **Snapshot** in einer neuen DB-Tabelle `availability_snapshots`
- Wird via **System-Crontab** oder einem vergleichbaren Scheduler auf dem Server eingerichtet
- Loggt Erfolg/Fehler in eine Datei `logs/cron.log`

---

### 3.3 Feature 3 — Personalisierter Newsletter

**Beschreibung:** Eingeloggte User können einen Favoriten-Block (Wochentag + Tageszeit) in ihrem Profil hinterlegen. Jeden Montag um 08:00 Uhr erhalten alle Abonnenten eine personalisierte HTML-Email mit der Verfügbarkeit für ihren Block in der kommenden Woche.

**User-Einstellungen (Profil-Screen, bestehend oder neu):**
- Wochentag-Auswahl: Montag bis Sonntag (Dropdown)
- Tageszeit-Auswahl: Morgen / Mittag / Abend (Dropdown)
- Newsletter aktivieren: Ja / Nein (Toggle)

**Email-Inhalt (HTML-Template):**
1. **Header**: `Deine Tennis-Wochenvorschau 🎾`
2. **Persönlicher Block**: `Freitag Abend — Verfügbarkeit diese Woche`
3. **Mini-Ampel-Tabelle**: Zeigt für jeden Freitag Abend der kommenden Woche die Verfügbarkeit je Standort
4. **CTA-Button**: `Jetzt Platz buchen →` mit vorausgefülltem Deep-Link zur App
5. **Footer**: Link zu `Einstellungen ändern` und `Abmelden`

**Versand:**
- Jeden Montag 08:00 Uhr via eigenem Cron-Job (`cron/send_newsletter.py`)
- Versand über bestehendes SMTP-Setup des Servers

---

## 4. Technische Architektur

### Frontend
- **Technologie:** Jinja2 Templates (bestehend), HTML/CSS, minimales JavaScript für Hover-Tooltips auf der Matrix
- **Betroffene Files:** `landing.html` (Erweiterung), ggf. neuer Partial `_dashboard_matrix.html`

### Backend
- **Technologie:** Flask (bestehend), Python
- **Neue Module:**
  - `cron/update_snapshots.py` — Stündlicher Scraper-Runner
  - `cron/send_newsletter.py` — Wöchentlicher Newsletter-Versand
  - `templates/email/newsletter.html` — HTML-Email-Template
- **Bestehende Module (wiederverwendet):**
  - `scrapers_v2.py` — Scraping-Logik für beide Standorte
  - `database/db.py` — DB-Verbindung und Initialisierung
  - `config.py` — Zentrale Konfiguration (wird um SMTP-Vars erweitert)

### Datenbank
- **Technologie:** SQLite (bestehend)
- **Neue Tabellen:**

  **`availability_snapshots`**
  | Feld | Typ | Beschreibung |
  |---|---|---|
  | `id` | INTEGER PRIMARY KEY | |
  | `captured_at` | DATETIME | Zeitpunkt des Snapshots |
  | `location` | TEXT | `arsenal` oder `postsv` |
  | `weekday` | INTEGER | 0=Mo bis 6=So |
  | `timeblock` | TEXT | `morning`, `midday`, `evening` |
  | `available_slots` | INTEGER | Anzahl freier Slots |

- **Erweiterung bestehende User-Tabelle** (nach Analyse von `database/db.py`):
  - `newsletter_active` BOOLEAN DEFAULT 0
  - `newsletter_weekday` INTEGER (0=Mo bis 6=So)
  - `newsletter_timeblock` TEXT (`morning`, `midday`, `evening`)

  > ⚠️ **Entwicklungsregel #1**: Vor jeder DB-Änderung zuerst `database/db.py` und alle bestehenden Schema-Definitionen vollständig analysieren. Neue Felder und Tabellen müssen zur bestehenden Architektur und Migrationsstrategie passen. Keine Annahmen über bestehende Spaltennamen.

### Datenfluss

```
[Cron stündlich]
scrapers_v2.py → update_snapshots.py → availability_snapshots (DB)
                                               ↓
                                    Flask Route /landing
                                               ↓
                                    landing.html (Matrix-Dashboard)

[Cron montags 08:00]
availability_snapshots (DB) + users (DB) → send_newsletter.py
                                                    ↓
                                         newsletter.html (Template)
                                                    ↓
                                           SMTP → User-Email
```

---

## 5. Deployment

### Umgebungsvariablen (`.env`)

```env
# SMTP Konfiguration
SMTP_HOST=
SMTP_PORT=
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=

# Newsletter Konfiguration
NEWSLETTER_SEND_DAY=monday
NEWSLETTER_SEND_TIME=08:00
```

### Cron-Konfiguration (Server-Crontab)

```bash
# Stündlicher Snapshot-Update
0 * * * * /path/to/venv/bin/python /path/to/app/cron/update_snapshots.py >> /path/to/app/logs/cron.log 2>&1

# Wöchentlicher Newsletter (Montags 08:00 Uhr)
0 8 * * 1 /path/to/venv/bin/python /path/to/app/cron/send_newsletter.py >> /path/to/app/logs/newsletter.log 2>&1
```

### Logging
- `logs/cron.log` — Protokoll des stündlichen Snapshot-Scripts (Erfolg, Fehler, Anzahl gespeicherter Einträge)
- `logs/newsletter.log` — Protokoll des Newsletter-Versands (Anzahl versendeter Emails, fehlgeschlagene Zustellungen)

### Datenbankstrategie
- Snapshots älter als **30 Tage** werden automatisch gelöscht (Cleanup-Funktion in `update_snapshots.py`), um die SQLite-Datei schlank zu halten.
- Schema-Änderungen an der bestehenden User-Tabelle werden als **SQL-Migrationsskript** dokumentiert und versioniert.
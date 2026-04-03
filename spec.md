# Tennis Booking Finder — Technische Spezifikation

## 1. Projektübersicht

Tennis Booking Finder ist eine Webanwendung für Tennisspieler in Wien, die freie Plätze auf mehreren Buchungsportalen gleichzeitig durchsucht. Der Nutzer gibt einen Zeitraum in natürlicher deutscher Sprache ein und erhält sofort eine konsolidierte Übersicht aller verfügbaren Slots. Ein bestehendes MVP ist bereits in Produktion — diese Spezifikation beschreibt gezielte Erweiterungen ohne die bestehende Architektur zu ersetzen.

---

## 2. Zielgruppe & User Stories

- Als **Tennisspieler in Wien** möchte ich freie Plätze bei Arsenal und Post SV gleichzeitig suchen, damit ich nicht zwei Portale manuell prüfen muss.
- Als **registrierter Nutzer** möchte ich meine Zugangsdaten für jedes Portal einmalig hinterlegen, damit die App automatisch in meinem Namen buchen kann.
- Als **Erstbesucher der Landing Page** möchte ich in unter 5 Sekunden verstehen was die App tut, damit ich entscheide ob ich mich registriere.
- Als **Nutzer** möchte ich meinen Wunschzeitraum auf Deutsch eingeben (z.B. „Dienstag 18-20 Uhr"), damit ich keine englischen Begriffe oder exakten Datumsformate kennen muss.
- Als **wiederkehrender Nutzer** möchte ich Empfehlungen basierend auf meinen bisherigen Buchungen erhalten, damit ich bevorzugte Plätze schneller finde.

---

## 3. Features & Screens

### 3.1 Landing Page *(neu)*
Öffentlich zugänglich, kein Login erforderlich. Einmaliger Eindruck für Erstbesucher.

**Aufbau:**
- **Hero Section:** Headline „Alle Wiener Tennisplätze. Ein Zeitfenster. Sofort." — großer Weißraum, subtile Tennisplatz-Linien als CSS-Hintergrundelement, ein primärer CTA-Button „Platz finden"
- **Feature-Sektion:** Drei Icons mit je einem Satz — *Mehrere Portale gleichzeitig / Natürliche Sprache / Direkt buchen*
- **How-it-works-Sektion:** Drei nummerierte Schritte — *Zeitraum eingeben → Verfügbare Plätze sehen → Buchen*
- **Zweiter CTA:** „Jetzt kostenlos ausprobieren" mit Link zur Registrierung

**Design-System:**
- Farbschema: Weiß/Hellgrau als Basis, Tennis-Gelb (`#E8FF00` oder ähnlich) als einziger Akzent
- Typografie: Moderne Sans-Serif (z.B. Inter oder DM Sans), keine Serifen
- UI-Elemente: Glassmorphism-Cards für Feature-Blöcke (weißer Hintergrund, `backdrop-filter`, subtiler Schatten)
- Ton: Deutsch, direkt, kein Marketing-Sprech

### 3.2 Registrierung & Login *(bestehendes Feature — keine Änderung)*
Bestehendes Flask-Login-System bleibt unverändert.

### 3.3 Credential Manager *(neu)*
Erreichbar über Nutzer-Profil nach Login.

- Liste aller angebundenen Portale (Arsenal, Post SV, zukünftige)
- Pro Portal: Formular für Benutzername + Passwort
- Statusanzeige: „Verbunden" / „Nicht konfiguriert" / „Fehler beim letzten Login"
- Zugangsdaten werden verschlüsselt gespeichert (AES-256, Schlüssel pro Nutzer)
- Klarer Hinweistext warum die App diese Daten benötigt (Vertrauensaufbau)

### 3.4 Suchinterface / Chat-Interface *(bestehendes Feature — Erweiterung)*
Bestehendes Interface bleibt erhalten. Erweiterung: Zeitraum-Parser wird auf vollständige Deutsch-Unterstützung umgestellt.

- Eingabe in natürlicher Sprache: „nächsten Dienstag 18-20 Uhr", „Samstag Nachmittag", „morgen ab 17 Uhr"
- Alle deutschen Wochentage werden korrekt erkannt
- Relative Ausdrücke (morgen, übermorgen, nächste Woche) werden aufgelöst
- Parsed Zeitraum wird dem Nutzer vor der Suche zur Bestätigung angezeigt

### 3.5 Ergebnisliste *(bestehendes Feature — keine Änderung)*
Konsolidierte Anzeige aller verfügbaren Slots über alle angebundenen Portale.

### 3.6 Buchung *(bestehendes Feature — Erweiterung)*
Buchung nutzt ab sofort die im Credential Manager hinterlegten Zugangsdaten automatisch, anstatt den Nutzer bei jeder Buchung nach Login-Daten zu fragen.

---

## 4. Technische Architektur

### Frontend
- **Technologie:** Bestehendes Flask-Template-System (Jinja2 + HTML/CSS/JS) bleibt erhalten
- **Landing Page:** Neue statische HTML-Seite als Jinja2-Template, reines CSS ohne zusätzliche UI-Frameworks — kein Bootstrap-Overhead für diese eine Seite
- **Glassmorphism-Effekte:** Reines CSS (`backdrop-filter: blur()`, `background: rgba()`, `box-shadow`)
- **Keine neuen JavaScript-Frameworks** — bestehendes JS bleibt, Landing Page kommt ohne JS aus

### Backend
- **Technologie:** Bestehendes Flask-Backend (`app.py`) wird erweitert, nicht ersetzt
- **Neue Route:** `GET /` zeigt Landing Page (bisher vermutlich direkt Login oder Suche)
- **Neues Modul:** `credential_manager.py` — verwaltet verschlüsselte Portal-Zugangsdaten pro Nutzer
- **Patch:** `time_parser.py` (oder equivalent) — Austausch der bestehenden Parsing-Logik durch `dateparser`-Library mit expliziter Sprache Deutsch (`PREFER_LOCALE_DATE_ORDER`, `RETURN_AS_TIMEZONE_AWARE`)
- **Bestehend:** `scrapers_v2.py` bleibt vollständig erhalten, erhält Zugangsdaten künftig vom Credential Manager

### Datenhaltung
- **Bestehende Datenbank** (vermutlich SQLite) wird um eine Tabelle `user_credentials` erweitert:
  ```
  user_credentials (id, user_id, portal_name, encrypted_username, encrypted_password, last_verified_at)
  ```
- **Verschlüsselung:** `cryptography`-Library (Fernet/AES-256), Encryption-Key wird aus dem User-Passwort-Hash abgeleitet oder separat in Umgebungsvariablen gehalten

### Datenfluss

**Suche:**
Nutzer gibt Zeitraum auf Deutsch ein → `dateparser` löst Ausdruck in konkretes Datum/Uhrzeit auf → geparster Zeitraum wird dem Nutzer zur Bestätigung angezeigt → Bestätigung löst parallele Scraper-Aufrufe in `scrapers_v2.py` aus → Ergebnisse werden konsolidiert und als Liste zurückgegeben.

**Buchung:**
Nutzer wählt Slot → Backend liest verschlüsselte Zugangsdaten für das jeweilige Portal aus `user_credentials` → entschlüsselt zur Laufzeit → übergibt Credentials an den zuständigen Scraper in `scrapers_v2.py` → Buchung wird ausgeführt → Ergebnis (Bestätigung oder Fehler) wird dem Nutzer angezeigt → Zugangsdaten werden sofort aus dem Arbeitsspeicher verworfen.

### Neue Abhängigkeiten
| Library | Zweck | Begründung |
|---|---|---|
| `dateparser` | Deutsch-Zeitraum-Parsing | Ersetzt buggy Eigenimplementierung, unterstützt alle deutschen Wochentage und relative Ausdrücke |
| `cryptography` | Fernet-Verschlüsselung | Verschlüsselung der Portal-Zugangsdaten in der Datenbank |

---

## 5. Deployment

### Bestehende Strategie
Die bestehende Deployment-Konfiguration (Server, Hosting-Provider, Prozess-Manager) bleibt vollständig erhalten.

### Ergänzungen für neue Features

**Umgebungsvariablen (neu erforderlich):**
```
CREDENTIAL_ENCRYPTION_KEY=<32-Byte-Zufallsschlüssel, base64-encodiert>
```
Dieser Schlüssel muss vor dem ersten Start generiert und sicher im Hosting-Environment hinterlegt werden. Er darf nicht im Repository liegen.

**Datenbank-Migration:**
Beim Deploy wird ein einmaliges Migrationsskript `migrate_add_credentials.py` ausgeführt, das die Tabelle `user_credentials` zur bestehenden Datenbank hinzufügt. Bestehende Tabellen werden nicht verändert.

**Rollout-Reihenfolge:**
1. `dateparser`-Patch deployen und mit allen deutschen Wochentagen testen
2. Credential Manager deployen (neue Tabelle + neue Route)
3. Landing Page deployen (neue Route `GET /`, bestehende Routen unverändert)
4. Buchungsflow auf automatische Credential-Nutzung umstellen

**Testrollout:**
Vor der Erweiterung auf weitere Tennisanlagen wird mit den bestehenden zwei Portalen (Arsenal, Post SV) verifiziert, dass Credential Manager und Zeitraum-Parsing stabil laufen.
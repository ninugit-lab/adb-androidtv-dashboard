# ADB AndroidTV Dashboard – Design

## Zweck

Eine kleine Django-App mit einem Dashboard, über das beliebige ADB-Shell-Befehle
("Commands") an mehrere, einzeln konfigurierbare AndroidTV-Geräte im lokalen
Netzwerk gesendet werden können. Commands werden zentral definiert und einem
oder mehreren Geräten zugewiesen; auf dem Dashboard erscheinen sie pro Gerät
als Schnellauswahl-Buttons.

## Nicht-Ziele

- Kein Login/Auth (App ist im vertrauten Heimnetz offen erreichbar).
- Keine Django-DB-Models für Geräte/Commands – Persistenz erfolgt über eine
  JSON-Datei.
- Keine App-Installation, kein Screen-Mirroring, kein File-Transfer – nur
  Shell-Commands.

## Architektur

**Stack:** Django (Standard-Projekt, SQLite bleibt ungenutzt für dieses
Feature), `pure-python-adb` (`ppadb`) für die ADB-Kommunikation, Vanilla
JS/Fetch für AJAX (kein Frontend-Framework nötig).

**Views/Routen:**

- `GET /` – Dashboard. Zeigt pro Gerät eine Karte mit Name, Online/Offline-
  Badge und einem Button pro zugewiesenem Command.
- `POST /device/<device_id>/run/<command_id>/` – führt den Command auf dem
  Gerät aus, gibt JSON `{ok: bool, output/error: str}` zurück (per Fetch vom
  Dashboard aufgerufen, kein Page-Reload).
- `GET/POST /config/` – Verwaltungsseite: Geräte anlegen/bearbeiten/löschen
  (Name, IP, Port), Commands anlegen/bearbeiten/löschen (Name, Shell-Befehl),
  Zuweisung von Commands zu Geräten via Checkboxen/Multi-Select.

**ADB-Anbindung (`adb_client.py`):**

- Ein `ppadb.client.Client`-Singleton (verbindet zum lokalen adb-Server,
  Standard `127.0.0.1:5037`).
- `connect_device(ip, port)` → versucht `client.remote_connect(ip, port)`,
  gibt bei Erfolg das Device-Objekt zurück, sonst `None`.
- `run_command(ip, port, cmd)` → verbindet, führt `device.shell(cmd)` aus,
  fängt Exceptions/Timeouts ab und liefert ein einheitliches Ergebnis-Objekt
  (`ok`, `output`, `error`).
- `check_status(ip, port)` → kurzer Connect-Versuch für die Online/Offline-
  Anzeige auf dem Dashboard (beim Laden der Seite serverseitig für jedes
  Gerät ausgeführt).

**Datenhaltung (`config_store.py` + `config.json`):**

Eine JSON-Datei im Projektverzeichnis, ausschließlich über die `/config`-UI
gepflegt (kein Workflow für manuelle Bearbeitung, aber technisch reines
JSON):

```json
{
  "devices": [
    {
      "id": "uuid",
      "name": "Wohnzimmer",
      "ip": "192.168.1.50",
      "port": 5555,
      "command_ids": ["uuid-1", "uuid-2"]
    }
  ],
  "commands": [
    {
      "id": "uuid-1",
      "name": "Netflix öffnen",
      "cmd": "monkey -p com.netflix.ninja -c android.intent.category.LAUNCHER 1"
    }
  ]
}
```

`config_store.py` kapselt Lesen/Schreiben (mit File-Lock beim Schreiben, um
Race Conditions bei gleichzeitigen Config-Änderungen zu vermeiden) und
stellt einfache Funktionen bereit: `load()`, `save(data)`,
`add_device()`, `update_device()`, `delete_device()`, analog für Commands
und für die Zuweisung (`assign_command(device_id, command_id)` /
`unassign_command(...)`). Views nutzen ausschließlich dieses Modul, kein
Django-ORM für diese Daten.

## Fehlerbehandlung

- Schlägt `adb connect` oder `device.shell()` fehl (Timeout, Verbindung
  abgelehnt, Exception), wird das im Dashboard als klare Fehlermeldung
  angezeigt (z. B. "Gerät nicht erreichbar"), die App bleibt stabil.
- Jede Gerätekarte zeigt zusätzlich einen Online/Offline-Status-Badge, der
  beim Laden der Dashboard-Seite per kurzem `check_status`-Aufruf für jedes
  Gerät ermittelt wird.

## Testing

- Unit-Tests für `config_store.py` (CRUD auf Devices/Commands, Zuweisung,
  Locking) ohne echte ADB-Verbindung.
- Unit-Tests für Views mit gemocktem `adb_client` (Erfolg, Verbindungsfehler,
  Shell-Fehler) um Statuscodes und JSON-Responses zu prüfen.
- Kein Live-Test gegen echte Hardware im automatisierten Testlauf; manuelles
  Testen gegen ein reales AndroidTV-Gerät als Abschluss der Implementierung.

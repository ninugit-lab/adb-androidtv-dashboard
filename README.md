# ADB AndroidTV Dashboard

Django-Dashboard zum Senden von ADB-Shell-Befehlen an mehrere AndroidTV-Geräte
im lokalen Netzwerk.

## Setup (kein venv, alle Pakete projekt-lokal)

**Linux/macOS:**
```bash
./setup.sh
python manage.py runserver
```

**Windows:**
```bat
setup.bat
python manage.py runserver
```

Danach:
- Dashboard: http://127.0.0.1:8000/
- Konfiguration: http://127.0.0.1:8000/config/

Geräte und Commands werden in `config.json` im Projektverzeichnis
gespeichert (wird beim ersten Speichern automatisch angelegt).

Voraussetzung: Ein laufender `adb`-Server auf dem Host (`adb start-server`),
erreichbar unter `127.0.0.1:5037`, sowie Netzwerkzugriff auf die
AndroidTV-Geräte (ADB-Debugging über Netzwerk muss auf den Geräten aktiviert
sein).

**Wichtig:** `pure-python-adb` verbindet sich nur zu einem bereits laufenden
`adb`-Server, startet ihn aber nicht selbst. Auf jedem neuen Host, von dem
aus die App läuft, muss `adb` installiert sein und mindestens einmal
`adb start-server` ausgeführt worden sein. Zusätzlich muss jedes AndroidTV-
Gerät die ADB-Verbindung vom jeweiligen Host autorisieren (Debugging-
Freigabe-Dialog auf dem Fernseher, host-spezifisch — ein neuer Laptop
braucht eine eigene Freigabe, auch wenn ein anderer Rechner bereits
verbunden war). Ohne laufenden `adb`-Server bzw. ohne Autorisierung zeigt
das Dashboard alle Geräte als "Offline" an, unabhängig vom Inhalt der
`config.json`.

### adb-Server unter Windows automatisch beim Login starten

Damit der `adb`-Server nicht nach jedem Neustart manuell gestartet werden
muss:

```bat
scripts\install-adb-autostart.bat
```

Legt eine Aufgabe in der Windows-Aufgabenplanung an, die `adb start-server`
bei jeder Anmeldung ausführt (Voraussetzung: `adb` ist im `PATH`). Danach
läuft der `adb`-Server automatisch, bevor das Dashboard gestartet wird.

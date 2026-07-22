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

@echo off
setlocal
set SCRIPT_DIR=%~dp0
schtasks /create /tn "ADB Server Autostart" /tr "\"%SCRIPT_DIR%start-adb-server.bat\"" /sc onlogon /rl limited /f
if errorlevel 1 (
    echo Einrichtung fehlgeschlagen.
    exit /b 1
)
echo Autostart eingerichtet. Der adb-Server startet ab jetzt bei jeder Windows-Anmeldung.

@echo off
cd /d "%~dp0"
python -m pip install --target=.\vendor -r requirements.txt
if errorlevel 1 (
    echo Setup fehlgeschlagen.
    exit /b 1
)
echo Setup complete. Run: python manage.py runserver

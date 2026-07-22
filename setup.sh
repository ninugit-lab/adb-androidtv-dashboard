#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
pip install --target=./vendor -r requirements.txt
echo "Setup complete. Run: python manage.py runserver"

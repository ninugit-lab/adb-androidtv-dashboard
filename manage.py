#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path


def main():
    vendor_path = str(Path(__file__).resolve().parent / "vendor")
    if vendor_path not in sys.path:
        sys.path.insert(0, vendor_path)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "adbdash.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Is it installed in ./vendor? "
            "Run ./setup.sh first."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

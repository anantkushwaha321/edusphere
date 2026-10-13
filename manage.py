#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import subprocess


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # Auto-detect local virtualenv if user forgot to activate it
        base_dir = os.path.dirname(os.path.abspath(__file__))
        venv_candidates = [
            os.path.join(base_dir, 'venv', 'Scripts', 'python.exe'),
            os.path.join(base_dir, 'venv', 'bin', 'python'),
            os.path.join(base_dir, '.venv', 'Scripts', 'python.exe'),
            os.path.join(base_dir, '.venv', 'bin', 'python'),
        ]
        for venv_python in venv_candidates:
            if os.path.exists(venv_python) and os.path.abspath(sys.executable).lower() != os.path.abspath(venv_python).lower():
                # Re-run transparently with the virtual environment's Python interpreter
                result = subprocess.run([venv_python] + sys.argv)
                sys.exit(result.returncode)

        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()

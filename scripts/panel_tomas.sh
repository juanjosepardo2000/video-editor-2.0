#!/bin/sh
# Abre el panel local de control de tomas en http://127.0.0.1:8765
cd "$(dirname "$0")/.." || exit 1
PYTHONPATH=src exec .venv/bin/python -W ignore -m tomas.server "$@"

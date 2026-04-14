#!/bin/bash
# Script simple para actualizar la base de datos de Polymarket

# Ir al directorio raíz del proyecto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

source .venv/bin/activate
python3 actualizar_poly/actualizar_db.py

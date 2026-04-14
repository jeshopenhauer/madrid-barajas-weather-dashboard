#!/bin/bash
# Script simplificado para actualizar base_datos.db de Meteociel

# Ir al directorio raíz del proyecto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

source .venv/bin/activate
python3 actualizar_meteociel/meteociel_actualizar.py

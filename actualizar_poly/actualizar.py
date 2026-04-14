#!/usr/bin/env python3
"""
Script simplificado para actualizar base de datos de Polymarket Madrid
Uso: python3 actualizar.py
"""

import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path

def print_header(text):
    print(f"\n{'='*70}")
    print(f"  {text}")
    print('='*70)

def main():
    print_header("🔄 ACTUALIZACIÓN POLYMARKET MADRID")
    
    # Obtener directorio del script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_script = os.path.join(script_dir, 'actualizar_db.py')
    
    # 1. Actualizar base de datos
    print("\n📥 Actualizando base de datos...")
    result = subprocess.run(
        ['python3', db_script, '2026', '3', '2026', '4'],
        capture_output=False
    )
    
    if result.returncode != 0:
        print("❌ Error actualizando base de datos")
        return 1
    
    print_header("✅ ACTUALIZACIÓN COMPLETADA")
    print(f"\n📁 Base de datos: ../polymarket_history.db")
    print(f"🕐 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelado por el usuario")
        sys.exit(1)

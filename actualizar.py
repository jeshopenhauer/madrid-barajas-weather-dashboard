#!/usr/bin/env python3
"""
Script simplificado para actualizar base de datos y gráficas de Polymarket Madrid
Uso: python3 actualizar.py
"""

import subprocess
import sys
from datetime import datetime

def print_header(text):
    print(f"\n{'='*70}")
    print(f"  {text}")
    print('='*70)

def main():
    print_header("🔄 ACTUALIZACIÓN POLYMARKET MADRID")
    
    # 1. Actualizar base de datos
    print("\n📥 Paso 1/3: Actualizando base de datos...")
    result = subprocess.run(
        ['python3', 'actualizar_db.py', '2026', '3', '2026', '4'],
        capture_output=False
    )
    
    if result.returncode != 0:
        print("❌ Error actualizando base de datos")
        return 1
    
    # 2. Generar gráficas
    print("\n📊 Paso 2/3: Generando gráficas...")
    result = subprocess.run(
        ['python3', 'generate_graphs.py'],
        capture_output=False
    )
    
    if result.returncode != 0:
        print("❌ Error generando gráficas")
        return 1
    
    # 3. Mostrar resumen
    print("\n📈 Paso 3/3: Resumen final...")
    result = subprocess.run(
        ['python3', 'check_db.py'],
        capture_output=False
    )
    
    print_header("✅ ACTUALIZACIÓN COMPLETADA")
    print(f"\n📁 Base de datos: polymarket_history.db")
    print(f"📁 Gráficas: madrid_graphs/")
    print(f"🕐 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelado por el usuario")
        sys.exit(1)

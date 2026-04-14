#!/usr/bin/env python3
"""
Inspecciona la estructura de base_datos.db
"""

import sqlite3

conn = sqlite3.connect('base_datos.db')
cursor = conn.cursor()

print("="*80)
print("ESTRUCTURA DE BASE_DATOS.DB")
print("="*80)

# Listar todas las tablas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()

print(f"\n📊 Total de tablas: {len(tables)}\n")

# Mostrar primeras y últimas tablas
print("Primeras 5 tablas:")
for table in tables[:5]:
    print(f"  - {table[0]}")

print("\nÚltimas 5 tablas:")
for table in tables[-5:]:
    print(f"  - {table[0]}")

# Obtener esquema de una tabla ejemplo
if tables:
    tabla_ejemplo = tables[-1][0]  # Última tabla (más reciente)
    print(f"\n📋 Esquema de '{tabla_ejemplo}':")
    cursor.execute(f"SELECT sql FROM sqlite_master WHERE name='{tabla_ejemplo}'")
    schema = cursor.fetchone()[0]
    print(schema)
    
    # Mostrar datos de ejemplo
    cursor.execute(f"SELECT * FROM {tabla_ejemplo} LIMIT 3")
    rows = cursor.fetchall()
    
    print(f"\n📊 Primeros 3 registros de '{tabla_ejemplo}':")
    cursor.execute(f"PRAGMA table_info({tabla_ejemplo})")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"Columnas: {columns}")
    
    for row in rows:
        print(f"  {row}")
    
    # Contar registros
    cursor.execute(f"SELECT COUNT(*) FROM {tabla_ejemplo}")
    count = cursor.fetchone()[0]
    print(f"\nTotal registros en '{tabla_ejemplo}': {count}")

conn.close()

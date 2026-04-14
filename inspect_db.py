#!/usr/bin/env python3
"""
Script para inspeccionar la estructura de base_datos.db
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

print(f"\n📊 Total tablas: {len(tables)}")
print("\nTablas encontradas:")
for table in tables:
    table_name = table[0]
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"  - {table_name}: {count} registros")

# Ver estructura de una tabla de ejemplo
if tables:
    example_table = tables[-1][0]  # Última tabla
    print(f"\n📋 Estructura de tabla ejemplo: {example_table}")
    cursor.execute(f"PRAGMA table_info({example_table})")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  - {col[1]} {col[2]} {'NOT NULL' if col[3] else ''} {'PRIMARY KEY' if col[5] else ''}")
    
    # Ver últimos registros
    print(f"\n📄 Últimos 3 registros de {example_table}:")
    cursor.execute(f"SELECT * FROM {example_table} ORDER BY timestamp_utc DESC LIMIT 3")
    for row in cursor.fetchall():
        print(f"  {row}")

conn.close()

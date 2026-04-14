#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('base_datos.db')
cursor = conn.cursor()

# Ver esquema de tabla marzo 2026
cursor.execute('SELECT sql FROM sqlite_master WHERE name="madrid_barajas_temperatures_2026_03"')
schema = cursor.fetchone()
if schema:
    print('ESQUEMA DE madrid_barajas_temperatures_2026_03:')
    print(schema[0])
    print()

# Ver últimos registros
cursor.execute('SELECT * FROM madrid_barajas_temperatures_2026_03 ORDER BY id DESC LIMIT 5')
print('ÚLTIMOS 5 REGISTROS:')
for row in cursor.fetchall():
    print(row)

conn.close()

#!/usr/bin/env python3
"""
Actualiza base de datos de Meteociel con datos históricos
PRIMERO PRUEBA EN UNA BD NUEVA (meteociel_test.db)
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import sqlite3
import time
import sys
import re

class MeteocielHistoricalUpdater:
    def __init__(self, db_path="meteociel_test.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.base_url = "https://www.meteociel.fr/temps-reel/obs_villes.php"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def create_table_for_month(self, year, month):
        """Crea tabla para un mes específico si no existe"""
        table_name = f"madrid_barajas_temperatures_{year}_{month:02d}"
        
        cursor = self.conn.cursor()
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_utc DATETIME NOT NULL UNIQUE,
                timestamp_local DATETIME NOT NULL,
                temperature REAL,
                humidity INTEGER,
                wind_speed INTEGER,
                pressure REAL
            )
        """)
        self.conn.commit()
        
        print(f"✅ Tabla '{table_name}' lista")
        return table_name
    
    def parse_wind_speed(self, cell):
        """
        Parsea velocidad del viento de una celda HTML
        Maneja formatos como: "9 km/h", "11 km/h (15)", etc.
        Retorna solo el primer número (velocidad, no ráfagas)
        """
        try:
            # Obtener todo el texto de la celda (sin parámetros extra)
            full_text = cell.get_text()
            
            # Buscar el primer número seguido de km/h
            match = re.search(r'(\d+)\s*km/h', full_text)
            if match:
                return int(match.group(1))
        except:
            pass
        return None
    
    def parse_pressure(self, cell):
        """
        Parsea presión de una celda HTML
        Maneja formatos como: "1021 hPa", "1020.6 hPa ↗", etc.
        """
        try:
            # Obtener todo el texto de la celda (sin parámetros extra)
            full_text = cell.get_text()
            
            # Buscar número (entero o decimal) seguido de hPa
            match = re.search(r'(\d+\.?\d*)\s*hPa', full_text)
            if match:
                return float(match.group(1))
        except:
            pass
        return None
    
    def scrape_day(self, year, month, day):
        """
        Scrapea datos de un día específico desde Meteociel
        IMPORTANTE: mois2 va de 0 (enero) a 11 (diciembre)
        """
        # Meteociel usa mois2=0-11 (0=enero, 11=diciembre)
        mois2 = month - 1
        
        # URL del archivo histórico
        url = f"{self.base_url}?code2=8221&jour2={day}&mois2={mois2}&annee2={year}"
        
        print(f"\n🔍 Scrapeando {year}-{month:02d}-{day:02d}...")
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.encoding = 'ISO-8859-1'
            
            if response.status_code != 200:
                print(f"   ❌ Error HTTP: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            rows = soup.find_all('tr')
            
            data_points = []
            
            for row in rows:
                cells = row.find_all('td')
                
                if len(cells) >= 12:  # Necesitamos al menos 12 columnas (0-11)
                    hora_cell = cells[0].get_text(strip=True)
                    
                    # Verificar formato de hora válido
                    if 'h' in hora_cell and len(hora_cell) <= 6:
                        try:
                            # Parsear hora UTC (formato: "18h30")
                            hora_utc_str = hora_cell.replace('h', ':')
                            if ':' not in hora_utc_str:
                                hora_utc_str += ':00'
                            
                            # Crear timestamp UTC
                            timestamp_utc = f"{year}-{month:02d}-{day:02d} {hora_utc_str}:00"
                            
                            # Convertir a hora local (UTC+1 en invierno, UTC+2 en verano)
                            # Por simplicidad usamos UTC+1 siempre
                            hora_parts = hora_utc_str.split(':')
                            hora_int = int(hora_parts[0])
                            minuto_int = int(hora_parts[1])
                            
                            dt_utc = datetime(year, month, day, hora_int, minuto_int)
                            dt_local = dt_utc + timedelta(hours=1)
                            timestamp_local = dt_local.strftime("%Y-%m-%d %H:%M:%S")
                            
                            # Extraer temperatura (columna 4)
                            temperature = None
                            temp_text = cells[4].get_text(strip=True)
                            if '°C' in temp_text or '°' in temp_text:
                                temp_value = temp_text.replace('°C', '').replace('°', '').strip()
                                if temp_value and temp_value != '-':
                                    temperature = float(temp_value)
                            
                            # Extraer humedad (columna 5)
                            humidity = None
                            try:
                                hum_text = cells[5].get_text(strip=True)
                                if '%' in hum_text:
                                    hum_value = hum_text.replace('%', '').strip()
                                    if hum_value and hum_value != '-':
                                        humidity = int(hum_value)
                            except:
                                pass
                            
                            # Extraer viento (columna 10) - NO columna 9
                            wind_speed = self.parse_wind_speed(cells[10])
                            
                            # Extraer presión (columna 11) - NO columna 10
                            pressure = self.parse_pressure(cells[11])
                            
                            data_point = {
                                'timestamp_utc': timestamp_utc,
                                'timestamp_local': timestamp_local,
                                'temperature': temperature,
                                'humidity': humidity,
                                'wind_speed': wind_speed,
                                'pressure': pressure
                            }
                            
                            data_points.append(data_point)
                            
                        except Exception as e:
                            continue
            
            print(f"   ✅ Obtenidos {len(data_points)} registros")
            return data_points
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return []
    
    def insert_data(self, table_name, data_points):
        """Inserta datos en la tabla"""
        if not data_points:
            return 0
        
        cursor = self.conn.cursor()
        inserted = 0
        
        for dp in data_points:
            try:
                cursor.execute(f"""
                    INSERT OR IGNORE INTO {table_name} 
                    (timestamp_utc, timestamp_local, temperature, humidity, wind_speed, pressure)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    dp['timestamp_utc'],
                    dp['timestamp_local'],
                    dp['temperature'],
                    dp['humidity'],
                    dp['wind_speed'],
                    dp['pressure']
                ))
                if cursor.rowcount > 0:
                    inserted += 1
            except sqlite3.IntegrityError:
                # Ya existe
                pass
        
        self.conn.commit()
        print(f"   💾 Insertados {inserted} registros nuevos")
        return inserted
    
    def get_last_date_in_db(self):
        """Obtiene la última fecha registrada en la base de datos"""
        cursor = self.conn.cursor()
        
        # Obtener todas las tablas de temperaturas
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE 'madrid_barajas_temperatures_%' 
            ORDER BY name DESC
        """)
        tables = cursor.fetchall()
        
        if not tables:
            return None
        
        last_date = None
        last_table = None
        
        for table_name, in tables:
            try:
                cursor.execute(f"SELECT MAX(timestamp_local) FROM {table_name}")
                max_date_str = cursor.fetchone()[0]
                if max_date_str:
                    max_date = datetime.strptime(max_date_str, "%Y-%m-%d %H:%M:%S")
                    if last_date is None or max_date > last_date:
                        last_date = max_date
                        last_table = table_name
            except:
                continue
        
        if last_date:
            print(f"📅 Última fecha en BD: {last_date.strftime('%Y-%m-%d %H:%M')}")
            print(f"📦 En la tabla: {last_table}")
        
        return last_date
    
    def update_from_date(self, start_date, end_date=None):
        """
        Actualiza datos desde start_date hasta end_date (o hoy si no se especifica)
        """
        if end_date is None:
            end_date = datetime.now()
        
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
        
        print("="*80)
        print("ACTUALIZANDO BASE DE DATOS METEOCIEL")
        print("="*80)
        print(f"Desde: {start_date.strftime('%Y-%m-%d')}")
        print(f"Hasta: {end_date.strftime('%Y-%m-%d')}")
        print(f"Base de datos: {self.db_path}")
        print("="*80)
        
        current_date = start_date
        total_inserted = 0
        
        while current_date <= end_date:
            year = current_date.year
            month = current_date.month
            day = current_date.day
            
            # Crear tabla para este mes si no existe
            table_name = self.create_table_for_month(year, month)
            
            # Scrapear día
            data_points = self.scrape_day(year, month, day)
            
            # Insertar datos
            inserted = self.insert_data(table_name, data_points)
            total_inserted += inserted
            
            # Avanzar al siguiente día
            current_date += timedelta(days=1)
            
            # Rate limiting
            time.sleep(0.5)
        
        print("\n" + "="*80)
        print("✅ ACTUALIZACIÓN COMPLETADA")
        print("="*80)
        print(f"Total registros nuevos insertados: {total_inserted}")
        
        self.show_summary()
    
    def show_summary(self):
        """Muestra resumen de la base de datos"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'madrid%' ORDER BY name")
        tables = cursor.fetchall()
        
        print(f"\n📊 Tablas en la base de datos: {len(tables)}")
        
        total_records = 0
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            total_records += count
            
            if count > 0:
                cursor.execute(f"SELECT MIN(timestamp_utc), MAX(timestamp_utc) FROM {table_name}")
                min_t, max_t = cursor.fetchone()
                print(f"  {table_name}: {count} registros ({min_t} - {max_t})")
        
        print(f"\n📈 Total registros: {total_records}")
    
    def close(self):
        """Cierra la conexión"""
        self.conn.close()


def main():
    import sys
    from datetime import datetime
    
    # Determinar qué base de datos usar
    if "--test" in sys.argv:
        db_path = "meteociel_test.db"
        print("🧪 MODO PRUEBA - Usando meteociel_test.db\n")
        sys.argv.remove("--test")
    else:
        db_path = "base_datos.db"
        print("📊 ACTUALIZANDO BASE DE DATOS REAL: base_datos.db\n")
    
    updater = MeteocielHistoricalUpdater(db_path=db_path)
    
    try:
        if len(sys.argv) >= 2 and sys.argv[1] not in ["--auto"]:
            # Argumentos: fecha_inicio [fecha_fin]
            start_date = sys.argv[1]
            end_date = sys.argv[2] if len(sys.argv) > 2 else None
            updater.update_from_date(start_date, end_date)
        else:
            # Modo automático: detectar última fecha y actualizar hasta hoy
            print("🤖 MODO AUTOMÁTICO")
            print("Detectando última fecha en la base de datos...\n")
            
            last_date = updater.get_last_date_in_db()
            
            if last_date:
                # Actualizar desde el día siguiente a la última fecha
                start_date = last_date + timedelta(days=1)
                start_date = start_date.replace(hour=0, minute=0, second=0)
                end_date = datetime.now()
                
                print(f"🔄 Actualizando desde {start_date.strftime('%Y-%m-%d')} hasta hoy\n")
                updater.update_from_date(start_date, end_date)
            else:
                print("⚠️  Base de datos vacía. Especifica fechas manualmente:")
                print("   python3 meteociel_actualizar.py YYYY-MM-DD [YYYY-MM-DD]")
                return
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Actualización interrumpida")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        updater.close()
        print("\n✅ Conexión cerrada")
        print("\n✅ Conexión cerrada")


if __name__ == "__main__":
    main()

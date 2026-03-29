#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import time
import sqlite3
import re
from typing import Dict, Any, List

class MeteocielHistoricalScraper:
    def __init__(self, db_path="base_datos.db"):
        self.base_url = "https://www.meteociel.fr/temps-reel/obs_villes.php"
        self.code_station = "8221"  # Madrid-Barajas
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.db_path = db_path
        self.madrid_tz = pytz.timezone('Europe/Madrid')
        self.utc_tz = pytz.utc

    def _ensure_table_exists(self, cursor, table_name):
        """Inicializa la tabla en la base de datos si no existe."""
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_utc DATETIME NOT NULL UNIQUE,
                timestamp_local DATETIME NOT NULL,
                temperature REAL,
                humidity INTEGER,
                wind_speed INTEGER,
                pressure REAL
            )
        ''')

    def convert_to_local_and_utc(self, fecha: datetime.date, hora_utc_str: str):
        # hora_utc_str expected format like "23h30" or "18h00"
        try:
            hora_utc_str = hora_utc_str.replace('h', ':')
            parts = hora_utc_str.split(':')
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
            
            # UTC timestamp
            dt_utc = datetime(fecha.year, fecha.month, fecha.day, hour, minute)
            dt_utc = self.utc_tz.localize(dt_utc)
            
            # Convert to local time appropriately considering DST (Europe/Madrid)
            dt_local = dt_utc.astimezone(self.madrid_tz)
            
            return dt_utc, dt_local
        except Exception as e:
            print(f"Error parsing time {hora_utc_str}: {e}")
            return None, None

    def scrape_day(self, date: datetime.date) -> List[Dict[str, Any]]:
        # En meteociel el mes empieza en 0
        jour = date.day
        mois = date.month - 1
        annee = date.year
        
        params = {
            'code2': self.code_station,
            'jour2': jour,
            'mois2': mois,
            'annee2': annee
        }
        
        url_with_params = f"{self.base_url}?code2={self.code_station}&jour2={jour}&mois2={mois}&annee2={annee}"
        
        max_retries = 3
        for retry in range(max_retries):
            try:
                response = requests.get(url_with_params, headers=self.headers, timeout=15)
                response.encoding = 'ISO-8859-1'
                
                if response.status_code != 200:
                    print(f"❌ Error HTTP {response.status_code} para {date.isoformat()}")
                    return []
                    
                soup = BeautifulSoup(response.text, 'html.parser')
                
                rows = soup.find_all('tr')
                data_list = []
                
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 10:
                        hora_cell = cells[0].get_text(strip=True)
                        if 'h' in hora_cell and len(hora_cell) <= 6:
                            try:
                                # Température
                                temp_text = cells[4].get_text(strip=True)
                                temperature = None
                                if '°C' in temp_text:
                                    temperature = float(temp_text.replace('°C', '').replace('°', '').strip())
                                    
                                # Humidité
                                humidity = None
                                hum_text = cells[5].get_text(strip=True)
                                if '%' in hum_text:
                                    try:
                                        humidity = int(hum_text.replace('%', '').strip())
                                    except:
                                        pass
                                    
                                # Búsqueda robusta de Viento y Presión con Regex
                                wind = None
                                pressure = None
                                for cell in cells[6:]:
                                    cell_text = cell.get_text(separator=' ', strip=True)
                                    
                                    if wind is None and 'km/h' in cell_text:
                                        match = re.search(r'(\d+)\s*km/h', cell_text)
                                        if match:
                                            wind = int(match.group(1))
                                            
                                    if pressure is None and 'hPa' in cell_text:
                                        match = re.search(r'(\d+(?:\.\d+)?)\s*hPa', cell_text)
                                        if match:
                                            pressure = float(match.group(1))
                                    
                                dt_utc, dt_local = self.convert_to_local_and_utc(date, hora_cell)
                                
                                if dt_utc and temperature is not None:
                                    data_list.append({
                                        'timestamp_utc': dt_utc,
                                        'timestamp_local': dt_local,
                                        'temperature': temperature,
                                        'humidity': humidity,
                                        'wind_speed': wind,
                                        'pressure': pressure
                                    })
                            except Exception as e:
                                pass
                return data_list
                
            except Exception as e:
                print(f"Error scraping {date.isoformat()}: {e} (Attempt {retry+1}/{max_retries})")
                time.sleep(2)
                
        return []

    def save_to_db(self, records: List[Dict[str, Any]]):
        if not records:
            return 0
            
        saved_count = 0
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Agrupar registros por Año_Mes para guardarlos en tablas diferentes
            records_by_month = {}
            for r in records:
                ym = r['timestamp_utc'].strftime('%Y_%m')
                if ym not in records_by_month:
                    records_by_month[ym] = []
                records_by_month[ym].append(r)
                
            for ym, month_records in records_by_month.items():
                table_name = f"madrid_barajas_temperatures_{ym}"
                # Nos aseguramos que la tabla del mes en cuestión exista
                self._ensure_table_exists(cursor, table_name)
                
                insert_query = f'''
                    INSERT OR IGNORE INTO {table_name}
                    (timestamp_utc, timestamp_local, temperature, humidity, wind_speed, pressure)
                    VALUES (?, ?, ?, ?, ?, ?)
                '''
                
                for r in month_records:
                    cursor.execute(insert_query, (
                        r['timestamp_utc'].strftime('%Y-%m-%d %H:%M:%S'),
                        r['timestamp_local'].strftime('%Y-%m-%d %H:%M:%S'),
                        r['temperature'],
                        r['humidity'],
                        r['wind_speed'],
                        r['pressure']
                    ))
                    if cursor.rowcount > 0:
                        saved_count += 1
                        
            conn.commit()
            return saved_count
        except Exception as e:
            print(f"Error guardando en BD: {e}")
            return 0
        finally:
            if conn:
                conn.close()

def main():
    db_path = "base_datos.db"
    scraper = MeteocielHistoricalScraper(db_path)
        
    start_date = datetime(2018, 1, 1).date()
    # Usando como fecha actual el 29 de Marzo de 2026 proporcionada en el prompt.
    end_date = datetime(2026, 3, 29).date()
    
    current_date = start_date
    
    print(f"Iniciando raspado histórico desde {start_date} hasta {end_date}")
    
    while current_date <= end_date:
        print(f"Scrapeando {current_date.isoformat()}... ", end="", flush=True)
        
        datos_dia = scraper.scrape_day(current_date)
        
        if datos_dia:
            nuevos = scraper.save_to_db(datos_dia)
            print(f"OK ({len(datos_dia)} registros, {nuevos} nuevos)")
        else:
            print("Sin datos o error")
            
        current_date += timedelta(days=1)
        
        # Pausa amable con el servidor (1-2 segundos)
        time.sleep(1)

if __name__ == "__main__":
    main()

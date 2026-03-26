#!/usr/bin/env python3
"""
Web Scraper para Meteociel - Aeropuerto Madrid-Barajas
URL: https://www.meteociel.fr/temps-reel/obs_villes.php?code2=8221

IMPORTANTE: La hora en la página está en UTC, hay que sumar 1 hora para hora local española
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import sys

class MeteocielScraper:
    def __init__(self):
        self.url = "https://www.meteociel.fr/temps-reel/obs_villes.php?code2=8221"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def get_temperature(self):
        """Obtiene la temperatura más reciente de la tabla de Meteociel"""
        try:
            response = requests.get(self.url, headers=self.headers, timeout=10)
            response.encoding = 'ISO-8859-1'  # La página usa ISO-8859-1
            
            if response.status_code != 200:
                print(f"❌ Error HTTP: {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscar todas las filas de la tabla
            rows = soup.find_all('tr')
            
            all_data = []
            
            for row in rows:
                cells = row.find_all('td')
                
                # La primera celda contiene la hora (formato: 18h30, 18h00, etc.)
                if len(cells) >= 10:  # Asegurar que tiene suficientes columnas
                    hora_cell = cells[0].get_text(strip=True)
                    
                    # Verificar si es una fila válida con hora (formato: XXhXX)
                    if 'h' in hora_cell and len(hora_cell) <= 6:
                        try:
                            # Extraer temperatura de la columna correcta (columna 4: "Température")
                            temp_text = cells[4].get_text(strip=True)
                            
                            if '°C' in temp_text:
                                temp_value = temp_text.replace('°C', '').replace('°', '').strip()
                                temperature = float(temp_value)
                                
                                # Extraer humedad (columna 5: "Humi.")
                                humidity = None
                                try:
                                    hum_text = cells[5].get_text(strip=True)
                                    if '%' in hum_text:
                                        humidity = int(hum_text.replace('%', '').strip())
                                except:
                                    pass
                                
                                # Extraer viento (columna 9: "Vent (rafales)")
                                wind = None
                                try:
                                    wind_text = cells[9].get_text(strip=True)
                                    if 'km/h' in wind_text:
                                        wind_value = wind_text.split()[0]  # Tomar primer número
                                        wind = int(wind_value)
                                except:
                                    pass
                                
                                # Extraer presión (columna 10: "Pression")
                                pressure = None
                                try:
                                    pres_text = cells[10].get_text(strip=True)
                                    if 'hPa' in pres_text:
                                        pressure = float(pres_text.replace('hPa', '').strip())
                                except:
                                    pass
                                
                                # Convertir hora UTC a hora local
                                hora_local = self.convert_utc_to_local(hora_cell)
                                
                                data = {
                                    'temperature': temperature,
                                    'humidity': humidity,
                                    'wind_speed': wind,
                                    'pressure': pressure,
                                    'timestamp_utc': hora_cell,
                                    'timestamp_local': hora_local,
                                    'scraped_at': datetime.now().isoformat()
                                }
                                
                                all_data.append(data)
                                
                        except Exception as e:
                            continue
            
            # Retornar el PRIMER dato de la lista (más reciente en la tabla)
            if all_data:
                return all_data[0]
            
            return None
            
        except Exception as e:
            print(f"❌ Error scraping: {e}")
            return None
    
    def convert_utc_to_local(self, hora_utc_str):
        """Convierte hora UTC a hora local española (UTC+1)"""
        try:
            # Formato: "18h30" -> "19:30" (hora local)
            hora_utc_str = hora_utc_str.replace('h', ':')
            
            # Parsear la hora
            if ':' in hora_utc_str:
                parts = hora_utc_str.split(':')
                hora = int(parts[0])
                minuto = int(parts[1]) if len(parts) > 1 else 0
            else:
                hora = int(hora_utc_str)
                minuto = 0
            
            # Sumar 1 hora (España = UTC+1 en invierno, UTC+2 en verano)
            # Por simplicidad usamos UTC+1
            hora_local = (hora + 1) % 24
            
            return f"{hora_local:02d}:{minuto:02d}"
            
        except:
            return hora_utc_str
    
    def print_status(self, data):
        """Imprime el estado actual"""
        if data is None:
            now = datetime.now().strftime('%H:%M:%S')
            print(f"[{now}] Meteociel   | ❌ Sin datos disponibles")
            return
        
        now = datetime.now().strftime('%H:%M:%S')
        
        temp = data.get('temperature')
        temp_str = f"{temp:>5.1f}°C" if temp is not None else "  N/A"
        
        hum = data.get('humidity')
        hum_str = f"{hum:>3}%" if hum is not None else " N/A"
        
        wind = data.get('wind_speed')
        wind_str = f"{wind:>3}" if wind is not None else " N/A"
        
        pres = data.get('pressure')
        pres_str = f"{pres:>6.1f}" if pres is not None else "    N/A"
        
        timestamp_local = data.get('timestamp_local', 'N/A')
        timestamp_utc = data.get('timestamp_utc', 'N/A')
        
        print(f"[{now}] Meteociel   | 🌡️  {temp_str} | "
              f"💧 {hum_str} | "
              f"💨 {wind_str} km/h | "
              f"📊 {pres_str} hPa | "
              f"⏰ {timestamp_local} (UTC: {timestamp_utc})")
    
    def monitor(self, interval=60):
        """Monitorea la temperatura continuamente"""
        print(f"\n{'='*80}")
        print(f"MONITOREO METEOCIEL - AEROPUERTO MADRID-BARAJAS")
        print(f"{'='*80}")
        print(f"Fuente: Meteociel.fr (Web Scraping)")
        print(f"URL: {self.url}")
        print(f"Intervalo: {interval} segundos")
        print(f"NOTA: Hora en UTC, se convierte a hora local (UTC+1)")
        print(f"{'='*80}\n")
        
        try:
            while True:
                data = self.get_temperature()
                self.print_status(data)
                
                if data:
                    print(f"\n📋 Datos completos:")
                    print(f"   Temperatura: {data.get('temperature')}°C")
                    print(f"   Humedad: {data.get('humidity')}%")
                    print(f"   Viento: {data.get('wind_speed')} km/h")
                    print(f"   Presión: {data.get('pressure')} hPa")
                    print(f"   Hora UTC: {data.get('timestamp_utc')}")
                    print(f"   Hora Local: {data.get('timestamp_local')}")
                    print()
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print(f"\n\nScraper detenido.\n")
            sys.exit(0)


def main():
    """Función principal"""
    scraper = MeteocielScraper()
    
    print("🔍 Probando scraper de Meteociel...\n")
    
    # Obtener una lectura
    data = scraper.get_temperature()
    
    if data:
        print("✅ Scraper funcionando correctamente!")
        print(f"\n📊 Datos obtenidos:")
        print(f"   🌡️  Temperatura: {data.get('temperature')}°C")
        print(f"   💧 Humedad: {data.get('humidity')}%")
        print(f"   💨 Viento: {data.get('wind_speed')} km/h")
        print(f"   📊 Presión: {data.get('pressure')} hPa")
        print(f"   ⏰ Hora UTC: {data.get('timestamp_utc')}")
        print(f"   ⏰ Hora Local (España): {data.get('timestamp_local')}")
        print()
    else:
        print("❌ No se pudieron obtener datos")
        print("Verificando estructura de la página...\n")
        
        # Hacer una prueba para ver el HTML
        try:
            response = requests.get(scraper.url, headers=scraper.headers, timeout=10)
            response.encoding = 'ISO-8859-1'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            print("📄 Buscando tablas en la página...")
            tables = soup.find_all('table')
            print(f"   Encontradas {len(tables)} tablas")
            
            print("\n📄 Primeras filas de datos:")
            rows = soup.find_all('tr')[:10]
            for i, row in enumerate(rows):
                cells = row.find_all('td')
                if cells:
                    print(f"   Fila {i}: {[cell.get_text(strip=True)[:20] for cell in cells[:6]]}")
        except Exception as e:
            print(f"Error en debug: {e}")
    
    print("\n" + "="*80)
    print("💡 Para monitoreo continuo, descomentar la línea al final del script")
    print("="*80)
    
    # Para monitoreo continuo (descomenta la siguiente línea):
    # scraper.monitor(interval=60)


if __name__ == "__main__":
    main()

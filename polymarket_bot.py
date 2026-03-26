#!/usr/bin/env python3
"""
Bot de Trading para Polymarket - Monitoreando  Weather en Madrid Barajas
COMPARANDO 5 FUENTES:
  1. Weather.com API (ICAO LEMD)
  2. PWS - Estación Personal IMADRI133
  3. PWS - Estación Personal IMADRI265
  4. AEMET OpenData (Oficial Gobierno España)
  5. Meteociel (Web Scraping - Tiempo Real)
"""

import requests
import json
from datetime import datetime, timedelta
import time
import sys
from bs4 import BeautifulSoup
import matplotlib
matplotlib.use('Agg')  # Backend sin ventana
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from collections import defaultdict
import os

# Forzar stdout sin buffer para que el dashboard lo reciba en tiempo real
sys.stdout.reconfigure(line_buffering=True)

class PolymarketWeatherBot:
    def __init__(self):
        # API 1: Weather.com (ICAO)
        self.weather_api_key = "e1f10a1e78da46f5b10a1e78da96f525"
        self.weather_url = "https://api.weather.com/v3/wx/observations/current"
        self.weather_params = {
            "apiKey": self.weather_api_key,
            "icaoCode": "LEMD",  # Aeropuerto Madrid-Barajas OFICIAL
            "units": "m",
            "language": "es-ES",
            "format": "json"
        }
        
        # USAR ENDPOINT DE LA ESTACIÓN PERSONAL (PWS)
        self.api_key = "e1f10a1e78da46f5b10a1e78da96f525"
        self.url = "https://api.weather.com/v2/pws/observations/current"
        
        # Estación PWS 1
        self.params_pws1 = {
            "apiKey": self.api_key,
            "stationId": "IMADRI133",  # Estación personal 1 en Barajas
            "units": "m",              # 'm' para métrico (Celsius, km/h, etc.)
            "format": "json",
            "numericPrecision": "decimal"
        }
        
        # Estación PWS 2
        self.params_pws2 = {
            "apiKey": self.api_key,
            "stationId": "IMADRI265",  # Estación personal 2 en Barajas
            "units": "m",
            "format": "json",
            "numericPrecision": "decimal"
        }
        
        # API 2: AEMET OpenData (Oficial Gobierno España)
        self.aemet_api_key = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJqZXN1c21vcmFsYXJhbmRhMTBAZ21haWwuY29tIiwianRpIjoiOWQ2ZTZjNTItMDZkMy00NzRhLWFjMTMtMjBhZjMyNDAyMjQ0IiwiaXNzIjoiQUVNRVQiLCJpYXQiOjE3NzQzNzcxNTksInVzZXJJZCI6IjlkNmU2YzUyLTA2ZDMtNDc0YS1hYzEzLTIwYWYzMjQwMjI0NCIsInJvbGUiOiIifQ.Tx_DszUtdhBJ9tpcPxPUwLnBW99rOqLvifyyCm3sECQ"
        self.aemet_base_url = "https://opendata.aemet.es/opendata/api"
        self.aemet_station_id = "3129"  # Madrid-Barajas
        self.aemet_headers = {
            "api_key": self.aemet_api_key,
            "Accept": "application/json"
        }
        
        # API 3: Meteociel (Web Scraping)
        self.meteociel_url = "https://www.meteociel.fr/temps-reel/obs_villes.php?code2=8221"
        self.meteociel_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Estado
        self.update_count = 0
        
        # Último dato de cada fuente (NO acumulativo)
        self.latest_data = {
            'weather_com': {'time': None, 'temp': None},
            'pws1': {'time': None, 'temp': None},
            'pws2': {'time': None, 'temp': None},
            'aemet': {'time': None, 'temp': None},
            'meteociel': {'time': None, 'temp': None}
        }
        
        # Directorio para guardar el gráfico
        self.output_dir = os.path.dirname(os.path.abspath(__file__))
        self.plot_path = os.path.join(self.output_dir, "temperature_plot.png")
        
    def get_weather_com_temperature(self):
        """Obtiene la temperatura de Weather.com API"""
        try:
            response = requests.get(self.weather_url, params=self.weather_params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            return {
                "temperature": data.get("temperature"),
                
                "humidity": data.get("relativeHumidity"),
                "pressure": data.get("pressureAltimeter"),
                "wind_speed": data.get("windSpeed"),
                "timestamp": data.get("validTimeLocal"),
            }
        except Exception as e:
            return None
    
    def get_pws_temperature(self, params):
        """Obtiene la temperatura de una Estación Personal (PWS)"""
        try:
            response = requests.get(self.url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            # La estructura de la respuesta de PWS es diferente
            if 'observations' in data and len(data['observations']) > 0:
                obs = data['observations'][0]
                metric = obs.get('metric', {})
                
                return {
                    "temperature": metric.get("temp"),
                  
                    "humidity": obs.get("humidity"),
                    "pressure": metric.get("pressure"),
                    "wind_speed": metric.get("windSpeed"),
                    "timestamp": obs.get("obsTimeLocal"),
                    "station_id": obs.get("stationID"),
                }
            return None
        except Exception as e:
            return None
    
    def get_aemet_temperature(self):
        """Obtiene la temperatura de AEMET OpenData (Oficial)"""
        try:
            # Paso 1: Obtener URL de datos
            url = f"{self.aemet_base_url}/observacion/convencional/datos/estacion/{self.aemet_station_id}"
            response = requests.get(url, headers=self.aemet_headers, timeout=10)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            if 'datos' not in data:
                return None
            
            # Paso 2: Obtener los datos reales
            datos_url = data['datos']
            datos_response = requests.get(datos_url, timeout=10)
            
            if datos_response.status_code != 200:
                return None
            
            observaciones = datos_response.json()
            
            # Obtener la observación más reciente
            if len(observaciones) > 0:
                obs = observaciones[-1]
                
                return {
                    "temperature": obs.get("ta"),
                   
                    "humidity": obs.get("hr"),
                    "pressure": obs.get("pres"),
                    "wind_speed": obs.get("vv"),
                    "timestamp": obs.get("fint"),
                }
            return None
                
        except Exception as e:
            return None
    
    def get_meteociel_temperature(self):
        """Obtiene temperatura de Meteociel (Web Scraping)"""
        try:
            response = requests.get(self.meteociel_url, headers=self.meteociel_headers, timeout=10)
            response.encoding = 'ISO-8859-1'
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            rows = soup.find_all('tr')
            
            all_data = []
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 10:  # Asegurar que tiene suficientes columnas
                    hora_cell = cells[0].get_text(strip=True)
                    if 'h' in hora_cell and len(hora_cell) <= 6:
                        try:
                            # Columna 4: Température
                            temp_text = cells[4].get_text(strip=True)
                            if '°C' in temp_text:
                                temp = float(temp_text.replace('°C', '').replace('°', '').strip())
                                
                                # Columna 5: Humedad
                                humidity = None
                                try:
                                    hum_text = cells[5].get_text(strip=True)
                                    if '%' in hum_text:
                                        humidity = int(hum_text.replace('%', '').strip())
                                except:
                                    pass
                                
                                # Columna 9: Viento
                                wind = None
                                try:
                                    wind_text = cells[9].get_text(strip=True)
                                    if 'km/h' in wind_text:
                                        wind = int(wind_text.split()[0])
                                except:
                                    pass
                                
                                # Convertir hora UTC a local (UTC+1)
                                hora_str = hora_cell.replace('h', ':')
                                if len(hora_str.split(':')[1]) == 1:
                                    hora_str = hora_str.replace(':', ':0')
                                hora_utc = datetime.strptime(f"{datetime.now().date()} {hora_str}", "%Y-%m-%d %H:%M")
                                hora_local = hora_utc + timedelta(hours=1)
                                
                                all_data.append({
                                    "temperature": temp,
                                    
                                    "humidity": humidity,
                                    "wind_speed": wind,
                                    "timestamp": hora_local.strftime("%H:%M"),
                                })
                        except:
                            continue
            
            # Retornar el primer dato (más reciente)
            return all_data[0] if all_data else None
        except Exception as e:
            return None
    
    def update_latest_data(self, source, temp, timestamp=None):
        """Actualiza el último dato de una fuente (NO acumulativo)"""
        if temp is None:
            return
        
        if timestamp is None:
            timestamp = datetime.now()
        elif isinstance(timestamp, str):
            # Convertir string "HH:MM" a datetime de hoy
            try:
                hour, minute = map(int, timestamp.split(':'))
                timestamp = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
            except:
                timestamp = datetime.now()
        
        self.latest_data[source]['time'] = timestamp
        self.latest_data[source]['temp'] = temp
    
    def generate_plot(self):
        """Genera el gráfico de temperaturas (último punto de cada fuente)"""
        try:
            plt.figure(figsize=(10, 6))
            
            # Colores y símbolos para cada fuente
            colors = {
                'weather_com': '#FF6B6B',
                'pws1': '#4ECDC4',
                'pws2': '#45B7D1',
                'aemet': '#96CEB4',
                'meteociel': '#9B59B6'
            }
            
            labels = {
                'weather_com': 'Weather.com',
                'pws1': 'IMADRI133',
                'pws2': 'IMADRI265',
                'aemet': 'AEMET',
                'meteociel': 'Meteociel'
            }
            
            markers = {
                'weather_com': 'o',
                'pws1': 's',
                'pws2': '^',
                'aemet': 'D',
                'meteociel': 'v'
            }
            
            # Plotear cada fuente (solo último punto)
            for source, data in self.latest_data.items():
                if data['time'] is not None and data['temp'] is not None:
                    plt.scatter(data['time'], data['temp'], 
                              marker=markers[source], s=200, 
                              color=colors[source], label=labels[source], 
                              alpha=0.8, edgecolors='black', linewidth=1.5, zorder=5)
                    
                    # Añadir etiqueta con valor
                    plt.annotate(f"{data['temp']:.1f}°C", 
                               (data['time'], data['temp']),
                               textcoords="offset points", 
                               xytext=(0, 10), 
                               ha='center', 
                               fontsize=9,
                               fontweight='bold',
                               bbox=dict(boxstyle='round,pad=0.3', 
                                       facecolor=colors[source], 
                                       alpha=0.3))
            
            plt.xlabel('Hora de Lectura (UTC+1)', fontsize=11)
            plt.ylabel('Temperatura (°C)', fontsize=11)
            plt.title('Últimas Lecturas de Temperatura - Madrid Barajas\n5 Fuentes en Tiempo Real', 
                     fontsize=13, fontweight='bold')
            plt.legend(loc='best', fontsize=10, framealpha=0.9)
            plt.grid(True, alpha=0.3, linestyle='--')
            
            # Formato del eje X (tiempo)
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            plt.gca().xaxis.set_major_locator(mdates.MinuteLocator(interval=10))
            plt.gcf().autofmt_xdate()  # Rotar etiquetas
            
            # Añadir rango al eje Y con margen
            temps = [d['temp'] for d in self.latest_data.values() if d['temp'] is not None]
            if temps:
                min_temp, max_temp = min(temps), max(temps)
                margin = (max_temp - min_temp) * 0.15 or 1
                plt.ylim(min_temp - margin, max_temp + margin)
            
            plt.tight_layout()
            plt.savefig(self.plot_path, dpi=100, bbox_inches='tight')
            plt.close()
            
            print(f"📊 Gráfico actualizado: {self.plot_path}", flush=True)
        except Exception as e:
            print(f"❌ Error generando gráfico: {e}", flush=True)
    
    
    
    def print_status(self, weather_data, pws1_data, pws2_data, aemet_data, meteociel_data):
        """Imprime el estado actual en tiempo real de las 5 APIs"""
        now = datetime.now().strftime('%H:%M:%S')
        
        # Línea 1: Weather.com
        if weather_data:
            temp = weather_data.get('temperature')
            hum = weather_data.get('humidity')
            wind = weather_data.get('wind_speed')
            
            temp_str = f"{temp:>6.2f}°C" if temp is not None else "   N/A"
            hum_str = f"{hum:>3}%" if hum is not None else " N/A"
            wind_str = f"{wind:>6.2f}" if wind is not None else "   N/A"
            
            print(f"[{now}] Weather.com  | {temp_str} | 💧 {hum_str} | 💨 {wind_str} km/h", flush=True)
        else:
            print(f"[{now}] Weather.com  | ❌ Sin datos", flush=True)
        
        # Línea 2: PWS 1 (IMADRI133)
        if pws1_data:
            temp = pws1_data.get('temperature')
            
            hum = pws1_data.get('humidity')
            wind = pws1_data.get('wind_speed')
            station = pws1_data.get('station_id', 'N/A')
            
            temp_str = f"{temp:>6.2f}°C" if temp is not None else "   N/A"
           
            hum_str = f"{hum:>3}%" if hum is not None else " N/A"
            wind_str = f"{wind:>6.2f}" if wind is not None else "   N/A"

            print(f"[{now}] {station} | {temp_str} | 💧 {hum_str} | 💨 {wind_str} km/h", flush=True)
        else:
            print(f"[{now}] IMADRI133 | ❌ Sin datos", flush=True)
        
        # Línea 3: PWS 2 (IMADRI265)
        if pws2_data:
            temp = pws2_data.get('temperature')
            
            hum = pws2_data.get('humidity')
            wind = pws2_data.get('wind_speed')
            station = pws2_data.get('station_id', 'N/A')
            
            temp_str = f"{temp:>6.2f}°C" if temp is not None else "   N/A"
           
            hum_str = f"{hum:>3}%" if hum is not None else " N/A"
            wind_str = f"{wind:>6.2f}" if wind is not None else "   N/A"

            print(f"[{now}] {station} | {temp_str} | 💧 {hum_str} | 💨 {wind_str} km/h", flush=True)
        else:
            print(f"[{now}] IMADRI265 | ❌ Sin datos", flush=True)
        
        # Línea 4: AEMET
        if aemet_data:
            temp = aemet_data.get('temperature')
           
            hum = aemet_data.get('humidity')
            wind = aemet_data.get('wind_speed')
            
            temp_str = f"{temp:>6.2f}°C" if temp is not None else "   N/A"
            
            hum_str = f"{hum:>3.0f}%" if hum is not None else " N/A"
            wind_str = f"{wind:>6.2f}" if wind is not None else "   N/A"
            
            print(f"[{now}] AEMET       | {temp_str} | 💧 {hum_str} | 💨 {wind_str} km/h", flush=True)
        else:
            print(f"[{now}] AEMET       | ❌ Sin datos", flush=True)
        
        # Línea 5: Meteociel
        if meteociel_data:
            temp = meteociel_data.get('temperature')
            hum = meteociel_data.get('humidity')
            wind = meteociel_data.get('wind_speed')
            timestamp = meteociel_data.get('timestamp', '')
            
            temp_str = f"{temp:>6.2f}°C" if temp is not None else "   N/A"
            hum_str = f"{hum:>3}%" if hum is not None else " N/A"
            wind_str = f"{wind:>3}" if wind is not None else " N/A"
            
            print(f"[ {timestamp:>5}] Meteociel   | {temp_str} | 💧 {hum_str} | 💨 {wind_str} km/h", flush=True)
        else:
            print(f"[{now}] Meteociel   | ❌ Sin datos", flush=True)
        
        print(flush=True)  # Línea en blanco para separar
    
    def monitor(self, interval=20):
        print(f"\n{'='*80}", flush=True)
        print(f"MONITOREO 5 FUENTES - AEROPUERTO MADRID-BARAJAS", flush=True)
        print(f"{'='*80}", flush=True)
        print(f"API 1: Weather.com (ICAO LEMD)", flush=True)
        print(f"API 2: PWS - Estación Personal IMADRI133", flush=True)
        print(f"API 3: PWS - Estación Personal IMADRI265", flush=True)
        print(f"API 4: AEMET OpenData (Oficial Gobierno España - Estación 3129)", flush=True)
        print(f"API 5: Meteociel (Web Scraping - Tiempo Real)", flush=True)
        print(f"Intervalo: {interval} segundos\n", flush=True)
        print(f"Gráfico: {self.plot_path}", flush=True)
        print(f"{'='*80}\n", flush=True)
        
        try:
            while True:
                self.update_count += 1
                
                weather_data   = self.get_weather_com_temperature()
                pws1_data      = self.get_pws_temperature(self.params_pws1)
                pws2_data      = self.get_pws_temperature(self.params_pws2)
                aemet_data     = self.get_aemet_temperature()
                meteociel_data = self.get_meteociel_temperature()
                
                # Actualizar últimos datos
                if weather_data:
                    self.update_latest_data('weather_com', weather_data.get('temperature'))
                if pws1_data:
                    self.update_latest_data('pws1', pws1_data.get('temperature'))
                if pws2_data:
                    self.update_latest_data('pws2', pws2_data.get('temperature'))
                if aemet_data:
                    self.update_latest_data('aemet', aemet_data.get('temperature'))
                if meteociel_data:
                    # Usar el timestamp de Meteociel si está disponible
                    self.update_latest_data('meteociel', 
                                          meteociel_data.get('temperature'),
                                          meteociel_data.get('timestamp'))
                
                # Generar gráfico cada actualización
                self.generate_plot()
                
                self.print_status(weather_data, pws1_data, pws2_data, aemet_data, meteociel_data)
                print(f"\n{'='*80}", flush=True)
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print(f"\n\nBot detenido.\n", flush=True)
            # Generar gráfico final
            self.generate_plot()
            sys.exit(0)
        


def main():
    """Función principal"""
    bot = PolymarketWeatherBot()
    
    # Para una sola lectura:
    # bot.get_single_reading()
    
    # Para monitoreo continuo (RECOMENDADO):
    bot.monitor(interval=20)  # Chequea cada 20 segundos

if __name__ == "__main__":
    main()

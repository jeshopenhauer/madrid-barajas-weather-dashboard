#!/usr/bin/env python3
"""
Bot de Trading para Polymarket - Monitoreando Weather en Madrid Barajas
COMPARANDO 9 FUENTES:
  1. Weather.com API (ICAO LEMD)
  2. PWS 1 - Estación Personal (IMADRI133)
  3. PWS 2 - Estación Personal (IMADRI265)
  4. PWS 3 - Estación Personal (IMADRI56)
  5. PWS 4 - Estación Personal (IMADRI883 - Timón)
  6. PWS 5 - Estación Personal (IMADRI364 - Alameda de Osuna)
  7. PWS 6 - Estación Personal (IMADRI882 - Alameda de Osuna)
  8. AEMET OpenData (Oficial Gobierno España)
  9. Meteociel (Web Scraping - Tiempo Real)
"""

import requests
import json
from datetime import datetime, timedelta
import time
import sys
from bs4 import BeautifulSoup

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
        
        # PWS 1: IMADRI133
        self.api_key = "e1f10a1e78da46f5b10a1e78da96f525"
        self.url = "https://api.weather.com/v2/pws/observations/current"
        self.params = {
            "apiKey": self.api_key,
            "stationId": "IMADRI133",  # Estación personal en Barajas
            "units": "m",              # 'm' para métrico (Celsius, km/h, etc.)
            "format": "json",
            "numericPrecision": "decimal"
        }
        
        # PWS 2: IMADRI265
        self.pws2_params = {
            "apiKey": self.api_key,
            "stationId": "IMADRI265",  # Segunda estación personal en Barajas
            "units": "m",
            "format": "json",
            "numericPrecision": "decimal"
        }
        
        # PWS 3: IMADRI56
        self.pws3_params = {
            "apiKey": self.api_key,
            "stationId": "IMADRI56",  # Tercera estación personal en Madrid
            "units": "m",
            "format": "json",
            "numericPrecision": "decimal"
        }
        
        # PWS 4: IMADRI883 (Timón)
        self.pws4_params = {
            "apiKey": self.api_key,
            "stationId": "IMADRI883",  # Timón
            "units": "m",
            "format": "json",
            "numericPrecision": "decimal"
        }
        
        # PWS 5: IMADRI364 (Alameda de Osuna)
        self.pws5_params = {
            "apiKey": self.api_key,
            "stationId": "IMADRI364",  # Alameda de Osuna
            "units": "m",
            "format": "json",
            "numericPrecision": "decimal"
        }
        
        # PWS 6: IMADRI882 (Alameda de Osuna)
        self.pws6_params = {
            "apiKey": self.api_key,
            "stationId": "IMADRI882",  # Alameda de Osuna
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
    
    def get_pws_temperature(self):
        """Obtiene la temperatura de la Estación Personal (PWS)"""
        try:
            response = requests.get(self.url, params=self.params, timeout=5)
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
    
    def get_pws2_temperature(self):
        """Obtiene la temperatura de la Segunda Estación Personal (PWS2 - IMADRID265)"""
        try:
            response = requests.get(self.url, params=self.pws2_params, timeout=5)
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
    
    def get_pws3_temperature(self):
        """Obtiene la temperatura de la Tercera Estación Personal (PWS3 - IMADRI56)"""
        try:
            response = requests.get(self.url, params=self.pws3_params, timeout=5)
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
    
    def get_pws4_temperature(self):
        """Obtiene la temperatura de PWS4 - IMADRI883 (Timón)"""
        try:
            response = requests.get(self.url, params=self.pws4_params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
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
    
    def get_pws5_temperature(self):
        """Obtiene la temperatura de PWS5 - IMADRI364 (Alameda de Osuna)"""
        try:
            response = requests.get(self.url, params=self.pws5_params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
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
    
    def get_pws6_temperature(self):
        """Obtiene la temperatura de PWS6 - IMADRI882 (Alameda de Osuna)"""
        try:
            response = requests.get(self.url, params=self.pws6_params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
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
    
    
    
    def print_status(self, weather_data, pws_data, pws2_data, pws3_data, pws4_data, pws5_data, pws6_data, aemet_data, meteociel_data):
        """Imprime el estado actual en tiempo real de las 9 APIs"""
        now = datetime.now().strftime('%H:%M:%S')
        
        # Línea 1: Weather.com
        if weather_data:
            temp = weather_data.get('temperature')
            hum = weather_data.get('humidity')
            wind = weather_data.get('wind_speed')
            print(f"[{now}] Weather.com  |   {temp:>3}°C | 💧 {hum:>3}% | 💨 {wind:>3} km/h", flush=True)
        else:
            print(f"[{now}] Weather.com  | ❌ Sin datos", flush=True)
        
        # Línea 2: PWS 1 (IMADRI133)
        if pws_data:
            temp = pws_data.get('temperature')
         
            hum = pws_data.get('humidity')
            wind = pws_data.get('wind_speed')
            station = pws_data.get('station_id', 'N/A')
            
            temp_str = f"{temp:>5.1f}°C" if temp is not None else "  N/A"
            hum_str = f"{hum:>3}%" if hum is not None else " N/A"
            wind_str = f"{wind:>5.1f}" if wind is not None else "  N/A"
            
            print(f"[{now}]  ({station}) |   {temp_str} | 💧 {hum_str} | 💨 {wind_str} km/h", flush=True)
        else:
            print(f"[{now}]  (IMADRI133)| ❌ Sin datos", flush=True)
        
        # Línea 3: PWS 2 (IMADRID265)
        if pws2_data:
            temp = pws2_data.get('temperature')
          
            hum = pws2_data.get('humidity')
            wind = pws2_data.get('wind_speed')
            station = pws2_data.get('station_id', 'N/A')
            
            temp_str = f"{temp:>5.1f}°C" if temp is not None else "  N/A"
            hum_str = f"{hum:>3}%" if hum is not None else " N/A"
            wind_str = f"{wind:>5.1f}" if wind is not None else "  N/A"
            
            print(f"[{now}]  ({station}) |   {temp_str} | 💧 {hum_str} | 💨 {wind_str} km/h", flush=True)
        else:
            print(f"[{now}]  (IMADRI265)| ❌ Sin datos", flush=True)
        
        # Línea 4: PWS 3 (IMADRI56)
        if pws3_data:
            temp = pws3_data.get('temperature')
            
            hum = pws3_data.get('humidity')
            wind = pws3_data.get('wind_speed')
            station = pws3_data.get('station_id', 'N/A')
            
            temp_str = f"{temp:>5.1f}°C" if temp is not None else "  N/A"
            hum_str = f"{hum:>3}%" if hum is not None else " N/A"
            wind_str = f"{wind:>5.1f}" if wind is not None else "  N/A"
            
            print(f"[{now}]  ({station})  |   {temp_str}  | 💧 {hum_str} | 💨 {wind_str} km/h", flush=True)
        else:
            print(f"[{now}]  (IMADRI56) | ❌ Sin datos", flush=True)
        
        # Línea 5: PWS 4 (IMADRI883 - Timón)
        if pws4_data:
            temp = pws4_data.get('temperature')
            hum = pws4_data.get('humidity')
            wind = pws4_data.get('wind_speed')
            station = pws4_data.get('station_id', 'N/A')
            
            temp_str = f"{temp:>5.1f}°C" if temp is not None else "  N/A"
            hum_str = f"{hum:>3}%" if hum is not None else " N/A"
            wind_str = f"{wind:>5.1f}" if wind is not None else "  N/A"
            
            print(f"[{now}]  ({station}) |   {temp_str} | 💧 {hum_str} | 💨 {wind_str} km/h", flush=True)
        else:
            print(f"[{now}]  (IMADRI883)| ❌ Sin datos", flush=True)
        
        # Línea 6: PWS 5 (IMADRI364 - Alameda de Osuna)
        if pws5_data:
            temp = pws5_data.get('temperature')
            hum = pws5_data.get('humidity')
            wind = pws5_data.get('wind_speed')
            station = pws5_data.get('station_id', 'N/A')
            
            temp_str = f"{temp:>5.1f}°C" if temp is not None else "  N/A"
            hum_str = f"{hum:>3}%" if hum is not None else " N/A"
            wind_str = f"{wind:>5.1f}" if wind is not None else "  N/A"
            
            print(f"[{now}]  ({station}) |   {temp_str} | 💧 {hum_str} | 💨 {wind_str} km/h", flush=True)
        else:
            print(f"[{now}]  (IMADRI364)| ❌ Sin datos", flush=True)
        
        # Línea 7: PWS 6 (IMADRI882 - Alameda de Osuna)
        if pws6_data:
            temp = pws6_data.get('temperature')
            hum = pws6_data.get('humidity')
            wind = pws6_data.get('wind_speed')
            station = pws6_data.get('station_id', 'N/A')
            
            temp_str = f"{temp:>5.1f}°C" if temp is not None else "  N/A"
            hum_str = f"{hum:>3}%" if hum is not None else " N/A"
            wind_str = f"{wind:>5.1f}" if wind is not None else "  N/A"
            
            print(f"[{now}]  ({station}) |   {temp_str} | 💧 {hum_str} | 💨 {wind_str} km/h", flush=True)
        else:
            print(f"[{now}]  (IMADRI882)| ❌ Sin datos", flush=True)
        
        # Línea 8: AEMET
        if aemet_data:
            temp = aemet_data.get('temperature')
            
            hum = aemet_data.get('humidity')
            wind = aemet_data.get('wind_speed')
            
            temp_str = f"{temp:>5.1f}°C" if temp is not None else "  N/A"
            hum_str = f"{hum:>3.0f}%" if hum is not None else " N/A"
            wind_str = f"{wind:>5.1f}" if wind is not None else "  N/A"
            
            print(f"[{now}] AEMET        |   {temp_str} | 💧 {hum_str} | 💨 {wind_str} km/h", flush=True)
        else:
            print(f"[{now}] AEMET        | ❌ Sin datos", flush=True)
        
        # Línea 9: Meteociel
        if meteociel_data:
            temp = meteociel_data.get('temperature')
            hum = meteociel_data.get('humidity')
            wind = meteociel_data.get('wind_speed')
            timestamp = meteociel_data.get('timestamp', '')
            
            temp_str = f"{temp:>5.1f}°C" if temp is not None else "  N/A"
            hum_str = f"{hum:>3}%" if hum is not None else " N/A"
            wind_str = f"{wind:>3}" if wind is not None else " N/A"
            
            print(f"[{now}] Meteociel    |   {temp_str} | Hora: {timestamp:>5} | 💧 {hum_str} ", flush=True)
        else:
            print(f"[{now}] Meteociel    | ❌ Sin datos", flush=True)
        
        print(flush=True)  # Línea en blanco para separar
    
    def monitor(self, interval=20):
        print(f"\n{'='*80}", flush=True)
        print(f"MONITOREO 9 FUENTES - AEROPUERTO MADRID-BARAJAS", flush=True)
        print(f"{'='*80}", flush=True)
        print(f"API 1: Weather.com (ICAO LEMD)", flush=True)
        print(f"API 2: PWS 1 - Estación Personal (IMADRI133)", flush=True)
        print(f"API 3: PWS 2 - Estación Personal (IMADRI265)", flush=True)
        print(f"API 4: PWS 3 - Estación Personal (IMADRI56)", flush=True)
        print(f"API 5: PWS 4 - Estación Personal (IMADRI883 - Timón)", flush=True)
        print(f"API 6: PWS 5 - Estación Personal (IMADRI364 - Alameda de Osuna)", flush=True)
        print(f"API 7: PWS 6 - Estación Personal (IMADRI882 - Alameda de Osuna)", flush=True)
        print(f"API 8: AEMET OpenData (Oficial Gobierno España - Estación 3129)", flush=True)
        print(f"API 9: Meteociel (Web Scraping - Tiempo Real)", flush=True)
        print(f"Intervalo: {interval} segundos\n", flush=True)
        print(f"{'='*80}\n", flush=True)
        
        try:
            while True:
                self.update_count += 1
                
                weather_data   = self.get_weather_com_temperature()
                pws_data       = self.get_pws_temperature()
                pws2_data      = self.get_pws2_temperature()
                pws3_data      = self.get_pws3_temperature()
                pws4_data      = self.get_pws4_temperature()
                pws5_data      = self.get_pws5_temperature()
                pws6_data      = self.get_pws6_temperature()
                aemet_data     = self.get_aemet_temperature()
                meteociel_data = self.get_meteociel_temperature()
                
                self.print_status(weather_data, pws_data, pws2_data, pws3_data, pws4_data, pws5_data, pws6_data, aemet_data, meteociel_data)
                print(f"\n{'='*80}", flush=True)
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print(f"\n\nBot detenido.\n", flush=True)
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

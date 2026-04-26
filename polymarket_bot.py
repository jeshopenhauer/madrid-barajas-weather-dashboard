#!/usr/bin/env python3
"""
Bot de Trading para Polymarket - VERSIÓN OPTIMIZADA
"""

import requests
import json
import re
from datetime import datetime, timedelta
import time
import sys
from bs4 import BeautifulSoup
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import os

sys.stdout.reconfigure(line_buffering=True)

class PolymarketWeatherBot:
    def __init__(self):
        # ✨ OPTIMIZACIÓN: Sesión HTTP reutilizable
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        self.api_key = "e1f10a1e78da46f5b10a1e78da96f525"
        
        # APIs configuradas
        self.weather_url = "https://api.weather.com/v3/wx/observations/current"
        self.weather_params = {
            "apiKey": self.api_key,
            "icaoCode": "LEMD",
            "units": "m",
            "language": "es-ES",
            "format": "json",
            
        }
        
        self.weather_v1_url = "https://api.weather.com/v1/location/LEMD:9:ES/observations.json"
        self.weather_v1_params = {
            "apiKey": self.api_key,
            "units": "m",
            "language": "es-ES",
            
        }
        
        self.weather_hist_url = "https://api.weather.com/v1/location/LEMD:9:ES/observations/historical.json"
        self.weather_hist_params = {
            "apiKey": self.api_key,
            "units": "m"
        }
        
        self.pws_url = "https://api.weather.com/v2/pws/observations/current"
        self.params_pws1 = {
            "apiKey": self.api_key,
            "stationId": "IMADRI133",
            "units": "m",
            "format": "json",
            "numericPrecision": "decimal"
        }
        self.params_pws2 = {
            "apiKey": self.api_key,
            "stationId": "IMADRI265",
            "units": "m",
            "format": "json",
            "numericPrecision": "decimal"
        }
        
        self.meteociel_url = "https://www.meteociel.fr/temps-reel/obs_villes.php?code2=8221"

        self.avwx_token = "MF_MQHY-xWLmV7Hwyccc_jh7H9q10cvRAFJHSLhRyvQ"
        
        self.graphs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "polymarket_graphs")
        os.makedirs(self.graphs_dir, exist_ok=True)
        
        self.today_str = datetime.now().strftime("%Y-%m-%d")
        self.history_plot_path = os.path.join(self.graphs_dir, f"polymarket_temperature_history_{self.today_str}.png")
        self.history_data_path = os.path.join(self.graphs_dir, f"polymarket_history_data_{self.today_str}.json")
        
        self.history_data = {
            'weather_com': [],
            'weather_v1': [],
            'pws1': [],
            'pws2': [],
            'meteociel': []
        }
        
    def get_weather_com_temperature(self):
        try:
            r = self.session.get(self.weather_url, params=self.weather_params, timeout=3)  # ⚡ 3 segundos
            r.raise_for_status()
            d = r.json()
            return {"temperature": d.get("temperature"), "timestamp": d.get("validTimeLocal")}
        except:
            return None
    
    def get_weather_v1_temperature(self):
        try:
            r = self.session.get(self.weather_v1_url, params=self.weather_v1_params, timeout=3)
            r.raise_for_status()
            d = r.json()
            if 'observation' in d:
                obs = d['observation']
                return {"temperature": obs.get("temp"), "timestamp": obs.get("obs_time_local") or obs.get("valid_time_gmt")}
            return None
        except:
            return None
    
    def get_pws_temperature(self, params):
        try:
            r = self.session.get(self.pws_url, params=params, timeout=3)
            r.raise_for_status()
            d = r.json()
            if 'observations' in d and d['observations']:
                obs = d['observations'][0]
                return {
                    "temperature": obs.get('metric', {}).get("temp"),
                    "timestamp": obs.get("obsTimeLocal"),
                    "station_id": obs.get("stationID")
                }
            return None
        except:
            return None
    
    def get_weather_historical_last(self):
        try:
            today = datetime.now().strftime("%Y%m%d")
            params = self.weather_hist_params.copy()
            params['startDate'] = today
            params['endDate'] = today
            r = self.session.get(self.weather_hist_url, params=params, timeout=3)
            r.raise_for_status()
            d = r.json()
            if 'observations' in d and d['observations']:
                last_obs = d['observations'][-1]  # Último registro
                return {
                    "temperature": last_obs.get('temp'),
                    "timestamp": datetime.fromtimestamp(last_obs.get('valid_time_gmt')),
                    "count": len(d['observations'])
                }
            return None
        except:
            return None
    
    @staticmethod
    def _metar_time(raw):
        if raw:
            m = re.search(r'\b(\d{6}Z)\b', raw)
            if m:
                return m.group(1)
        return "N/A"

    def get_temp_aviationweather(self):
        try:
            # ✨ HFT: Cache buster con milisegundos para forzar datos frescos
            cache_buster = int(time.time() * 1000)
            params = {
                "ids": "LEMD",
                "format": "raw", # Formato texto plano (mucho más rápido que JSON)
                "_": cache_buster
            }
            
            # ✨ HFT: Timeout agresivo de 1.5s
            r = self.session.get(
                "https://aviationweather.gov/api/data/metar",
                params=params,
                timeout=1.5
            )
            r.raise_for_status()
            metar_raw = r.text.strip()
            
            if metar_raw and "LEMD" in metar_raw:
                # Extraer temperatura con Regex (busca el bloque tipo 25/08 o M02/M05)
                temp_match = re.search(r'\b(M?\d{2})/(M?\d{2})?\b', metar_raw)
                temp = None
                if temp_match:
                    temp_str = temp_match.group(1)
                    # Convertir 'M' a negativo si hace bajo cero
                    temp = float(temp_str.replace('M', '-'))
                
                return {
                    "temperature": temp, 
                    "metar_time": self._metar_time(metar_raw),
                    "raw": metar_raw # Pasamos el raw para imprimirlo en la terminal
                }
        except:
            pass # Si falla o tarda más de 1.5s, ignorar para no bloquear el bot
        return None

    def get_temp_avwx(self):
        try:
            r = self.session.get(
                "https://avwx.rest/api/metar/LEMD",
                headers={"Authorization": self.avwx_token},
                timeout=5
            )
            r.raise_for_status()
            data = r.json()
            temp_obj = data.get("temperature")
            temp = temp_obj.get("value") if isinstance(temp_obj, dict) else temp_obj
            return {"temperature": temp, "metar_time": self._metar_time(data.get("raw", ""))}
        except:
            pass
        return None

    def get_meteociel_temperature(self):
        try:
            r = self.session.get(self.meteociel_url, timeout=5)
            r.encoding = 'ISO-8859-1'
            if r.status_code != 200:
                return None
            
            soup = BeautifulSoup(r.text, 'html.parser')
            for row in soup.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) >= 10:
                    hora_cell = cells[0].get_text(strip=True)
                    if 'h' in hora_cell and len(hora_cell) <= 6:
                        try:
                            temp_text = cells[4].get_text(strip=True)
                            if '°C' in temp_text:
                                temp = float(temp_text.replace('°C', '').replace('°', '').strip())
                                hora_str = hora_cell.replace('h', ':')
                                if len(hora_str.split(':')[1]) == 1:
                                    hora_str = hora_str.replace(':', ':0')
                                hora_utc = datetime.strptime(f"{datetime.now().date()} {hora_str}", "%Y-%m-%d %H:%M")
                                hora_local = hora_utc + timedelta(hours=2)
                                return {"temperature": temp, "timestamp": hora_local}
                        except:
                            continue
            return None
        except:
            return None
    
    def add_to_history(self, source, temp, timestamp=None):
        if temp is None:
            return
        if timestamp is None:
            timestamp = datetime.now()
        elif isinstance(timestamp, str):
            try:
                hour, minute = map(int, timestamp.split(':'))
                timestamp = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
            except:
                timestamp = datetime.now()
        # Si timestamp ya es un datetime, usarlo directamente
        self.history_data[source].append({'time': timestamp, 'temp': temp})
    
    def generate_history_plot(self):
        current_date_str = datetime.now().strftime("%Y-%m-%d")
        if current_date_str != self.today_str:
            self.today_str = current_date_str
            self.history_plot_path = os.path.join(self.graphs_dir, f"polymarket_temperature_history_{self.today_str}.png")
            self.history_data_path = os.path.join(self.graphs_dir, f"polymarket_history_data_{self.today_str}.json")
        
        try:
            # JSON optimizado
            json_data = {src: [{'time': d['time'].strftime('%Y-%m-%d %H:%M:%S'), 'temp': d['temp']} 
                               for d in data_list] for src, data_list in self.history_data.items()}
            with open(self.history_data_path, 'w') as f:
                json.dump(json_data, f, indent=4)
            
            fig, ax = plt.subplots(figsize=(10, 5.2), dpi=100)
            
            colors = {'weather_com': "#FF0000", 'weather_v1': "#FF00CC", 'pws1': "#09FF00", 'pws2': "#0044FF", 'meteociel': "#B700FF"}
            labels = {'weather_com': 'Weather.com v3 (ICAO LEMD)', 'weather_v1': 'Weather.com v1 (LEMD:9:ES)', 'pws1': 'IMADRI133 (PWS)', 'pws2': 'IMADRI265 (PWS)', 'meteociel': 'Meteociel'}
            markers = {'weather_com': 'o', 'weather_v1': 's', 'pws1': 'v', 'pws2': 'v', 'meteociel': 'v'}
            
            for source in ['weather_com', 'weather_v1', 'pws1', 'pws2', 'meteociel']:
                data = self.history_data[source]
                if data:
                    timestamps = [d['time'] for d in data]
                    temps = [d['temp'] for d in data]
                    label_info = f"{labels[source]} | {timestamps[-1].strftime('%H:%M:%S')} - {temps[-1]:.2f}°C"
                    ax.plot(timestamps, temps, marker=markers[source], linestyle='-', linewidth=1.6, markersize=3.5,
                           color=colors[source], label=label_info, alpha=0.85, zorder=3)
            
            ax.set_xlabel('Tiempo (UTC+1)', fontsize=10, fontweight='bold')
            ax.set_ylabel('Temperatura (°C)', fontsize=10, fontweight='bold')
            ax.set_title('Tracking 5 Fuentes - Historial Completo', fontsize=11, fontweight='bold', pad=8)
            ax.legend(loc='upper left', fontsize=8, framealpha=0.92, edgecolor='gray', frameon=True)
            ax.grid(True, alpha=0.2, linestyle='--', axis='y')
            ax.yaxis.set_major_locator(ticker.MultipleLocator(1))
            ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.5))
            ax.grid(True, which='minor', alpha=0.2, linestyle='--', axis='y')
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=15))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=0, ha='right', fontsize=8)
            
            all_temps = [d['temp'] for data_list in self.history_data.values() for d in data_list if d['temp'] is not None]
            if all_temps:
                min_temp, max_temp = min(all_temps), max(all_temps)
                margin = (max_temp - min_temp) * 0.12 or 1
                ax.set_ylim(int(min_temp - margin), int(max_temp + margin) + 1)
            
            fig.subplots_adjust(left=0.08, right=0.98, top=0.88, bottom=0.13)
            plt.savefig(self.history_plot_path, dpi=100, bbox_inches='tight')
            plt.close(fig)  # 🧹 Liberar memoria
            os.utime(self.history_plot_path, None)
        except Exception as e:
            print(f"❌ Error gráfico: {e}", flush=True)
    
    def print_status(self, weather_data, weather_v1_data, pws1_data, pws2_data, meteociel_data, weather_hist_data, metar_noaa=None, metar_avwx=None):
        now = datetime.now().strftime('%H:%M:%S')
        def fmt(data): return f"{data.get('temperature'):>6.2f}°C" if data and data.get('temperature') is not None else "   N/A"

        print(f"[{now}] Weather v3 | {fmt(weather_data)}", flush=True)
        print(f"[{now}] Weather v1 | {fmt(weather_v1_data)}", flush=True)
        print(f"[{now}] {pws1_data.get('station_id', 'IMADRI133'):>9} | {fmt(pws1_data)}" if pws1_data else f"[{now}] IMADRI133 | ❌ Sin datos", flush=True)
        print(f"[{now}] {pws2_data.get('station_id', 'IMADRI265'):>9} | {fmt(pws2_data)}" if pws2_data else f"[{now}] IMADRI265 | ❌ Sin datos", flush=True)
        meteociel_time = meteociel_data.get('timestamp').strftime('%H:%M') if meteociel_data and meteociel_data.get('timestamp') else now
        print(f"[{meteociel_time}:00] Meteociel | {fmt(meteociel_data)}" if meteociel_data else f"[{now}] Meteociel   | ❌ Sin datos", flush=True)
        if weather_hist_data:
            hist_time = weather_hist_data.get('timestamp')
            hist_time_str = hist_time.strftime('%H:%M') if hist_time else now
            count = weather_hist_data.get('count', 0)
            print(f"[{hist_time_str}:00] Histórico | {fmt(weather_hist_data)}  {count} registros", flush=True)
        else:
            print(f"[{now}] Histórico | ❌ Sin datos", flush=True)
        if metar_noaa:
            ts = metar_noaa.get('metar_time', 'N/A')
            raw_str = metar_noaa.get('raw', '')
            # Imprime con tu formato original, añadiendo el texto RAW al final
            print(f"[{now}] AviationWx | {fmt(metar_noaa)}  {ts} | {raw_str}", flush=True)
        else:
            print(f"[{now}] AviationWx | ❌ Sin datos", flush=True)
        if metar_avwx:
            ts = metar_avwx.get('metar_time', 'N/A')
            print(f"[{now}] AVWX METAR | {fmt(metar_avwx)}  {ts}", flush=True)
        else:
            print(f"[{now}] AVWX METAR | ❌ Sin datos", flush=True)
        print(flush=True)
    
    def monitor(self, interval=20):
        print(f"\n{'='*80}\nMONITOREO - AEROPUERTO MADRID-BARAJAS (OPTIMIZADO)\n{'='*80}", flush=True)
        print("API 1: Weather.com v3 (ICAO LEMD)\nAPI 2: Weather.com v1 (LEMD:9:ES)\nAPI 3: PWS IMADRI133\nAPI 4: PWS IMADRI265\nAPI 5: Meteociel\nAPI 6: Weather.com Histórico (último registro)\nAPI 7: AviationWeather NOAA METAR\nAPI 8: AVWX METAR", flush=True)
        print(f"Intervalo: {interval}s\n{'='*80}\n", flush=True)
        
        try:
            while True:
                weather_data = self.get_weather_com_temperature()
                weather_v1_data = self.get_weather_v1_temperature()
                pws1_data = self.get_pws_temperature(self.params_pws1)
                pws2_data = self.get_pws_temperature(self.params_pws2)
                meteociel_data = self.get_meteociel_temperature()
                weather_hist_data = self.get_weather_historical_last()
                metar_noaa = self.get_temp_aviationweather()
                metar_avwx = self.get_temp_avwx()

                for src, data in [('weather_com', weather_data), ('weather_v1', weather_v1_data),
                                  ('pws1', pws1_data), ('pws2', pws2_data)]:
                    if data:
                        self.add_to_history(src, data.get('temperature'))
                if meteociel_data:
                    self.add_to_history('meteociel', meteociel_data.get('temperature'), meteociel_data.get('timestamp'))
                # NO añadir METAR ni histórico al historial de gráficas

                self.print_status(weather_data, weather_v1_data, pws1_data, pws2_data, meteociel_data, weather_hist_data, metar_noaa, metar_avwx)
                print(f"\n{'='*80}", flush=True)
                self.generate_history_plot()
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\nBot detenido.\n", flush=True)
            self.generate_history_plot()
            self.session.close()  # 🔒 Cerrar sesión
            sys.exit(0)

def main():
    bot = PolymarketWeatherBot()
    bot.monitor(interval=20)

if __name__ == "__main__":
    main()
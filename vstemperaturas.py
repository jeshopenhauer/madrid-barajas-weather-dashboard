#!/usr/bin/env python3
"""
Script para comparar temperaturas de ayer vs hoy en Madrid-Barajas
Extrae los datos del gráfico de Meteociel directamente del HTML
"""

import requests
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import re
import sys

class TemperatureComparison:
    def __init__(self):
        self.base_url = "https://www.meteociel.fr/temps-reel/obs_villes.php"
        self.code = "8221"  # Madrid Barajas
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Datos extraídos
        self.yesterday_data = {}
        self.today_data = {}
        
        # Configurar matplotlib
        plt.ion()
        self.fig, self.ax = plt.subplots(figsize=(15, 8))
    
    def get_url_for_date(self, date):
        """Genera la URL para una fecha específica"""
        # NOTA: Meteociel tiene los datos en mois2=2 (febrero) aunque estemos en marzo
        # Esto es una peculiaridad de su sistema
        return f"{self.base_url}?code2={self.code}&jour2={date.day}&mois2=2&annee2={date.year}"
    
    def extract_temperature_data_from_html(self, url, date_label):
        """Descarga el HTML y extrae los datos del gráfico de temperatura"""
        try:
            print(f"�� Obteniendo datos de {date_label}...")
            print(f"    URL: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=15)
            response.encoding = 'ISO-8859-1'  # La página usa ISO-8859-1
            
            if response.status_code != 200:
                print(f"❌ Error HTTP: {response.status_code}")
                return {}
            
            # Buscar el gráfico de temperatura (type=0) en el HTML
            # Patrón: src='//static.meteociel.fr/cartes_obs/graphe2.php?type=0&data...
            pattern = r"src=['\"]//static\.meteociel\.fr/cartes_obs/graphe2\.php\?type=0&([^'\"]+)['\"]"
            match = re.search(pattern, response.text)
            
            if not match:
                print(f"❌ No se encontró el gráfico de temperatura en el HTML")
                return {}
            
            # Extraer la cadena de parámetros
            params_str = match.group(1)
            
            # Parsear los datos de temperatura
            # Formato: data23.5=8&data23=8.1&data22.5=9&...
            data_pattern = r'data([\d.]+)=([\d.]+)'
            matches = re.findall(data_pattern, params_str)
            
            if not matches:
                print(f"❌ No se encontraron datos de temperatura")
                return {}
            
            # Convertir a diccionario {hora: temperatura}
            # IMPORTANTE: Convertir de UTC a hora local Madrid (UTC+1)
            temp_data = {}
            for hour_str, temp_str in matches:
                hour_utc = float(hour_str)
                temp = float(temp_str)
                # Sumar 1 hora para convertir de UTC a Madrid (UTC+1)
                hour_local = (hour_utc + 1) % 24
                temp_data[hour_local] = temp
            
            print(f"✅ Extraídos {len(temp_data)} puntos de datos de {date_label}")
            return temp_data
            
        except Exception as e:
            print(f"❌ Error extrayendo datos de {date_label}: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def load_data(self):
        """Carga los datos de ayer y hoy"""
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        
        print(f"\n{'='*80}")
        print(f"📊 COMPARACIÓN DE TEMPERATURAS - MADRID BARAJAS")
        print(f"{'='*80}")
        print(f"Ayer: {yesterday.strftime('%d/%m/%Y')}")
        print(f"Hoy:  {today.strftime('%d/%m/%Y')}")
        print(f"{'='*80}\n")
        
        # Obtener datos
        yesterday_url = self.get_url_for_date(yesterday)
        today_url = self.get_url_for_date(today)
        
        self.yesterday_data = self.extract_temperature_data_from_html(yesterday_url, "AYER")
        self.today_data = self.extract_temperature_data_from_html(today_url, "HOY")
    
    def plot_comparison(self):
        """Crea el gráfico comparativo"""
        self.ax.clear()
        
        if not self.yesterday_data and not self.today_data:
            self.ax.text(0.5, 0.5, 'No hay datos disponibles',
                        ha='center', va='center', fontsize=16)
            plt.draw()
            plt.pause(0.1)
            return
        
        # Plotear datos de ayer (rojo)
        if self.yesterday_data:
            # Ordenar por hora
            hours_yesterday = sorted(self.yesterday_data.keys())
            temps_yesterday = [self.yesterday_data[h] for h in hours_yesterday]
            
            self.ax.plot(hours_yesterday, temps_yesterday,
                        'o-', color='#FF6B6B', linewidth=2.5, markersize=6,
                        label=f'Ayer ({len(temps_yesterday)} mediciones)', alpha=0.8)
        
        # Plotear datos de hoy (azul/turquesa)
        if self.today_data:
            # Ordenar por hora
            hours_today = sorted(self.today_data.keys())
            temps_today = [self.today_data[h] for h in hours_today]
            
            self.ax.plot(hours_today, temps_today,
                        'o-', color='#4ECDC4', linewidth=2.5, markersize=6,
                        label=f'Hoy ({len(temps_today)} mediciones)', alpha=0.8)
            
            # Marcar el último punto de hoy
            if temps_today:
                last_hour = hours_today[-1]
                last_temp = temps_today[-1]
                self.ax.plot(last_hour, last_temp,
                            'o', color='#FFD700', markersize=14,
                            markeredgecolor='black', markeredgewidth=2,
                            label=f'Última lectura: {last_temp:.1f}°C a las {int(last_hour):02d}:{int((last_hour % 1) * 60):02d}',
                            zorder=5)
        
        # Configurar el gráfico
        self.ax.set_xlabel('Hora del día (Madrid - UTC+1)', fontsize=13, fontweight='bold')
        self.ax.set_ylabel('Temperatura (°C)', fontsize=13, fontweight='bold')
        
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        title = f'📊 Comparación de Temperaturas - Madrid Barajas\n'
        title += f'🔴 Ayer: {yesterday.strftime("%d/%m/%Y")} vs 🔵 Hoy: {today.strftime("%d/%m/%Y")}'
        self.ax.set_title(title, fontsize=15, fontweight='bold', pad=20)
        
        self.ax.legend(loc='best', fontsize=8, framealpha=0.5)
        self.ax.grid(True, alpha=0.3, linestyle='--', linewidth=1)
        
        # Configurar eje X (horas del día)
        self.ax.set_xlim(0, 24)
        self.ax.set_xticks(range(0, 25, 2))
        self.ax.set_xticklabels([f'{h:02d}:00' for h in range(0, 25, 2)],
                               rotation=45, ha='right')
        
        # Ajustar límites del eje Y
        all_temps = []
        if self.yesterday_data:
            all_temps.extend(self.yesterday_data.values())
        if self.today_data:
            all_temps.extend(self.today_data.values())
        
        if all_temps:
            min_temp = min(all_temps)
            max_temp = max(all_temps)
            margin = (max_temp - min_temp) * 0.1 or 1
            self.ax.set_ylim(min_temp - margin, max_temp + margin)
        
        # Ajustar layout
        self.fig.tight_layout()
        
        # Timestamp
        now = datetime.now().strftime('%H:%M:%S - %d/%m/%Y')
        self.fig.text(0.99, 0.01, f'Datos extraídos: {now}',
                     ha='right', va='bottom', fontsize=9, style='italic', alpha=0.7)
        
        plt.draw()
        plt.pause(0.1)
    
    def run(self):
        """Ejecuta el comparador (sin actualización automática)"""
        # Cargar datos
        self.load_data()
        
        # Mostrar gráfico
        self.plot_comparison()
        
        print(f"\n{'='*80}")
        print(f"✅ Gráfico generado - Presiona Ctrl+C o cierra la ventana para salir")
        print(f"{'='*80}\n")
        
        try:
            # Mantener la ventana abierta
            plt.ioff()
            plt.show()
        except KeyboardInterrupt:
            print(f"\n✅ Programa terminado.\n")
            sys.exit(0)

def main():
    """Función principal"""
    print("🚀 Iniciando comparador de temperaturas Meteociel...")
    print("📥 Extrayendo datos del HTML...\n")
    try:
        comparison = TemperatureComparison()
        comparison.run()
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

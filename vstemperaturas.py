#!/usr/bin/env python3
"""
Script para comparar temperaturas de ayer vs hoy en Madrid-Barajas
Extrae los datos del gráfico de Meteociel directamente del HTML
"""

import requests
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import re
import sys

# ═══════════════════════════════════════════════════════════════════════════
# 🔧 CONFIGURACIÓN - Cambiar estas variables según necesites
# ═══════════════════════════════════════════════════════════════════════════
CUSTOM_DAY = 30        # Día específico a comparar (ej: 24 para el día 24 de marzo)
CUSTOM_MONTH = 2       # Mes Meteociel: 2=marzo, 3=abril (siempre el mes actual en formato Meteociel)
# ═══════════════════════════════════════════════════════════════════════════

class TemperatureComparison:
    def __init__(self, custom_day=None, custom_month=2):
        """
        Inicializa el comparador de temperaturas
        
        Args:
            custom_day: Día específico a comparar (ej: 24 para el día 24)
            custom_month: Mes del día específico (2 para mois2=2, 3 para mois2=3, etc.)
        """
        self.base_url = "https://www.meteociel.fr/temps-reel/obs_villes.php"
        self.code = "8221"  # Madrid Barajas
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Día específico a comparar (opcional)
        self.custom_day = custom_day
        self.custom_month = custom_month
        
        # Datos extraídos
        self.yesterday_data = {}
        self.today_data = {}
        self.custom_data = {}
        
        # Configurar matplotlib
        plt.ion()
        self.fig, self.ax = plt.subplots(figsize=(15, 8))
    
    def get_url_for_date(self, date, custom_month=None):
        """Genera la URL para una fecha específica"""
        # NOTA: Meteociel tiene los datos en mois2=2 (febrero) aunque estemos en marzo
        # Esto es una peculiaridad de su sistema
        # A partir de abril probablemente sea mois2=3
        month = custom_month if custom_month is not None else 2
        return f"{self.base_url}?code2={self.code}&jour2={date.day}&mois2={month}&annee2={date.year}"
    
    def get_url_for_custom_day(self, day, month, year):
        """Genera la URL para un día específico"""
        return f"{self.base_url}?code2={self.code}&jour2={day}&mois2={month}&annee2={year}"
    
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
            temp_data = {}
            for hour_str, temp_str in matches:
                hour_utc = float(hour_str)
                temp = float(temp_str)
                temp_data[hour_utc] = temp
            
            print(f"✅ Extraídos {len(temp_data)} puntos de datos de {date_label}")
            return temp_data
            
        except Exception as e:
            print(f"❌ Error extrayendo datos de {date_label}: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def load_data(self):
        """Carga los datos de ayer, hoy y (opcionalmente) un día específico"""
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        
        print(f"\n{'='*80}")
        print(f"📊 COMPARACIÓN DE TEMPERATURAS - MADRID BARAJAS")
        print(f"{'='*80}")
        print(f"Ayer: {yesterday.strftime('%d/%m/%Y')}")
        print(f"Hoy:  {today.strftime('%d/%m/%Y')}")
        if self.custom_day:
            print(f"Día específico: {self.custom_day:02d}/{self.custom_month:02d}/{today.year}")
        print(f"{'='*80}\n")
        
        # Obtener datos de ayer y hoy
        yesterday_url = self.get_url_for_date(yesterday)
        today_url = self.get_url_for_date(today)
        
        self.yesterday_data = self.extract_temperature_data_from_html(yesterday_url, "AYER")
        self.today_data = self.extract_temperature_data_from_html(today_url, "HOY")
        
        # Obtener datos del día específico si se especificó
        if self.custom_day:
            custom_url = self.get_url_for_custom_day(self.custom_day, self.custom_month, today.year)
            label = f"DÍA {self.custom_day:02d}/{self.custom_month:02d}"
            self.custom_data = self.extract_temperature_data_from_html(custom_url, label)
    
    def plot_comparison(self):
        """Crea el gráfico comparativo"""
        self.ax.clear()
        
        if not self.yesterday_data and not self.today_data and not self.custom_data:
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
        
        # Plotear datos del día específico (verde/morado)
        if self.custom_data:
            hours_custom = sorted(self.custom_data.keys())
            temps_custom = [self.custom_data[h] for h in hours_custom]
            
            self.ax.plot(hours_custom, temps_custom,
                        'o-', color='#9B59B6', linewidth=2.5, markersize=6,
                        label=f'Día {self.custom_day:02d}/{self.custom_month:02d} ({len(temps_custom)} mediciones)', alpha=0.8)
        
        # Configurar el gráfico
        self.ax.set_xlabel('Hora del día (UTC)', fontsize=13, fontweight='bold')
        self.ax.set_ylabel('Temperatura (°C)', fontsize=13, fontweight='bold')
        
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        title = f'📊 Comparación de Temperaturas - Madrid Barajas\n'
        title += f'🔴 Ayer: {yesterday.strftime("%d/%m/%Y")} vs 🔵 Hoy: {today.strftime("%d/%m/%Y")}'
        if self.custom_day:
            title += f' vs 🟣 {self.custom_day:02d}/{self.custom_month:02d}/{today.year}'
        self.ax.set_title(title, fontsize=15, fontweight='bold', pad=20)
        
        self.ax.legend(loc='best', fontsize=11, framealpha=0.9)
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
        if self.custom_data:
            all_temps.extend(self.custom_data.values())
        
        if all_temps:
            min_temp = min(all_temps)
            max_temp = max(all_temps)
            margin = (max_temp - min_temp) * 0.1 or 1
            self.ax.set_ylim(min_temp - margin, max_temp + margin)
            
            # Añadir marcas en el eje Y cada 1°C
            # Marcas principales cada 1°C
            self.ax.yaxis.set_major_locator(ticker.MultipleLocator(1))
            # Marcas secundarias cada 0.5°C
            self.ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.5))
            # Mostrar grid para marcas principales
            self.ax.grid(True, which='major', alpha=0.3, linestyle='-', linewidth=1)
            self.ax.grid(True, which='minor', alpha=0.15, linestyle=':', linewidth=0.5)
        
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
    
    # Ejemplo de uso:
    # Para comparar con el día 24: TemperatureComparison(custom_day=24, custom_month=2)
    # Para solo ayer vs hoy: TemperatureComparison()
    
    # Usar las variables de configuración del inicio del archivo
    custom_day = CUSTOM_DAY
    custom_month = CUSTOM_MONTH
    
    # Permitir sobreescribir con argumentos de línea de comandos
    # Uso: python vstemperaturas.py [día] [mes]
    if len(sys.argv) > 1:
        try:
            custom_day = int(sys.argv[1])
            print(f"📅 Comparando con el día específico: {custom_day:02d}/{custom_month:02d}\n")
        except ValueError:
            print(f"⚠️  Argumento inválido. Uso: python vstemperaturas.py [día] [mes]\n")
            print(f"    Ejemplo: python vstemperaturas.py 24 2\n")
    
    # Permitir pasar mes como segundo argumento: python vstemperaturas.py 24 3
    if len(sys.argv) > 2:
        try:
            custom_month = int(sys.argv[2])
            print(f"📅 Usando mes: mois2={custom_month}\n")
        except ValueError:
            print(f"⚠️  Mes inválido, usando mois2={custom_month}\n")
    
    try:
        comparison = TemperatureComparison(custom_day=custom_day, custom_month=custom_month)
        comparison.run()
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

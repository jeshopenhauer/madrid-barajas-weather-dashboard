#!/usr/bin/env python3
"""
Script para investigar estaciones PWS tipo IMADRI
Busca la estación con mejor actualización y precisión (decimales)
"""

import requests
import time
from datetime import datetime
import json

API_KEY = "e1f10a1e78da46f5b10a1e78da96f525"
BASE_URL = "https://api.weather.com/v2/pws/observations/current"

# Estaciones de la lista que proporcionaste
KNOWN_STATIONS = [
    "IMADRI364", "IMADRI763", "IMADRI265", "IMADRI608", "IMADRI733",
    "IMADRI740", "IMADRI682", "IMADRI569", "IMADRI454", "IMADRI672",
    "IMADRI204", "IMADRI813", "IMADRI707", "IMADRI416", "IMADRI122",
    "IMADRI783", "IMADRI43", "IMADRI479", "IMADRI786"
]

def test_station(station_id):
    """Prueba una estación y devuelve sus datos"""
    params = {
        "apiKey": API_KEY,
        "stationId": station_id,
        "format": "json",
        "units": "m",
        "numericPrecision": "decimal"
    }
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'observations' in data and len(data['observations']) > 0:
                obs = data['observations'][0]
                
                # Extraer datos clave
                temp = obs.get('metric', {}).get('temp')
                hum = obs.get('humidity')
                
                # Verificar si tiene decimales
                has_decimals = temp is not None and isinstance(temp, (int, float)) and temp != int(temp)
                
                # Timestamp de observación
                obs_time = obs.get('obsTimeLocal', 'N/A')
                
                return {
                    'station_id': station_id,
                    'temperature': temp,
                    'humidity': hum,
                    'has_decimals': has_decimals,
                    'obs_time': obs_time,
                    'neighborhood': obs.get('neighborhood', 'N/A'),
                    'success': True
                }
        
        return {'station_id': station_id, 'success': False, 'reason': f'HTTP {response.status_code}'}
    
    except Exception as e:
        return {'station_id': station_id, 'success': False, 'reason': str(e)}

def scan_imadri_range(start, end):
    """Escanea un rango de números IMADRI"""
    found_stations = []
    
    print(f"\n🔍 Escaneando IMADRI{start:03d} a IMADRI{end:03d}...")
    
    for num in range(start, end + 1):
        station_id = f"IMADRI{num}"
        result = test_station(station_id)
        
        if result['success']:
            found_stations.append(result)
            decimals = "✅ SÍ" if result['has_decimals'] else "❌ NO"
            print(f"  ✓ {station_id} | {result['neighborhood'][:20]:20s} | {result['temperature']:>6}°C | Decimales: {decimals}")
        
        # Pequeña pausa para no saturar la API
        time.sleep(0.1)
    
    return found_stations

def main():
    print("="*80)
    print("INVESTIGACIÓN DE ESTACIONES PWS TIPO IMADRI")
    print("="*80)
    
    # 1. Probar estaciones conocidas
    print("\n📋 PARTE 1: Probando estaciones conocidas de la lista")
    print("-"*80)
    
    known_results = []
    for station in KNOWN_STATIONS:
        result = test_station(station)
        known_results.append(result)
        time.sleep(0.1)
    
    # Ordenar por las que tienen decimales
    known_results.sort(key=lambda x: (not x.get('has_decimals', False), x.get('station_id', '')))
    
    print("\n📊 RESULTADOS DE ESTACIONES CONOCIDAS:")
    print("-"*80)
    for r in known_results:
        if r['success']:
            decimals = "✅ Decimales" if r['has_decimals'] else "❌ Sin decimales"
            print(f"{r['station_id']:12s} | {r['neighborhood'][:25]:25s} | {r['temperature']:>6}°C | {decimals}")
    
    # 2. Probar algunos números adicionales estratégicos
    print("\n\n🔍 PARTE 2: Probando estaciones adicionales")
    print("-"*80)
    
    all_found = []
    
    # Probar números aleatorios que podrían existir
    additional_numbers = list(range(1, 50)) + list(range(56, 100)) + list(range(133, 150)) + list(range(211, 220))
    
    for num in additional_numbers:
        station_id = f"IMADRI{num}"
        if station_id not in KNOWN_STATIONS:  # Evitar duplicados
            result = test_station(station_id)
            if result['success']:
                all_found.append(result)
                decimals = "✅ SÍ" if result['has_decimals'] else "❌ NO"
                print(f"  ✓ {station_id} | {result['neighborhood'][:20]:20s} | {result['temperature']:>6}°C | Decimales: {decimals}")
            time.sleep(0.05)
    
    # 3. Análisis final - buscar la MEJOR estación
    print("\n\n🏆 ANÁLISIS FINAL: Mejores estaciones para usar")
    print("="*80)
    
    # Combinar todas las estaciones encontradas
    all_stations = known_results + all_found
    
    # Filtrar solo las exitosas con decimales
    decimal_stations = [s for s in all_stations if s.get('success') and s.get('has_decimals')]
    
    if decimal_stations:
        print("\n✅ ESTACIONES CON DECIMALES (mejor precisión):")
        print("-"*80)
        for s in decimal_stations:
            print(f"  {s['station_id']:12s} | {s['neighborhood'][:30]:30s} | {s['temperature']:>6}°C | Hora: {s['obs_time']}")
        
        print("\n💡 RECOMENDACIÓN:")
        print(f"   Usa: {decimal_stations[0]['station_id']} ({decimal_stations[0]['neighborhood']})")
    else:
        print("\n⚠️  No se encontraron estaciones con decimales")
    
    # Guardar resultados en JSON
    with open('pws_stations_analysis.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'known_stations': known_results,
            'scanned_stations': all_found,
            'decimal_stations': decimal_stations
        }, f, indent=2)
    
    print(f"\n💾 Resultados guardados en: pws_stations_analysis.json")

if __name__ == "__main__":
    main()

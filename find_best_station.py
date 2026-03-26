#!/usr/bin/env python3
"""
Script simple para encontrar la mejor estación PWS cerca de Barajas
Criterios: 1) Tiene decimales, 2) Actualización reciente, 3) Datos completos
"""

import requests
from datetime import datetime
import json

API_KEY = "e1f10a1e78da46f5b10a1e78da96f525"
BASE_URL = "https://api.weather.com/v2/pws/observations/current"

# Estaciones cerca de Barajas
STATIONS = [
    "IMADRI265",  # Barajas (la que usas ahora)
    "IMADRI133",  # Barajas
    "IMADRI56",   # Madrid
    "IMADRI211",  # Probar este
    "IMADRI682",  # Pinar del Rey
    "IMADRI416",  # Pinar del Rey
    "IMADRI763",  # Rejas (muy cerca de Barajas)
    "IMADRI364",  # Alameda de Osuna
    "IMADRI122",  # Madrid
    "IMADRI14",   # Guindalera
    "IMADRI22",   # Fuencarral
    "IMADRI36",   # Carabanchel
]

def test_station_detailed(station_id):
    """Prueba una estación y obtiene todos los detalles"""
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
                metric = obs.get('metric', {})
                
                temp = metric.get('temp')
                hum = obs.get('humidity')
                wind = metric.get('windSpeed')
                obs_time_str = obs.get('obsTimeLocal', '')
                
                # Parsear tiempo de observación
                try:
                    # Formato: "2026-03-25 11:45:00"
                    if obs_time_str:
                        obs_time = datetime.strptime(obs_time_str[:19], '%Y-%m-%d %H:%M:%S')
                        time_diff = (datetime.now() - obs_time).total_seconds() / 60
                    else:
                        time_diff = 999
                except Exception as e:
                    print(f"Error parsing time for {station_id}: {obs_time_str}, {e}")
                    time_diff = 999
                
                # Verificar decimales
                has_decimals = temp is not None and isinstance(temp, (int, float)) and (temp != int(temp) or str(temp).endswith('.0'))
                
                return {
                    'station_id': station_id,
                    'temperature': temp,
                    'humidity': hum,
                    'wind_speed': wind,
                    'has_decimals': has_decimals,
                    'obs_time': obs_time_str,
                    'minutes_old': round(time_diff, 1),
                    'neighborhood': obs.get('neighborhood', 'N/A'),
                    'lat': obs.get('lat', 0),
                    'lon': obs.get('lon', 0),
                    'success': True,
                    'complete_data': temp is not None and hum is not None
                }
        
        return {'station_id': station_id, 'success': False}
    
    except Exception as e:
        return {'station_id': station_id, 'success': False, 'error': str(e)}

def main():
    print("="*100)
    print(" " * 30 + "🔍 BÚSQUEDA DE LA MEJOR ESTACIÓN PWS")
    print("="*100)
    print()
    
    results = []
    
    for station in STATIONS:
        print(f"Probando {station}...", end=" ")
        result = test_station_detailed(station)
        results.append(result)
        
        if result['success']:
            print(f"✅ {result['temperature']}°C - {result['neighborhood']}")
        else:
            print("❌ Sin datos")
    
    print("\n" + "="*100)
    print(" " * 35 + "📊 ANÁLISIS DETALLADO")
    print("="*100)
    
    # Filtrar exitosas
    successful = [r for r in results if r['success']]
    
    if not successful:
        print("❌ No se encontraron estaciones activas")
        return
    
    # Ordenar por: 1) Tiene decimales, 2) Datos completos, 3) Más reciente
    successful.sort(key=lambda x: (
        not x.get('has_decimals', False),
        not x.get('complete_data', False),
        x.get('minutes_old', 999)
    ))
    
    print("\n🏆 RANKING DE ESTACIONES (mejor a peor):\n")
    print(f"{'#':<3} {'Estación':<12} {'Ubicación':<25} {'Temp':<8} {'Decimales':<10} {'Antigüedad':<15} {'Datos':<10}")
    print("-" * 100)
    
    for i, r in enumerate(successful, 1):
        decimals = "✅ SÍ" if r.get('has_decimals') else "❌ NO"
        complete = "✅ Completos" if r.get('complete_data') else "⚠️ Parciales"
        age = f"{r.get('minutes_old', 0):.1f} min"
        temp = f"{r.get('temperature', 0)}°C"
        
        marker = "⭐" if i == 1 else "  "
        print(f"{marker}{i:<3} {r['station_id']:<12} {r['neighborhood'][:24]:<25} {temp:<8} {decimals:<10} {age:<15} {complete:<10}")
    
    # Mostrar recomendación
    best = successful[0]
    print("\n" + "="*100)
    print("💡 RECOMENDACIÓN FINAL:")
    print("="*100)
    print(f"""
🎯 MEJOR ESTACIÓN: {best['station_id']}
   📍 Ubicación: {best['neighborhood']}
   🌡️  Temperatura: {best['temperature']}°C
   ✅ Decimales: {'SÍ' if best['has_decimals'] else 'NO'}
   ⏱️  Actualizada hace: {best['minutes_old']:.1f} minutos
   📊 Datos: {'Completos' if best['complete_data'] else 'Parciales'}
   
🔄 CAMBIO RECOMENDADO:
   Actual: IMADRI265 (Barajas)
   Nueva:  {best['station_id']} ({best['neighborhood']})
    """)
    
    # Comparar con IMADRI265
    current = next((r for r in successful if r['station_id'] == 'IMADRI265'), None)
    if current and best['station_id'] != 'IMADRI265':
        print("📈 VENTAJAS vs IMADRI265:")
        if best['has_decimals'] and not current.get('has_decimals', True):
            print("   ✅ Tiene decimales (más precisión)")
        if best['minutes_old'] < current.get('minutes_old', 999):
            print(f"   ✅ Más reciente ({best['minutes_old']:.1f} min vs {current['minutes_old']:.1f} min)")
        if best['complete_data'] and not current.get('complete_data', True):
            print("   ✅ Datos más completos")
    
    # Guardar
    with open('best_pws_station.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'best_station': best,
            'all_results': successful
        }, f, indent=2)
    
    print(f"\n💾 Resultados guardados en: best_pws_station.json\n")

if __name__ == "__main__":
    main()

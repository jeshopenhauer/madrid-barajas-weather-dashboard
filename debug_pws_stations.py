#!/usr/bin/env python3
"""
Script de debug para verificar las respuestas de las estaciones PWS
"""

import requests
import json

API_KEY = "e1f10a1e78da46f5b10a1e78da96f525"
BASE_URL = "https://api.weather.com/v2/pws/observations/current"

STATIONS = {
    "IMADRI133": "Barajas",
    "IMADRI265": "Barajas", 
    "IMADRI56": "Madrid",
    "IMADRI883": "Timón",
    "IMADRI364": "Alameda de Osuna",
    "IMADRI882": "Alameda de Osuna"
}

print("="*80)
print("DEBUG: Verificando respuestas RAW de las estaciones PWS")
print("="*80)
print()

for station_id, location in STATIONS.items():
    print(f"\n{'='*80}")
    print(f"ESTACIÓN: {station_id} ({location})")
    print("="*80)
    
    params = {
        "apiKey": API_KEY,
        "stationId": station_id,
        "format": "json",
        "units": "m",
        "numericPrecision": "decimal"
    }
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"URL: {response.url}")
        print()
        
        if response.status_code == 200:
            data = response.json()
            
            # Imprimir JSON completo formateado
            print("RESPUESTA JSON:")
            print(json.dumps(data, indent=2))
            print()
            
            # Extraer datos específicos
            if 'observations' in data and len(data['observations']) > 0:
                obs = data['observations'][0]
                metric = obs.get('metric', {})
                
                temp = metric.get('temp')
                hum = obs.get('humidity')
                wind = metric.get('windSpeed')
                obs_time = obs.get('obsTimeLocal')
                neighborhood = obs.get('neighborhood')
                
                print("DATOS EXTRAÍDOS:")
                print(f"  - Temperatura: {temp}°C (tipo: {type(temp).__name__})")
                print(f"  - Humedad: {hum}%")
                print(f"  - Viento: {wind} km/h")
                print(f"  - Hora obs: {obs_time}")
                print(f"  - Ubicación: {neighborhood}")
                print(f"  - Station ID real: {obs.get('stationID')}")
            else:
                print("⚠️  No hay 'observations' en la respuesta")
        else:
            print(f"❌ Error HTTP {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"❌ EXCEPCIÓN: {e}")

print("\n" + "="*80)
print("FIN DEL DEBUG")
print("="*80)

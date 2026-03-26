#!/usr/bin/env python3
"""
Barrido completo IMADRI0-1000
Muestra solo las estaciones que responden con su temperatura
"""

import requests
import sys

API_KEY = "e1f10a1e78da46f5b10a1e78da96f525"
BASE_URL = "https://api.weather.com/v2/pws/observations/current"

print("="*80)
print("BARRIDO COMPLETO IMADRI0 - IMADRI1000")
print("="*80)
print()

found_count = 0

for n in range(0, 1001):
    station_id = f"IMADRI{n}"
    
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
                temp = obs.get('metric', {}).get('temp')
                neighborhood = obs.get('neighborhood', 'N/A')
                
                if temp is not None:
                    found_count += 1
                    print(f"{station_id:12s} | {neighborhood:30s} | {temp:>6}°C")
                    sys.stdout.flush()
    
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Interrumpido en IMADRI{n}")
        print(f"✅ Encontradas {found_count} estaciones activas hasta ahora")
        sys.exit(0)
    except:
        pass  # Ignorar errores, seguir escaneando

print()
print("="*80)
print(f"✅ TOTAL ENCONTRADAS: {found_count} estaciones activas")
print("="*80)

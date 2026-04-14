#!/usr/bin/env python3
"""
Script de debug para ver la estructura HTML de Meteociel
"""

import requests
from bs4 import BeautifulSoup
import re

url = "https://www.meteociel.fr/temps-reel/obs_villes.php?code2=8221&jour2=1&mois2=3&annee2=2026"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

print(f"Descargando: {url}\n")

response = requests.get(url, headers=headers, timeout=15)
response.encoding = 'ISO-8859-1'

soup = BeautifulSoup(response.text, 'html.parser')
rows = soup.find_all('tr')

print(f"Total de filas encontradas: {len(rows)}\n")

# Examinar las primeras 5 filas válidas
count = 0
for row in rows:
    cells = row.find_all('td')
    
    if len(cells) >= 11:
        hora_cell = cells[0].get_text(strip=True)
        
        if 'h' in hora_cell and len(hora_cell) <= 6:
            count += 1
            if count <= 3:
                print(f"="*80)
                print(f"FILA {count}: Hora {hora_cell}")
                print(f"="*80)
                
                for i, cell in enumerate(cells[:11 ]):
                    print(f"\nColumna {i}:")
                    print(f"  Texto simple: {cell.get_text(strip=True)[:50]}")
                    print(f"  Texto completo: {cell.get_text(separator='|', strip=True)[:80]}")
                    
                    # Especial para columnas 9 y 10
                    if i == 9:
                        print(f"  >>> VIENTO <<<")
                        wind_text = cell.get_text(separator=' ', strip=True)
                        print(f"  Texto para regex: '{wind_text}'")
                        match = re.search(r'(\d+)\s*km/h', wind_text)
                        if match:
                            print(f"  ✅ Match encontrado: {match.group(1)} km/h")
                        else:
                            print(f"  ❌ No match")
                    
                    if i == 10:
                        print(f"  >>> PRESIÓN <<<")
                        pres_text = cell.get_text(separator=' ', strip=True)
                        print(f"  Texto para regex: '{pres_text}'")
                        match = re.search(r'(\d+\.?\d*)\s*hPa', pres_text)
                        if match:
                            print(f"  ✅ Match encontrado: {match.group(1)} hPa")
                        else:
                            print(f"  ❌ No match")
                
                print()
            
            if count >= 3:
                break

print(f"\nTotal de filas de datos válidas: {count}")

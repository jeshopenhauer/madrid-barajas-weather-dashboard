#!/usr/bin/env python3
"""
Temperaturas LEMD desde múltiples fuentes (actualización cada 20 s):
  1. Aviation Weather (NOAA) METAR API
  2. AVWX REST API
"""

import requests
import time
import re
from datetime import datetime, timezone

AVWX_TOKEN = "MF_MQHY-xWLmV7Hwyccc_jh7H9q10cvRAFJHSLhRyvQ"
STATION    = "LEMD"
INTERVAL   = 20  # segundos


def extract_metar_time(raw):
    """Extrae el timestamp METAR (p.ej. '181000Z') del mensaje crudo."""
    if raw:
        match = re.search(r'\b(\d{6}Z)\b', raw)
        if match:
            return match.group(1)
    return "N/A"


def get_temp_aviationweather():
    url     = "https://aviationweather.gov/api/data/metar"
    params  = {"ids": STATION, "format": "json"}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data:
            latest = data[0]
            return latest.get("temp"), extract_metar_time(latest.get("rawOb"))
    except Exception as e:
        print(f"  [AviationWeather error] {e}")
    return None, "N/A"


def get_temp_avwx():
    url     = f"https://avwx.rest/api/metar/{STATION}"
    headers = {"Authorization": AVWX_TOKEN}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        temp_obj = data.get("temperature")
        temp = temp_obj.get("value") if isinstance(temp_obj, dict) else temp_obj
        return temp, extract_metar_time(data.get("raw"))
    except Exception as e:
        print(f"  [AVWX error] {e}")
    return None, "N/A"


if __name__ == "__main__":
    print(f"Monitorizando {STATION} — actualización cada {INTERVAL} s  (Ctrl+C para salir)\n")
    try:
        while True:
            now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            t1, ts1 = get_temp_aviationweather()
            t2, ts2 = get_temp_avwx()

            t1_str = f"{t1} °C" if t1 is not None else "N/A"
            t2_str = f"{t2} °C" if t2 is not None else "N/A"

            print(f"[{now}]")
            print(f"  AviationWeather : {t1_str:<8}  {ts1}")
            print(f"  AVWX            : {t2_str:<8}  {ts2}")
            print()
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("Detenido.")

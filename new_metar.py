import requests
import re
import time

def start_debug_stream():
    icao = "LEMD"
    # UPDATED URL: NOAA's modern API endpoint
    url = "https://aviationweather.gov/api/data/metar"
    
    session = requests.Session()
    # Faking a standard browser to prevent automatic bot-blocking
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/plain"
    })

    print(f"Testing modern AWC connection for {icao}...")

    try:
        while True:
            params = {
                "ids": icao,
                "format": "raw",
                "_": int(time.time() * 1000) # Cache buster
            }

            try:
                # Increased timeout to 5 seconds so we don't drop slow connections while testing
                response = session.get(url, params=params, timeout=5.0)
                
                # This will trigger an HTTPError if NOAA is blocking you (e.g., Error 403)
                response.raise_for_status()
                
                metar_raw = response.text.strip()
                
                if metar_raw:
                    local_ms = time.strftime('%H:%M:%S')
                    print(f"[{local_ms}] SUCCESS | Raw: {metar_raw}")
                else:
                    print(f"[{time.strftime('%H:%M:%S')}] Connected, but NOAA returned a blank page.")
                
            except requests.exceptions.HTTPError as e:
                print(f"BLOCKED BY SERVER: {e}")
            except requests.exceptions.Timeout:
                print("TIMEOUT: NOAA took longer than 5 seconds to respond.")
            except requests.exceptions.RequestException as e:
                print(f"NETWORK ERROR: {e}")

            time.sleep(5) 

    except KeyboardInterrupt:
        print("\nTest stopped.")

if __name__ == "__main__":
    start_debug_stream()
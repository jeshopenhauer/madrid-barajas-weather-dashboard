import requests
from datetime import datetime
from math import inf
import time


def get_current_temperature_barajas(max_retries: int = 3, retry_delay: float = 2.0):
    """Devuelve SOLO la temperatura actual (hora más cercana) en Madrid-Barajas.

    Pensado para trading: usa la hora horaria más cercana al momento actual.
    """

    url = (
        "https://api.open-meteo.com/v1/forecast"
        "?latitude=40.4908&longitude=-3.5638"
        "&hourly=temperature_2m"
        "&timezone=Europe%2FMadrid"
    )

    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            current_temp = None
            current_time_api = None

            if (
                "hourly" in data
                and data["hourly"].get("temperature_2m")
                and data["hourly"].get("time")
            ):
                times_str = data["hourly"]["time"]
                temps = data["hourly"]["temperature_2m"]

                now = datetime.now()
                best_idx = None
                best_diff = inf

                for i, ts in enumerate(times_str):
                    try:
                        dt = datetime.fromisoformat(ts)
                    except ValueError:
                        continue
                    diff = abs((dt - now).total_seconds())
                    if diff < best_diff:
                        best_diff = diff
                        best_idx = i

                if best_idx is not None:
                    current_temp = temps[best_idx]
                    current_time_api = datetime.fromisoformat(times_str[best_idx])

            if current_time_api is None:
                current_time_api = datetime.now()

            return {
                "current_temperature": current_temp,
                "current_temperature_time": current_time_api.isoformat(),
            }

        except requests.exceptions.RequestException as e:
            last_error = e
            print(
                f"Intento {attempt}/{max_retries} – error al llamar a Open-Meteo: {e}"
            )
            if attempt == max_retries:
                break
            time.sleep(retry_delay)

    return {
        "current_temperature": None,
        "current_temperature_time": None,
        "error": str(last_error) if last_error else "unknown_error",
    }


if __name__ == "__main__":
    # Ejemplo rápido de uso
    data = get_current_temperature_barajas()
    print(data)
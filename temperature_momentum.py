#!/usr/bin/env python3
"""
Dashboard de Momentum de Temperatura - Análisis Técnico para Polymarket
Mercado: Temperatura Máxima Madrid Barajas (LEMD)
"""

import os
import json
import time
import sys
import warnings
import requests
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import matplotlib.gridspec as gridspec
from datetime import datetime, timedelta
from scipy.signal import savgol_filter
from scipy.interpolate import interp1d

sys.stdout.reconfigure(line_buffering=True)
warnings.filterwarnings('ignore')

# ──────────────────────────────────────────────
#  CONFIGURACIÓN
# ──────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
GRAPHS_DIR = os.path.join(BASE_DIR, "polymarket_graphs")
os.makedirs(GRAPHS_DIR, exist_ok=True)

COLLECT_INTERVAL = 20
SAVGOL_WINDOW    = 11
SAVGOL_WINDOW_WC = 7
POLY_DEGREE      = 4
RESAMPLE_DT      = 1.0   # minutos

COLORS = {
    'weather_com': "#FF0000",
    'pws1':        "#09FF00",
    'pws2':        "#0044FF",
}
LABELS = {
    'weather_com': 'Weather.com (ICAO LEMD)',
    'pws1':        'IMADRI133 (PWS)',
    'pws2':        'IMADRI265 (PWS)',
}
SOURCE_ORDER = ['weather_com', 'pws1', 'pws2']


# ──────────────────────────────────────────────
#  RECOLECTOR DE DATOS
# ──────────────────────────────────────────────
class TemperatureDataCollector:

    def __init__(self):
        self.api_key = "e1f10a1e78da46f5b10a1e78da96f525"

        self.weather_url    = "https://api.weather.com/v3/wx/observations/current"
        self.weather_params = {
            "apiKey": self.api_key, "icaoCode": "LEMD",
            "units": "m", "language": "es-ES", "format": "json",
        }

        self.pws_url = "https://api.weather.com/v2/pws/observations/current"
        self.pws_params = {
            "IMADRI133": {"apiKey": self.api_key, "stationId": "IMADRI133",
                          "units": "m", "format": "json", "numericPrecision": "decimal"},
            "IMADRI265": {"apiKey": self.api_key, "stationId": "IMADRI265",
                          "units": "m", "format": "json", "numericPrecision": "decimal"},
        }

        self.history: dict[str, list[dict]] = {s: [] for s in SOURCE_ORDER}

    def _fetch_weather_com(self):
        try:
            r = requests.get(self.weather_url, params=self.weather_params, timeout=6)
            r.raise_for_status()
            d    = r.json()
            temp = d.get("temperature")
            ts   = d.get("validTimeLocal")
            if temp is None:
                return None
            return {'time': _parse_timestamp(ts), 'temp': float(temp)}
        except Exception:
            return None

    def _fetch_pws(self, station_id: str):
        try:
            r = requests.get(self.pws_url, params=self.pws_params[station_id], timeout=6)
            r.raise_for_status()
            obs = r.json().get('observations', [])
            if not obs:
                return None
            o    = obs[0]
            temp = o.get('metric', {}).get('temp')
            ts   = o.get('obsTimeLocal')
            if temp is None:
                return None
            return {'time': _parse_timestamp(ts), 'temp': float(temp)}
        except Exception:
            return None

    def collect(self):
        return {
            'weather_com': self._fetch_weather_com(),
            'pws1':        self._fetch_pws("IMADRI133"),
            'pws2':        self._fetch_pws("IMADRI265"),
        }

    def add_to_history(self, readings: dict):
        """
        Añade lecturas evitando duplicados.
        Umbral: 15s para PWS/Weather (actualizan ~20-60s).
        """
        thresholds = {
            'weather_com': 15,
            'pws1':        15,
            'pws2':        15,
        }
        for source, data in readings.items():
            if data is None or data['temp'] is None:
                continue
            hist = self.history[source]
            thr  = thresholds.get(source, 15)
            if hist and abs((data['time'] - hist[-1]['time']).total_seconds()) < thr:
                continue
            hist.append(data)

    def save_json(self):
        today = datetime.now().strftime("%Y-%m-%d")
        path  = os.path.join(GRAPHS_DIR, f"history_{today}.json")
        out   = {
            src: [{'time': d['time'].strftime('%Y-%m-%d %H:%M:%S'), 'temp': d['temp']}
                  for d in lst]
            for src, lst in self.history.items()
        }
        with open(path, 'w') as f:
            json.dump(out, f, indent=2)

    def load_json(self):
        today = datetime.now().strftime("%Y-%m-%d")
        path  = os.path.join(GRAPHS_DIR, f"history_{today}.json")
        if not os.path.exists(path):
            return
        with open(path) as f:
            raw = json.load(f)
        for src, lst in raw.items():
            if src not in self.history:
                continue
            self.history[src] = [
                {'time': datetime.strptime(d['time'], '%Y-%m-%d %H:%M:%S'),
                 'temp': d['temp']}
                for d in lst
            ]
        counts = {s: len(self.history[s]) for s in SOURCE_ORDER}
        print(f"[LOAD] Histórico cargado: { {k:v for k,v in counts.items() if v>0} }")


# ──────────────────────────────────────────────
#  UTILIDADES MATEMÁTICAS
# ──────────────────────────────────────────────

def _parse_timestamp(ts) -> datetime:
    if isinstance(ts, str):
        for fmt in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%H:%M'):
            try:
                if fmt == '%H:%M':
                    h, m = map(int, ts.split(':'))
                    return datetime.now().replace(hour=h, minute=m,
                                                  second=0, microsecond=0)
                return datetime.strptime(ts, fmt)
            except Exception:
                continue
    return datetime.now()


def _to_minutes(times: list) -> np.ndarray:
    t0 = times[0]
    return np.array([(t - t0).total_seconds() / 60.0 for t in times])


def resample_uniform(times: list, temps: np.ndarray, dt_min: float = RESAMPLE_DT):
    """Interpola a grid temporal uniforme (spline cúbico, fallback lineal)."""
    t_mins = _to_minutes(times)
    span   = t_mins[-1] - t_mins[0]
    if span < dt_min * 2:
        return None, None
    t_uniform = np.arange(t_mins[0], t_mins[-1], dt_min)
    if len(t_uniform) < 2:
        return None, None
    try:
        kind = 'cubic' if len(t_mins) >= 4 else 'linear'
        interp    = interp1d(t_mins, temps, kind=kind, fill_value='extrapolate')
        T_uniform = interp(t_uniform)
    except Exception:
        try:
            interp    = interp1d(t_mins, temps, kind='linear', fill_value='extrapolate')
            T_uniform = interp(t_uniform)
        except Exception:
            return None, None
    t0            = times[0]
    times_uniform = [t0 + timedelta(minutes=float(m)) for m in t_uniform]
    return times_uniform, T_uniform


def savgol_derivative(times: list, temps: np.ndarray,
                      window: int, poly_order: int = 3):
    """dT/dt con Savitzky-Golay sobre grid uniforme. Resultado en °C/min."""
    times_u, temps_u = resample_uniform(times, temps)
    if times_u is None or len(temps_u) < poly_order + 2:
        return [], []
    # window debe ser impar y <= len(temps_u)
    n   = len(temps_u)
    win = min(window, n)
    if win % 2 == 0:
        win -= 1
    if win < poly_order + 2:
        win = poly_order + 2 if (poly_order + 2) % 2 == 1 else poly_order + 3
    if win > n:
        return [], []
    try:
        mom = savgol_filter(temps_u, window_length=win,
                            polyorder=poly_order, deriv=1, delta=RESAMPLE_DT)
        return times_u, mom
    except Exception:
        return [], []


# ──────────────────────────────────────────────
#  GENERADOR DE GRÁFICOS
# ──────────────────────────────────────────────

def _style_ax(ax, title: str, ylabel: str):
    """Aplica estilo oscuro tipo trading a un eje."""
    ax.set_facecolor('#161b22')
    ax.set_title(title, color='white', fontsize=11, fontweight='bold', pad=6)
    ax.set_ylabel(ylabel, color='#aaaaaa', fontsize=9)
    ax.tick_params(axis='both', colors='#aaaaaa', labelsize=8)
    for spine in ax.spines.values():
        spine.set_color('#30363d')
        spine.set_visible(True)
    ax.grid(True, color='#30363d', linewidth=0.6, linestyle='--', alpha=0.7)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.xaxis.set_major_locator(mdates.MinuteLocator(byminute=range(0, 60, 30)))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins=5))
    ax.legend(loc='upper left', fontsize=7.5,
              facecolor='#161b22', edgecolor='#30363d',
              labelcolor='white', framealpha=0.85)


def generate_dashboard(collector: TemperatureDataCollector):
    sources_ok = [s for s in SOURCE_ORDER if len(collector.history[s]) >= 3]
    if not sources_ok:
        print("  ⚠ No hay suficientes datos aún (mínimo 3 puntos por fuente).")
        return

    fig = plt.figure(figsize=(16, 10), dpi=100)
    fig.patch.set_facecolor('#0d1117')
    gs = gridspec.GridSpec(2, 1, hspace=0.35, figure=fig)

    ax_temp = fig.add_subplot(gs[0])
    ax_sg   = fig.add_subplot(gs[1], sharex=ax_temp)

    # Máximo de Weather.com (resuelve el mercado)
    wc_hist    = collector.history.get('weather_com', [])
    wc_max     = max((d['temp'] for d in wc_hist), default=None)
    wc_current = wc_hist[-1]['temp'] if wc_hist else None

    for source in SOURCE_ORDER:
        hist = collector.history[source]
        if len(hist) < 3:
            continue

        times = [d['time'] for d in hist]
        temps = np.array([d['temp'] for d in hist])
        color = COLORS[source]
        label = LABELS[source]

        t_max_idx  = int(np.argmax(temps))
        t_max_val  = temps[t_max_idx]
        t_max_time = times[t_max_idx]

        # Panel 1 — Temperatura
        ax_temp.plot(times, temps, '-', color=color, label=label,
                     linewidth=1.8, alpha=0.9)
        ax_temp.plot(t_max_time, t_max_val, 'v', color=color,
                     markersize=8, zorder=5)

        # Panel 2 — dT/dt Savitzky-Golay
        win = SAVGOL_WINDOW if source in ('pws1', 'pws2') else SAVGOL_WINDOW_WC
        sg_times, sg_mom = savgol_derivative(times, temps, window=win, poly_order=3)
        if len(sg_times) > 1:
            ax_sg.plot(sg_times, sg_mom, '-', color=color,
                       label=label, linewidth=1.8, alpha=0.88)

    # Línea del máximo Weather.com (strike del mercado)
    if wc_max is not None:
        ax_temp.axhline(wc_max, color='#FF6666', linewidth=1.2,
                        linestyle='--', alpha=0.7,
                        label=f'Máx Weather.com: {wc_max:.0f}°C')

    # Líneas de cero en paneles de momentum
    ax_sg.axhline(0, color='#ffffff', linewidth=0.8, linestyle='-', alpha=0.35)

    # Aplicar estilos
    _style_ax(ax_temp, "Temperatura  (°C)", "°C")
    _style_ax(ax_sg,   "Momentum  dT/dt  Savitzky-Golay  (°C/min)", "°C/min")

    ax_sg.set_xlabel("Hora  (UTC+1)", color='#aaaaaa',
                     fontsize=9, fontweight='bold')

    # Título principal
    now_str = datetime.now().strftime('%Y-%m-%d  %H:%M:%S')
    wc_str  = f"{wc_current:.0f}°C" if wc_current is not None else "—"
    max_str = f"{wc_max:.0f}°C"     if wc_max     is not None else "—"
    fig.suptitle(
        f"Polymarket  ·  Temperatura Máxima Madrid Barajas (LEMD)\n"
        f"Weather.com actual: {wc_str}   |   Máx. del día: {max_str}   |   {now_str}",
        color='white', fontsize=13, fontweight='bold', y=0.998
    )

    out = os.path.join(GRAPHS_DIR, "momentum_dashboard.png")
    plt.savefig(out, dpi=100, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    print(f"  ✅ Dashboard guardado → {out}")

    _print_summary(collector, wc_max)


def _print_summary(collector: TemperatureDataCollector, wc_max):
    print(f"\n{'─'*72}")
    print(f"  {'FUENTE':<26}  {'T_act':>6}  {'T_max':>6}  {'dT/dt SG':>10}  Tendencia")
    print(f"{'─'*72}")
    for source in SOURCE_ORDER:
        hist = collector.history[source]
        if len(hist) < 3:
            print(f"  {LABELS[source]:<26}  sin datos suficientes")
            continue
        times     = [d['time'] for d in hist]
        temps     = np.array([d['temp'] for d in hist])
        t_actual  = temps[-1]
        t_max_day = np.max(temps)
        win       = SAVGOL_WINDOW if source in ('pws1','pws2') else SAVGOL_WINDOW_WC
        sg_t, sg_m = savgol_derivative(times, temps, window=win, poly_order=3)
        mom = sg_m[-1] if len(sg_m) > 0 else float('nan')
        trend = "▲ SUBE" if mom > 0.02 else ("▼ BAJA" if mom < -0.02 else "→ PLANA")
        print(f"  {LABELS[source]:<26}  {t_actual:>5.2f}°  {t_max_day:>5.1f}°  "
              f"  {mom:>+8.4f}  {trend}")
    if wc_max is not None:
        print(f"\n  🔴 Resolución mercado (Weather.com máx): {wc_max:.0f}°C")
    print(f"{'─'*72}\n")


# ──────────────────────────────────────────────
#  MAIN
# ──────────────────────────────────────────────

def main():
    print(f"\n{'═'*70}")
    print(f"  POLYMARKET TEMPERATURE MOMENTUM DASHBOARD")
    print(f"  Madrid Barajas (LEMD)  ·  Intervalo: {COLLECT_INTERVAL}s")
    print(f"{'═'*70}\n")

    collector = TemperatureDataCollector()
    collector.load_json()

    update_count = 0
    try:
        while True:
            t_start  = time.time()
            readings = collector.collect()
            collector.add_to_history(readings)
            collector.save_json()

            n_ok = sum(1 for v in readings.values() if v is not None)
            update_count += 1
            print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                  f"#{update_count}  |  {n_ok}/4 APIs OK  |  generando dashboard…")

            generate_dashboard(collector)

            elapsed = time.time() - t_start
            time.sleep(max(0.0, COLLECT_INTERVAL - elapsed))

    except KeyboardInterrupt:
        print("\n  Bot detenido.\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
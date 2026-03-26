#!/usr/bin/env python3
"""
Dashboard principal - Madrid Barajas Weather Monitor
Layout:
  ┌─────────────────────┬─────────────────────┐
  │   VS TEMPERATURAS   │  < IMÁGENES SAT >   │
  ├─────────────────────┴─────────────────────┤
  │              TERMINAL                      │
  └────────────────────────────────────────────┘
"""

import tkinter as tk
from tkinter import ttk, font
import threading
import subprocess
import queue
import os
import sys
import time
from datetime import datetime, timedelta
from PIL import Image, ImageTk
import requests
import re
import io
import matplotlib
matplotlib.use('Agg')  # Sin ventana, renderizar en memoria
import matplotlib.pyplot as plt
import matplotlib.figure as mfigure
from matplotlib.backends.backend_agg import FigureCanvasAgg

# ─── Rutas ───────────────────────────────────────────────────────────────────
# Cuando el script corre empaquetado por PyInstaller, los datos se extraen en
# `sys._MEIPASS`. Usar ese directorio como BASE_DIR en modo "frozen".
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SAT_DIR = os.path.join(BASE_DIR, "satellite_images")

SAT_TYPES = [
    ("infrarrojo",  "satellite_images/infrarrojo/infrarrojo_latest.png",   "🛰️ Infrarrojo (IR)"),
    ("vapor_agua",  "satellite_images/vapor_agua/vapor_agua_latest.png",    "💨 Vapor de Agua"),
    ("masas_aire",  "satellite_images/masas_aire/masas_aire_latest.png",    "🌈 Masas de Aire"),
    ("visible_ir",  "satellite_images/visible_ir/visible_ir_latest.png",    "👁️ Visible / IR"),
    ("masas_aire_gif", "satellite_images/masas_aire_gif/masas_aire_gif_latest.gif", "🎬 Masas de Aire (GIF)"),
    ("visible_gif",    "satellite_images/visible_gif/visible_gif_latest.gif",       "🎬 Visible (GIF)"),
]

# ─── Cola de logs ─────────────────────────────────────────────────────────────
log_queue = queue.Queue()


# ══════════════════════════════════════════════════════════════════════════════
#  Helpers de datos
# ══════════════════════════════════════════════════════════════════════════════

def get_temp_data_from_meteociel(date):
    """Extrae datos de temperatura del HTML de Meteociel (lógica de vstemperaturas.py)"""
    base_url = "https://www.meteociel.fr/temps-reel/obs_villes.php"
    code     = "8221"
    headers  = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    url      = f"{base_url}?code2={code}&jour2={date.day}&mois2=2&annee2={date.year}"

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'ISO-8859-1'
        if response.status_code != 200:
            return {}

        pattern = r"src=['\"]//static\.meteociel\.fr/cartes_obs/graphe2\.php\?type=0&([^'\"]+)['\"]"
        match   = re.search(pattern, response.text)
        if not match:
            return {}

        params_str  = match.group(1)
        data_pattern = r'data([\d.]+)=([\d.-]+)'
        matches      = re.findall(data_pattern, params_str)
        if not matches:
            return {}

        temp_data = {}
        for hour_str, temp_str in matches:
            hour_utc  = float(hour_str)
            temp      = float(temp_str)
            hour_local = (hour_utc + 1) % 24   # UTC+1
            temp_data[hour_local] = temp
        return temp_data
    except Exception:
        return {}


def build_temp_figure(width_px, height_px):
    """Genera la figura matplotlib de comparación de temperaturas y la devuelve como PIL Image."""
    today     = datetime.now()
    yesterday = today - timedelta(days=1)

    today_data     = get_temp_data_from_meteociel(today)
    yesterday_data = get_temp_data_from_meteociel(yesterday)

    dpi = 96
    fig = mfigure.Figure(figsize=(width_px / dpi, height_px / dpi), dpi=dpi)
    ax  = fig.add_subplot(111)

    if yesterday_data:
        h = sorted(yesterday_data.keys())
        t = [yesterday_data[x] for x in h]
        ax.plot(h, t, 'o-', color='#FF6B6B', linewidth=2.5, markersize=5,
                label=f'Ayer {yesterday.strftime("%d/%m")} ({len(t)} pts)', alpha=0.85)

    if today_data:
        h = sorted(today_data.keys())
        t = [today_data[x] for x in h]
        ax.plot(h, t, 'o-', color='#4ECDC4', linewidth=2.5, markersize=5,
                label=f'Hoy {today.strftime("%d/%m")} ({len(t)} pts)', alpha=0.85)
        if t:
            last_h, last_t = h[-1], t[-1]
            last_hh = int(last_h)
            last_mm = int((last_h % 1) * 60)
            ax.plot(last_h, last_t, 'o', color='#FFD700', markersize=12,
                    markeredgecolor='black', markeredgewidth=2,
                    label=f'Última: {last_t:.1f}°C a las {last_hh:02d}:{last_mm:02d}',
                    zorder=5)
            # Etiqueta con coordenadas pegada al punto
            ax.annotate(
                f'{last_t:.1f}°C\n{last_hh:02d}:{last_mm:02d}h',
                xy=(last_h, last_t),
                xytext=(10, 8),          # desplazamiento en puntos
                textcoords='offset points',
                fontsize=8,
                fontweight='bold',
                color='#FFD700',
                bbox=dict(boxstyle='round,pad=0.3', fc='#1e1e2e', ec='#FFD700', alpha=0.85),
                arrowprops=dict(arrowstyle='->', color='#FFD700', lw=1.2),
                zorder=6,
            )

    ax.set_xlabel('Hora (Madrid UTC+1)', fontsize=9)
    ax.set_ylabel('Temperatura (°C)', fontsize=9)
    ax.set_title(f'VS Temperaturas - Barajas\nAyer vs Hoy', fontsize=10, fontweight='bold')
    ax.legend(loc='best', fontsize=8, framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xlim(0, 24)
    ax.set_xticks(range(0, 25, 2))
    ax.set_xticklabels([f'{h:02d}h' for h in range(0, 25, 2)], fontsize=7)

    all_temps = list(yesterday_data.values()) + list(today_data.values())
    if all_temps:
        mn, mx = min(all_temps), max(all_temps)
        margin = (mx - mn) * 0.12 or 1
        y_min = mn - margin
        y_max = mx + margin
        ax.set_ylim(y_min, y_max)
        # Marcas cada 0.5 °C
        import math
        y_start = math.floor(y_min * 2) / 2   # redondear hacia abajo al 0.5 más cercano
        y_end   = math.ceil(y_max  * 2) / 2   # redondear hacia arriba al 0.5 más cercano
        yticks  = []
        v = y_start
        while v <= y_end + 0.001:
            yticks.append(round(v, 1))
            v += 0.5
        ax.set_yticks(yticks)
        ax.set_yticklabels([f'{t:.1f}' for t in yticks], fontsize=7)
        ax.yaxis.grid(True, which='both', alpha=0.25, linestyle='--')

    fig.tight_layout()

    canvas = FigureCanvasAgg(fig)
    canvas.draw()
    buf = canvas.buffer_rgba()
    pil_img = Image.frombytes('RGBA', canvas.get_width_height(), buf)
    plt.close(fig)
    return pil_img


# ══════════════════════════════════════════════════════════════════════════════
#  Dashboard
# ══════════════════════════════════════════════════════════════════════════════

class Dashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🌤️  Madrid Barajas - Weather Dashboard")
        self.configure(bg="#1e1e2e")
        self.geometry("1600x950")
        self.minsize(1200, 800)
        self.resizable(True, True)
        # Evitar que los Label con imagen fuercen resize de la ventana
        self.pack_propagate(False)

        self._sat_index   = 0          # índice imagen satélite activa
        self._sat_photo   = None       # referencia PIL → Tk (evita GC)
        self._temp_photo  = None
        self._resize_job  = None       # job pendiente de resize
        self._gif_job     = None       # job de animación GIF
        self._gif_frames  = []         # frames del GIF animado
        self._gif_durations = []       # duraciones de cada frame
        self._gif_current_frame = 0    # frame actual del GIF

        self._build_ui()
        self._start_background_threads()
        self._poll_log_queue()         # arrancar polling de logs YA
        self.after(2000, self._schedule_refresh)  # primera carga tras 2s

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        TITLE_FG  = "#cdd6f4"
        BG        = "#1e1e2e"
        PANEL_BG  = "#181825"
        BORDER    = "#45475a"

        # ── fila superior (temperatura | satélite) ──
        top_frame = tk.Frame(self, bg=BG)
        top_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(8, 4))
        top_frame.columnconfigure(0, weight=1)
        top_frame.columnconfigure(1, weight=1)
        top_frame.rowconfigure(0, weight=1)

        # Panel izquierdo: VS TEMPERATURAS
        left_panel = tk.Frame(top_frame, bg=PANEL_BG, relief=tk.FLAT,
                              highlightbackground=BORDER, highlightthickness=1)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        self.left_panel = left_panel  # guardar referencia para medir tamaño

        tk.Label(left_panel, text="VS TEMPERATURAS",
                 bg=PANEL_BG, fg=TITLE_FG,
                 font=("Arial", 11, "bold")).pack(pady=(6, 2))

        self.temp_canvas = tk.Label(left_panel, bg=PANEL_BG,
                                    width=1, height=1)  # tamaño mínimo fijo
        self.temp_canvas.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.temp_status = tk.Label(left_panel, text="Cargando...",
                                    bg=PANEL_BG, fg="#6c7086", font=("Arial", 8))
        self.temp_status.pack(pady=(0, 4))

        # Panel derecho: IMÁGENES SATÉLITE
        right_panel = tk.Frame(top_frame, bg=PANEL_BG, relief=tk.FLAT,
                               highlightbackground=BORDER, highlightthickness=1)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        self.right_panel = right_panel  # guardar referencia para medir tamaño

        # Barra de navegación satélite
        nav_frame = tk.Frame(right_panel, bg=PANEL_BG)
        nav_frame.pack(fill=tk.X, pady=(6, 2))

        btn_style = {"bg": "#313244", "fg": TITLE_FG, "font": ("Arial", 14, "bold"),
                     "relief": tk.FLAT, "activebackground": "#45475a",
                     "activeforeground": "white", "cursor": "hand2",
                     "width": 2}

        tk.Button(nav_frame, text="〈", command=self._sat_prev, **btn_style).pack(side=tk.LEFT, padx=8)

        self.sat_title = tk.Label(nav_frame, text="IMÁGENES SATÉLITE",
                                  bg=PANEL_BG, fg=TITLE_FG,
                                  font=("Arial", 11, "bold"))
        self.sat_title.pack(side=tk.LEFT, expand=True)

        tk.Button(nav_frame, text="〉", command=self._sat_next, **btn_style).pack(side=tk.RIGHT, padx=8)

        self.sat_canvas = tk.Label(right_panel, bg=PANEL_BG,
                                   width=1, height=1)  # tamaño mínimo fijo
        self.sat_canvas.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.sat_status = tk.Label(right_panel, text="Cargando...",
                                   bg=PANEL_BG, fg="#6c7086", font=("Arial", 8))
        self.sat_status.pack(pady=(0, 4))

        # ── fila inferior: TERMINAL ──
        term_frame = tk.Frame(self, bg=PANEL_BG,
                              highlightbackground=BORDER, highlightthickness=1)
        term_frame.pack(fill=tk.BOTH, expand=False, padx=8, pady=(4, 8))

        tk.Label(term_frame, text="TERMINAL — polymarket_bot",
                 bg=PANEL_BG, fg=TITLE_FG,
                 font=("Arial", 10, "bold")).pack(anchor="w", padx=8, pady=(4, 0))

        self.terminal = tk.Text(
            term_frame,
            height=15,
            bg="#11111b", fg="#cdd6f4",
            font=("Courier New", 9),
            relief=tk.FLAT,
            insertbackground="white",
            state=tk.DISABLED,
            wrap=tk.WORD,
        )
        self.terminal.pack(fill=tk.BOTH, expand=True, padx=6, pady=(2, 6))

        # Scrollbar
        vsb = ttk.Scrollbar(term_frame, orient="vertical", command=self.terminal.yview)
        self.terminal["yscrollcommand"] = vsb.set
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # Tags de color para el terminal
        self.terminal.tag_config("ok",    foreground="#a6e3a1")
        self.terminal.tag_config("error", foreground="#f38ba8")
        self.terminal.tag_config("info",  foreground="#89b4fa")
        self.terminal.tag_config("warn",  foreground="#fab387")

    # ── Satélite ──────────────────────────────────────────────────────────────

    def _sat_prev(self):
        self._sat_index = (self._sat_index - 1) % len(SAT_TYPES)
        self._refresh_satellite_display()

    def _sat_next(self):
        self._sat_index = (self._sat_index + 1) % len(SAT_TYPES)
        self._refresh_satellite_display()

    def _refresh_satellite_display(self):
        key, path, label = SAT_TYPES[self._sat_index]
        full_path = os.path.join(BASE_DIR, path)

        self.sat_title.config(text=f"{label}  [{self._sat_index+1}/{len(SAT_TYPES)}]")

        if not os.path.exists(full_path):
            self.sat_status.config(text=f"⚠️  Imagen no encontrada: {path}")
            self.sat_canvas.config(image='', text="Sin imagen", fg="#f38ba8")
            return

        try:
            # Detener animación previa si existe
            if hasattr(self, '_gif_job') and self._gif_job:
                self.after_cancel(self._gif_job)
                self._gif_job = None

            # Usar el panel como referencia, no el Label (evita bucle de crecimiento)
            w = self.right_panel.winfo_width()  - 16
            h = self.right_panel.winfo_height() - 70
            if w < 50: w = 480
            if h < 50: h = 380

            # Detectar si es GIF animado
            is_gif = full_path.lower().endswith('.gif')
            
            if is_gif:
                # Cargar GIF y extraer frames
                img = Image.open(full_path)
                self._gif_frames = []
                self._gif_durations = []
                
                try:
                    frame_idx = 0
                    while True:
                        img.seek(frame_idx)
                        # Redimensionar frame
                        frame = img.copy().convert("RGBA")
                        frame = frame.resize((w, h), Image.LANCZOS)
                        photo = ImageTk.PhotoImage(frame)
                        self._gif_frames.append(photo)
                        # Duración del frame (por defecto 100ms si no está definida)
                        duration = img.info.get('duration', 100)
                        self._gif_durations.append(duration)
                        frame_idx += 1
                except EOFError:
                    pass  # Fin de frames
                
                if self._gif_frames:
                    self._gif_current_frame = 0
                    self._animate_gif()
                    mtime = datetime.fromtimestamp(os.path.getmtime(full_path))
                    self.sat_status.config(
                        text=f"Actualizado: {mtime.strftime('%H:%M:%S')}  |  {os.path.getsize(full_path)//1024} KB  |  {len(self._gif_frames)} frames"
                    )
                else:
                    self.sat_status.config(text="❌ GIF sin frames")
            else:
                # Imagen estática (PNG)
                img   = Image.open(full_path).convert("RGB")
                img   = img.resize((w, h), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)

                self._sat_photo = photo
                self.sat_canvas.config(image=photo, text="")

                mtime = datetime.fromtimestamp(os.path.getmtime(full_path))
                self.sat_status.config(text=f"Actualizado: {mtime.strftime('%H:%M:%S')}  |  {os.path.getsize(full_path)//1024} KB")
                
        except Exception as e:
            self.sat_status.config(text=f"❌ Error: {e}")

    def _animate_gif(self):
        """Anima el GIF cambiando de frame"""
        if not hasattr(self, '_gif_frames') or not self._gif_frames:
            return
        
        # Mostrar frame actual
        photo = self._gif_frames[self._gif_current_frame]
        self.sat_canvas.config(image=photo, text="")
        self._sat_photo = photo  # Mantener referencia
        
        # Programar siguiente frame
        duration = self._gif_durations[self._gif_current_frame]
        self._gif_current_frame = (self._gif_current_frame + 1) % len(self._gif_frames)
        self._gif_job = self.after(duration, self._animate_gif)

    # ── Temperaturas ──────────────────────────────────────────────────────────

    def _do_temp_refresh_async(self):
        """Genera el gráfico en hilo aparte para no bloquear la UI."""
        def worker():
            try:
                w = max(self.left_panel.winfo_width()  - 16, 560)
                h = max(self.left_panel.winfo_height() - 60, 380)
                pil_img = build_temp_figure(w, h)
                pil_img = pil_img.convert("RGB").resize((w, h), Image.LANCZOS)
                photo   = ImageTk.PhotoImage(pil_img)
                self.after(0, lambda: self._apply_temp_photo(photo))
            except Exception as e:
                self.after(0, lambda msg=str(e): self.temp_status.config(text=f"❌ {msg}"))

        threading.Thread(target=worker, daemon=True).start()

    def _apply_temp_photo(self, photo):
        self._temp_photo = photo
        self.temp_canvas.config(image=photo, text="")
        self.temp_status.config(text=f"Actualizado: {datetime.now().strftime('%H:%M:%S')}")

    # ── Terminal ──────────────────────────────────────────────────────────────

    def _append_terminal(self, text):
        self.terminal.config(state=tk.NORMAL)

        # Colorear según contenido
        if "✅" in text or "OK" in text.upper():
            tag = "ok"
        elif "❌" in text or "Error" in text.lower():
            tag = "error"
        elif "🔄" in text or "Actualizando" in text:
            tag = "warn"
        else:
            tag = "info"

        self.terminal.insert(tk.END, text + "\n", tag)

        # Limitar a 300 líneas para no crecer indefinidamente
        lines = int(self.terminal.index('end-1c').split('.')[0])
        if lines > 300:
            self.terminal.delete('1.0', f'{lines - 300}.0')

        self.terminal.see(tk.END)
        self.terminal.config(state=tk.DISABLED)

    def _poll_log_queue(self):
        """Vacía la cola de logs y los escribe en el terminal."""
        while not log_queue.empty():
            try:
                line = log_queue.get_nowait()
                self._append_terminal(line)
            except queue.Empty:
                break
        self.after(300, self._poll_log_queue)

    # ── Hilos de fondo ────────────────────────────────────────────────────────

    def _start_background_threads(self):
        # Hilo para polymarket_bot
        t = threading.Thread(target=self._run_polymarket_bot, daemon=True)
        t.start()

        # Hilo para satellite_images
        t2 = threading.Thread(target=self._run_satellite_downloader, daemon=True)
        t2.start()

    def _run_polymarket_bot(self):
        """Corre polymarket_bot.py como subprocess y captura su stdout."""
        script = os.path.join(BASE_DIR, "polymarket_bot.py")
        log_queue.put(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 Iniciando polymarket_bot...")
        try:
            proc = subprocess.Popen(
                [sys.executable, "-u", script],   # -u = unbuffered
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=0,                         # sin buffer
                cwd=BASE_DIR,
                env={**os.environ, "PYTHONUNBUFFERED": "1"},
            )
            for line in iter(proc.stdout.readline, ''):
                line = line.rstrip()
                if line:
                    log_queue.put(line)
            proc.stdout.close()
            proc.wait()
            log_queue.put(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  polymarket_bot terminó (código {proc.returncode})")
        except Exception as e:
            log_queue.put(f"❌ Error ejecutando polymarket_bot: {e}")

    def _run_satellite_downloader(self):
        """Corre satellite_images.py como subprocess y captura su stdout."""
        script = os.path.join(BASE_DIR, "satellite_images.py")
        log_queue.put(f"[{datetime.now().strftime('%H:%M:%S')}] 🛰️  Iniciando satellite_images...")
        try:
            proc = subprocess.Popen(
                [sys.executable, script],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=BASE_DIR,
            )
            for line in iter(proc.stdout.readline, ''):
                line = line.rstrip()
                if line:
                    log_queue.put(line)
            proc.stdout.close()
            proc.wait()
            log_queue.put(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  satellite_images terminó (código {proc.returncode})")
        except Exception as e:
            log_queue.put(f"❌ Error ejecutando satellite_images: {e}")

    # ── Refresh periódico ─────────────────────────────────────────────────────

    def _schedule_sat_refresh(self):
        """Refresca imágenes satélite cada 5 minutos."""
        self._refresh_satellite_display()
        self.after(300_000, self._schedule_sat_refresh)   # cada 5 minutos

    def _schedule_temp_refresh(self):
        """Refresca la gráfica de temperatura cada 20 segundos."""
        self._do_temp_refresh_async()
        self.after(20_000, self._schedule_temp_refresh)   # cada 20 segundos

    def _schedule_refresh(self):
        """Arranca los dos ciclos de refresco independientes."""
        self._schedule_sat_refresh()
        self._schedule_temp_refresh()


# ══════════════════════════════════════════════════════════════════════════════

def main():
    # Verificar dependencias
    try:
        from PIL import Image
    except ImportError:
        print("❌ Falta Pillow: pip install Pillow")
        sys.exit(1)

    app = Dashboard()
    app.mainloop()


if __name__ == "__main__":
    main()

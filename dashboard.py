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
from tkinter import ttk
import threading
import subprocess
import queue
import os
import sys
from datetime import datetime, timedelta
from PIL import Image, ImageTk
import requests
import re
import matplotlib
matplotlib.use('Agg')  # Sin ventana, renderizar en memoria
import matplotlib.figure as mfigure
import matplotlib.ticker as ticker
from matplotlib.backends.backend_agg import FigureCanvasAgg

# ─── Rutas ───────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))

SAT_TYPES = [
    ("infrarrojo_sp",  "satellite_images/infrarrojo_sp/infrarrojo_sp_latest.png",   "Infrarrojo España"),
    ("infrarrojo_eu",  "satellite_images/infrarrojo_eu/infrarrojo_eu_latest.png",   "Infrarrojo Europa"),
    ("vapor_agua_sp",  "satellite_images/vapor_agua_sp/vapor_agua_sp_latest.png",   "Vapor de Agua España"),
    ("vapor_agua_eu",  "satellite_images/vapor_agua_eu/vapor_agua_eu_latest.png",   "Vapor de Agua Europa"),
    ("masas_aire_sp",  "satellite_images/masas_aire_sp/masas_aire_sp_latest.png",   "Masas de Aire España"),
    ("masas_aire_eu",  "satellite_images/masas_aire_eu/masas_aire_eu_latest.png",   "Masas de Aire Europa"),
    ("visible_sp",     "satellite_images/visible_sp/visible_sp_latest.png",         "Visible España"),
    ("visible_eu",     "satellite_images/visible_eu/visible_eu_latest.png",         "Visible Europa"),
]

# ─── Cola de logs ─────────────────────────────────────────────────────────────
log_queue = queue.Queue()


# ══════════════════════════════════════════════════════════════════════════════
#  Helpers de datos
# ══════════════════════════════════════════════════════════════════════════════

def get_temp_data_from_meteociel(date, custom_month=None):
    """Extrae datos de temperatura del HTML de Meteociel"""
    base_url = "https://www.meteociel.fr/temps-reel/obs_villes.php"
    code     = "8221"
    headers  = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    # Calcular el mes de Meteociel automáticamente
    # Meteociel usa formato 0-11: mois2=0 (enero), mois2=1 (febrero), ..., mois2=11 (diciembre)
    if custom_month is not None:
        # custom_month viene en formato normal (1-12), convertir a formato Meteociel (0-11)
        meteociel_month = custom_month - 1
    else:
        # Usar el mes de la fecha (restar 1 para formato Meteociel)
        meteociel_month = date.month - 1
    
    url = f"{base_url}?code2={code}&jour2={date.day}&mois2={meteociel_month}&annee2={date.year}"

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
        temp_data[hour_utc] = temp
    return temp_data

def build_temp_figure(width_px, height_px, custom_day=None, custom_month=None):
    """Genera la figura matplotlib de comparación de temperaturas y la devuelve como PIL Image."""
    today     = datetime.now()
    yesterday = today - timedelta(days=1)

    today_data     = get_temp_data_from_meteociel(today)
    yesterday_data = get_temp_data_from_meteociel(yesterday)
    
    # Obtener datos del día personalizado si se proporciona
    custom_data = {}
    if custom_day and custom_month:
        custom_date = datetime(today.year, custom_month, custom_day)
        custom_data = get_temp_data_from_meteociel(custom_date, custom_month)

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
            ax.plot(h[-1], t[-1], 'o', color='#FFD700', markersize=12,
                    markeredgecolor='black', markeredgewidth=2,
                    label=f'Última: {t[-1]:.1f}°C a las {int(h[-1]):02d}:{int((h[-1]%1)*60):02d}',
                    zorder=5)
    
    if custom_data:
        h = sorted(custom_data.keys())
        t = [custom_data[x] for x in h]
        ax.plot(h, t, 'o-', color='#9B59B6', linewidth=2.5, markersize=5,
                label=f'Día {custom_day:02d}/{custom_month:02d} ({len(t)} pts)', alpha=0.85)

    ax.set_xlabel('Hora (UTC)', fontsize=9)
    ax.set_ylabel('Temperatura (°C)', fontsize=9)
    title_text = f'VS Temperaturas - Barajas\nAyer vs Hoy'
    if custom_day and custom_month:
        title_text += f' vs {custom_day:02d}/{custom_month:02d}'
    ax.set_title(title_text, fontsize=10, fontweight='bold')
    ax.legend(loc='best', fontsize=8, framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xlim(0, 24)
    ax.set_xticks(range(0, 25, 2))
    ax.set_xticklabels([f'{h:02d}h' for h in range(0, 25, 2)], fontsize=7)

    all_temps = list(yesterday_data.values()) + list(today_data.values()) + list(custom_data.values())
    if all_temps:
        mn, mx = min(all_temps), max(all_temps)
        margin = (mx - mn) * 0.12 or 1
        ax.set_ylim(mn - margin, mx + margin)
        
        # Añadir marcas en el eje Y cada 1°C
        ax.yaxis.set_major_locator(ticker.MultipleLocator(1))
        ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.5))
        ax.grid(True, which='major', alpha=0.3, linestyle='--', linewidth=1)
        ax.grid(True, which='minor', alpha=0.15, linestyle=':', linewidth=0.5)
    else:
        ax.grid(True, alpha=0.3, linestyle='--')

    canvas = FigureCanvasAgg(fig)
    canvas.draw()
    buf = canvas.buffer_rgba()
    pil_img = Image.frombytes('RGBA', canvas.get_width_height(), buf)
    fig.clear()
    return pil_img


# ══════════════════════════════════════════════════════════════════════════════
#  Dashboard
# ══════════════════════════════════════════════════════════════════════════════

class Dashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🌤️  Madrid Barajas - Weather Dashboard")
        self.configure(bg="#1e1e2e")
        self.geometry("1400x820")
        self.minsize(1100, 700)
        self.resizable(True, True)
        # Evitar que los Label con imagen fuercen resize de la ventana
        self.pack_propagate(False)

        self._sat_index   = 0          # índice imagen satélite activa
        self._sat_photo   = None       # referencia PIL → Tk (evita GC)
        self._temp_photo  = None
        self._resize_job  = None       # job pendiente de resize
        
        # Variables para día de comparación personalizado
        self.custom_day   = tk.IntVar(value=24)   # Día a comparar
        self.custom_month = tk.IntVar(value=3)    # Mes en formato normal (1-12)
        
        # Índice para navegación entre gráficos de temperatura
        self._temp_graph_index = 0  # 0=VS Temperaturas, 1=Temperature Plot (polymarket)

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

        # ── PanedWindow vertical principal (gráficos | terminal) ──
        # Permite cambiar tamaño entre los gráficos y la terminal
        main_paned = tk.PanedWindow(self, orient="vertical",
                                    bg=BG, sashwidth=5,
                                    sashpad=3, handlesize=12)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=(8, 8))

        # ── PanedWindow horizontal superior (temperatura | satélite) ──
        # Permite arrastrabilidad entre paneles izquierdo y derecho
        top_paned = tk.PanedWindow(main_paned, orient="horizontal", 
                                   bg=BG, sashwidth=5, 
                                   sashpad=3, handlesize=12)
        main_paned.add(top_paned, height=500)

        # Panel izquierdo: VS TEMPERATURAS
        left_panel = tk.Frame(top_paned, bg=PANEL_BG, relief=tk.FLAT,
                              highlightbackground=BORDER, highlightthickness=1)
        top_paned.add(left_panel, width=700)
        self.left_panel = left_panel  # guardar referencia para medir tamaño

        # Barra de título con controles y navegación
        temp_header = tk.Frame(left_panel, bg=PANEL_BG)
        temp_header.pack(fill=tk.X, pady=(6, 2))
        
        # Botón navegación izquierda
        btn_style = {"bg": "#313244", "fg": TITLE_FG, "font": ("Arial", 14, "bold"),
                     "relief": tk.FLAT, "activebackground": "#45475a",
                     "activeforeground": "white", "cursor": "hand2",
                     "width": 2}
        
        tk.Button(temp_header, text="〈", command=self._temp_prev, **btn_style).pack(side=tk.LEFT, padx=8)
        
        # Título del gráfico (dinámico)
        self.temp_title = tk.Label(temp_header, text="VS TEMPERATURAS  [1/2]",
                 bg=PANEL_BG, fg=TITLE_FG,
                 font=("Arial", 11, "bold"))
        self.temp_title.pack(side=tk.LEFT, expand=True)
        
        # Botón navegación derecha
        tk.Button(temp_header, text="〉", command=self._temp_next, **btn_style).pack(side=tk.RIGHT, padx=8)
        
        # Controles para día personalizado (solo visible en VS Temperaturas)
        self.control_frame = tk.Frame(temp_header, bg=PANEL_BG)
        self.control_frame.pack(side=tk.RIGHT, padx=8)
        
        tk.Label(self.control_frame, text="Comparar con:",
                 bg=PANEL_BG, fg="#a6adc8", font=("Arial", 8)).pack(side=tk.LEFT, padx=(0, 4))
        
        # Spinbox para día
        day_spin = tk.Spinbox(self.control_frame, from_=1, to=31, width=3,
                             textvariable=self.custom_day,
                             bg="#313244", fg=TITLE_FG, 
                             buttonbackground="#45475a",
                             font=("Arial", 9),
                             command=self._on_custom_day_changed)
        day_spin.pack(side=tk.LEFT, padx=2)
        
        tk.Label(self.control_frame, text="/",
                 bg=PANEL_BG, fg="#a6adc8", font=("Arial", 9)).pack(side=tk.LEFT)
        
        # Spinbox para mes
        month_spin = tk.Spinbox(self.control_frame, from_=1, to=12, width=3,
                               textvariable=self.custom_month,
                               bg="#313244", fg=TITLE_FG,
                               buttonbackground="#45475a",
                               font=("Arial", 9),
                               command=self._on_custom_day_changed)
        month_spin.pack(side=tk.LEFT, padx=2)
        
        # Botón refresh
        tk.Button(self.control_frame, text="🔄", 
                 command=self._on_custom_day_changed,
                 bg="#313244", fg=TITLE_FG, font=("Arial", 10),
                 relief=tk.FLAT, cursor="hand2",
                 activebackground="#45475a", width=2).pack(side=tk.LEFT, padx=(4, 0))

        self.temp_canvas = tk.Label(left_panel, bg=PANEL_BG,
                                    width=1, height=1)  # tamaño mínimo fijo
        self.temp_canvas.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.temp_status = tk.Label(left_panel, text="Cargando...",
                                    bg=PANEL_BG, fg="#6c7086", font=("Arial", 8))
        self.temp_status.pack(pady=(0, 4))

        # Panel derecho: IMÁGENES SATÉLITE
        right_panel = tk.Frame(top_paned, bg=PANEL_BG, relief=tk.FLAT,
                               highlightbackground=BORDER, highlightthickness=1)
        top_paned.add(right_panel, width=600)
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

        # ── fila inferior: TERMINAL (en PanedWindow vertical) ──
        term_frame = tk.Frame(main_paned, bg=PANEL_BG,
                              highlightbackground=BORDER, highlightthickness=1)
        main_paned.add(term_frame, height=150)

        tk.Label(term_frame, text="TERMINAL — polymarket_bot",
                 bg=PANEL_BG, fg=TITLE_FG,
                 font=("Arial", 10, "bold")).pack(anchor="w", padx=8, pady=(4, 0))

        self.terminal = tk.Text(
            term_frame,
            height=10,
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
        
        # Evento de redimensionamiento para refrescar gráficos
        self.bind("<Configure>", self._on_window_configure)

    def _on_window_configure(self, event=None):
        """Maneja el redimensionamiento de la ventana y refresa los gráficos."""
        # Cancelar job previo si existe
        if self._resize_job:
            self.after_cancel(self._resize_job)
        
        # Programar un refresh con delay (evita múltiples refreshes mientras se arrastra)
        self._resize_job = self.after(500, self._refresh_on_resize)
    
    def _refresh_on_resize(self):
        """Refresa los gráficos cuando la ventana se redimensiona."""
        self._resize_job = None
        if self._temp_graph_index == 0:
            self._do_temp_refresh_async()
        else:
            self._load_temperature_plot()
        self._refresh_satellite_display()

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

        # Usar el panel como referencia, no el Label (evita bucle de crecimiento)
        w = self.right_panel.winfo_width()  - 16
        h = self.right_panel.winfo_height() - 70
        if w < 50: w = 480
        if h < 50: h = 380

        img   = Image.open(full_path).convert("RGB")
        img   = img.resize((w, h), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)

        self._sat_photo = photo
        self.sat_canvas.config(image=photo, text="")

        mtime = datetime.fromtimestamp(os.path.getmtime(full_path))
        self.sat_status.config(text=f"Actualizado: {mtime.strftime('%H:%M:%S')}  |  {os.path.getsize(full_path)//1024} KB")

    # ── Temperaturas ──────────────────────────────────────────────────────────

    def _temp_prev(self):
        """Navegar al gráfico de temperatura anterior"""
        self._temp_graph_index = (self._temp_graph_index - 1) % 2
        self._refresh_temp_display()
    
    def _temp_next(self):
        """Navegar al siguiente gráfico de temperatura"""
        self._temp_graph_index = (self._temp_graph_index + 1) % 2
        self._refresh_temp_display()
    
    def _refresh_temp_display(self):
        """Actualiza el gráfico de temperatura mostrado según el índice"""
        if self._temp_graph_index == 0:
            # Gráfico VS Temperaturas (generado por build_temp_figure)
            self.temp_title.config(text="VS TEMPERATURAS  [1/2]")
            self.control_frame.pack(side=tk.RIGHT, padx=8)  # Mostrar controles
            self._do_temp_refresh_async()
        else:
            # Gráfico Temperature Plot (generado por polymarket_bot.py)
            self.temp_title.config(text="ÚLTIMAS LECTURAS  [2/2]")
            self.control_frame.pack_forget()  # Ocultar controles
            self._load_temperature_plot()

    def _load_temperature_plot(self):
        """Carga el gráfico generado por polymarket_bot.py"""
        plot_path = os.path.join(BASE_DIR, "polymarket_graphs", "polymarket_temperature_history.png")
        
        # Encontrar el archivo de gráfico y JSON más reciente
        # Para esto buscamos los más recientes creados hoy u otro día si no hay de hoy.
        graphs_dir = os.path.join(BASE_DIR, "polymarket_graphs")
        import glob
        
        # Buscar el plot más reciente
        plot_files = glob.glob(os.path.join(graphs_dir, "polymarket_temperature_history_*.png"))
        if plot_files:
            plot_path = max(plot_files, key=os.path.getmtime)
        else:
            plot_path = os.path.join(graphs_dir, "polymarket_temperature_history.png")
        
        if os.path.exists(plot_path):
            w = max(self.left_panel.winfo_width()  - 16, 560)
            h = max(self.left_panel.winfo_height() - 60, 380)
            
            img = Image.open(plot_path).convert("RGB")
            img = img.resize((w, h), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            
            self._temp_photo = photo
            self.temp_canvas.config(image=photo, text="")
            
            mtime = datetime.fromtimestamp(os.path.getmtime(plot_path))
            self.temp_status.config(text=f"Actualizado: {mtime.strftime('%H:%M:%S')}  |  {os.path.getsize(plot_path)//1024} KB")
        else:
            self.temp_status.config(text="⚠️  Gráfico no disponible", fg="#f38ba8")
            self.temp_canvas.config(image='', text="Gráfico no disponible", fg="#f38ba8")

    def _on_custom_day_changed(self):
        """Callback cuando el usuario cambia el día/mes personalizado"""
        self._do_temp_refresh_async()

    def _do_temp_refresh_async(self):
        """Genera el gráfico en hilo aparte para no bloquear la UI."""
        def worker():
            w = max(self.left_panel.winfo_width()  - 16, 560)
            h = max(self.left_panel.winfo_height() - 60, 380)
            # Obtener valores actuales de día y mes
            custom_day = self.custom_day.get()
            custom_month = self.custom_month.get()
            pil_img = build_temp_figure(w, h, custom_day, custom_month)
            pil_img = pil_img.convert("RGB").resize((w, h), Image.LANCZOS)
            photo   = ImageTk.PhotoImage(pil_img)
            self.after(0, lambda: self._apply_temp_photo(photo))

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

    def _run_satellite_downloader(self):
        """Corre satellite_images.py como subprocess y captura su stdout."""
        script = os.path.join(BASE_DIR, "satellite_images.py")
        log_queue.put(f"[{datetime.now().strftime('%H:%M:%S')}] 🛰️  Iniciando satellite_images...")
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

    # ── Refresh periódico ─────────────────────────────────────────────────────

    def _schedule_sat_refresh(self):
        """Refresca imágenes satélite cada 15 minutos."""
        self._refresh_satellite_display()
        self.after(900_000, self._schedule_sat_refresh)   # cada 15 minutos

    def _schedule_temp_refresh(self):
        """Refresca la gráfica de temperatura cada 20 segundos."""
        # Actualizar según el gráfico activo
        if self._temp_graph_index == 0:
            self._do_temp_refresh_async()
        else:
            self._load_temperature_plot()

        self.after(5_000, self._schedule_temp_refresh)   # cada 5 segundos

    def _schedule_refresh(self):
        """Arranca los dos ciclos de refresco independientes."""
        self._schedule_sat_refresh()
        self._schedule_temp_refresh()

    def _check_plot_update(self):
        """Revisa periódicamente si el gráfico ha sido actualizado e intenta recargarlo."""
        graphs_dir = os.path.join(BASE_DIR, "polymarket_graphs")
        import glob
        plot_files = glob.glob(os.path.join(graphs_dir, "polymarket_temperature_history_*.png"))
        if plot_files:
            plot_path = max(plot_files, key=os.path.getmtime)
        else:
            plot_path = os.path.join(graphs_dir, "polymarket_temperature_history.png")

        try:
            if os.path.exists(plot_path):
                mod_time = os.path.getmtime(plot_path)
                # Comparar con el tiempo de modificación registrado
                if not hasattr(self, "_last_plot_mod_time") or mod_time > self._last_plot_mod_time:
                    self._last_plot_mod_time = mod_time
                    self._load_temperature_plot()
        except Exception as e:
            log_queue.put(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Error al verificar actualización de gráfico: {e}")


# ══════════════════════════════════════════════════════════════════════════════

def main():
    app = Dashboard()
    app.mainloop()


if __name__ == "__main__":
    main()

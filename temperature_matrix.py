import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.patches as patches
import calendar

def generar_matriz_final_optimizada(db_path, anio, mes):
    mes_str = f"{mes:02d}"
    tabla_nombre = f"madrid_barajas_temperatures_{anio}_{mes_str}"
    
    print(f"[*] Procesando: {tabla_nombre} (Ventana 11:00 - 18:30 UTC)")
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(f"SELECT timestamp_utc, temperature FROM {tabla_nombre};", conn)
    except:
        return print(f"[!] Tabla {tabla_nombre} no encontrada.")
    finally:
        conn.close()

    # 1. PROCESAMIENTO DE DATOS
    df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
    df = df.dropna(subset=['temperature']).sort_values('timestamp_utc').reset_index(drop=True)
    
    # Cálculo de incrementos crudos
    df['delta_T'] = df['temperature'].diff()
    df['dt_hours'] = df['timestamp_utc'].diff().dt.total_seconds() / 3600.0
    df = df[df['dt_hours'] <= 1.0].copy() # Filtro de continuidad
    
    df['day'] = df['timestamp_utc'].dt.day
    df['time_utc'] = df['timestamp_utc'].dt.strftime('%H:%M')
    
    # --- DETECCIÓN DE PICOS (TOP 1 y TOP 2) ---
    # 1. Identificar la TEMPERATURA MÁXIMA (Top 1)
    idx_max = df.groupby('day')['temperature'].idxmax()
    df_peaks_1 = df.loc[idx_max, ['day', 'time_utc', 'temperature']].rename(columns={'temperature': 'Tmax1'})
    
    # 2. Identificar la SEGUNDA TEMPERATURA MÁXIMA (Top 2)
    # Eliminamos temporalmente los registros del Top 1 y volvemos a buscar el máximo
    df_sin_top1 = df.drop(idx_max)
    idx_max_2 = df_sin_top1.groupby('day')['temperature'].idxmax().dropna()
    df_peaks_2 = df.loc[idx_max_2, ['day', 'time_utc', 'temperature']].rename(columns={'temperature': 'Tmax2'})
    
    # 2. CONSTRUCCIÓN DE LA MATRIZ (11:00 - 18:30)
    horas_ventana = [f"{h:02d}:{m:02d}" for h in range(11, 19) for m in (0, 30)]
    
    grid = df.pivot_table(index='day', columns='time_utc', values='delta_T', aggfunc='first')
    _, dias_en_mes = calendar.monthrange(anio, mes)
    
    # Reindexar para la ventana específica
    grid = grid.reindex(index=range(1, dias_en_mes + 1), columns=horas_ventana)

    # =====================================================================
    # 3. RENDERIZADO VISUAL
    # =====================================================================
    fig, ax = plt.subplots(figsize=(18, 12))
    fig.patch.set_facecolor('white')
    
    # Dibujar Heatmap (Rojo/Azul, sin barra de color)
    sns.heatmap(grid, cmap='RdBu_r', center=0, annot=True, fmt=".1f",
                cbar=False, linewidths=0.8, linecolor='#f0f0f0', ax=ax,
                annot_kws={"size": 9, "weight": "bold"})
    
    # --- LÓGICA DE LOS RECUADROS (Verde y Amarillo) ---
    column_map = {hora: i for i, hora in enumerate(horas_ventana)}
    
    # Dibujar Recuadro Verde (Top 1)
    for _, row in df_peaks_1.iterrows():
        dia = int(row['day'])
        hora = row['time_utc']
        if hora in column_map:
            col_idx = column_map[hora]
            row_idx = dia - 1 
            ax.add_patch(patches.Rectangle((col_idx, row_idx), 1, 1, 
                                          fill=False, edgecolor='#2ecc71', # Verde esmeralda
                                          lw=4, zorder=10))

    # Dibujar Recuadro Amarillo (Top 2)
    for _, row in df_peaks_2.iterrows():
        dia = int(row['day'])
        hora = row['time_utc']
        if hora in column_map:
            col_idx = column_map[hora]
            row_idx = dia - 1 
            # Si el Top 1 y Top 2 ocurren en la misma celda (muy raro en intervalos de 30 min, pero posible), 
            # el amarillo se dibuja un poco más pequeño para que se vean ambos.
            ax.add_patch(patches.Rectangle((col_idx + 0.05, row_idx + 0.05), 0.9, 0.9, 
                                          fill=False, edgecolor="#6a00ff", # Amarillo oro
                                          lw=3, zorder=9, linestyle='-'))

    # --- ESTÉTICA DE EJES ---
    nombre_mes = calendar.month_name[mes].capitalize()
    ax.set_title(f'Flujo Térmico UTC: {nombre_mes} {anio} (Ventana 11:00 - 18:30)\n', 
                 fontsize=16, fontweight='bold', pad=40)
    
    ax.set_xlabel('Hora del Día (UTC)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Día del Mes', fontsize=12, fontweight='bold')

    # Eje superior
    ax_top = ax.secondary_xaxis('top')
    ax_top.set_xticks(range(len(horas_ventana)))
    ax_top.set_xticklabels(horas_ventana, rotation=45, fontsize=9)

    # Eje derecho (Temperatura Máxima Absoluta)
    ax_right = ax.twinx()
    ax_right.set_ylim(ax.get_ylim())
    ax_right.set_yticks(ax.get_yticks())
    
    tmax_diaria = df.groupby('day')['temperature'].max()
    labels_max = [f"MAX: {tmax_diaria.get(dia, 0.0):.1f}°C" if dia in tmax_diaria else "" 
                  for dia in grid.index]
                  
    ax_right.set_yticklabels(labels_max, fontsize=10, fontweight='bold', color='#c0392b')
    ax_right.set_ylabel('Temperatura Máxima Diaria (UTC)', fontsize=12, fontweight='bold', color='#c0392b', rotation=270, labelpad=25)
    
    # Invertir el eje Y
    ax_right.invert_yaxis()
    ax.invert_yaxis()

    plt.tight_layout()
    archivo_salida = f'Analisis_Arbitraje_UTC_{anio}_{mes:02d}.png'
    plt.savefig(archivo_salida, dpi=300)
    print(f"[✓] Matriz guardada como: {archivo_salida}\n")
    plt.show()

if __name__ == "__main__":
    import locale
    try: locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    except: pass

    # Interfaz por terminal
    print("=== MATRIZ DE ARBITRAJE TÉRMICO (11:00-18:30 UTC) ===")
    while True:
        try:
            entrada = input("Introduce Año y Mes (ej. '2024 7') o 'q' para salir: ")
            if entrada.lower() == 'q': break
            p = entrada.split()
            if len(p) == 2:
                generar_matriz_final_optimizada('base_datos.db', int(p[0]), int(p[1]))
            else: print("[!] Formato incorrecto. Usa: Año Mes")
        except ValueError: print("[!] Datos no válidos.")
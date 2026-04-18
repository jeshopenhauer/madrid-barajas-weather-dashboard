#!/usr/bin/env python3
"""
Genera un HTML interactivo con Plotly mostrando la evolución de precios
(probabilidad YES) de todos los mercados de temperatura por día.

El selector de día usa un <select> HTML nativo + Plotly.restyle/relayout
para evitar el bug de Plotly updatemenus que revierte al día inicial al
interactuar con el gráfico.
"""

import json
import sqlite3
import re
from datetime import datetime
from pathlib import Path

import plotly.graph_objects as go

DB_PATH = Path(__file__).parent / "polymarket_history.db"
OUTPUT  = Path(__file__).parent / "polymarket_graphs" / "temperaturas_interactivo.html"

MONTH_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}

COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    "#aec7e8", "#ffbb78", "#98df8a", "#ff9896", "#c5b0d5",
]


def date_from_slug(slug: str) -> str:
    """Extrae la fecha real del evento desde el slug, p.ej.:
    'highest-temperature-in-madrid-on-march-19-2026' → '19 Mar 2026'
    Evita usar end_date (que apunta al día siguiente del mercado).
    """
    match = re.search(r"-on-([a-z]+)-(\d{1,2})-(\d{4})$", slug)
    if match:
        month_str, day, year = match.groups()
        month_num = MONTH_MAP.get(month_str.lower(), 1)
        try:
            return datetime(int(year), month_num, int(day)).strftime("%d %b %Y")
        except ValueError:
            pass
    return slug


def temp_sort_key(temp_str: str) -> float:
    nums = re.findall(r"[-\d]+", temp_str)
    val = float(nums[0]) if nums else 0
    if "or below" in temp_str:
        val -= 0.5
    elif "or higher" in temp_str:
        val += 0.5
    return val


def date_from_slug_dt(slug: str):
    """Devuelve un datetime para ordenar cronológicamente."""
    match = re.search(r"-on-([a-z]+)-(\d{1,2})-(\d{4})$", slug)
    if match:
        month_str, day, year = match.groups()
        month_num = MONTH_MAP.get(month_str.lower(), 1)
        try:
            return datetime(int(year), month_num, int(day))
        except ValueError:
            pass
    return datetime.min


def load_data(conn: sqlite3.Connection):
    c = conn.cursor()
    c.execute("SELECT slug FROM events")
    slugs = [row[0] for row in c.fetchall()]
    events = sorted(slugs, key=date_from_slug_dt)

    days = []
    for slug in events:
        day_label = date_from_slug(slug)

        c.execute(
            "SELECT id, temperature, token_yes FROM markets WHERE event_slug=?",
            (slug,),
        )
        markets = sorted(c.fetchall(), key=lambda m: temp_sort_key(m[1]))

        traces = []
        for market_id, temperature, token_yes in markets:
            c.execute(
                """
                SELECT datetime, price
                FROM price_snapshots
                WHERE market_id=? AND token_id=?
                ORDER BY timestamp
                """,
                (market_id, token_yes),
            )
            rows = c.fetchall()
            if not rows:
                continue
            traces.append((temperature, [r[0] for r in rows], [r[1] for r in rows]))

        if traces:
            days.append({"label": day_label, "slug": slug, "traces": traces})

    return days


def build_figure(days):
    fig = go.Figure()
    all_traces_per_day = []
    global_idx = 0

    for d_i, day in enumerate(days):
        is_first = d_i == 0
        day_indices = []
        for i, (temperature, times, prices) in enumerate(day["traces"]):
            fig.add_trace(
                go.Scatter(
                    x=times,
                    y=[p * 100 for p in prices],
                    mode="lines+markers",
                    name=temperature,
                    line=dict(color=COLORS[i % len(COLORS)], width=2),
                    marker=dict(size=4),
                    visible=is_first,
                    hovertemplate=(
                        f"<b>{temperature}</b><br>"
                        "Fecha: %{x}<br>"
                        "Prob: %{y:.1f}%<extra></extra>"
                    ),
                )
            )
            day_indices.append(global_idx)
            global_idx += 1
        all_traces_per_day.append(day_indices)

    first_label = days[0]["label"] if days else ""

    fig.update_layout(
        title=dict(text=f"Probabilidades de temperatura · {first_label}", font=dict(size=18)),
        xaxis=dict(
            title="Fecha/Hora",
            showgrid=True,
            gridcolor="#e0e0e0",
            # Sin rangeslider: causaba que Plotly revirtiera al día inicial
            # al interactuar con el gráfico. Usar scroll/drag para zoom.
        ),
        yaxis=dict(
            title="Probabilidad YES (%)",
            showgrid=True,
            gridcolor="#e0e0e0",
            range=[0, 100],
            ticksuffix="%",
        ),
        legend=dict(
            title="Temperatura",
            orientation="v",
            x=1.02,
            xanchor="left",
            y=1,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="#cccccc",
            borderwidth=1,
        ),
        hovermode="x unified",
        plot_bgcolor="#fafafa",
        paper_bgcolor="#ffffff",
        height=620,
        margin=dict(l=60, r=200, t=80, b=60),
    )

    return fig, all_traces_per_day, global_idx


def main():
    conn = sqlite3.connect(DB_PATH)
    try:
        days = load_data(conn)
    finally:
        conn.close()

    if not days:
        print("No se encontraron datos en la base de datos.")
        return

    print(f"Días encontrados: {len(days)}")
    for d in days:
        print(f"  {d['label']}: {len(d['traces'])} mercados de temperatura")

    fig, all_traces_per_day, total_traces = build_figure(days)

    # Serializar el mapa día→índices para el JS del selector
    day_data = [
        {
            "label": day["label"],
            "indices": all_traces_per_day[i],
            "title": f"Probabilidades de temperatura · {day['label']}",
        }
        for i, day in enumerate(days)
    ]

    options_html = "\n".join(
        f'            <option value="{i}">{d["label"]}</option>'
        for i, d in enumerate(days)
    )

    # Obtener el div+script de Plotly (sin full HTML)
    # NO usar div_id propio: Plotly asigna su propio id interno al <div>;
    # lo localizamos con document.querySelector('.plotly-graph-div') en el JS.
    plot_div = fig.to_html(
        full_html=False,
        include_plotlyjs="cdn",
        config={
            "scrollZoom": True,
            "displayModeBar": True,
            "toImageButtonOptions": {"format": "png", "width": 1600, "height": 700},
        },
    )

    full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Polymarket – Temperaturas Madrid</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f0f2f5;
        }}
        #controls {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 12px;
            padding: 12px 16px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.12);
        }}
        #controls label {{
            font-size: 15px;
            font-weight: bold;
            color: #333;
        }}
        #day-select {{
            font-size: 14px;
            padding: 6px 12px;
            border-radius: 5px;
            border: 1px solid #aaa;
            background: #fafafa;
            cursor: pointer;
            min-width: 160px;
        }}
        #hint {{
            font-size: 12px;
            color: #888;
            margin-left: auto;
        }}
        #polymarket-plot {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.12);
            padding: 4px;
        }}
    </style>
</head>
<body>
    <div id="controls">
        <label for="day-select">Día de mercado:</label>
        <select id="day-select" onchange="changeDay(this.value)">
{options_html}
        </select>
        <span id="hint">🔍 Rueda del ratón para zoom · Doble clic para resetear</span>
    </div>

    {plot_div}

    <script>
        var DAY_DATA    = {json.dumps(day_data)};
        var TOTAL       = {total_traces};

        function changeDay(idx) {{
            idx = parseInt(idx);
            var day     = DAY_DATA[idx];
            var visible = new Array(TOTAL).fill(false);
            day.indices.forEach(function(i) {{ visible[i] = true; }});

            // El div de Plotly es el primer .js-plotly-plot del documento
            var div = document.querySelector('.js-plotly-plot');
            Plotly.restyle(div, {{'visible': visible}});
            Plotly.relayout(div, {{'title.text': day.title, 'xaxis.autorange': true}});
        }}

        // Sincronizar select con el gráfico al cargar la página
        window.addEventListener('load', function() {{
            var sel = document.getElementById('day-select');
            changeDay(sel.value);
        }});
    </script>
</body>
</html>
"""

    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(full_html, encoding="utf-8")
    print(f"\nHTML generado: {OUTPUT}")


if __name__ == "__main__":
    main()

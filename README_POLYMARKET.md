# Sistemas de Datos Históricos - Forecast Bot

## 1. Base de datos Polymarket (polymarket_history.db)

Datos de mercados de pronósticos de temperatura de Madrid desde Polymarket.

### Archivos
- **polymarket_history.db** - Base de datos con mercados de predicción (157K snapshots)
- **actualizar_db.py** - Script inteligente de actualización
- **actualizar.sh** - Script bash simplificado

### Uso diario
```bash
./actualizar.sh
```

Detecta automáticamente nuevos días y los descarga. Solo descarga lo que falta.

### Estado actual
```
📅 Eventos: 30
🎯 Mercados: 330  
📊 Snapshots: 157,281
📆 Rango: 16 marzo - 15 abril 2026
```

---

## 2. Base de datos Meteociel (base_datos.db)

Datos meteorológicos reales del Aeropuerto Madrid-Barajas desde 2018 vía web scraping.

### Archivos
- **base_datos.db** - Base de datos histórica con datos reales (145K registros)
- **meteociel_actualizar.py** - Script de actualización automática
- **actualizar_meteociel.sh** - Script bash simplificado
- **meteociel_web_scrapping.py** - Scraper base (referencia)

### Uso diario
```bash
./actualizar_meteociel.sh
```

Detecta automáticamente la última fecha en la BD y actualiza hasta hoy.

### Datos capturados
- Temperatura (°C)
- Humedad (%)
- Velocidad del viento (km/h)
- Presión atmosférica (hPa)
- Timestamp en UTC y hora local

### Estado actual
```
📊 Total registros: 144,736
📆 Rango: 2018 - 14 abril 2026
⏱️  Frecuencia: cada 30 minutos
```

### Uso avanzado

**Actualizar desde fecha específica:**
```bash
python3 meteociel_actualizar.py 2026-04-01 2026-04-15
```

**Modo prueba (sin tocar base_datos.db):**
```bash
python3 meteociel_actualizar.py --test 2026-04-14
```

---

## Notas importantes

- Ambos scripts son inteligentes: solo descargan datos nuevos
- Ejecutar diariamente para mantener actualizado
- Polymarket: datos desde marzo 16, 2026
- Meteociel: datos desde 2018
- Cada actualización tarda 1-5 minutos dependiendo del rango

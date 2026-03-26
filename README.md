# 🌤️ Madrid Barajas Weather Dashboard

Dashboard meteorológico en tiempo real para el Aeropuerto Madrid-Barajas con monitoreo multi-fuente de datos e imágenes satelitales de Europa.

## 📋 Características

### 🎯 Monitoreo Multi-Fuente (9 APIs)
- **Weather.com** - ICAO LEMD (Oficial Aeropuerto)
- **6 Estaciones Personales PWS**:
  - IMADRI133 (Barajas)
  - IMADRI265 (Barajas)
  - IMADRI56 (Madrid)
  - IMADRI883 (Timón)
  - IMADRI364 (Alameda de Osuna)
  - IMADRI882 (Alameda de Osuna)
- **AEMET OpenData** - Gobierno de España (Estación 3129)
- **Meteociel** - Web Scraping en tiempo real

### 🛰️ Imágenes Satelitales
- **5 tipos de visualizaciones de Europa (MTG Meteosat)**:
  - Infrarrojo Europa
  - Visible Color Europa
  - Vapor de Agua Europa
  - Vapor de Agua 2 Europa
  - Masas de Aire Europa (Airmass RGB)

### 📊 Gráficos de Temperatura
- Comparación en tiempo real entre múltiples fuentes
- Actualización automática cada 20 segundos
- Visualización gráfica de tendencias

## 🚀 Instalación

### Requisitos
- Python 3.8+
- pip
- tkinter (generalmente incluido con Python)

### Pasos

1. **Clonar el repositorio**
```bash
git clone https://github.com/jeshopenhauer/madrid-barajas-weather-dashboard.git
cd madrid-barajas-weather-dashboard
```

2. **Crear entorno virtual**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# o
.venv\Scripts\activate  # Windows
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Ejecutar el dashboard**
```bash
python dashboard.py
```

## 📦 Estructura del Proyecto

```
forecast_bot/
├── dashboard.py              # GUI principal con Tkinter
├── polymarket_bot.py        # Monitoreo de 9 fuentes de datos
├── satellite_images.py      # Descarga de imágenes satelitales
├── meteociel_scraper.py     # Scraper para Meteociel
├── requirements.txt         # Dependencias Python
├── .gitignore
└── README.md
```

## 🛠️ Uso

### Dashboard Principal
```bash
python dashboard.py
```
El dashboard mostrará:
- Terminal en vivo con datos de las 9 fuentes
- Imágenes satelitales de Europa con navegación (←/→)
- Gráfico de comparación de temperaturas

### Solo Monitoreo (Sin GUI)
```bash
python polymarket_bot.py
```

### Descargar Imágenes Satelitales
```bash
python satellite_images.py
```

## 🔑 APIs Utilizadas

- **Weather.com API**: Datos oficiales del aeropuerto y estaciones PWS con precisión decimal
- **AEMET OpenData**: API oficial del Gobierno de España
- **Meteociel**: Web scraping para datos en tiempo real e imágenes satelitales
- **MTG Meteosat**: Satélite de tercera generación para imágenes de Europa

## 📸 Características Técnicas

### Precisión de Datos
- Todas las estaciones PWS reportan con decimales (9.3°C, 10.5°C, etc.)
- Parámetro `numericPrecision: decimal` en todas las requests
- Actualización cada 20 segundos

### Imágenes Satelitales
- Descarga automática cada 5 minutos
- Imágenes de alta resolución de toda Europa
- 5 canales diferentes del satélite MTG Meteosat
- Navegación con flechas izquierda/derecha

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 💡 Función Git Rápida

Si clonas este repo, puedes añadir esta función a tu `~/.bashrc`:

```bash
gitpush() {
    if [ -z "$1" ]; then
        echo "❌ Error: Debes proporcionar un mensaje de commit"
        echo "Uso: gitpush \"tu mensaje de commit\""
        return 1
    fi
    git add .
    git commit -m "$1"
    git push
    echo "✅ ¡Cambios subidos exitosamente!"
}
```

Uso: `gitpush "mensaje de commit"`

## 📝 Notas

- Las estaciones PWS pueden tener ligeras variaciones de temperatura (±1-2°C)
- AEMET suele reportar temperaturas más altas (sensores oficiales del aeropuerto)
- Las imágenes satelitales se actualizan cada 5 minutos automáticamente
- Todas las imágenes son de Europa completa (España, Portugal, Francia, Italia, etc.)

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver archivo `LICENSE` para más detalles.

## 👤 Autor

Desarrollado para monitoreo meteorológico en tiempo real del Aeropuerto Madrid-Barajas.

## 🙏 Agradecimientos

- Weather.com por su API de datos meteorológicos con precisión decimal
- AEMET por los datos oficiales del gobierno español
- Meteociel por los datos en tiempo real e imágenes satelitales
- EUMETSAT por el satélite MTG Meteosat de tercera generación

---

**⚠️ Disclaimer**: Este proyecto es solo para fines educativos y de monitoreo personal. No debe usarse para decisiones críticas relacionadas con el clima o la aviación.

# 🌤️ Madrid Barajas Weather Dashboard

Dashboard meteorológico en tiempo real para el Aeropuerto Madrid-Barajas con monitoreo multi-fuente de datos e imágenes satelitales animadas.

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
- **6 tipos de visualizaciones**:
  - Infrarrojo
  - Vapor de Agua
  - Masas de Aire (PNG)
  - Visible IR
  - Masas de Aire (GIF Animado)
  - Visible (GIF Animado)

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
git clone https://github.com/TU_USUARIO/forecast_bot.git
cd forecast_bot
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
├── temperature_comparison.py # Comparación de temperaturas
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
- Imágenes satelitales con navegación (←/→)
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

- **Weather.com API**: Datos oficiales del aeropuerto y estaciones PWS
- **AEMET OpenData**: API oficial del Gobierno de España
- **Meteociel**: Web scraping para datos en tiempo real
- **Meteosatonline**: Imágenes satelitales GIF animadas

## 📸 Capturas de Pantalla

### Dashboard Principal
*Interfaz con terminal, imágenes satelitales y gráficos*

### Comparación de Temperaturas
*9 fuentes de datos en tiempo real con diferencias de ±2°C típicamente*

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Notas

- Las estaciones PWS pueden tener ligeras variaciones de temperatura (±1-2°C)
- AEMET suele reportar temperaturas más altas (sensores oficiales)
- Las imágenes satelitales se descargan automáticamente cada 15 minutos
- Los GIFs animados se reproducen automáticamente en el dashboard

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la [MIT License](LICENSE).

## 👤 Autor

Desarrollado para monitoreo meteorológico en tiempo real del Aeropuerto Madrid-Barajas.

## 🙏 Agradecimientos

- Weather.com por su API de datos meteorológicos
- AEMET por los datos oficiales del gobierno
- Meteociel por los datos en tiempo real
- Meteosatonline por las imágenes satelitales

---

**⚠️ Disclaimer**: Este proyecto es solo para fines educativos y de monitoreo personal. No debe usarse para decisiones críticas relacionadas con el clima o la aviación.

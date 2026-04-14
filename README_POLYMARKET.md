# Sistema de Datos Históricos de Polymarket - Madrid Temperature

## Archivos principales

- **polymarket_history.db** - Base de datos con todos los datos históricos
- **actualizar_db.py** - Script para actualizar la base de datos
- **actualizar.sh** - Script bash simplificado para actualizar

## Uso diario

### Opción 1: Script automático (RECOMENDADO)
```bash
./actualizar.sh
```

### Opción 2: Comando directo
```bash
python3 actualizar_db.py
```

Esto descargará automáticamente todos los días nuevos desde marzo 2026 hasta hoy.

## Uso avanzado

### Actualizar un mes específico
```bash
python3 actualizar_db.py 2026 3    # Marzo 2026
python3 actualizar_db.py 2026 4    # Abril 2026
```

### Actualizar un rango de meses
```bash
python3 actualizar_db.py 2026 3 2026 4    # Desde marzo a abril 2026
```

## Estado actual de la base de datos

```
📅 Eventos: 27
🎯 Mercados: 297  
📊 Snapshots: 141,972
📆 Rango: 16 marzo - 14 abril 2026
```

## Notas

- El script es inteligente: **solo descarga eventos nuevos**
- No descargará eventos que ya existen en la DB
- Polymarket solo tiene datos desde marzo 16, 2026
- Cada actualización tarda ~2-5 minutos dependiendo de cuántos días nuevos haya

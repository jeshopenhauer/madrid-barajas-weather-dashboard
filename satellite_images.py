#!/usr/bin/env python3
"""
Script para descargar imágenes de satélite de Meteociel
Descarga múltiples tipos de imágenes y las organiza en carpetas
"""

import requests
from datetime import datetime
import time
import os
import sys

class SatelliteImageDownloader:
    def __init__(self, base_dir="satellite_images"):
        # Directorio base para guardar las imágenes
        self.base_dir = base_dir
        
        # Crear directorio base si no existe
        os.makedirs(self.base_dir, exist_ok=True)
        
        # URLs de los diferentes tipos de imágenes de satélite (8 canales)
        # Usar URLs directas de modeles20.meteociel.fr
        self.satellite_types = {
            "infrarrojo_sp": {
                "url": "https://modeles20.meteociel.fr/satellite/latestsatirmtgsp.png",
                "description": "Infrarrojo España",
                "folder": "infrarrojo_sp"
            },
            "infrarrojo_eu": {
                "url": "https://modeles20.meteociel.fr/satellite/latestsatirmtgeu.png",
                "description": "Infrarrojo Europa",
                "folder": "infrarrojo_eu"
            },
            "vapor_agua_sp": {
                "url": "https://modeles20.meteociel.fr/satellite/latestsatwvmtgsp.png",
                "description": "Vapor de Agua España",
                "folder": "vapor_agua_sp"
            },
            "vapor_agua_eu": {
                "url": "https://modeles20.meteociel.fr/satellite/latestsatwvmtgeu.png",
                "description": "Vapor de Agua Europa",
                "folder": "vapor_agua_eu"
            },
            "masas_aire_sp": {
                "url": "https://modeles20.meteociel.fr/satellite/latestsatairmassrgbmtgsp.png",
                "description": "Masas de Aire España",
                "folder": "masas_aire_sp"
            },
            "masas_aire_eu": {
                "url": "https://modeles20.meteociel.fr/satellite/latestsatairmassrgbmtgeu.png",
                "description": "Masas de Aire Europa",
                "folder": "masas_aire_eu"
            },
            "visible_sp": {
                "url": "https://modeles20.meteociel.fr/satellite/latestsatviscolmtgsp.png",
                "description": "Visible España",
                "folder": "visible_sp"
            },
            "visible_eu": {
                "url": "https://modeles20.meteociel.fr/satellite/latestsatviscolmtgeu.png",
                "description": "Visible Europa",
                "folder": "visible_eu"
            }
        }
        
        # Crear carpetas para cada tipo de imagen
        for sat_type, info in self.satellite_types.items():
            folder_path = os.path.join(self.base_dir, info["folder"])
            os.makedirs(folder_path, exist_ok=True)
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.meteociel.fr/'
        }
    
    def download_satellite_image(self, sat_type, info):
        """Descarga una imagen de satélite específica"""
        try:
            now = datetime.now()
            timestamp_str = now.strftime('%Y%m%d_%H%M%S')
            time_display = now.strftime('%H:%M:%S')
            
            print(f"[{time_display}] 📡 Descargando {info['description']}...")
            
            # Descargar la imagen
            response = requests.get(info['url'], headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                # Rutas para guardar
                folder_path = os.path.join(self.base_dir, info['folder'])
                
                # Guardar solo imagen "latest" (siempre se sobrescribe)
                latest_filename = f"{sat_type}_latest.png"
                latest_path = os.path.join(folder_path, latest_filename)
                
                # Escribir la imagen (solo una copia)
                with open(latest_path, 'wb') as f:
                    f.write(response.content)
                
                size_kb = len(response.content) / 1024
                print(f"[{time_display}] ✅ {info['description']} descargada ({size_kb:.1f} KB)")
                print(f"             └─ Guardada en: {latest_path}")
                return True
            else:
                print(f"[{time_display}] ❌ Error descargando {info['description']}: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            time_display = datetime.now().strftime('%H:%M:%S')
            print(f"[{time_display}] ❌ Error descargando {info['description']}: {e}")
            return False
    
    def download_all_images(self):
        """Descarga todas las imágenes de satélite"""
        print(f"\n{'='*80}")
        print(f"📡 DESCARGANDO IMÁGENES DE SATÉLITE")
        print(f"{'='*80}\n")
        
        success_count = 0
        total_count = len(self.satellite_types)
        
        for sat_type, info in self.satellite_types.items():
            if self.download_satellite_image(sat_type, info):
                success_count += 1
            time.sleep(0.5)  # Pequeña pausa entre descargas
        
        print(f"\n{'='*80}")
        print(f"✅ Descargadas {success_count}/{total_count} imágenes")
        print(f"{'='*80}\n")
        
        return success_count
    
    def run(self, update_interval=300):
        """
        Ejecuta el descargador con actualización automática
        
        Args:
            update_interval: Segundos entre descargas (default: 300 = 5 minutos)
        """
        print(f"\n{'='*80}")
        print(f"🛰️  DESCARGADOR DE IMÁGENES DE SATÉLITE - METEOCIEL")
        print(f"{'='*80}")
        print(f"Regiones: España/Portugal + Europa")
        print(f"Satélite: MTG Meteosat12 (Tercera generación)")
        print(f"Directorio: {os.path.abspath(self.base_dir)}/")
        print(f"{'='*80}")
        print(f"\nTipos de imágenes (8 canales):")
        for sat_type, info in self.satellite_types.items():
            print(f"  • {info['description']}")
        print(f"{'='*80}\n")
        
        # Primera descarga
        self.download_all_images()
        
        print(f"🔄 Actualizando cada {update_interval} segundos ({update_interval//60} minutos)")
        print(f"� Solo se guarda la última imagen de cada tipo (se sobrescribe)")
        print(f"❌ Presiona Ctrl+C para detener\n")
        print(f"{'='*80}\n")
        
        iteration = 0
        
        try:
            while True:
                time.sleep(update_interval)
                iteration += 1
                
                print(f"\n{'─'*80}")
                print(f"🔄 Actualización #{iteration}")
                print(f"{'─'*80}\n")
                
                self.download_all_images()
                
        except KeyboardInterrupt:
            print(f"\n\n✅ Descargador detenido.\n")
            print(f"📁 Las imágenes se encuentran en: {os.path.abspath(self.base_dir)}/\n")
            sys.exit(0)

def main():
    """Función principal"""
    print("🚀 Iniciando descargador de imágenes de satélite...")
    print("🛰️  Meteociel - MTG Meteosat12\n")
    
    try:
        downloader = SatelliteImageDownloader(base_dir="satellite_images")
        # Actualizar cada 5 minutos (300 segundos)
        downloader.run(update_interval=300)
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
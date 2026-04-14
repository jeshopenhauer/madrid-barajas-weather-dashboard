#!/usr/bin/env python3
"""
Script inteligente para actualizar la base de datos
Solo descarga eventos que NO estén ya registrados
"""

import sqlite3
import requests
import json
from datetime import datetime
from pathlib import Path
import time
import calendar
import os

class SmartPolymarketUpdater:
    def __init__(self, db_path=None):
        # Si no se especifica ruta, usar la base de datos en el directorio padre
        if db_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(script_dir, "..", "polymarket_history.db")
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.month_names = {
            1: "january", 2: "february", 3: "march", 4: "april", 
            5: "may", 6: "june", 7: "july", 8: "august",
            9: "september", 10: "october", 11: "november", 12: "december"
        }
    
    def get_existing_events(self):
        """Obtiene lista de eventos ya registrados en la DB"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT slug FROM events")
        return set(row[0] for row in cursor.fetchall())
    
    def check_event_exists(self, year, month, day):
        """Verifica si un evento específico existe en Polymarket"""
        month_str = self.month_names[month]
        slug = f"highest-temperature-in-madrid-on-{month_str}-{day}-{year}"
        
        url = "https://gamma-api.polymarket.com/events"
        params = {"slug": slug}
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            events = response.json()
            if events:
                return events[0]
        return None
    
    def save_event(self, event):
        """Guarda un evento en la base de datos"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO events (slug, title, description, end_date, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            event['slug'],
            event.get('title', ''),
            event.get('description', ''),
            event.get('endDate', ''),
            event.get('createdAt', '')
        ))
        self.conn.commit()
    
    def save_market(self, market, event_slug):
        """Guarda un mercado en la base de datos"""
        cursor = self.conn.cursor()
        
        temp = market.get('groupItemTitle', '')
        token_ids = json.loads(market['clobTokenIds'])
        
        cursor.execute("""
            INSERT OR REPLACE INTO markets 
            (id, event_slug, question, temperature, token_yes, token_no, active, closed, end_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            market['id'],
            event_slug,
            market['question'],
            temp,
            token_ids[1],
            token_ids[0],
            1 if market.get('active') else 0,
            1 if market.get('closed') else 0,
            market.get('endDate', '')
        ))
        self.conn.commit()
    
    def download_market_history(self, token_id, market_id, market_name):
        """Descarga el histórico de un mercado"""
        url = "https://clob.polymarket.com/prices-history"
        
        params = {
            'market': token_id,
            'interval': 'max',
            'fidelity': 1
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            return 0
        
        data = response.json()
        history = data.get('history', [])
        
        if not history:
            return 0
        
        # Guardar snapshots
        cursor = self.conn.cursor()
        saved = 0
        
        for point in history:
            timestamp = point['t']
            price = point['p']
            dt = datetime.fromtimestamp(timestamp)
            
            cursor.execute("""
                INSERT OR IGNORE INTO price_snapshots 
                (market_id, token_id, timestamp, price, datetime)
                VALUES (?, ?, ?, ?, ?)
            """, (
                market_id,
                token_id,
                timestamp,
                price,
                dt.isoformat()
            ))
            saved += 1
        
        self.conn.commit()
        return len(history)
    
    def update_month(self, year, month):
        """Actualiza un mes completo, solo descargando eventos nuevos"""
        print(f"\n{'='*80}")
        print(f"ACTUALIZANDO: {self.month_names[month].upper()} {year}")
        print(f"{'='*80}")
        
        # Obtener eventos existentes
        existing_events = self.get_existing_events()
        print(f"📊 Eventos ya en DB: {len(existing_events)}")
        
        month_str = self.month_names[month]
        days_in_month = calendar.monthrange(year, month)[1]
        
        new_events = 0
        new_markets = 0
        new_points = 0
        
        today = datetime.now()
        today_tuple = (today.year, today.month, today.day)
        
        for day in range(1, days_in_month + 1):
            slug = f"highest-temperature-in-madrid-on-{month_str}-{day}-{year}"
            this_day = (year, month, day)
            
            # Verificar si ya existe
            if slug in existing_events:
                if this_day < today_tuple:
                    print(f"   ⏭️  {month_str.capitalize()} {day:2d}: Ya existe en DB")
                    continue
                else:
                    # Día actual o futuro: refrescar snapshots aunque ya exista
                    print(f"   🔄 {month_str.capitalize()} {day:2d}: Actualizando (día activo)...")
                    cursor = self.conn.cursor()
                    cursor.execute(
                        "SELECT id, token_yes, question FROM markets WHERE event_slug = ?", (slug,)
                    )
                    for market_id, token_yes, question in cursor.fetchall():
                        new_points += self.download_market_history(token_yes, market_id, question)
                    time.sleep(0.2)
                    continue
            
            # Si no existe, intentar descargarlo
            event = self.check_event_exists(year, month, day)
            
            if not event:
                print(f"   ⚠️  {month_str.capitalize()} {day:2d}: No disponible en Polymarket")
                continue
            
            # Descargar el evento nuevo
            print(f"   🆕 {month_str.capitalize()} {day:2d}: Descargando...")
            
            self.save_event(event)
            new_events += 1
            
            markets = event.get('markets', [])
            for market in markets:
                self.save_market(market, slug)
                new_markets += 1
                
                # Descargar histórico
                token_ids = json.loads(market['clobTokenIds'])
                token_yes = token_ids[1]
                
                points = self.download_market_history(
                    token_yes,
                    market['id'],
                    market['question']
                )
                new_points += points
            
            time.sleep(0.2)  # Rate limiting
        
        print(f"\n{'='*80}")
        print(f"✅ ACTUALIZACIÓN COMPLETADA")
        print(f"{'='*80}")
        print(f"   🆕 Eventos nuevos: {new_events}")
        print(f"   🎯 Mercados nuevos: {new_markets}")
        print(f"   📊 Puntos nuevos: {new_points}")
    
    def update_year(self, year):
        """Actualiza un año completo"""
        print(f"\n{'='*80}")
        print(f"ACTUALIZANDO AÑO COMPLETO: {year}")
        print(f"{'='*80}")
        
        for month in range(1, 13):
            self.update_month(year, month)
    
    def update_range(self, start_year, start_month, end_year, end_month):
        """Actualiza un rango de meses"""
        print(f"\n{'='*80}")
        print(f"ACTUALIZANDO RANGO: {start_year}-{start_month:02d} a {end_year}-{end_month:02d}")
        print(f"{'='*80}")
        
        current_year = start_year
        current_month = start_month
        
        while (current_year < end_year) or (current_year == end_year and current_month <= end_month):
            self.update_month(current_year, current_month)
            
            # Avanzar al siguiente mes
            current_month += 1
            if current_month > 12:
                current_month = 1
                current_year += 1
    
    def show_summary(self):
        """Muestra un resumen de la base de datos"""
        cursor = self.conn.cursor()
        
        print(f"\n{'='*80}")
        print("📈 RESUMEN DE BASE DE DATOS")
        print(f"{'='*80}")
        
        cursor.execute("SELECT COUNT(*) FROM events")
        n_events = cursor.fetchone()[0]
        print(f"   📅 Eventos totales: {n_events}")
        
        cursor.execute("SELECT COUNT(*) FROM markets")
        n_markets = cursor.fetchone()[0]
        print(f"   🎯 Mercados totales: {n_markets}")
        
        cursor.execute("SELECT COUNT(*) FROM price_snapshots")
        n_snapshots = cursor.fetchone()[0]
        print(f"   📊 Snapshots totales: {n_snapshots:,}")
        
        if n_snapshots > 0:
            cursor.execute("SELECT MIN(datetime), MAX(datetime) FROM price_snapshots")
            min_date, max_date = cursor.fetchone()
            print(f"   📆 Rango temporal: {min_date[:10]} a {max_date[:10]}")
    
    def close(self):
        """Cierra la conexión"""
        self.conn.close()


def main():
    import sys
    from datetime import datetime
    
    updater = SmartPolymarketUpdater()
    
    try:
        if len(sys.argv) == 1:
            # Sin argumentos: actualizar desde marzo 2026 hasta hoy
            print("🎯 ACTUALIZACIÓN AUTOMÁTICA")
            print("Actualizando desde marzo 2026 hasta el mes actual...\n")
            
            now = datetime.now()
            current_year = now.year
            current_month = now.month
            
            # Actualizar desde marzo 2026 hasta el mes actual
            updater.update_range(2026, 3, current_year, current_month)
        
        elif len(sys.argv) == 3:
            # Año y mes específicos
            year = int(sys.argv[1])
            month = int(sys.argv[2])
            updater.update_month(year, month)
        
        elif len(sys.argv) == 5:
            # Rango de fechas
            start_year = int(sys.argv[1])
            start_month = int(sys.argv[2])
            end_year = int(sys.argv[3])
            end_month = int(sys.argv[4])
            updater.update_range(start_year, start_month, end_year, end_month)
        
        else:
            print("❌ Argumentos incorrectos")
            print("💡 Sin argumentos: actualiza todo automáticamente")
            print("💡 Con argumentos: python3 actualizar_db.py [año] [mes]")
            return
        
        updater.show_summary()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Actualización interrumpida por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        updater.close()
        print("\n✅ Conexión cerrada")


if __name__ == "__main__":
    main()

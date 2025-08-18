#!/usr/bin/env python3
"""
Generador de reportes detallados y análisis de estadísticas ETL
"""

import json
import glob
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import argparse

class ETLStatsAnalyzer:
    """Analizador de estadísticas del pipeline ETL"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.stats_files = list(self.project_root.glob("etl_stats_*.json"))
        self.stats_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    def load_latest_stats(self) -> Dict[str, Any]:
        """Carga las estadísticas más recientes"""
        if not self.stats_files:
            raise FileNotFoundError("No se encontraron archivos de estadísticas")
        
        latest_file = self.stats_files[0]
        with open(latest_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_historical_stats(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Carga estadísticas históricas"""
        historical = []
        for stats_file in self.stats_files[:limit]:
            try:
                with open(stats_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['_file'] = stats_file.name
                    historical.append(data)
            except Exception as e:
                print(f"[ADVERTENCIA] Error cargando {stats_file}: {e}")
        return historical
    
    def generate_current_report(self) -> str:
        """Genera reporte del estado actual"""
        try:
            stats = self.load_latest_stats()
        except FileNotFoundError:
            return "[ERROR] No hay datos de estadísticas disponibles"
        
        report = []
        report.append("=" * 70)
        report.append("[STATS] REPORTE DETALLADO - ÚLTIMO PIPELINE ETL")
        report.append("=" * 70)
        
        # Información de ejecución
        exec_info = stats.get("execution", {})
        report.append(f"\n[TIEMPO] INFORMACIÓN DE EJECUCIÓN:")
        report.append(f"   Timestamp: {exec_info.get('timestamp', 'N/A')}")
        report.append(f"   Duración: {exec_info.get('total_time_formatted', 'N/A')}")
        report.append(f"   Éxito: {'[OK] SÍ' if exec_info.get('success') else '[ERROR] NO'}")
        
        # Análisis de scrapers
        scrapers_info = stats.get("scrapers", {})
        report.append(f"\n[SCRAPERS] ANÁLISIS DE SCRAPERS:")
        report.append(f"   Total ejecutados: {scrapers_info.get('total', 0)}")
        report.append(f"   Exitosos: {scrapers_info.get('successful', 0)}")
        report.append(f"   Fallidos: {scrapers_info.get('failed', 0)}")
        
        if scrapers_info.get('details'):
            report.append(f"\n   Detalles por tienda:")
            for tienda, details in scrapers_info['details'].items():
                status_icon = "[OK]" if details['status'] == 'success' else "[ERROR]"
                report.append(f"     {status_icon} {tienda.upper()}: {details['status']}")
                if details.get('error'):
                    report.append(f"        Error: {details['error']}")
        
        # Análisis de datos
        data_summary = stats.get("data_summary", {})
        if data_summary:
            report.append(f"\n[DATOS] ANÁLISIS DE DATOS:")
            
            # Datos raw por tienda
            total_raw = 0
            report.append(f"\n   [ARCHIVOS] Datos raw extraídos:")
            for key, info in data_summary.items():
                if key != "unified":
                    productos = info.get("productos", 0)
                    total_raw += productos
                    tienda, categoria = key.split('_')
                    report.append(f"     {tienda.upper()} {categoria}: {productos} productos")
            
            report.append(f"\n   [STATS] Total raw: {total_raw} productos")
            
            # Datos unificados
            if "unified" in data_summary:
                unified = data_summary["unified"]
                report.append(f"\n   [OBJETIVO] Datos unificados:")
                report.append(f"     Total productos únicos: {unified.get('total_products', 0)}")
                report.append(f"     Productos multi-tienda: {unified.get('multi_store_products', 0)}")
                
                # Eficiencia de deduplicación
                if total_raw > 0:
                    unique_count = unified.get('total_products', 0)
                    dedup_rate = (1 - unique_count / total_raw) * 100
                    savings = total_raw - unique_count
                    report.append(f"     Deduplicación: {dedup_rate:.1f}% ({savings} productos duplicados eliminados)")
                
                # Por categoría
                categories = unified.get('categories', {})
                if categories:
                    report.append(f"\n   [DIRECTORIO] Por categoría:")
                    for cat, count in categories.items():
                        percentage = (count / unified.get('total_products', 1)) * 100
                        report.append(f"     {cat.title()}: {count} ({percentage:.1f}%)")
                
                # Por tienda
                stores = unified.get('stores', {})
                if stores:
                    report.append(f"\n   [EMOJI] Presencia por tienda:")
                    for store, count in stores.items():
                        report.append(f"     {store.upper()}: {count} productos")
        
        # Análisis de archivos
        files_info = stats.get("files", {})
        report.append(f"\n[ARCHIVOS] ANÁLISIS DE ARCHIVOS:")
        report.append(f"   Raw generados: {files_info.get('raw_generated', 0)}/6")
        report.append(f"   Procesado exitoso: {'[OK]' if files_info.get('processed_generated') else '[ERROR]'}")
        report.append(f"   Validación exitosa: {'[OK]' if files_info.get('final_validation') else '[ERROR]'}")
        
        if files_info.get('raw_files'):
            report.append(f"\n   Archivos raw generados:")
            for filename in files_info['raw_files']:
                report.append(f"     [ARCHIVO] {filename}")
        
        report.append("\n" + "=" * 70)
        
        return "\n".join(report)
    
    def generate_historical_report(self, limit: int = 5) -> str:
        """Genera reporte histórico de ejecuciones"""
        historical = self.load_historical_stats(limit)
        
        if not historical:
            return "[ERROR] No hay datos históricos disponibles"
        
        report = []
        report.append("=" * 70)
        report.append(f"[DATOS] REPORTE HISTÓRICO - ÚLTIMAS {len(historical)} EJECUCIONES")
        report.append("=" * 70)
        
        # Tabla resumen
        report.append(f"\n{'Fecha':<20} {'Duración':<12} {'Éxito':<8} {'Productos':<10} {'Tiendas':<8}")
        report.append("-" * 70)
        
        success_count = 0
        total_times = []
        
        for stats in historical:
            exec_info = stats.get("execution", {})
            timestamp = exec_info.get('timestamp', 'N/A')[:19]  # YYYY-MM-DD HH:MM:SS
            duration = exec_info.get('total_time_formatted', 'N/A')
            success = exec_info.get('success', False)
            if success:
                success_count += 1
            
            # Extraer tiempo para estadísticas
            if exec_info.get('total_time_seconds'):
                total_times.append(exec_info['total_time_seconds'])
            
            unified = stats.get("data_summary", {}).get("unified", {})
            productos = unified.get('total_products', 0)
            
            scrapers = stats.get("scrapers", {})
            tiendas_exitosas = scrapers.get('successful', 0)
            
            success_icon = "[OK]" if success else "[ERROR]"
            
            report.append(f"{timestamp:<20} {duration:<12} {success_icon:<8} {productos:<10} {tiendas_exitosas}/3")
        
        # Estadísticas generales
        report.append(f"\n[STATS] ESTADÍSTICAS GENERALES:")
        report.append(f"   Tasa de éxito: {success_count}/{len(historical)} ({(success_count/len(historical)*100):.1f}%)")
        
        if total_times:
            avg_time = sum(total_times) / len(total_times)
            min_time = min(total_times)
            max_time = max(total_times)
            
            report.append(f"   Tiempo promedio: {int(avg_time//60)}m {int(avg_time%60)}s")
            report.append(f"   Tiempo mínimo: {int(min_time//60)}m {int(min_time%60)}s")
            report.append(f"   Tiempo máximo: {int(max_time//60)}m {int(max_time%60)}s")
        
        # Análisis de tendencias
        if len(historical) >= 3:
            report.append(f"\n[DATOS] TENDENCIAS:")
            
            # Productos por ejecución (últimas 3)
            recent_products = []
            for stats in historical[:3]:
                unified = stats.get("data_summary", {}).get("unified", {})
                productos = unified.get('total_products', 0)
                if productos > 0:
                    recent_products.append(productos)
            
            if len(recent_products) >= 2:
                if recent_products[0] > recent_products[1]:
                    trend = "[DATOS] Incremento"
                elif recent_products[0] < recent_products[1]:
                    trend = "[EMOJI] Decremento"
                else:
                    trend = "[STATS] Estable"
                
                report.append(f"   Productos únicos: {trend}")
                report.append(f"     Última: {recent_products[0]}")
                if len(recent_products) > 1:
                    report.append(f"     Anterior: {recent_products[1]}")
        
        report.append("\n" + "=" * 70)
        
        return "\n".join(report)
    
    def generate_comparison_report(self) -> str:
        """Genera reporte de comparación entre tiendas"""
        try:
            stats = self.load_latest_stats()
        except FileNotFoundError:
            return "[ERROR] No hay datos disponibles para comparación"
        
        data_summary = stats.get("data_summary", {})
        unified = data_summary.get("unified", {})
        
        if not data_summary:
            return "[ERROR] No hay datos de resumen disponibles"
        
        report = []
        report.append("=" * 70)
        report.append("[EMOJI] REPORTE DE COMPARACIÓN ENTRE TIENDAS")
        report.append("=" * 70)
        
        # Análisis por tienda raw
        tiendas_raw = {}
        for key, info in data_summary.items():
            if key != "unified":
                tienda, categoria = key.split('_')
                if tienda not in tiendas_raw:
                    tiendas_raw[tienda] = {'total': 0, 'categorias': {}}
                
                productos = info.get("productos", 0)
                tiendas_raw[tienda]['total'] += productos
                tiendas_raw[tienda]['categorias'][categoria] = productos
        
        report.append(f"\n[STATS] PRODUCTOS EXTRAÍDOS (RAW):")
        report.append(f"{'Tienda':<12} {'Total':<8} {'Maquillaje':<12} {'Skincare':<10}")
        report.append("-" * 50)
        
        for tienda in sorted(tiendas_raw.keys()):
            info = tiendas_raw[tienda]
            total = info['total']
            maquillaje = info['categorias'].get('maquillaje', 0)
            skincare = info['categorias'].get('skincare', 0)
            
            report.append(f"{tienda.upper():<12} {total:<8} {maquillaje:<12} {skincare:<10}")
        
        # Análisis de presencia en datos unificados
        if unified and unified.get('stores'):
            stores = unified['stores']
            total_unified = unified.get('total_products', 1)
            
            report.append(f"\n[OBJETIVO] PRESENCIA EN DATOS UNIFICADOS:")
            report.append(f"{'Tienda':<12} {'Productos':<10} {'% Share':<10} {'Cobertura':<10}")
            report.append("-" * 50)
            
            for store in sorted(stores.keys()):
                count = stores[store]
                share = (count / total_unified) * 100
                
                # Calcular cobertura (vs raw)
                raw_total = tiendas_raw.get(store.lower(), {}).get('total', 1)
                coverage = (count / raw_total) * 100 if raw_total > 0 else 0
                
                report.append(f"{store.upper():<12} {count:<10} {share:<9.1f}% {coverage:<9.1f}%")
        
        # Análisis de competitividad
        if unified.get('multi_store_products', 0) > 0:
            multi_store = unified['multi_store_products']
            total_products = unified.get('total_products', 1)
            competition_rate = (multi_store / total_products) * 100
            
            report.append(f"\n🥊 ANÁLISIS DE COMPETENCIA:")
            report.append(f"   Productos con múltiples tiendas: {multi_store}")
            report.append(f"   Tasa de competencia: {competition_rate:.1f}%")
            report.append(f"   Productos exclusivos: {total_products - multi_store}")
        
        report.append("\n" + "=" * 70)
        
        return "\n".join(report)
    
    def save_report(self, report_content: str, report_type: str) -> str:
        """Guarda reporte en archivo"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"etl_report_{report_type}_{timestamp}.txt"
        filepath = self.project_root / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)
            return str(filepath)
        except Exception as e:
            print(f"[ERROR] Error guardando reporte: {e}")
            return ""

def main():
    parser = argparse.ArgumentParser(description='Generador de reportes ETL')
    parser.add_argument('--type', choices=['current', 'historical', 'comparison', 'all'],
                       default='current', help='Tipo de reporte a generar')
    parser.add_argument('--save', action='store_true', help='Guardar reporte en archivo')
    parser.add_argument('--limit', type=int, default=5, help='Límite para reporte histórico')
    
    args = parser.parse_args()
    
    analyzer = ETLStatsAnalyzer()
    
    try:
        if args.type == 'current':
            report = analyzer.generate_current_report()
            print(report)
            if args.save:
                filepath = analyzer.save_report(report, 'current')
                if filepath:
                    print(f"\n[ARCHIVO] Reporte guardado en: {filepath}")
        
        elif args.type == 'historical':
            report = analyzer.generate_historical_report(args.limit)
            print(report)
            if args.save:
                filepath = analyzer.save_report(report, 'historical')
                if filepath:
                    print(f"\n[ARCHIVO] Reporte guardado en: {filepath}")
        
        elif args.type == 'comparison':
            report = analyzer.generate_comparison_report()
            print(report)
            if args.save:
                filepath = analyzer.save_report(report, 'comparison')
                if filepath:
                    print(f"\n[ARCHIVO] Reporte guardado en: {filepath}")
        
        elif args.type == 'all':
            reports = {
                'current': analyzer.generate_current_report(),
                'historical': analyzer.generate_historical_report(args.limit),
                'comparison': analyzer.generate_comparison_report()
            }
            
            for report_type, content in reports.items():
                print(content)
                print("\n" + "[EMOJI]" * 70 + "\n")
                
                if args.save:
                    filepath = analyzer.save_report(content, report_type)
                    if filepath:
                        print(f"[ARCHIVO] Reporte {report_type} guardado en: {filepath}")
    
    except Exception as e:
        print(f"[ERROR] Error generando reporte: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

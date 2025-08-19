"""
Generador de estadísticas para el sistema ETL
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class StatsGenerator:
    """Generador de estadísticas detalladas para ETL"""
    
    def __init__(self, config, file_manager, logger):
        """
        Inicializa el generador de estadísticas
        
        Args:
            config: Instancia de ETLConfig
            file_manager: Instancia de FileManager
            logger: Instancia de Logger
        """
        self.config = config
        self.file_manager = file_manager
        self.logger = logger
    
    def generate_execution_stats(self, 
                               scraper_results: List[Dict],
                               processor_success: bool,
                               validation_success: bool,
                               total_time: float) -> Dict[str, Any]:
        """
        Genera estadísticas completas de ejecución
        
        Args:
            scraper_results: Resultados de los scrapers
            processor_success: Si el procesamiento fue exitoso
            validation_success: Si la validación fue exitosa
            total_time: Tiempo total de ejecución
            
        Returns:
            Dict con estadísticas completas
        """
        self.logger.info("[STATS] Generando estadísticas de ejecución...")
        
        stats = {
            "metadata": self._generate_metadata(total_time, processor_success, validation_success),
            "scrapers": self._generate_scraper_stats(scraper_results),
            "files": self._generate_file_stats(),
            "data_summary": self._generate_data_summary(),
            "performance": self._generate_performance_stats(total_time),
            "validation": self._generate_validation_stats(validation_success)
        }
        
        return stats
    
    def _generate_metadata(self, total_time: float, processor_success: bool, validation_success: bool) -> Dict:
        """Genera metadatos de la ejecución"""
        return {
            "timestamp": datetime.now().isoformat(),
            "total_time_seconds": round(total_time, 2),
            "total_time_formatted": f"{int(total_time // 60)}m {int(total_time % 60)}s",
            "success": processor_success and validation_success,
            "etl_version": "2.0.0",
            "config": {
                "headless": self.config.headless,
                "max_pages": self.config.max_pages,
                "max_workers": self.config.max_workers
            }
        }
    
    def _generate_scraper_stats(self, scraper_results: List[Dict]) -> Dict:
        """Genera estadísticas de scrapers"""
        successful = sum(1 for r in scraper_results if r["status"] == "success")
        failed = sum(1 for r in scraper_results if r["status"] == "error")
        
        details = {}
        for result in scraper_results:
            store = result["tienda"]
            details[store] = {
                "status": result["status"],
                "error": result.get("error") if result["status"] == "error" else None,
                "files_generated": self._count_store_files(store)
            }
        
        return {
            "total": len(scraper_results),
            "successful": successful,
            "failed": failed,
            "success_rate": round(successful / len(scraper_results) * 100, 1) if scraper_results else 0,
            "details": details
        }
    
    def _count_store_files(self, store_name: str) -> int:
        """Cuenta archivos generados por una tienda"""
        count = 0
        store_config = self.config.get_store_config(store_name.lower())
        
        for category in store_config.get("categories", []):
            file_path = self.config.get_raw_file_path(store_name.lower(), category)
            if file_path.exists():
                count += 1
        
        return count
    
    def _generate_file_stats(self) -> Dict:
        """Genera estadísticas de archivos"""
        file_status = self.file_manager.check_raw_files_exist()
        missing_files = self.file_manager.get_missing_raw_files()
        
        raw_files_info = {}
        total_raw_size = 0
        
        for filename in self.config.expected_raw_files:
            file_path = self.config.raw_dir / filename
            file_stats = self.file_manager.get_file_stats(file_path)
            raw_files_info[filename] = file_stats
            if file_stats["exists"]:
                total_raw_size += file_stats["size_bytes"]
        
        # Estadísticas del archivo procesado
        processed_stats = self.file_manager.get_file_stats(self.config.unified_products_path)
        
        return {
            "raw": {
                "total_expected": len(self.config.expected_raw_files),
                "generated": len([f for f in file_status.values() if f]),
                "missing": len(missing_files),
                "missing_files": missing_files,
                "total_size_mb": round(total_raw_size / (1024 * 1024), 2),
                "details": raw_files_info
            },
            "processed": {
                "exists": processed_stats["exists"],
                "size_mb": processed_stats["size_mb"],
                "records": processed_stats["records"],
                "modified": processed_stats["modified"]
            }
        }
    
    def _generate_data_summary(self) -> Dict:
        """Genera resumen de datos extraídos y procesados"""
        summary = {
            "raw_data": {},
            "unified_data": {},
            "deduplication": {}
        }
        
        # Analizar datos raw
        total_raw_products = 0
        raw_by_store = {}
        raw_by_category = {}
        
        for filename in self.config.expected_raw_files:
            if filename in self.file_manager.check_raw_files_exist() and \
               self.file_manager.check_raw_files_exist()[filename]:
                
                file_path = self.config.raw_dir / filename
                data = self.file_manager.load_json_file(file_path)
                
                if data and "productos" in data:
                    productos = data["productos"]
                    count = len(productos)
                    total_raw_products += count
                    
                    # Extraer tienda y categoría del nombre del archivo
                    parts = filename.replace('.json', '').split('_')
                    store = parts[0]
                    category = parts[1]
                    
                    raw_by_store[store] = raw_by_store.get(store, 0) + count
                    raw_by_category[category] = raw_by_category.get(category, 0) + count
                    
                    summary["raw_data"][filename] = {
                        "productos": count,
                        "tienda": data.get("tienda", store.upper()),
                        "categoria": data.get("categoria", category),
                        "fecha_extraccion": data.get("fecha_extraccion", "N/A")
                    }
        
        summary["raw_data"]["totals"] = {
            "total_products": total_raw_products,
            "by_store": raw_by_store,
            "by_category": raw_by_category
        }
        
        # Analizar datos unificados
        unified_data = self.file_manager.load_json_file(self.config.unified_products_path)
        if unified_data:
            unified_stats = self._analyze_unified_data(unified_data)
            summary["unified_data"] = unified_stats
            
            # Calcular estadísticas de deduplicación
            if total_raw_products > 0:
                dedup_rate = (1 - unified_stats["total_products"] / total_raw_products) * 100
                summary["deduplication"] = {
                    "raw_products": total_raw_products,
                    "unified_products": unified_stats["total_products"],
                    "deduplication_rate": round(dedup_rate, 1),
                    "multi_store_products": unified_stats["multi_store_products"],
                    "multi_store_rate": round(unified_stats["multi_store_products"] / unified_stats["total_products"] * 100, 1) if unified_stats["total_products"] > 0 else 0
                }
        
        return summary
    
    def _analyze_unified_data(self, unified_data: List[Dict]) -> Dict:
        """Analiza datos unificados en detalle"""
        stats = {
            "total_products": len(unified_data),
            "categories": {},
            "stores": {},
            "brands": {},
            "multi_store_products": 0,
            "price_stats": {
                "min_price": float('inf'),
                "max_price": 0,
                "avg_price": 0
            }
        }
        
        total_price = 0
        price_count = 0
        
        for product in unified_data:
            # Contar por categoría
            cat = product.get('categoria', 'unknown')
            stats["categories"][cat] = stats["categories"].get(cat, 0) + 1
            
            # Contar por marca
            brand = product.get('marca', 'unknown')
            stats["brands"][brand] = stats["brands"].get(brand, 0) + 1
            
            # Analizar tiendas y precios
            tiendas_producto = product.get('tiendas', [])
            if len(tiendas_producto) > 1:
                stats["multi_store_products"] += 1
            
            for tienda in tiendas_producto:
                fuente = tienda.get('fuente', 'unknown')
                stats["stores"][fuente] = stats["stores"].get(fuente, 0) + 1
                
                # Analizar precios
                try:
                    precio = float(tienda.get('precio', 0))
                    if precio > 0:
                        stats["price_stats"]["min_price"] = min(stats["price_stats"]["min_price"], precio)
                        stats["price_stats"]["max_price"] = max(stats["price_stats"]["max_price"], precio)
                        total_price += precio
                        price_count += 1
                except (ValueError, TypeError):
                    pass
        
        # Calcular precio promedio
        if price_count > 0:
            stats["price_stats"]["avg_price"] = round(total_price / price_count, 2)
        
        # Limpiar precio mínimo si no se encontraron precios
        if stats["price_stats"]["min_price"] == float('inf'):
            stats["price_stats"]["min_price"] = 0
        
        return stats
    
    def _generate_performance_stats(self, total_time: float) -> Dict:
        """Genera estadísticas de rendimiento"""
        unified_data = self.file_manager.load_json_file(self.config.unified_products_path)
        products_count = len(unified_data) if unified_data else 0
        
        return {
            "total_time_seconds": round(total_time, 2),
            "products_processed": products_count,
            "products_per_second": round(products_count / total_time, 2) if total_time > 0 else 0,
            "average_scraper_time": round(total_time / 3, 2) if total_time > 0 else 0  # Asumiendo 3 scrapers
        }
    
    def _generate_validation_stats(self, validation_success: bool) -> Dict:
        """Genera estadísticas de validación"""
        return {
            "final_validation": validation_success,
            "required_fields_check": validation_success,
            "data_integrity_check": validation_success
        }
    
    def save_stats(self, stats: Dict[str, Any]) -> Optional[str]:
        """
        Guarda estadísticas en archivo JSON
        
        Args:
            stats: Estadísticas a guardar
            
        Returns:
            Path del archivo guardado o None si hay error
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        stats_file = self.config.get_stats_file_path(timestamp)
        
        if self.file_manager.save_json_file(stats, stats_file):
            self.logger.info(f"[STATS] Estadísticas guardadas en: {stats_file}")
            return str(stats_file)
        else:
            self.logger.error("[STATS] Error guardando estadísticas")
            return None
    
    def print_execution_summary(self, stats: Dict[str, Any]) -> None:
        """Imprime resumen de ejecución en consola"""
        print("\n" + "="*60)
        print("[STATS] RESUMEN DETALLADO DE EJECUCIÓN ETL v2.0")
        print("="*60)
        
        # Información general
        metadata = stats["metadata"]
        print(f"[TIEMPO] Tiempo total: {metadata['total_time_formatted']}")
        print(f"[OK] Éxito general: {'SÍ' if metadata['success'] else 'NO'}")
        print(f"[TIMESTAMP] Ejecutado: {metadata['timestamp']}")
        
        # Scrapers
        scraper_stats = stats["scrapers"]
        print(f"\n[SCRAPERS] EXTRACCIÓN:")
        print(f"   Éxito: {scraper_stats['successful']}/{scraper_stats['total']} ({scraper_stats['success_rate']}%)")
        
        for store, details in scraper_stats["details"].items():
            status_icon = "[OK]" if details["status"] == "success" else "[ERROR]"
            print(f"   {status_icon} {store}: {details['files_generated']} archivos")
        
        # Datos
        data_summary = stats["data_summary"]
        if "raw_data" in data_summary and "totals" in data_summary["raw_data"]:
            raw_totals = data_summary["raw_data"]["totals"]
            print(f"\n[DATOS RAW] EXTRACCIÓN:")
            print(f"   Total productos: {raw_totals['total_products']}")
            for store, count in raw_totals["by_store"].items():
                print(f"     {store.upper()}: {count}")
        
        if "unified_data" in data_summary:
            unified = data_summary["unified_data"]
            print(f"\n[DATOS UNIFICADOS] TRANSFORMACIÓN:")
            print(f"   Total productos: {unified['total_products']}")
            print(f"   Multi-tienda: {unified['multi_store_products']}")
            print(f"   Categorías: {len(unified['categories'])}")
            print(f"   Marcas: {len(unified['brands'])}")
        
        if "deduplication" in data_summary:
            dedup = data_summary["deduplication"]
            print(f"\n[DEDUPLICACIÓN] OPTIMIZACIÓN:")
            print(f"   Tasa deduplicación: {dedup['deduplication_rate']}%")
            print(f"   {dedup['raw_products']} raw → {dedup['unified_products']} únicos")
        
        # Rendimiento
        performance = stats["performance"]
        print(f"\n[RENDIMIENTO]:")
        print(f"   Productos/segundo: {performance['products_per_second']}")
        print(f"   Tiempo promedio por scraper: {performance['average_scraper_time']}s")
        
        print("="*60)



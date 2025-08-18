#!/usr/bin/env python3
"""
Pipeline ETL completo para CotizaBelleza
Ejecuta scrapers -> procesa raw data -> genera unified data

Uso: python etl_pipeline.py [--headless] [--max-pages N]
"""

import os
import sys
import json
import time
import shutil
import logging
import argparse
import subprocess
import multiprocessing
from pathlib import Path
from typing import List, Dict, Any
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('etl_pipeline.log')
    ]
)
logger = logging.getLogger('ETL_Pipeline')

class ETLPipeline:
    """Pipeline ETL completo para scraping y procesamiento de datos"""
    
    def __init__(self, headless: bool = True, max_pages: int = None):
        self.headless = headless
        self.max_pages = max_pages
        self.project_root = Path(__file__).parent
        self.raw_dir = self.project_root / "data" / "raw"
        self.processed_dir = self.project_root / "data" / "processed"
        
        # Crear directorios si no existen
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Archivos esperados después del scraping
        self.expected_files = [
            "dbs_maquillaje.json",
            "dbs_skincare.json", 
            "maicao_maquillaje.json",
            "maicao_skincare.json",
            "preunic_maquillaje.json",
            "preunic_skincare.json"
        ]
    
    def run_scraper_dbs(self) -> Dict[str, Any]:
        """Ejecuta el scraper de DBS"""
        logger.info("[INICIANDO] Iniciando scraper DBS...")
        try:
            # Importar y ejecutar scraper DBS
            sys.path.append(str(self.project_root / "scraper" / "scrapers"))
            from dbs_selenium_scraper import scrapear_todas_categorias as dbs_scraper
            
            resultado = dbs_scraper(
                headless=self.headless,
                max_paginas_por_categoria=self.max_pages
            )
            
            logger.info("[OK] Scraper DBS completado")
            return {"status": "success", "tienda": "DBS", "resultado": resultado}
            
        except Exception as e:
            logger.error(f"[ERROR] Error en scraper DBS: {e}")
            return {"status": "error", "tienda": "DBS", "error": str(e)}
    
    def run_scraper_maicao(self) -> Dict[str, Any]:
        """Ejecuta el scraper de Maicao"""
        logger.info("[INICIANDO] Iniciando scraper Maicao...")
        try:
            # Importar y ejecutar scraper Maicao
            sys.path.append(str(self.project_root / "scraper" / "scrapers"))
            from maicao_selenium_scraper import scrape_maicao_all_categories as maicao_scraper
            
            resultado = maicao_scraper(
                headless=self.headless,
                max_pages_per_category=self.max_pages
            )
            
            logger.info("[OK] Scraper Maicao completado")
            return {"status": "success", "tienda": "Maicao", "resultado": resultado}
            
        except Exception as e:
            logger.error(f"[ERROR] Error en scraper Maicao: {e}")
            return {"status": "error", "tienda": "Maicao", "error": str(e)}
    
    def run_scraper_preunic(self) -> Dict[str, Any]:
        """Ejecuta el scraper de Preunic"""
        logger.info("[INICIANDO] Iniciando scraper Preunic...")
        try:
            # Importar y ejecutar scraper Preunic
            sys.path.append(str(self.project_root / "scraper" / "scrapers"))
            from preunic_selenium_scraper import scrapear_todas_categorias_preunic as preunic_scraper
            
            # Preunic usa scroll infinito, no páginas
            max_scrolls = self.max_pages * 5 if self.max_pages else None
            
            resultado = preunic_scraper(
                headless=self.headless,
                max_scrolls=max_scrolls or 50  # Sin limite = 50 scrolls por defecto
            )
            
            logger.info("[OK] Scraper Preunic completado")
            return {"status": "success", "tienda": "Preunic", "resultado": resultado}
            
        except Exception as e:
            logger.error(f"[ERROR] Error en scraper Preunic: {e}")
            return {"status": "error", "tienda": "Preunic", "error": str(e)}
    
    def move_scraped_files_to_raw(self) -> None:
        """Mueve archivos generados por scrapers a data/raw/"""
        logger.info("[ARCHIVOS] Moviendo archivos a data/raw/...")
        
        # Directorios donde pueden estar los archivos generados
        source_dirs = [
            self.project_root / "scraper" / "data",
            self.project_root / "data"
        ]
        
        moved_count = 0
        
        for source_dir in source_dirs:
            if not source_dir.exists():
                continue
                
            # Buscar archivos JSON de las tiendas
            for pattern in ["*_maquillaje*.json", "*_skincare*.json"]:
                for file_path in source_dir.glob(pattern):
                    # Determinar nombre final sin timestamp
                    filename = file_path.name
                    for tienda in ["dbs", "maicao", "preunic"]:
                        for categoria in ["maquillaje", "skincare"]:
                            if tienda in filename.lower() and categoria in filename.lower():
                                target_name = f"{tienda}_{categoria}.json"
                                target_path = self.raw_dir / target_name
                                
                                # Mover archivo
                                shutil.move(str(file_path), str(target_path))
                                logger.info(f"[MOVIDO] Movido: {filename} -> {target_name}")
                                moved_count += 1
                                break
        
        logger.info(f"[ARCHIVOS] {moved_count} archivos movidos a data/raw/")
    
    def run_scrapers_parallel(self) -> List[Dict[str, Any]]:
        """Ejecuta todos los scrapers en paralelo"""
        logger.info("[EJECUTANDO] Iniciando scrapers en paralelo...")
        
        scrapers = [
            self.run_scraper_dbs,
            self.run_scraper_maicao,
            self.run_scraper_preunic
        ]
        
        results = []
        start_time = time.time()
        
        # Ejecutar scrapers en paralelo
        with ProcessPoolExecutor(max_workers=3) as executor:
            # Enviar tareas
            future_to_scraper = {
                executor.submit(scraper): scraper.__name__ 
                for scraper in scrapers
            }
            
            # Recoger resultados conforme completan
            for future in as_completed(future_to_scraper):
                scraper_name = future_to_scraper[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result["status"] == "success":
                        logger.info(f"[OK] {result['tienda']} completado exitosamente")
                    else:
                        logger.error(f"[ERROR] {result['tienda']} falló: {result['error']}")
                        
                except Exception as e:
                    logger.error(f"[ERROR] Error inesperado en {scraper_name}: {e}")
                    results.append({
                        "status": "error", 
                        "tienda": scraper_name, 
                        "error": str(e)
                    })
        
        elapsed_time = time.time() - start_time
        successful = sum(1 for r in results if r["status"] == "success")
        
        logger.info(f"[COMPLETADO] Scrapers completados en {elapsed_time:.1f}s - {successful}/3 exitosos")
        
        return results
    
    def run_processor(self) -> bool:
        """Ejecuta el processor para generar unified_products.json"""
        logger.info("[PROCESANDO] Iniciando processor...")
        
        try:
            # Verificar que existen archivos raw necesarios
            missing_files = []
            for filename in self.expected_files:
                if not (self.raw_dir / filename).exists():
                    missing_files.append(filename)
            
            if missing_files:
                logger.warning(f"[ADVERTENCIA] Archivos faltantes en raw: {missing_files}")
                logger.info("Continuando con archivos disponibles...")
            
            # Ejecutar processor
            sys.path.append(str(self.project_root / "processor"))
            from normalize import main as run_processor
            
            # Cambiar directorio de trabajo temporalmente
            original_cwd = os.getcwd()
            os.chdir(str(self.project_root / "processor"))
            
            try:
                # Ejecutar processor con argumentos
                sys.argv = [
                    'normalize.py',
                    '--out', '../data/processed/unified_products.json'
                ]
                
                result = run_processor()
                
                if result == 0:
                    logger.info("[OK] Processor completado exitosamente")
                    return True
                else:
                    logger.error("[ERROR] Processor falló")
                    return False
                    
            finally:
                os.chdir(original_cwd)
                
        except Exception as e:
            logger.error(f"[ERROR] Error en processor: {e}")
            return False
    
    def validate_final_output(self) -> bool:
        """Valida que el archivo final unified_products.json sea correcto"""
        logger.info("[VALIDANDO] Validando salida final...")
        
        output_file = self.processed_dir / "unified_products.json"
        
        if not output_file.exists():
            logger.error("[ERROR] Archivo unified_products.json no encontrado")
            return False
        
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                logger.error("[ERROR] Archivo debe contener una lista")
                return False
            
            if len(data) == 0:
                logger.warning("[ADVERTENCIA] Archivo está vacío")
                return False
            
            # Verificar estructura básica
            sample = data[0]
            required_fields = ['product_id', 'nombre', 'marca', 'categoria', 'tiendas']
            
            for field in required_fields:
                if field not in sample:
                    logger.error(f"[ERROR] Campo requerido faltante: {field}")
                    return False
            
            logger.info(f"[OK] Archivo válido: {len(data)} productos unificados")
            
            # Estadísticas
            categorias = {}
            tiendas_count = {}
            
            for product in data:
                cat = product.get('categoria', 'unknown')
                categorias[cat] = categorias.get(cat, 0) + 1
                
                for tienda in product.get('tiendas', []):
                    fuente = tienda.get('fuente', 'unknown')
                    tiendas_count[fuente] = tiendas_count.get(fuente, 0) + 1
            
            logger.info(f"[STATS] Por categoría: {dict(categorias)}")
            logger.info(f"[STATS] Por tienda: {dict(tiendas_count)}")
            
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Error validando archivo: {e}")
            return False
    
    def generate_execution_stats(self, scraper_results: List[Dict], processor_success: bool, 
                               validation_success: bool, total_time: float) -> Dict[str, Any]:
        """Genera estadísticas detalladas de la ejecución"""
        logger.info("[STATS] Generando estadísticas de ejecución...")
        
        stats = {
            "execution": {
                "timestamp": datetime.now().isoformat(),
                "total_time_seconds": round(total_time, 2),
                "total_time_formatted": f"{int(total_time // 60)}m {int(total_time % 60)}s",
                "success": processor_success and validation_success
            },
            "scrapers": {
                "total": len(scraper_results),
                "successful": sum(1 for r in scraper_results if r["status"] == "success"),
                "failed": sum(1 for r in scraper_results if r["status"] == "error"),
                "details": {}
            },
            "files": {
                "raw_generated": 0,
                "raw_files": [],
                "processed_generated": processor_success,
                "final_validation": validation_success
            },
            "data_summary": {}
        }
        
        # Detalles de scrapers
        for result in scraper_results:
            tienda = result["tienda"]
            stats["scrapers"]["details"][tienda] = {
                "status": result["status"],
                "error": result.get("error") if result["status"] == "error" else None
            }
        
        # Verificar archivos raw generados
        for filename in self.expected_files:
            file_path = self.raw_dir / filename
            if file_path.exists():
                stats["files"]["raw_generated"] += 1
                stats["files"]["raw_files"].append(filename)
                
                # Obtener estadísticas del archivo
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_data = json.load(f)
                    
                    tienda = filename.split('_')[0]
                    categoria = filename.split('_')[1].replace('.json', '')
                    
                    key = f"{tienda}_{categoria}"
                    stats["data_summary"][key] = {
                        "productos": len(file_data.get('productos', [])),
                        "tienda": file_data.get('tienda', tienda.upper()),
                        "categoria": file_data.get('categoria', categoria),
                        "fecha_extraccion": file_data.get('fecha_extraccion', 'N/A')
                    }
                    
                except Exception as e:
                    logger.warning(f"No se pudo leer estadísticas de {filename}: {e}")
        
        # Estadísticas del archivo final procesado
        if validation_success:
            try:
                output_file = self.processed_dir / "unified_products.json"
                with open(output_file, 'r', encoding='utf-8') as f:
                    unified_data = json.load(f)
                
                stats["data_summary"]["unified"] = {
                    "total_products": len(unified_data),
                    "categories": {},
                    "stores": {},
                    "multi_store_products": 0
                }
                
                for product in unified_data:
                    # Contar por categoría
                    cat = product.get('categoria', 'unknown')
                    stats["data_summary"]["unified"]["categories"][cat] = \
                        stats["data_summary"]["unified"]["categories"].get(cat, 0) + 1
                    
                    # Contar por tienda y productos multi-tienda
                    tiendas_producto = product.get('tiendas', [])
                    if len(tiendas_producto) > 1:
                        stats["data_summary"]["unified"]["multi_store_products"] += 1
                    
                    for tienda in tiendas_producto:
                        fuente = tienda.get('fuente', 'unknown')
                        stats["data_summary"]["unified"]["stores"][fuente] = \
                            stats["data_summary"]["unified"]["stores"].get(fuente, 0) + 1
                
            except Exception as e:
                logger.warning(f"No se pudieron obtener estadísticas del archivo unificado: {e}")
        
        return stats
    
    def save_execution_stats(self, stats: Dict[str, Any]) -> str:
        """Guarda las estadísticas en un archivo JSON"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        stats_file = self.project_root / f"etl_stats_{timestamp}.json"
        
        try:
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            
            logger.info(f"[STATS] Estadísticas guardadas en: {stats_file}")
            return str(stats_file)
            
        except Exception as e:
            logger.error(f"[ERROR] Error guardando estadísticas: {e}")
            return ""
    
    def print_execution_summary(self, stats: Dict[str, Any]) -> None:
        """Imprime un resumen detallado de la ejecución"""
        print("\n" + "="*60)
        print("[STATS] RESUMEN DETALLADO DE EJECUCIÓN")
        print("="*60)
        
        # Información general
        exec_info = stats["execution"]
        print(f"[TIEMPO] Tiempo total: {exec_info['total_time_formatted']}")
        print(f"[OK] Éxito general: {'SÍ' if exec_info['success'] else 'NO'}")
        print(f"[TIMESTAMP] Timestamp: {exec_info['timestamp']}")
        
        # Scrapers
        print(f"\n[SCRAPERS] SCRAPERS:")
        scraper_info = stats["scrapers"]
        print(f"   Total: {scraper_info['total']}")
        print(f"   Exitosos: {scraper_info['successful']}")
        print(f"   Fallidos: {scraper_info['failed']}")
        
        for tienda, details in scraper_info["details"].items():
            status_icon = "[OK]" if details["status"] == "success" else "[ERROR]"
            print(f"   {status_icon} {tienda}: {details['status']}")
            if details.get("error"):
                print(f"      Error: {details['error']}")
        
        # Archivos
        print(f"\n[ARCHIVOS] ARCHIVOS:")
        file_info = stats["files"]
        print(f"   Raw generados: {file_info['raw_generated']}/6")
        print(f"   Procesado: {'[OK]' if file_info['processed_generated'] else '[ERROR]'}")
        print(f"   Validación: {'[OK]' if file_info['final_validation'] else '[ERROR]'}")
        
        # Datos por archivo
        print(f"\n[DATOS] DATOS EXTRAÍDOS:")
        data_summary = stats["data_summary"]
        
        total_raw_products = 0
        for key, info in data_summary.items():
            if key != "unified":
                productos = info["productos"]
                total_raw_products += productos
                print(f"   {key}: {productos} productos")
        
        if "unified" in data_summary:
            unified_info = data_summary["unified"]
            print(f"\n[UNIFICADOS] DATOS UNIFICADOS:")
            print(f"   Total productos: {unified_info['total_products']}")
            print(f"   Productos multi-tienda: {unified_info['multi_store_products']}")
            
            print(f"   Por categoría:")
            for cat, count in unified_info["categories"].items():
                print(f"     {cat}: {count}")
            
            print(f"   Por tienda:")
            for store, count in unified_info["stores"].items():
                print(f"     {store}: {count}")
            
            # Cálculo de eficiencia de deduplicación
            if total_raw_products > 0:
                dedup_efficiency = (1 - unified_info['total_products'] / total_raw_products) * 100
                print(f"\n[STATS] Eficiencia deduplicación: {dedup_efficiency:.1f}%")
                print(f"   ({total_raw_products} raw -> {unified_info['total_products']} únicos)")
        
        print("="*60)
    
    def run_full_pipeline(self) -> bool:
        """Ejecuta el pipeline completo: scrapers -> raw -> processor -> unified"""
        start_time = time.time()
        
        logger.info("[INICIANDO] INICIANDO PIPELINE ETL COMPLETO")
        logger.info(f"Configuración: headless={self.headless}, max_pages={self.max_pages}")
        
        # Paso 1: Ejecutar scrapers en paralelo
        logger.info("\n" + "="*50)
        logger.info("PASO 1: EJECUTANDO SCRAPERS")
        logger.info("="*50)
        
        scraper_results = self.run_scrapers_parallel()
        successful_scrapers = sum(1 for r in scraper_results if r["status"] == "success")
        
        if successful_scrapers == 0:
            logger.error("[ERROR] Todos los scrapers fallaron. Abortando pipeline.")
            return False
        
        # Paso 2: Mover archivos a raw
        logger.info("\n" + "="*50)
        logger.info("PASO 2: ORGANIZANDO ARCHIVOS RAW")
        logger.info("="*50)
        
        self.move_scraped_files_to_raw()
        
        # Paso 3: Ejecutar processor
        logger.info("\n" + "="*50)
        logger.info("PASO 3: PROCESANDO DATOS")
        logger.info("="*50)
        
        processor_success = self.run_processor()
        
        if not processor_success:
            logger.error("[ERROR] Processor falló. Pipeline incompleto.")
            # Continuar para generar estadísticas parciales
        
        # Paso 4: Validar salida final
        logger.info("\n" + "="*50)
        logger.info("PASO 4: VALIDACIÓN FINAL")
        logger.info("="*50)
        
        validation_success = self.validate_final_output() if processor_success else False
        
        # Paso 5: Generar estadísticas
        logger.info("\n" + "="*50)
        logger.info("PASO 5: GENERANDO ESTADÍSTICAS")
        logger.info("="*50)
        
        total_time = time.time() - start_time
        stats = self.generate_execution_stats(
            scraper_results, processor_success, validation_success, total_time
        )
        
        # Guardar estadísticas
        stats_file = self.save_execution_stats(stats)
        
        # Mostrar resumen
        self.print_execution_summary(stats)
        
        # Resumen final
        logger.info("\n" + "="*50)
        logger.info("RESUMEN FINAL")
        logger.info("="*50)
        logger.info(f"[TIEMPO] Tiempo total: {total_time:.1f}s")
        logger.info(f"[SCRAPERS] Scrapers exitosos: {successful_scrapers}/3")
        logger.info(f"[PROCESANDO] Processor: {'[OK]' if processor_success else '[ERROR]'}")
        logger.info(f"[VALIDANDO] Validación: {'[OK]' if validation_success else '[ERROR]'}")
        logger.info(f"[STATS] Estadísticas: {stats_file}")
        
        final_success = processor_success and validation_success
        
        if final_success:
            logger.info("[EXITO] PIPELINE ETL COMPLETADO EXITOSAMENTE")
            logger.info(f"[ARCHIVO] Archivo final: {self.processed_dir}/unified_products.json")
        else:
            logger.error("[ERROR] PIPELINE FALLÓ O INCOMPLETO")
        
        return final_success


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Pipeline ETL completo para CotizaBelleza')
    parser.add_argument('--headless', action='store_true', default=True,
                       help='Ejecutar scrapers en modo headless (default: True)')
    parser.add_argument('--visible', action='store_true',
                       help='Ejecutar scrapers con navegador visible (override headless)')
    parser.add_argument('--max-pages', type=int, 
                       help='Límite de páginas por categoría (default: sin límite)')
    parser.add_argument('--stats-only', action='store_true',
                       help='Solo generar estadísticas del último archivo unificado')
    
    args = parser.parse_args()
    
    # Modo solo estadísticas
    if args.stats_only:
        pipeline = ETLPipeline()
        if (pipeline.processed_dir / "unified_products.json").exists():
            print("[STATS] Generando estadísticas del archivo existente...")
            success = pipeline.validate_final_output()
            if success:
                print("[OK] Estadísticas generadas exitosamente")
            else:
                print("[ERROR] Error generando estadísticas")
        else:
            print("[ERROR] No existe archivo unified_products.json")
        return
    
    # Determinar modo headless
    headless = args.headless and not args.visible
    
    # Crear y ejecutar pipeline
    pipeline = ETLPipeline(headless=headless, max_pages=args.max_pages)
    
    try:
        success = pipeline.run_full_pipeline()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("\n[ADVERTENCIA] Pipeline interrumpido por usuario")
        sys.exit(130)
    except Exception as e:
        logger.error(f"[ERROR] Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

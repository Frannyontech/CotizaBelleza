"""
Orquestador de scrapers para el sistema ETL
"""

import sys
import time
from pathlib import Path
from typing import Dict, List, Any
from concurrent.futures import ProcessPoolExecutor, as_completed


class ScraperOrchestrator:
    """Orquestador para ejecutar scrapers en paralelo"""
    
    def __init__(self, config, logger):
        """
        Inicializa el orquestador de scrapers
        
        Args:
            config: Instancia de ETLConfig
            logger: Instancia de Logger
        """
        self.config = config
        self.logger = logger
    
    def run_all_scrapers(self) -> List[Dict[str, Any]]:
        """
        Ejecuta todos los scrapers en paralelo
        
        Returns:
            Lista de resultados de cada scraper
        """
        self.logger.info("[SCRAPERS] Iniciando scrapers en paralelo...")
        
        scrapers = [
            ("dbs", self._run_dbs_scraper),
            ("maicao", self._run_maicao_scraper), 
            ("preunic", self._run_preunic_scraper)
        ]
        
        results = []
        start_time = time.time()
        
        # Ejecutar scrapers en paralelo
        with ProcessPoolExecutor(max_workers=self.config.max_workers) as executor:
            # Enviar tareas
            future_to_scraper = {
                executor.submit(scraper_func): scraper_name 
                for scraper_name, scraper_func in scrapers
            }
            
            # Recoger resultados conforme completan
            for future in as_completed(future_to_scraper):
                scraper_name = future_to_scraper[future]
                try:
                    result = future.result(timeout=self.config.scraper_timeout)
                    results.append(result)
                    
                    if result["status"] == "success":
                        self.logger.info(f"[OK] {result['tienda']} completado exitosamente")
                    else:
                        self.logger.error(f"[ERROR] {result['tienda']} falló: {result['error']}")
                        
                except Exception as e:
                    self.logger.error(f"[ERROR] Error inesperado en {scraper_name}: {e}")
                    results.append({
                        "status": "error", 
                        "tienda": scraper_name, 
                        "error": str(e)
                    })
        
        elapsed_time = time.time() - start_time
        successful = sum(1 for r in results if r["status"] == "success")
        
        self.logger.info(f"[COMPLETADO] Scrapers completados en {elapsed_time:.1f}s - {successful}/3 exitosos")
        
        return results
    
    def _run_dbs_scraper(self) -> Dict[str, Any]:
        """Ejecuta el scraper de DBS"""
        return self._run_single_scraper("dbs")
    
    def _run_maicao_scraper(self) -> Dict[str, Any]:
        """Ejecuta el scraper de Maicao"""
        return self._run_single_scraper("maicao")
    
    def _run_preunic_scraper(self) -> Dict[str, Any]:
        """Ejecuta el scraper de Preunic"""
        return self._run_single_scraper("preunic")
    
    def _run_single_scraper(self, store_name: str) -> Dict[str, Any]:
        """
        Ejecuta un scraper individual
        
        Args:
            store_name: Nombre de la tienda
            
        Returns:
            Dict con resultado del scraper
        """
        self.logger.info(f"[INICIANDO] Iniciando scraper {store_name.upper()}...")
        
        try:
            store_config = self.config.get_store_config(store_name)
            if not store_config:
                raise ValueError(f"Configuración no encontrada para {store_name}")
            
            # Importar y ejecutar scraper dinámicamente
            sys.path.append(str(self.config.project_root / "scraper" / "scrapers"))
            
            module_name = store_config["scraper_module"].split('.')[-1]
            scraper_module = __import__(module_name)
            scraper_function = getattr(scraper_module, store_config["scraper_function"])
            
            # Preparar argumentos según el tipo de scraper
            kwargs = {"headless": self.config.headless}
            
            if store_config.get("uses_pages", True):
                if store_name == "dbs":
                    kwargs["max_paginas_por_categoria"] = self.config.max_pages
                elif store_name == "maicao":
                    kwargs["max_pages_per_category"] = self.config.max_pages
            else:
                # Preunic usa API de Algolia - no necesita argumentos especiales
                # El scraper maneja internamente la paginación de la API
                pass
            
            # Ejecutar scraper
            resultado = scraper_function(**kwargs)
            
            self.logger.info(f"[OK] Scraper {store_name.upper()} completado")
            return {
                "status": "success", 
                "tienda": store_config["name"], 
                "resultado": resultado,
                "store_code": store_name
            }
            
        except Exception as e:
            self.logger.error(f"[ERROR] Error en scraper {store_name.upper()}: {e}")
            return {
                "status": "error", 
                "tienda": store_name.upper(), 
                "error": str(e),
                "store_code": store_name
            }


class ScraperValidator:
    """Validador específico para resultados de scrapers"""
    
    def __init__(self, config, logger):
        """
        Inicializa el validador de scrapers
        
        Args:
            config: Instancia de ETLConfig
            logger: Instancia de Logger
        """
        self.config = config
        self.logger = logger
    
    def validate_scraper_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Valida los resultados de todos los scrapers
        
        Args:
            results: Lista de resultados de scrapers
            
        Returns:
            Dict con estadísticas de validación
        """
        validation = {
            "total_scrapers": len(results),
            "successful": 0,
            "failed": 0,
            "details": {},
            "files_generated": {},
            "overall_success": False
        }
        
        for result in results:
            store_code = result.get("store_code", result.get("tienda", "unknown").lower())
            
            if result["status"] == "success":
                validation["successful"] += 1
                
                # Verificar archivos generados
                files_count = self._count_generated_files(store_code)
                validation["files_generated"][store_code] = files_count
                
                validation["details"][store_code] = {
                    "status": "success",
                    "files_generated": files_count,
                    "expected_files": len(self.config.get_store_config(store_code).get("categories", [])),
                    "complete": files_count > 0
                }
            else:
                validation["failed"] += 1
                validation["details"][store_code] = {
                    "status": "failed",
                    "error": result.get("error", "Unknown error"),
                    "files_generated": 0,
                    "complete": False
                }
        
        # Determinar éxito general
        validation["overall_success"] = validation["successful"] > 0
        
        # Log resumen
        self.logger.info(f"[VALIDACIÓN] Scrapers exitosos: {validation['successful']}/{validation['total_scrapers']}")
        for store, details in validation["details"].items():
            if details["status"] == "success":
                self.logger.info(f"[VALIDACIÓN] {store.upper()}: {details['files_generated']} archivos generados")
            else:
                self.logger.error(f"[VALIDACIÓN] {store.upper()}: FALLÓ - {details['error']}")
        
        return validation
    
    def _count_generated_files(self, store_name: str) -> int:
        """
        Cuenta archivos generados por un scraper específico
        
        Args:
            store_name: Nombre de la tienda
            
        Returns:
            Número de archivos encontrados
        """
        count = 0
        store_config = self.config.get_store_config(store_name)
        
        for category in store_config.get("categories", []):
            file_path = self.config.get_raw_file_path(store_name, category)
            if file_path.exists():
                count += 1
        
        return count
    
    def get_missing_files(self) -> List[str]:
        """
        Obtiene lista de archivos esperados que no fueron generados
        
        Returns:
            Lista de archivos faltantes
        """
        missing = []
        
        for filename in self.config.expected_raw_files:
            file_path = self.config.raw_dir / filename
            if not file_path.exists():
                missing.append(filename)
        
        return missing



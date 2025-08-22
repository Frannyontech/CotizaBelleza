"""
Orquestador principal del sistema ETL
"""

import time
from datetime import datetime
from typing import Dict, Any, Optional

from .config import ETLConfig
from .utils import FileManager, get_pipeline_logger, StatsGenerator, DataValidator
from .scrapers import ScraperOrchestrator, ScraperValidator
from .processor import ProcessorOrchestrator


class ETLOrchestrator:
    """Orquestador principal del pipeline ETL"""
    
    def __init__(self, config: Optional[ETLConfig] = None):
        """
        Inicializa el orquestador ETL
        
        Args:
            config: Configuración ETL (opcional, se crea una por defecto)
        """
        self.config = config or ETLConfig()
        self.logger = get_pipeline_logger(self.config)
        
        # Inicializar componentes
        self.file_manager = FileManager(self.config)
        self.file_manager.set_logger(self.logger)
        
        self.stats_generator = StatsGenerator(self.config, self.file_manager, self.logger)
        self.validator = DataValidator(self.config, self.logger)
        
        self.scraper_orchestrator = ScraperOrchestrator(self.config, self.logger)
        self.scraper_validator = ScraperValidator(self.config, self.logger)
        
        self.processor_orchestrator = ProcessorOrchestrator(self.config, self.logger)
        
        # Validar configuración
        if not self.config.validate_configuration():
            self.logger.error("[ERROR] Configuración ETL inválida")
            raise ValueError("Configuración ETL inválida")
    
    def run_full_pipeline(self) -> bool:
        """
        Ejecuta el pipeline ETL completo
        
        Returns:
            True si el pipeline fue exitoso
        """
        start_time = time.time()
        
        self.logger.info("=" * 60)
        self.logger.info("INICIANDO PIPELINE ETL COMPLETO v2.0")
        self.logger.info("=" * 60)
        self.logger.info(f"Configuración: headless={self.config.headless}, max_pages={self.config.max_pages}")
        
        # Variables para tracking de éxito
        scraper_results = []
        processor_success = False
        validation_success = False
        
        try:
            # Paso 1: Ejecutar scrapers
            scraper_step_logger = get_pipeline_logger(self.config, "SCRAPERS")
            scraper_step_logger.start("Ejecutando scrapers en paralelo")
            
            scraper_results = self.scraper_orchestrator.run_all_scrapers()
            scraper_validation = self.scraper_validator.validate_scraper_results(scraper_results)
            
            successful_scrapers = scraper_validation["successful"]
            if successful_scrapers == 0:
                scraper_step_logger.error("Todos los scrapers fallaron. Abortando pipeline.")
                return False
            
            scraper_step_logger.finish(True, f"{successful_scrapers}/3 scrapers exitosos")
            
            # Paso 2: Organizar archivos
            file_step_logger = get_pipeline_logger(self.config, "ARCHIVOS")
            file_step_logger.start("Organizando archivos raw")
            
            moved_files = self.file_manager.move_scraped_files_to_raw()
            file_step_logger.finish(True, f"{moved_files} archivos organizados")
            
            # Paso 3: Procesar datos
            processor_step_logger = get_pipeline_logger(self.config, "PROCESAMIENTO")
            processor_step_logger.start("Procesando y unificando datos")
            
            processor_success = self.processor_orchestrator.run_processor()
            processor_step_logger.finish(processor_success, 
                                       "Datos unificados exitosamente" if processor_success else "Error en procesamiento")
            
            # Paso 4: Validación final
            validation_step_logger = get_pipeline_logger(self.config, "VALIDACIÓN")
            validation_step_logger.start("Validando datos finales")
            
            if processor_success:
                validation_success, validation_errors = self.validator.validate_unified_data()
                if validation_success:
                    validation_step_logger.finish(True, "Datos válidos")
                else:
                    validation_step_logger.error(f"Errores de validación: {len(validation_errors)}")
                    for error in validation_errors[:3]:
                        validation_step_logger.error(f"  - {error}")
                    validation_step_logger.finish(False, "Validación falló")
            else:
                validation_step_logger.finish(False, "Saltado por error en procesamiento")
            
            # Paso 5: Generar estadísticas
            stats_step_logger = get_pipeline_logger(self.config, "ESTADÍSTICAS")
            stats_step_logger.start("Generando estadísticas")
            
            total_time = time.time() - start_time
            stats = self.stats_generator.generate_execution_stats(
                scraper_results, processor_success, validation_success, total_time
            )
            
            stats_file = self.stats_generator.save_stats(stats)
            if stats_file:
                stats_step_logger.finish(True, f"Estadísticas guardadas: {stats_file}")
            else:
                stats_step_logger.finish(False, "Error guardando estadísticas")
            
            # Mostrar resumen
            self.stats_generator.print_execution_summary(stats)
            
            # Resumen final
            final_success = processor_success and validation_success
            self.logger.log_execution_summary(
                total_time, 
                sum([successful_scrapers > 0, processor_success, validation_success]),
                3,  # Total de pasos críticos
                final_success
            )
            
            if final_success:
                self.logger.log_success("PIPELINE ETL COMPLETADO EXITOSAMENTE")
                self.logger.info(f"[ARCHIVO] Archivo final: {self.config.unified_products_path}")
            else:
                self.logger.log_error("PIPELINE FALLÓ O INCOMPLETO")
            
            return final_success
            
        except KeyboardInterrupt:
            self.logger.warning("\n[ADVERTENCIA] Pipeline interrumpido por usuario")
            return False
        except Exception as e:
            self.logger.exception(f"[ERROR] Error inesperado en pipeline: {e}")
            return False
    
    def run_scrapers_only(self) -> bool:
        """
        Ejecuta solo los scrapers
        
        Returns:
            True si al menos un scraper fue exitoso
        """
        self.logger.info("[SCRAPERS] Ejecutando solo scrapers...")
        
        scraper_results = self.scraper_orchestrator.run_all_scrapers()
        scraper_validation = self.scraper_validator.validate_scraper_results(scraper_results)
        
        # Organizar archivos
        moved_files = self.file_manager.move_scraped_files_to_raw()
        self.logger.info(f"[ARCHIVOS] {moved_files} archivos organizados")
        
        success = scraper_validation["successful"] > 0
        if success:
            self.logger.log_success(f"Scrapers completados: {scraper_validation['successful']}/3 exitosos")
        else:
            self.logger.log_error("Todos los scrapers fallaron")
        
        return success
    
    def run_processor_only(self) -> bool:
        """
        Ejecuta solo el procesamiento (asume que ya existen archivos raw)
        
        Returns:
            True si el procesamiento fue exitoso
        """
        self.logger.info("[PROCESAMIENTO] Ejecutando solo procesamiento...")
        
        # Verificar archivos raw
        missing_files = self.file_manager.get_missing_raw_files()
        if len(missing_files) == len(self.config.expected_raw_files):
            self.logger.error("[ERROR] No hay archivos raw disponibles")
            return False
        
        if missing_files:
            self.logger.warning(f"[ADVERTENCIA] Archivos faltantes: {missing_files}")
        
        # Ejecutar procesamiento
        processor_success = self.processor_orchestrator.run_processor()
        
        if processor_success:
            # Validar resultado
            validation_success, validation_errors = self.validator.validate_unified_data()
            if validation_success:
                self.logger.log_success("Procesamiento y validación exitosos")
                return True
            else:
                self.logger.log_error(f"Procesamiento exitoso pero validación falló: {len(validation_errors)} errores")
                return False
        else:
            self.logger.log_error("Procesamiento falló")
            return False
    
    def validate_only(self) -> bool:
        """
        Ejecuta solo validación de datos existentes
        
        Returns:
            True si la validación fue exitosa
        """
        self.logger.info("[VALIDACIÓN] Ejecutando solo validación...")
        
        # Validar datos unificados
        if not self.config.unified_products_path.exists():
            self.logger.error("[ERROR] No existe archivo unified_products.json")
            return False
        
        validation_success, validation_errors = self.validator.validate_unified_data()
        
        if validation_success:
            self.logger.log_success("Validación exitosa")
            
            # Mostrar estadísticas
            import json
            with open(self.config.unified_products_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.logger.info(f"[STATS] Productos: {len(data)}")
            categorias = set(p.get('categoria', 'unknown') for p in data)
            tiendas = set(t.get('fuente', 'unknown') for p in data for t in p.get('tiendas', []))
            multi_store = sum(1 for p in data if len(p.get('tiendas', [])) > 1)
            
            self.logger.info(f"[STATS] Categorías: {len(categorias)}")
            self.logger.info(f"[STATS] Tiendas: {len(tiendas)}")
            self.logger.info(f"[STATS] Multi-tienda: {multi_store}")
            
        else:
            self.logger.log_error(f"Validación falló: {len(validation_errors)} errores")
            for error in validation_errors[:5]:
                self.logger.error(f"  - {error}")
        
        return validation_success
    
    def get_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual del sistema ETL
        
        Returns:
            Dict con estado del sistema
        """
        status = {
            "config": {
                "headless": self.config.headless,
                "max_pages": self.config.max_pages,
                "max_workers": self.config.max_workers
            },
            "directories": {
                "data_dir": str(self.config.data_dir),
                "raw_dir": str(self.config.raw_dir),
                "processed_dir": str(self.config.processed_dir),
                "logs_dir": str(self.config.logs_dir),
                "stats_dir": str(self.config.stats_dir)
            },
            "files": {
                "raw_files": self.file_manager.check_raw_files_exist(),
                "unified_file_exists": self.config.unified_products_path.exists()
            }
        }
        
        # Agregar estadísticas del archivo unificado si existe
        if status["files"]["unified_file_exists"]:
            unified_stats = self.file_manager.get_file_stats(self.config.unified_products_path)
            status["unified_stats"] = unified_stats
        
        return status
    
    @classmethod
    def create_from_args(cls, headless: bool = True, max_pages: Optional[int] = None, **kwargs):
        """
        Factory method para crear orquestador desde argumentos
        
        Args:
            headless: Modo headless para scrapers
            max_pages: Límite de páginas por categoría
            **kwargs: Argumentos adicionales para la configuración
            
        Returns:
            Instancia de ETLOrchestrator
        """
        config = ETLConfig(headless=headless, max_pages=max_pages, **kwargs)
        return cls(config)



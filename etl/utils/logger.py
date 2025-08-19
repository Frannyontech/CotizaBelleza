"""
Sistema de logging centralizado para ETL
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


class Logger:
    """Logger centralizado para el sistema ETL"""
    
    def __init__(self, config, name: str = "ETL"):
        """
        Inicializa el logger
        
        Args:
            config: Instancia de ETLConfig
            name: Nombre del logger
        """
        self.config = config
        self.name = name
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Configura el logger con handlers para consola y archivo"""
        logger = logging.getLogger(self.name)
        
        # Evitar duplicar handlers
        if logger.handlers:
            return logger
        
        # Configurar nivel
        log_level = getattr(logging, self.config.log_config["level"].upper())
        logger.setLevel(log_level)
        
        # Formatter
        formatter = logging.Formatter(self.config.log_config["format"])
        
        # Handler para consola
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Handler para archivo con rotación
        try:
            file_handler = RotatingFileHandler(
                filename=self.config.log_file_path,
                maxBytes=self.config.log_config["max_file_size"],
                backupCount=self.config.log_config["backup_count"],
                encoding='utf-8'
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            # Si no se puede crear el archivo de log, continuar solo con consola
            logger.warning(f"No se pudo crear archivo de log: {e}")
        
        return logger
    
    def debug(self, message: str):
        """Log debug"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """Log info"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error"""
        self.logger.error(message)
    
    def critical(self, message: str):
        """Log critical"""
        self.logger.critical(message)
    
    def exception(self, message: str):
        """Log exception con traceback"""
        self.logger.exception(message)
    
    def log_step(self, step_name: str, message: str = ""):
        """Log para pasos del pipeline"""
        separator = "=" * 50
        self.info(f"\n{separator}")
        self.info(f"PASO: {step_name}")
        self.info(separator)
        if message:
            self.info(message)
    
    def log_success(self, message: str):
        """Log para éxitos"""
        self.info(f"[OK] {message}")
    
    def log_error(self, message: str):
        """Log para errores"""
        self.error(f"[ERROR] {message}")
    
    def log_warning(self, message: str):
        """Log para advertencias"""
        self.warning(f"[ADVERTENCIA] {message}")
    
    def log_stats(self, stats_dict: dict, title: str = "ESTADÍSTICAS"):
        """Log para estadísticas"""
        self.info(f"\n[{title}]")
        for key, value in stats_dict.items():
            self.info(f"  {key}: {value}")
    
    def log_execution_summary(self, 
                            total_time: float,
                            successful_steps: int,
                            total_steps: int,
                            final_success: bool):
        """Log resumen final de ejecución"""
        separator = "=" * 60
        self.info(f"\n{separator}")
        self.info("RESUMEN FINAL DE EJECUCIÓN")
        self.info(separator)
        self.info(f"Tiempo total: {total_time:.1f}s")
        self.info(f"Pasos exitosos: {successful_steps}/{total_steps}")
        self.info(f"Estado final: {'ÉXITO' if final_success else 'ERROR'}")
        self.info(separator)
    
    @classmethod
    def get_logger(cls, config, name: str = "ETL") -> 'Logger':
        """Factory method para obtener una instancia del logger"""
        return cls(config, name)


class StepLogger:
    """Logger específico para pasos del pipeline"""
    
    def __init__(self, logger: Logger, step_name: str):
        """
        Inicializa logger de paso
        
        Args:
            logger: Instancia del logger principal
            step_name: Nombre del paso
        """
        self.logger = logger
        self.step_name = step_name
        self.start_time = None
    
    def start(self, message: str = ""):
        """Inicia el paso"""
        import time
        self.start_time = time.time()
        self.logger.log_step(self.step_name, message)
    
    def info(self, message: str):
        """Log info del paso"""
        self.logger.info(f"[{self.step_name}] {message}")
    
    def success(self, message: str):
        """Log éxito del paso"""
        self.logger.log_success(f"[{self.step_name}] {message}")
    
    def error(self, message: str):
        """Log error del paso"""
        self.logger.log_error(f"[{self.step_name}] {message}")
    
    def warning(self, message: str):
        """Log warning del paso"""
        self.logger.log_warning(f"[{self.step_name}] {message}")
    
    def finish(self, success: bool, message: str = ""):
        """Finaliza el paso"""
        if self.start_time:
            import time
            elapsed = time.time() - self.start_time
            status = "COMPLETADO" if success else "FALLÓ"
            final_message = f"{self.step_name} {status} en {elapsed:.1f}s"
            if message:
                final_message += f" - {message}"
            
            if success:
                self.logger.log_success(final_message)
            else:
                self.logger.log_error(final_message)
        else:
            if success:
                self.logger.log_success(f"{self.step_name} {message}")
            else:
                self.logger.log_error(f"{self.step_name} {message}")


def get_pipeline_logger(config, step_name: Optional[str] = None):
    """
    Factory function para obtener logger del pipeline
    
    Args:
        config: Configuración ETL
        step_name: Nombre del paso (opcional, para StepLogger)
        
    Returns:
        Logger o StepLogger según el caso
    """
    base_logger = Logger.get_logger(config)
    
    if step_name:
        return StepLogger(base_logger, step_name)
    
    return base_logger



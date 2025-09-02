"""
Configuración de logging para el sistema ETL de CotizaBelleza
Integra logging estándar de Python con Celery para tracking completo de operaciones
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any


class ETLFormatter(logging.Formatter):
    """
    Formato personalizado para logs del ETL
    Incluye timestamp, nivel, módulo y mensaje estructurado
    """
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def format(self, record):
        # Personalizar formato para diferentes tipos de mensajes
        if hasattr(record, 'etl_step') and record.etl_step:
            record.msg = f"[{record.etl_step}] {record.msg}"
        
        if hasattr(record, 'product_count') and record.product_count is not None:
            record.msg = f"{record.msg} | Productos: {record.product_count}"
        
        if hasattr(record, 'execution_time') and record.execution_time is not None:
            record.msg = f"{record.msg} | Tiempo: {record.execution_time:.2f}s"
        
        return super().format(record)


class ETLStepLogger:
    """
    Logger especializado para pasos del ETL
    Registra inicio, progreso y fin de cada etapa
    """
    
    def __init__(self, logger: logging.Logger, step_name: str):
        self.logger = logger
        self.step_name = step_name
        self.start_time = None
        self.product_count = 0
    
    def start(self, message: str):
        """Registra el inicio de un paso del ETL"""
        self.start_time = datetime.now()
        self.logger.info(f"INICIO: {message}", extra={
            'etl_step': self.step_name,
            'step_action': 'start'
        })
    
    def progress(self, message: str, product_count: int = None):
        """Registra progreso del paso actual"""
        if product_count is not None:
            self.product_count = product_count
        
        self.logger.info(f"PROGRESO: {message}", extra={
            'etl_step': self.step_name,
            'product_count': self.product_count,
            'step_action': 'progress'
        })
    
    def finish(self, success: bool, message: str, product_count: int = None):
        """Registra la finalización de un paso del ETL"""
        if product_count is not None:
            self.product_count = product_count
        
        execution_time = None
        if self.start_time:
            execution_time = (datetime.now() - self.start_time).total_seconds()
        
        level = logging.INFO if success else logging.ERROR
        status = "EXITOSO" if success else "FALLIDO"
        
        self.logger.log(level, f"FIN: {status} - {message}", extra={
            'etl_step': self.step_name,
            'product_count': self.product_count,
            'execution_time': execution_time,
            'step_action': 'finish',
            'step_success': success
        })
        
        return success
    
    def error(self, message: str, exception: Exception = None):
        """Registra errores durante la ejecución del paso"""
        error_msg = f"ERROR: {message}"
        if exception:
            error_msg += f" | Excepción: {str(exception)}"
        
        self.logger.error(error_msg, extra={
            'etl_step': self.step_name,
            'step_action': 'error',
            'exception_type': type(exception).__name__ if exception else None
        })


class ETLProductLogger:
    """
    Logger especializado para tracking de productos
    Registra conteos y estadísticas de productos procesados
    """
    
    def __init__(self, logger: logging.Logger, source: str):
        self.logger = logger
        self.source = source
        self.total_products = 0
        self.successful_products = 0
        self.failed_products = 0
    
    def log_extraction_start(self, expected_count: int = None):
        """Registra inicio de extracción de productos"""
        message = f"Iniciando extracción desde {self.source}"
        if expected_count:
            message += f" (esperados: {expected_count})"
        
        self.logger.info(message, extra={
            'etl_step': 'EXTRACCION',
            'source': self.source,
            'expected_count': expected_count
        })
    
    def log_product_extracted(self, product_id: str, product_name: str):
        """Registra un producto extraído exitosamente"""
        self.successful_products += 1
        self.total_products += 1
        
        self.logger.debug(f"Producto extraído: {product_name} (ID: {product_id})", extra={
            'etl_step': 'EXTRACCION',
            'source': self.source,
            'product_id': product_id,
            'product_name': product_name,
            'product_count': self.successful_products
        })
    
    def log_extraction_error(self, error: str, product_id: str = None):
        """Registra error durante extracción"""
        self.failed_products += 1
        self.total_products += 1
        
        error_msg = f"Error en extracción: {error}"
        if product_id:
            error_msg += f" (Producto ID: {product_id})"
        
        self.logger.error(error_msg, extra={
            'etl_step': 'EXTRACCION',
            'source': self.source,
            'product_id': product_id,
            'error': error
        })
    
    def log_extraction_complete(self):
        """Registra finalización de extracción con estadísticas"""
        success_rate = (self.successful_products / self.total_products * 100) if self.total_products > 0 else 0
        
        self.logger.info(f"Extracción completada desde {self.source}", extra={
            'etl_step': 'EXTRACCION',
            'source': self.source,
            'total_products': self.total_products,
            'successful_products': self.successful_products,
            'failed_products': self.failed_products,
            'success_rate': f"{success_rate:.1f}%"
        })
        
        return {
            'total': self.total_products,
            'successful': self.successful_products,
            'failed': self.failed_products,
            'success_rate': success_rate
        }


def setup_etl_logging(
    log_file: str = "etl.log",
    log_level: str = "INFO",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    console_output: bool = True
) -> logging.Logger:
    """
    Configura el sistema de logging para el ETL
    
    Args:
        log_file: Nombre del archivo de log (se crea en la raíz del proyecto)
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        max_bytes: Tamaño máximo del archivo de log antes de rotar
        backup_count: Número de archivos de backup a mantener
        console_output: Si mostrar logs en consola además del archivo
        
    Returns:
        Logger configurado para el ETL
    """
    # Obtener directorio raíz del proyecto
    project_root = Path(__file__).parent.parent
    
    # Crear directorio de logs si no existe
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Configurar archivo de log
    log_file_path = logs_dir / log_file
    
    # Crear logger principal del ETL
    etl_logger = logging.getLogger('etl')
    etl_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Evitar duplicación de handlers
    if etl_logger.handlers:
        return etl_logger
    
    # Handler para archivo con rotación
    file_handler = logging.handlers.RotatingFileHandler(
        log_file_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, log_level.upper()))
    
    # Aplicar formato personalizado
    formatter = ETLFormatter()
    file_handler.setFormatter(formatter)
    
    # Agregar handler de archivo
    etl_logger.addHandler(file_handler)
    
    # Handler para consola (opcional)
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(formatter)
        etl_logger.addHandler(console_handler)
    
    # Log inicial de configuración
    etl_logger.info("Sistema de logging ETL inicializado", extra={
        'etl_step': 'SISTEMA',
        'log_file': str(log_file_path),
        'log_level': log_level,
        'max_bytes': max_bytes,
        'backup_count': backup_count
    })
    
    return etl_logger


def get_etl_logger(name: str = None) -> logging.Logger:
    """
    Obtiene un logger configurado para el ETL
    
    Args:
        name: Nombre del logger (opcional)
        
    Returns:
        Logger configurado
    """
    if name:
        return logging.getLogger(f'etl.{name}')
    return logging.getLogger('etl')


def get_etl_step_logger(step_name: str, logger: logging.Logger = None) -> ETLStepLogger:
    """
    Obtiene un logger especializado para pasos del ETL
    
    Args:
        step_name: Nombre del paso del ETL
        logger: Logger base (opcional)
        
    Returns:
        ETLStepLogger configurado
    """
    if logger is None:
        logger = get_etl_logger()
    
    return ETLStepLogger(logger, step_name)


def get_etl_product_logger(source: str, logger: logging.Logger = None) -> ETLProductLogger:
    """
    Obtiene un logger especializado para tracking de productos
    
    Args:
        source: Fuente de datos (ej: 'maicao', 'preunic', 'dbs')
        logger: Logger base (opcional)
        
    Returns:
        ETLProductLogger configurado
    """
    if logger is None:
        logger = get_etl_logger()
    
    return ETLProductLogger(logger, source)


def log_celery_task_start(task_name: str, task_id: str, args: tuple = None, kwargs: dict = None):
    """
    Registra el inicio de una tarea de Celery
    
    Args:
        task_name: Nombre de la tarea
        task_id: ID único de la tarea
        args: Argumentos posicionales
        kwargs: Argumentos nombrados
    """
    logger = get_etl_logger('celery')
    
    task_info = f"Tarea: {task_name} | ID: {task_id}"
    if args:
        task_info += f" | Args: {args}"
    if kwargs:
        task_info += f" | Kwargs: {kwargs}"
    
    logger.info(f"Iniciando tarea Celery: {task_info}", extra={
        'etl_step': 'CELERY',
        'task_name': task_name,
        'task_id': task_id,
        'task_args': str(args) if args else None,
        'task_kwargs': str(kwargs) if kwargs else None
    })


def log_celery_task_success(task_name: str, task_id: str, result: Any, execution_time: float):
    """
    Registra la finalización exitosa de una tarea de Celery
    
    Args:
        task_name: Nombre de la tarea
        task_id: ID único de la tarea
        result: Resultado de la tarea
        execution_time: Tiempo de ejecución en segundos
    """
    logger = get_etl_logger('celery')
    
    logger.info(f"Tarea Celery completada exitosamente: {task_name} | ID: {task_id}", extra={
        'etl_step': 'CELERY',
        'task_name': task_name,
        'task_id': task_id,
        'task_result': str(result)[:200],  # Limitar longitud del resultado
        'execution_time': execution_time,
        'task_status': 'success'
    })


def log_celery_task_error(task_name: str, task_id: str, error: Exception, execution_time: float):
    """
    Registra el error en una tarea de Celery
    
    Args:
        task_name: Nombre de la tarea
        task_id: ID único de la tarea
        error: Excepción que causó el error
        execution_time: Tiempo de ejecución antes del error
    """
    logger = get_etl_logger('celery')
    
    logger.error(f"Error en tarea Celery: {task_name} | ID: {task_id} | Error: {str(error)}", extra={
        'etl_step': 'CELERY',
        'task_name': task_name,
        'task_id': task_id,
        'error_type': type(error).__name__,
        'error_message': str(error),
        'execution_time': execution_time,
        'task_status': 'error'
    })


# No hay configuración automática para evitar duplicación

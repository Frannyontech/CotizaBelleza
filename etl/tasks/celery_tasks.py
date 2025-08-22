"""
Tareas Celery para ETL v2.0 con programación automática
"""

from celery.utils.log import get_task_logger
import sys
import subprocess
import os
from pathlib import Path

# Importar configuración de Celery
from ..celery_app import app

logger = get_task_logger(__name__)


@app.task(bind=True, name='etl.tasks.celery_tasks.run_etl_task')
def run_etl_task(self, mode='prod'):
    """
    Tarea programada para ejecutar ETL automáticamente
    
    Args:
        mode: 'dev', 'test', 'prod' según el tipo de ejecución
        
    Returns:
        Dict con resultado del ETL
    """
    try:
        logger.info(f"🕐 [ETL Programado] Iniciando ejecución automática - Modo: {mode}")
        
        # Obtener directorio base del proyecto
        base_dir = Path(__file__).parent.parent.parent
        
        # Determinar argumentos según modo
        if mode == 'dev':
            args = ['full', '--headless', '--max-pages', '5']
        elif mode == 'prod':
            args = ['full', '--headless', '--max-pages', '5']  # 5 páginas para producción
        elif mode == 'test':
            args = ['full', '--headless', '--max-pages', '1']
        else:
            args = ['status']
        
        # Ejecutar etl_v2.py directamente para mayor control
        cmd = [sys.executable, '-m', 'etl.etl_v2'] + args
        
        logger.info(f"📝 [ETL Programado] Ejecutando comando: {' '.join(cmd)}")
        
        # Ejecutar el comando con timeout de 30 minutos
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=1800,
            cwd=str(base_dir)  # Ejecutar desde el directorio del proyecto
        )
        
        if result.returncode == 0:
            logger.info("✅ [ETL Programado] Completado exitosamente")
            
            # Verificar que se generó el archivo unified_products.json
            unified_file = base_dir / 'data' / 'processed' / 'unified_products.json'
            file_exists = unified_file.exists()
            file_size = unified_file.stat().st_size if file_exists else 0
            
            return {
                "status": "success", 
                "mode": mode,
                "scheduled": True,
                "output": result.stdout[-500:] if result.stdout else "ETL ejecutado correctamente",
                "unified_file_exists": file_exists,
                "unified_file_size_mb": round(file_size / (1024 * 1024), 2),
                "timestamp": str(__import__('datetime').datetime.now())
            }
        else:
            logger.error(f"❌ [ETL Programado] Error en ejecución: {result.stderr}")
            return {
                "status": "error", 
                "mode": mode, 
                "scheduled": True,
                "error": result.stderr[-500:] if result.stderr else "Error desconocido",
                "output": result.stdout[-500:] if result.stdout else "",
                "timestamp": str(__import__('datetime').datetime.now())
            }
            
    except subprocess.TimeoutExpired:
        logger.error("❌ [ETL Programado] Timeout después de 30 minutos")
        return {
            "status": "timeout", 
            "mode": mode, 
            "scheduled": True,
            "error": "Timeout después de 30 minutos",
            "timestamp": str(__import__('datetime').datetime.now())
        }
    except Exception as e:
        logger.error(f"❌ [ETL Programado] Error inesperado: {str(e)}")
        return {
            "status": "error", 
            "mode": mode, 
            "scheduled": True,
            "error": str(e),
            "timestamp": str(__import__('datetime').datetime.now())
        }


@app.task(bind=True, name='etl_simple.status')
def status_task(self):
    """
    Tarea simple para verificar estado del sistema
    
    Returns:
        Dict con información de estado
    """
    try:
        logger.info("🔍 [ETL Simple] Verificando estado")
        
        import os
        from pathlib import Path
        
        # Verificar archivos importantes
        base_dir = Path(__file__).parent.parent.parent
        unified_file = base_dir / 'data' / 'processed' / 'unified_products.json'
        
        status_info = {
            "status": "success",
            "timestamp": str(__import__('datetime').datetime.now()),
            "unified_data_exists": unified_file.exists(),
            "unified_data_size": unified_file.stat().st_size if unified_file.exists() else 0,
            "system": "operational"
        }
        
        if unified_file.exists():
            import json
            try:
                with open(unified_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "productos" in data:
                        status_info["products_count"] = len(data["productos"])
                    elif isinstance(data, list):
                        status_info["products_count"] = len(data)
                    else:
                        status_info["products_count"] = 0
            except:
                status_info["products_count"] = 0
        
        logger.info("✅ [ETL Simple] Estado verificado")
        return status_info
        
    except Exception as e:
        logger.error(f"❌ [ETL Simple] Error verificando estado: {str(e)}")
        return {"status": "error", "error": str(e)}


"""
Nueva tarea de Celery para probar IDs persistentes
"""

@app.task(bind=True, name='etl.tasks.celery_tasks.run_etl_with_persistent_ids')
def run_etl_with_persistent_ids(self, test_id='test_persistence'):
    """
    Tarea específica para probar IDs persistentes
    Ejecuta ETL completo y procesa con sistema de IDs persistentes
    """
    try:
        logger.info(f'[TEST IDs Persistentes] Iniciando prueba: {test_id}')
        
        # Obtener directorio base del proyecto
        base_dir = Path(__file__).parent.parent.parent
        
        # 1. Ejecutar ETL completo con 5 páginas
        args = ['full', '--headless', '--max-pages', '5']
        cmd = [sys.executable, '-m', 'etl.etl_v2'] + args
        
        logger.info(f'[TEST] Ejecutando ETL: {" ".join(cmd)}')
        
        # Ejecutar scraping
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=1800,
            cwd=str(base_dir)
        )
        
        if result.returncode != 0:
            logger.error(f'[TEST] Error en ETL: {result.stderr}')
            return {
                "status": "error",
                "test_id": test_id,
                "error": result.stderr,
                "timestamp": str(__import__('datetime').datetime.now())
            }
        
        logger.info('[TEST] ETL completado, procesando con IDs persistentes...')
        
        # 2. Procesar con IDs persistentes
        unified_file = base_dir / 'data' / 'processed' / 'unified_products.json'
        
        if not unified_file.exists():
            logger.error('[TEST] Archivo unified_products.json no encontrado')
            return {
                "status": "error",
                "test_id": test_id,
                "error": "Archivo unified_products.json no encontrado",
                "timestamp": str(__import__('datetime').datetime.now())
            }
        
        # Ejecutar procesamiento de IDs persistentes
        cmd_persistent = [
            sys.executable, 'manage_persistent_ids.py', 
            'procesar-json', str(unified_file)
        ]
        
        result_persistent = subprocess.run(
            cmd_persistent,
            capture_output=True,
            text=True,
            cwd=str(base_dir)
        )
        
        if result_persistent.returncode == 0:
            logger.info(f'[TEST] IDs persistentes procesados correctamente para {test_id}')
            
            # Obtener estadísticas
            cmd_stats = [sys.executable, 'manage_persistent_ids.py', 'estadisticas']
            stats_result = subprocess.run(
                cmd_stats,
                capture_output=True,
                text=True,
                cwd=str(base_dir)
            )
            
            return {
                "status": "success",
                "test_id": test_id,
                "etl_output": result.stdout[-500:],
                "persistent_output": result_persistent.stdout,
                "stats": stats_result.stdout if stats_result.returncode == 0 else "Error obteniendo stats",
                "timestamp": str(__import__('datetime').datetime.now())
            }
        else:
            logger.error(f'[TEST] Error procesando IDs persistentes: {result_persistent.stderr}')
            return {
                "status": "error",
                "test_id": test_id,
                "error": f"Error IDs persistentes: {result_persistent.stderr}",
                "timestamp": str(__import__('datetime').datetime.now())
            }
            
    except subprocess.TimeoutExpired:
        logger.error(f'[TEST] Timeout en prueba {test_id}')
        return {
            "status": "timeout",
            "test_id": test_id,
            "error": "Timeout después de 30 minutos",
            "timestamp": str(__import__('datetime').datetime.now())
        }
    except Exception as e:
        logger.error(f'[TEST] Error inesperado en {test_id}: {str(e)}')
        return {
            "status": "error",
            "test_id": test_id,
            "error": str(e),
            "timestamp": str(__import__('datetime').datetime.now())
        }

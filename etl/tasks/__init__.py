"""
Tareas Celery para ETL v2.0
"""

# Importar solo las tareas que existen
try:
    from .celery_tasks import run_etl_task, status_task
    __all__ = ['run_etl_task', 'status_task']
except ImportError:
    __all__ = []

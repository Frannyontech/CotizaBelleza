"""
Configuración de Celery para ETL v2.0 con programación automática
Utiliza variables de entorno para configuración flexible
"""

from celery import Celery
from celery.schedules import crontab
import os

# Configurar Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cotizabelleza.settings')

# Crear instancia de Celery
app = Celery('etl_cotizabelleza')

# Configuración de Celery
app.conf.update(
    # Broker y Backend con Redis
    broker_url=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    result_backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    
    # Serialización
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Configuración de tareas
    task_always_eager=False,
    task_eager_propagates=True,
    task_time_limit=1800,  # 30 minutos
    worker_prefetch_multiplier=1,
    
    # Configuración para Windows (desarrollo)
    # En producción Linux, cambiar por: worker_pool='prefork'
    worker_pool='solo',  # Threading sin multiprocessing
    worker_concurrency=1,
    
    # Zona horaria
    timezone='America/Santiago',
)

# Configuración del programador Celery Beat
app.conf.beat_schedule = {
    "etl-diario": {
        "task": "etl.tasks.celery_tasks.run_etl_task",
        "schedule": crontab(
            minute=int(os.getenv('ETL_SCHEDULE_MINUTE', '45')), 
            hour=int(os.getenv('ETL_SCHEDULE_HOUR', '20'))
        ),  # Programado vía variables de entorno
        "args": ("prod",),
    },
}

# Auto-descubrir tareas
app.autodiscover_tasks(['etl.tasks'])

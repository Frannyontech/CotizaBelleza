"""
ETL Package para CotizaBelleza
Estructura organizacional para Extract, Transform, Load
"""

__version__ = "2.0.0"
__author__ = "CotizaBelleza Team"

# Importaciones principales
from .config import ETLConfig
from .orchestrator import ETLOrchestrator
from .utils import FileManager, Logger, StatsGenerator

__all__ = [
    'ETLConfig',
    'ETLOrchestrator', 
    'FileManager',
    'Logger',
    'StatsGenerator'
]



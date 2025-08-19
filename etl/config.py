"""
Configuración centralizada para el sistema ETL
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class ETLConfig:
    """Configuración centralizada del sistema ETL"""
    
    # Paths principales
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    
    # Directorios de datos
    data_dir: Path = field(init=False)
    raw_dir: Path = field(init=False)
    processed_dir: Path = field(init=False)
    logs_dir: Path = field(init=False)
    stats_dir: Path = field(init=False)
    
    # Configuración de scrapers
    headless: bool = True
    max_pages: Optional[int] = None
    scraper_timeout: int = 7200  # 2 horas
    max_workers: int = 3
    
    # Archivos esperados
    expected_raw_files: List[str] = field(default_factory=lambda: [
        "dbs_maquillaje.json",
        "dbs_skincare.json", 
        "maicao_maquillaje.json",
        "maicao_skincare.json",
        "preunic_maquillaje.json",
        "preunic_skincare.json"
    ])
    
    # Configuración de tiendas
    stores_config: Dict[str, Dict] = field(default_factory=lambda: {
        "dbs": {
            "name": "DBS",
            "scraper_module": "scraper.scrapers.dbs_selenium_scraper",
            "scraper_function": "scrapear_todas_categorias",
            "categories": ["maquillaje", "skincare"],
            "uses_pages": True
        },
        "maicao": {
            "name": "Maicao", 
            "scraper_module": "scraper.scrapers.maicao_selenium_scraper",
            "scraper_function": "scrape_maicao_all_categories",
            "categories": ["maquillaje", "skincare"],
            "uses_pages": True
        },
        "preunic": {
            "name": "Preunic",
            "scraper_module": "scraper.scrapers.preunic_selenium_scraper", 
            "scraper_function": "scrapear_todas_categorias_preunic",
            "categories": ["maquillaje", "skincare"],
            "uses_pages": False,  # Usa scroll infinito
            "scroll_multiplier": 5
        }
    })
    
    # Configuración del processor
    processor_config: Dict = field(default_factory=lambda: {
        "module": "processor.normalize",
        "function": "main",
        "output_file": "unified_products.json"
    })
    
    # Configuración de logging
    log_config: Dict = field(default_factory=lambda: {
        "level": "INFO",
        "format": "%(asctime)s - %(levelname)s - [%(name)s] %(message)s",
        "file_name": "etl_pipeline.log",
        "max_file_size": 10 * 1024 * 1024,  # 10MB
        "backup_count": 5
    })
    
    def __post_init__(self):
        """Inicializa paths derivados después de la creación"""
        self.data_dir = self.project_root / "data"
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.logs_dir = self.project_root / "logs"
        self.stats_dir = self.project_root / "stats"
        
        # Crear directorios si no existen
        self._create_directories()
    
    def _create_directories(self):
        """Crea todos los directorios necesarios"""
        directories = [
            self.data_dir,
            self.raw_dir, 
            self.processed_dir,
            self.logs_dir,
            self.stats_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @property
    def unified_products_path(self) -> Path:
        """Path al archivo de productos unificados"""
        return self.processed_dir / self.processor_config["output_file"]
    
    @property
    def log_file_path(self) -> Path:
        """Path al archivo de logs"""
        return self.logs_dir / self.log_config["file_name"]
    
    def get_store_config(self, store_name: str) -> Dict:
        """Obtiene configuración de una tienda específica"""
        return self.stores_config.get(store_name.lower(), {})
    
    def get_raw_file_path(self, store: str, category: str) -> Path:
        """Genera path para archivo raw de tienda/categoría"""
        filename = f"{store.lower()}_{category.lower()}.json"
        return self.raw_dir / filename
    
    def get_stats_file_path(self, timestamp: str) -> Path:
        """Genera path para archivo de estadísticas"""
        filename = f"etl_stats_{timestamp}.json"
        return self.stats_dir / filename
    
    def validate_configuration(self) -> bool:
        """Valida que la configuración sea correcta"""
        try:
            # Verificar que existan todos los directorios críticos
            critical_dirs = [self.data_dir, self.raw_dir, self.processed_dir]
            for directory in critical_dirs:
                if not directory.exists():
                    return False
            
            # Verificar configuración de tiendas
            for store_name, config in self.stores_config.items():
                required_fields = ["name", "scraper_module", "scraper_function", "categories"]
                if not all(field in config for field in required_fields):
                    return False
            
            return True
            
        except Exception:
            return False
    
    @classmethod
    def from_env(cls, **kwargs):
        """Crea configuración desde variables de entorno"""
        config = cls(**kwargs)
        
        # Override con variables de entorno si existen
        if "ETL_HEADLESS" in os.environ:
            config.headless = os.environ["ETL_HEADLESS"].lower() == "true"
        
        if "ETL_MAX_PAGES" in os.environ:
            try:
                config.max_pages = int(os.environ["ETL_MAX_PAGES"])
            except ValueError:
                pass
        
        if "ETL_MAX_WORKERS" in os.environ:
            try:
                config.max_workers = int(os.environ["ETL_MAX_WORKERS"])
            except ValueError:
                pass
        
        return config



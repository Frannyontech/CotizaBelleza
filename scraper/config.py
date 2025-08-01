import environ
from pathlib import Path

# Configuración de requests
REQUEST_CONFIG = {
    'timeout': 10,
    'headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
}

# Configuración de delays
DELAY_CONFIG = {
    'min_delay': 1.0,
    'max_delay': 3.0,
    'random_delay': True,
}

# URLs de sitios de belleza
SITE_URLS = {
    'dbs': 'https://www.dbs.cl',
    'maicao': 'https://www.maicao.cl',
    'preunic': 'https://www.preunic.cl',
}

# Categorías de belleza
CATEGORIAS_BELLEZA = [
    'maquillaje',
    'skincare',
    'perfumes',
    'cabello',
]

# Configuración de exportación
EXPORT_CONFIG = {
    'json': True,
    'csv': False,
    'excel': False,
    'output_dir': 'output',
}

# Configuración de logging
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'scraper.log',
} 
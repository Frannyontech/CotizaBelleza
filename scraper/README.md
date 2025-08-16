# Módulo de Scraping - CotizaBelleza

Módulo base para scraping de sitios web de belleza usando requests + BeautifulSoup.

## 🚀 Características

- **Scraping inteligente** con requests y BeautifulSoup
- **Extracción de dataLayer** para obtener información detallada de productos
- **Manejo de delays** para ser respetuoso con los servidores
- **Logging completo** para debugging y monitoreo
- **Exportación múltiple** (JSON, CSV)
- **Configuración flexible** para diferentes sitios web

## 📁 Estructura del Proyecto

```
scraper/
├── __init__.py                 # Módulo principal
├── config.py                   # Configuraciones y constantes
├── utils.py                    # Utilidades y funciones auxiliares
├── unify_products.py          # Script de unificación de datos
├── README.md                  # Esta documentación
├── data/                      # Datos extraídos
│   ├── dbs_productos.json     # Productos DBS
│   ├── preunic_productos.json # Productos Preunic
│   └── maicao_productos.json  # Productos Maicao
└── scrapers/
    ├── __init__.py               # Submódulo scrapers
    ├── dbs_selenium_scraper.py   # Scraper DBS (Selenium)
    ├── preunic_selenium_scraper.py # Scraper Preunic (Selenium)
    └── maicao_selenium_scraper.py  # Scraper Maicao (Selenium)
```

## 🛠️ Instalación

### Dependencias

```bash
pip install requests beautifulsoup4 selenium
```

### Dependencias del sistema

```bash
# ChromeDriver para Selenium (debe estar en PATH)
# O usar webdriver-manager para instalación automática:
pip install webdriver-manager
```

### Dependencias opcionales

```bash
pip install pandas openpyxl  # Para exportación a Excel
```

## 📖 Uso Básico

### Scraper de Maicao (Selenium con Paginación)

```python
from scraper.scrapers.maicao_selenium_scraper import scrape_maicao_all_categories

# Scraping completo de todas las categorías
productos = scrape_maicao_all_categories(headless=True)

# Scraping limitado (solo primeras páginas para pruebas)
productos = scrape_maicao_all_categories(headless=True, max_pages_per_category=3)

# Ejecutar directamente
cd scraper/scrapers
python maicao_selenium_scraper.py
```

### Scraping de DBS

```python
from scraper.scrapers.dbs_selenium_scraper import scrapear_pagina_dbs

# Scraping de una página de categoría
url = "https://www.dbs.cl/maquillaje"
productos = scrapear_pagina_dbs(url)

# Mostrar resultados
for producto in productos:
    print(f"{producto.nombre} - ${producto.precio}")
```

### Scraping de múltiples páginas

```python
from scraper.scrapers.dbs_scraper import scrapear_catalogo_dbs

# URLs de categorías
urls = [
    "https://www.dbs.cl/maquillaje",
    "https://www.dbs.cl/skincare",
]

# Scraping con delay entre requests
productos = scrapear_catalogo_dbs(urls, delay=2.0)

print(f"Total de productos: {len(productos)}")
```

### Uso con logging

```python
from scraper.utils import setup_logging, save_to_json, generate_filename

# Configurar logging
logger = setup_logging('mi_scraper')

# Scraping
productos = scrapear_pagina_dbs(url)

# Guardar resultados
if productos:
    filename = generate_filename("productos_dbs", "json")
    save_to_json([p.to_dict() for p in productos], filename)
    logger.info(f"Datos guardados en {filename}")
```

## 🔧 Configuración

### Configuración de delays

```python
from scraper.config import DELAY_CONFIG

# Modificar delays
DELAY_CONFIG['min_delay'] = 1.5
DELAY_CONFIG['max_delay'] = 3.0
DELAY_CONFIG['random_delay'] = True
```

### Configuración de headers

```python
from scraper.config import REQUEST_CONFIG

# Agregar headers personalizados
REQUEST_CONFIG['headers']['User-Agent'] = 'Mi Bot/1.0'
```

## 📊 Clase DBSProduct

Cada producto extraído se representa como un objeto `DBSProduct`:

```python
producto = DBSProduct(
    nombre="Base de Maquillaje",
    marca="L'Oréal",
    precio=15990.0,
    categoria="maquillaje",
    stock=True,
    estrellas=4.5,
    url="https://www.dbs.cl/producto/123",
    imagen="https://www.dbs.cl/imagen.jpg"
)

# Convertir a diccionario
datos = producto.to_dict()
```

### Atributos disponibles

- `nombre`: Nombre del producto
- `marca`: Marca del producto
- `precio`: Precio numérico
- `categoria`: Categoría del producto
- `stock`: Disponibilidad (True/False)
- `estrellas`: Rating del producto (0.0 - 5.0)
- `url`: URL del producto
- `imagen`: URL de la imagen

## 🔍 Extracción de dataLayer

El scraper extrae información del atributo `onclick` que contiene dataLayer:

```javascript
// Ejemplo de dataLayer en onclick
onclick="dataLayer.push({
    'product_name': 'Base de Maquillaje',
    'product_brand': 'L\'Oréal',
    'product_price': '15990',
    'product_category': 'maquillaje',
    'product_availability': 'in stock',
    'product_rating': '4.5'
})"
```

## 📈 Funciones de Utilidad

### Limpieza de texto

```python
from scraper.utils import clean_text

texto_limpio = clean_text("  Texto   con   espacios  ")
# Resultado: "Texto con espacios"
```

### Extracción de precios

```python
from scraper.utils import extract_price

precio = extract_price("$15.990")
# Resultado: 15990.0
```

### Exportación de datos

```python
from scraper.utils import save_to_json, save_to_csv

# Guardar en JSON
save_to_json(productos_dict, "productos.json")

# Guardar en CSV
save_to_csv(productos_dict, "productos.csv")
```

## 🚨 Consideraciones Éticas

### Delays y Rate Limiting

- **Delay mínimo**: 1 segundo entre requests
- **Delay recomendado**: 2-3 segundos
- **Delay aleatorio**: Evita patrones detectables

### Headers apropiados

- **User-Agent**: Identifica el bot
- **Accept**: Headers estándar del navegador
- **Referer**: Simula navegación real

### Respeto a robots.txt

```python
# Verificar robots.txt antes de scraping
import requests
from urllib.robotparser import RobotFileParser

rp = RobotFileParser()
rp.set_url("https://www.dbs.cl/robots.txt")
rp.read()

if rp.can_fetch("*", "/maquillaje"):
    # Proceder con scraping
    productos = scrapear_pagina_dbs(url)
```

## 🐛 Debugging

### Logging detallado

```python
from scraper.utils import setup_logging

logger = setup_logging('debug_scraper')
logger.setLevel('DEBUG')

# El scraper mostrará información detallada
productos = scrapear_pagina_dbs(url)
```

### Verificar respuesta HTTP

```python
from scraper.scrapers.dbs_scraper import DBSScraper

scraper = DBSScraper()
soup = scraper._get_page(url)

if soup:
    print("Página cargada correctamente")
    print(f"Título: {soup.title.string}")
else:
    print("Error al cargar la página")
```

## 📝 Ejemplos Completos

Ver `example_usage.py` para ejemplos completos de:

1. Scraping de una página
2. Scraping de múltiples páginas
3. Scraping con logging
4. Análisis de precios
5. Exportación de datos

## 🔄 Extensibilidad

### Agregar nuevo scraper

```python
# scraper/scrapers/nuevo_sitio_scraper.py
from .dbs_scraper import DBSScraper

class NuevoSitioScraper(DBSScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.nuevo-sitio.cl"
    
    def scrapear_pagina_nuevo_sitio(self, url):
        # Implementar lógica específica
        pass
```

### Personalizar selectores CSS

```python
# En config.py
CSS_SELECTORS['nuevo_sitio'] = {
    'product_container': '.producto',
    'product_name': '.nombre-producto',
    'product_price': '.precio',
    # ...
}
```

## 🏪 Tiendas Soportadas

| Tienda | Scraper | Tecnología | Categorías | Estado |
|--------|---------|------------|------------|--------|
| **DBS** | `dbs_selenium_scraper.py` | Selenium + BeautifulSoup | `maquillaje`, `skincare` | ✅ Funcional |
| **Preunic** | `preunic_selenium_scraper.py` | Selenium + BeautifulSoup | `maquillaje`, `skincare` | ✅ Funcional |
| **Maicao** | `maicao_selenium_scraper.py` | Selenium + Paginación | `maquillaje`, `skincare` | ✅ Funcional |

### Características por Scraper

#### Maicao Scraper
- ✅ **Paginación avanzada** (detección automática de páginas)
- ✅ **Extracción de precios desde detalle** si no se encuentra en lista
- ✅ **Scroll infinito reemplazado** por navegación correcta
- ✅ **Estructura JSON estandarizada** con otras tiendas

#### DBS Scraper
- ✅ **Navegación por páginas** numeradas
- ✅ **Detección automática de total de páginas**
- ✅ **Extracción de imágenes lazy-loading**

#### Preunic Scraper
- ✅ **Scroll infinito** hasta carga completa
- ✅ **Manejo de productos sin precio**
- ✅ **Extracción de marcas inteligente**

## 📄 Licencia

Este módulo es parte del proyecto CotizaBelleza y está bajo la misma licencia.

## 🤝 Contribuciones

Para contribuir al módulo de scraping:

1. Fork el repositorio
2. Crea una rama para tu feature
3. Implementa el scraper para un nuevo sitio
4. Agrega tests y documentación
5. Envía un pull request

## 📞 Soporte

Para reportar bugs o solicitar features:

- Abre un issue en GitHub
- Incluye logs y ejemplos de reproducción
- Especifica la versión del módulo 
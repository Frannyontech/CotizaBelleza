import time
import re
from typing import List, Dict, Optional
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json


class DBSProduct:
    
    def __init__(self, nombre: str, marca: str, precio: float, 
                 categoria: str, stock: bool, estrellas: float = 0.0,
                 url: str = "", imagen: str = ""):
        self.nombre = nombre
        self.marca = marca
        self.precio = precio
        self.categoria = categoria
        self.stock = stock
        self.estrellas = estrellas
        self.url = url
        self.imagen = imagen
    
    def to_dict(self) -> Dict:
        return {
            'nombre': self.nombre,
            'marca': self.marca,
            'precio': self.precio,
            'categoria': self.categoria,
            'stock': self.stock,
            'estrellas': self.estrellas,
            'url': self.url,
            'imagen': self.imagen
        }
    
    def __str__(self) -> str:
        return f"{self.marca} - {self.nombre} - ${self.precio}"

class DBSSeleniumScraper:
    
    def __init__(self, headless: bool = True):
        self.base_url = "https://www.dbs.cl"
        self.driver = None
        self.setup_driver(headless)
    
    def setup_driver(self, headless: bool):
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument("--headless")
        
        # Configuraciones anti-detección
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print("Driver de Chrome configurado correctamente")
        except Exception as e:
            print(f"Error al configurar el driver: {e}")
            self.driver = None
    
    def _get_page_with_selenium(self, url: str) -> Optional[BeautifulSoup]:
        if not self.driver:
            return None
        
        try:
            print(f"Cargando página: {url}")
            self.driver.get(url)
            time.sleep(3)
            
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "product"))
                )
                print("Elementos de productos cargados")
            except:
                print("No se encontraron elementos con clase 'product', continuando...")
            
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            print(f"Página cargada exitosamente")
            return soup
            
        except Exception as e:
            print(f"Error al cargar la página: {e}")
            return None
    
    def _detectar_total_paginas(self, categoria: str) -> int:
        try:
            url = f"{self.base_url}/{categoria}"
            soup = self._get_page_with_selenium(url)
            
            if not soup:
                return 1
            
            # Buscar elementos de paginación
            pagination_elements = soup.find_all('a', href=re.compile(r'page=\d+'))
            
            if pagination_elements:
                page_numbers = []
                for elem in pagination_elements:
                    href = elem.get('href', '')
                    match = re.search(r'page=(\d+)', href)
                    if match:
                        page_numbers.append(int(match.group(1)))
                
                if page_numbers:
                    max_page = max(page_numbers)
                    print(f"Total de páginas detectadas para {categoria}: {max_page}")
                    return max_page
            
            # Verificar si hay muchos productos
            product_elements = soup.find_all(class_='product')
            if len(product_elements) >= 120:
                print(f"Muchos productos encontrados en {categoria}, asumiendo múltiples páginas")
                return 5
            
            print(f"Solo 1 página detectada para {categoria}")
            return 1
            
        except Exception as e:
            print(f"Error detectando páginas para {categoria}: {e}")
            return 1
    
    def _extract_product_info_from_element(self, product_element) -> Optional[DBSProduct]:
        try:
            text = product_element.get_text(strip=True)
            if not text:
                return None
            
            # Extraer precio
            precio = self._extract_precio(product_element, text)
            
            # Extraer marca y nombre
            marca, nombre = self._extract_marca_nombre(text, product_element)
            
            # Limpiar nombre
            nombre = self._limpiar_nombre(nombre)
            
            # Extraer URL e imagen
            url = self._extract_url(product_element)
            imagen = self._extract_imagen(product_element)
            
            # Determinar stock y estrellas
            stock = self._determinar_stock(product_element)
            estrellas = self._extract_estrellas(product_element)
            
            # Determinar categoría
            categoria = self._determinar_categoria(url)
            
            # Crear producto si tiene nombre válido
            if nombre and len(nombre.strip()) > 2:
                return DBSProduct(
                    nombre=nombre.strip(),
                    marca=marca.strip(),
                    precio=precio,
                    categoria=categoria,
                    stock=stock,
                    estrellas=estrellas,
                    url=url,
                    imagen=imagen
                )
            
            return None
            
        except Exception as e:
            print(f"Error extrayendo producto: {e}")
            return None
    
    def _extract_precio(self, product_element, text: str) -> float:
        precio = 0.0
        price_pattern = re.compile(r'\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)')
        
        # Buscar precio en el texto principal
        price_match = price_pattern.search(text)
        if price_match:
            price_str = price_match.group(1).replace('.', '').replace(',', '.')
            try:
                precio = float(price_str)
                return precio
            except ValueError:
                pass
        
        # Buscar en elementos pricebox
        price_elements = product_element.find_all(class_='pricebox')
        for price_elem in price_elements:
            price_text = price_elem.get_text(strip=True)
            price_match = price_pattern.search(price_text)
            if price_match:
                price_str = price_match.group(1).replace('.', '').replace(',', '.')
                try:
                    return float(price_str)
                except ValueError:
                    continue
        
        # Buscar en otros elementos de precio
        price_elements = product_element.find_all(class_=re.compile(r'price|precio', re.IGNORECASE))
        for price_elem in price_elements:
            price_text = price_elem.get_text(strip=True)
            price_match = price_pattern.search(price_text)
            if price_match:
                price_str = price_match.group(1).replace('.', '').replace(',', '.')
                try:
                    return float(price_str)
                except ValueError:
                    continue
        
        return precio
    
    def _extract_marca_nombre(self, text: str, product_element) -> tuple:
        marcas_conocidas = [
            '3INA', 'ABSOLUTE NEW YORK', 'ANASTASIA BEVERLY HILLS', 'ARDELL', 'BAG NY', 'BEAUTY CREATIONS', 
            'BEAUTY TOOLS', 'BIOTHERM', 'BYPHASSE', 'BYS', 'CARMEX', 'CATRICE', 'CHINA GLAZE', 'CLINIQUE', 
            'DANESSA MYRICKS', 'DBS BASICS', 'DBS COLLECTION', 'ECOTOOLS', 'ESSENCE', 'ESTÉE LAUDER', 'FLORMAR', 
            'FRUDIA, GELIFY', 'GLAM FACTOR', 'HELLO SUNDAY', 'ICONIC LONDON', 'ILASH', 'J CAT', 'KIKO MILANO', 'KISS', 
            'LANCÔME', 'LIP SMACKER', 'L\'ORÉAL PARIS', 'MAKEUP REVOLUTION', 'MARIO BADESCU', 'MASGLO', 'MAYBELLINE', 
            'MISSHA', 'MIZON', 'MOIRA', 'NUDESTIX', 'NYX', 'PMU', 'OPI', 'PHYSICIANS FORMULA', 'PIXI', 'REAL TECHNIQUES', 
            'REVLON', 'REVOX B77', 'RISQUE', 'ROM&ND', 'SALLY HANSEN', 'SIGMA', 'TESSA', 'THE BALM', 'TOCOBO', 'TONY MOLY', 
            'TWEEZERMAN', 'UNLEASHIA', 'URBAN DECAY', 'WET N WILD', 'MOROCCANOIL', 'REDKEN', 'KIEHL\'S', 'COSRX', 'BOVEY', 
            'REVUELE', 'REVOX', 'APIVITA', 'MARC ANTHONY', 'KÉRASTASE', 'CLOE PROFESSIONAL', 'INSIGHT', 'OUIDAD', 'TANGLE TEEZER'
        ]
        
        # Buscar marca conocida
        for marca_conocida in marcas_conocidas:
            if marca_conocida.lower() in text.lower():
                marca_pos = text.lower().find(marca_conocida.lower())
                if marca_pos != -1:
                    nombre_start = marca_pos + len(marca_conocida)
                    nombre = text[nombre_start:].strip()
                    return marca_conocida, nombre
        
        # Buscar en elementos HTML
        brand_elements = product_element.find_all(class_=re.compile(r'brand|marca', re.IGNORECASE))
        name_elements = product_element.find_all(class_=re.compile(r'name|nombre|title', re.IGNORECASE))
        
        marca = brand_elements[0].get_text(strip=True) if brand_elements else ""
        nombre = name_elements[0].get_text(strip=True) if name_elements else text
        
        # Patrón "MARCA - NOMBRE"
        if not marca:
            marca_nombre_pattern = re.compile(r'^([A-Z\s]+)\s*-\s*(.+)', re.IGNORECASE)
            match = marca_nombre_pattern.match(text)
            if match:
                marca = match.group(1).strip()
                nombre = match.group(2).strip()
            else:
                marca = ""
                nombre = text
        
        return marca, nombre
    
    def _limpiar_nombre(self, nombre: str) -> str:
        if not nombre:
            return ""
        
        patrones_limpieza = [
            r'Valoración:\d+%',
            r'Desde\$.*?Añadir al carrito',
            r'New.*?%',
            r'Sale.*?%',
            r'Ganador⭐',
            r'\$.*?Añadir al carrito',
            r'^\s*[-]\s*'
        ]
        
        for patron in patrones_limpieza:
            nombre = re.sub(patron, '', nombre).strip()
        
        return nombre
    
    def _extract_url(self, product_element) -> str:
        if product_element.name == 'a':
            return urljoin(self.base_url, product_element.get('href', ''))
        
        link = product_element.find('a')
        if link:
            return urljoin(self.base_url, link.get('href', ''))
        
        return ""
    
    def _extract_imagen(self, product_element) -> str:
        img_element = product_element.find('img')
        if img_element:
            img_src = img_element.get('src', '') or img_element.get('data-src', '') or img_element.get('data-lazy-src', '')
            if img_src:
                return urljoin(self.base_url, img_src)
        return ""
    
    def _determinar_stock(self, product_element) -> bool:
        stock_indicators = product_element.find_all(text=re.compile(r'no está disponible|agotado|out of stock', re.IGNORECASE))
        return not bool(stock_indicators)
    
    def _extract_estrellas(self, product_element) -> float:
        star_elements = product_element.find_all(class_=re.compile(r'star|rating|valoración', re.IGNORECASE))
        if star_elements:
            star_text = star_elements[0].get_text(strip=True)
            star_match = re.search(r'(\d+(?:\.\d+)?)', star_text)
            if star_match:
                try:
                    return float(star_match.group(1))
                except ValueError:
                    pass
        return 0.0
    
    def _determinar_categoria(self, url: str) -> str:
        if "maquillaje" in url.lower():
            return "maquillaje"
        elif "skincare" in url.lower():
            return "skincare"
        return "general"
    
    def scrapear_pagina_dbs(self, url: str) -> List[DBSProduct]:
        print(f"Scrapeando página: {url}")
        
        soup = self._get_page_with_selenium(url)
        if not soup:
            return []
        
        productos = []
        
        # Buscar elementos de productos
        product_elements = soup.find_all(class_='product')
        product_links = soup.find_all('a', class_='product')
        data_product_elements = soup.find_all(attrs={'data-product': True})
        
        print(f"Elementos con clase 'product': {len(product_elements)}")
        print(f"Enlaces con clase 'product': {len(product_links)}")
        print(f"Elementos con data-product: {len(data_product_elements)}")
        
        # Combinar todos los elementos únicos
        all_elements = list(set(product_elements + product_links + data_product_elements))
        print(f"Total de elementos de productos encontrados: {len(all_elements)}")
        
        for element in all_elements:
            producto = self._extract_product_info_from_element(element)
            if producto:
                productos.append(producto)
                print(f"Producto encontrado: {producto}")
        
        return productos
    
    def scrapear_catalogo_dbs(self, urls: List[str], delay: float = 3.0) -> List[DBSProduct]:
        todos_productos = []
        
        for i, url in enumerate(urls, 1):
            print(f"\nProcesando página {i}/{len(urls)}")
            productos_pagina = self.scrapear_pagina_dbs(url)
            todos_productos.extend(productos_pagina)
            
            if i < len(urls):
                print(f"Esperando {delay} segundos...")
                time.sleep(delay)
        
        print(f"\nTotal de productos extraídos: {len(todos_productos)}")
        return todos_productos
    
    def close(self):
        if self.driver:
            self.driver.quit()
            print("Driver cerrado")


def scrapear_pagina_dbs(categoria: str, pagina: int = 1, headless: bool = True) -> List[DBSProduct]:
    scraper = DBSSeleniumScraper(headless=headless)
    try:
        url = f"https://www.dbs.cl/{categoria}" if pagina == 1 else f"https://www.dbs.cl/{categoria}?page={pagina}"
        return scraper.scrapear_pagina_dbs(url)
    finally:
        scraper.close()


def scrapear_catalogo_dbs(categoria: str, max_paginas: int = None, delay: float = 3.0, headless: bool = True) -> List[DBSProduct]:
    scraper = DBSSeleniumScraper(headless=headless)
    try:
        if max_paginas is None:
            print(f"Detectando total de páginas para {categoria}...")
            max_paginas = scraper._detectar_total_paginas(categoria)
        else:
            print(f"Usando {max_paginas} páginas para {categoria}")
        
        urls = [f"https://www.dbs.cl/{categoria}" if pagina == 1 else f"https://www.dbs.cl/{categoria}?page={pagina}" 
                for pagina in range(1, max_paginas + 1)]
        
        print(f"Iniciando scraping de {len(urls)} páginas de {categoria}")
        return scraper.scrapear_catalogo_dbs(urls, delay)
    finally:
        scraper.close()


def scrapear_todas_categorias(headless: bool = True, guardar_json: bool = True) -> dict:
    print("SCRAPING COMPLETO DE DBS")
    print("=" * 50)
    
    categorias = ['maquillaje', 'skincare']
    resultados = {}
    
    for categoria in categorias:
        print(f"\nSCRAPING COMPLETO DE {categoria.upper()}")
        print("-" * 40)
        productos = scrapear_catalogo_dbs(categoria, max_paginas=None, headless=headless)
        resultados[categoria] = productos
        print(f"{categoria.capitalize()}: {len(productos)} productos")
    
    # Resumen final
    total_productos = sum(len(productos) for productos in resultados.values())
    print(f"\nRESUMEN FINAL:")
    print(f"Total de productos extraídos: {total_productos}")
    for categoria, productos in resultados.items():
        print(f"{categoria.capitalize()}: {len(productos)} productos")
    
    if guardar_json:
        guardar_resultados_json(resultados)
    
    return resultados


def guardar_resultados_json(resultados: dict, nombre_archivo: str = "dbs_productos.json"):
    try:
        total_productos = sum(len(productos) for productos in resultados.values())
        
        datos_json = {
            'fecha_extraccion': time.strftime("%Y-%m-%d %H:%M:%S"),
            'total_productos': total_productos,
        }
        
        # Agregar datos de cada categoría
        for categoria, productos in resultados.items():
            datos_json[categoria] = {
                'cantidad': len(productos),
                'productos': [producto.to_dict() for producto in productos]
            }
        
        # Guardar archivo JSON
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            json.dump(datos_json, f, ensure_ascii=False, indent=2)
        
        print(f"\nARCHIVO JSON GUARDADO:")
        print(f"Ubicación: {nombre_archivo}")
        print(f"Total de productos: {datos_json['total_productos']}")
        for categoria, datos in datos_json.items():
            if categoria != 'fecha_extraccion' and categoria != 'total_productos':
                print(f"{categoria.capitalize()}: {datos['cantidad']} productos")
        
    except Exception as e:
        print(f"Error al guardar JSON: {e}")


if __name__ == "__main__":
    print("SCRAPING COMPLETO DE DBS")
    print("=" * 50)
    
    resultados = scrapear_todas_categorias(headless=True)
    
    print(f"\nEJEMPLOS DE PRODUCTOS:")
    for categoria, productos in resultados.items():
        print(f"\n{categoria.capitalize()} (primeros 3):")
        for i, producto in enumerate(productos[:3], 1):
            print(f"{i}. {producto}")
    
    print(f"\nScraping completo finalizado!") 
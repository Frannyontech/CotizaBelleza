import time
import re
import os
import json
from typing import List, Optional, Dict
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

class DBSProduct:
    def __init__(self, nombre: str, marca: str, precio: float, 
                 categoria: str, stock: str, url: str = "", imagen: str = ""):
        self.nombre = nombre
        self.marca = marca
        self.precio = precio
        self.categoria = categoria
        self.stock = stock
        self.url = url
        self.imagen = imagen

    def to_dict(self) -> Dict:
        return {
            'nombre': self.nombre,
            'marca': self.marca,
            'precio': self.precio,
            'categoria': self.categoria,
            'stock': self.stock,
            'url': self.url,
            'imagen': self.imagen
        }

    def __str__(self) -> str:
        return f"{self.nombre} - {self.marca} - ${self.precio}"

class DBSSeleniumScraper:
    def __init__(self, headless: bool = True):
        self.driver = None
        self.setup_driver(headless)
        
        # Lista de marcas conocidas para priorizar
        self.marcas_conocidas = [
            'KIKO MILANO', 'ESSENCE', 'CATRICE', 'NYX', 'MAYBELLINE', 
            'L\'ORÉAL PARIS', 'BIOTHERM', 'CLINIQUE', 'KIEHL\'S',
            'REVUELE', 'REVOX B77', 'SKIN1004', 'COSRX', 'BOVEY',
            'APIVITA', 'BYPHASSE', 'TOCOBO', 'DBS BASICS'
        ]

    def setup_driver(self, headless: bool):
        options = Options()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=options)

    def _get_page_with_selenium(self, url: str) -> Optional[BeautifulSoup]:
        try:
            self.driver.get(url)
            
            # Esperar a que los productos se carguen
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.product-item'))
            )
            
            # Esperar a que las imágenes se carguen completamente
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.product-image-photo'))
            )
            
            # Scroll para cargar imágenes lazy
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            # Scroll adicional para asegurar que todas las imágenes se carguen
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(2)
            
            return BeautifulSoup(self.driver.page_source, 'html.parser')
        except Exception as e:
            print(f"Error cargando página: {e}")
            return None

    def obtener_total_paginas(self, categoria: str) -> int:
        url = f"https://dbs.cl/{categoria}"
        
        try:
            soup = self._get_page_with_selenium(url)
            
            if not soup:
                return 1
            
            # Obtener todo el texto de la página
            all_text = soup.get_text()
            
            # Usar el patrón que sabemos que funciona
            pattern = r'Artículos\s*\d+-\d+\s*de\s*([\d,]+)'
            match = re.search(pattern, all_text)
            
            if match:
                total_productos = int(match.group(1).replace(',', ''))
                productos_por_pagina = 24
                total_paginas = (total_productos + productos_por_pagina - 1) // productos_por_pagina
                print(f"Detectados {total_productos} productos en {total_paginas} páginas para {categoria}")
                return max(1, total_paginas)
            
            print(f"No se pudo detectar el total de páginas para {categoria}, usando 1 página")
            return 1
            
        except Exception as e:
            print(f"Error detectando páginas para {categoria}: {e}")
            return 1

    def _extract_product_info_from_element(self, product_element, categoria_pagina: str = "general") -> Optional[DBSProduct]:
        try:
            nombre = self._extract_nombre(product_element)
            marca = self._extract_marca(product_element)
            precio = self._extract_precio(product_element)
            url = self._extract_url(product_element)
            imagen = self._extract_imagen(product_element)
            stock = self._determinar_stock(product_element)
            categoria = categoria_pagina  # Usar la categoría de la página en lugar de determinarla por URL
            
            if not nombre or len(nombre.strip()) < 3:
                return None
            
            # Validar que no sea un elemento de filtro o navegación
            if any(keyword in nombre.lower() for keyword in ['filtro', 'filter', 'ordenar']):
                return None
            
            if precio <= 0:
                return None
            
            return DBSProduct(
                nombre=nombre.strip(),
                marca=marca.strip(),
                precio=precio,
                categoria=categoria,
                stock=stock,
                url=url,
                imagen=imagen
            )
            
        except Exception as e:
            print(f"Error extrayendo producto: {e}")
            return None

    def _extract_nombre(self, product_element) -> str:
        name_selectors = [
            '.product-name',
            '.product-item-name',
            'h2', 'h3', 'h4',
            '.product-title',
            '.item-name',
            '.product-name a',
            '.product-item-name a',
            '.product-item-title',
            '.product-item-title a',
            'a[title]',
            '.product-item a'
        ]
        
        for selector in name_selectors:
            elements = product_element.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text and len(text) > 3:
                    # Validar que el texto sea alfabético, no monetario
                    if self._es_texto_alfabetico(text):
                        return self._limpiar_nombre(text)
        
        # Si no encuentra con selectores específicos, buscar en enlaces
        links = product_element.select('a[href]')
        for link in links:
            text = link.get_text(strip=True)
            href = link.get('href', '')
            if text and len(text) > 3 and 'dbs.cl' in href:
                if self._es_texto_alfabetico(text):
                    return self._limpiar_nombre(text)
        
        # Buscar en el atributo title de enlaces
        for link in links:
            title = link.get('title', '')
            if title and len(title) > 3:
                if self._es_texto_alfabetico(title):
                    return self._limpiar_nombre(title)
        
        return ""

    def _es_texto_alfabetico(self, text: str) -> bool:
        """Valida que el texto sea alfabético, no monetario o numérico"""
        # Eliminar espacios y caracteres especiales
        clean_text = re.sub(r'[^\w\s]', '', text).strip()
        
        # Verificar que no contenga rangos de precio
        if re.search(r'\$\s*\d+', clean_text):
            return False
        
        # Verificar que no sea solo números
        if clean_text.isdigit():
            return False
        
        # Verificar que no contenga patrones de precio
        if re.search(r'\d+\s*-\s*\d+', clean_text):
            return False
        
        # Verificar que tenga al menos algunas letras
        if not re.search(r'[a-zA-Z]', clean_text):
            return False
        
        # Verificar que no sea un rango de precio
        if re.search(r'\$\s*\d+\s*-\s*\$\s*\d+', text):
            return False
        
        return True

    def _extract_marca(self, product_element) -> str:
        # Primero buscar en marcas conocidas
        for marca in self.marcas_conocidas:
            # Buscar en el texto del elemento
            text = product_element.get_text().upper()
            if marca.upper() in text:
                return marca
        
        # Si no encuentra marca conocida, buscar en elementos específicos
        brand_selectors = [
            '.product-brand',
            '.brand',
            '.product-item-brand',
            '.item-brand'
        ]
        
        for selector in brand_selectors:
            elements = product_element.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text and len(text) > 1:
                    return text
        
        # Si no encuentra marca, retornar "DBS" por defecto
        return "DBS"

    def _extract_precio(self, product_element) -> float:
        price_selectors = [
            '.price',
            '.product-price',
            '.price-box .price',
            '.product-item-price',
            '.item-price',
            '[data-price]'
        ]
        
        for selector in price_selectors:
            elements = product_element.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text:
                    # Extraer solo el primer precio (evitar rangos)
                    precio = self._extraer_precio_unico(text)
                    if precio > 0:
                        return precio
        
        return 0.0

    def _extraer_precio_unico(self, text: str) -> float:
        """Extrae un precio único, evitando rangos"""
        # Buscar patrones de precio chileno
        patterns = [
            r'\$?\s*([\d,]+(?:\.[\d]{3})*(?:\.\d{2})?)',
            r'([\d,]+(?:\.[\d]{3})*(?:\.\d{2})?)\s*pesos',
            r'([\d,]+(?:\.[\d]{3})*(?:\.\d{2})?)\s*CLP'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                # Tomar solo el primer precio encontrado
                precio_str = matches[0].replace(',', '').replace('.', '')
                try:
                    precio = float(precio_str)
                    if precio > 0:
                        return precio
                except ValueError:
                    continue
        
        return 0.0

    def _limpiar_nombre(self, nombre: str) -> str:
        # Eliminar patrones de precio y caracteres especiales
        nombre = re.sub(r'\$\s*\d+', '', nombre)
        nombre = re.sub(r'\d+\s*-\s*\d+', '', nombre)
        nombre = re.sub(r'[^\w\s\-\.]', '', nombre)
        nombre = re.sub(r'\s+', ' ', nombre)
        return nombre.strip()

    def _extract_url(self, product_element) -> str:
        links = product_element.select('a[href]')
        for link in links:
            href = link.get('href', '')
            if href and 'dbs.cl' in href:
                if not href.startswith('http'):
                    href = 'https://www.dbs.cl' + href
                return href
        return ""

    def _extract_imagen(self, product_element) -> str:
        # Selectores específicos basados en la estructura HTML de DBS
        img_selectors = [
            '.product-image-photo',
            '.product-item-photo img',
            '.product-image-container img',
            '.product-image-wrapper img',
            'img[src*="dbs.cl"]',
            'img[data-src*="dbs.cl"]',
            'img[srcset*="dbs.cl"]',
            '.product-item img',
            'a img',
            'img',
            '.product-image-photo img',
            '.product-item-photo-container img',
            '.product-item-image img',
            '.product-item-image-container img',
            '.product-item-info img',
            '.product-item-details img'
        ]
        
        # Primero buscar en src normal
        for selector in img_selectors:
            images = product_element.select(selector)
            for img in images:
                src = img.get('src', '')
                if src and 'dbs.cl' in src and not src.startswith('data:image/'):
                    if not src.startswith('http'):
                        src = 'https://www.dbs.cl' + src
                    return src
        
        # Buscar en atributos data-src (lazy loading)
        for selector in img_selectors:
            images = product_element.select(selector)
            for img in images:
                src = img.get('data-src', '')
                if src and 'dbs.cl' in src and not src.startswith('data:image/'):
                    if not src.startswith('http'):
                        src = 'https://www.dbs.cl' + src
                    return src
        
        # Buscar en el atributo srcset
        for selector in img_selectors:
            images = product_element.select(selector)
            for img in images:
                srcset = img.get('srcset', '')
                if srcset and 'dbs.cl' in srcset:
                    # Extraer la primera URL del srcset (sin parámetros de densidad)
                    urls = re.findall(r'([^\s,]+)', srcset)
                    for url in urls:
                        if 'dbs.cl' in url and not url.startswith('data:image/'):
                            # Remover parámetros de densidad (2x, 3x)
                            clean_url = re.sub(r'\s+\d+x$', '', url)
                            if not clean_url.startswith('http'):
                                clean_url = 'https://www.dbs.cl' + clean_url
                            return clean_url
        
        # Buscar en elementos padre que puedan contener imágenes
        parent_elements = product_element.select('a[href*="dbs.cl"]')
        for parent in parent_elements:
            images = parent.select('img')
            for img in images:
                src = img.get('src', '')
                if src and 'dbs.cl' in src and not src.startswith('data:image/'):
                    if not src.startswith('http'):
                        src = 'https://www.dbs.cl' + src
                    return src
        
        # Buscar en cualquier elemento que contenga una imagen
        all_images = product_element.find_all('img')
        for img in all_images:
            src = img.get('src', '')
            if src and 'dbs.cl' in src and not src.startswith('data:image/'):
                if not src.startswith('http'):
                    src = 'https://www.dbs.cl' + src
                return src
        
        return ""

    def _determinar_stock(self, product_element) -> str:
        # Buscar indicadores de stock
        stock_indicators = product_element.select('.stock, .availability, .product-stock')
        for indicator in stock_indicators:
            text = indicator.get_text(strip=True).lower()
            if 'agotado' in text or 'sin stock' in text or 'out of stock' in text:
                return "Out of stock"
        
        return "In stock"



    def scrapear_pagina_dbs(self, url: str) -> List[DBSProduct]:
        soup = self._get_page_with_selenium(url)
        if not soup:
            return []
        
        # Determinar categoría basada en la URL de la página
        categoria_pagina = "general"
        if '/skincare' in url:
            categoria_pagina = 'skincare'
        elif '/maquillaje' in url:
            categoria_pagina = 'maquillaje'
        
        # Usar solo selectores específicos para productos
        product_selectors = [
            '.product-item',
            'li.item.product.product-item'
        ]
        
        all_elements = []
        for selector in product_selectors:
            elements = soup.select(selector)
            all_elements.extend(elements)
        
        seen = set()
        unique_elements = []
        for element in all_elements:
            element_id = id(element)
            if element_id not in seen:
                seen.add(element_id)
                unique_elements.append(element)
        
        filtered_elements = []
        for element in unique_elements:
            text = element.get_text(strip=True)
            if not text or len(text) < 3:
                continue
            
            # Filtros más estrictos para elementos no válidos
            if any(keyword in text.lower() for keyword in ['filtro', 'filter', 'ordenar']):
                continue
            
            if not element.find('a'):
                continue
            
            filtered_elements.append(element)
        
        productos = []
        for element in filtered_elements:
            producto = self._extract_product_info_from_element(element, categoria_pagina)
            if producto:
                productos.append(producto)
        
        # Usar nombre + url como clave única
        productos_unicos = []
        seen_products = set()
        
        for producto in productos:
            product_key = f"{producto.nombre.lower().strip()}_{producto.url}"
            
            if product_key not in seen_products:
                seen_products.add(product_key)
                productos_unicos.append(producto)
        
        return productos_unicos

    def scrapear_catalogo_dbs(self, categoria: str, max_paginas: int = None, delay: float = 1.0) -> List[DBSProduct]:
        if max_paginas is None:
            max_paginas = self.obtener_total_paginas(categoria)
        
        todos_productos = []
        
        for pagina in range(1, max_paginas + 1):
            url = f"https://dbs.cl/{categoria}?p={pagina}"
            productos = self.scrapear_pagina_dbs(url)
            todos_productos.extend(productos)
            
            # Usar WebDriverWait en lugar de time.sleep
            if pagina < max_paginas:
                try:
                    WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '.product-item'))
                    )
                except:
                    time.sleep(delay)
        
        return todos_productos

    def close(self):
        if self.driver:
            self.driver.quit()




def scrapear_todas_categorias(headless=True, max_paginas_por_categoria=5):
    scraper = DBSSeleniumScraper(headless=headless)
    
    try:
        # Scrapear todas las categorías y recopilar todos los productos
        todos_productos = []
        categorias = ['maquillaje', 'skincare']
        
        for categoria in categorias:
            print(f"Scrapeando categoría: {categoria}")
            productos_categoria = scraper.scrapear_catalogo_dbs(categoria, max_paginas=max_paginas_por_categoria)
            # Agregar todos los productos con su categoría detectada
            for producto in productos_categoria:
                todos_productos.append(producto)
        
        print(f"\nTotal productos extraídos: {len(todos_productos)}")
        
        # Deduplicar productos usando URL como clave única (lógica de Maicao)
        productos_unicos = {}  # url -> producto
        for producto in todos_productos:
            if producto.url not in productos_unicos:
                productos_unicos[producto.url] = producto
        
        productos_finales = list(productos_unicos.values())
        print(f"Productos únicos después de deduplicación: {len(productos_finales)}")
        
        # Organizar productos por categoría final
        resultados = {}
        for categoria in categorias:
            productos_categoria = [p for p in productos_finales if p.categoria == categoria]
            resultados[categoria] = {
                'cantidad': len(productos_categoria),
                'productos': [producto.to_dict() for producto in productos_categoria]
            }
            print(f"Categoría '{categoria}': {len(productos_categoria)} productos únicos")
        
        from datetime import datetime
        data_completa = {
            'fecha_extraccion': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_productos': len(productos_finales),
            **resultados
        }
        
        # Guardar solo archivos separados por categoría
        archivos_guardados = guardar_resultados_por_categoria(data_completa, "dbs")
        print(f"\n=== RESUMEN DBS ===")
        print(f"Total archivos generados: {len(archivos_guardados)}")
        for archivo in archivos_guardados:
            print(f"  - {archivo}")
        
        return data_completa
        
    finally:
        scraper.close()




def guardar_resultados_por_categoria(resultados, tienda_prefix="dbs"):
    """
    Guarda los resultados en archivos JSON separados por categoría
    """
    # Obtener la ruta correcta al directorio data
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    data_dir = os.path.join(project_root, "data")
    os.makedirs(data_dir, exist_ok=True)
    archivos_guardados = []
    
    # Extraer metadatos generales
    metadatos = {
        'fecha_extraccion': resultados.get('fecha_extraccion'),
        'tienda': tienda_prefix.upper()
    }
    
    # Guardar cada categoría en un archivo separado
    for categoria, datos_categoria in resultados.items():
        if categoria in ['fecha_extraccion', 'total_productos']:
            continue  # Saltar metadatos
            
        # Crear estructura para archivo individual
        estructura_categoria = {
            **metadatos,
            'categoria': categoria,
            'total_productos': datos_categoria['cantidad'],
            'productos': datos_categoria['productos']
        }
        
        # Nombre del archivo: tienda_categoria.json
        nombre_archivo = f"{tienda_prefix}_{categoria}.json"
        ruta_archivo = os.path.join(data_dir, nombre_archivo)
        
        # Guardar archivo
        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            json.dump(estructura_categoria, f, ensure_ascii=False, indent=2)
        
        print(f"Categoría '{categoria}' guardada en: {ruta_archivo}")
        archivos_guardados.append(ruta_archivo)
    
    return archivos_guardados




if __name__ == "__main__":
    print("=== SCRAPER DBS - ARCHIVOS SEPARADOS POR CATEGORÍA ===")
    print("Iniciando scraping de DBS con archivos separados...")
    
    # Configuración
    headless = True  # Cambiar a False si quieres ver el navegador
    max_paginas_por_categoria = 5  # Limitar para pruebas, usar None para todas las páginas
    
    try:
        resultado = scrapear_todas_categorias(
            headless=headless, 
            max_paginas_por_categoria=max_paginas_por_categoria
        )
        
        print(f"\n🎉 SCRAPING COMPLETADO")
        print(f"Total productos extraídos: {resultado['total_productos']}")
        
        for categoria, datos in resultado.items():
            if categoria not in ['fecha_extraccion', 'total_productos']:
                print(f"  {categoria}: {datos['cantidad']} productos")
        
    except Exception as e:
        print(f"❌ Error durante el scraping: {e}")
        import traceback
        traceback.print_exc()
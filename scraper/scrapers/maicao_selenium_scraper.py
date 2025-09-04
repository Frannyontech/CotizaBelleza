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
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

class MaicaoProduct:
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

class MaicaoSeleniumScraper:
    def __init__(self, headless: bool = True):
        self.driver = None
        self.setup_driver(headless)
        
        # Lista de marcas conocidas para identificación
        self.marcas_conocidas = [
            'MAYBELLINE', 'REVLON', 'L\'OREAL', 'LOREAL', 'NYX', 'ESSENCE', 
            'CATRICE', 'COVERGIRL', 'RIMMEL', 'BOURJOIS', 'MILANI', 
            'WET N WILD', 'SKIN1004', 'MIXSOON', 'NEUTROGENA', 'TOCOBO', 
            'NIVEA', 'KIKO', 'CLINIQUE', 'ESTEE LAUDER', 'LANCOME', 
            'DIOR', 'CHANEL', 'MAC', 'URBAN DECAY', 'TOO FACED', 'BENEFIT',
            'THE ORDINARY', 'CERAVE', 'LA ROCHE POSAY', 'VICHY', 'EUCERIN',
            'GARNIER', 'OLAY', 'POND\'S', 'AVEENO', 'DOVE', 'MAICAO'
        ]

    def setup_driver(self, headless: bool):
        options = Options()
        
        # Modo incógnito para evitar cookies
        options.add_argument('--incognito')
        
        if headless:
            options.add_argument('--headless=new')
        
        # Configuración optimizada
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Configuraciones experimentales anti-detección
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Logging reducido
        options.add_argument('--log-level=3')
        options.add_argument('--silent')
        options.add_argument('--disable-logging')
        
        self.driver = webdriver.Chrome(options=options)
        
        # Limpiar cookies al inicio
        self.driver.delete_all_cookies()
        
        # Ocultar propiedades de webdriver
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Configurar headers adicionales
        self.driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {
            'headers': {
                'DNT': '1',
                'Sec-GPC': '1',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
        })

    def _detect_total_pages(self, categoria_url: str) -> int:
        """Detecta el número total de páginas disponibles"""
        try:
            self.driver.get(categoria_url)
            time.sleep(5)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Buscar elementos de paginación
            pagination_elements = soup.select('.pagination')
            if pagination_elements:
                # Buscar el texto de paginación como "1234...109"
                pagination_text = pagination_elements[0].get_text(strip=True)
                
                # Extraer el último número que indica el total de páginas
                numbers = re.findall(r'\d+', pagination_text)
                if numbers:
                    total_pages = int(numbers[-1])  # El último número suele ser el total
                    print(f"Total de páginas detectadas: {total_pages}")
                    return total_pages
            
            # Fallback: buscar botones de página numerados
            page_buttons = soup.select('.btn-page, [class*="page"]')
            page_numbers = []
            for button in page_buttons:
                text = button.get_text(strip=True)
                if text.isdigit():
                    page_numbers.append(int(text))
            
            if page_numbers:
                total_pages = max(page_numbers)
                print(f"Total de páginas detectadas (fallback): {total_pages}")
                return total_pages
            
            print("No se pudo detectar el número total de páginas, usando 1")
            return 1
            
        except Exception as e:
            print(f"Error detectando total de páginas: {e}")
            return 1

    def _extract_product_price_from_detail(self, product_url: str) -> float:
        """Extrae el precio de la página de detalle del producto si no se encuentra en la lista"""
        try:
            # Abrir nueva pestaña
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[1])
            
            # Navegar a la página del producto
            self.driver.get(product_url)
            time.sleep(3)
            
            # Buscar precio en la página de detalle
            precio_selectores = [
                '.price', '.product-price', '.price-value', '.price-current',
                '.precio', '.valor', '.cost', '.amount', '[class*="price"]',
                '.product-price-value', '.price-box .price', '.price-wrapper .price'
            ]
            
            for selector in precio_selectores:
                try:
                    precio_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    precio_texto = precio_element.text.strip()
                    if precio_texto and '$' in precio_texto:
                        precio = self._extraer_precio_del_texto(precio_texto)
                        if precio > 0:
                            return precio
                except NoSuchElementException:
                    continue
            
            # Buscar en el HTML completo si no se encuentra con selectores
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            texto_completo = soup.get_text()
            precio_match = re.search(r'\$[\s]*([0-9,.]+)', texto_completo)
            if precio_match:
                precio = self._extraer_precio_del_texto(precio_match.group())
                if precio > 0:
                    return precio
            
            return 0
            
        except Exception as e:
            print(f"Error extrayendo precio de detalle: {e}")
            return 0
        finally:
            # Cerrar pestaña y volver a la principal
            try:
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
            except Exception:
                pass

    def _extraer_precio_del_texto(self, texto: str) -> float:
        """Extrae precio numérico del texto, retornando float CLP"""
        if not texto:
            return 0
        
        # Buscar patrones de precio chileno
        patterns = [
            r'\$[\s]*([0-9,.]+)',
            r'([0-9,.]+)[\s]*pesos',
            r'([0-9,.]+)[\s]*CLP'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, texto.replace(' ', ''))
            if match:
                precio_str = match.group(1).replace(',', '').replace('.', '')
                try:
                    precio = float(precio_str)
                    if precio > 0:
                        return precio
                except ValueError:
                    continue
        
        return 0

    def _extract_marca_from_element(self, product_element) -> str:
        """Extrae la marca del elemento de producto"""
        # Buscar específicamente en enlaces de marca de Maicao
        marca_links = product_element.select('a[href*="/busqueda?q="]')
        for link in marca_links:
            marca_texto = link.get_text(strip=True)
            if marca_texto and marca_texto.upper() in self.marcas_conocidas:
                return marca_texto.upper()
        
        # Buscar en elementos con clase brand
        brand_elements = product_element.select('[class*="brand"]')
        for element in brand_elements:
            marca_texto = element.get_text(strip=True)
            if marca_texto and len(marca_texto) > 1:
                return marca_texto.upper()
        
        # Fallback: extraer de nombre
        return "MAICAO"
    
    def _extract_marca_from_name(self, nombre: str) -> str:
        """Extrae la marca del nombre del producto"""
        if not nombre:
            return "MAICAO"
        
        nombre_upper = nombre.upper()
        
        # Buscar marcas conocidas en el nombre
        for marca in self.marcas_conocidas:
            if marca in nombre_upper:
                return marca
        
        # Si no encuentra marca conocida, tomar la primera palabra
        primera_palabra = nombre.split()[0] if nombre.split() else "MAICAO"
        return primera_palabra.upper()

    def _determine_stock_status(self, product_element) -> str:
        """Determina el estado del stock del producto"""
        texto_elemento = product_element.get_text().lower()
        
        # Indicadores de productos agotados
        indicadores_agotado = [
            'agotado', 'sin stock', 'out of stock', 'no disponible', 
            'no available', 'sold out', 'fuera de stock'
        ]
        
        for indicador in indicadores_agotado:
            if indicador in texto_elemento:
                return "Out of stock"
        
        # Si no hay indicadores de agotado, asumir que está en stock
        return "In stock"

    def _extract_product_info_from_element(self, product_element, categoria: str) -> Optional[MaicaoProduct]:
        """Extrae información de un elemento de producto"""
        try:
            # Extraer nombre
            nombre = self._extract_nombre(product_element)
            if not nombre or len(nombre.strip()) < 3:
                return None
            
            # Extraer URL
            url = self._extract_url(product_element)
            if not url:
                return None
            
            # Extraer precio (primero de la lista, luego de detalle si es necesario)
            precio = self._extract_precio(product_element)
            if precio <= 0 and url:
                print(f"Precio no encontrado en lista para '{nombre}', extrayendo de página de detalle...")
                precio = self._extract_product_price_from_detail(url)
            
            # Extraer otros campos
            imagen = self._extract_imagen(product_element)
            marca = self._extract_marca_from_element(product_element)
            if marca == "MAICAO":  # Si no encontró marca en el elemento, buscar en el nombre
                marca = self._extract_marca_from_name(nombre)
            stock = self._determine_stock_status(product_element)
            
            return MaicaoProduct(
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
        """Extrae el nombre del producto"""
        # Buscar en enlaces específicos que contienen el nombre del producto
        enlaces = product_element.select('a[href*=".html"]')
        for enlace in enlaces:
            texto = enlace.get_text(strip=True)
            if texto and len(texto) > 3 and self._es_texto_valido(texto):
                # Evitar texto de marca solamente
                if texto.upper() not in self.marcas_conocidas:
                    return self._limpiar_nombre(texto)
        
        # Fallback: buscar en selectores tradicionales
        nombre_selectores = [
            '.product-name', '.product-title', '.product-item-name',
            'h2', 'h3', 'h4', '.item-name', '.title', '.name',
            'a[title]', '.product-name a', '.product-title a',
            '[class*="title"]', '[class*="name"]'
        ]
        
        for selector in nombre_selectores:
            elementos = product_element.select(selector)
            for elemento in elementos:
                if selector == 'a[title]':
                    texto = elemento.get('title', '').strip()
                else:
                    texto = elemento.get_text(strip=True)
                
                if texto and len(texto) > 3 and self._es_texto_valido(texto):
                    return self._limpiar_nombre(texto)
        
        return ""

    def _extract_precio(self, product_element) -> float:
        """Extrae el precio del elemento de producto"""
        # Buscar específicamente en la clase .sales que contiene el precio en Maicao
        precio_selectores = [
            '.sales',  # Selector específico de Maicao
            '.price', '.product-price', '.price-value', '.price-current',
            '.precio', '.valor', '.cost', '.amount', '[class*="price"]',
            '.price-box .price', '.price-wrapper .price'
        ]
        
        for selector in precio_selectores:
            elementos = product_element.select(selector)
            for elemento in elementos:
                texto = elemento.get_text(strip=True)
                if texto and '$' in texto:
                    precio = self._extraer_precio_del_texto(texto)
                    if precio > 0:
                        return precio
        
        return 0

    def _extract_url(self, product_element) -> str:
        """Extrae la URL del producto"""
        # Buscar específicamente enlaces que contengan .html (productos de Maicao)
        enlaces = product_element.select('a[href*=".html"]')
        for enlace in enlaces:
            href = enlace.get('href', '')
            if href:
                if href.startswith('http'):
                    return href
                elif href.startswith('/'):
                    return f"https://www.maicao.cl{href}"
        
        # Fallback: buscar cualquier enlace
        enlaces = product_element.select('a[href]')
        for enlace in enlaces:
            href = enlace.get('href', '')
            if href and '.html' in href:
                if href.startswith('http'):
                    return href
                elif href.startswith('/'):
                    return f"https://www.maicao.cl{href}"
        return ""

    def _extract_imagen(self, product_element) -> str:
        """Extrae la URL de la imagen del producto"""
        # Buscar específicamente imágenes del producto (no iconos o badges)
        imagenes = product_element.select('img[alt*="imagen"], img[src*="large/"]')
        for img in imagenes:
            src = img.get('src', '')
            if src and 'large/' in src and not src.startswith('data:'):
                if src.startswith('http'):
                    return src
                elif src.startswith('/'):
                    return f"https://www.maicao.cl{src}"
        
        # Fallback: buscar cualquier imagen con src válido
        img_selectores = [
            'img[src]', 'img[data-src]', 'img[data-lazy]', 'img[data-original]'
        ]
        
        for selector in img_selectores:
            imagenes = product_element.select(selector)
            for img in imagenes:
                src = (img.get('src') or img.get('data-src') or 
                      img.get('data-lazy') or img.get('data-original', ''))
                
                # Filtrar iconos y badges
                if (src and not src.startswith('data:') and 
                    'cart-icon' not in src and 'ribbon-' not in src and 
                    len(src) > 20):
                    if src.startswith('http'):
                        return src
                    elif src.startswith('/'):
                        return f"https://www.maicao.cl{src}"
        
        return ""

    def _es_texto_valido(self, texto: str) -> bool:
        """Valida que el texto sea un nombre de producto válido"""
        # Eliminar caracteres especiales para verificación
        texto_limpio = re.sub(r'[^\w\s]', '', texto).strip()
        
        # Verificar que no contenga solo números
        if texto_limpio.isdigit():
            return False
        
        # Verificar que tenga letras
        if not re.search(r'[a-zA-Z]', texto_limpio):
            return False
        
        # Verificar que no sea un precio
        if re.search(r'\$\s*\d+', texto):
            return False
        
        return True

    def _limpiar_nombre(self, nombre: str) -> str:
        """Limpia y normaliza el nombre del producto"""
        # Eliminar patrones de precio y caracteres especiales innecesarios
        nombre = re.sub(r'\$\s*\d+', '', nombre)
        nombre = re.sub(r'\d+\s*-\s*\d+', '', nombre)
        nombre = re.sub(r'[^\w\s\-\.]', ' ', nombre)
        nombre = re.sub(r'\s+', ' ', nombre)
        return nombre.strip()

    def scrape_category(self, categoria_url: str, categoria_nombre: str, max_pages: int = None) -> List[MaicaoProduct]:
        """Scrapea una categoría específica de Maicao usando paginación"""
        # Mostrar nombre amigable para logs
        nombre_display = "cuidado de la piel" if categoria_nombre == "skincare" else categoria_nombre
        print(f"Scrapeando categoría: {nombre_display}")
        print(f"URL: {categoria_url}")
        
        try:
            # Detectar el total de páginas disponibles
            if max_pages is None:
                total_pages = self._detect_total_pages(categoria_url)
            else:
                total_pages = max_pages
            
            print(f"Scrapeando {total_pages} páginas de productos...")
            
            todos_productos = []
            productos_por_pagina = 18  # Maicao muestra 18 productos por página
            
            for pagina in range(1, total_pages + 1):
                # Calcular el parámetro start (empieza en 0 para la primera página)
                start = (pagina - 1) * productos_por_pagina
                url_pagina = f"{categoria_url}?start={start}" if start > 0 else categoria_url
                
                print(f"\nPágina {pagina}/{total_pages}: {url_pagina}")
                
                try:
                    # Navegar a la página específica
                    self.driver.get(url_pagina)
                    time.sleep(3)  # Tiempo para carga
                    
                    # Obtener HTML de la página
                    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    
                    # Buscar elementos de productos
                    elementos_productos = soup.select('.product.product-wrapper')
                    
                    if not elementos_productos:
                        print(f"No se encontraron productos en la página {pagina}, terminando...")
                        break
                    
                    print(f"Productos encontrados en página {pagina}: {len(elementos_productos)}")
                    
                    # Procesar productos de esta página
                    productos_pagina = []
                    for i, elemento in enumerate(elementos_productos):
                        try:
                            producto = self._extract_product_info_from_element(elemento, categoria_nombre)
                            
                            if producto and producto.nombre:
                                productos_pagina.append(producto)
                            
                        except Exception as e:
                            print(f"Error procesando producto {i+1} en página {pagina}: {e}")
                    
                    # Agregar productos de esta página al total
                    todos_productos.extend(productos_pagina)
                    
                    print(f"Productos válidos extraídos de página {pagina}: {len(productos_pagina)}")
                    
                    # Progreso cada 10 páginas
                    if pagina % 10 == 0:
                        print(f"Progreso: {pagina}/{total_pages} páginas procesadas. Total productos: {len(todos_productos)}")
                    
                    # Pausa entre páginas para evitar sobrecarga del servidor
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"Error en página {pagina}: {e}")
                    continue
            
            # Eliminar duplicados basados en URL (por si acaso)
            productos_unicos = []
            urls_vistas = set()
            
            for producto in todos_productos:
                if producto.url not in urls_vistas:
                    urls_vistas.add(producto.url)
                    productos_unicos.append(producto)
            
            print(f"\nCategoría {nombre_display} completada:")
            print(f"- Total páginas procesadas: {total_pages}")
            print(f"- Productos extraídos (con duplicados): {len(todos_productos)}")
            print(f"- Productos únicos finales: {len(productos_unicos)}")
            
            return productos_unicos
            
        except Exception as e:
            print(f"Error scrapeando categoría {categoria_nombre}: {e}")
            return []

    def close(self):
        """Cierra el driver de Selenium"""
        if self.driver:
            self.driver.quit()

def scrape_maicao_all_categories(headless: bool = True, max_pages_per_category: int = None) -> Dict:
    """Función principal que scrapea todas las categorías de Maicao"""
    
    # URLs de las categorías
    categorias = {
        "maquillaje": "https://www.maicao.cl/maquillaje/",
        "skincare": "https://www.maicao.cl/cuidado-de-la-piel/"
    }
    
    scraper = MaicaoSeleniumScraper(headless=headless)
    resultados = {}
    
    try:
        for categoria_nombre, categoria_url in categorias.items():
            print(f"\n{'='*50}")
            print(f"SCRAPEANDO CATEGORÍA: {categoria_nombre.upper()}")
            print(f"{'='*50}")
            
            productos_categoria = scraper.scrape_category(categoria_url, categoria_nombre, max_pages_per_category)
            
            # Convertir productos a diccionarios y agregar a resultados
            productos_dict = [producto.to_dict() for producto in productos_categoria]
            resultados[categoria_nombre] = {
                'cantidad': len(productos_categoria),
                'productos': productos_dict
            }
            
            nombre_display = "cuidado de la piel" if categoria_nombre == "skincare" else categoria_nombre
            print(f"Categoría {nombre_display}: {len(productos_categoria)} productos extraídos")
            
            # Pausa entre categorías
            time.sleep(3)
        
        # Crear estructura final consistente con otros scrapers
        from datetime import datetime
        data_completa = {
            'fecha_extraccion': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_productos': sum(cat['cantidad'] for cat in resultados.values()),
            **resultados
        }
        
        # Estadísticas finales
        print(f"\n{'='*50}")
        print("ESTADÍSTICAS FINALES")
        print(f"{'='*50}")
        
        for categoria, datos in resultados.items():
            nombre_display = "cuidado de la piel" if categoria == "skincare" else categoria
            print(f"Categoría '{nombre_display}': {datos['cantidad']} productos")
        
        print(f"TOTAL FINAL: {data_completa['total_productos']} productos")
        
        # Guardar solo archivos separados por categoría
        archivos_guardados = guardar_resultados_por_categoria_maicao(data_completa, "maicao")
        print(f"\n=== RESUMEN MAICAO ===")
        print(f"Total archivos generados: {len(archivos_guardados)}")
        for archivo in archivos_guardados:
            print(f"  - {archivo}")
        
        return data_completa
        
    except Exception as e:
        print(f"Error general en el scraping: {e}")
        return {}
    
    finally:
        scraper.close()

def guardar_resultados_por_categoria_maicao(resultados, tienda_prefix="maicao"):
    """
    Guarda los resultados en archivos JSON separados por categoría para Maicao
    """
    # Obtener la ruta absoluta desde el directorio del script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))  # Subir dos niveles: scraper/scrapers -> scraper -> raíz
    data_dir = os.path.join(project_root, "data", "raw")
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
    print("=== SCRAPER MAICAO - ARCHIVOS SEPARADOS POR CATEGORÍA ===")
    print("Iniciando scraping de Maicao con archivos separados...")
    
    # Configuración
    max_pages = 5  # Limitado a 5 páginas por categoría
    headless = True  # Cambiar a False si quieres ver el navegador
    
    if max_pages:
        print(f"MODO PRUEBA: Limitado a {max_pages} páginas por categoría")
    else:
        print("MODO COMPLETO: Scrapeando todas las páginas disponibles")
    
    try:
        resultado = scrape_maicao_all_categories(headless=headless, max_pages_per_category=max_pages)
        
        print(f"\nSCRAPING COMPLETADO")
        total = resultado.get('total_productos', 0) if isinstance(resultado, dict) else len(resultado)
        print(f"Total productos extraídos: {total}")
        
        if isinstance(resultado, dict):
            for categoria, datos in resultado.items():
                if categoria not in ['fecha_extraccion', 'total_productos']:
                    print(f"  {categoria}: {datos['cantidad']} productos")
        
    except Exception as e:
        print(f"Error durante el scraping: {e}")
        import traceback
        traceback.print_exc()

import time
import re
import os
import json
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def scrape_preunic_list(categoria: str = "maquillaje", headless: bool = True, max_scrolls: int = 15, scroll_delay: float = 1.0, save_json: bool = True) -> List[Dict]:
    """
    Scraper para productos de Preunic con scroll infinito
    
    Args:
        categoria: Categoría a scrapear ('maquillaje', 'skincare', 'perfumes')
        headless: Ejecutar en modo headless
        max_scrolls: Máximo número de scrolls a realizar
        scroll_delay: Delay entre scrolls en segundos
        save_json: Si guardar resultados en JSON automáticamente
    
    Returns:
        Lista de diccionarios con datos de productos
    """
    
    # Mapeo de categorías: nombre estándar -> nombre en Preunic
    categoria_mapping = {
        'maquillaje': 'maquillaje',
        'skincare': 'cuidado del rostro',
        'perfumes': 'perfumes'
    }
    
    # Obtener la categoría real de Preunic
    categoria_preunic = categoria_mapping.get(categoria, categoria)
    categoria_estandar = categoria  # Mantener el nombre estándar para el resultado
    
    print(f"Categoría solicitada: {categoria}")
    if categoria_preunic != categoria:
        print(f"Categoría en Preunic: {categoria_preunic}")
    
    # Configurar opciones optimizadas de Chrome
    options = Options()
    if headless:
        options.add_argument('--headless=new')
    
    # Configuración básica optimizada
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1366,900')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-web-security')
    options.add_argument('--disable-features=VizDisplayCompositor')
    
    # Configuración anti-detección
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-plugins')
    options.add_argument('--disable-background-networking')
    options.add_argument('--disable-background-timer-throttling')
    options.add_argument('--disable-renderer-backgrounding')
    options.add_argument('--disable-backgrounding-occluded-windows')
    
    # User agent
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Configuraciones experimentales
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option("detach", True)
    
    # Logging reducido
    options.add_argument('--log-level=3')
    options.add_argument('--silent')
    options.add_argument('--disable-logging')
    
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        
        # Ocultar propiedades de webdriver
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Navegar a la URL de la categoría especificada usando el nombre en Preunic
        if categoria_preunic == 'cuidado del rostro':
            url = f"https://preunic.cl/t/maquillaje?categories%5B0%5D=cuidado%20del%20rostro"
        else:
            url = f"https://preunic.cl/t/{categoria_preunic}?categories%5B0%5D={categoria_preunic}"
        
        print(f"Cargando página de {categoria_estandar}: {url}")
        driver.get(url)
        
        # Esperar inicial
        time.sleep(5)
        
        # Esperar explícitamente a que se carguen los elementos .ais-Hits-item
        print("Esperando elementos .ais-Hits-item...")
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.ais-Hits-item'))
            )
            print("Elementos .ais-Hits-item encontrados!")
        except Exception as e:
            print(f"No se encontraron elementos .ais-Hits-item: {e}")
        
        # Realizar scroll infinito optimizado hasta que no carguen más productos
        print(f"Iniciando scroll infinito (máximo {max_scrolls} scrolls)...")
        productos_anteriores = 0
        scrolls_realizados = 0
        productos_sin_cambio = 0
        
        while scrolls_realizados < max_scrolls:
            # Hacer scroll hacia abajo de forma más suave
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_delay)
            
            # Contar productos actuales
            elementos_actuales = driver.find_elements(By.CSS_SELECTOR, '.ais-Hits-item')
            productos_actuales = len(elementos_actuales)
            
            print(f"Scroll {scrolls_realizados + 1}/{max_scrolls}: {productos_actuales} productos")
            
            # Si no hay nuevos productos, incrementar contador
            if productos_actuales == productos_anteriores:
                productos_sin_cambio += 1
                if productos_sin_cambio >= 3:  # Salir después de 3 scrolls sin cambios
                    print("No se cargaron más productos después de 3 intentos, finalizando scroll")
                    break
            else:
                productos_sin_cambio = 0  # Resetear contador si hay cambios
            
            productos_anteriores = productos_actuales
            scrolls_realizados += 1
        
        # Obtener HTML final
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Buscar todos los elementos de productos
        productos_elementos = soup.select('.ais-Hits-item')
        print(f"Total elementos de productos encontrados: {len(productos_elementos)}")
        
        productos_finales = []
        productos_procesados = 0
        productos_con_error = 0
        
        print(f"Procesando {len(productos_elementos)} productos...")
        
        for i, elemento in enumerate(productos_elementos):
            try:
                productos_procesados += 1
                
                # Extraer nombre del producto (aria-label del <a>) con mejor búsqueda
                nombre = ""
                link_element = elemento.select_one('a[aria-label]')
                if link_element:
                    nombre = link_element.get('aria-label', '').strip()
                
                if not nombre:
                    # Fallback mejorado: buscar en múltiples selectores
                    nombre_selectors = [
                        'h2', 'h3', 'h4',
                        '.product-title', '.product-name',
                        '[class*="title"]', '[class*="name"]',
                        'a[title]'
                    ]
                    for selector in nombre_selectors:
                        nombre_alt = elemento.select_one(selector)
                        if nombre_alt:
                            if selector == 'a[title]':
                                nombre = nombre_alt.get('title', '').strip()
                            else:
                                nombre = nombre_alt.get_text(strip=True)
                            if nombre:
                                break
                
                # Extraer URL absoluta del producto
                url_producto = ""
                if link_element:
                    href = link_element.get('href', '')
                    if href:
                        if href.startswith('http'):
                            url_producto = href
                        else:
                            url_producto = f"https://preunic.cl{href}"
                
                # Extraer imagen (src del <img>) con fallbacks
                imagen = ""
                img_selectors = ['img[src]', 'img[data-src]', 'img[data-lazy]']
                for img_selector in img_selectors:
                    img_element = elemento.select_one(img_selector)
                    if img_element:
                        src = img_element.get('src') or img_element.get('data-src') or img_element.get('data-lazy', '')
                        if src and not src.startswith('data:'):
                            if src.startswith('http'):
                                imagen = src
                            else:
                                imagen = f"https://preunic.cl{src}"
                            break
                
                # Extraer precio (.plp-price, [class*="price"] o span que contenga $)
                precio_texto = ""
                precio_normalizado = 0
                
                # Buscar en selectores específicos
                precio_selectors = [
                    '.plp-price',
                    '[class*="price"]',
                    '.price',
                    '.product-price'
                ]
                
                for selector in precio_selectors:
                    precio_element = elemento.select_one(selector)
                    if precio_element:
                        precio_texto = precio_element.get_text(strip=True)
                        if '$' in precio_texto:
                            break
                
                # Si no se encuentra precio, buscar cualquier texto que contenga $
                if not precio_texto:
                    texto_completo = elemento.get_text()
                    precio_match = re.search(r'\$[\d,.\s]+', texto_completo)
                    if precio_match:
                        precio_texto = precio_match.group()
                
                # Normalizar el precio eliminando $, puntos y espacios, retornando un int
                if precio_texto:
                    precio_clean = re.sub(r'[^\d]', '', precio_texto)
                    if precio_clean:
                        try:
                            precio_normalizado = int(precio_clean)
                        except ValueError:
                            precio_normalizado = 0
                
                # Extraer marca del nombre del producto
                marca = extraer_marca_del_nombre(nombre)
                
                # Validar datos mínimos antes de agregar
                if nombre and url_producto and len(nombre) > 2:
                    producto = {
                        'name': nombre.strip(),
                        'url': url_producto.strip(),
                        'image': imagen.strip(),
                        'price': precio_normalizado,
                        'price_text': precio_texto.strip(),
                        'categoria': categoria_estandar
                    }
                    productos_finales.append(producto)
                else:
                    print(f"Producto {i+1} omitido por datos insuficientes")
                    
            except Exception as e:
                productos_con_error += 1
                print(f"Error procesando producto {i+1}: {e}")
                continue
        
        # Mostrar estadísticas de procesamiento
        print(f"\nEstadísticas de procesamiento:")
        print(f"Productos encontrados: {len(productos_elementos)}")
        print(f"Productos procesados: {productos_procesados}")
        print(f"Productos válidos extraídos: {len(productos_finales)}")
        print(f"Productos con errores: {productos_con_error}")
        
        # Guardar resultados automáticamente si se especifica
        if save_json and productos_finales:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            filename = f"scraper/data/preunic_{categoria_estandar}_{timestamp}.json"
            os.makedirs("scraper/data", exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(productos_finales, f, ensure_ascii=False, indent=2)
            
            print(f"Resultados guardados automáticamente en: {filename}")
        
        return productos_finales
        
    except Exception as e:
        print(f"Error general en scraping: {e}")
        return []
    
    finally:
        if driver:
            driver.quit()

def extraer_marca_del_nombre(nombre: str) -> str:
    """Extraer la marca del nombre del producto"""
    if not nombre:
        return "PREUNIC"
    
    # Lista de marcas conocidas
    marcas_conocidas = [
        'MAYBELLINE', 'REVLON', 'L\'OREAL', 'LOREAL', 'COVERGIRL', 'RIMMEL',
        'BOURJOIS', 'MILANI', 'WET N WILD', 'NYX', 'ESSENCE', 'CATRICE',
        'SKIN1004', 'MIXSOON', 'NEUTROGENA', 'TOCOBO', 'NIVEA', 'KIKO',
        'CLINIQUE', 'ESTEE LAUDER', 'LANCOME', 'DIOR', 'CHANEL'
    ]
    
    nombre_upper = nombre.upper()
    
    # Buscar marca en el nombre
    for marca in marcas_conocidas:
        if marca in nombre_upper:
            return marca
    
    # Si no encuentra marca conocida, tomar la primera palabra
    primera_palabra = nombre.split()[0] if nombre.split() else "PREUNIC"
    return primera_palabra.upper()

def main_scraper_preunic(categoria: str = "maquillaje", headless: bool = True):
    """
    Función principal que ejecuta el scraping
    """
    print(f"Scraper de Preunic - {categoria.upper()}")
    print("Iniciando extracción de productos...")
    
    # Ejecutar scraping con configuración optimizada
    productos = scrape_preunic_list(
        categoria=categoria,
        headless=headless,
        max_scrolls=20,
        scroll_delay=0.8,
        save_json=True
    )
    
    print(f"\nTotal de productos extraídos: {len(productos)}")
    
    if productos:
        # Análisis de datos
        precios = [p['price'] for p in productos if p['price'] > 0]
        productos_con_imagen = sum(1 for p in productos if p['image'])
        
        print(f"Productos con precio válido: {len(precios)}")
        print(f"Productos con imagen: {productos_con_imagen}")
        if precios:
            print(f"Precio promedio: ${sum(precios)//len(precios):,}")
            print(f"Precio mínimo: ${min(precios):,}")
            print(f"Precio máximo: ${max(precios):,}")
    
    return productos

if __name__ == "__main__":
    main_scraper_preunic()
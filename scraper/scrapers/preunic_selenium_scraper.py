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

def parse_precio(txt: str) -> int | None:
    """
    Normaliza precios CLP: "$7.299" -> 7299 (int)
    """
    if not txt: 
        return None
    # quita espacios, símbolos y separadores de miles
    t = txt.strip()
    t = re.sub(r"[^\d]", "", t)  # deja solo dígitos
    return int(t) if t else None

def get_text_by_selectors(node, selectors):
    """
    Busca texto usando múltiples selectores en orden de prioridad
    """
    for sel in selectors:
        try:
            el = node.find_element("css selector", sel)
            txt = el.text.strip()
            if txt: 
                return txt
        except Exception:
            continue
    return ""

def get_text_by_selectors_soup(element, selectors):
    """
    Busca texto usando múltiples selectores con BeautifulSoup
    """
    for sel in selectors:
        try:
            el = element.select_one(sel)
            if el:
                txt = el.get_text(strip=True)
                if txt:
                    return txt
        except Exception:
            continue
    return ""

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
                
                # Extraer precios: normal y oferta (según estructura actual de Preunic)
                
                # Buscar todos los textos que contengan "Normal:" y "Oferta:"
                def extract_preunic_prices(elemento):
                    texto_completo = elemento.get_text()
                    precio_normal = None
                    precio_oferta = None
                    
                    # Buscar "Normal: $XXXX"
                    normal_match = re.search(r'Normal:\s*\$?([\d,\.]+)', texto_completo, re.IGNORECASE)
                    if normal_match:
                        precio_normal = parse_precio(normal_match.group(1))
                    
                    # Buscar "Oferta: $XXXX" 
                    oferta_match = re.search(r'Oferta:\s*\$?([\d,\.]+)', texto_completo, re.IGNORECASE)
                    if oferta_match:
                        precio_oferta = parse_precio(oferta_match.group(1))
                    
                    # Evitar sbpay - buscar y excluir cualquier precio que aparezca después de "sbpay"
                    # NO extraer precios que estén cerca de "sbpay"
                    if 'sbpay' in texto_completo.lower():
                        # Si hay sbpay, ser más específico con las extracciones
                        lineas = texto_completo.split('\n')
                        for linea in lineas:
                            if 'sbpay' in linea.lower():
                                continue  # Saltar líneas que contengan sbpay
                            
                            if 'normal:' in linea.lower():
                                normal_match = re.search(r'Normal:\s*\$?([\d,\.]+)', linea, re.IGNORECASE)
                                if normal_match:
                                    precio_normal = parse_precio(normal_match.group(1))
                            
                            if 'oferta:' in linea.lower():
                                oferta_match = re.search(r'Oferta:\s*\$?([\d,\.]+)', linea, re.IGNORECASE)
                                if oferta_match:
                                    precio_oferta = parse_precio(oferta_match.group(1))
                    
                    return precio_normal, precio_oferta
                
                precio_normal, precio_oferta = extract_preunic_prices(elemento)
                
                # Debug: mostrar qué se extrajo
                if i <= 3:  # Solo para los primeros 3 productos para no llenar logs
                    texto_debug = elemento.get_text()[:200] + "..." if len(elemento.get_text()) > 200 else elemento.get_text()
                    print(f"DEBUG Producto {i+1}: Normal={precio_normal}, Oferta={precio_oferta}")
                    print(f"Texto: {texto_debug}")
                
                # Fallback: si no encuentra precios con los patrones anteriores, buscar cualquier precio
                if precio_normal is None and precio_oferta is None:
                    # Buscar cualquier precio en el elemento, pero evitar sbpay
                    texto = elemento.get_text()
                    if 'sbpay' not in texto.lower():
                        # Buscar precio con formato $X.XXX
                        precio_match = re.search(r'\$[\d,\.]+', texto)
                        if precio_match:
                            precio_normal = parse_precio(precio_match.group())
                
                # Precio vigente para compatibilidad
                precio_vigente = precio_oferta if precio_oferta is not None else precio_normal
                
                # Validaciones de precios
                if precio_oferta is not None and precio_normal is not None:
                    if precio_oferta > precio_normal:
                        print(f"Advertencia: Precio oferta ({precio_oferta}) mayor que precio normal ({precio_normal}) en producto {i+1}")
                
                # Mantener compatibilidad con código legado
                precio_normalizado = precio_vigente if precio_vigente is not None else 0
                
                # Generar texto de precio para compatibilidad
                if precio_oferta is not None:
                    precio_texto = f"${precio_oferta:,}"
                elif precio_normal is not None:
                    precio_texto = f"${precio_normal:,}"
                else:
                    precio_texto = ""
                
                # Extraer marca del nombre del producto
                marca = extraer_marca_del_nombre(nombre)
                
                # Validar datos mínimos antes de agregar
                if nombre and url_producto and len(nombre) > 2:
                    # Advertencia si no hay precio válido
                    if precio_vigente is None or precio_vigente == 0:
                        print(f"Advertencia: Producto {i+1} sin precio válido: {nombre[:50]}...")
                    
                    producto = {
                        'name': nombre.strip(),
                        'url': url_producto.strip(),
                        'image': imagen.strip(),
                        'price': precio_normalizado,
                        'price_text': precio_texto.strip(),
                        'precio_normal': precio_normal,
                        'precio_oferta': precio_oferta,
                        'categoria': categoria_estandar
                    }
                    productos_finales.append(producto)
                else:
                    print(f"Producto {i+1} omitido por datos insuficientes")
                    
            except Exception as e:
                productos_con_error += 1
                print(f"Error procesando producto {i+1}: {e}")
                continue
        
        # Calcular estadísticas de ofertas
        productos_con_oferta = sum(1 for p in productos_finales if p.get('precio_oferta') is not None)
        productos_con_precio_normal = sum(1 for p in productos_finales if p.get('precio_normal') is not None)
        productos_sin_precio = sum(1 for p in productos_finales if p.get('price', 0) == 0)
        
        # Mostrar estadísticas de procesamiento
        print(f"\nEstadísticas de procesamiento:")
        print(f"Productos encontrados: {len(productos_elementos)}")
        print(f"Productos procesados: {productos_procesados}")
        print(f"Productos válidos extraídos: {len(productos_finales)}")
        print(f"Productos con errores: {productos_con_error}")
        print(f"Productos con precio oferta: {productos_con_oferta}")
        print(f"Productos con precio normal: {productos_con_precio_normal}")
        print(f"Productos sin precio válido: {productos_sin_precio}")
        
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

def guardar_resultados_por_categoria_preunic(resultados, tienda_prefix="preunic"):
    """
    Guarda los resultados en archivos JSON separados por categoría para Preunic
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

def scrapear_todas_categorias_preunic(headless=True, max_scrolls=20):
    """
    Scrapea todas las categorías de Preunic y genera archivos JSON separados
    """
    print("=== SCRAPING PREUNIC - TODAS LAS CATEGORÍAS ===")
    
    resultados = {}
    categorias = ['maquillaje', 'skincare']
    
    for categoria in categorias:
        print(f"\n🔄 Scrapeando categoría: {categoria}")
        
        # Scrapear categoría sin guardar JSON automáticamente
        productos_categoria = scrape_preunic_list(
            categoria=categoria,
            headless=headless,
            max_scrolls=max_scrolls,
            scroll_delay=0.8,
            save_json=False  # No guardar automáticamente
        )
        
        # Adaptar estructura de productos para que coincida con el formato estándar
        productos_adaptados = []
        for producto in productos_categoria:
            producto_adaptado = {
                'nombre': producto.get('name', ''),
                'marca': extraer_marca_del_nombre(producto.get('name', '')),
                'precio': float(producto.get('price', 0)),
                'precio_normal': producto.get('precio_normal'),
                'precio_oferta': producto.get('precio_oferta'),
                'categoria': categoria,  # Usar categoría estándar
                'stock': "In stock" if producto.get('available', True) else "Out of stock",
                'url': producto.get('url', ''),
                'imagen': producto.get('image', ''),
                'fuente': 'preunic'
            }
            productos_adaptados.append(producto_adaptado)
        
        resultados[categoria] = {
            'cantidad': len(productos_adaptados),
            'productos': productos_adaptados
        }
        
        print(f"✅ {categoria}: {len(productos_adaptados)} productos extraídos")
    
    from datetime import datetime
    data_completa = {
        'fecha_extraccion': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_productos': sum(cat['cantidad'] for cat in resultados.values()),
        **resultados
    }
    
    # Guardar solo archivos separados por categoría
    archivos_guardados = guardar_resultados_por_categoria_preunic(data_completa, "preunic")
    print(f"\n=== RESUMEN PREUNIC ===")
    print(f"Total archivos generados: {len(archivos_guardados)}")
    for archivo in archivos_guardados:
        print(f"  - {archivo}")
    
    return data_completa

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
        productos_con_oferta = sum(1 for p in productos if p.get('precio_oferta') is not None)
        productos_con_precio_normal = sum(1 for p in productos if p.get('precio_normal') is not None)
        
        print(f"Productos con precio válido: {len(precios)}")
        print(f"Productos con imagen: {productos_con_imagen}")
        print(f"Productos con precio oferta: {productos_con_oferta}")
        print(f"Productos con precio normal: {productos_con_precio_normal}")
        if precios:
            print(f"Precio promedio: ${sum(precios)//len(precios):,}")
            print(f"Precio mínimo: ${min(precios):,}")
            print(f"Precio máximo: ${max(precios):,}")
    
    return productos

if __name__ == "__main__":
    print("=== SCRAPER PREUNIC - ARCHIVOS SEPARADOS POR CATEGORÍA ===")
    print("Iniciando scraping de Preunic con archivos separados...")
    
    # Configuración
    headless = True  # Cambiar a False si quieres ver el navegador
    max_scrolls = 20  # Número de scrolls por categoría
    
    try:
        resultado = scrapear_todas_categorias_preunic(
            headless=headless, 
            max_scrolls=max_scrolls
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
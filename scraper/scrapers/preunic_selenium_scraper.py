#!/usr/bin/env python
"""
Scraper final de Preunic usando API de Algolia
Extrae productos de manera eficiente usando la API pública de Algolia
Corrige problemas de URL (usando slug y sku) y precios (solo normal y oferta)
"""
import requests
import json
import time
import os
from typing import List, Dict, Optional
from datetime import datetime

class PreunicAlgoliaScraper:
    """Scraper para Preunic usando API de Algolia"""
    
    def __init__(self):
        # Configuración de la API de Algolia
        self.application_id = "7GDQZIKE3Q"
        self.api_key = "dcb263ac3f5bb5b523aad2f8c6029f7f"
        self.index_name = "Ecommerce-Products_production"
        self.endpoint = f"https://{self.application_id}-dsn.algolia.net/1/indexes/*/queries"
        
        # Headers para la API
        self.headers = {
            # Headers anti-tracking
            "DNT": "1",  # Do Not Track
            "Sec-GPC": "1",  # Global Privacy Control
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "Content-Type": "application/json",
            "X-Algolia-Application-Id": self.application_id,
            "X-Algolia-API-Key": self.api_key
        }
        
        # Configuración de paginación
        self.hits_per_page = 24  # Productos por página
        self.max_pages = 5  # Máximo 5 páginas por categoría
    
    def search_products(self, categoria: str, page: int = 0) -> Optional[Dict]:
        """
        Busca productos en la API de Algolia
    
    Args:
            categoria: Categoría a buscar ('skincare' o 'maquillaje')
            page: Número de página (0-based)
    
    Returns:
            Respuesta de la API o None si hay error
        """
        try:
            # Mapear categorías a facetFilters correctos
            facet_mapping = {
                'maquillaje': 'categories.lvl0:maquillaje',
                'skincare': 'categories.lvl0:cuidado del rostro'
            }
            
            facet_filter = facet_mapping.get(categoria)
            if not facet_filter:
                print(f"Categoría no válida: {categoria}")
                return None
            
            # Construir payload de la API
            payload = {
                "requests": [
                    {
                        "indexName": self.index_name,
                        "params": f"query=&hitsPerPage={self.hits_per_page}&page={page}&facetFilters=%5B%22{facet_filter}%22%5D&attributesToRetrieve=%5B%22*%22%5D&attributesToHighlight=%5B%5D"
                    }
                ]
            }
            
            print(f"🔍 Buscando {categoria} - Página {page + 1}")
            
            # Hacer request a la API
            response = requests.post(
                self.endpoint,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                print(f"Error en API: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error buscando productos: {e}")
            return None
    
    def extract_product_data(self, product: Dict, categoria: str) -> Optional[Dict]:
        """
        Extrae y normaliza datos de un producto
        
        Args:
            product: Producto raw de la API
            categoria: Categoría del producto
            
        Returns:
            Producto normalizado o None si no es válido
        """
        try:
            # Extraer datos básicos
            nombre = product.get('name', '')
            precio = product.get('price', 0)
            
            # CORRECCIÓN: Solo usar precio normal y oferta (sin card_price/sbpay)
            precio_normal = precio  # Precio base
            precio_oferta = product.get('offer_price')  # Precio de oferta
            
            # Determinar precio final (prioridad: oferta > normal)
            precio_final = precio_oferta if precio_oferta else precio_normal
            
            # CORRECCIÓN: Construir URL usando slug y sku
            slug = product.get('slug', '')
            sku = product.get('sku', '')
            url = f"https://preunic.cl/products/{slug}?sku={sku}" if slug and sku else ""
            
            # Extraer imagen
            imagen = product.get('image', '')
            
            # Extraer marca
            marca = product.get('brand', 'preunic')
            
            # Validar datos mínimos
            if not nombre or not precio_final:
                return None
            
            return {
                'nombre': nombre,
                'marca': marca,
                'precio': precio_final,  # Precio final (oferta o normal)
                'precio_normal': precio_normal,
                'precio_oferta': precio_oferta,
                'categoria': categoria,
                'stock': 'In stock',
                'url': url,  # URL construida con slug y sku
                'imagen': imagen,
                'fuente': 'preunic'
            }
            
        except Exception as e:
            print(f"Error procesando producto: {e}")
            return None
    
    def scrape_categoria(self, categoria: str) -> List[Dict]:
        """
        Scrapea una categoría completa (5 páginas)
        
        Args:
            categoria: Categoría a scrapear
            
        Returns:
            Lista de productos extraídos
        """
        print(f"\nIniciando scraping de categoría: {categoria}")
        
        todos_productos = []
        nombres_visitados = set()
        
        for page in range(self.max_pages):
            print(f"\n📄 Procesando página {page + 1}/{self.max_pages}")
            
            # Buscar productos en la página actual
            response_data = self.search_products(categoria, page)
            
            if not response_data:
                print(f"No se pudo obtener datos de la página {page + 1}")
                break
                
            # Extraer productos de la respuesta
            results = response_data.get('results', [])
            if not results:
                print(f"No hay resultados en la página {page + 1}")
                break
                
            # Procesar productos de esta página
            productos_pagina = results[0].get('hits', [])
            productos_nuevos = 0
            
            for product in productos_pagina:
                # Verificar si ya procesamos este producto por nombre
                product_name = product.get('name', '')
                if product_name in nombres_visitados:
                    continue
                
                # Extraer y normalizar datos del producto
                producto_normalizado = self.extract_product_data(product, categoria)
                
                if producto_normalizado:
                    todos_productos.append(producto_normalizado)
                    nombres_visitados.add(product_name)
                    productos_nuevos += 1
            
            print(f"Página {page + 1}: {len(productos_pagina)} productos encontrados, {productos_nuevos} nuevos")
            
            # Si no hay productos nuevos, terminar
            if productos_nuevos == 0:
                print(f"Sin productos nuevos en página {page + 1}, finalizando")
                break
            
            # Pausa entre requests para ser respetuoso con la API
            if page < self.max_pages - 1:
                time.sleep(1)
        
        print(f"Categoría {categoria}: {len(todos_productos)} productos únicos extraídos")
        return todos_productos
    
    def scrape_all_categories(self) -> Dict[str, List[Dict]]:
        """
        Scrapea todas las categorías
        
        Returns:
            Diccionario con productos por categoría
        """
        print("=== SCRAPER PREUNIC - API ALGOLIA (FINAL CORREGIDO) ===")
        print("Extrayendo productos usando API pública de Algolia")
        print("CORRECCIONES:")
        print("- URLs construidas usando campo 'slug'")
        print("- Precios: solo normal y oferta (sin sbpay/card_price)")
        
        categorias = ['maquillaje', 'skincare']
        resultados = {}
        
        for categoria in categorias:
            productos = self.scrape_categoria(categoria)
            resultados[categoria] = productos
        
        return resultados
    
    def save_results(self, productos_por_categoria: Dict[str, List[Dict]]) -> List[str]:
        """
        Guarda los resultados en archivos JSON separados por categoría
        
        Args:
            productos_por_categoria: Productos organizados por categoría
            
        Returns:
            Lista de archivos guardados
        """
        archivos_guardados = []
        
        # Crear directorio data/raw si no existe
        raw_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "raw")
        os.makedirs(raw_dir, exist_ok=True)
        
        for categoria, productos in productos_por_categoria.items():
            # Crear estructura de datos para cada categoría
            datos = {
                "fecha_extraccion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "tienda": "PREUNIC",
                "categoria": categoria,
                "total_productos": len(productos),
                "productos": productos
            }
            
            # Generar nombre de archivo
            filename = f"preunic_{categoria}.json"
            filepath = os.path.join(raw_dir, filename)
            
            # Guardar archivo
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(datos, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Archivo guardado: {filepath}")
            archivos_guardados.append(filepath)
        
        return archivos_guardados

    def print_summary(self, productos_por_categoria: Dict[str, List[Dict]]):
        """Imprime resumen de la extracción"""
        print("\n" + "="*60)
        print("RESUMEN DE EXTRACCIÓN PREUNIC - API ALGOLIA (FINAL CORREGIDO)")
        print("="*60)
        
        total_productos = 0
        for categoria, productos in productos_por_categoria.items():
            print(f"📦 {categoria.upper()}: {len(productos)} productos")
            total_productos += len(productos)
        
        print(f"\nTOTAL: {total_productos} productos extraídos")
        print("="*60)


def main():
    """Función principal"""
    try:
        # Crear instancia del scraper
        scraper = PreunicAlgoliaScraper()
        
        # Scrapear todas las categorías
        resultados = scraper.scrape_all_categories()
        
        # Guardar resultados
        archivos = scraper.save_results(resultados)
        
        # Mostrar resumen
        scraper.print_summary(resultados)
        
        print(f"\nSCRAPING COMPLETADO EXITOSAMENTE")
        print(f"Archivos generados:")
        for archivo in archivos:
            print(f"   - {archivo}")
        
    except Exception as e:
        print(f"Error durante el scraping: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


def scrape_all_categories(headless=True, **kwargs):
    """
    Función independiente para ser llamada por el ETL
    
    Args:
        headless: Modo headless para el navegador
        **kwargs: Argumentos adicionales (ignorados para Preunic)
        
    Returns:
        Dict con resultados de scraping
    """
    try:
        # Crear instancia del scraper
        scraper = PreunicAlgoliaScraper()
        
        # Scrapear todas las categorías
        resultados = scraper.scrape_all_categories()
        
        # Guardar resultados
        archivos = scraper.save_results(resultados)
        
        return {
            "status": "success",
            "archivos_generados": archivos,
            "resultados": resultados,
            "total_productos": sum(len(productos) for productos in resultados.values())
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

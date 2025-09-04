"""
Gestor de IDs persistentes para productos de CotizaBelleza
Maneja la creación, recuperación y actualización de productos con IDs persistentes
"""

import hashlib
import uuid
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from django.db import transaction
from django.utils import timezone

from core.models import (
    ProductoPersistente, 
    PrecioHistorico, 
    EstadisticaProducto
)
from core.patterns.product_subject import ProductoSubject


class PersistentIdManager:
    """
    Clase principal para manejar IDs persistentes de productos
    """
    
    def __init__(self):
        self.productos_cache = {}  # Cache para evitar consultas repetidas
        self.nuevos_productos = []  # Lista de productos nuevos creados
        self.productos_actualizados = []  # Lista de productos actualizados
    
    @staticmethod
    def normalizar_nombre(nombre: str) -> str:
        """
        Normaliza nombre del producto para comparación consistente
        """
        if not nombre:
            return ""
        
        # Convertir a minúsculas
        nombre_limpio = nombre.lower()
        
        # Eliminar caracteres especiales pero mantener espacios
        nombre_limpio = re.sub(r'[^\w\s]', ' ', nombre_limpio)
        
        # Eliminar espacios extras
        nombre_limpio = ' '.join(nombre_limpio.split())
        
        # Eliminar palabras comunes que pueden variar
        palabras_ignorar = ['ml', 'gr', 'und', 'unidades', 'pack', 'x']
        palabras = nombre_limpio.split()
        palabras_filtradas = [p for p in palabras if p not in palabras_ignorar]
        
        # Eliminar variantes de color al final (después del guión)
        nombre_sin_color = ' '.join(palabras_filtradas)
        if ' - ' in nombre_sin_color:
            nombre_sin_color = nombre_sin_color.split(' - ')[0]
        
        return nombre_sin_color
    
    @staticmethod
    def normalizar_marca(marca: str) -> str:
        """
        Normaliza marca para comparación consistente
        """
        if not marca:
            return "sin_marca"
        
        marca_limpia = marca.lower().strip()
        
        # Mapeo de marcas comunes con variaciones
        mapeo_marcas = {
            'loreal': 'l\'oreal',
            'l oreal': 'l\'oreal',
            'maybelline new york': 'maybelline',
            'maybelline ny': 'maybelline',
            'covergirl': 'cover girl',
            'wet n wild': 'wet n\' wild',
        }
        
        return mapeo_marcas.get(marca_limpia, marca_limpia)
    
    @staticmethod
    def normalizar_categoria(categoria: str) -> str:
        """
        Normaliza categoría para comparación consistente
        """
        if not categoria:
            return "sin_categoria"
        
        categoria_limpia = categoria.lower().strip()
        
        # Mapeo de categorías
        mapeo_categorias = {
            'maquillaje': 'maquillaje',
            'makeup': 'maquillaje',
            'skincare': 'skincare',
            'cuidado_piel': 'skincare',
            'cuidado de la piel': 'skincare',
            'cuidado del rostro': 'skincare',
            'facial': 'skincare',
            'perfumes': 'fragancias',
            'fragancias': 'fragancias',
        }
        
        return mapeo_categorias.get(categoria_limpia, categoria_limpia)
    
    @staticmethod
    def generar_hash_unico(nombre_normalizado: str, marca: str, categoria: str) -> str:
        """
        Genera hash único para identificar productos duplicados
        """
        contenido = f"{nombre_normalizado}|{marca}|{categoria}"
        return hashlib.sha256(contenido.encode('utf-8')).hexdigest()
    
    @staticmethod
    def generar_internal_id() -> str:
        """
        Genera un internal_id único con prefijo cb_
        """
        return f"cb_{uuid.uuid4().hex[:8]}"
    
    def buscar_o_crear_producto(self, producto_data: Dict) -> Tuple[ProductoPersistente, bool]:
        """
        Busca un producto existente o crea uno nuevo basado en datos normalizados
        
        Args:
            producto_data: Dict con datos del producto {nombre, marca, categoria, ...}
            
        Returns:
            Tuple[ProductoPersistente, bool]: (producto, es_nuevo)
        """
        
        # Normalizar datos
        nombre_normalizado = self.normalizar_nombre(producto_data.get('nombre', ''))
        marca_normalizada = self.normalizar_marca(producto_data.get('marca', ''))
        categoria_normalizada = self.normalizar_categoria(producto_data.get('categoria', ''))
        
        # Generar hash único
        hash_unico = self.generar_hash_unico(nombre_normalizado, marca_normalizada, categoria_normalizada)
        
        # Verificar cache primero
        if hash_unico in self.productos_cache:
            producto = self.productos_cache[hash_unico]
            producto.actualizar_aparicion()
            self.productos_actualizados.append(producto)
            return producto, False
        
        # Buscar en base de datos por hash exacto
        try:
            producto = ProductoPersistente.objects.get(hash_unico=hash_unico)
            self.productos_cache[hash_unico] = producto
            producto.actualizar_aparicion()
            self.productos_actualizados.append(producto)
            return producto, False
            
        except ProductoPersistente.DoesNotExist:
            # Buscar por similitud antes de crear nuevo producto
            producto_similar = self.buscar_producto_similar(nombre_normalizado, marca_normalizada, categoria_normalizada)
            
            if producto_similar:
                # Usar el producto similar encontrado
                self.productos_cache[hash_unico] = producto_similar
                producto_similar.actualizar_aparicion()
                self.productos_actualizados.append(producto_similar)
                return producto_similar, False
            
            # Crear nuevo producto si no se encontró similar
            producto = self.crear_nuevo_producto(
                nombre_normalizado=nombre_normalizado,
                marca_normalizada=marca_normalizada,
                categoria_normalizada=categoria_normalizada,
                hash_unico=hash_unico,
                producto_data=producto_data
            )
            
            self.productos_cache[hash_unico] = producto
            self.nuevos_productos.append(producto)
            return producto, True
    
    def buscar_producto_similar(self, nombre_normalizado: str, marca_normalizada: str, categoria_normalizada: str) -> Optional[ProductoPersistente]:
        """
        Busca un producto similar basado en similitud de nombre, marca y categoría
        
        Args:
            nombre_normalizado: Nombre normalizado del producto
            marca_normalizada: Marca normalizada
            categoria_normalizada: Categoría normalizada
            
        Returns:
            ProductoPersistente si se encuentra uno similar, None en caso contrario
        """
        from difflib import SequenceMatcher
        
        # Buscar productos con la misma marca y categoría
        productos_candidatos = ProductoPersistente.objects.filter(
            marca=marca_normalizada,
            categoria=categoria_normalizada
        )
        
        mejor_similitud = 0.8  # Umbral mínimo de similitud
        mejor_producto = None
        productos_similares = []
        
        for producto in productos_candidatos:
            # Calcular similitud entre nombres normalizados
            similitud = SequenceMatcher(None, nombre_normalizado, producto.nombre_normalizado).ratio()
            
            # Si la similitud es alta, considerar este producto
            if similitud > mejor_similitud:
                productos_similares.append((producto, similitud))
        
        if not productos_similares:
            return None
        
        # Ordenar por similitud (mayor primero)
        productos_similares.sort(key=lambda x: x[1], reverse=True)
        
        # Priorizar productos con reseñas
        productos_con_resenas = [(p, s) for p, s in productos_similares if p.resenas.count() > 0]
        
        if productos_con_resenas:
            # Si hay productos con reseñas, usar el más similar
            return productos_con_resenas[0][0]
        else:
            # Si no hay productos con reseñas, usar el más similar
            return productos_similares[0][0]
    
    def crear_nuevo_producto(self, nombre_normalizado: str, marca_normalizada: str, 
                           categoria_normalizada: str, hash_unico: str, 
                           producto_data: Dict) -> ProductoSubject:
        """
        Crea un nuevo producto persistente como ProductoSubject
        """
        
        producto = ProductoSubject.objects.create(
            internal_id=self.generar_internal_id(),
            nombre_normalizado=nombre_normalizado,
            marca=marca_normalizada,
            categoria=categoria_normalizada,
            hash_unico=hash_unico,
            nombre_original=producto_data.get('nombre', ''),
            descripcion=producto_data.get('descripcion', ''),
            imagen_url=producto_data.get('imagen', ''),
            veces_encontrado=1
        )
        
        # Crear estadísticas iniciales
        EstadisticaProducto.objects.create(producto=producto)
        
        return producto
    
    def agregar_precio_historico(self, producto: ProductoSubject, 
                               precio_data: Dict, fecha_scraping: datetime) -> PrecioHistorico:
        """
        Agrega un nuevo precio histórico para un producto y notifica a observadores
        """
        
        # Extraer información de precio
        precio = precio_data.get('precio', 0)
        precio_original = precio_data.get('precio_normal') or precio_data.get('precio_original')
        tiene_descuento = bool(precio_original and precio_original > precio)
        tienda = precio_data.get('fuente', 'desconocida')
        url_producto = precio_data.get('url', '')
        
        # Obtener precio anterior para comparación
        precio_anterior = producto.get_current_price(tienda)
        
        # Verificar si ya existe un precio para este producto, tienda y fecha
        precio_existente = PrecioHistorico.objects.filter(
            producto=producto,
            tienda=tienda,
            fecha_scraping__date=fecha_scraping.date()
        ).first()
        
        if precio_existente:
            # Actualizar precio existente
            precio_existente.precio = precio
            precio_existente.precio_original = precio_original
            precio_existente.tiene_descuento = tiene_descuento
            precio_existente.stock = precio_data.get('stock', 'in stock').lower() == 'in stock'
            precio_existente.disponible = True
            precio_existente.url_producto = url_producto
            precio_existente.imagen_url = precio_data.get('imagen', '')
            precio_existente.save()
            
            # Notificar cambio de precio si es diferente
            if precio_anterior is not None and abs(precio_anterior - precio) > 0.01:
                producto.notify_price_change(precio_anterior, precio, tienda, url_producto)
            
            return precio_existente
        else:
            # Crear nuevo precio usando el método del ProductoSubject
            precio_historico = producto.update_price_and_notify(
                new_price=precio,
                store=tienda,
                url=url_producto,
                precio_original=precio_original,
                tiene_descuento=tiene_descuento,
                stock=precio_data.get('stock', 'in stock').lower() == 'in stock',
                disponible=True,
                imagen_url=precio_data.get('imagen', ''),
                fecha_scraping=fecha_scraping,
                fuente_scraping=f"etl_{fecha_scraping.strftime('%Y_%m_%d')}"
            )
            return precio_historico
    
    def procesar_productos_json(self, productos_json: List[Dict], 
                              fecha_scraping: Optional[datetime] = None) -> Dict:
        """
        Procesa una lista de productos del JSON unificado y asigna IDs persistentes
        PRESERVA productos existentes con reseñas/alertas
        
        Args:
            productos_json: Lista de productos del JSON
            fecha_scraping: Fecha del scraping (default: ahora)
            
        Returns:
            Dict con estadísticas del procesamiento
        """
        
        if fecha_scraping is None:
            fecha_scraping = timezone.now()
        
        estadisticas = {
            'productos_procesados': 0,
            'productos_nuevos': 0,
            'productos_actualizados': 0,
            'precios_agregados': 0,
            'productos_preservados': 0,
            'errores': []
        }
        
        # Obtener productos que deben preservarse (con reseñas o alertas)
        productos_a_preservar = self.obtener_productos_con_resenas_o_alertas()
        print(f"Productos con reseñas/alertas que se preservarán: {len(productos_a_preservar)}")
        
        # Marcar productos encontrados en este scraping
        productos_encontrados = set()
        
        for producto_data in productos_json:
            try:
                with transaction.atomic():
                    # Buscar o crear producto
                    producto, es_nuevo = self.buscar_o_crear_producto(producto_data)
                    productos_encontrados.add(producto.internal_id)
                    
                    # Procesar precios por tienda
                    tiendas = producto_data.get('tiendas', [])
                    for tienda_data in tiendas:
                        self.agregar_precio_historico(producto, tienda_data, fecha_scraping)
                        estadisticas['precios_agregados'] += 1
                    
                    # Actualizar estadísticas
                    if es_nuevo:
                        estadisticas['productos_nuevos'] += 1
                    else:
                        estadisticas['productos_actualizados'] += 1
                    
                    estadisticas['productos_procesados'] += 1
                    
            except Exception as e:
                error_msg = f"Error procesando producto {producto_data.get('nombre', 'sin_nombre')}: {str(e)}"
                estadisticas['errores'].append(error_msg)
                print(f"Error: {error_msg}")
        
        # Preservar productos con reseñas/alertas que no aparecieron en este scraping
        productos_preservados = self.preservar_productos_con_resenas_alertas(productos_encontrados)
        estadisticas['productos_preservados'] = productos_preservados
        
        # Actualizar estadísticas de productos afectados
        self.actualizar_estadisticas_productos()
        
        return estadisticas
    
    def obtener_productos_con_resenas_o_alertas(self) -> List[ProductoPersistente]:
        """
        Obtiene productos que tienen reseñas o alertas
        """
        from core.models import ResenaProductoPersistente, AlertaPrecioProductoPersistente
        
        # Productos con reseñas
        productos_con_resenas = ProductoPersistente.objects.filter(
            resenas__isnull=False
        ).distinct()
        
        # Productos con alertas
        productos_con_alertas = ProductoPersistente.objects.filter(
            alertas_precio__isnull=False
        ).distinct()
        
        # Combinar y eliminar duplicados
        todos_productos = list(productos_con_resenas) + list(productos_con_alertas)
        productos_unicos = list({p.internal_id: p for p in todos_productos}.values())
        
        return productos_unicos
    
    def buscar_producto_por_datos(self, nombre: str, marca: str, categoria: str) -> Optional[ProductoPersistente]:
        """
        Busca un producto persistente por nombre, marca y categoría
        
        Args:
            nombre: Nombre del producto
            marca: Marca del producto
            categoria: Categoría del producto
            
        Returns:
            ProductoPersistente si se encuentra, None en caso contrario
        """
        try:
            # Normalizar datos
            nombre_normalizado = self.normalizar_nombre(nombre)
            marca_normalizada = self.normalizar_marca(marca)
            categoria_normalizada = self.normalizar_categoria(categoria)
            
            # Mapear categorías del JSON a categorías de la BD
            if categoria_normalizada == "skincare":
                categoria_normalizada = "cuidado_piel"
            
            # Generar hash único
            hash_unico = self.generar_hash_unico(nombre_normalizado, marca_normalizada, categoria_normalizada)
            
            # Buscar por hash único
            producto = ProductoPersistente.objects.filter(hash_unico=hash_unico).first()
            
            if producto:
                return producto
            
            # Si no se encuentra por hash, buscar por similitud
            return self.buscar_producto_similar(nombre_normalizado, marca_normalizada, categoria_normalizada)
            
        except Exception as e:
            print(f"Error buscando producto por datos: {e}")
            return None
    
    def preservar_productos_con_resenas_alertas(self, productos_encontrados: set) -> int:
        """
        Preserva productos con reseñas/alertas que no aparecieron en el scraping actual
        """
        productos_a_preservar = self.obtener_productos_con_resenas_o_alertas()
        productos_preservados = 0
        
        for producto in productos_a_preservar:
            if producto.internal_id not in productos_encontrados:
                # Reactivar producto si estaba desactivado
                if not producto.activo:
                    producto.activo = True
                    producto.ultima_actualizacion = timezone.now()
                    producto.save()
                    productos_preservados += 1
                    print(f"Producto preservado: {producto.internal_id} - {producto.nombre_original}")
        
        return productos_preservados
    
    def actualizar_estadisticas_productos(self):
        """
        Actualiza estadísticas de todos los productos que fueron modificados
        """
        productos_para_actualizar = set()
        productos_para_actualizar.update(self.nuevos_productos)
        productos_para_actualizar.update(self.productos_actualizados)
        
        for producto in productos_para_actualizar:
            try:
                estadistica, created = EstadisticaProducto.objects.get_or_create(
                    producto=producto
                )
                estadistica.actualizar_estadisticas()
            except Exception as e:
                print(f"Error actualizando estadísticas para {producto.internal_id}: {e}")
    
    def generar_json_con_ids_persistentes(self, productos_json: List[Dict]) -> List[Dict]:
        """
        Procesa JSON de productos y retorna versión con IDs persistentes asignados
        
        Args:
            productos_json: Lista de productos del JSON original
            
        Returns:
            Lista de productos con internal_id asignado
        """
        
        productos_con_ids = []
        
        for producto_data in productos_json:
            try:
                # Buscar o crear producto (sin guardar precios históricos)
                producto, es_nuevo = self.buscar_o_crear_producto(producto_data)
                
                # Agregar internal_id al producto
                producto_con_id = producto_data.copy()
                producto_con_id['internal_id'] = producto.internal_id
                producto_con_id['es_nuevo'] = es_nuevo
                
                productos_con_ids.append(producto_con_id)
                
            except Exception as e:
                print(f"Error asignando ID a producto {producto_data.get('nombre', 'sin_nombre')}: {e}")
                # Agregar producto sin internal_id en caso de error
                producto_data['internal_id'] = None
                producto_data['error'] = str(e)
                productos_con_ids.append(producto_data)
        
        return productos_con_ids
    
    def obtener_estadisticas_procesamiento(self) -> Dict:
        """
        Obtiene estadísticas del procesamiento actual
        """
        return {
            'productos_en_cache': len(self.productos_cache),
            'productos_nuevos': len(self.nuevos_productos),
            'productos_actualizados': len(self.productos_actualizados),
            'nuevos_internal_ids': [p.internal_id for p in self.nuevos_productos],
            'productos_actualizados_ids': [p.internal_id for p in self.productos_actualizados]
        }
    
    def limpiar_cache(self):
        """
        Limpia el cache interno
        """
        self.productos_cache.clear()
        self.nuevos_productos.clear()
        self.productos_actualizados.clear()


def procesar_json_unificado_con_ids_persistentes(ruta_json: str, 
                                                fecha_scraping: Optional[datetime] = None) -> Dict:
    """
    Función principal para procesar un archivo JSON unificado y asignar IDs persistentes
    
    Args:
        ruta_json: Ruta al archivo JSON unificado
        fecha_scraping: Fecha del scraping (opcional)
        
    Returns:
        Dict con estadísticas y resultados del procesamiento
    """
    
    import json
    
    # Leer archivo JSON
    try:
        with open(ruta_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extraer lista de productos
        if isinstance(data, dict) and 'productos' in data:
            productos = data['productos']
        elif isinstance(data, list):
            productos = data
        else:
            raise ValueError("Formato de JSON no reconocido")
        
    except Exception as e:
        return {
            'error': f"Error leyendo archivo JSON: {e}",
            'exito': False
        }
    
    # Procesar productos
    manager = PersistentIdManager()
    estadisticas = manager.procesar_productos_json(productos, fecha_scraping)
    estadisticas_procesamiento = manager.obtener_estadisticas_procesamiento()
    
    # Combinar estadísticas
    resultado = {
        'exito': True,
        'archivo_procesado': ruta_json,
        'fecha_procesamiento': fecha_scraping or timezone.now(),
        **estadisticas,
        **estadisticas_procesamiento
    }
    
    return resultado


# Función de ejemplo para uso directo
def ejemplo_uso():
    """
    Ejemplo de cómo usar el sistema de IDs persistentes
    """
    
    # Datos de ejemplo (simulando JSON del scraper)
    productos_ejemplo = [
        {
            "nombre": "Máscara de Pestañas Maybelline Great Lash Waterproof Negro",
            "marca": "MAYBELLINE",
            "categoria": "maquillaje",
            "tiendas": [
                {
                    "fuente": "preunic",
                    "precio": 3679.0,
                    "precio_normal": 4599.0,
                    "stock": "In stock",
                    "url": "https://preunic.cl/producto-123",
                    "imagen": "https://preunic.cl/imagen.jpg"
                }
            ]
        },
        {
            "nombre": "Mascara Maybelline Great Lash WaterProof Black",  # Variación del mismo producto
            "marca": "Maybelline",
            "categoria": "Maquillaje",
            "tiendas": [
                {
                    "fuente": "dbs",
                    "precio": 3890.0,
                    "stock": "In stock",
                    "url": "https://dbs.cl/producto-456"
                }
            ]
        }
    ]
    
    # Procesar productos
    manager = PersistentIdManager()
    estadisticas = manager.procesar_productos_json(productos_ejemplo)
    
    print("Estadísticas del procesamiento:")
    print(f"- Productos procesados: {estadisticas['productos_procesados']}")
    print(f"- Productos nuevos: {estadisticas['productos_nuevos']}")
    print(f"- Productos actualizados: {estadisticas['productos_actualizados']}")
    print(f"- Precios agregados: {estadisticas['precios_agregados']}")
    
    if estadisticas['errores']:
        print("Errores:")
        for error in estadisticas['errores']:
            print(f"  - {error}")
    
    return estadisticas


if __name__ == "__main__":
    ejemplo_uso()

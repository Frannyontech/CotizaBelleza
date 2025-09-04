"""
Procesador del ETL integrado con sistema de IDs persistentes
Extiende el procesador existente para incluir manejo de IDs persistentes
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Agregar el directorio del proyecto al path para imports
sys.path.append(str(Path(__file__).parent.parent))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cotizabelleza.settings')
import django
django.setup()

from core.services.persistent_id_manager import PersistentIdManager
from core.models import ProductoPersistente, PrecioHistorico, EstadisticaProducto


class PersistentETLProcessor:
    """
    Procesador del ETL que integra IDs persistentes
    """
    
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(__file__).parent.parent
        self.data_dir = self.base_dir / 'data'
        self.raw_dir = self.data_dir / 'raw'
        self.processed_dir = self.data_dir / 'processed'
        
        # Asegurar que existen los directorios
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        self.id_manager = PersistentIdManager()
        self.estadisticas = {
            'archivos_procesados': 0,
            'productos_totales': 0,
            'productos_nuevos': 0,
            'productos_actualizados': 0,
            'precios_agregados': 0,
            'errores': []
        }
    
    def procesar_archivo_raw(self, archivo_path: Path) -> List[Dict]:
        """
        Procesa un archivo raw individual y extrae productos
        """
        try:
            with open(archivo_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extraer productos del archivo
            if isinstance(data, dict):
                productos = data.get('productos', [])
                tienda = data.get('tienda', 'desconocida')
                categoria = data.get('categoria', 'desconocida')
            elif isinstance(data, list):
                productos = data
                tienda = 'desconocida'
                categoria = 'desconocida'
            else:
                productos = []
            
            # Normalizar formato de productos para el procesador unificado
            productos_normalizados = []
            for producto in productos:
                producto_normalizado = self.normalizar_producto_raw(producto, tienda, categoria)
                if producto_normalizado:
                    productos_normalizados.append(producto_normalizado)
            
            self.estadisticas['archivos_procesados'] += 1
            print(f"Procesado {archivo_path.name}: {len(productos_normalizados)} productos")
            
            return productos_normalizados
            
        except Exception as e:
            error_msg = f"Error procesando {archivo_path}: {e}"
            self.estadisticas['errores'].append(error_msg)
            print(f"Error: {error_msg}")
            return []
    
    def normalizar_categoria(self, categoria: str) -> str:
        """
        Normaliza categorías para consistencia
        """
        if not categoria:
            return 'desconocida'
        
        categoria_limpia = categoria.lower().strip()
        
        # Mapeo de categorías para consistencia
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
    
    def normalizar_producto_raw(self, producto: Dict, tienda_default: str, categoria_default: str) -> Optional[Dict]:
        """
        Normaliza un producto individual al formato del procesador unificado
        """
        try:
            # Extraer información básica
            nombre = producto.get('nombre') or producto.get('name', '')
            marca = producto.get('marca') or self.extraer_marca_del_nombre(nombre)
            categoria = producto.get('categoria') or categoria_default
            
            # Normalizar categoría
            categoria = self.normalizar_categoria(categoria)
            
            if not nombre:
                return None
            
            # Extraer información de precio
            precio = float(producto.get('precio', 0) or producto.get('price', 0))
            precio_normal = producto.get('precio_normal')
            if precio_normal:
                precio_normal = float(precio_normal)
            
            # Crear estructura unificada
            producto_unificado = {
                'nombre': nombre,
                'marca': marca,
                'categoria': categoria,
                'tiendas': [{
                    'fuente': tienda_default,
                    'precio': precio,
                    'precio_normal': precio_normal,
                    'stock': producto.get('stock', 'In stock'),
                    'url': producto.get('url') or producto.get('url_producto', ''),
                    'imagen': producto.get('imagen') or producto.get('imagen_url', ''),
                    'marca_origen': marca
                }]
            }
            
            return producto_unificado
            
        except Exception as e:
            print(f"Error normalizando producto {producto.get('nombre', 'sin_nombre')}: {e}")
            return None
    
    def extraer_marca_del_nombre(self, nombre: str) -> str:
        """
        Extrae la marca del nombre del producto si no está especificada
        """
        if not nombre:
            return "sin_marca"
        
        # Lista de marcas conocidas
        marcas_conocidas = [
            'MAYBELLINE', 'REVLON', 'L\'OREAL', 'LOREAL', 'COVERGIRL', 'RIMMEL',
            'BOURJOIS', 'MILANI', 'WET N WILD', 'NYX', 'ESSENCE', 'CATRICE',
            'SKIN1004', 'MIXSOON', 'NEUTROGENA', 'TOCOBO', 'NIVEA', 'KIKO',
            'CLINIQUE', 'ESTEE LAUDER', 'LANCOME', 'DIOR', 'CHANEL'
        ]
        
        nombre_upper = nombre.upper()
        for marca in marcas_conocidas:
            if marca in nombre_upper:
                return marca
        
        # Si no encuentra marca conocida, tomar la primera palabra
        primera_palabra = nombre.split()[0] if nombre.split() else "sin_marca"
        return primera_palabra.upper()
    
    def combinar_productos_por_tienda(self, todos_productos: List[Dict]) -> List[Dict]:
        """
        Combina productos que son el mismo pero de diferentes tiendas usando deduplicación avanzada
        """
        # Usar el sistema de deduplicación avanzado
        from core.services.deduplication import deduplicar_productos_avanzado
        
        print("Aplicando deduplicación avanzada por similitud...")
        productos_deduplicados, estadisticas = deduplicar_productos_avanzado(todos_productos, umbral_similitud=0.75)
        
        print(f"Productos después de deduplicación: {len(productos_deduplicados)} (original: {len(todos_productos)})")
        print(f"Duplicados eliminados: {estadisticas['duplicados_eliminados']}")
        
        return productos_deduplicados
    
    def procesar_todos_archivos_raw(self) -> List[Dict]:
        """
        Procesa todos los archivos raw y combina en una lista unificada
        """
        todos_productos = []
        
        # Buscar todos los archivos JSON en el directorio raw
        archivos_raw = list(self.raw_dir.glob('*.json'))
        
        if not archivos_raw:
            print("No se encontraron archivos raw para procesar")
            return []
        
        print(f"Procesando {len(archivos_raw)} archivos raw...")
        
        for archivo in archivos_raw:
            productos = self.procesar_archivo_raw(archivo)
            todos_productos.extend(productos)
        
        # Combinar productos por tienda
        productos_combinados = self.combinar_productos_por_tienda(todos_productos)
        
        print(f"Total productos únicos después de combinación: {len(productos_combinados)}")
        return productos_combinados
    
    def procesar_con_ids_persistentes(self, fecha_scraping: Optional[datetime] = None) -> Dict:
        """
        Proceso principal: procesa archivos raw y asigna IDs persistentes
        """
        if fecha_scraping is None:
            fecha_scraping = datetime.now()
        
        print("Iniciando procesamiento con IDs persistentes...")
        
        # Paso 1: Procesar archivos raw
        productos_unificados = self.procesar_todos_archivos_raw()
        self.estadisticas['productos_totales'] = len(productos_unificados)
        
        if not productos_unificados:
            return {
                'exito': False,
                'error': 'No se encontraron productos para procesar',
                'estadisticas': self.estadisticas
            }
        
        # Paso 2: Asignar IDs persistentes y guardar en BD
        print("Asignando IDs persistentes y guardando en base de datos...")
        estadisticas_bd = self.id_manager.procesar_productos_json(productos_unificados, fecha_scraping)
        
        # Combinar estadísticas
        self.estadisticas.update({
            'productos_nuevos': estadisticas_bd['productos_nuevos'],
            'productos_actualizados': estadisticas_bd['productos_actualizados'],
            'precios_agregados': estadisticas_bd['precios_agregados']
        })
        self.estadisticas['errores'].extend(estadisticas_bd['errores'])
        
        # Paso 3: Generar JSON con IDs persistentes
        productos_con_ids = self.id_manager.generar_json_con_ids_persistentes(productos_unificados)
        
        # Asegurar que todos los productos tengan product_id basado en internal_id
        for producto in productos_con_ids:
            if producto.get('internal_id') and not producto.get('product_id'):
                # Asignar internal_id como product_id
                producto['product_id'] = producto['internal_id']
            elif not producto.get('product_id'):
                # Si no tiene internal_id ni product_id, buscar el producto persistente
                nombre = producto.get('nombre', '')
                marca = producto.get('marca', '')
                categoria = producto.get('categoria', '')
                
                # Buscar el producto persistente correspondiente
                producto_persistente = self.id_manager.buscar_producto_por_datos(nombre, marca, categoria)
                if producto_persistente:
                    producto['product_id'] = producto_persistente.internal_id
                    producto['internal_id'] = producto_persistente.internal_id
        
        # Paso 4: Guardar JSON procesado
        archivo_salida = self.processed_dir / 'unified_products_with_persistent_ids.json'
        self.guardar_json_procesado(productos_con_ids, archivo_salida, fecha_scraping)
        
        # Paso 5: Mantener compatibilidad con JSON original
        archivo_original = self.processed_dir / 'unified_products.json'
        self.guardar_json_compatible(productos_con_ids, archivo_original)
        
        resultado = {
            'exito': True,
            'fecha_procesamiento': fecha_scraping,
            'archivo_con_ids': str(archivo_salida),
            'archivo_compatible': str(archivo_original),
            'estadisticas': self.estadisticas,
            'estadisticas_bd': estadisticas_bd
        }
        
        self.imprimir_resumen(resultado)
        return resultado
    
    def guardar_json_procesado(self, productos: List[Dict], archivo_salida: Path, fecha_scraping: datetime):
        """
        Guarda JSON con IDs persistentes y metadatos completos
        """
        data_completa = {
            'metadata': {
                'fecha_procesamiento': fecha_scraping.isoformat(),
                'version': '2.0_persistent_ids',
                'total_productos': len(productos),
                'estadisticas': self.estadisticas
            },
            'productos': productos
        }
        
        with open(archivo_salida, 'w', encoding='utf-8') as f:
            json.dump(data_completa, f, ensure_ascii=False, indent=2)
        
        print(f"Guardado JSON con IDs persistentes: {archivo_salida}")
    
    def guardar_json_compatible(self, productos: List[Dict], archivo_salida: Path):
        """
        Guarda JSON en formato compatible con sistema existente
        Incluye TODOS los productos activos de la BD, no solo los del scraping actual
        """
        # Obtener TODOS los productos activos de la BD, incluyendo los que no aparecieron en este scraping
        productos_bd_activos = self.obtener_todos_productos_activos()
        
        # Crear estructura compatible
        productos_compatibles = []
        
        # Agregar productos del scraping actual
        for producto in productos:
            producto_compatible = {k: v for k, v in producto.items() 
                                 if k not in ['es_nuevo', 'error']}
            # Cambiar internal_id por product_id para compatibilidad
            if 'internal_id' in producto_compatible:
                producto_compatible['product_id'] = producto_compatible.pop('internal_id')
            productos_compatibles.append(producto_compatible)
        
        # Agregar productos existentes que no aparecieron en este scraping pero tienen reseñas/alertas
        productos_existentes = self.obtener_productos_con_resenas_o_alertas()
        for producto_bd in productos_existentes:
            # Verificar si ya está en la lista
            ya_incluido = any(p.get('product_id') == producto_bd.internal_id for p in productos_compatibles)
            
            if not ya_incluido:
                # Agregar producto existente con datos de la BD
                producto_compatible = self.convertir_producto_bd_a_json(producto_bd)
                productos_compatibles.append(producto_compatible)
        
        with open(archivo_salida, 'w', encoding='utf-8') as f:
            json.dump(productos_compatibles, f, ensure_ascii=False, indent=2)
        
        print(f"Guardado JSON compatible: {archivo_salida}")
        print(f"  - Productos del scraping: {len(productos)}")
        print(f"  - Productos existentes preservados: {len(productos_compatibles) - len(productos)}")
        print(f"  - Total productos en JSON: {len(productos_compatibles)}")
    
    def obtener_todos_productos_activos(self) -> List[ProductoPersistente]:
        """
        Obtiene todos los productos activos de la BD
        """
        return list(ProductoPersistente.objects.filter(activo=True))
    
    def obtener_productos_con_resenas_o_alertas(self) -> List[ProductoPersistente]:
        """
        Obtiene productos que tienen reseñas o alertas, aunque no aparezcan en el scraping actual
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
        
        print(f"Productos con reseñas encontrados: {productos_con_resenas.count()}")
        print(f"Productos con alertas encontrados: {productos_con_alertas.count()}")
        print(f"Total productos a preservar: {len(productos_unicos)}")
        
        return productos_unicos
    
    def convertir_producto_bd_a_json(self, producto_bd: ProductoPersistente) -> Dict:
        """
        Convierte un producto de la BD al formato JSON compatible
        """
        # Obtener el precio más reciente
        precio_reciente = PrecioHistorico.objects.filter(
            producto=producto_bd
        ).order_by('-fecha_scraping').first()
        
        producto_json = {
            'product_id': producto_bd.internal_id,
            'nombre': producto_bd.nombre_original,
            'marca': producto_bd.marca,
            'categoria': producto_bd.categoria,
            'tiendas': []
        }
        
        if precio_reciente:
            tienda_data = {
                'fuente': precio_reciente.tienda,
                'precio': float(precio_reciente.precio),
                'stock': 'In stock' if precio_reciente.stock else 'Out of stock',
                'url': precio_reciente.url_producto or '',
                'imagen': precio_reciente.imagen_url or '',
                'marca_origen': producto_bd.marca
            }
            
            if precio_reciente.precio_original:
                tienda_data['precio_normal'] = float(precio_reciente.precio_original)
            
            producto_json['tiendas'].append(tienda_data)
        
        return producto_json
    
    def imprimir_resumen(self, resultado: Dict):
        """
        Imprime resumen del procesamiento
        """
        print("\n" + "="*60)
        print("RESUMEN DEL PROCESAMIENTO CON IDS PERSISTENTES")
        print("="*60)
        
        stats = resultado['estadisticas']
        print(f"Archivos raw procesados: {stats['archivos_procesados']}")
        print(f"Productos totales: {stats['productos_totales']}")
        print(f"Productos nuevos: {stats['productos_nuevos']}")
        print(f"Productos actualizados: {stats['productos_actualizados']}")
        print(f"Precios históricos agregados: {stats['precios_agregados']}")
        
        if stats['errores']:
            print(f"\nErrores encontrados ({len(stats['errores'])}):")
            for error in stats['errores'][:5]:  # Mostrar solo los primeros 5
                print(f"  - {error}")
            if len(stats['errores']) > 5:
                print(f"  ... y {len(stats['errores']) - 5} errores más")
        
        print(f"\nArchivo con IDs: {resultado['archivo_con_ids']}")
        print(f"Archivo compatible: {resultado['archivo_compatible']}")
        print("="*60)


def procesar_etl_con_ids_persistentes(base_dir: Optional[str] = None) -> Dict:
    """
    Función principal para ejecutar el procesamiento con IDs persistentes
    """
    try:
        base_path = Path(base_dir) if base_dir else Path(__file__).parent.parent
        processor = PersistentETLProcessor(base_path)
        resultado = processor.procesar_con_ids_persistentes()
        return resultado
        
    except Exception as e:
        return {
            'exito': False,
            'error': f"Error en procesamiento: {e}",
            'estadisticas': {}
        }


if __name__ == "__main__":
    # Ejecutar procesamiento
    import argparse
    
    parser = argparse.ArgumentParser(description='Procesador ETL con IDs persistentes')
    parser.add_argument('--base-dir', help='Directorio base del proyecto')
    args = parser.parse_args()
    
    resultado = procesar_etl_con_ids_persistentes(args.base_dir)
    
    if resultado['exito']:
        print("\nProcesamiento completado exitosamente")
        sys.exit(0)
    else:
        print(f"\nError en procesamiento: {resultado['error']}")
        sys.exit(1)

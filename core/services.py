"""
Servicios - Capa de lógica de dominio en el patrón MVC
Integra el pipeline ETL con la lógica de negocio
"""
import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from django.db import transaction
from decimal import Decimal

from django.contrib.auth.models import User
from .models import Categoria, Tienda, Producto, PrecioProducto, AlertaPrecio, Resena
from .serializers import ResenaSerializer


class ETLService:
    """Servicio para manejar el pipeline ETL completo"""
    
    @staticmethod
    def run_scraper(tienda: str, categoria: str = None) -> Dict:
        """Ejecuta el scraper para una tienda específica"""
        try:
            scraper_path = Path(settings.BASE_DIR) / "scraper" / "scrapers"
            
            scraper_files = {
                'dbs': 'dbs_selenium_scraper.py',
                'maicao': 'maicao_selenium_scraper.py',
                'preunic': 'preunic_selenium_scraper.py'
            }
            
            scraper_file = scraper_files.get(tienda.lower())
            if not scraper_file:
                raise ValueError(f"Scraper no encontrado para tienda: {tienda}")
            
            scraper_full_path = scraper_path / scraper_file
            
            # Ejecutar scraper
            cmd = ["python", str(scraper_full_path)]
            if categoria:
                cmd.extend(["--categoria", categoria])
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                cwd=str(scraper_path)
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': f'Scraper {tienda} ejecutado exitosamente',
                    'output': result.stdout
                }
            else:
                return {
                    'success': False,
                    'message': f'Error ejecutando scraper {tienda}',
                    'error': result.stderr
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error ejecutando scraper: {str(e)}'
            }
    
    @staticmethod
    def run_processor(min_strong: int = 90, min_prob: int = 85, output_file: str = None) -> Dict:
        """Ejecuta el procesador de normalización de datos"""
        try:
            processor_path = Path(settings.BASE_DIR) / "processor"
            
            cmd = ["python", "-m", "processor.normalize"]
            cmd.extend(["--min-strong", str(min_strong)])
            cmd.extend(["--min-prob", str(min_prob)])
            
            if output_file:
                cmd.extend(["--out", output_file])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(settings.BASE_DIR)
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': 'Procesador ejecutado exitosamente',
                    'output': result.stdout
                }
            else:
                return {
                    'success': False,
                    'message': 'Error ejecutando procesador',
                    'error': result.stderr
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error ejecutando procesador: {str(e)}'
            }
    
    @staticmethod
    def load_data_to_db(file_path: str, tienda: str, clear_data: bool = False) -> Dict:
        """Carga datos procesados a la base de datos usando el comando Django"""
        try:
            from django.core.management import call_command
            from io import StringIO
            
            out = StringIO()
            
            # Preparar argumentos para el comando
            cmd_args = [
                '--file', file_path,
                '--tienda', tienda
            ]
            
            if clear_data:
                cmd_args.append('--clear')
            
            # Ejecutar comando Django
            call_command('load_scraper_data', *cmd_args, stdout=out)
            
            return {
                'success': True,
                'message': f'Datos cargados exitosamente desde {file_path}',
                'output': out.getvalue()
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error cargando datos: {str(e)}'
            }
    
    @staticmethod
    def run_full_etl_pipeline(tiendas: List[str] = None, categorias: List[str] = None) -> Dict:
        """Ejecuta el pipeline ETL completo: Extract -> Transform -> Load"""
        if not tiendas:
            tiendas = ['dbs', 'maicao', 'preunic']
        
        if not categorias:
            categorias = ['maquillaje', 'skincare']
        
        results = {
            'extract': {},
            'transform': {},
            'load': {},
            'success': True,
            'errors': []
        }
        
        try:
            # EXTRACT: Ejecutar scrapers
            for tienda in tiendas:
                for categoria in categorias:
                    scraper_result = ETLService.run_scraper(tienda, categoria)
                    results['extract'][f'{tienda}_{categoria}'] = scraper_result
                    
                    if not scraper_result['success']:
                        results['success'] = False
                        results['errors'].append(f"Scraper {tienda}/{categoria}: {scraper_result['message']}")
            
            # TRANSFORM: Ejecutar procesador
            if results['success']:
                processor_result = ETLService.run_processor()
                results['transform'] = processor_result
                
                if not processor_result['success']:
                    results['success'] = False
                    results['errors'].append(f"Procesador: {processor_result['message']}")
            
            # LOAD: Cargar datos a BD
            if results['success']:
                unified_file = Path(settings.BASE_DIR) / "data" / "processed" / "unified_products.json"
                
                # También cargar datos raw a la BD para mantener compatibilidad
                for tienda in tiendas:
                    data_path = Path(settings.BASE_DIR) / "scraper" / "data" / f"{tienda}_productos.json"
                    if data_path.exists():
                        load_result = ETLService.load_data_to_db(str(data_path), tienda.upper())
                        results['load'][tienda] = load_result
                        
                        if not load_result['success']:
                            results['success'] = False
                            results['errors'].append(f"Carga {tienda}: {load_result['message']}")
            
            return results
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error en pipeline ETL: {str(e)}',
                'results': results
            }


class DataIntegrationService:
    """Servicio para integrar datos del ETL con la aplicación MVC"""
    
    @staticmethod
    def sync_unified_data_with_db() -> Dict:
        """Sincroniza datos unificados con la base de datos Django"""
        try:
            unified_data = UnifiedDataController.load_unified_products()
            productos = unified_data.get("productos", [])
            
            stats = {
                'productos_procesados': 0,
                'productos_creados': 0,
                'precios_creados': 0,
                'categorias_creadas': 0,
                'tiendas_creadas': 0
            }
            
            with transaction.atomic():
                # Procesar cada producto unificado
                for producto_data in productos:
                    stats['productos_procesados'] += 1
                    
                    # Crear/obtener categoría
                    categoria_nombre = producto_data.get('categoria', 'general')
                    categoria, created = Categoria.objects.get_or_create(
                        nombre=categoria_nombre
                    )
                    if created:
                        stats['categorias_creadas'] += 1
                    
                    # Crear/obtener producto
                    producto, created = Producto.objects.get_or_create(
                        nombre=producto_data.get('nombre', ''),
                        marca=producto_data.get('marca', ''),
                        defaults={
                            'descripcion': producto_data.get('nombre', ''),
                            'imagen_url': '',
                            'categoria': categoria
                        }
                    )
                    if created:
                        stats['productos_creados'] += 1
                    
                    # Procesar tiendas y precios
                    for tienda_data in producto_data.get('tiendas', []):
                        fuente = tienda_data.get('fuente', '').upper()
                        if not fuente:
                            continue
                        
                        # Crear/obtener tienda
                        tienda, created = Tienda.objects.get_or_create(
                            nombre=fuente,
                            defaults={'url_website': ''}
                        )
                        if created:
                            stats['tiendas_creadas'] += 1
                        
                        # Crear precio
                        precio = tienda_data.get('precio', 0)
                        if precio > 0:
                            stock_value = tienda_data.get('stock', 'In stock')
                            stock_bool = stock_value == 'In stock' if isinstance(stock_value, str) else bool(stock_value)
                            
                            precio_obj, created = PrecioProducto.objects.get_or_create(
                                producto=producto,
                                tienda=tienda,
                                defaults={
                                    'precio': Decimal(str(precio)),
                                    'stock': stock_bool,
                                    'url_producto': tienda_data.get('url', '')
                                }
                            )
                            if created:
                                stats['precios_creados'] += 1
            
            return {
                'success': True,
                'message': 'Sincronización completada exitosamente',
                'stats': stats
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error en sincronización: {str(e)}'
            }
    
    @staticmethod
    def get_data_sources_status() -> Dict:
        """Obtiene el estado de las fuentes de datos"""
        base_dir = Path(settings.BASE_DIR)
        
        # Archivos raw del scraper
        scraper_files = [
            'scraper/data/dbs_maquillaje.json',
            'scraper/data/dbs_skincare.json',
            'scraper/data/maicao_maquillaje.json',
            'scraper/data/maicao_skincare.json',
            'scraper/data/preunic_maquillaje.json',
            'scraper/data/preunic_skincare.json'
        ]
        
        # Archivos procesados
        processed_files = [
            'data/processed/unified_products.json'
        ]
        
        status = {
            'scraper_files': {},
            'processed_files': {},
            'database_stats': {}
        }
        
        # Verificar archivos del scraper
        for file_path in scraper_files:
            full_path = base_dir / file_path
            status['scraper_files'][file_path] = {
                'exists': full_path.exists(),
                'size': full_path.stat().st_size if full_path.exists() else 0,
                'modified': full_path.stat().st_mtime if full_path.exists() else None
            }
        
        # Verificar archivos procesados
        for file_path in processed_files:
            full_path = base_dir / file_path
            status['processed_files'][file_path] = {
                'exists': full_path.exists(),
                'size': full_path.stat().st_size if full_path.exists() else 0,
                'modified': full_path.stat().st_mtime if full_path.exists() else None
            }
        
        # Estadísticas de la base de datos
        status['database_stats'] = {
            'productos': Producto.objects.count(),
            'precios': PrecioProducto.objects.count(),
            'categorias': Categoria.objects.count(),
            'tiendas': Tienda.objects.count()
        }
        
        return status


class ProductoService:
    """Servicio de negocio para productos que integra datos ETL y BD"""
    
    @staticmethod
    def get_productos_hibridos(filtros: Dict = None) -> List[Dict]:
        """Obtiene productos combinando datos de BD y archivo unificado"""
        filtros = filtros or {}
        
        # Datos de la base de datos
        productos_bd = ProductoController.buscar_productos(
            categoria_id=filtros.get('categoria_id'),
            tienda_id=filtros.get('tienda_id'),
            search=filtros.get('search'),
            limit=filtros.get('limit', 50)
        )
        
        # Datos del archivo unificado
        try:
            unified_data = UnifiedDataController.load_unified_products()
            productos_unified = unified_data.get("productos", [])
            
            # Aplicar filtros a datos unificados
            if filtros.get('search'):
                search_term = filtros['search'].lower()
                productos_unified = [
                    p for p in productos_unified 
                    if search_term in p.get('nombre', '').lower() or 
                       search_term in p.get('marca', '').lower()
                ]
            
            if filtros.get('categoria'):
                productos_unified = [
                    p for p in productos_unified 
                    if p.get('categoria') == filtros['categoria']
                ]
            
            # Combinar y deduplicar resultados
            productos_combinados = productos_bd.copy()
            
            # Agregar productos del archivo unificado que no están en BD
            productos_bd_nombres = {p['nombre'] for p in productos_bd}
            for producto_unified in productos_unified[:20]:  # Limitar para performance
                if producto_unified.get('nombre') not in productos_bd_nombres:
                    # Adaptar formato
                    producto_adaptado = {
                        'id': producto_unified.get('product_id', ''),
                        'nombre': producto_unified.get('nombre', ''),
                        'marca': producto_unified.get('marca', ''),
                        'categoria': producto_unified.get('categoria', ''),
                        'precio_min': min([t.get('precio', 0) for t in producto_unified.get('tiendas', [])]),
                        'tiendas_disponibles': [t.get('fuente') for t in producto_unified.get('tiendas', [])],
                        'imagen_url': '',
                        'descripcion': '',
                        'source': 'unified'
                    }
                    productos_combinados.append(producto_adaptado)
            
            return productos_combinados
            
        except Exception as e:
            # Si falla la carga unificada, devolver solo datos de BD
            return productos_bd
    
    @staticmethod
    def get_dashboard_hibrido() -> Dict:
        """Obtiene datos de dashboard combinando BD y archivo unificado"""
        try:
            # Datos de la base de datos
            stats_bd = DashboardController.get_estadisticas()
            productos_populares_bd = DashboardController.get_productos_populares()
            
            # Datos del archivo unificado
            try:
                stats_unified = UnifiedDataController.get_unified_dashboard()
                
                # Combinar estadísticas
                dashboard_data = {
                    'estadisticas': {
                        'total_productos_bd': stats_bd['total_productos'],
                        'total_productos_unified': stats_unified['estadisticas']['total_productos'],
                        'total_categorias': max(stats_bd['total_categorias'], stats_unified['estadisticas']['total_categorias']),
                        'total_tiendas': max(stats_bd['total_tiendas'], stats_unified['estadisticas']['total_tiendas']),
                        'precio_promedio': stats_bd['precio_promedio'],
                        'precio_min': stats_bd['precio_min'],
                        'precio_max': stats_bd['precio_max']
                    },
                    'productos_populares': productos_populares_bd,
                    'productos_por_categoria': DashboardController.get_productos_por_categoria(),
                    'tiendas_disponibles': stats_unified.get('tiendas_disponibles', []),
                    'categorias_disponibles': stats_unified.get('categorias_disponibles', []),
                    'data_sources': {
                        'database': True,
                        'unified_file': True
                    }
                }
                
                return dashboard_data
                
            except Exception:
                # Si falla unified, usar solo BD
                return {
                    'estadisticas': stats_bd,
                    'productos_populares': productos_populares_bd,
                    'productos_por_categoria': DashboardController.get_productos_por_categoria(),
                    'data_sources': {
                        'database': True,
                        'unified_file': False
                    }
                }
                
        except Exception as e:
            raise ValueError(f"Error obteniendo dashboard híbrido: {str(e)}")


class ETLSchedulerService:
    """Servicio para programar y automatizar el pipeline ETL"""
    
    @staticmethod
    def schedule_daily_etl() -> Dict:
        """Programa ETL diario (placeholder para implementación con Celery/Cron)"""
        # Esta función sería implementada con Celery para scheduling real
        return {
            'success': True,
            'message': 'ETL programado para ejecución diaria',
            'next_run': 'Requiere implementación de Celery/Cron'
        }
    
    @staticmethod
    def get_etl_logs() -> List[Dict]:
        """Obtiene logs del pipeline ETL"""
        # Placeholder para sistema de logs más avanzado
        return [
            {
                'timestamp': '2024-01-01T00:00:00Z',
                'stage': 'extract',
                'status': 'success',
                'message': 'Scraping completado'
            },
            {
                'timestamp': '2024-01-01T00:05:00Z',
                'stage': 'transform',
                'status': 'success',
                'message': 'Normalización completada'
            },
            {
                'timestamp': '2024-01-01T00:10:00Z',
                'stage': 'load',
                'status': 'success',
                'message': 'Carga a BD completada'
            }
        ]


# ============================================================================
# BUSINESS LOGIC SERVICES (Consolidated from controllers.py)
# ============================================================================

class DashboardService:
    """Servicio para lógica de dashboard"""
    
    @staticmethod
    def get_estadisticas():
        """Obtiene estadísticas generales del sistema"""
        total_productos = Producto.objects.count()
        total_categorias = Categoria.objects.count()
        total_tiendas = Tienda.objects.count()
        
        # Usar manager personalizado para estadísticas de precios
        estadisticas_precios = PrecioProducto.objects.estadisticas_generales()
        
        return {
            'total_productos': total_productos,
            'productos_con_precios': estadisticas_precios['total_productos_con_precio'],
            'total_categorias': total_categorias,
            'total_tiendas': total_tiendas,
            'precio_promedio': float(estadisticas_precios['precio_promedio']),
            'precio_min': float(estadisticas_precios['precio_min']),
            'precio_max': float(estadisticas_precios['precio_max'])
        }
    
    @staticmethod
    def get_productos_por_categoria():
        """Obtiene productos agrupados por categoría"""
        return list(Categoria.objects.con_estadisticas().values('nombre', 'cantidad_productos'))
    
    @staticmethod
    def get_tiendas_disponibles():
        """Obtiene lista de tiendas con productos disponibles"""
        return list(Tienda.objects.con_estadisticas().values('id', 'nombre', 'cantidad_productos'))
    
    @staticmethod 
    def get_categorias_disponibles():
        """Obtiene lista de categorías con productos disponibles"""
        return list(Categoria.objects.con_estadisticas().values('id', 'nombre', 'cantidad_productos'))
    
    @staticmethod
    def get_productos_populares(limit=8):
        """Obtiene productos más populares con información detallada"""
        productos_populares = Producto.objects.populares(limit)
        productos_data = []
        
        for producto in productos_populares:
            precio_min = producto.get_precio_min()
            if precio_min:
                productos_data.append({
                    'id': producto.id,
                    'nombre': producto.nombre,
                    'marca': producto.marca or '',
                    'categoria': producto.categoria.nombre,
                    'precio_min': float(precio_min),
                    'tiendas_disponibles': producto.get_tiendas_disponibles(),
                    'imagen_url': producto.imagen_url or '',
                    'num_precios': producto.num_precios
                })
        
        return productos_data


class ProductoService:
    """Servicio para lógica de productos"""
    
    @staticmethod
    def buscar_productos(categoria_id=None, tienda_id=None, search=None, limit=50):
        """Busca productos con filtros aplicados"""
        productos = Producto.objects.all()
        
        if categoria_id:
            productos = productos.filter(categoria_id=categoria_id)
        
        if search:
            productos = productos.buscar(search)
        
        if tienda_id:
            productos = productos.por_tienda_id(tienda_id)
        
        # Obtener productos con precios
        productos_data = []
        for producto in productos[:limit]:
            precio_min = producto.get_precio_min()
            if precio_min:
                productos_data.append({
                    'id': producto.id,
                    'nombre': producto.nombre,
                    'marca': producto.marca or '',
                    'categoria': producto.categoria.nombre,
                    'precio_min': float(precio_min),
                    'tiendas_disponibles': producto.get_tiendas_disponibles(),
                    'imagen_url': producto.imagen_url or '',
                    'descripcion': producto.descripcion or ''
                })
        
        return productos_data
    
    @staticmethod
    def get_producto_detalle(producto_id):
        """Obtiene detalles completos de un producto"""
        try:
            producto = Producto.objects.get(id=producto_id)
            
            precios_producto = PrecioProducto.objects.filter(
                producto=producto,
                stock=True
            ).select_related('tienda')
            
            precio_min = producto.get_precio_min()
            precio_max = producto.get_precio_max()
            
            # Información detallada de tiendas
            tiendas_detalladas = []
            for precio in precios_producto:
                tiendas_detalladas.append({
                    'nombre': precio.tienda.nombre,
                    'precio': float(precio.precio),
                    'stock': precio.stock,
                    'url_producto': precio.url_producto or '',
                    'fecha_extraccion': precio.fecha_extraccion.isoformat()
                })
            
            stock_disponible = precios_producto.filter(stock=True).exists()
            
            return {
                'id': producto.id,
                'nombre': producto.nombre,
                'marca': producto.marca or '',
                'categoria': producto.categoria.nombre if producto.categoria else '',
                'descripcion': producto.descripcion or '',
                'precio': float(precio_min) if precio_min else 0,
                'precio_min': float(precio_min) if precio_min else 0,
                'precio_max': float(precio_max) if precio_max else 0,
                'precio_original': float(precio_max) if precio_max else 0,
                'stock': 'In stock' if stock_disponible else 'Out of stock',
                'url': precios_producto.first().url_producto if precios_producto.exists() else '',
                'imagen_url': producto.imagen_url or '',
                'tiendas_disponibles': producto.get_tiendas_disponibles(),
                'tiendas_detalladas': tiendas_detalladas,
                'num_precios': precios_producto.count()
            }
        except Producto.DoesNotExist:
            return None
    
    @staticmethod
    def get_productos_por_tienda(tienda_nombre, categoria_nombre=None, search=None, marca=None):
        """Obtiene productos de una tienda específica desde datos unificados"""
        try:
            # Cargar productos unificados
            unified_data = UnifiedDataService.load_unified_products()
            productos = unified_data.get("productos", [])
            
            # Filtrar por tienda
            tienda_lower = tienda_nombre.lower()
            productos_tienda = []
            
            for producto in productos:
                tiendas = producto.get('tiendas', [])
                for tienda in tiendas:
                    if tienda.get('fuente', '').lower() == tienda_lower:
                        # Aplicar filtros adicionales
                        if categoria_nombre and producto.get('categoria') != categoria_nombre:
                            continue
                        
                        if search:
                            search_lower = search.lower()
                            if not (search_lower in producto.get('nombre', '').lower() or 
                                   search_lower in producto.get('marca', '').lower()):
                                continue
                        
                        if marca and marca.lower() not in producto.get('marca', '').lower():
                            continue
                        
                        # Agregar producto a la lista
                        productos_tienda.append({
                            'id': producto.get('product_id'),
                            'product_id': producto.get('product_id'),
                            'nombre': producto.get('nombre', ''),
                            'marca': producto.get('marca', ''),
                            'categoria': producto.get('categoria', ''),
                            'precio': float(tienda.get('precio', 0)),
                            'stock': True,  # Asumimos que está en stock si está en el JSON
                            'url_producto': tienda.get('url', ''),
                            'imagen_url': tienda.get('imagen') or producto.get('imagen', ''),
                            'descripcion': producto.get('descripcion', ''),
                            'fecha_extraccion': tienda.get('fecha_extraccion', ''),
                            'tienda': tienda_nombre.upper()
                        })
                        break  # Solo agregamos una vez por producto
            
            # Ordenar por precio
            productos_tienda.sort(key=lambda x: x['precio'])
            
            # Obtener categorías disponibles para esta tienda
            categorias_disponibles = list(set(
                p.get('categoria') for p in productos
                if any(t.get('fuente', '').lower() == tienda_lower for t in p.get('tiendas', []))
                and p.get('categoria')
            ))
            
            return {
                'productos': productos_tienda,
                'total': len(productos_tienda),
                'categorias_disponibles': categorias_disponibles,
                'tienda': tienda_nombre
            }
            
        except Exception as e:
            print(f"Error in get_productos_por_tienda: {e}")
            return {
                'productos': [],
                'total': 0,
                'categorias_disponibles': [],
                'tienda': tienda_nombre
            }


class CategoriaService:
    """Servicio para lógica de categorías"""
    
    @staticmethod
    def get_categorias_con_estadisticas():
        """Obtiene todas las categorías con estadísticas"""
        return list(Categoria.objects.con_estadisticas().values('id', 'nombre', 'cantidad_productos'))


class TiendaService:
    """Servicio para lógica de tiendas"""
    
    @staticmethod
    def get_tiendas_con_estadisticas():
        """Obtiene todas las tiendas con estadísticas"""
        return list(Tienda.objects.con_estadisticas().values('id', 'nombre', 'url_website', 'cantidad_productos'))


class PrecioService:
    """Servicio para lógica de precios"""
    
    @staticmethod
    def get_precios_por_producto(producto_id):
        """Obtiene todos los precios de un producto"""
        precios = PrecioProducto.objects.filter(
            producto_id=producto_id,
            stock=True
        ).select_related('tienda')
        
        precios_data = []
        for precio in precios:
            precios_data.append({
                'id': precio.id,
                'tienda': precio.tienda.nombre,
                'precio': float(precio.precio),
                'stock': precio.stock,
                'url_producto': precio.url_producto or '',
                'fecha_extraccion': precio.fecha_extraccion.isoformat()
            })
        
        return precios_data


class UsuarioService:
    """Servicio para lógica de usuarios"""
    
    @staticmethod
    def crear_usuario(username, email, password):
        """Crea un nuevo usuario con validaciones"""
        # Validaciones
        if User.objects.filter(username=username).exists():
            raise ValueError("El nombre de usuario ya existe")
        
        if email and User.objects.filter(email=email).exists():
            raise ValueError("El email ya está registrado")
        
        # Crear usuario
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        return user


class AlertaService:
    """Servicio para lógica de alertas"""
    
    @staticmethod
    def crear_alerta_precio(producto_id, email):
        """Crea una alerta de precio"""
        # Verificar que el producto existe
        try:
            producto = Producto.objects.get(id=producto_id)
        except Producto.DoesNotExist:
            raise ValueError("Producto no encontrado")
        
        # Verificar si ya existe una alerta
        if AlertaPrecio.objects.filter(producto=producto, email=email).exists():
            raise ValueError("Ya existe una alerta para este email y producto")
        
        # Crear la alerta
        alerta = AlertaPrecio.objects.create(
            producto=producto,
            email=email
        )
        return alerta


class ResenaService:
    """Servicio para lógica de reseñas"""
    
    @staticmethod
    def get_resenas_producto(producto_id):
        """Obtiene reseñas de un producto con estadísticas"""
        try:
            producto = Producto.objects.get(id=producto_id)
        except Producto.DoesNotExist:
            raise ValueError("Producto no encontrado")
        
        # Obtener reseñas usando manager personalizado
        resenas = Resena.objects.por_producto(producto_id)
        estadisticas = Resena.objects.estadisticas_producto(producto_id)
        
        # Reseñas recientes para vista de detalle
        resenas_recientes = Resena.objects.por_producto(producto_id).recientes()
        
        return {
            "producto_id": producto_id,
            "total_resenas": estadisticas['total_resenas'],
            "promedio_valoracion": estadisticas['promedio_valoracion'],
            "resenas_recientes": ResenaSerializer(resenas_recientes, many=True).data,
            "todas_resenas": ResenaSerializer(resenas, many=True).data
        }
    
    @staticmethod
    def crear_resena(producto_id, valoracion, comentario, autor=None):
        """Crea una nueva reseña"""
        try:
            producto = Producto.objects.get(id=producto_id)
        except Producto.DoesNotExist:
            raise ValueError("Producto no encontrado")
        
        # Validaciones
        if not (1 <= valoracion <= 5):
            raise ValueError("La valoración debe estar entre 1 y 5")
        
        if len(comentario.strip()) < 10:
            raise ValueError("El comentario debe tener al menos 10 caracteres")
        
        # Crear usuario temporal
        if not autor:
            username = f'anonimo_{producto_id}_{len(comentario)}'
        else:
            username = f'temp_{autor.replace(" ", "_").lower()}_{producto_id}'
        
        usuario, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': autor.split(' ')[0] if autor and ' ' in autor else (autor or 'Usuario'),
                'last_name': ' '.join(autor.split(' ')[1:]) if autor and ' ' in autor else '',
                'email': f'{username}@example.com'
            }
        )
        
        # Verificar si ya existe una reseña
        if Resena.objects.filter(producto=producto, usuario=usuario).exists():
            raise ValueError("Ya has escrito una reseña para este producto")
        
        # Crear la reseña
        resena = Resena.objects.create(
            producto=producto,
            usuario=usuario,
            valoracion=valoracion,
            comentario=comentario.strip(),
            nombre_autor=autor
        )
        
        return resena


class UnifiedDataService:
    """Servicio para datos unificados del procesador"""
    
    @staticmethod
    def load_unified_products():
        """Cargar productos unificados desde el archivo JSON"""
        try:
            possible_paths = [
                os.path.join(settings.BASE_DIR, 'data', 'processed', 'unified_products.json'),
            ]
            
            for json_path in possible_paths:
                if os.path.exists(json_path):
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Handle both array format and object format
                        if isinstance(data, list):
                            return {"productos": data}
                        elif isinstance(data, dict) and "productos" in data:
                            return data
                        else:
                            return {"productos": []}
            
            return {"productos": []}
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ValueError(f"Error loading unified products: {e}")
    
    @staticmethod
    def get_unified_dashboard():
        """Obtiene datos de dashboard desde productos unificados"""
        unified_data = UnifiedDataService.load_unified_products()
        productos = unified_data.get("productos", [])
        
        # Estadísticas básicas
        total_productos = len(productos)
        tiendas_disponibles = set()
        categorias_disponibles = set()
        
        for producto in productos:
            # Extract stores from tiendas array
            tiendas_producto = producto.get('tiendas', [])
            for tienda in tiendas_producto:
                if tienda.get('fuente'):
                    tiendas_disponibles.add(tienda['fuente'])
            
            if producto.get('categoria'):
                categorias_disponibles.add(producto['categoria'])
        
        # Productos populares (primeros para simplificar)
        productos_populares = productos[:10]
        
        return {
            'estadisticas': {
                'total_productos': total_productos,
                'total_tiendas': len(tiendas_disponibles),
                'total_categorias': len(categorias_disponibles),
            },
            'productos_populares': productos_populares,
            'tiendas_disponibles': list(tiendas_disponibles),
            'categorias_disponibles': list(categorias_disponibles)
        }


class UtilService:
    """Servicio para utilidades y funciones helper"""
    
    @staticmethod
    def find_product_by_id(producto_id):
        """Helper function to find numeric product ID from various formats"""
        try:
            # If it's already numeric, return as-is
            if str(producto_id).isdigit():
                return int(producto_id)
            
            # If it contains underscores (e.g., "dbs_123"), extract the numeric part
            if '_' in str(producto_id):
                parts = str(producto_id).split('_')
                for part in parts:
                    if part.isdigit():
                        return int(part)
            
            # If it contains hyphens (canonical format), try to extract numeric part
            if '-' in str(producto_id):
                parts = str(producto_id).split('-')
                for part in parts:
                    if part.isdigit():
                        return int(part)
            
            return None
        except (ValueError, TypeError):
            return None

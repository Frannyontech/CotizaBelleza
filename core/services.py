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

from .models import Categoria, Tienda, Producto, PrecioProducto
from .controllers import (
    DashboardController, ProductoController, CategoriaController,
    TiendaController, PrecioController, UnifiedDataController
)


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

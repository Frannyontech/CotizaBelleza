from django.core.management.base import BaseCommand
from django.core.management.color import make_style
import json
from pathlib import Path
from datetime import datetime

from core.services.persistent_id_manager import PersistentIdManager, procesar_json_unificado_con_ids_persistentes
from core.services.deduplication import deduplicar_productos_avanzado
from processor.persistent_processor import PersistentETLProcessor
from core.models import ProductoPersistente, PrecioHistorico, EstadisticaProducto
from django.db.models import Count


class Command(BaseCommand):
    help = 'Gestor del sistema de IDs persistentes de CotizaBelleza'
    
    def add_arguments(self, parser):
        parser.add_argument('comando', choices=[
            'procesar-json', 'procesar-etl', 'deduplicar', 'estadisticas', 
            'buscar', 'actualizar-estadisticas', 'limpiar'
        ], help='Comando a ejecutar')
        
        parser.add_argument('archivo', nargs='?', help='Archivo a procesar (para algunos comandos)')
        parser.add_argument('--fecha', help='Fecha del scraping (YYYY-MM-DD)')
        parser.add_argument('--base-dir', help='Directorio base del proyecto')
        parser.add_argument('--salida', help='Archivo de salida')
        parser.add_argument('--umbral', type=float, default=0.85, help='Umbral de similitud')
        parser.add_argument('--dias', type=int, default=30, help='Días de antigüedad')
        parser.add_argument('termino', nargs='?', help='Término de búsqueda')

    def handle(self, *args, **options):
        comando = options['comando']
        
        try:
            if comando == 'procesar-json':
                if not options['archivo']:
                    self.stdout.write(self.style.ERROR('Debe especificar un archivo JSON'))
                    return
                self.comando_procesar_json(options['archivo'], options.get('fecha'))
            
            elif comando == 'procesar-etl':
                self.comando_procesar_etl_completo(options.get('base_dir'))
            
            elif comando == 'deduplicar':
                if not options['archivo']:
                    self.stdout.write(self.style.ERROR('Debe especificar un archivo JSON'))
                    return
                self.comando_deduplicar_json(
                    options['archivo'], 
                    options.get('salida'), 
                    options.get('umbral', 0.85)
                )
            
            elif comando == 'estadisticas':
                self.comando_estadisticas()
            
            elif comando == 'buscar':
                if not options['termino']:
                    self.stdout.write(self.style.ERROR('Debe especificar un término de búsqueda'))
                    return
                self.comando_buscar_producto(options['termino'])
            
            elif comando == 'actualizar-estadisticas':
                self.comando_actualizar_estadisticas()
            
            elif comando == 'limpiar':
                self.comando_limpiar_datos_antiguos(options.get('dias', 30))
        
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nOperación cancelada por el usuario'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error inesperado: {e}'))
            import traceback
            traceback.print_exc()

    def comando_procesar_json(self, archivo_json: str, fecha_scraping: str = None):
        """Procesa un archivo JSON unificado y asigna IDs persistentes"""
        self.stdout.write(f"Procesando archivo JSON: {archivo_json}")
        
        fecha = None
        if fecha_scraping:
            try:
                fecha = datetime.fromisoformat(fecha_scraping)
            except ValueError:
                self.stdout.write(self.style.ERROR(f"Fecha inválida '{fecha_scraping}'. Use formato YYYY-MM-DD"))
                return
        
        resultado = procesar_json_unificado_con_ids_persistentes(archivo_json, fecha)
        
        if resultado['exito']:
            self.stdout.write(self.style.SUCCESS("Procesamiento exitoso!"))
            self.stdout.write(f"   Productos procesados: {resultado['productos_procesados']}")
            self.stdout.write(f"   Productos nuevos: {resultado['productos_nuevos']}")
            self.stdout.write(f"   Productos actualizados: {resultado['productos_actualizados']}")
            self.stdout.write(f"   Precios agregados: {resultado['precios_agregados']}")
            
            if resultado['errores']:
                self.stdout.write(f"   Errores: {len(resultado['errores'])}")
        else:
            self.stdout.write(self.style.ERROR(f"Error: {resultado['error']}"))

    def comando_estadisticas(self):
        """Muestra estadísticas del sistema de IDs persistentes"""
        self.stdout.write("ESTADÍSTICAS DEL SISTEMA DE IDS PERSISTENTES")
        self.stdout.write("=" * 60)
        
        total_productos = ProductoPersistente.objects.count()
        productos_activos = ProductoPersistente.objects.filter(activo=True).count()
        
        self.stdout.write(f"Total productos persistentes: {total_productos}")
        self.stdout.write(f"Productos activos: {productos_activos}")
        
        self.stdout.write("\nPor categoría:")
        categorias = ProductoPersistente.objects.values('categoria').annotate(
            count=Count('id')
        ).order_by('-count')
        
        for cat in categorias:
            self.stdout.write(f"  {cat['categoria']}: {cat['count']} productos")
        
        self.stdout.write("\nTop 10 marcas:")
        marcas = ProductoPersistente.objects.values('marca').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        for marca in marcas:
            self.stdout.write(f"  {marca['marca']}: {marca['count']} productos")
        
        total_precios = PrecioHistorico.objects.count()
        precios_con_stock = PrecioHistorico.objects.filter(stock=True).count()
        
        self.stdout.write(f"\nPrecios históricos:")
        self.stdout.write(f"  Total registros: {total_precios}")
        self.stdout.write(f"  Con stock: {precios_con_stock}")
        
        self.stdout.write("\nPor tienda:")
        tiendas = PrecioHistorico.objects.values('tienda').annotate(
            count=Count('id')
        ).order_by('-count')
        
        for tienda in tiendas:
            self.stdout.write(f"  {tienda['tienda']}: {tienda['count']} precios")

    def comando_buscar_producto(self, termino: str):
        """Busca productos por término"""
        self.stdout.write(f"Buscando productos con término: '{termino}'")
        
        productos = ProductoPersistente.objects.filter(
            nombre_normalizado__icontains=termino.lower()
        )[:10]
        
        if not productos:
            self.stdout.write("No se encontraron productos")
            return
        
        self.stdout.write(f"\nEncontrados {len(productos)} productos:")
        self.stdout.write("-" * 80)
        
        for producto in productos:
            self.stdout.write(f"ID: {producto.internal_id}")
            self.stdout.write(f"Nombre: {producto.nombre_original}")
            self.stdout.write(f"Marca: {producto.marca}")
            self.stdout.write(f"Categoría: {producto.categoria}")
            self.stdout.write(f"Veces encontrado: {producto.veces_encontrado}")
            self.stdout.write("-" * 80)

import json
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Categoria, Tienda, Producto, PrecioProducto
from decimal import Decimal

class Command(BaseCommand):
    help = 'Carga datos de scrapers de diferentes tiendas al sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help='Ruta al archivo JSON del scraper (ej: scraper/data/dbs_productos.json)'
        )
        parser.add_argument(
            '--tienda',
            type=str,
            required=True,
            help='Nombre de la tienda (ej: DBS, Maicao, Preunic)'
        )
        parser.add_argument(
            '--url-tienda',
            type=str,
            help='URL de la tienda (ej: https://dbs.cl)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Limpiar datos existentes de la tienda antes de cargar'
        )
        parser.add_argument(
            '--categorias',
            type=str,
            nargs='+',
            help='Categorías específicas a procesar (ej: maquillaje skincare)'
        )

    def truncate_text(self, text, max_length):
        if text and len(text) > max_length:
            return text[:max_length-3] + "..."
        return text

    def get_tienda_config(self, tienda_nombre):
        """Configuración específica por tienda"""
        configs = {
            'DBS': {
                'url': 'https://dbs.cl',
                'categorias_default': ['maquillaje', 'skincare'],
                'stock_mapping': {'In stock': True, 'Out of stock': False}
            },
            'MAICAO': {
                'url': 'https://maicao.com',
                'categorias_default': ['maquillaje', 'skincare', 'perfumes'],
                'stock_mapping': {'In stock': True, 'Out of stock': False}
            },
            'PREUNIC': {
                'url': 'https://preunic.com',
                'categorias_default': ['maquillaje', 'skincare', 'belleza'],
                'stock_mapping': {'In stock': True, 'Out of stock': False}
            }
        }
        return configs.get(tienda_nombre.upper(), {
            'url': '',
            'categorias_default': ['general'],
            'stock_mapping': {'In stock': True, 'Out of stock': False}
        })

    def handle(self, *args, **options):
        file_path = options['file']
        tienda_nombre = options['tienda']
        url_tienda = options['url_tienda']
        clear_data = options['clear']
        categorias_especificas = options['categorias']
        
        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f'El archivo {file_path} no existe')
            )
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            self.stdout.write(
                self.style.SUCCESS(f'Cargando datos de {tienda_nombre} desde {file_path}...')
            )

            # Obtener configuración de la tienda
            tienda_config = self.get_tienda_config(tienda_nombre)
            if not url_tienda:
                url_tienda = tienda_config['url']

            with transaction.atomic():
                # Crear o obtener tienda
                tienda, created = Tienda.objects.get_or_create(
                    nombre=tienda_nombre.upper(),
                    defaults={'url_website': url_tienda}
                )
                if created:
                    self.stdout.write(f'Tienda creada: {tienda_nombre.upper()}')

                # Determinar categorías a procesar
                categorias_a_procesar = categorias_especificas if categorias_especificas else tienda_config['categorias_default']
                
                # Crear categorías dinámicamente
                categorias_creadas = {}
                for categoria_nombre in categorias_a_procesar:
                    categoria, created = Categoria.objects.get_or_create(
                        nombre=categoria_nombre
                    )
                    categorias_creadas[categoria_nombre] = categoria
                    if created:
                        self.stdout.write(f'Categoría creada: {categoria_nombre}')

                # Limpiar datos existentes si se solicita
                if clear_data:
                    PrecioProducto.objects.filter(tienda=tienda).delete()
                    Producto.objects.filter(
                        tiendas_producto__tienda=tienda
                    ).delete()
                    self.stdout.write(f'Datos existentes de {tienda_nombre} eliminados')

                productos_creados = 0
                precios_creados = 0

                # Procesar datos del JSON
                for categoria_key, categoria_data in data.items():
                    if categoria_key in ['fecha_extraccion', 'total_productos']:
                        continue
                    
                    # Solo procesar categorías especificadas
                    if categoria_key not in categorias_a_procesar:
                        continue

                    categoria_model = categorias_creadas.get(categoria_key)
                    if not categoria_model:
                        continue

                    self.stdout.write(f'Procesando categoría: {categoria_key}')

                    for producto_data in categoria_data.get('productos', []):
                        # Truncar datos si son demasiado largos
                        nombre = self.truncate_text(producto_data['nombre'], 500)
                        marca = self.truncate_text(producto_data.get('marca', ''), 200)
                        imagen_url = self.truncate_text(producto_data.get('imagen', ''), 500)
                        url_producto = self.truncate_text(producto_data.get('url', ''), 500)

                        # Crear o actualizar producto
                        producto, created = Producto.objects.get_or_create(
                            nombre=nombre,
                            marca=marca,
                            defaults={
                                'descripcion': nombre,
                                'imagen_url': imagen_url,
                                'categoria': categoria_model
                            }
                        )

                        # Si el producto ya existía, actualizar la imagen si está vacía
                        if not created and (not producto.imagen_url or producto.imagen_url == ''):
                            producto.imagen_url = imagen_url
                            producto.save()
                            self.stdout.write(f'Imagen actualizada para: {nombre}')

                        if created:
                            productos_creados += 1

                        # Crear precio del producto
                        if producto_data.get('precio', 0) > 0:
                            # Manejar diferentes formatos de stock
                            stock_value = producto_data.get('stock', True)
                            if isinstance(stock_value, str):
                                stock_bool = tienda_config['stock_mapping'].get(stock_value, True)
                            else:
                                stock_bool = bool(stock_value)

                            precio, created = PrecioProducto.objects.get_or_create(
                                producto=producto,
                                tienda=tienda,
                                defaults={
                                    'precio': Decimal(str(producto_data['precio'])),
                                    'stock': stock_bool,
                                    'url_producto': url_producto
                                }
                            )
                            if created:
                                precios_creados += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Carga completada para {tienda_nombre}:\n'
                        f'- Productos creados: {productos_creados}\n'
                        f'- Precios creados: {precios_creados}\n'
                        f'- Categorías procesadas: {len(categorias_creadas)}\n'
                        f'- Tienda: {tienda_nombre.upper()}'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al cargar datos: {str(e)}')
            )
            raise 
import json
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Categoria, Tienda, Producto, PrecioProducto
from decimal import Decimal

class Command(BaseCommand):
    help = 'Carga datos del scraper de DBS al sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='scraper/dbs_productos.json',
            help='Ruta al archivo JSON del scraper'
        )

    def truncate_text(self, text, max_length):
        """Trunca el texto si excede la longitud máxima"""
        if text and len(text) > max_length:
            return text[:max_length-3] + "..."
        return text

    def handle(self, *args, **options):
        file_path = options['file']
        
        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f'El archivo {file_path} no existe')
            )
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            self.stdout.write(
                self.style.SUCCESS(f'Cargando datos de {file_path}...')
            )

            with transaction.atomic():
                # Crear solo las categorías necesarias
                categorias = {
                    'maquillaje': 'Maquillaje',
                    'skincare': 'Skincare'
                }

                categorias_creadas = {}
                for key, nombre in categorias.items():
                    categoria, created = Categoria.objects.get_or_create(
                        nombre=nombre
                    )
                    categorias_creadas[key] = categoria
                    if created:
                        self.stdout.write(f'Categoría creada: {nombre}')

                # Crear tienda DBS
                tienda_dbs, created = Tienda.objects.get_or_create(
                    nombre='DBS',
                    defaults={'url_website': 'https://dbs.cl'}
                )
                if created:
                    self.stdout.write('Tienda creada: DBS')

                # Procesar solo productos de maquillaje y skincare
                productos_creados = 0
                precios_creados = 0

                for categoria_key, categoria_data in data.items():
                    if categoria_key in ['fecha_extraccion', 'total_productos']:
                        continue
                    
                    # Solo procesar maquillaje y skincare
                    if categoria_key not in ['maquillaje', 'skincare']:
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
                            defaults={
                                'marca': marca,
                                'descripcion': nombre,
                                'imagen_url': imagen_url,
                                'categoria': categoria_model
                            }
                        )

                        if created:
                            productos_creados += 1

                        # Crear precio del producto
                        if producto_data.get('precio', 0) > 0:
                            precio, created = PrecioProducto.objects.get_or_create(
                                producto=producto,
                                tienda=tienda_dbs,
                                defaults={
                                    'precio': Decimal(str(producto_data['precio'])),
                                    'stock': producto_data.get('stock', True),
                                    'url_producto': url_producto
                                }
                            )
                            if created:
                                precios_creados += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Carga completada:\n'
                        f'- Productos creados: {productos_creados}\n'
                        f'- Precios creados: {precios_creados}\n'
                        f'- Categorías: {len(categorias_creadas)}\n'
                        f'- Tienda: DBS'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al cargar datos: {str(e)}')
            ) 
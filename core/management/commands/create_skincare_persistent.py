from django.core.management.base import BaseCommand
from core.models import ProductoPersistente, PrecioHistorico
from core.views import load_unified_products
from django.utils import timezone
import hashlib
import uuid


class Command(BaseCommand):
    help = 'Crear productos persistentes para productos de skincare desde JSON unificado'

    def handle(self, *args, **options):
        try:
            # Cargar productos unificados
            unified_data = load_unified_products()
            productos = unified_data.get("productos", [])
            
            # Filtrar solo productos de skincare
            productos_skincare = [
                p for p in productos 
                if p.get('categoria', '').lower() in ['skincare', 'cuidado_piel', 'cuidado de la piel']
            ]
            
            self.stdout.write(f"Encontrados {len(productos_skincare)} productos de skincare")
            
            productos_creados = 0
            productos_actualizados = 0
            
            for producto in productos_skincare:
                nombre = producto.get('nombre', '')
                marca = producto.get('marca', '')
                categoria = 'skincare'
                
                if not nombre or not marca:
                    continue
                
                # Generar hash único
                nombre_normalizado = nombre.lower().strip()
                marca_normalizada = marca.lower().strip()
                hash_unico = hashlib.sha256(
                    f"{nombre_normalizado}|{marca_normalizada}|{categoria}".encode('utf-8')
                ).hexdigest()
                
                # Buscar si ya existe
                producto_existente = ProductoPersistente.objects.filter(hash_unico=hash_unico).first()
                
                if producto_existente:
                    # Actualizar producto existente
                    producto_existente.actualizar_aparicion()
                    productos_actualizados += 1
                    continue
                
                # Crear nuevo producto persistente
                internal_id = f"cb_{uuid.uuid4().hex[:8]}"
                
                nuevo_producto = ProductoPersistente.objects.create(
                    internal_id=internal_id,
                    nombre_normalizado=nombre_normalizado,
                    marca=marca_normalizada,
                    categoria=categoria,
                    hash_unico=hash_unico,
                    nombre_original=nombre,
                    descripcion=f"Producto de skincare de la marca {marca}",
                    imagen_url=producto.get('imagen') or '',
                    activo=True
                )
                
                # Crear precios históricos para cada tienda
                tiendas = producto.get('tiendas', [])
                for tienda in tiendas:
                    try:
                        precio = float(tienda.get('precio', 0))
                        if precio > 0:
                            PrecioHistorico.objects.create(
                                producto=nuevo_producto,
                                tienda=tienda.get('fuente', 'unknown'),
                                precio=precio,
                                precio_original=precio,
                                tiene_descuento=False,
                                stock=True,
                                disponible=True,
                                url_producto=tienda.get('url', ''),
                                imagen_url=tienda.get('imagen', ''),
                                fecha_extraccion=timezone.now(),
                                fecha_scraping=timezone.now(),
                                fuente_scraping='skincare_migration'
                            )
                    except (ValueError, TypeError):
                        continue
                
                productos_creados += 1
                
                if productos_creados % 10 == 0:
                    self.stdout.write(f"Procesados {productos_creados} productos...")
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Migración completada: {productos_creados} productos creados, {productos_actualizados} actualizados'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error durante la migración: {str(e)}')
            )

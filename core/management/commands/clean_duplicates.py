from django.core.management.base import BaseCommand
from django.db import models
from core.models import Producto, PrecioProducto


class Command(BaseCommand):
    help = 'Limpia productos duplicados manteniendo el más reciente'

    def handle(self, *args, **options):
        self.stdout.write('Limpiando productos duplicados...')
        
        # Encontrar productos duplicados
        duplicados = Producto.objects.values('nombre', 'marca').annotate(
            count=models.Count('id')
        ).filter(count__gt=1)
        
        total_eliminados = 0
        
        for duplicado in duplicados:
            nombre = duplicado['nombre']
            marca = duplicado['marca']
            count = duplicado['count']
            
            self.stdout.write(f'Procesando: {nombre} - {marca} ({count} duplicados)')
            
            # Obtener todos los productos con el mismo nombre y marca
            productos = Producto.objects.filter(nombre=nombre, marca=marca).order_by('-id')
            
            # Mantener el primero (más reciente) y eliminar el resto
            producto_a_mantener = productos.first()
            productos_a_eliminar = productos[1:]
            
            for producto in productos_a_eliminar:
                # Mover los precios al producto que se mantiene
                precios = PrecioProducto.objects.filter(producto=producto)
                for precio in precios:
                    precio.producto = producto_a_mantener
                    precio.save()
                
                # Eliminar el producto duplicado
                producto.delete()
                total_eliminados += 1
                
                self.stdout.write(f'  - Eliminado: {producto.nombre} (ID: {producto.id})')
        
        self.stdout.write(
            self.style.SUCCESS(f'Limpieza completada. {total_eliminados} productos duplicados eliminados.')
        ) 
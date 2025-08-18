"""
Managers personalizados para los modelos - Parte de la capa Model en MVC
"""
from django.db import models
from django.db.models import Min, Max, Count, Avg


class ProductoManager(models.Manager):
    """Manager personalizado para Producto con consultas optimizadas"""
    
    def con_precios(self):
        """Productos que tienen al menos un precio"""
        return self.filter(precios__isnull=False).distinct()
    
    def por_categoria(self, categoria_nombre):
        """Filtrar productos por categoría"""
        return self.filter(categoria__nombre=categoria_nombre)
    
    def por_tienda(self, tienda_nombre):
        """Filtrar productos disponibles en una tienda específica"""
        return self.filter(precios__tienda__nombre=tienda_nombre).distinct()
    
    def buscar(self, query):
        """Buscar productos por nombre o marca"""
        return self.filter(
            models.Q(nombre__icontains=query) | 
            models.Q(marca__icontains=query)
        )
    
    def populares(self, limit=8):
        """Obtener productos más populares (con más precios)"""
        return self.annotate(
            num_precios=Count('precios')
        ).filter(
            num_precios__gt=0
        ).order_by('-num_precios')[:limit]
    
    def con_estadisticas_precios(self):
        """Productos con estadísticas de precios calculadas"""
        return self.prefetch_related('precios__tienda').annotate(
            precio_min=Min('precios__precio'),
            precio_max=Max('precios__precio'),
            num_tiendas=Count('precios__tienda', distinct=True)
        )


class PrecioProductoManager(models.Manager):
    """Manager personalizado para PrecioProducto"""
    
    def en_stock(self):
        """Precios de productos en stock"""
        return self.filter(stock=True)
    
    def por_tienda(self, tienda_nombre):
        """Precios de una tienda específica"""
        return self.filter(tienda__nombre=tienda_nombre)
    
    def estadisticas_generales(self):
        """Estadísticas generales de precios"""
        precios_en_stock = self.en_stock()
        return {
            'precio_promedio': precios_en_stock.aggregate(Avg('precio'))['precio__avg'] or 0,
            'precio_min': precios_en_stock.aggregate(Min('precio'))['precio__min'] or 0,
            'precio_max': precios_en_stock.aggregate(Max('precio'))['precio__max'] or 0,
            'total_productos_con_precio': precios_en_stock.values('producto').distinct().count()
        }


class CategoriaManager(models.Manager):
    """Manager personalizado para Categoria"""
    
    def con_productos(self):
        """Categorías que tienen productos"""
        return self.filter(productos__isnull=False).distinct()
    
    def con_estadisticas(self):
        """Categorías con estadísticas de productos"""
        return self.annotate(
            cantidad_productos=Count('productos')
        ).order_by('-cantidad_productos')


class TiendaManager(models.Manager):
    """Manager personalizado para Tienda"""
    
    def con_productos(self):
        """Tiendas que tienen productos"""
        return self.filter(productos_tienda__isnull=False).distinct()
    
    def con_estadisticas(self):
        """Tiendas con estadísticas de productos"""
        return self.annotate(
            cantidad_productos=Count('productos_tienda')
        ).order_by('-cantidad_productos')


class ResenaManager(models.Manager):
    """Manager personalizado para Resena"""
    
    def por_producto(self, producto_id):
        """Reseñas de un producto específico"""
        return self.filter(producto_id=producto_id).order_by('-fecha_creacion')
    
    def recientes(self, limit=3):
        """Reseñas más recientes"""
        return self.order_by('-fecha_creacion')[:limit]
    
    def estadisticas_producto(self, producto_id):
        """Estadísticas de reseñas para un producto"""
        resenas = self.filter(producto_id=producto_id)
        total = resenas.count()
        if total > 0:
            promedio = resenas.aggregate(Avg('valoracion'))['valoracion__avg']
            return {
                'total_resenas': total,
                'promedio_valoracion': round(promedio, 1) if promedio else 0
            }
        return {'total_resenas': 0, 'promedio_valoracion': 0}

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Count, Min, Max, Avg
from decimal import Decimal


# ============================================================================
# CUSTOM MANAGERS
# ============================================================================

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
    
    def por_tienda_id(self, tienda_id):
        """Filtrar productos disponibles en una tienda específica por ID"""
        return self.filter(precios__tienda_id=tienda_id).distinct()
    
    def buscar(self, texto):
        """Búsqueda de texto en nombre, marca y descripción"""
        return self.filter(
            models.Q(nombre__icontains=texto) |
            models.Q(marca__icontains=texto) |
            models.Q(descripcion__icontains=texto)
        )
    
    def populares(self, limit=10):
        """Productos más populares basados en número de precios/tiendas"""
        return self.annotate(
            num_precios=Count('precios', distinct=True)
        ).filter(num_precios__gt=0).order_by('-num_precios')[:limit]
    
    def con_descuento(self, porcentaje_minimo=10):
        """Productos con descuentos significativos"""
        return self.annotate(
            precio_min=Min('precios__precio'),
            precio_max=Max('precios__precio')
        ).filter(
            precio_min__lt=models.F('precio_max') * (100 - porcentaje_minimo) / 100
        )


class PrecioProductoManager(models.Manager):
    """Manager personalizado para PrecioProducto"""
    
    def en_stock(self):
        """Precios de productos en stock"""
        return self.filter(stock=True)
    
    def por_tienda(self, tienda_nombre):
        """Precios de una tienda específica"""
        return self.filter(tienda__nombre=tienda_nombre)
    
    def mas_baratos(self, limit=10):
        """Los precios más baratos disponibles"""
        return self.filter(stock=True).order_by('precio')[:limit]
    
    def actualizados_hoy(self):
        """Precios actualizados hoy"""
        from django.utils import timezone
        hoy = timezone.now().date()
        return self.filter(fecha_extraccion__date=hoy)
    
    def estadisticas_generales(self):
        """Estadísticas generales de precios"""
        stats = self.filter(stock=True).aggregate(
            precio_min=Min('precio'),
            precio_max=Max('precio'),
            precio_promedio=Avg('precio'),
            total_productos_con_precio=Count('producto', distinct=True)
        )
        
        # Asegurar que los valores no sean None
        return {
            'precio_min': stats['precio_min'] or 0,
            'precio_max': stats['precio_max'] or 0,
            'precio_promedio': stats['precio_promedio'] or 0,
            'total_productos_con_precio': stats['total_productos_con_precio'] or 0
        }


class CategoriaManager(models.Manager):
    """Manager personalizado para Categoria"""
    
    def con_productos(self):
        """Categorías que tienen al menos un producto"""
        return self.filter(productos__isnull=False).distinct()
    
    def con_estadisticas(self):
        """Categorías con estadísticas de productos"""
        return self.annotate(
            cantidad_productos=Count('productos', distinct=True)
        ).filter(cantidad_productos__gt=0)
    
    def populares(self, limit=5):
        """Categorías más populares por número de productos"""
        return self.con_estadisticas().order_by('-cantidad_productos')[:limit]


class TiendaManager(models.Manager):
    """Manager personalizado para Tienda"""
    
    def con_productos(self):
        """Tiendas que tienen al menos un producto en stock"""
        return self.filter(precios_tienda__stock=True).distinct()
    
    def con_estadisticas(self):
        """Tiendas con estadísticas de productos"""
        return self.annotate(
            cantidad_productos=Count('precios_tienda__producto', distinct=True)
        ).filter(cantidad_productos__gt=0)
    
    def activas(self):
        """Tiendas activas (con precios recientes)"""
        from django.utils import timezone
        hace_una_semana = timezone.now() - timezone.timedelta(days=7)
        return self.filter(precios_tienda__fecha_extraccion__gte=hace_una_semana).distinct()


class ResenaManager(models.Manager):
    """Manager personalizado para Resena"""
    
    def por_producto(self, producto_id):
        """Reseñas de un producto específico"""
        return self.filter(producto_id=producto_id)
    
    def recientes(self, limit=10):
        """Reseñas más recientes"""
        return self.order_by('-fecha_creacion')[:limit]
    
    def por_valoracion(self, valoracion_minima=4):
        """Reseñas con valoración alta"""
        return self.filter(valoracion__gte=valoracion_minima)
    
    def estadisticas_producto(self, producto_id):
        """Estadísticas de reseñas para un producto"""
        stats = self.filter(producto_id=producto_id).aggregate(
            total_resenas=Count('id'),
            promedio_valoracion=Avg('valoracion')
        )
        
        return {
            'total_resenas': stats['total_resenas'] or 0,
            'promedio_valoracion': round(stats['promedio_valoracion'], 1) if stats['promedio_valoracion'] else 0
        }


# ============================================================================
# MODELS
# ============================================================================

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    
    # Manager personalizado
    objects = CategoriaManager()
    
    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre

class Tienda(models.Model):
    nombre = models.CharField(max_length=100)
    url_website = models.URLField(max_length=255, blank=True, null=True)
    
    # Manager personalizado
    objects = TiendaManager()
    
    class Meta:
        verbose_name = "Tienda"
        verbose_name_plural = "Tiendas"
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre

class Producto(models.Model):
    nombre = models.CharField(max_length=500)
    marca = models.CharField(max_length=200, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    imagen_url = models.URLField(max_length=500, blank=True, null=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='productos')
    
    # Manager personalizado
    objects = ProductoManager()
    
    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} - {self.marca}" if self.marca else self.nombre
    
    def get_precio_min(self):
        """Obtiene el precio mínimo del producto"""
        precio_min = self.precios.filter(stock=True).aggregate(
            models.Min('precio')
        )['precio__min']
        return precio_min
    
    def get_precio_max(self):
        """Obtiene el precio máximo del producto"""
        precio_max = self.precios.filter(stock=True).aggregate(
            models.Max('precio')
        )['precio__max']
        return precio_max
    
    def get_tiendas_disponibles(self):
        """Obtiene las tiendas donde está disponible el producto"""
        return [p.tienda.nombre for p in self.precios.filter(stock=True).select_related('tienda')]

class ProductoTienda(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='tiendas_producto')
    tienda = models.ForeignKey(Tienda, on_delete=models.CASCADE, related_name='productos_tienda')
    
    class Meta:
        verbose_name = "Producto en Tienda"
        verbose_name_plural = "Productos en Tiendas"
        unique_together = ['producto', 'tienda']
        ordering = ['producto__nombre', 'tienda__nombre']
    
    def __str__(self):
        return f"{self.producto.nombre} en {self.tienda.nombre}"

class PrecioProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='precios')
    tienda = models.ForeignKey(Tienda, on_delete=models.CASCADE, related_name='precios_tienda')
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.BooleanField(default=True)
    fecha_extraccion = models.DateTimeField(auto_now_add=True)
    fecha_baja = models.DateTimeField(blank=True, null=True)
    url_producto = models.URLField(max_length=500, blank=True, null=True)
    
    # Manager personalizado
    objects = PrecioProductoManager()
    
    class Meta:
        verbose_name = "Precio de Producto"
        verbose_name_plural = "Precios de Productos"
        ordering = ['-fecha_extraccion']
    
    def __str__(self):
        return f"{self.producto.nombre} en {self.tienda.nombre} - ${self.precio}"

class Resena(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='resenas')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resenas_usuario')
    valoracion = models.SmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comentario = models.TextField()
    nombre_autor = models.CharField(max_length=100, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    # Manager personalizado
    objects = ResenaManager()
    
    class Meta:
        verbose_name = "Reseña"
        verbose_name_plural = "Reseñas"
        unique_together = ['producto', 'usuario']
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Reseña de {self.usuario.username} para {self.producto.nombre} - {self.valoracion}/5"

class Alerta(models.Model):
    fecha_notificacion = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Alerta"
        verbose_name_plural = "Alertas"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Alerta {self.id} - {self.fecha_creacion.strftime('%d/%m/%Y')}"

class AlertaUsuario(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='alertas_producto')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alertas_usuario')
    alerta = models.ForeignKey(Alerta, on_delete=models.CASCADE, related_name='usuarios_alerta')
    alerta_activa = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Alerta de Usuario"
        verbose_name_plural = "Alertas de Usuarios"
        unique_together = ['producto', 'usuario', 'alerta']
        ordering = ['-alerta__fecha_creacion']
    
    def __str__(self):
        return f"Alerta de {self.usuario.username} para {self.producto.nombre}"

class AlertaPrecio(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='alertas_precio')
    email = models.EmailField(max_length=255)
    precio_objetivo = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_ultima_notificacion = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Alerta de Precio"
        verbose_name_plural = "Alertas de Precios"
        unique_together = ['producto', 'email']
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Alerta de {self.email} para {self.producto.nombre}"


# MODELOS UNIFICADOS - IDs canónicos como definitivos

class ResenaUnificada(models.Model):
    """Modelo para reseñas usando IDs unificados como definitivos"""
    
    # ID del producto unificado (ej: cb_666f92f1)
    producto_id = models.CharField(max_length=50, db_index=True)
    
    # Información del producto (para evitar lookups)
    producto_nombre = models.CharField(max_length=500)
    producto_marca = models.CharField(max_length=200, blank=True, null=True)
    producto_categoria = models.CharField(max_length=100, blank=True, null=True)
    
    # Usuario y reseña
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resenas_unificadas')
    valoracion = models.SmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comentario = models.TextField()
    nombre_autor = models.CharField(max_length=100, blank=True, null=True)
    
    # Timestamps
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Reseña Unificada"
        verbose_name_plural = "Reseñas Unificadas"
        unique_together = ['producto_id', 'usuario']
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['producto_id', '-fecha_creacion']),
            models.Index(fields=['valoracion']),
        ]
    
    def __str__(self):
        return f"Reseña de {self.nombre_autor or self.usuario.username} para {self.producto_nombre} - {self.valoracion}/5"


class AlertaPrecioUnificada(models.Model):
    """Modelo para alertas de precio usando IDs unificados"""
    
    # ID del producto unificado
    producto_id = models.CharField(max_length=50, db_index=True)
    
    # Información del producto (para evitar lookups)
    producto_nombre = models.CharField(max_length=500)
    producto_marca = models.CharField(max_length=200, blank=True, null=True)
    
    # Email para la alerta
    email = models.EmailField(max_length=255)
    
    # Precio objetivo (opcional)
    precio_objetivo = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Estado
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_ultima_notificacion = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Alerta de Precio Unificada"
        verbose_name_plural = "Alertas de Precios Unificadas"
        unique_together = ['producto_id', 'email']
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Alerta de {self.email} para {self.producto_nombre}"


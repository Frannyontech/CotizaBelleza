from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from .managers import (
    ProductoManager, PrecioProductoManager, CategoriaManager, 
    TiendaManager, ResenaManager
)

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
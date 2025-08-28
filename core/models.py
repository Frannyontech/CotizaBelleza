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


# ============================================================================
# SISTEMA DE IDS PERSISTENTES
# ============================================================================

import hashlib
import uuid


class ProductoPersistente(models.Model):
    """
    Modelo principal de productos con IDs persistentes
    Un producto mantiene su internal_id aunque cambien precios/stock
    """
    
    # ID interno persistente (ej: cb_abc123def)
    internal_id = models.CharField(max_length=50, unique=True, db_index=True)
    
    # Campos para identificación única
    nombre_normalizado = models.CharField(max_length=500, db_index=True)
    marca = models.CharField(max_length=200, db_index=True)
    categoria = models.CharField(max_length=100, db_index=True)
    
    # Hash único para deduplicación
    hash_unico = models.CharField(max_length=64, unique=True, db_index=True)
    
    # Información del producto
    nombre_original = models.CharField(max_length=500)
    descripcion = models.TextField(blank=True, null=True)
    imagen_url = models.URLField(max_length=500, blank=True, null=True)
    
    # Metadatos
    primera_aparicion = models.DateTimeField(auto_now_add=True)
    ultima_actualizacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)
    
    # Estadísticas
    veces_encontrado = models.PositiveIntegerField(default=1)
    
    class Meta:
        verbose_name = "Producto Persistente"
        verbose_name_plural = "Productos Persistentes"
        ordering = ['-ultima_actualizacion']
        indexes = [
            models.Index(fields=['internal_id']),
            models.Index(fields=['hash_unico']),
            models.Index(fields=['marca', 'categoria']),
            models.Index(fields=['nombre_normalizado']),
        ]
    
    def __str__(self):
        return f"{self.internal_id}: {self.nombre_original} - {self.marca}"
    
    @classmethod
    def generar_internal_id(cls):
        """Genera un internal_id único con prefijo cb_"""
        return f"cb_{uuid.uuid4().hex[:8]}"
    
    @classmethod
    def generar_hash_unico(cls, nombre_normalizado, marca, categoria):
        """Genera hash único para deduplicación"""
        contenido = f"{nombre_normalizado.lower()}|{marca.lower()}|{categoria.lower()}"
        return hashlib.sha256(contenido.encode('utf-8')).hexdigest()
    
    def actualizar_aparicion(self):
        """Incrementa contador de apariciones"""
        from django.utils import timezone
        self.veces_encontrado += 1
        self.ultima_actualizacion = timezone.now()
        self.save(update_fields=['veces_encontrado', 'ultima_actualizacion'])


class PrecioHistorico(models.Model):
    """
    Historial de precios por tienda para cada producto persistente
    """
    
    # Relación con producto persistente
    producto = models.ForeignKey(
        ProductoPersistente, 
        on_delete=models.CASCADE, 
        related_name='precios_historicos'
    )
    
    # Información de precio
    tienda = models.CharField(max_length=100, db_index=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    precio_original = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tiene_descuento = models.BooleanField(default=False)
    
    # Estado del producto
    stock = models.BooleanField(default=True)
    disponible = models.BooleanField(default=True)
    
    # URLs y metadatos
    url_producto = models.URLField(max_length=500, blank=True, null=True)
    imagen_url = models.URLField(max_length=500, blank=True, null=True)
    
    # Timestamps
    fecha_extraccion = models.DateTimeField(auto_now_add=True)
    fecha_scraping = models.DateTimeField()  # Fecha del scraping que lo generó
    
    # Información adicional del scraping
    fuente_scraping = models.CharField(max_length=100)  # ej: "etl_2025_01_15"
    
    class Meta:
        verbose_name = "Precio Histórico"
        verbose_name_plural = "Precios Históricos"
        ordering = ['-fecha_extraccion']
        indexes = [
            models.Index(fields=['producto', '-fecha_extraccion']),
            models.Index(fields=['tienda', '-fecha_extraccion']),
            models.Index(fields=['fecha_scraping']),
            models.Index(fields=['stock', 'disponible']),
        ]
        
        # Un producto solo puede tener un precio por tienda por fecha de scraping
        unique_together = ['producto', 'tienda', 'fecha_scraping']
    
    def __str__(self):
        return f"{self.producto.internal_id} - {self.tienda}: ${self.precio} ({self.fecha_extraccion.date()})"
    
    @property
    def porcentaje_descuento(self):
        """Calcula porcentaje de descuento si existe precio original"""
        if self.precio_original and self.precio_original > self.precio:
            return round(((self.precio_original - self.precio) / self.precio_original) * 100, 1)
        return 0


class ResenaProductoPersistente(models.Model):
    """
    Reseñas vinculadas a productos persistentes
    """
    
    # Relación con producto persistente
    producto = models.ForeignKey(
        ProductoPersistente, 
        on_delete=models.CASCADE, 
        related_name='resenas'
    )
    
    # Usuario y reseña
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resenas_productos_persistentes')
    valoracion = models.SmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comentario = models.TextField()
    nombre_autor = models.CharField(max_length=100, blank=True, null=True)
    
    # Timestamps
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Metadatos
    verificada = models.BooleanField(default=False)
    activa = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Reseña de Producto Persistente"
        verbose_name_plural = "Reseñas de Productos Persistentes"
        unique_together = ['producto', 'usuario']
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['producto', '-fecha_creacion']),
            models.Index(fields=['valoracion']),
            models.Index(fields=['verificada', 'activa']),
        ]
    
    def __str__(self):
        autor = self.nombre_autor or self.usuario.username
        return f"Reseña de {autor} para {self.producto.nombre_original} - {self.valoracion}/5"


class AlertaPrecioProductoPersistente(models.Model):
    """Alerta de precio para un producto específico"""
    producto = models.ForeignKey(ProductoPersistente, on_delete=models.CASCADE, related_name='alertas_precio')
    email = models.EmailField(max_length=255)  # Email del usuario (requerido)
    precio_inicial = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Precio al crear alerta
    activa = models.BooleanField(default=True)
    notificada = models.BooleanField(default=False)  # Para evitar duplicados
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_activacion = models.DateTimeField(auto_now_add=True)  # Fecha cuando se activa la alerta
    fecha_fin = models.DateTimeField(null=True, blank=True)  # 1 semana después
    fecha_ultima_notificacion = models.DateTimeField(null=True, blank=True)
    ultima_revision = models.DateTimeField(null=True, blank=True)
    notificaciones_enviadas = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['producto', 'email']  # Una alerta por producto por email
        verbose_name = 'Alerta de Precio'
        verbose_name_plural = 'Alertas de Precio'
    
    def save(self, *args, **kwargs):
        if not self.fecha_fin:
            # Calcular fecha de fin (1 semana después)
            from django.utils import timezone
            from datetime import timedelta
            self.fecha_fin = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Alerta {self.id}: {self.producto.nombre_original} - ${self.precio_inicial}"
    
    def get_user_email(self):
        """Obtener email del usuario"""
        return self.email
    
    def esta_activa(self):
        """Verifica si la alerta está dentro del período de 1 semana"""
        from django.utils import timezone
        return self.activa and timezone.now() <= self.fecha_fin
    
    def dias_restantes(self):
        """Calcula días restantes de la alerta"""
        from django.utils import timezone
        if self.fecha_fin:
            delta = self.fecha_fin - timezone.now()
            return max(0, delta.days)
        return 0


class MailLog(models.Model):
    """Registro de emails enviados"""
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('sent', 'Enviado'),
        ('failed', 'Fallido'),
        ('cancelled', 'Cancelado'),
    ]
    
    alerta = models.ForeignKey(AlertaPrecioProductoPersistente, on_delete=models.CASCADE, related_name='mail_logs')
    producto = models.ForeignKey(ProductoPersistente, on_delete=models.CASCADE, related_name='mail_logs')
    user_email = models.EmailField()
    precio_actual = models.DecimalField(max_digits=10, decimal_places=2)
    precio_objetivo = models.DecimalField(max_digits=10, decimal_places=2)
    tienda_url = models.URLField(max_length=500, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(auto_now_add=True)
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = 'Log de Email'
        verbose_name_plural = 'Logs de Email'
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"Mail {self.id}: {self.user_email} - {self.producto.nombre_original}"


class EmailTemplate(models.Model):
    """Plantillas de email para diferentes tipos de notificaciones"""
    name = models.CharField(max_length=100, unique=True)
    subject = models.CharField(max_length=200)
    html_content = models.TextField()
    text_content = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Plantilla de Email'
        verbose_name_plural = 'Plantillas de Email'
    
    def __str__(self):
        return self.name


class EstadisticaProducto(models.Model):
    """
    Estadísticas agregadas por producto para optimizar consultas
    """
    
    producto = models.OneToOneField(
        ProductoPersistente, 
        on_delete=models.CASCADE, 
        related_name='estadisticas'
    )
    
    # Estadísticas de precios
    precio_min_actual = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    precio_max_actual = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    precio_promedio = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    
    # Estadísticas de tiendas
    num_tiendas_disponible = models.PositiveIntegerField(default=0)
    tiendas_con_stock = models.PositiveIntegerField(default=0)
    
    # Estadísticas de reseñas
    num_resenas = models.PositiveIntegerField(default=0)
    valoracion_promedio = models.DecimalField(max_digits=3, decimal_places=2, null=True)
    
    # Estadísticas de alertas
    num_alertas_activas = models.PositiveIntegerField(default=0)
    
    # Última actualización
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Estadística de Producto"
        verbose_name_plural = "Estadísticas de Productos"
    
    def actualizar_estadisticas(self):
        """Recalcula todas las estadísticas del producto"""
        from django.db.models import Min, Max, Avg, Count
        
        # Estadísticas de precios actuales (stock disponible)
        precios_actuales = self.producto.precios_historicos.filter(
            stock=True, 
            disponible=True
        ).values_list('precio', flat=True)
        
        if precios_actuales:
            self.precio_min_actual = min(precios_actuales)
            self.precio_max_actual = max(precios_actuales)
            self.precio_promedio = sum(precios_actuales) / len(precios_actuales)
        else:
            self.precio_min_actual = None
            self.precio_max_actual = None
            self.precio_promedio = None
        
        # Estadísticas de tiendas
        tiendas_stats = self.producto.precios_historicos.aggregate(
            total=Count('tienda', distinct=True),
            con_stock=Count('tienda', distinct=True, filter=models.Q(stock=True, disponible=True))
        )
        self.num_tiendas_disponible = tiendas_stats['total'] or 0
        self.tiendas_con_stock = tiendas_stats['con_stock'] or 0
        
        # Estadísticas de reseñas
        resenas_stats = self.producto.resenas.filter(activa=True).aggregate(
            total=Count('id'),
            promedio=Avg('valoracion')
        )
        self.num_resenas = resenas_stats['total'] or 0
        self.valoracion_promedio = resenas_stats['promedio']
        
        # Estadísticas de alertas
        self.num_alertas_activas = self.producto.alertas_precio.filter(activa=True).count()
        
        self.save()
        return self


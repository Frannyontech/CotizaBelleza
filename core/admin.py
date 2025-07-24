from django.contrib import admin
from .models import (
    Categoria, Tienda, Producto, ProductoTienda, 
    PrecioProducto, Resena, Alerta, AlertaUsuario
)

# Register your models here.

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre']
    search_fields = ['nombre']
    ordering = ['nombre']

@admin.register(Tienda)
class TiendaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'url_website']
    search_fields = ['nombre']
    ordering = ['nombre']

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'marca', 'categoria']
    list_filter = ['categoria', 'marca']
    search_fields = ['nombre', 'marca', 'descripcion']
    ordering = ['nombre']
    autocomplete_fields = ['categoria']

@admin.register(ProductoTienda)
class ProductoTiendaAdmin(admin.ModelAdmin):
    list_display = ['producto', 'tienda']
    list_filter = ['tienda', 'producto__categoria']
    search_fields = ['producto__nombre', 'tienda__nombre']
    ordering = ['producto__nombre', 'tienda__nombre']
    autocomplete_fields = ['producto', 'tienda']

@admin.register(PrecioProducto)
class PrecioProductoAdmin(admin.ModelAdmin):
    list_display = ['producto', 'tienda', 'precio', 'stock', 'fecha_extraccion']
    list_filter = ['stock', 'fecha_extraccion', 'tienda', 'producto__categoria']
    search_fields = ['producto__nombre', 'tienda__nombre']
    ordering = ['-fecha_extraccion']
    autocomplete_fields = ['producto', 'tienda']

@admin.register(Resena)
class ResenaAdmin(admin.ModelAdmin):
    list_display = ['producto', 'usuario', 'valoracion', 'fecha_creacion']
    list_filter = ['valoracion', 'fecha_creacion', 'producto__categoria']
    search_fields = ['producto__nombre', 'usuario__username', 'comentario']
    ordering = ['-fecha_creacion']
    autocomplete_fields = ['producto', 'usuario']

@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ['id', 'fecha_notificacion', 'fecha_creacion']
    list_filter = ['fecha_notificacion', 'fecha_creacion']
    ordering = ['-fecha_creacion']

@admin.register(AlertaUsuario)
class AlertaUsuarioAdmin(admin.ModelAdmin):
    list_display = ['producto', 'usuario', 'alerta', 'alerta_activa']
    list_filter = ['alerta_activa', 'alerta__fecha_creacion', 'producto__categoria']
    search_fields = ['producto__nombre', 'usuario__username']
    ordering = ['-alerta__fecha_creacion']
    autocomplete_fields = ['producto', 'usuario']

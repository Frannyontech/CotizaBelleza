from django.contrib import admin
from .models import (
    Categoria, Tienda, Producto, 
    PrecioProducto, Resena, AlertaPrecio,
    ResenaUnificada, AlertaPrecioUnificada
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

@admin.register(AlertaPrecio)
class AlertaPrecioAdmin(admin.ModelAdmin):
    list_display = ['producto', 'email', 'precio_objetivo', 'activa', 'fecha_creacion']
    list_filter = ['activa', 'fecha_creacion', 'producto__categoria']
    search_fields = ['producto__nombre', 'email']
    ordering = ['-fecha_creacion']
    autocomplete_fields = ['producto']

@admin.register(ResenaUnificada)
class ResenaUnificadaAdmin(admin.ModelAdmin):
    list_display = ['producto_id', 'producto_nombre', 'usuario', 'valoracion', 'fecha_creacion']
    list_filter = ['valoracion', 'fecha_creacion', 'producto_categoria']
    search_fields = ['producto_nombre', 'usuario__username', 'comentario', 'producto_id']
    ordering = ['-fecha_creacion']
    autocomplete_fields = ['usuario']

@admin.register(AlertaPrecioUnificada)
class AlertaPrecioUnificadaAdmin(admin.ModelAdmin):
    list_display = ['producto_id', 'producto_nombre', 'email', 'precio_objetivo', 'activa', 'fecha_creacion']
    list_filter = ['activa', 'fecha_creacion']
    search_fields = ['producto_nombre', 'email', 'producto_id']
    ordering = ['-fecha_creacion']
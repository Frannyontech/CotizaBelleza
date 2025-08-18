"""
Controladores - Capa de lógica de negocio en el patrón MVC
Contiene la lógica de negocio separada de las vistas
"""
from django.db.models import Min, Max, Count, Avg
from django.contrib.auth.models import User
from .models import Producto, PrecioProducto, Categoria, Tienda, AlertaPrecio, Resena
from .serializers import (
    ProductoSerializer, PrecioProductoSerializer, 
    CategoriaSerializer, TiendaSerializer, AlertaPrecioSerializer, ResenaSerializer
)
import json
import os
from django.conf import settings


class DashboardController:
    """Controlador para lógica de dashboard"""
    
    @staticmethod
    def get_estadisticas():
        """Obtiene estadísticas generales del sistema"""
        total_productos = Producto.objects.count()
        total_categorias = Categoria.objects.count()
        total_tiendas = Tienda.objects.count()
        
        # Usar manager personalizado para estadísticas de precios
        estadisticas_precios = PrecioProducto.objects.estadisticas_generales()
        
        return {
            'total_productos': total_productos,
            'productos_con_precios': estadisticas_precios['total_productos_con_precio'],
            'total_categorias': total_categorias,
            'total_tiendas': total_tiendas,
            'precio_promedio': float(estadisticas_precios['precio_promedio']),
            'precio_min': float(estadisticas_precios['precio_min']),
            'precio_max': float(estadisticas_precios['precio_max'])
        }
    
    @staticmethod
    def get_productos_por_categoria():
        """Obtiene productos agrupados por categoría"""
        return list(Categoria.objects.con_estadisticas().values('nombre', 'cantidad_productos'))
    
    @staticmethod
    def get_productos_populares(limit=8):
        """Obtiene productos más populares con información detallada"""
        productos_populares = Producto.objects.populares(limit)
        productos_data = []
        
        for producto in productos_populares:
            precio_min = producto.get_precio_min()
            if precio_min:
                productos_data.append({
                    'id': producto.id,
                    'nombre': producto.nombre,
                    'marca': producto.marca or '',
                    'categoria': producto.categoria.nombre,
                    'precio_min': float(precio_min),
                    'tiendas_disponibles': producto.get_tiendas_disponibles(),
                    'imagen_url': producto.imagen_url or '',
                    'num_precios': producto.num_precios
                })
        
        return productos_data


class ProductoController:
    """Controlador para lógica de productos"""
    
    @staticmethod
    def buscar_productos(categoria_id=None, tienda_id=None, search=None, limit=50):
        """Busca productos con filtros aplicados"""
        productos = Producto.objects.all()
        
        if categoria_id:
            productos = productos.filter(categoria_id=categoria_id)
        
        if search:
            productos = productos.buscar(search)
        
        if tienda_id:
            productos = productos.por_tienda_id(tienda_id)
        
        # Obtener productos con precios
        productos_data = []
        for producto in productos[:limit]:
            precio_min = producto.get_precio_min()
            if precio_min:
                productos_data.append({
                    'id': producto.id,
                    'nombre': producto.nombre,
                    'marca': producto.marca or '',
                    'categoria': producto.categoria.nombre,
                    'precio_min': float(precio_min),
                    'tiendas_disponibles': producto.get_tiendas_disponibles(),
                    'imagen_url': producto.imagen_url or '',
                    'descripcion': producto.descripcion or ''
                })
        
        return productos_data
    
    @staticmethod
    def get_producto_detalle(producto_id):
        """Obtiene detalles completos de un producto"""
        try:
            producto = Producto.objects.get(id=producto_id)
            
            precios_producto = PrecioProducto.objects.filter(
                producto=producto,
                stock=True
            ).select_related('tienda')
            
            precio_min = producto.get_precio_min()
            precio_max = producto.get_precio_max()
            
            # Información detallada de tiendas
            tiendas_detalladas = []
            for precio in precios_producto:
                tiendas_detalladas.append({
                    'nombre': precio.tienda.nombre,
                    'precio': float(precio.precio),
                    'stock': precio.stock,
                    'url_producto': precio.url_producto or '',
                    'fecha_extraccion': precio.fecha_extraccion.isoformat()
                })
            
            stock_disponible = precios_producto.filter(stock=True).exists()
            
            return {
                'id': producto.id,
                'nombre': producto.nombre,
                'marca': producto.marca or '',
                'categoria': producto.categoria.nombre if producto.categoria else '',
                'descripcion': producto.descripcion or '',
                'precio': float(precio_min) if precio_min else 0,
                'precio_min': float(precio_min) if precio_min else 0,
                'precio_max': float(precio_max) if precio_max else 0,
                'precio_original': float(precio_max) if precio_max else 0,
                'stock': 'In stock' if stock_disponible else 'Out of stock',
                'url': precios_producto.first().url_producto if precios_producto.exists() else '',
                'imagen_url': producto.imagen_url or '',
                'tiendas_disponibles': producto.get_tiendas_disponibles(),
                'tiendas_detalladas': tiendas_detalladas,
                'num_precios': precios_producto.count()
            }
        except Producto.DoesNotExist:
            return None
    
    @staticmethod
    def get_productos_por_tienda(tienda_nombre, categoria_nombre=None, search=None, marca=None):
        """Obtiene productos de una tienda específica"""
        productos = Producto.objects.por_tienda(tienda_nombre)
        
        if categoria_nombre:
            productos = productos.filter(categoria__nombre=categoria_nombre)
        
        if search:
            productos = productos.buscar(search)
        
        if marca:
            productos = productos.filter(marca__icontains=marca)
        
        productos_data = []
        seen_products = set()  # Para evitar duplicados
        
        for producto in productos:
            precio_tienda = PrecioProducto.objects.filter(
                producto=producto,
                tienda__nombre=tienda_nombre,
                stock=True
            ).first()
            
            if precio_tienda:
                # Crear clave única para evitar duplicados
                product_key = f"{producto.nombre}_{producto.marca}_{precio_tienda.precio}"
                
                if product_key not in seen_products:
                    seen_products.add(product_key)
                    
                    productos_data.append({
                        'id': producto.id,
                        'nombre': producto.nombre,
                        'marca': producto.marca or '',
                        'categoria': producto.categoria.nombre,
                        'precio': float(precio_tienda.precio),
                        'stock': precio_tienda.stock,
                        'url_producto': precio_tienda.url_producto or '',
                        'imagen_url': producto.imagen_url or '',
                        'descripcion': producto.descripcion or '',
                        'fecha_extraccion': precio_tienda.fecha_extraccion.isoformat(),
                        'tienda': tienda_nombre
                    })
        
        # Ordenar por precio
        productos_data.sort(key=lambda x: x['precio'])
        
        # Obtener categorías disponibles para la tienda
        categorias_disponibles = list(
            Categoria.objects.filter(
                productos__precios__tienda__nombre=tienda_nombre
            ).distinct().values_list('nombre', flat=True)
        )
        
        return {
            'productos': productos_data,
            'total': len(productos_data),
            'categorias_disponibles': categorias_disponibles,
            'tienda': tienda_nombre
        }


class CategoriaController:
    """Controlador para lógica de categorías"""
    
    @staticmethod
    def get_categorias_con_estadisticas():
        """Obtiene todas las categorías con estadísticas"""
        return list(Categoria.objects.con_estadisticas().values('id', 'nombre', 'cantidad_productos'))


class TiendaController:
    """Controlador para lógica de tiendas"""
    
    @staticmethod
    def get_tiendas_con_estadisticas():
        """Obtiene todas las tiendas con estadísticas"""
        return list(Tienda.objects.con_estadisticas().values('id', 'nombre', 'url_website', 'cantidad_productos'))


class PrecioController:
    """Controlador para lógica de precios"""
    
    @staticmethod
    def get_precios_por_producto(producto_id):
        """Obtiene todos los precios de un producto"""
        precios = PrecioProducto.objects.filter(
            producto_id=producto_id,
            stock=True
        ).select_related('tienda')
        
        precios_data = []
        for precio in precios:
            precios_data.append({
                'id': precio.id,
                'tienda': precio.tienda.nombre,
                'precio': float(precio.precio),
                'stock': precio.stock,
                'url_producto': precio.url_producto or '',
                'fecha_extraccion': precio.fecha_extraccion.isoformat()
            })
        
        return precios_data


class UsuarioController:
    """Controlador para lógica de usuarios"""
    
    @staticmethod
    def crear_usuario(username, email, password):
        """Crea un nuevo usuario con validaciones"""
        # Validaciones
        if User.objects.filter(username=username).exists():
            raise ValueError("El nombre de usuario ya existe")
        
        if email and User.objects.filter(email=email).exists():
            raise ValueError("El email ya está registrado")
        
        # Crear usuario
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        return user


class AlertaController:
    """Controlador para lógica de alertas"""
    
    @staticmethod
    def crear_alerta_precio(producto_id, email):
        """Crea una alerta de precio"""
        # Verificar que el producto existe
        try:
            producto = Producto.objects.get(id=producto_id)
        except Producto.DoesNotExist:
            raise ValueError("Producto no encontrado")
        
        # Verificar si ya existe una alerta
        if AlertaPrecio.objects.filter(producto=producto, email=email).exists():
            raise ValueError("Ya existe una alerta para este email y producto")
        
        # Crear la alerta
        alerta = AlertaPrecio.objects.create(
            producto=producto,
            email=email
        )
        return alerta


class ResenaController:
    """Controlador para lógica de reseñas"""
    
    @staticmethod
    def get_resenas_producto(producto_id):
        """Obtiene reseñas de un producto con estadísticas"""
        try:
            producto = Producto.objects.get(id=producto_id)
        except Producto.DoesNotExist:
            raise ValueError("Producto no encontrado")
        
        # Obtener reseñas usando manager personalizado
        resenas = Resena.objects.por_producto(producto_id)
        estadisticas = Resena.objects.estadisticas_producto(producto_id)
        
        # Reseñas recientes para vista de detalle
        resenas_recientes = Resena.objects.por_producto(producto_id).recientes()
        
        return {
            "producto_id": producto_id,
            "total_resenas": estadisticas['total_resenas'],
            "promedio_valoracion": estadisticas['promedio_valoracion'],
            "resenas_recientes": ResenaSerializer(resenas_recientes, many=True).data,
            "todas_resenas": ResenaSerializer(resenas, many=True).data
        }
    
    @staticmethod
    def crear_resena(producto_id, valoracion, comentario, autor=None):
        """Crea una nueva reseña"""
        try:
            producto = Producto.objects.get(id=producto_id)
        except Producto.DoesNotExist:
            raise ValueError("Producto no encontrado")
        
        # Validaciones
        if not (1 <= valoracion <= 5):
            raise ValueError("La valoración debe estar entre 1 y 5")
        
        if len(comentario.strip()) < 10:
            raise ValueError("El comentario debe tener al menos 10 caracteres")
        
        # Crear usuario temporal
        if not autor:
            username = f'anonimo_{producto_id}_{len(comentario)}'
        else:
            username = f'temp_{autor.replace(" ", "_").lower()}_{producto_id}'
        
        usuario, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': autor.split(' ')[0] if autor and ' ' in autor else (autor or 'Usuario'),
                'last_name': ' '.join(autor.split(' ')[1:]) if autor and ' ' in autor else '',
                'email': f'{username}@example.com'
            }
        )
        
        # Verificar si ya existe una reseña
        if Resena.objects.filter(producto=producto, usuario=usuario).exists():
            raise ValueError("Ya has escrito una reseña para este producto")
        
        # Crear la reseña
        resena = Resena.objects.create(
            producto=producto,
            usuario=usuario,
            valoracion=valoracion,
            comentario=comentario.strip(),
            nombre_autor=autor
        )
        
        return resena


class UnifiedDataController:
    """Controlador para datos unificados del procesador"""
    
    @staticmethod
    def load_unified_products():
        """Cargar productos unificados desde el archivo JSON"""
        try:
            possible_paths = [
                os.path.join(settings.BASE_DIR, 'data', 'processed', 'unified_products.json'),
            ]
            
            for json_path in possible_paths:
                if os.path.exists(json_path):
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Handle both array format and object format
                        if isinstance(data, list):
                            return {"productos": data}
                        elif isinstance(data, dict) and "productos" in data:
                            return data
                        else:
                            return {"productos": []}
            
            return {"productos": []}
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ValueError(f"Error loading unified products: {e}")
    
    @staticmethod
    def get_unified_dashboard():
        """Obtiene datos de dashboard desde productos unificados"""
        unified_data = UnifiedDataController.load_unified_products()
        productos = unified_data.get("productos", [])
        
        # Estadísticas básicas
        total_productos = len(productos)
        tiendas_disponibles = set()
        categorias_disponibles = set()
        
        for producto in productos:
            # Extract stores from tiendas array
            tiendas_producto = producto.get('tiendas', [])
            for tienda in tiendas_producto:
                if tienda.get('fuente'):
                    tiendas_disponibles.add(tienda['fuente'])
            
            if producto.get('categoria'):
                categorias_disponibles.add(producto['categoria'])
        
        # Productos populares (primeros para simplificar)
        productos_populares = productos[:10]
        
        return {
            'estadisticas': {
                'total_productos': total_productos,
                'total_tiendas': len(tiendas_disponibles),
                'total_categorias': len(categorias_disponibles),
            },
            'productos_populares': productos_populares,
            'tiendas_disponibles': list(tiendas_disponibles),
            'categorias_disponibles': list(categorias_disponibles)
        }


class UtilController:
    """Controlador para utilidades y funciones helper"""
    
    @staticmethod
    def find_product_by_id(producto_id):
        """Helper function to find numeric product ID from various formats"""
        try:
            # If it's already numeric, return as-is
            if str(producto_id).isdigit():
                return int(producto_id)
            
            # If it contains underscores (e.g., "dbs_123"), extract the numeric part
            if '_' in str(producto_id):
                parts = str(producto_id).split('_')
                for part in parts:
                    if part.isdigit():
                        return int(part)
            
            # If it contains hyphens (canonical format), try to extract numeric part
            if '-' in str(producto_id):
                parts = str(producto_id).split('-')
                for part in parts:
                    if part.isdigit():
                        return int(part)
            
            return None
        except (ValueError, TypeError):
            return None

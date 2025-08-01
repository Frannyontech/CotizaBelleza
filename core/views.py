from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db.models import Min, Max, Count, Avg
from .models import Producto, PrecioProducto, Categoria, Tienda
from .serializers import (
    ProductoSerializer, PrecioProductoSerializer, 
    UserSerializer, CategoriaSerializer, TiendaSerializer
)


def home(request):
    return HttpResponse("<h1>¡Bienvenido a CotizaBelleza!</h1><p>El proyecto Django creado por Francisca Galaz está funcionando correctamente.</p>")

class DashboardAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """API para obtener datos del dashboard"""
        try:
            # Estadísticas generales
            total_productos = Producto.objects.count()
            total_categorias = Categoria.objects.count()
            total_tiendas = Tienda.objects.count()
            
            # Productos con precios
            productos_con_precios = PrecioProducto.objects.filter(
                stock=True
            ).values('producto').distinct().count()
            
            # Precio promedio
            precio_promedio = PrecioProducto.objects.filter(
                stock=True
            ).aggregate(Avg('precio'))['precio__avg'] or 0
            
            # Rango de precios
            precios = PrecioProducto.objects.filter(stock=True)
            precio_min = precios.aggregate(Min('precio'))['precio__min'] or 0
            precio_max = precios.aggregate(Max('precio'))['precio__max'] or 0
            
            # Productos por categoría
            productos_por_categoria = Categoria.objects.annotate(
                cantidad_productos=Count('productos')
            ).values('nombre', 'cantidad_productos')
            
            # Productos populares (con más precios)
            productos_populares = Producto.objects.annotate(
                num_precios=Count('precios')
            ).filter(
                num_precios__gt=0
            ).order_by('-num_precios')[:8]
            
            # Serializar productos populares con sus precios
            productos_populares_data = []
            for producto in productos_populares:
                precios_producto = PrecioProducto.objects.filter(
                    producto=producto,
                    stock=True
                ).select_related('tienda')
                
                if precios_producto.exists():
                    precio_min_producto = precios_producto.aggregate(Min('precio'))['precio__min']
                    tiendas_disponibles = [p.tienda.nombre for p in precios_producto]
                    
                    productos_populares_data.append({
                        'id': producto.id,
                        'nombre': producto.nombre,
                        'marca': producto.marca or '',
                        'categoria': producto.categoria.nombre,
                        'precio_min': float(precio_min_producto),
                        'tiendas_disponibles': tiendas_disponibles,
                        'imagen_url': producto.imagen_url or '',
                        'num_precios': producto.num_precios
                    })
            
            return Response({
                'estadisticas': {
                    'total_productos': total_productos,
                    'productos_con_precios': productos_con_precios,
                    'total_categorias': total_categorias,
                    'total_tiendas': total_tiendas,
                    'precio_promedio': float(precio_promedio),
                    'precio_min': float(precio_min),
                    'precio_max': float(precio_max)
                },
                'productos_por_categoria': list(productos_por_categoria),
                'productos_populares': productos_populares_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Error al obtener datos del dashboard: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ProductoListAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        categoria_id = request.query_params.get('categoria')
        tienda_id = request.query_params.get('tienda')
        search = request.query_params.get('search', '')
        
        productos = Producto.objects.all()
        
        # Filtrar por categoría
        if categoria_id:
            try:
                productos = productos.filter(categoria_id=categoria_id)
            except ValueError:
                return Response(
                    {"error": "ID de categoría inválido"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Filtrar por búsqueda
        if search:
            productos = productos.filter(nombre__icontains=search)
        
        # Filtrar por tienda
        if tienda_id:
            productos = productos.filter(precios__tienda_id=tienda_id)
        
        # Incluir información de precios
        productos_data = []
        for producto in productos[:50]:  # Limitar a 50 productos
            precios = PrecioProducto.objects.filter(
                producto=producto,
                stock=True
            ).select_related('tienda')
            
            if precios.exists():
                precio_min = precios.aggregate(Min('precio'))['precio__min']
                tiendas = [p.tienda.nombre for p in precios]
                
                productos_data.append({
                    'id': producto.id,
                    'nombre': producto.nombre,
                    'marca': producto.marca or '',
                    'categoria': producto.categoria.nombre,
                    'precio_min': float(precio_min),
                    'tiendas_disponibles': tiendas,
                    'imagen_url': producto.imagen_url or '',
                    'descripcion': producto.descripcion or ''
                })
        
        return Response(productos_data, status=status.HTTP_200_OK)

class CategoriaListAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        categorias = Categoria.objects.annotate(
            cantidad_productos=Count('productos')
        ).values('id', 'nombre', 'cantidad_productos')
        
        return Response(list(categorias), status=status.HTTP_200_OK)

class TiendaListAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        tiendas = Tienda.objects.annotate(
            cantidad_productos=Count('productos_tienda')
        ).values('id', 'nombre', 'url_website', 'cantidad_productos')
        
        return Response(list(tiendas), status=status.HTTP_200_OK)

class PreciosPorProductoAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        producto_id = request.query_params.get('producto')
        
        if not producto_id:
            return Response(
                {"error": "Se requiere el parámetro 'producto'"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
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
            
            return Response(precios_data, status=status.HTTP_200_OK)
        except ValueError:
            return Response(
                {"error": "ID de producto inválido"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class UsuarioCreateAPIView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        
        if serializer.is_valid():
            username = serializer.validated_data.get('username')
            email = serializer.validated_data.get('email')
            
            if User.objects.filter(username=username).exists():
                return Response(
                    {"error": "El nombre de usuario ya existe"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if email and User.objects.filter(email=email).exists():
                return Response(
                    {"error": "El email ya está registrado"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user = serializer.save()
            return Response(
                {
                    "message": "Usuario creado exitosamente",
                    "user": UserSerializer(user).data
                }, 
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

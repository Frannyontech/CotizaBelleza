"""
Vistas MVT - Capa de presentación limpia que delega lógica a servicios
"""
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db.models import Min, Max, Count, Avg

from .models import Producto, PrecioProducto, Categoria, Tienda, AlertaPrecio, Resena, ResenaUnificada
from .serializers import (
    ProductoSerializer, PrecioProductoSerializer, 
    UserSerializer, CategoriaSerializer, TiendaSerializer, AlertaPrecioSerializer, ResenaSerializer
)
from .services import (
    DashboardService, ProductoService, CategoriaService,
    TiendaService, PrecioService, UsuarioService,
    AlertaService, ResenaService, UnifiedDataService,
    ETLService, DataIntegrationService
)
import json
import os
from django.conf import settings


def home(request):
    """Vista simple de bienvenida"""
    return HttpResponse(
        "<h1>¡Bienvenido a CotizaBelleza!</h1>"
        "<p>Sistema de cotizaciones con arquitectura MVT + ETL</p>"
    )


class DashboardAPIView(APIView):
    """Vista para dashboard - Delega toda la lógica al servicio"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            dashboard_data = DashboardService.get_estadisticas()
            productos_populares = DashboardService.get_productos_populares()
            productos_por_categoria = DashboardService.get_productos_por_categoria()
            tiendas_disponibles = DashboardService.get_tiendas_disponibles()
            categorias_disponibles = DashboardService.get_categorias_disponibles()
            
            return Response({
                'estadisticas': dashboard_data,
                'productos_populares': productos_populares,
                'productos_por_categoria': productos_por_categoria,
                'tiendas_disponibles': tiendas_disponibles,
                'categorias_disponibles': categorias_disponibles
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Error al obtener datos del dashboard: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProductoListAPIView(APIView):
    """Vista para listado de productos"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            categoria_id = request.GET.get('categoria')
            tienda_id = request.GET.get('tienda')
            search = request.GET.get('search')
            limit = int(request.GET.get('limit', 50))
            
            productos = ProductoService.buscar_productos(
                categoria_id=categoria_id,
                tienda_id=tienda_id,
                search=search,
                limit=limit
            )
            
            return Response({
                'productos': productos,
                'total': len(productos)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Error al buscar productos: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CategoriaListAPIView(APIView):
    """Vista para listado de categorías"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            categorias = CategoriaService.get_categorias_con_estadisticas()
            return Response(categorias, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Error al obtener categorías: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TiendaListAPIView(APIView):
    """Vista para listado de tiendas"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            tiendas = TiendaService.get_tiendas_con_estadisticas()
            return Response(tiendas, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Error al obtener tiendas: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PreciosPorProductoAPIView(APIView):
    """Vista para precios de un producto específico"""
    permission_classes = [AllowAny]
    
    def get(self, request, producto_id):
        try:
            precios = PrecioService.get_precios_por_producto(producto_id)
            return Response(precios, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Error al obtener precios: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProductoDetalleAPIView(APIView):
    """Vista para detalle de producto"""
    permission_classes = [AllowAny]
    
    def get(self, request, producto_id):
        try:
            producto_detalle = ProductoService.get_producto_detalle(producto_id)
            
            if not producto_detalle:
                return Response(
                    {"error": "Producto no encontrado"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(producto_detalle, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Error al obtener detalle del producto: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TiendaProductosAPIView(APIView):
    """Vista para productos de una tienda específica"""
    permission_classes = [AllowAny]
    
    def get(self, request, tienda_nombre):
        try:
            categoria_nombre = request.GET.get('categoria')
            search = request.GET.get('search')
            marca = request.GET.get('marca')
            
            productos_tienda = ProductoService.get_productos_por_tienda(
                tienda_nombre=tienda_nombre,
                categoria_nombre=categoria_nombre,
                search=search,
                marca=marca
            )
            
            return Response(productos_tienda, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Error al obtener productos de la tienda: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TiendaProductoDetalleAPIView(APIView):
    """Vista para detalle de producto en tienda específica"""
    permission_classes = [AllowAny]
    
    def get(self, request, tienda_nombre, producto_id):
        try:
            producto_detalle = ProductoService.get_producto_detalle(producto_id)
            
            if not producto_detalle:
                return Response(
                    {"error": "Producto no encontrado"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Filtrar información específica de la tienda
            tiendas_detalladas = [
                tienda for tienda in producto_detalle.get('tiendas_detalladas', [])
                if tienda['nombre'].lower() == tienda_nombre.lower()
            ]
            
            producto_detalle['tiendas_detalladas'] = tiendas_detalladas
            
            return Response(producto_detalle, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Error al obtener detalle del producto: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UsuarioCreateAPIView(APIView):
    """Vista para crear usuarios"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            username = request.data.get('username')
            email = request.data.get('email')
            password = request.data.get('password')
            
            if not username or not password:
                return Response(
                    {"error": "Se requiere username y password"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user = UsuarioService.crear_usuario(username, email, password)
            user_serializer = UserSerializer(user)
            
            return Response({
                "message": "Usuario creado exitosamente",
                "user": user_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Error al crear usuario: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AlertaPrecioCreateAPIView(APIView):
    """Vista para crear alertas de precio"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            producto_id = request.data.get('producto_id')
            email = request.data.get('email')
            
            if not producto_id or not email:
                return Response(
                    {"error": "Se requiere producto_id y email"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            alerta = AlertaService.crear_alerta_precio(producto_id, email)
            alerta_serializer = AlertaPrecioSerializer(alerta)
            
            return Response({
                "message": "Alerta creada exitosamente",
                "alerta": alerta_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Error al crear la alerta: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProductoResenasAPIView(APIView):
    """Vista para reseñas de productos usando IDs unificados"""
    permission_classes = [AllowAny]
    
    def get(self, request, producto_id):
        try:
            # Verificar si el producto existe en el sistema unificado
            producto_info = _get_product_info_from_unified(producto_id)
            if not producto_info:
                return Response(
                    {"error": "Producto no encontrado"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Obtener reseñas usando el nuevo modelo unificado
            resenas = ResenaUnificada.objects.filter(producto_id=producto_id).order_by('-fecha_creacion')
            
            # Calcular estadísticas
            total_resenas = resenas.count()
            if total_resenas > 0:
                promedio_valoracion = resenas.aggregate(promedio=Avg('valoracion'))['promedio']
                promedio_valoracion = round(promedio_valoracion, 1) if promedio_valoracion else 0
            else:
                promedio_valoracion = 0
            
            # Reseñas recientes (3 más recientes)
            resenas_recientes = resenas[:3]
            
            # Convertir a formato API
            resenas_recientes_data = []
            todas_resenas_data = []
            
            for resena in resenas_recientes:
                resena_data = {
                    'id': resena.id,
                    'usuario': {
                        'id': resena.usuario.id,
                        'username': resena.usuario.username,
                        'first_name': resena.usuario.first_name,
                        'last_name': resena.usuario.last_name
                    },
                    'valoracion': resena.valoracion,
                    'comentario': resena.comentario,
                    'nombre_autor': resena.nombre_autor,
                    'fecha_creacion': resena.fecha_creacion.isoformat()
                }
                resenas_recientes_data.append(resena_data)
            
            for resena in resenas:
                resena_data = {
                    'id': resena.id,
                    'usuario': {
                        'id': resena.usuario.id,
                        'username': resena.usuario.username,
                        'first_name': resena.usuario.first_name,
                        'last_name': resena.usuario.last_name
                    },
                    'valoracion': resena.valoracion,
                    'comentario': resena.comentario,
                    'nombre_autor': resena.nombre_autor,
                    'fecha_creacion': resena.fecha_creacion.isoformat()
                }
                todas_resenas_data.append(resena_data)
            
            return Response({
                "producto_id": producto_id,
                "producto_info": producto_info,
                "total_resenas": total_resenas,
                "promedio_valoracion": promedio_valoracion,
                "resenas_recientes": resenas_recientes_data,
                "todas_resenas": todas_resenas_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Error al obtener las reseñas: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request, producto_id):
        try:
            # Verificar que el producto existe en el sistema unificado
            producto_info = _get_product_info_from_unified(producto_id)
            if not producto_info:
                return Response(
                    {"error": "Producto no encontrado"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Obtener datos de la reseña
            valoracion = request.data.get('valoracion')
            comentario = request.data.get('comentario')
            autor = request.data.get('autor')
            
            # Validaciones básicas
            if not valoracion or not comentario:
                return Response(
                    {"error": "Se requiere valoración y comentario"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not (1 <= valoracion <= 5):
                return Response(
                    {"error": "La valoración debe estar entre 1 y 5"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if len(comentario.strip()) < 10:
                return Response(
                    {"error": "El comentario debe tener al menos 10 caracteres"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Crear usuario temporal
            username = f'temp_{autor.replace(" ", "_").lower()}_{producto_id}' if autor else f'anonimo_{producto_id}_{len(comentario)}'
            
            usuario, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': autor.split(' ')[0] if autor and ' ' in autor else (autor or 'Usuario'),
                    'last_name': ' '.join(autor.split(' ')[1:]) if autor and ' ' in autor else '',
                    'email': f'{username}@example.com'
                }
            )
            
            # Verificar si ya existe una reseña de este usuario para este producto
            if ResenaUnificada.objects.filter(producto_id=producto_id, usuario=usuario).exists():
                return Response(
                    {"error": "Ya has escrito una reseña para este producto"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Crear la reseña en el modelo unificado
            resena = ResenaUnificada.objects.create(
                producto_id=producto_id,
                producto_nombre=producto_info['nombre'],
                producto_marca=producto_info['marca'],
                producto_categoria=producto_info['categoria'],
                usuario=usuario,
                valoracion=valoracion,
                comentario=comentario.strip(),
                nombre_autor=autor
            )
            
            # Crear respuesta
            resena_data = {
                'id': resena.id,
                'producto_id': resena.producto_id,
                'usuario': {
                    'id': resena.usuario.id,
                    'username': resena.usuario.username,
                    'first_name': resena.usuario.first_name,
                    'last_name': resena.usuario.last_name
                },
                'valoracion': resena.valoracion,
                'comentario': resena.comentario,
                'nombre_autor': resena.nombre_autor,
                'fecha_creacion': resena.fecha_creacion.isoformat()
            }
            
            return Response({
                "message": "Reseña creada exitosamente",
                "resena": resena_data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"error": f"Error al crear la reseña: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ETLControlAPIView(APIView):
    """Vista para control del pipeline ETL"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            action = request.data.get('action')
            tienda = request.data.get('tienda')
            categoria = request.data.get('categoria')
            
            if action == 'run_scraper':
                if not tienda:
                    return Response(
                        {"error": "Se requiere especificar la tienda"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                result = ETLService.run_scraper(tienda, categoria)
                return Response(result, status=status.HTTP_200_OK)
            
            elif action == 'run_processor':
                result = ETLService.run_processor()
                return Response(result, status=status.HTTP_200_OK)
            
            elif action == 'run_full_pipeline':
                result = ETLService.run_full_pipeline()
                return Response(result, status=status.HTTP_200_OK)
            
            else:
                return Response(
                    {"error": "Acción no válida"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {"error": f"Error en pipeline ETL: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ETLStatusAPIView(APIView):
    """Vista para obtener el estado del pipeline ETL"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            status_data = ETLService.get_pipeline_status()
            return Response(status_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Error al obtener estado del ETL: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UnifiedProductsAPIView(APIView):
    """Vista para productos unificados"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            unified_data = UnifiedDataService.load_unified_products()
            return Response(unified_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Error al obtener productos unificados: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UnifiedDashboardAPIView(APIView):
    """Vista para dashboard unificado"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            dashboard_data = UnifiedDataService.get_unified_dashboard()
            return Response(dashboard_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Error al obtener dashboard unificado: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

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
        print(f"Error loading unified products: {e}")
        return {"productos": []}


def _get_product_info_from_unified(canonical_id):
    """Helper para obtener información de producto desde unified_products.json"""
    try:
        unified_data = load_unified_products()
        productos = unified_data.get("productos", [])
        
        for producto in productos:
            if producto.get("product_id") == canonical_id:
                return {
                    "id": producto.get("product_id"),
                    "nombre": producto.get("nombre", ""),
                    "marca": producto.get("marca", ""),
                    "categoria": producto.get("categoria", ""),
                    "source": "unified"
                }
        
        return None
    except Exception as e:
        print(f"Error getting product info: {e}")
        return None
"""
Vistas MVC - Capa de presentación limpia que delega lógica a controladores y servicios
"""
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .controllers import (
    DashboardController, ProductoController, CategoriaController,
    TiendaController, PrecioController, UsuarioController,
    AlertaController, ResenaController, UtilController
)
from .services import ETLService, DataIntegrationService, ProductoService


def home(request):
    """Vista simple de bienvenida"""
    return HttpResponse(
        "<h1>¡Bienvenido a CotizaBelleza!</h1>"
        "<p>Sistema de cotizaciones con arquitectura MVC + ETL</p>"
    )


class DashboardAPIView(APIView):
    """Vista para dashboard - Delega toda la lógica al controlador"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            # Usar servicio híbrido que combina BD + archivo unificado
            dashboard_data = ProductoService.get_dashboard_hibrido()
            return Response(dashboard_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Error al obtener datos del dashboard: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProductoListAPIView(APIView):
    """Vista para listado de productos - Delega al controlador"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            # Extraer parámetros
            filtros = {
                'categoria_id': request.query_params.get('categoria'),
                'tienda_id': request.query_params.get('tienda'),
                'search': request.query_params.get('search', ''),
                'limit': 50
            }
            
            # Validar parámetros
            if filtros['categoria_id']:
                try:
                    filtros['categoria_id'] = int(filtros['categoria_id'])
                except ValueError:
                    return Response(
                        {"error": "ID de categoría inválido"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Usar servicio híbrido
            productos_data = ProductoService.get_productos_hibridos(filtros)
            return Response(productos_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Error al obtener productos: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CategoriaListAPIView(APIView):
    """Vista para listado de categorías - Delega al controlador"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            categorias = CategoriaController.get_categorias_con_estadisticas()
            return Response(categorias, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Error al obtener categorías: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TiendaListAPIView(APIView):
    """Vista para listado de tiendas - Delega al controlador"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            tiendas = TiendaController.get_tiendas_con_estadisticas()
            return Response(tiendas, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Error al obtener tiendas: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PreciosPorProductoAPIView(APIView):
    """Vista para precios de producto - Delega al controlador"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        producto_id = request.query_params.get('producto')
        
        if not producto_id:
            return Response(
                {"error": "Se requiere el parámetro 'producto'"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            precios_data = PrecioController.get_precios_por_producto(producto_id)
            return Response(precios_data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Error al obtener precios: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProductoDetalleAPIView(APIView):
    """Vista para detalle de producto - Delega al controlador"""
    permission_classes = [AllowAny]
    
    def get(self, request, producto_id):
        try:
            producto_data = ProductoController.get_producto_detalle(producto_id)
            
            if not producto_data:
                return Response(
                    {"error": "Producto no encontrado"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(producto_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Error al obtener el producto: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TiendaProductosAPIView(APIView):
    """Vista genérica para productos de tienda - Usa parámetro de tienda"""
    permission_classes = [AllowAny]
    
    def get(self, request, tienda_nombre):
        try:
            categoria_nombre = request.query_params.get('categoria', '')
            search = request.query_params.get('search', '')
            marca = request.query_params.get('marca', '')
            
            resultado = ProductoController.get_productos_por_tienda(
                tienda_nombre.upper(), categoria_nombre, search, marca
            )
            
            return Response(resultado, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Error al obtener productos de {tienda_nombre}: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TiendaProductoDetalleAPIView(APIView):
    """Vista genérica para detalle de producto en tienda"""
    permission_classes = [AllowAny]
    
    def get(self, request, tienda_nombre, producto_id):
        try:
            # Usar el controlador general y filtrar por tienda
            producto_data = ProductoController.get_producto_detalle(producto_id)
            
            if not producto_data:
                return Response(
                    {"error": "Producto no encontrado"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Filtrar solo información de la tienda específica
            tienda_upper = tienda_nombre.upper()
            tiendas_filtradas = [
                t for t in producto_data.get('tiendas_detalladas', [])
                if t.get('nombre') == tienda_upper
            ]
            
            if not tiendas_filtradas:
                return Response(
                    {"error": f"Producto no encontrado en {tienda_nombre}"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Adaptar respuesta para la tienda específica
            producto_data.update({
                'tienda': tienda_upper,
                'tiendas_detalladas': tiendas_filtradas,
                'precio': tiendas_filtradas[0].get('precio', 0),
                'stock': tiendas_filtradas[0].get('stock', False),
                'url_producto': tiendas_filtradas[0].get('url_producto', '')
            })
            
            return Response(producto_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Error al obtener producto de {tienda_nombre}: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UsuarioCreateAPIView(APIView):
    """Vista para crear usuario - Delega al controlador"""
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
            
            user = UsuarioController.crear_usuario(username, email, password)
            
            return Response(
                {
                    "message": "Usuario creado exitosamente",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email
                    }
                }, 
                status=status.HTTP_201_CREATED
            )
            
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
    """Vista para crear alerta de precio - Delega al controlador"""
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
            
            alerta = AlertaController.crear_alerta_precio(producto_id, email)
            
            return Response({
                "message": "Alerta de precio creada exitosamente",
                "alerta": {
                    "id": alerta.id,
                    "producto": alerta.producto.nombre,
                    "email": alerta.email,
                    "activa": alerta.activa
                }
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
    """Vista para reseñas de producto - Delega al controlador"""
    permission_classes = [AllowAny]
    
    def get(self, request, producto_id):
        try:
            # Convertir ID si es necesario
            numeric_id = UtilController.find_product_by_id(producto_id)
            if not numeric_id:
                return Response(
                    {"error": "ID de producto inválido"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            resenas_data = ResenaController.get_resenas_producto(numeric_id)
            return Response(resenas_data, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST if "no encontrado" in str(e) else status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"Error al obtener las reseñas: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request, producto_id):
        try:
            # Convertir ID si es necesario
            numeric_id = UtilController.find_product_by_id(producto_id)
            if not numeric_id:
                return Response(
                    {"error": "ID de producto inválido"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            valoracion = request.data.get('valoracion')
            comentario = request.data.get('comentario')
            autor = request.data.get('autor')
            
            resena = ResenaController.crear_resena(numeric_id, valoracion, comentario, autor)
            
            return Response({
                "message": "Reseña creada exitosamente",
                "resena": {
                    "id": resena.id,
                    "valoracion": resena.valoracion,
                    "comentario": resena.comentario,
                    "autor": resena.nombre_autor,
                    "fecha": resena.fecha_creacion.isoformat()
                }
            }, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Error al crear la reseña: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# VISTAS PARA GESTIÓN ETL

class ETLControlAPIView(APIView):
    """Vista para controlar el pipeline ETL"""
    permission_classes = [AllowAny]  # En producción cambiar por permisos de admin
    
    def post(self, request):
        """Ejecutar pipeline ETL completo"""
        try:
            action = request.data.get('action', 'full_pipeline')
            
            if action == 'full_pipeline':
                tiendas = request.data.get('tiendas', ['dbs', 'maicao', 'preunic'])
                categorias = request.data.get('categorias', ['maquillaje', 'skincare'])
                
                result = ETLService.run_full_etl_pipeline(tiendas, categorias)
                return Response(result, status=status.HTTP_200_OK)
            
            elif action == 'scraper':
                tienda = request.data.get('tienda')
                categoria = request.data.get('categoria')
                
                if not tienda:
                    return Response(
                        {"error": "Se requiere especificar la tienda"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                result = ETLService.run_scraper(tienda, categoria)
                return Response(result, status=status.HTTP_200_OK)
            
            elif action == 'processor':
                min_strong = request.data.get('min_strong', 90)
                min_prob = request.data.get('min_prob', 85)
                output_file = request.data.get('output_file')
                
                result = ETLService.run_processor(min_strong, min_prob, output_file)
                return Response(result, status=status.HTTP_200_OK)
            
            elif action == 'sync':
                result = DataIntegrationService.sync_unified_data_with_db()
                return Response(result, status=status.HTTP_200_OK)
            
            else:
                return Response(
                    {"error": f"Acción no reconocida: {action}"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {"error": f"Error ejecutando ETL: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ETLStatusAPIView(APIView):
    """Vista para obtener estado del ETL"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            status_data = DataIntegrationService.get_data_sources_status()
            return Response(status_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Error obteniendo estado ETL: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UnifiedProductsAPIView(APIView):
    """Vista para productos unificados del procesador"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            from .controllers import UnifiedDataController
            unified_data = UnifiedDataController.load_unified_products()
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
            from .controllers import UnifiedDataController
            dashboard_data = UnifiedDataController.get_unified_dashboard()
            return Response(dashboard_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Error al obtener dashboard unificado: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

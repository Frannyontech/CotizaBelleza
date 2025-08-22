"""
Vistas MVT - Arquitectura limpia con datos unificados
"""
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
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
    """Vista para dashboard usando datos unificados"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            unified_data = load_unified_products()
            productos = unified_data.get("productos", [])
            
            # Calcular estadísticas
            categorias = {}
            tiendas = {}
            multi_store = 0
            
            for producto in productos:
                # Categorías
                cat = producto.get('categoria', 'unknown')
                categorias[cat] = categorias.get(cat, 0) + 1
                
                # Tiendas y multi-store
                tiendas_producto = producto.get('tiendas', [])
                if len(tiendas_producto) > 1:
                    multi_store += 1
                
                for tienda in tiendas_producto:
                    fuente = tienda.get('fuente', 'unknown')
                    tiendas[fuente] = tiendas.get(fuente, 0) + 1
            
            # Formato para frontend
            tiendas_disponibles = [{"id": i+1, "nombre": nombre.upper(), "cantidad_productos": count} 
                                  for i, (nombre, count) in enumerate(tiendas.items())]
            
            categorias_disponibles = [{"id": i+1, "nombre": nombre, "cantidad_productos": count} 
                                     for i, (nombre, count) in enumerate(categorias.items())]
            
            # Seleccionar productos populares balanceados por tienda
            def seleccionar_productos_balanceados(productos, count=10):
                # Agrupar productos por tienda
                productos_por_tienda = {}
                productos_multi_tienda = []
                
                for producto in productos:
                    tiendas_producto = producto.get('tiendas', [])
                    if len(tiendas_producto) > 1:
                        productos_multi_tienda.append(producto)
                    else:
                        for tienda in tiendas_producto:
                            fuente = tienda.get('fuente', 'unknown').lower()
                            if fuente not in productos_por_tienda:
                                productos_por_tienda[fuente] = []
                            productos_por_tienda[fuente].append(producto)
                
                # Seleccionar productos balanceados
                seleccionados = []
                
                # 1. Agregar productos multi-tienda (prioridad alta)
                seleccionados.extend(productos_multi_tienda[:3])
                
                # 2. Agregar productos de cada tienda de forma balanceada
                tiendas_disponibles = list(productos_por_tienda.keys())
                productos_restantes = count - len(seleccionados)
                
                if tiendas_disponibles:
                    productos_por_tienda_cantidad = productos_restantes // len(tiendas_disponibles)
                    productos_extra = productos_restantes % len(tiendas_disponibles)
                    
                    for i, tienda in enumerate(tiendas_disponibles):
                        productos_tienda = productos_por_tienda[tienda]
                        cantidad = productos_por_tienda_cantidad + (1 if i < productos_extra else 0)
                        seleccionados.extend(productos_tienda[:cantidad])
                
                return seleccionados[:count]
            
            productos_populares = seleccionar_productos_balanceados(productos, 10)
            
            return Response({
                "estadisticas": {
                    "total_productos": len(productos),
                    "productos_con_precios": len(productos),
                    "total_categorias": len(categorias),
                    "total_tiendas": len(tiendas),
                    "multi_store_products": multi_store
                },
                "productos_populares": productos_populares,
                "productos_por_categoria": [{"nombre": k, "cantidad_productos": v} for k, v in categorias.items()],
                "tiendas_disponibles": tiendas_disponibles,
                "categorias_disponibles": categorias_disponibles
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Error al obtener datos del dashboard: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )





class TiendaProductosAPIView(APIView):
    """Vista para productos de una tienda específica"""
    permission_classes = [AllowAny]
    
    def get(self, request, tienda_nombre):
        try:
            unified_data = load_unified_products()
            productos = unified_data.get("productos", [])
            
            # Filtrar productos por tienda
            productos_tienda = []
            for producto in productos:
                for tienda in producto.get('tiendas', []):
                    if tienda.get('fuente', '').lower() == tienda_nombre.lower():
                        productos_tienda.append(producto)
                        break
            
            categorias_disponibles = list(set(p.get('categoria', 'unknown') for p in productos_tienda))
            
            return Response({
                "productos": productos_tienda,
                "total": len(productos_tienda),
                "categorias_disponibles": categorias_disponibles,
                "tienda": tienda_nombre.upper()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Error al obtener productos de la tienda: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )





class ProductoResenasAPIView(APIView):
    """Vista para reseñas de productos usando sistema de IDs persistentes"""
    permission_classes = [AllowAny]
    
    def get(self, request, producto_id, **kwargs):
        try:
            from core.models import ProductoPersistente, ResenaProductoPersistente
            
            # Buscar el producto por internal_id
            producto = ProductoPersistente.objects.filter(internal_id=producto_id).first()
            
            if not producto:
                return Response(
                    {"error": f"Producto no encontrado: {producto_id}"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Obtener reseñas de la base de datos
            resenas_db = ResenaProductoPersistente.objects.filter(producto=producto).order_by('-fecha_creacion')
            
            # Convertir a formato esperado por el frontend
            resenas_producto = []
            for resena in resenas_db:
                resenas_producto.append({
                    "id": resena.id,
                    "autor": resena.nombre_autor or resena.usuario.username if resena.usuario else "Usuario Anónimo",
                    "nombre_autor": resena.nombre_autor or resena.usuario.username if resena.usuario else "Usuario Anónimo",
                    "valoracion": resena.valoracion,
                    "comentario": resena.comentario,
                    "fecha": resena.fecha_creacion.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "fecha_creacion": resena.fecha_creacion.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "producto_id": producto_id,
                    "tienda": "GENERAL"
                })
            
            # Calcular promedio de valoración
            promedio = 0
            if resenas_producto:
                total_valoracion = sum(r.get('valoracion', 0) for r in resenas_producto)
                promedio = round(total_valoracion / len(resenas_producto), 1)
            
            return Response({
                "resenas_recientes": resenas_producto[-3:] if resenas_producto else [],  # Últimas 3
                "todas_resenas": resenas_producto,
                "total_resenas": len(resenas_producto),
                "promedio_valoracion": promedio
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Error al obtener las reseñas: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request, producto_id, **kwargs):
        try:
            from core.models import ProductoPersistente, ResenaProductoPersistente
            from django.contrib.auth.models import User
            
            # Buscar el producto por internal_id
            producto = ProductoPersistente.objects.filter(internal_id=producto_id).first()
            
            if not producto:
                return Response(
                    {"error": f"Producto no encontrado: {producto_id}"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Obtener o crear usuario (para reseñas anónimas)
            author_name = request.data.get('author') or request.data.get('autor', 'Usuario Anónimo')
            if not author_name or author_name.strip() == '':
                author_name = 'Usuario Anónimo'
            
            # Buscar usuario existente o crear uno temporal
            usuario, created = User.objects.get_or_create(
                username=author_name,
                defaults={
                    'email': f'{author_name.lower().replace(" ", "_")}@anonimo.com',
                    'first_name': author_name,
                    'is_active': True
                }
            )
            
            # Crear la reseña en la base de datos
            nueva_resena = ResenaProductoPersistente.objects.create(
                producto=producto,
                usuario=usuario,
                valoracion=int(request.data.get('rating') or request.data.get('valoracion', 5)),
                comentario=request.data.get('comment') or request.data.get('comentario', ''),
                nombre_autor=author_name,
                verificada=True
            )
            
            # Convertir a formato esperado por el frontend
            resena_response = {
                "id": nueva_resena.id,
                "autor": author_name,
                "nombre_autor": author_name,
                "valoracion": nueva_resena.valoracion,
                "comentario": nueva_resena.comentario,
                "fecha": nueva_resena.fecha_creacion.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "fecha_creacion": nueva_resena.fecha_creacion.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "producto_id": producto_id,
                "tienda": "GENERAL"
            }
            
            return Response({
                "success": True,
                "message": "¡Reseña guardada correctamente!",
                "resena": resena_response
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"error": f"Error al crear la reseña: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )





class UnifiedProductsAPIView(APIView):
    """Vista para productos unificados"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            unified_data = load_unified_products()
            productos = unified_data.get("productos", [])
            
            return Response({
                "productos": productos,
                "total": len(productos),
                "timestamp": "2025-08-18T22:08:57"
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Error al obtener productos unificados: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_unified_products():
    """Cargar productos unificados desde el archivo JSON"""
    try:
        unified_path = os.path.join(settings.BASE_DIR, 'data', 'processed', 'unified_products.json')
        
        if os.path.exists(unified_path):
            with open(unified_path, 'r', encoding='utf-8') as f:
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
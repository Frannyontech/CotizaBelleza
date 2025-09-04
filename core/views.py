"""
Vistas MVT - Arquitectura limpia con datos unificados
"""
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
from utils.security import mask_email, decrypt_email
import json
import os
import re
import hashlib
from django.core.cache import cache


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
            
            # Seleccionar productos populares con prioridad en coincidencias para tesis
            def seleccionar_productos_balanceados(productos, count=20):
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
                
                # 1. Agregar productos multi-tienda (prioridad máxima para tesis)
                # Mostrar la mayoría de productos con coincidencias (hasta 15)
                max_multi_tienda = min(15, len(productos_multi_tienda))
                seleccionados.extend(productos_multi_tienda[:max_multi_tienda])
                
                # 2. Agregar productos de tiendas individuales para completar los 20
                productos_restantes = count - len(seleccionados)
                
                if productos_restantes > 0 and productos_por_tienda:
                    tiendas_disponibles = list(productos_por_tienda.keys())
                    productos_por_tienda_cantidad = productos_restantes // len(tiendas_disponibles)
                    productos_extra = productos_restantes % len(tiendas_disponibles)
                    
                    for i, tienda in enumerate(tiendas_disponibles):
                        productos_tienda = productos_por_tienda[tienda]
                        cantidad = productos_por_tienda_cantidad + (1 if i < productos_extra else 0)
                        seleccionados.extend(productos_tienda[:cantidad])
                
                return seleccionados[:count]
            
            productos_populares = seleccionar_productos_balanceados(productos, 20)
            
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


class ProductDetailAPIView(APIView):
    """Vista unificada para obtener detalles de productos (persistentes y unificados)"""
    permission_classes = [AllowAny]
    
    def get(self, request, product_id):
        try:
            # Primero buscar en productos unificados para obtener información completa
            unified_data = load_unified_products()
            productos = unified_data.get("productos", [])
            
            # Buscar por product_id exacto
            producto_unificado = next((p for p in productos if p.get('product_id') == product_id), None)
            
            if producto_unificado:
                # Producto encontrado en JSON unificado - usar esta información completa
                tiendas = producto_unificado.get('tiendas', [])
                precio_min = min([float(t.get('precio', 0)) for t in tiendas]) if tiendas else 0
                
                return Response({
                    "product_id": producto_unificado.get('product_id'),
                    "nombre": producto_unificado.get('nombre'),
                    "marca": producto_unificado.get('marca'),
                    "categoria": producto_unificado.get('categoria'),
                    "imagen_url": producto_unificado.get('imagen') or (tiendas[0].get('imagen') if tiendas else ''),
                    "precio_min": precio_min,
                    "tiendasCount": len(tiendas),
                    "tiendas_disponibles": [t.get('fuente', '').upper() for t in tiendas],
                    "tiendas": tiendas,
                    "source": "unified"
                }, status=status.HTTP_200_OK)
            
            # Si no se encuentra en unificados, buscar en productos persistentes por internal_id
            from core.models import ProductoPersistente
            
            producto_persistente = ProductoPersistente.objects.filter(internal_id=product_id).first()
            
            if producto_persistente:
                # Producto encontrado en base de datos persistente
                # Obtener el precio más reciente del producto persistente
                precio_reciente = producto_persistente.precios_historicos.order_by('-fecha_scraping').first()
                precio_actual = precio_reciente.precio if precio_reciente else 0
                tienda_nombre = precio_reciente.tienda if precio_reciente else "GENERAL"
                
                return Response({
                    "product_id": producto_persistente.internal_id,
                    "nombre": producto_persistente.nombre_original,
                    "marca": producto_persistente.marca,
                    "categoria": producto_persistente.categoria,
                    "imagen_url": producto_persistente.imagen_url or (precio_reciente.imagen_url if precio_reciente else ''),
                    "precio_min": precio_actual,
                    "tiendasCount": 1,
                    "tiendas_disponibles": [tienda_nombre.upper()],
                    "tiendas": [{
                        "fuente": tienda_nombre,
                        "precio": precio_actual,
                        "stock": "En stock" if producto_persistente.activo else "Sin stock",
                        "url": precio_reciente.url_producto if precio_reciente else "#",
                        "imagen": precio_reciente.imagen_url if precio_reciente else producto_persistente.imagen_url
                    }],
                    "source": "persistent"
                }, status=status.HTTP_200_OK)
            
            # Si no se encuentra en persistentes, buscar en productos unificados
            unified_data = load_unified_products()
            productos = unified_data.get("productos", [])
            
            # Buscar por product_id exacto
            producto_unificado = next((p for p in productos if p.get('product_id') == product_id), None)
            
            if producto_unificado:
                # Producto encontrado en JSON unificado
                tiendas = producto_unificado.get('tiendas', [])
                precio_min = min([float(t.get('precio', 0)) for t in tiendas]) if tiendas else 0
                
                return Response({
                    "product_id": producto_unificado.get('product_id'),
                    "nombre": producto_unificado.get('nombre'),
                    "marca": producto_unificado.get('marca'),
                    "categoria": producto_unificado.get('categoria'),
                    "imagen_url": producto_unificado.get('imagen') or (tiendas[0].get('imagen') if tiendas else ''),
                    "precio_min": precio_min,
                    "tiendasCount": len(tiendas),
                    "tiendas_disponibles": [t.get('fuente', '').upper() for t in tiendas],
                    "tiendas": tiendas,
                    "source": "unified"
                }, status=status.HTTP_200_OK)
            
            # Si no se encuentra en ninguno de los dos, devolver 404
            return Response(
                {"error": f"Producto no encontrado: {product_id}"}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        except Exception as e:
            return Response(
                {"error": f"Error al obtener producto: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProductosFiltradosAPIView(APIView):
    """Vista para productos con filtrado dinámico"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            # Obtener parámetros de filtro
            categoria = request.GET.get('categoria', '')
            tienda = request.GET.get('tienda', '')
            limit = int(request.GET.get('limit', 20))
            
            unified_data = load_unified_products()
            productos = unified_data.get("productos", [])
            
            # Aplicar filtros
            productos_filtrados = []
            
            for producto in productos:
                # Filtro por categoría
                if categoria and producto.get('categoria', '') != categoria:
                    continue
                
                # Filtro por tienda
                if tienda:
                    tienda_encontrada = False
                    for tienda_producto in producto.get('tiendas', []):
                        if tienda_producto.get('fuente', '').upper() == tienda.upper():
                            tienda_encontrada = True
                            break
                    if not tienda_encontrada:
                        continue
                
                productos_filtrados.append(producto)
            
            # Limitar resultados
            productos_filtrados = productos_filtrados[:limit]
            
            # Convertir a formato del frontend
            dashboard_products = []
            for product in productos_filtrados:
                tiendas = product.get('tiendas', [])
                precio_min = None
                imagen_url = ''
                tiendas_disponibles = []
                
                # Extraer precio mínimo e imagen
                for tienda in tiendas:
                    # Imagen - usar cualquier imagen disponible
                    if tienda.get('imagen') and not imagen_url:
                        imagen_url = tienda.get('imagen')
                    
                    # Precio - convertir y validar
                    try:
                        precio = float(tienda.get('precio', 0))
                        if precio > 0 and (precio_min is None or precio < precio_min):
                            precio_min = precio
                    except (ValueError, TypeError):
                        pass
                    
                    # Tienda - agregar fuente
                    if tienda.get('fuente'):
                        tiendas_disponibles.append(tienda.get('fuente').upper())
                
                dashboard_products.append({
                    'id': product.get('product_id'),
                    'product_id': product.get('product_id'),
                    'nombre': product.get('nombre', 'Sin nombre'),
                    'marca': product.get('marca', ''),
                    'categoria': product.get('categoria', ''),
                    'precio_min': precio_min or 0,
                    'imagen_url': imagen_url or '',
                    'tiendas_disponibles': list(set(tiendas_disponibles)),
                    'tiendasCount': len(tiendas)
                })
            
            return Response({
                "productos": dashboard_products,
                "total": len(productos_filtrados),
                "filtros_aplicados": {
                    "categoria": categoria,
                    "tienda": tienda
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Error al obtener productos filtrados: {str(e)}"}, 
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


class AlertasAPIView(APIView):
    """API para gestionar alertas de precio"""
    permission_classes = [AllowAny]
    
    def _get_client_ip(self, request):
        """Obtiene la IP del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _check_rate_limit(self, request, email, action='create_alert'):
        """Verifica límites de rate para prevenir spam"""
        client_ip = self._get_client_ip(request)
        
        # Límites por IP
        ip_key = f"rate_limit_ip_{action}_{client_ip}"
        ip_count = cache.get(ip_key, 0)
        
        # Límites por email
        email_key = f"rate_limit_email_{action}_{hashlib.md5(email.encode()).hexdigest()}"
        email_count = cache.get(email_key, 0)
        
        # Límites: 5 alertas por hora por IP, 3 por email
        if action == 'create_alert':
            ip_limit = 5
            email_limit = 3
            window = 3600  # 1 hora
        else:
            ip_limit = 20
            email_limit = 10
            window = 3600
        
        if ip_count >= ip_limit:
            return False, f"Demasiadas solicitudes desde esta IP. Límite: {ip_limit} por hora"
        
        if email_count >= email_limit:
            return False, f"Demasiadas solicitudes para este email. Límite: {email_limit} por hora"
        
        # Incrementar contadores
        cache.set(ip_key, ip_count + 1, window)
        cache.set(email_key, email_count + 1, window)
        
        return True, None
    
    def _is_valid_email(self, email):
        """Valida formato de email de forma estricta"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email)) and len(email) <= 254
    
    def get(self, request):
        """Obtener alertas por email o todas las alertas del sistema"""
        try:
            # Verificar si se solicita ver todas las alertas
            show_all = request.GET.get('all', '').lower() == 'true'
            
            if show_all:
                # Mostrar todas las alertas del sistema (para administración)
                from core.models import AlertaPrecioProductoPersistente
                
                alertas = AlertaPrecioProductoPersistente.objects.filter(
                    activa=True
                ).select_related('producto').order_by('-fecha_creacion')
                
                alertas_data = []
                for alerta in alertas:
                    # Obtener precio actual del producto
                    precio_actual = alerta.producto.precios_historicos.filter(
                        disponible=True
                    ).order_by('-fecha_scraping').first()
                    
                    # Obtener email enmascarado
                    email_enmascarado = alerta.get_email_enmascarado()
                    
                    alertas_data.append({
                        'id': alerta.id,
                        'email': email_enmascarado,  # Email enmascarado para seguridad
                        'producto': {
                            'id': alerta.producto.internal_id,
                            'nombre': alerta.producto.nombre_original,
                            'marca': alerta.producto.marca,
                            'imagen': alerta.producto.imagen_url or '',
                        },
                        'precio_inicial': float(alerta.precio_inicial) if alerta.precio_inicial else None,
                        'precio_actual': float(precio_actual.precio) if precio_actual else None,
                        'activa': alerta.activa,
                        'notificada': alerta.notificada,
                        'fecha_creacion': alerta.fecha_creacion.isoformat(),
                        'fecha_ultima_notificacion': alerta.fecha_ultima_notificacion.isoformat() if alerta.fecha_ultima_notificacion else None,
                    })
                
                return Response({
                    'alertas': alertas_data,
                    'total': len(alertas_data),
                    'nota': 'Emails enmascarados por seguridad'
                })
            
            # Comportamiento original: obtener alertas por email específico
            email = request.GET.get('email')
            if not email:
                return Response(
                    {'error': 'email requerido o usar all=true para ver todas las alertas'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            from core.models import AlertaPrecioProductoPersistente
            from utils.security import encrypt_email
            
            # Encriptar email para la búsqueda
            email_encrypted = encrypt_email(email)
            
            alertas = AlertaPrecioProductoPersistente.objects.filter(
                email=email_encrypted,
                activa=True
            ).select_related('producto')
            
            alertas_data = []
            for alerta in alertas:
                # Obtener precio actual del producto
                precio_actual = alerta.producto.precios_historicos.filter(
                    disponible=True
                ).order_by('-fecha_scraping').first()
                
                alertas_data.append({
                    'id': alerta.id,
                    'producto': {
                        'id': alerta.producto.internal_id,
                        'nombre': alerta.producto.nombre_original,
                        'marca': alerta.producto.marca,
                        'imagen': alerta.producto.imagen_url or '',
                    },
                    'precio_inicial': float(alerta.precio_inicial) if alerta.precio_inicial else None,
                    'precio_actual': float(precio_actual.precio) if precio_actual else None,
                    'activa': alerta.activa,
                    'notificada': alerta.notificada,
                    'fecha_creacion': alerta.fecha_creacion.isoformat(),
                    'fecha_ultima_notificacion': alerta.fecha_ultima_notificacion.isoformat() if alerta.fecha_ultima_notificacion else None,
                })
            
            return Response({
                'alertas': alertas_data,
                'total': len(alertas_data)
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """Crear nueva alerta de precio"""
        try:
            data = request.data
            print(f"DEBUG: Datos recibidos: {data}")
            email = data.get('email')
            producto_id = data.get('producto_id')
            
            print(f"DEBUG: email={email}, producto_id={producto_id}")
            
            if not all([email, producto_id]):
                return Response(
                    {'error': 'email y producto_id son requeridos'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validar formato de email
            if not self._is_valid_email(email):
                return Response(
                    {'error': 'Formato de email inválido'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verificar rate limiting
            rate_ok, rate_error = self._check_rate_limit(request, email, 'create_alert')
            if not rate_ok:
                return Response(
                    {'error': rate_error}, 
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            
            from core.models import AlertaPrecioProductoPersistente, ProductoPersistente
            from utils.security import encrypt_email
            from django.db import transaction
            
            try:
                producto = ProductoPersistente.objects.get(internal_id=producto_id)
            except ProductoPersistente.DoesNotExist:
                return Response(
                    {'error': 'Producto no encontrado'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Obtener precio actual del producto para establecer precio inicial
            precio_actual = producto.precios_historicos.filter(
                disponible=True
            ).order_by('-fecha_scraping').first()
            
            if not precio_actual:
                return Response(
                    {'error': 'No se pudo obtener el precio actual del producto'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Usar hash simple para verificar duplicados (temporalmente)
            import hashlib
            email_hash = hashlib.md5(email.lower().encode()).hexdigest()
            
            print(f"DEBUG: Verificando alerta existente para producto {producto_id} y email {email}")
            print(f"DEBUG: Email hash: {email_hash}")
            
            # Usar transacción atómica para evitar condiciones de carrera
            with transaction.atomic():
                # Verificar si ya existe una alerta para este email y producto
                # Buscar por hash del email en lugar de email encriptado
                alertas_existentes = AlertaPrecioProductoPersistente.objects.filter(
                    producto=producto
                )
                
                # Verificar si alguna alerta tiene el mismo hash de email
                alerta_existente = None
                for alerta in alertas_existentes:
                    try:
                        # Intentar desencriptar el email almacenado
                        email_almacenado = alerta.get_user_email()
                        if email_almacenado.lower() == email.lower():
                            alerta_existente = alerta
                            break
                    except:
                        continue
                
                print(f"DEBUG: Alerta existente encontrada: {alerta_existente}")
                
                if alerta_existente:
                    print(f"DEBUG: Alerta duplicada detectada, devolviendo error 400")
                    # Si ya existe una alerta, devolver error 400
                    return Response({
                        'error': 'email_already_subscribed'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Crear nueva alerta con email encriptado
                email_encrypted = encrypt_email(email)
                alerta = AlertaPrecioProductoPersistente.objects.create(
                    producto=producto,
                    email=email_encrypted,  # El modelo se encargará de la encriptación
                    precio_inicial=float(precio_actual.precio),
                    activa=True,
                    notificada=False
                )
                
                print(f"DEBUG: Alerta creada exitosamente con ID: {alerta.id}")
            
            # Enviar email de confirmación
            try:
                # Email de confirmación
                subject = '¡Alerta de Precio Creada!'
                
                # Obtener nombre de la tienda de forma segura
                nombre_tienda = 'No especificada'
                if precio_actual.tienda:
                    if hasattr(precio_actual.tienda, 'nombre'):
                        nombre_tienda = precio_actual.tienda.nombre
                    else:
                        nombre_tienda = str(precio_actual.tienda)
                
                # Construir URL del producto
                producto_url = f"http://localhost:5173/detalle-producto/{producto.internal_id}"
                
                # Obtener imagen del producto desde unified_products.json si no está en el modelo
                imagen_url = producto.imagen_url
                if not imagen_url or imagen_url.strip() == '':
                    # Buscar en unified_products.json
                    unified_data = load_unified_products()
                    productos = unified_data.get("productos", [])
                    
                    for p in productos:
                        if p.get("product_id") == producto.internal_id:
                            # Tomar la primera imagen disponible de las tiendas
                            tiendas = p.get("tiendas", [])
                            for tienda in tiendas:
                                if tienda.get("imagen"):
                                    imagen_url = tienda.get("imagen")
                                    break
                            break
                
                # Preparar contexto para el template
                context = {
                    'producto': producto,
                    'precio_actual': precio_actual,
                    'nombre_tienda': nombre_tienda,
                    'producto_url': producto_url,
                    'imagen_url': imagen_url if imagen_url and imagen_url.strip() else None,
                }
                
                # Renderizar templates
                html_message = render_to_string('emails/alert_created.html', context)
                message = render_to_string('emails/alert_created.txt', context)
                
                # Crear email con HTML
                email_msg = EmailMessage(
                    subject=subject,
                    body=html_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[email],
                )
                email_msg.content_subtype = "html"  # Indicar que es HTML
                
                success = email_msg.send(fail_silently=False)
                
                if success:
                    print(f"Email de confirmación enviado a {mask_email(email)}")
                else:
                    print(f"Error enviando email de confirmación a {mask_email(email)}")
                    
            except Exception as e:
                print(f"Error en email de confirmación: {e}")
            
            return Response({
                'message': 'alert_created'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def put(self, request, alerta_id):
        """Actualizar alerta existente"""
        try:
            data = request.data
            activa = data.get('activa')
            
            from core.models import AlertaPrecioProductoPersistente
            
            try:
                alerta = AlertaPrecioProductoPersistente.objects.get(id=alerta_id)
            except AlertaPrecioProductoPersistente.DoesNotExist:
                return Response(
                    {'error': 'Alerta no encontrada'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            if activa is not None:
                alerta.activa = activa
            
            alerta.save()
            
            return Response({
                'message': 'Alerta actualizada exitosamente',
                'alerta_id': alerta.id
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, alerta_id):
        """Eliminar alerta"""
        try:
            from core.models import AlertaPrecioProductoPersistente
            
            try:
                alerta = AlertaPrecioProductoPersistente.objects.get(id=alerta_id)
            except AlertaPrecioProductoPersistente.DoesNotExist:
                return Response(
                    {'error': 'Alerta no encontrada'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            alerta.delete()
            
            return Response({
                'message': 'Alerta eliminada exitosamente'
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmailVerificationAPIView(APIView):
    """API para verificación de emails"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Solicitar verificación de email"""
        try:
            email = request.data.get('email')
            
            if not email:
                return Response(
                    {'error': 'email requerido'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validar formato de email
            if not self._is_valid_email(email):
                return Response(
                    {'error': 'Formato de email inválido'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verificar rate limiting
            rate_ok, rate_error = self._check_rate_limit(request, email, 'verify_email')
            if not rate_ok:
                return Response(
                    {'error': rate_error}, 
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            
            from core.services.email_service import EmailService
            
            # Enviar email de verificación
            success = EmailService.send_verification_email(email)
            
            if success:
                return Response({
                    'message': 'Email de verificación enviado'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Error enviando email de verificación'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get(self, request):
        """Verificar token de email"""
        try:
            token = request.GET.get('token')
            
            if not token:
                return Response(
                    {'error': 'token requerido'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            from core.services.email_service import EmailService
            
            success, message, email = EmailService.verify_email_token(token)
            
            if success:
                return Response({
                    'message': message,
                    'email': mask_email(email) if email else None
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': message
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _is_valid_email(self, email):
        """Valida formato de email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email)) and len(email) <= 254
    
    def _check_rate_limit(self, request, email, action='verify_email'):
        """Verifica rate limiting"""
        client_ip = self._get_client_ip(request)
        
        ip_key = f"rate_limit_ip_{action}_{client_ip}"
        email_key = f"rate_limit_email_{action}_{hashlib.md5(email.encode()).hexdigest()}"
        
        ip_count = cache.get(ip_key, 0)
        email_count = cache.get(email_key, 0)
        
        # Límites más estrictos para verificación
        ip_limit = 3  # 3 verificaciones por hora por IP
        email_limit = 2  # 2 verificaciones por hora por email
        window = 3600
        
        if ip_count >= ip_limit:
            return False, f"Demasiadas solicitudes de verificación desde esta IP. Límite: {ip_limit} por hora"
        
        if email_count >= email_limit:
            return False, f"Demasiadas solicitudes de verificación para este email. Límite: {email_limit} por hora"
        
        cache.set(ip_key, ip_count + 1, window)
        cache.set(email_key, email_count + 1, window)
        
        return True, None
    
    def _get_client_ip(self, request):
        """Obtiene la IP del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class UnsubscribeAPIView(APIView):
    """API para unsubscribe de emails"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Unsubscribe usando token"""
        try:
            token = request.GET.get('token')
            
            if not token:
                return Response(
                    {'error': 'token requerido'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            from core.services.email_service import EmailService
            
            success, message = EmailService.unsubscribe_email(token)
            
            if success:
                return Response({
                    'message': message
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': message
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



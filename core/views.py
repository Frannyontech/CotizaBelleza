from django.shortcuts import render
from django.http import HttpResponse
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
import json
import os
from django.conf import settings


def home(request):
    return HttpResponse("<h1>¡Bienvenido a CotizaBelleza!</h1><p>El proyecto Django creado por Francisca Galaz está funcionando correctamente.</p>")

class DashboardAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            total_productos = Producto.objects.count()
            total_categorias = Categoria.objects.count()
            total_tiendas = Tienda.objects.count()
            
            productos_con_precios = PrecioProducto.objects.filter(
                stock=True
            ).values('producto').distinct().count()
            
            precio_promedio = PrecioProducto.objects.filter(
                stock=True
            ).aggregate(Avg('precio'))['precio__avg'] or 0
            
            precios = PrecioProducto.objects.filter(stock=True)
            precio_min = precios.aggregate(Min('precio'))['precio__min'] or 0
            precio_max = precios.aggregate(Max('precio'))['precio__max'] or 0
            
            productos_por_categoria = Categoria.objects.annotate(
                cantidad_productos=Count('productos')
            ).values('nombre', 'cantidad_productos')
            
            productos_populares = Producto.objects.annotate(
                num_precios=Count('precios')
            ).filter(
                num_precios__gt=0
            ).order_by('-num_precios')[:8]
            
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
        
        if categoria_id:
            try:
                productos = productos.filter(categoria_id=categoria_id)
            except ValueError:
                return Response(
                    {"error": "ID de categoría inválido"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if search:
            productos = productos.filter(nombre__icontains=search)
        
        if tienda_id:
            productos = productos.filter(precios__tienda_id=tienda_id)
        
        productos_data = []
        for producto in productos[:50]:
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

class ProductoDetalleAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, producto_id):
        try:
            producto = Producto.objects.get(id=producto_id)
            
            precios_producto = PrecioProducto.objects.filter(
                producto=producto,
                stock=True
            ).select_related('tienda')
            
            precio_min = precios_producto.aggregate(Min('precio'))['precio__min']
            precio_max = precios_producto.aggregate(Max('precio'))['precio__max']
            
            # Obtener información detallada de cada tienda
            tiendas_detalladas = []
            for precio in precios_producto:
                tiendas_detalladas.append({
                    'nombre': precio.tienda.nombre,
                    'precio': float(precio.precio),
                    'stock': precio.stock,
                    'url_producto': precio.url_producto or '',
                    'fecha_extraccion': precio.fecha_extraccion.isoformat()
                })
            
            # Obtener el stock del primer precio disponible
            stock_disponible = precios_producto.filter(stock=True).exists()
            
            producto_data = {
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
                'tiendas_disponibles': [p.tienda.nombre for p in precios_producto],
                'tiendas_detalladas': tiendas_detalladas,
                'num_precios': precios_producto.count()
            }
            
            return Response(producto_data, status=status.HTTP_200_OK)
            
        except Producto.DoesNotExist:
            return Response(
                {"error": "Producto no encontrado"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"Error al obtener el producto: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DBSProductosAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            categoria_nombre = request.query_params.get('categoria', '')
            search = request.query_params.get('search', '')
            marca = request.query_params.get('marca', '')
            
            productos = Producto.objects.filter(
                precios__tienda__nombre='DBS'
            ).distinct()
            
            if categoria_nombre:
                productos = productos.filter(categoria__nombre=categoria_nombre)
            
            if search:
                productos = productos.filter(nombre__icontains=search)
            
            if marca:
                productos = productos.filter(marca__icontains=marca)
            
            productos_data = []
            seen_products = set()  # Para evitar duplicados
            
            for producto in productos:
                precio_dbs = PrecioProducto.objects.filter(
                    producto=producto,
                    tienda__nombre='DBS',
                    stock=True
                ).first()
                
                if precio_dbs:
                    # Crear clave única para evitar duplicados
                    product_key = f"{producto.nombre}_{producto.marca}_{precio_dbs.precio}"
                    
                    if product_key not in seen_products:
                        seen_products.add(product_key)
                        
                        productos_data.append({
                            'id': producto.id,
                            'nombre': producto.nombre,
                            'marca': producto.marca or '',
                            'categoria': producto.categoria.nombre,
                            'precio': float(precio_dbs.precio),
                            'stock': precio_dbs.stock,
                            'url_producto': precio_dbs.url_producto or '',
                            'imagen_url': producto.imagen_url or '',
                            'descripcion': producto.descripcion or '',
                            'fecha_extraccion': precio_dbs.fecha_extraccion.isoformat(),
                            'tienda': 'DBS'
                        })
            
            productos_data.sort(key=lambda x: x['precio'])
            
            return Response({
                'productos': productos_data,
                'total': len(productos_data),
                'categorias_disponibles': list(Categoria.objects.values_list('nombre', flat=True))
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Error al obtener productos DBS: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PREUNICProductosAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            categoria_nombre = request.query_params.get('categoria', '')
            search = request.query_params.get('search', '')
            marca = request.query_params.get('marca', '')
            
            productos = Producto.objects.filter(
                precios__tienda__nombre='PREUNIC'
            ).distinct()
            
            if categoria_nombre:
                productos = productos.filter(categoria__nombre=categoria_nombre)
            
            if search:
                productos = productos.filter(nombre__icontains=search)
            
            if marca:
                productos = productos.filter(marca__icontains=marca)
            
            productos_data = []
            seen_products = set()  # Para evitar duplicados
            
            for producto in productos:
                precio_preunic = PrecioProducto.objects.filter(
                    producto=producto,
                    tienda__nombre='PREUNIC',
                    stock=True
                ).first()
                
                if precio_preunic:
                    # Crear clave única para evitar duplicados
                    product_key = f"{producto.nombre}_{producto.marca}_{precio_preunic.precio}"
                    
                    if product_key not in seen_products:
                        seen_products.add(product_key)
                        
                        productos_data.append({
                            'id': producto.id,
                            'nombre': producto.nombre,
                            'marca': producto.marca or '',
                            'categoria': producto.categoria.nombre,
                            'precio': float(precio_preunic.precio),
                            'stock': precio_preunic.stock,
                            'url_producto': precio_preunic.url_producto or '',
                            'imagen_url': producto.imagen_url or '',
                            'descripcion': producto.descripcion or '',
                            'tienda': 'PREUNIC',
                            'fecha_extraccion': precio_preunic.fecha_extraccion.isoformat()
                        })
            
            # Obtener categorías disponibles dinámicamente
            categorias_disponibles = list(
                Categoria.objects.filter(
                    productos__precios__tienda__nombre='PREUNIC'
                ).distinct().values_list('nombre', flat=True)
            )
            
            return Response({
                'productos': productos_data,
                'total': len(productos_data),
                'categorias_disponibles': categorias_disponibles,
                'tienda': 'PREUNIC'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Error al obtener productos Preunic: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class MAICAOProductosAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            categoria_nombre = request.query_params.get('categoria', '')
            search = request.query_params.get('search', '')
            marca = request.query_params.get('marca', '')
            
            productos = Producto.objects.filter(
                precios__tienda__nombre='MAICAO'
            ).distinct()
            
            if categoria_nombre:
                productos = productos.filter(categoria__nombre=categoria_nombre)
            
            if search:
                productos = productos.filter(nombre__icontains=search)
            
            if marca:
                productos = productos.filter(marca__icontains=marca)
            
            productos_data = []
            seen_products = set()  # Para evitar duplicados
            
            for producto in productos:
                precio_maicao = PrecioProducto.objects.filter(
                    producto=producto,
                    tienda__nombre='MAICAO',
                    stock=True
                ).first()
                
                if precio_maicao:
                    # Crear clave única para evitar duplicados
                    product_key = f"{producto.nombre}_{producto.marca}_{precio_maicao.precio}"
                    
                    if product_key not in seen_products:
                        seen_products.add(product_key)
                        
                        productos_data.append({
                            'id': producto.id,
                            'nombre': producto.nombre,
                            'marca': producto.marca or '',
                            'categoria': producto.categoria.nombre,
                            'precio': float(precio_maicao.precio),
                            'stock': precio_maicao.stock,
                            'url_producto': precio_maicao.url_producto or '',
                            'imagen_url': producto.imagen_url or '',
                            'descripcion': producto.descripcion or '',
                            'tienda': 'MAICAO',
                            'fecha_extraccion': precio_maicao.fecha_extraccion.isoformat()
                        })
            
            # Obtener categorías disponibles dinámicamente
            categorias_disponibles = list(
                Categoria.objects.filter(
                    productos__precios__tienda__nombre='MAICAO'
                ).distinct().values_list('nombre', flat=True)
            )
            
            return Response({
                'productos': productos_data,
                'total': len(productos_data),
                'categorias_disponibles': categorias_disponibles,
                'tienda': 'MAICAO'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Error al obtener productos Maicao: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class MAICAOProductoDetalleAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, producto_id):
        try:
            producto = Producto.objects.get(id=producto_id)
            
            precios_producto = PrecioProducto.objects.filter(
                producto=producto,
                tienda__nombre='MAICAO',
                stock=True
            ).select_related('tienda')
            
            if not precios_producto.exists():
                return Response(
                    {"error": "Producto no encontrado en Maicao"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            precio_min = precios_producto.aggregate(Min('precio'))['precio__min']
            precio_max = precios_producto.aggregate(Max('precio'))['precio__max']
            
            # Obtener información detallada de cada tienda
            tiendas_detalladas = []
            for precio in precios_producto:
                tiendas_detalladas.append({
                    'tienda': precio.tienda.nombre,
                    'precio': float(precio.precio),
                    'stock': precio.stock,
                    'url_producto': precio.url_producto or '',
                    'fecha_extraccion': precio.fecha_extraccion.isoformat()
                })
            
            producto_data = {
                'id': producto.id,
                'nombre': producto.nombre,
                'marca': producto.marca or '',
                'categoria': producto.categoria.nombre,
                'imagen_url': producto.imagen_url or '',
                'descripcion': producto.descripcion or '',
                'precio_min': float(precio_min),
                'precio_max': float(precio_max),
                'tiendas': tiendas_detalladas
            }
            
            return Response(producto_data, status=status.HTTP_200_OK)
            
        except Producto.DoesNotExist:
            return Response(
                {"error": "Producto no encontrado"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"Error al obtener detalle del producto: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PREUNICProductoDetalleAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, producto_id):
        try:
            producto = Producto.objects.get(id=producto_id)
            
            precios_producto = PrecioProducto.objects.filter(
                producto=producto,
                tienda__nombre='PREUNIC',
                stock=True
            ).select_related('tienda')
            
            if not precios_producto.exists():
                return Response(
                    {"error": "Producto no encontrado en Preunic"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            precio_min = precios_producto.aggregate(Min('precio'))['precio__min']
            precio_max = precios_producto.aggregate(Max('precio'))['precio__max']
            
            # Obtener información detallada de cada tienda
            tiendas_detalladas = []
            for precio in precios_producto:
                tiendas_detalladas.append({
                    'tienda': precio.tienda.nombre,
                    'precio': float(precio.precio),
                    'stock': precio.stock,
                    'url_producto': precio.url_producto or '',
                    'fecha_extraccion': precio.fecha_extraccion.isoformat()
                })
            
            # Obtener el stock del primer precio disponible
            stock_disponible = precios_producto.filter(stock=True).exists()
            
            producto_data = {
                'id': producto.id,
                'nombre': producto.nombre,
                'marca': producto.marca or '',
                'categoria': producto.categoria.nombre if producto.categoria else '',
                'descripcion': producto.descripcion or '',
                'precio': float(precio_min) if precio_min else 0,
                'precio_min': float(precio_min) if precio_min else 0,
                'precio_max': float(precio_max) if precio_max else 0,
                'precio_original': float(precio_max) if precio_max else 0,
                'stock': stock_disponible,
                'url_producto': precios_producto.first().url_producto if precios_producto.exists() else '',
                'imagen_url': producto.imagen_url or '',
                'tienda': 'PREUNIC',
                'tiendas_disponibles': [p.tienda.nombre for p in precios_producto],
                'tiendas_detalladas': tiendas_detalladas,
                'num_precios': precios_producto.count()
            }
            
            return Response(producto_data, status=status.HTTP_200_OK)
            
        except Producto.DoesNotExist:
            return Response(
                {"error": "Producto no encontrado"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"Error al obtener producto Preunic: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
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

class AlertaPrecioCreateAPIView(APIView):
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
            
            # Verificar que el producto existe
            try:
                producto = Producto.objects.get(id=producto_id)
            except Producto.DoesNotExist:
                return Response(
                    {"error": "Producto no encontrado"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Verificar si ya existe una alerta para este email y producto
            if AlertaPrecio.objects.filter(producto=producto, email=email).exists():
                return Response(
                    {"error": "Ya existe una alerta para este email y producto"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Crear la alerta
            alerta = AlertaPrecio.objects.create(
                producto=producto,
                email=email
            )
            
            return Response({
                "message": "Alerta de precio creada exitosamente",
                "alerta": AlertaPrecioSerializer(alerta).data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"error": f"Error al crear la alerta: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ProductoResenasAPIView(APIView):
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

def load_unified_products():
    """Cargar productos unificados desde el archivo JSON"""
    try:
        possible_paths = [
            os.path.join(settings.BASE_DIR, 'data', 'processed', 'unified_products.json'),  # Primary data source
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

class UnifiedProductsAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            unified_data = load_unified_products()
            return Response(unified_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Error al obtener productos unificados: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UnifiedDashboardAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            unified_data = load_unified_products()
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
            
            # Seleccionar 10 productos populares (los primeros para simplificar)
            productos_populares = productos[:10]
            
            dashboard_data = {
                'estadisticas': {
                    'total_productos': total_productos,
                    'total_tiendas': len(tiendas_disponibles),
                    'total_categorias': len(categorias_disponibles),
                },
                'productos_populares': productos_populares,
                'tiendas_disponibles': list(tiendas_disponibles),
                'categorias_disponibles': list(categorias_disponibles)
            }
            
            return Response(dashboard_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Error al obtener datos del dashboard unificado: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

def _find_product_by_id(producto_id):
    """Helper function to find numeric product ID from various formats"""
    try:
        # If it's already numeric, return as-is
        if str(producto_id).isdigit():
            return int(producto_id)
        
        # If it's a canonical product ID (cb_xxxxx), try to find matching product
        if str(producto_id).startswith('cb_'):
            # Try to find product by searching the unified data
            return _find_product_by_canonical_id(producto_id)
        
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

def _find_product_by_canonical_id(canonical_id):
    """Find a database product that matches a canonical ID from unified data"""
    try:
        # Load unified data directly to avoid circular imports
        unified_data = load_unified_products()
        productos = unified_data.get("productos", [])
        
        # Find the product in unified data
        target_product = None
        for producto in productos:
            if producto.get('product_id') == canonical_id:
                target_product = producto
                break
        
        if not target_product:
            return None
        
        # Try to find a matching product in the database by name and marca
        from .models import Producto
        
        # Search by exact name and marca match
        matching_products = Producto.objects.filter(
            nombre__iexact=target_product.get('nombre', ''),
            marca__iexact=target_product.get('marca', '')
        )
        
        if matching_products.exists():
            return matching_products.first().id
        
        # If no exact match, try partial name match
        matching_products = Producto.objects.filter(
            nombre__icontains=target_product.get('nombre', '')[:50]  # First 50 chars
        )
        
        if matching_products.exists():
            return matching_products.first().id
        
        return None
    except Exception:
        return None

def _get_product_info_from_unified(producto_id):
    """Get product info from unified data file"""
    try:
        unified_data = load_unified_products()
        productos = unified_data.get("productos", [])
        
        for producto in productos:
            if producto.get('product_id') == producto_id:
                return {
                    'id': producto_id,
                    'nombre': producto.get('nombre', ''),
                    'marca': producto.get('marca', ''),
                    'categoria': producto.get('categoria', ''),
                    'source': 'unified'
                }
        return None
    except Exception:
        return None

def _create_or_get_placeholder_product(producto_id):
    """Create or get a placeholder product for canonical IDs"""
    try:
        from .models import Producto, Categoria
        
        # Get product info from unified data
        producto_info = _get_product_info_from_unified(producto_id)
        if not producto_info:
            return None
        
        # Get or create category
        categoria, _ = Categoria.objects.get_or_create(
            nombre=producto_info.get('categoria', 'general')
        )
        
        # Create placeholder product name that includes the canonical ID
        nombre_placeholder = f"{producto_info.get('nombre', 'Producto')[:400]} [{producto_id}]"
        
        # Create or get placeholder product
        producto, created = Producto.objects.get_or_create(
            nombre=nombre_placeholder,
            defaults={
                'marca': producto_info.get('marca', '')[:200],
                'categoria': categoria,
                'descripcion': f"Producto del sistema unificado - ID: {producto_id}"
            }
        )
        
        return producto.id
    except Exception as e:
        print(f"Error creating placeholder product: {e}")
        return None

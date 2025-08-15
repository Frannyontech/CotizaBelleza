from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db.models import Min, Max, Count, Avg
from .models import Producto, PrecioProducto, Categoria, Tienda, AlertaPrecio, Resena
from .serializers import (
    ProductoSerializer, PrecioProductoSerializer, 
    UserSerializer, CategoriaSerializer, TiendaSerializer, AlertaPrecioSerializer, ResenaSerializer
)


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
                            'fecha_extraccion': precio_dbs.fecha_extraccion.isoformat()
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
            # Verificar que el producto existe
            try:
                producto = Producto.objects.get(id=producto_id)
            except Producto.DoesNotExist:
                return Response(
                    {"error": "Producto no encontrado"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Obtener las reseñas del producto (ordenadas por fecha descendente)
            resenas = Resena.objects.filter(producto=producto).order_by('-fecha_creacion')
            
            # Calcular estadísticas
            total_resenas = resenas.count()
            if total_resenas > 0:
                promedio_valoracion = resenas.aggregate(promedio=Avg('valoracion'))['promedio']
                promedio_valoracion = round(promedio_valoracion, 1) if promedio_valoracion else 0
            else:
                promedio_valoracion = 0
            
            # Serializar las 3 reseñas más recientes para la vista de detalle
            resenas_recientes = resenas[:3]
            resenas_serializer = ResenaSerializer(resenas_recientes, many=True)
            
            return Response({
                "producto_id": producto_id,
                "total_resenas": total_resenas,
                "promedio_valoracion": promedio_valoracion,
                "resenas_recientes": resenas_serializer.data,
                "todas_resenas": ResenaSerializer(resenas, many=True).data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Error al obtener las reseñas: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request, producto_id):
        try:
            # Verificar que el producto existe
            try:
                producto = Producto.objects.get(id=producto_id)
            except Producto.DoesNotExist:
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
            
            # Crear usuario anónimo si no se proporciona autor
            if not autor:
                # Crear o obtener un usuario anónimo genérico
                usuario_anonimo, created = User.objects.get_or_create(
                    username=f'anonimo_{producto_id}_{len(comentario)}',
                    defaults={
                        'first_name': 'Usuario',
                        'last_name': 'Anónimo',
                        'email': f'anonimo{producto_id}@example.com'
                    }
                )
                usuario = usuario_anonimo
            else:
                # Crear usuario temporal con el nombre proporcionado
                usuario_temp, created = User.objects.get_or_create(
                    username=f'temp_{autor.replace(" ", "_").lower()}_{producto_id}',
                    defaults={
                        'first_name': autor.split(' ')[0] if ' ' in autor else autor,
                        'last_name': ' '.join(autor.split(' ')[1:]) if ' ' in autor else '',
                        'email': f'temp_{autor.replace(" ", "_").lower()}@example.com'
                    }
                )
                usuario = usuario_temp
            
            # Verificar si ya existe una reseña de este usuario para este producto
            resena_existente = Resena.objects.filter(producto=producto, usuario=usuario).first()
            if resena_existente:
                return Response(
                    {"error": "Ya has escrito una reseña para este producto"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Crear la reseña
            resena = Resena.objects.create(
                producto=producto,
                usuario=usuario,
                valoracion=valoracion,
                comentario=comentario.strip(),
                nombre_autor=autor  # Guardar el nombre original del autor
            )
            
            # Serializar y retornar la reseña creada
            resena_serializer = ResenaSerializer(resena)
            
            return Response({
                "message": "Reseña creada exitosamente",
                "resena": resena_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"error": f"Error al crear la reseña: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Producto, PrecioProducto, Categoria
from .serializers import (
    ProductoSerializer, PrecioProductoSerializer, 
    UserSerializer, CategoriaSerializer
)


def home(request):
    return HttpResponse("<h1>¡Bienvenido a CotizaBelleza!</h1><p>El proyecto Django creado por Francisca Galaz está funcionando correctamente.</p>")

class ProductoListAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        categoria_id = request.query_params.get('categoria')
        
        if categoria_id:
            try:
                productos = Producto.objects.filter(categoria_id=categoria_id)
            except ValueError:
                return Response(
                    {"error": "ID de categoría inválido"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            productos = Producto.objects.all()
        
        serializer = ProductoSerializer(productos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

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
            precios = PrecioProducto.objects.filter(producto_id=producto_id)
            serializer = PrecioProductoSerializer(precios, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
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
            # Verificar si el usuario ya existe
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
            
            # Crear el usuario
            user = serializer.save()
            return Response(
                {
                    "message": "Usuario creado exitosamente",
                    "user": UserSerializer(user).data
                }, 
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

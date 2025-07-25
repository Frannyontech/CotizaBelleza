from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .models import Producto
from .serializers import ProductoSerializer

# Create your views here.

def home(request):
    """Vista de inicio del proyecto CotizaBelleza"""
    return HttpResponse("<h1>¡Bienvenido a CotizaBelleza!</h1><p>El proyecto Django está funcionando correctamente.</p>")

class ProductoListAPIView(APIView):
    """API View para listar todos los productos"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Obtiene todos los productos y los retorna serializados"""
        productos = Producto.objects.all()
        serializer = ProductoSerializer(productos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Producto, Categoria, Tienda, PrecioProducto, 
    Alerta, AlertaUsuario, Resena, AlertaPrecio
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'

class TiendaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tienda
        fields = '__all__'

class ProductoSerializer(serializers.ModelSerializer):
    categoria = CategoriaSerializer(read_only=True)
    
    class Meta:
        model = Producto
        fields = '__all__'

class PrecioProductoSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)
    tienda = TiendaSerializer(read_only=True)
    
    class Meta:
        model = PrecioProducto
        fields = '__all__'

class ResenaSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)
    usuario = UserSerializer(read_only=True)
    
    class Meta:
        model = Resena
        fields = '__all__'

class AlertaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alerta
        fields = '__all__'

class AlertaUsuarioSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)
    usuario = UserSerializer(read_only=True)
    alerta = AlertaSerializer(read_only=True)
    
    class Meta:
        model = AlertaUsuario
        fields = '__all__'

class AlertaPrecioSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)
    
    class Meta:
        model = AlertaPrecio
        fields = '__all__' 
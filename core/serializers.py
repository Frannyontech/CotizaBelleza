from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Producto, Categoria, Tienda, PrecioProducto, 
    Resena, AlertaPrecio, AlertaPrecioProductoPersistente,
    ProductoPersistente, PrecioHistorico
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

class AlertaPrecioSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)
    email = serializers.SerializerMethodField()
    
    class Meta:
        model = AlertaPrecio
        fields = '__all__'
    
    def get_email(self, obj):
        """Retorna el email enmascarado en lugar del encriptado"""
        return obj.get_email_masked()

class AlertaPrecioProductoPersistenteSerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField()
    
    class Meta:
        model = AlertaPrecioProductoPersistente
        fields = '__all__'
    
    def get_email(self, obj):
        """Retorna el email enmascarado en lugar del encriptado"""
        return obj.get_email_enmascarado()

class ProductoPersistenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductoPersistente
        fields = '__all__'

class PrecioHistoricoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrecioHistorico
        fields = '__all__' 
#!/usr/bin/env python3
"""
Script para probar las URLs de imágenes de la base de datos
"""

import os
import sys
import django
import requests
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cotizabelleza.settings')
django.setup()

from core.models import Producto

def test_image_urls():
    """Probar las URLs de imágenes de los productos"""
    print("🔍 Probando URLs de imágenes...")
    
    productos = Producto.objects.filter(imagen_url__isnull=False).exclude(imagen_url='')[:10]
    
    working_urls = 0
    total_urls = 0
    
    for producto in productos:
        total_urls += 1
        print(f"\n📦 Producto: {producto.nombre}")
        print(f"🖼️  URL: {producto.imagen_url}")
        
        try:
            # Intentar hacer una petición HEAD para verificar si la imagen existe
            response = requests.head(producto.imagen_url, timeout=5)
            if response.status_code == 200:
                print("✅ URL funciona")
                working_urls += 1
            else:
                print(f"❌ URL no funciona (status: {response.status_code})")
        except Exception as e:
            print(f"❌ Error al acceder a la URL: {str(e)}")
    
    print(f"\n📊 Resumen:")
    print(f"   - URLs probadas: {total_urls}")
    print(f"   - URLs que funcionan: {working_urls}")
    print(f"   - URLs que fallan: {total_urls - working_urls}")
    
    if working_urls == 0:
        print("\n⚠️  Ninguna URL funciona. Usando imagen por defecto.")
    else:
        print(f"\n✅ {working_urls} URLs funcionan correctamente.")

if __name__ == "__main__":
    test_image_urls() 
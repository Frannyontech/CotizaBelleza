#!/usr/bin/env python3
"""
Script para configurar el backend de CotizaBelleza
- Carga datos del scraper
- Ejecuta migraciones
- Verifica la conexión
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cotizabelleza.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.db import connection
from core.models import Producto, Categoria, Tienda, PrecioProducto

def run_migrations():
    """Ejecutar migraciones de Django"""
    print("🔄 Ejecutando migraciones...")
    try:
        execute_from_command_line(['manage.py', 'makemigrations'])
        execute_from_command_line(['manage.py', 'migrate'])
        print("✅ Migraciones completadas")
    except Exception as e:
        print(f"❌ Error en migraciones: {e}")
        return False
    return True

def load_scraper_data():
    """Cargar datos del scraper"""
    print("🔄 Cargando datos del scraper...")
    try:
        execute_from_command_line(['manage.py', 'load_scraper_data'])
        print("✅ Datos del scraper cargados")
    except Exception as e:
        print(f"❌ Error cargando datos del scraper: {e}")
        return False
    return True

def verify_data():
    """Verificar que los datos se cargaron correctamente"""
    print("🔍 Verificando datos...")
    try:
        total_productos = Producto.objects.count()
        total_categorias = Categoria.objects.count()
        total_tiendas = Tienda.objects.count()
        total_precios = PrecioProducto.objects.count()
        
        print(f"📊 Estadísticas:")
        print(f"   - Productos: {total_productos}")
        print(f"   - Categorías: {total_categorias}")
        print(f"   - Tiendas: {total_tiendas}")
        print(f"   - Precios: {total_precios}")
        
        if total_productos > 0 and total_precios > 0:
            print("✅ Datos verificados correctamente")
            return True
        else:
            print("⚠️  No se encontraron suficientes datos")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando datos: {e}")
        return False

def test_api_endpoints():
    """Probar endpoints de la API"""
    print("🌐 Probando endpoints de la API...")
    try:
        from django.test import Client
        from django.urls import reverse
        
        client = Client()
        
        # Probar endpoint del dashboard
        response = client.get('/api/dashboard/')
        if response.status_code == 200:
            print("✅ API Dashboard funcionando")
        else:
            print(f"❌ Error en API Dashboard: {response.status_code}")
            
        # Probar endpoint de productos
        response = client.get('/api/productos/')
        if response.status_code == 200:
            print("✅ API Productos funcionando")
        else:
            print(f"❌ Error en API Productos: {response.status_code}")
            
        # Probar endpoint de categorías
        response = client.get('/api/categorias/')
        if response.status_code == 200:
            print("✅ API Categorías funcionando")
        else:
            print(f"❌ Error en API Categorías: {response.status_code}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error probando APIs: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Configurando backend de CotizaBelleza...")
    print("=" * 50)
    
    # Verificar conexión a la base de datos
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✅ Conexión a la base de datos exitosa")
    except Exception as e:
        print(f"❌ Error de conexión a la base de datos: {e}")
        return
    
    # Ejecutar migraciones
    if not run_migrations():
        return
    
    # Cargar datos del scraper
    if not load_scraper_data():
        return
    
    # Verificar datos
    if not verify_data():
        return
    
    # Probar APIs
    if not test_api_endpoints():
        return
    
    print("=" * 50)
    print("🎉 ¡Backend configurado exitosamente!")
    print("📝 Para iniciar el servidor Django:")
    print("   python manage.py runserver")
    print("📝 Para iniciar el frontend:")
    print("   cd cotizabelleza-frontend && npm run dev")

if __name__ == "__main__":
    main() 
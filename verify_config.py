#!/usr/bin/env python
"""
Script universal para verificar la configuración de Django
Funciona en Windows, Linux y macOS
"""
import os
import sys
import django

def verify_django_config():
    """Verifica que Django esté configurado correctamente"""
    print("🔍 Verificando configuración de Django...")
    
    try:
        # Configurar Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cotizabelleza.test_settings')
        django.setup()
        
        print("✅ Django configurado correctamente")
        
        # Verificar que los modelos se pueden importar
        from core.models import Categoria, Tienda, ProductoPersistente
        print("✅ Modelos importados correctamente")
        
        # Verificar configuración de base de datos
        from django.conf import settings
        print(f"✅ Base de datos configurada: {settings.DATABASES['default']['ENGINE']}")
        
        # Verificar configuración de email
        print(f"✅ Email backend configurado: {settings.EMAIL_BACKEND}")
        
        # Verificar configuración de Celery
        print(f"✅ Celery eager mode: {settings.CELERY_TASK_ALWAYS_EAGER}")
        
        # Verificar configuración de cache
        print(f"✅ Cache configurado: {settings.CACHES['default']['BACKEND']}")
        
        print("\n🎉 ¡Toda la configuración está correcta!")
        print("💡 Puedes ejecutar los tests con: python run_tests.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en la configuración: {e}")
        print("\n🔧 Posibles soluciones:")
        print("1. Verificar que el virtual environment esté activado")
        print("2. Verificar que todas las dependencias estén instaladas")
        print("3. Verificar que el archivo cotizabelleza/test_settings.py existe")
        return False

if __name__ == '__main__':
    success = verify_django_config()
    sys.exit(0 if success else 1)

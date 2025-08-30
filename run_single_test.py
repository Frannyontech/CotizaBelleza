#!/usr/bin/env python
"""
Script universal para ejecutar un test específico
Funciona en Windows, Linux y macOS
"""
import os
import sys
import subprocess

def run_single_test(test_path=None):
    """Ejecuta un test específico"""
    print("🚀 Configurando entorno de testing...")
    
    # Configurar variable de entorno
    os.environ['DJANGO_SETTINGS_MODULE'] = 'cotizabelleza.test_settings'
    print(f"✅ DJANGO_SETTINGS_MODULE configurado como: {os.environ['DJANGO_SETTINGS_MODULE']}")
    
    # Si no se especifica test, usar uno por defecto
    if not test_path:
        test_path = "tests/test_models.py::TestCategoria::test_str_representation"
    
    print(f"\n🧪 Ejecutando test: {test_path}")
    
    # Construir comando pytest
    cmd = [
        sys.executable,  # Usar el Python actual
        '-m', 'pytest',
        test_path,
        '-v',
        '--tb=short'
    ]
    
    try:
        # Ejecutar test
        result = subprocess.run(cmd, check=True)
        print("\n✅ Test completado exitosamente!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando test: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

if __name__ == '__main__':
    # Permitir especificar test como argumento
    test_path = sys.argv[1] if len(sys.argv) > 1 else None
    success = run_single_test(test_path)
    sys.exit(0 if success else 1)

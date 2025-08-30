#!/usr/bin/env python
"""
Script universal para ejecutar tests de Django
Funciona en Windows, Linux y macOS
"""
import os
import sys
import subprocess
import webbrowser
from pathlib import Path

def run_tests():
    """Ejecuta todos los tests con cobertura"""
    print("🚀 Configurando entorno de testing...")
    
    # Configurar variable de entorno
    os.environ['DJANGO_SETTINGS_MODULE'] = 'cotizabelleza.test_settings'
    print(f"✅ DJANGO_SETTINGS_MODULE configurado como: {os.environ['DJANGO_SETTINGS_MODULE']}")
    
    print("\n📊 Ejecutando tests con pytest...")
    
    # Construir comando pytest
    cmd = [
        sys.executable,  # Usar el Python actual
        '-m', 'pytest',
        '--nomigrations',
        '--cov=.',
        '--cov-report=html:htmlcov',
        '--cov-report=term-missing',
        '-v'
    ]
    
    try:
        # Ejecutar tests
        result = subprocess.run(cmd, check=True)
        
        print("\n✅ Tests completados exitosamente!")
        
        # Verificar si existe el reporte de cobertura
        coverage_file = Path('htmlcov/index.html')
        if coverage_file.exists():
            print("📈 Abriendo reporte de cobertura...")
            webbrowser.open(f'file://{coverage_file.absolute()}')
        else:
            print("⚠️  No se encontró el reporte de cobertura")
            
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando tests: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

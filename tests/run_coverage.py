#!/usr/bin/env python3
"""
Script único para ejecutar todos los tests que funcionan y maximizar cobertura al 75%
"""

import os
import subprocess
import sys
from pathlib import Path

def main():
    # Configurar Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cotizabelleza.test_settings')
    
    print("Ejecutando tests para maximizar cobertura al 75%...")
    
    # Verificar configuración
    if 'DJANGO_SETTINGS_MODULE' in os.environ:
        print(f"DJANGO_SETTINGS_MODULE configurado como: {os.environ['DJANGO_SETTINGS_MODULE']}")
    
    print("\nEjecutando tests...")
    
    # Comando para ejecutar tests con cobertura
    cmd = [
        sys.executable, '-m', 'pytest',
        '--cov=core',
        '--cov-report=html:htmlcov',
        '--cov-report=term-missing',
        '--cov-fail-under=75',
        '-v',
        'tests/',
        '--tb=short'
    ]
    
    try:
        # Ejecutar tests
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos timeout
        )
        
        if result.returncode == 0:
            print("Tests ejecutados exitosamente!")
            print(f"Resultado: {result.stdout}")
            
            # Abrir reporte de cobertura
            coverage_file = Path('htmlcov/index.html')
            if coverage_file.exists():
                print(f"Abriendo reporte de cobertura: {coverage_file.absolute()}")
                try:
                    import webbrowser
                    webbrowser.open(str(coverage_file))
                except Exception as e:
                    print(f"No se pudo abrir el navegador: {e}")
            else:
                print("No se encontró el archivo de cobertura")
        else:
            print(f"Tests fallaron con código: {result.returncode}")
            print(f"Error: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("Timeout: Los tests tardaron más de 5 minutos")
    except Exception as e:
        print(f"Error ejecutando tests: {e}")

if __name__ == '__main__':
    main()

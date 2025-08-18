#!/usr/bin/env python3
"""
Script de comandos simplificado para ejecutar el pipeline ETL
"""

import sys
import subprocess
from pathlib import Path

def print_help():
    """Muestra ayuda de comandos"""
    print("""
[EJECUTANDO] COMANDOS ETL COTIZABELLEZA

DESARROLLO (con límites):
  python run_etl.py dev          - Pipeline completo con límite de 2 páginas
  python run_etl.py dev-visible  - Pipeline con navegador visible (debug)
  python run_etl.py test         - Pipeline rápido con 1 página por tienda

PRODUCCIÓN (sin límites):
  python run_etl.py prod         - Pipeline completo SIN límites
  python run_etl.py prod-bg      - Pipeline en background (headless)

ESTADÍSTICAS:
  python run_etl.py stats        - Solo mostrar estadísticas del último run
  python run_etl.py check        - Verificar archivos generados

ARCHIVOS GENERADOS:
  - data/raw/                    - Datos crudos por tienda
  - data/processed/              - Datos unificados 
  - etl_stats_YYYYMMDD_HHMMSS.json - Estadísticas detalladas
  - etl_pipeline.log             - Logs de ejecución

EJEMPLOS:
  python run_etl.py dev          # Desarrollo con límites
  python run_etl.py prod         # Producción completa
  python run_etl.py stats        # Ver estadísticas
""")

def run_command(cmd_args):
    """Ejecuta comando del pipeline"""
    try:
        result = subprocess.run([sys.executable, "etl_pipeline.py"] + cmd_args, 
                              check=True, capture_output=False)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error ejecutando comando: {e}")
        return False
    except FileNotFoundError:
        print("[ERROR] Archivo etl_pipeline.py no encontrado")
        return False

def check_files():
    """Verifica archivos generados"""
    project_root = Path(__file__).parent
    
    print("[ARCHIVOS] VERIFICANDO ARCHIVOS GENERADOS:")
    
    # Archivos raw
    raw_dir = project_root / "data" / "raw"
    expected_raw = [
        "dbs_maquillaje.json", "dbs_skincare.json",
        "maicao_maquillaje.json", "maicao_skincare.json", 
        "preunic_maquillaje.json", "preunic_skincare.json"
    ]
    
    print(f"\n[DIRECTORIO] Raw data ({raw_dir}):")
    raw_count = 0
    for file in expected_raw:
        file_path = raw_dir / file
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"  [OK] {file} ({size_mb:.1f} MB)")
            raw_count += 1
        else:
            print(f"  [ERROR] {file} (faltante)")
    
    # Archivo procesado
    processed_dir = project_root / "data" / "processed"
    unified_file = processed_dir / "unified_products.json"
    
    print(f"\n[DIRECTORIO] Processed data ({processed_dir}):")
    if unified_file.exists():
        size_mb = unified_file.stat().st_size / (1024 * 1024)
        print(f"  [OK] unified_products.json ({size_mb:.1f} MB)")
    else:
        print(f"  [ERROR] unified_products.json (faltante)")
    
    # Archivos de estadísticas
    stats_files = list(project_root.glob("etl_stats_*.json"))
    print(f"\n[STATS] Estadísticas:")
    if stats_files:
        # Mostrar últimos 3 archivos
        stats_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        for i, stats_file in enumerate(stats_files[:3]):
            print(f"  [DATOS] {stats_file.name}")
    else:
        print(f"  [ERROR] No hay archivos de estadísticas")
    
    print(f"\n[RESUMEN] RESUMEN:")
    print(f"  Raw files: {raw_count}/6")
    print(f"  Processed: {'[OK]' if unified_file.exists() else '[ERROR]'}")
    print(f"  Stats: {len(stats_files)} archivos")

def main():
    if len(sys.argv) != 2:
        print_help()
        return
    
    command = sys.argv[1].lower()
    
    # Comandos de desarrollo
    if command == "dev":
        print("[EMOJI] MODO DESARROLLO (2 páginas por tienda)")
        run_command(["--headless", "--max-pages", "2"])
        
    elif command == "dev-visible":
        print("[EMOJI] MODO DESARROLLO VISIBLE (2 páginas por tienda)")
        run_command(["--visible", "--max-pages", "2"])
        
    elif command == "test":
        print("[EMOJI] MODO TEST (1 página por tienda)")
        run_command(["--headless", "--max-pages", "1"])
    
    # Comandos de producción
    elif command == "prod":
        print("[EJECUTANDO] MODO PRODUCCIÓN (sin límites)")
        run_command(["--visible"])
        
    elif command == "prod-bg":
        print("[EJECUTANDO] MODO PRODUCCIÓN BACKGROUND (sin límites)")
        run_command(["--headless"])
    
    # Estadísticas
    elif command == "stats":
        print("[STATS] GENERANDO ESTADÍSTICAS")
        run_command(["--stats-only"])
        
    elif command == "check":
        check_files()
    
    # Ayuda
    elif command in ["help", "-h", "--help"]:
        print_help()
        
    else:
        print(f"[ERROR] Comando desconocido: {command}")
        print_help()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Pipeline ETL v2.0 para CotizaBelleza
Versión refactorizada con arquitectura modular

Uso: python etl_v2.py [comando] [opciones]
"""

import argparse
import sys
from pathlib import Path

# Importar módulos ETL directamente desde el mismo paquete
import os
from . import ETLOrchestrator, ETLConfig


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='Pipeline ETL v2.0 para CotizaBelleza',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Comandos disponibles:
  full        Ejecuta el pipeline completo (scrapers + procesamiento + validación)
  scrapers    Ejecuta solo los scrapers
  process     Ejecuta solo el procesamiento (requiere archivos raw)
  validate    Ejecuta solo validación de datos existentes
  status      Muestra estado actual del sistema

Ejemplos:
  python etl_v2.py full --headless --max-pages 2
  python etl_v2.py scrapers --visible
  python etl_v2.py process
  python etl_v2.py validate
  python etl_v2.py status
        """
    )
    
    # Comando principal
    parser.add_argument('command', 
                       choices=['full', 'scrapers', 'process', 'validate', 'status'],
                       help='Comando a ejecutar')
    
    # Opciones de configuración
    parser.add_argument('--headless', action='store_true', default=True,
                       help='Ejecutar scrapers en modo headless (default: True)')
    parser.add_argument('--visible', action='store_true',
                       help='Ejecutar scrapers con navegador visible (override headless)')
    parser.add_argument('--max-pages', type=int, 
                       help='Límite de páginas por categoría (default: sin límite)')
    parser.add_argument('--max-workers', type=int, default=3,
                       help='Número máximo de workers para paralelización (default: 3)')
    
    # Opciones de salida
    parser.add_argument('--quiet', action='store_true',
                       help='Modo silencioso (solo errores)')
    parser.add_argument('--verbose', action='store_true',
                       help='Modo verbose (más detalles)')
    
    args = parser.parse_args()
    
    try:
        # Configurar nivel de logging si se especifica
        config_kwargs = {}
        if args.quiet or args.verbose:
            log_level = "ERROR" if args.quiet else "DEBUG"
            config_kwargs["log_config"] = {"level": log_level}
        
        # Determinar modo headless
        headless = args.headless and not args.visible
        
        # Crear configuración
        config = ETLConfig(
            headless=headless,
            max_pages=args.max_pages,
            max_workers=args.max_workers,
            **config_kwargs
        )
        
        # Crear orquestador
        orchestrator = ETLOrchestrator(config)
        
        # Ejecutar comando
        success = execute_command(orchestrator, args.command)
        
        # Salir con código apropiado
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n[ADVERTENCIA] Operación interrumpida por usuario")
        sys.exit(130)
    except Exception as e:
        print(f"[ERROR] Error inesperado: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def execute_command(orchestrator: ETLOrchestrator, command: str) -> bool:
    """
    Ejecuta el comando especificado
    
    Args:
        orchestrator: Instancia del orquestador ETL
        command: Comando a ejecutar
        
    Returns:
        True si el comando fue exitoso
    """
    if command == 'full':
        return orchestrator.run_full_pipeline()
    
    elif command == 'scrapers':
        return orchestrator.run_scrapers_only()
    
    elif command == 'process':
        return orchestrator.run_processor_only()
    
    elif command == 'validate':
        return orchestrator.validate_only()
    
    elif command == 'status':
        return show_status(orchestrator)
    
    else:
        print(f"[ERROR] Comando desconocido: {command}")
        return False


def show_status(orchestrator: ETLOrchestrator) -> bool:
    """
    Muestra el estado actual del sistema
    
    Args:
        orchestrator: Instancia del orquestador ETL
        
    Returns:
        True siempre (solo informativo)
    """
    try:
        status = orchestrator.get_status()
        
        print("\n" + "="*60)
        print("ESTADO ACTUAL DEL SISTEMA ETL v2.0")
        print("="*60)
        
        # Configuración
        config = status["config"]
        print(f"\n[CONFIGURACIÓN]")
        print(f"  Modo headless: {config['headless']}")
        print(f"  Máximo páginas: {config['max_pages'] or 'Sin límite'}")
        print(f"  Workers: {config['max_workers']}")
        
        # Directorios
        dirs = status["directories"]
        print(f"\n[DIRECTORIOS]")
        print(f"  Datos: {dirs['data_dir']}")
        print(f"  Raw: {dirs['raw_dir']}")
        print(f"  Procesados: {dirs['processed_dir']}")
        print(f"  Logs: {dirs['logs_dir']}")
        print(f"  Stats: {dirs['stats_dir']}")
        
        # Archivos raw
        raw_files = status["files"]["raw_files"]
        print(f"\n[ARCHIVOS RAW]")
        available = sum(1 for exists in raw_files.values() if exists)
        print(f"  Disponibles: {available}/{len(raw_files)}")
        
        for filename, exists in raw_files.items():
            status_icon = "✓" if exists else "✗"
            print(f"    {status_icon} {filename}")
        
        # Archivo unificado
        unified_exists = status["files"]["unified_file_exists"]
        print(f"\n[ARCHIVO UNIFICADO]")
        print(f"  Existe: {'✓' if unified_exists else '✗'} unified_products.json")
        
        if unified_exists and "unified_stats" in status:
            stats = status["unified_stats"]
            print(f"  Tamaño: {stats['size_mb']} MB")
            print(f"  Productos: {stats['records']:,}")
            print(f"  Modificado: {stats['modified']}")
        
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error obteniendo estado: {e}")
        return False


if __name__ == "__main__":
    main()

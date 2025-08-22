#!/usr/bin/env python3
"""
ETL v2.0 - Script unificado SIMPLIFICADO
Maneja tanto ejecución directa como tareas Celery
"""

import os
import sys
import subprocess
import argparse
import threading
import time
from datetime import datetime
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cotizabelleza.settings')

def run_etl_direct(mode='dev'):
    """Ejecutar ETL directamente (sin Celery)"""
    print(f"🚀 Ejecutando ETL v2.0 directo - Modo: {mode}")
    print("=" * 40)
    
    # Determinar argumentos
    if mode == 'dev':
        args = ['full', '--headless', '--max-pages', '2']
    elif mode == 'prod':
        args = ['full', '--headless']
    elif mode == 'test':
        args = ['full', '--headless', '--max-pages', '1']
    else:
        args = ['status']
    
    # Ejecutar ETL v2.0
    cmd = [sys.executable, '-m', 'etl.etl_v2'] + args
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def start_celery_worker():
    """Iniciar worker Celery simplificado"""
    print("🚀 Iniciando Celery Worker Simple...")
    print("🔧 Configuración: pool=solo, concurrency=1")
    print("=" * 40)
    
    cmd = [
        sys.executable, '-m', 'celery',
        '--app=etl.celery_app:app',
        'worker',
        '--loglevel=info',
        '--pool=solo',
        '--concurrency=1'
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n⏹️  Worker detenido")
    except Exception as e:
        print(f"❌ Error: {e}")

def start_celery_beat():
    """Iniciar beat Celery simplificado"""
    print("⏰ Iniciando Celery Beat Simple...")
    print("📅 Programador de tareas ETL")
    print("=" * 40)
    
    cmd = [
        sys.executable, '-m', 'celery',
        '--app=etl.celery_app:app',
        'beat',
        '--loglevel=info'
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n⏹️  Beat detenido")
    except Exception as e:
        print(f"❌ Error: {e}")

def start_celery_services():
    """Iniciar worker y beat juntos"""
    print("🚀 Iniciando servicios de Celery (Worker + Beat)")
    print("=" * 50)
    print("📋 Servicios que se iniciarán:")
    print("   • Celery Worker (procesa tareas)")
    print("   • Celery Beat (programa tareas)")
    print("=" * 50)
    
    def run_worker():
        start_celery_worker()
    
    def run_beat():
        start_celery_beat()
    
    # Crear threads para ejecutar ambos servicios
    worker_thread = threading.Thread(target=run_worker, daemon=True)
    beat_thread = threading.Thread(target=run_beat, daemon=True)
    
    try:
        print("🔄 Iniciando Worker...")
        worker_thread.start()
        time.sleep(2)  # Pequeña pausa para que el worker se inicie
        
        print("🔄 Iniciando Beat...")
        beat_thread.start()
        
        print("✅ Ambos servicios iniciados")
        print("💡 Presiona Ctrl+C para detener ambos servicios")
        print("=" * 50)
        
        # Mantener el script vivo
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Deteniendo servicios...")
        print("✅ Servicios detenidos")

def run_celery_task(task_mode='dev'):
    """Ejecutar tarea ETL con Celery"""
    try:
        import django
        django.setup()
        
        from etl.tasks.celery_tasks import run_etl_task, status_task
        
        print(f"🎯 Enviando tarea Celery - Modo: {task_mode}")
        print("=" * 40)
        
        if task_mode == 'status':
            result = status_task.delay()
        else:
            result = run_etl_task.delay(task_mode)
        
        print(f"📤 Tarea enviada: {result.id}")
        print("⏳ Ejecutándose en background...")
        print("💡 Revisa logs del worker para ver progreso")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_system():
    """Verificar estado del sistema"""
    print("🔍 Estado del Sistema")
    print("=" * 30)
    
    # Verificar Redis
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        if r.ping():
            print("✅ Redis: Conectado")
        else:
            print("❌ Redis: Desconectado")
    except:
        print("❌ Redis: No disponible")
    
    # Verificar datos ETL
    unified_file = Path('data/processed/unified_products.json')
    if unified_file.exists():
        size_mb = unified_file.stat().st_size / (1024 * 1024)
        print(f"✅ Datos ETL: {size_mb:.1f} MB")
    else:
        print("⚠️  Datos ETL: No encontrados")
    
    # Verificar workers Celery
    try:
        import django
        django.setup()
        from etl.celery_app import app
        
        stats = app.control.inspect().stats()
        if stats:
            print(f"✅ Workers Celery: {len(stats)} activos")
        else:
            print("❌ Workers Celery: Ninguno activo")
    except:
        print("⚠️  Workers Celery: No verificables")

def stop_celery_services():
    """Detener servicios de Celery"""
    import psutil
    
    print("🛑 Deteniendo servicios de Celery...")
    stopped_count = 0
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if 'celery' in cmdline and ('worker' in cmdline or 'beat' in cmdline):
                print(f"   Deteniendo proceso: {proc.info['pid']} - {proc.info['name']}")
                proc.terminate()
                stopped_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if stopped_count > 0:
        print(f"✅ {stopped_count} proceso(s) de Celery detenidos")
    else:
        print("ℹ️  No se encontraron procesos de Celery ejecutándose")

def list_celery_processes():
    """Listar procesos de Celery activos"""
    import psutil
    
    print("📋 Procesos de Celery activos:")
    print("-" * 50)
    
    found_processes = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if 'celery' in cmdline and ('worker' in cmdline or 'beat' in cmdline):
                found_processes = True
                service_type = "Worker" if 'worker' in cmdline else "Beat"
                uptime = datetime.now() - datetime.fromtimestamp(proc.info['create_time'])
                print(f"   PID: {proc.info['pid']} | {service_type} | Uptime: {str(uptime).split('.')[0]}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if not found_processes:
        print("   No hay procesos de Celery ejecutándose")

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='ETL v2.0 Simplificado')
    parser.add_argument('command', choices=[
        'dev', 'prod', 'test', 'status',           # Ejecución directa
        'worker', 'beat', 'services',              # Celery services
        'celery-dev', 'celery-prod', 'celery-status', # Tareas Celery
        'check',                                    # Estado del sistema
        'stop', 'kill',                            # Detener servicios
        'ps', 'list'                               # Listar procesos
    ], help='Comando a ejecutar')
    
    args = parser.parse_args()
    
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Ejecución directa
    if args.command in ['dev', 'prod', 'test', 'status']:
        success = run_etl_direct(args.command)
        sys.exit(0 if success else 1)
    
    # Servicios Celery
    elif args.command == 'worker':
        start_celery_worker()
    elif args.command == 'beat':
        start_celery_beat()
    elif args.command == 'services':
        start_celery_services()
    
    # Tareas Celery
    elif args.command.startswith('celery-'):
        mode = args.command.replace('celery-', '')
        success = run_celery_task(mode)
        sys.exit(0 if success else 1)
    
    # Estado del sistema
    elif args.command == 'check':
        check_system()
    
    # Detener servicios
    elif args.command in ['stop', 'kill']:
        stop_celery_services()
    
    # Listar procesos
    elif args.command in ['ps', 'list']:
        list_celery_processes()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

"""
Comando de gestión para configurar el patrón Observer
"""
from django.core.management.base import BaseCommand, CommandError
from core.services.observer_service import ObserverService
from core.patterns.product_subject import ProductoSubject
from core.patterns.price_alert_observer import PriceAlertObserver
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Configura y gestiona el patrón Observer para notificaciones de precio'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['setup', 'stats', 'test', 'cleanup', 'reset'],
            help='Acción a realizar'
        )
        parser.add_argument(
            '--product-id',
            type=str,
            help='ID del producto para acciones específicas'
        )
        parser.add_argument(
            '--test-price',
            type=float,
            help='Precio de prueba para test'
        )
        parser.add_argument(
            '--store',
            type=str,
            default='Test Store',
            help='Tienda para pruebas'
        )
    
    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'setup':
            self.setup_observers()
        elif action == 'stats':
            self.show_stats()
        elif action == 'test':
            self.test_notification(options)
        elif action == 'cleanup':
            self.cleanup_observers()
        elif action == 'reset':
            self.reset_notifications()
    
    def setup_observers(self):
        """Configura todos los observadores"""
        self.stdout.write("🔧 Configurando sistema de observadores...")
        
        try:
            total_observers = ObserverService.setup_all_observers()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Sistema configurado exitosamente: {total_observers} observadores activos"
                )
            )
            
            # Mostrar detalles
            stats = ObserverService.get_observer_stats()
            if stats:
                self.stdout.write(f"\n📊 Estadísticas:")
                self.stdout.write(f"  - Productos con observadores: {stats.get('total_subjects', 0)}")
                self.stdout.write(f"  - Observadores totales: {stats.get('total_observers', 0)}")
                self.stdout.write(f"  - Observadores activos: {stats.get('active_observers', 0)}")
                self.stdout.write(f"  - Promedio por producto: {stats.get('average_observers_per_subject', 0):.1f}")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error configurando observadores: {e}")
            )
    
    def show_stats(self):
        """Muestra estadísticas del sistema"""
        self.stdout.write("📊 Estadísticas del sistema de observadores...")
        
        try:
            stats = ObserverService.get_observer_stats()
            
            if stats:
                self.stdout.write(f"\n📈 Resumen:")
                self.stdout.write(f"  - Productos con observadores: {stats.get('total_subjects', 0)}")
                self.stdout.write(f"  - Observadores totales: {stats.get('total_observers', 0)}")
                self.stdout.write(f"  - Observadores activos: {stats.get('active_observers', 0)}")
                self.stdout.write(f"  - Promedio por producto: {stats.get('average_observers_per_subject', 0):.1f}")
                
                # Mostrar productos con más observadores
                subjects = ProductoSubject.objects.get_subjects_with_observers()
                if subjects:
                    self.stdout.write(f"\n🏆 Productos con más observadores:")
                    for subject in subjects[:5]:  # Top 5
                        observers_count = subject.observers_count
                        if observers_count > 0:
                            self.stdout.write(f"  - {subject.nombre_original}: {observers_count} observadores")
            else:
                self.stdout.write(self.style.WARNING("⚠️ No hay estadísticas disponibles"))
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error obteniendo estadísticas: {e}")
            )
    
    def test_notification(self, options):
        """Prueba el sistema de notificaciones"""
        product_id = options.get('product_id')
        test_price = options.get('test_price')
        store = options.get('store')
        
        if not product_id:
            self.stdout.write(
                self.style.ERROR("❌ Debes especificar --product-id para pruebas")
            )
            return
        
        if not test_price:
            self.stdout.write(
                self.style.ERROR("❌ Debes especificar --test-price para pruebas")
            )
            return
        
        self.stdout.write(f"🧪 Probando notificación para producto {product_id}...")
        
        try:
            success = ObserverService.test_notification(product_id, test_price, store)
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Notificación de prueba enviada: ${test_price} en {store}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR("❌ Error enviando notificación de prueba")
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error en prueba: {e}")
            )
    
    def cleanup_observers(self):
        """Limpia observadores inactivos"""
        self.stdout.write("🧹 Limpiando observadores inactivos...")
        
        try:
            removed = ObserverService.cleanup_inactive_observers()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Limpieza completada: {removed} observadores inactivos removidos"
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error en limpieza: {e}")
            )
    
    def reset_notifications(self):
        """Resetea el estado de notificaciones"""
        self.stdout.write("🔄 Reseteando estado de notificaciones...")
        
        try:
            updated = PriceAlertObserver.objects.reset_all_notifications()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Reset completado: {updated} notificaciones reseteadas"
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error en reset: {e}")
            )






"""
Servicio para gestionar el patrón Observer en CotizaBelleza
"""
from core.patterns.product_subject import ProductoSubject
from core.patterns.price_alert_observer import PriceAlertObserver
import logging

logger = logging.getLogger(__name__)


class ObserverService:
    """Servicio para gestionar el patrón Observer"""
    
    @staticmethod
    def setup_observers_for_product(product_id: str):
        """
        Configura observadores para un producto específico
        
        Args:
            product_id: ID del producto
        """
        try:
            # Obtener el producto como subject
            subject = ProductoSubject.objects.get_subject(product_id)
            if not subject:
                logger.warning(f"No se pudo obtener ProductoSubject para {product_id}")
                return False
            
            # Obtener todas las alertas activas para este producto
            observers = PriceAlertObserver.objects.get_observers_by_product(product_id)
            
            # Adjuntar observadores al subject
            for observer in observers:
                subject.attach(observer)
                logger.info(f"Observer {observer.id} adjuntado a {subject.internal_id}")
            
            logger.info(f"Configurados {observers.count()} observadores para producto {product_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error configurando observadores para producto {product_id}: {e}")
            return False
    
    @staticmethod
    def setup_all_observers():
        """
        Configura observadores para todos los productos que tienen alertas
        """
        try:
            # Obtener todos los productos que tienen alertas
            subjects = ProductoSubject.objects.get_subjects_with_observers()
            
            total_observers = 0
            for subject in subjects:
                observers = PriceAlertObserver.objects.get_observers_by_product(subject.internal_id)
                
                for observer in observers:
                    subject.attach(observer)
                    total_observers += 1
                
                logger.info(f"Configurados {observers.count()} observadores para {subject.internal_id}")
            
            logger.info(f"Configuración completa: {total_observers} observadores en {subjects.count()} productos")
            return total_observers
            
        except Exception as e:
            logger.error(f"Error configurando todos los observadores: {e}")
            return 0
    
    @staticmethod
    def add_observer_for_alert(alert_id: int):
        """
        Agrega un observador específico para una alerta
        
        Args:
            alert_id: ID de la alerta
        """
        try:
            # Obtener la alerta como observer
            observer = PriceAlertObserver.objects.get(id=alert_id)
            
            # Obtener el producto como subject
            subject = ProductoSubject.objects.get_subject(observer.producto.internal_id)
            if not subject:
                logger.error(f"No se pudo obtener ProductoSubject para alerta {alert_id}")
                return False
            
            # Adjuntar observer al subject
            subject.attach(observer)
            logger.info(f"Observer {alert_id} adjuntado a {subject.internal_id}")
            return True
            
        except PriceAlertObserver.DoesNotExist:
            logger.error(f"Alerta {alert_id} no encontrada")
            return False
        except Exception as e:
            logger.error(f"Error agregando observer para alerta {alert_id}: {e}")
            return False
    
    @staticmethod
    def remove_observer_for_alert(alert_id: int):
        """
        Remueve un observador específico para una alerta
        
        Args:
            alert_id: ID de la alerta
        """
        try:
            # Obtener la alerta como observer
            observer = PriceAlertObserver.objects.get(id=alert_id)
            
            # Obtener el producto como subject
            subject = ProductoSubject.objects.get_subject(observer.producto.internal_id)
            if not subject:
                logger.error(f"No se pudo obtener ProductoSubject para alerta {alert_id}")
                return False
            
            # Remover observer del subject
            subject.detach(observer)
            logger.info(f"Observer {alert_id} removido de {subject.internal_id}")
            return True
            
        except PriceAlertObserver.DoesNotExist:
            logger.error(f"Alerta {alert_id} no encontrada")
            return False
        except Exception as e:
            logger.error(f"Error removiendo observer para alerta {alert_id}: {e}")
            return False
    
    @staticmethod
    def get_observers_for_product(product_id: str):
        """
        Obtiene todos los observadores de un producto
        
        Args:
            product_id: ID del producto
            
        Returns:
            list: Lista de observadores
        """
        try:
            subject = ProductoSubject.objects.get_subject(product_id)
            if not subject:
                return []
            
            return subject._observers
            
        except Exception as e:
            logger.error(f"Error obteniendo observadores para producto {product_id}: {e}")
            return []
    
    @staticmethod
    def get_observer_stats():
        """
        Obtiene estadísticas de los observadores
        
        Returns:
            dict: Estadísticas de observadores
        """
        try:
            subjects = ProductoSubject.objects.get_subjects_with_observers()
            
            total_subjects = subjects.count()
            total_observers = sum(subject.observers_count for subject in subjects)
            
            # Contar observadores activos
            active_observers = PriceAlertObserver.objects.get_all_active_observers().count()
            
            return {
                'total_subjects': total_subjects,
                'total_observers': total_observers,
                'active_observers': active_observers,
                'average_observers_per_subject': total_observers / total_subjects if total_subjects > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de observadores: {e}")
            return {}
    
    @staticmethod
    def test_notification(product_id: str, test_price: float, store: str = "Test Store"):
        """
        Prueba el sistema de notificaciones para un producto
        
        Args:
            product_id: ID del producto
            test_price: Precio de prueba
            store: Tienda de prueba
        """
        try:
            subject = ProductoSubject.objects.get_subject(product_id)
            if not subject:
                logger.error(f"No se pudo obtener ProductoSubject para {product_id}")
                return False
            
            # Simular cambio de precio
            old_price = subject.get_current_price(store) or 0
            subject.notify_price_change(old_price, test_price, store, "https://test.com")
            
            logger.info(f"Notificación de prueba enviada para {product_id}: ${old_price} -> ${test_price}")
            return True
            
        except Exception as e:
            logger.error(f"Error en prueba de notificación para {product_id}: {e}")
            return False
    
    @staticmethod
    def cleanup_inactive_observers():
        """
        Limpia observadores inactivos de los subjects
        """
        try:
            subjects = ProductoSubject.objects.get_subjects_with_observers()
            total_removed = 0
            
            for subject in subjects:
                # Obtener observadores activos para este producto
                active_observers = PriceAlertObserver.objects.get_observers_by_product(subject.internal_id)
                active_observer_ids = set(active_observers.values_list('id', flat=True))
                
                # Remover observadores inactivos
                observers_to_remove = []
                for observer in subject._observers:
                    if observer.id not in active_observer_ids:
                        observers_to_remove.append(observer)
                
                for observer in observers_to_remove:
                    subject.detach(observer)
                    total_removed += 1
                
                logger.info(f"Removidos {len(observers_to_remove)} observadores inactivos de {subject.internal_id}")
            
            logger.info(f"Limpieza completada: {total_removed} observadores inactivos removidos")
            return total_removed
            
        except Exception as e:
            logger.error(f"Error en limpieza de observadores inactivos: {e}")
            return 0






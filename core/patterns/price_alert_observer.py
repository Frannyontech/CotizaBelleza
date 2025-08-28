"""
PriceAlert como Observer del patrón Observer
"""
from django.utils import timezone
from core.patterns.observer import Observer, PriceChangeEvent
from core.models import AlertaPrecioProductoPersistente as BaseAlertaPrecio
from core.tasks import send_price_alert_email
import logging

logger = logging.getLogger(__name__)


class PriceAlertObserver(BaseAlertaPrecio):
    """
    AlertaPrecioProductoPersistente extendido como Observer del patrón Observer
    Reacciona a cambios de precio y dispara emails cuando se cumple la condición
    """
    
    class Meta:
        proxy = True
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def should_notify(self, subject, **kwargs) -> bool:
        """
        Determina si este observador debe ser notificado
        
        Args:
            subject: El ProductoSubject que notificó el cambio
            **kwargs: Datos adicionales, incluyendo price_event
            
        Returns:
            bool: True si debe ser notificado
        """
        price_event = kwargs.get('price_event')
        if not price_event:
            return False
        
        # Verificar que la alerta esté activa
        if not self.activa:
            return False
        
        # Verificar que el producto coincida
        if price_event.product_id != self.producto.internal_id:
            return False
        
        # Verificar que el precio actual sea menor o igual al objetivo
        if price_event.new_price > self.precio_objetivo:
            return False
        
        # Verificar que no se haya notificado recientemente
        if self.notificada and self.fecha_ultima_notificacion:
            tiempo_desde_ultima = (timezone.now() - self.fecha_ultima_notificacion).total_seconds()
            if tiempo_desde_ultima < 3600:  # 1 hora
                logger.debug(f"Alerta {self.id} ya notificada recientemente")
                return False
        
        logger.info(f"Alerta {self.id} debe ser notificada: precio ${price_event.new_price} <= objetivo ${self.precio_objetivo}")
        return True
    
    def update(self, subject, **kwargs):
        """
        Método que se llama cuando el subject notifica cambios
        
        Args:
            subject: El ProductoSubject que notificó el cambio
            **kwargs: Datos adicionales, incluyendo price_event
        """
        price_event = kwargs.get('price_event')
        if not price_event:
            logger.warning(f"PriceAlertObserver {self.id} recibió notificación sin price_event")
            return
        
        try:
            logger.info(f"PriceAlertObserver {self.id} procesando cambio de precio: {price_event}")
            
            # Determinar si debe enviar notificación según el tipo de cambio
            should_send = self.should_send_notification_for_change(price_event)
            
            if should_send:
                # Disparar tarea de Celery para enviar email con información del cambio
                send_price_alert_email.delay(
                    alerta_id=self.id,
                    precio_actual=price_event.new_price,
                    precio_anterior=price_event.old_price,
                    tipo_cambio=price_event.change_type.value,
                    porcentaje_cambio=price_event.change_percentage,
                    monto_cambio=price_event.change_amount,
                    tienda_url=price_event.url
                )
                
                # Marcar como notificada
                self.notificada = True
                self.fecha_ultima_notificacion = timezone.now()
                self.save(update_fields=['notificada', 'fecha_ultima_notificacion'])
                
                logger.info(f"Email disparado para alerta {self.id}: {self.producto.nombre_original} - {price_event.change_type.value} ${price_event.old_price} -> ${price_event.new_price}")
            else:
                logger.info(f"Alerta {self.id} no requiere notificación para cambio: {price_event.change_type.value}")
            
        except Exception as e:
            logger.error(f"Error procesando alerta {self.id}: {e}")
    
    def should_send_notification_for_change(self, price_event) -> bool:
        """
        Determina si debe enviar notificación según el tipo de cambio
        
        Args:
            price_event: Evento de cambio de precio
            
        Returns:
            bool: True si debe enviar notificación
        """
        from core.patterns.price_change_types import PriceChangeType
        
        # Siempre notificar si el precio bajó (es una buena noticia)
        if price_event.change_type == PriceChangeType.DECREASED:
            return True
        
        # Notificar si es un nuevo precio y está por debajo del objetivo
        if price_event.change_type == PriceChangeType.NEW_PRICE:
            return price_event.new_price <= self.precio_objetivo
        
        # Para precios que subieron, solo notificar si aún está por debajo del objetivo
        if price_event.change_type == PriceChangeType.INCREASED:
            return price_event.new_price <= self.precio_objetivo
        
        # Para precios sin cambios, no notificar
        if price_event.change_type == PriceChangeType.UNCHANGED:
            return False
        
        return False
    
    def get_user_email(self) -> str:
        """Obtiene el email del usuario"""
        if self.usuario:
            return self.usuario.email
        return self.email
    
    def is_condition_met(self, current_price: float) -> bool:
        """
        Verifica si se cumple la condición de la alerta
        
        Args:
            current_price: Precio actual del producto
            
        Returns:
            bool: True si se cumple la condición
        """
        return current_price <= self.precio_objetivo
    
    def get_price_difference(self, current_price: float) -> float:
        """
        Calcula la diferencia entre el precio objetivo y el actual
        
        Args:
            current_price: Precio actual del producto
            
        Returns:
            float: Diferencia de precio (positiva si hay ahorro)
        """
        return self.precio_objetivo - current_price
    
    def reset_notification_status(self):
        """Resetea el estado de notificación"""
        self.notificada = False
        self.fecha_ultima_notificacion = None
        self.save(update_fields=['notificada', 'fecha_ultima_notificacion'])
        logger.info(f"Estado de notificación reseteado para alerta {self.id}")
    
    def __str__(self):
        return f"PriceAlertObserver({self.id}: {self.producto.nombre_original} - ${self.precio_objetivo})"


class PriceAlertObserverManager:
    """Manager para PriceAlertObserver con funcionalidades del patrón Observer"""
    
    @staticmethod
    def create_observer_for_product(product_id: str) -> list:
        """
        Crea observadores para todas las alertas de un producto
        
        Args:
            product_id: ID del producto
            
        Returns:
            list: Lista de PriceAlertObserver creados
        """
        from core.models import ProductoPersistente
        
        try:
            producto = ProductoPersistente.objects.get(internal_id=product_id)
            alertas = PriceAlertObserver.objects.filter(
                producto=producto,
                activa=True
            )
            
            observers = []
            for alerta in alertas:
                observers.append(PriceAlertObserver.objects.get(id=alerta.id))
            
            logger.info(f"Creados {len(observers)} observadores para producto {product_id}")
            return observers
            
        except ProductoPersistente.DoesNotExist:
            logger.error(f"Producto no encontrado: {product_id}")
            return []
    
    @staticmethod
    def get_all_active_observers():
        """
        Obtiene todos los observadores activos
        
        Returns:
            QuerySet: Observadores activos
        """
        return PriceAlertObserver.objects.filter(activa=True)
    
    @staticmethod
    def reset_all_notifications():
        """Resetea el estado de notificación de todas las alertas"""
        updated = PriceAlertObserver.objects.filter(
            notificada=True
        ).update(
            notificada=False,
            fecha_ultima_notificacion=None
        )
        
        logger.info(f"Reseteadas {updated} notificaciones de alertas")
        return updated
    
    @staticmethod
    def get_observers_by_user(user_id: int):
        """
        Obtiene observadores de un usuario específico
        
        Args:
            user_id: ID del usuario
            
        Returns:
            QuerySet: Observadores del usuario
        """
        return PriceAlertObserver.objects.filter(
            usuario_id=user_id,
            activa=True
        )
    
    @staticmethod
    def get_observers_by_product(product_id: str):
        """
        Obtiene observadores de un producto específico
        
        Args:
            product_id: ID del producto
            
        Returns:
            QuerySet: Observadores del producto
        """
        from core.models import ProductoPersistente
        
        try:
            producto = ProductoPersistente.objects.get(internal_id=product_id)
            return PriceAlertObserver.objects.filter(
                producto=producto,
                activa=True
            )
        except ProductoPersistente.DoesNotExist:
            return PriceAlertObserver.objects.none()


# Configurar el manager
PriceAlertObserver.objects = PriceAlertObserverManager()

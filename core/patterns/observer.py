"""
Patrón Observer para CotizaBelleza
Implementa el patrón de diseño Observer para notificaciones de cambios de precio
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class Observer(ABC):
    """Clase base para todos los observadores"""
    
    @abstractmethod
    def update(self, subject, **kwargs):
        """
        Método que se llama cuando el subject notifica cambios
        
        Args:
            subject: El objeto que notificó el cambio
            **kwargs: Datos adicionales del cambio
        """
        pass
    
    @abstractmethod
    def should_notify(self, subject, **kwargs) -> bool:
        """
        Determina si este observador debe ser notificado
        
        Args:
            subject: El objeto que notificó el cambio
            **kwargs: Datos adicionales del cambio
            
        Returns:
            bool: True si debe ser notificado
        """
        pass


class Subject(ABC):
    """Clase base para todos los subjects (observables)"""
    
    def __init__(self):
        self._observers: List[Observer] = []
        self._notifications_enabled = True
    
    def attach(self, observer: Observer):
        """Agrega un observador"""
        if observer not in self._observers:
            self._observers.append(observer)
            logger.debug(f"Observer {observer} agregado a {self}")
    
    def detach(self, observer: Observer):
        """Remueve un observador"""
        if observer in self._observers:
            self._observers.remove(observer)
            logger.debug(f"Observer {observer} removido de {self}")
    
    def notify(self, **kwargs):
        """
        Notifica a todos los observadores
        
        Args:
            **kwargs: Datos adicionales para pasar a los observadores
        """
        if not self._notifications_enabled:
            return
        
        notified_count = 0
        for observer in self._observers:
            try:
                if observer.should_notify(self, **kwargs):
                    observer.update(self, **kwargs)
                    notified_count += 1
            except Exception as e:
                logger.error(f"Error notificando observer {observer}: {e}")
        
        logger.info(f"Notificados {notified_count} observadores de {len(self._observers)} totales")
    
    def enable_notifications(self):
        """Habilita las notificaciones"""
        self._notifications_enabled = True
    
    def disable_notifications(self):
        """Deshabilita las notificaciones"""
        self._notifications_enabled = False
    
    @property
    def observers_count(self) -> int:
        """Retorna el número de observadores"""
        return len(self._observers)


class PriceChangeEvent:
    """Evento de cambio de precio"""
    
    def __init__(self, product_id: str, old_price: float, new_price: float, 
                 store: str, url: str = None, timestamp=None):
        self.product_id = product_id
        self.old_price = old_price
        self.new_price = new_price
        self.store = store
        self.url = url
        self.timestamp = timestamp
        
        # Calcular información del cambio
        from core.patterns.price_change_types import PriceChangeDirection
        self.change_type = PriceChangeDirection.get_change_type(old_price, new_price)
        self.change_percentage = PriceChangeDirection.get_change_percentage(old_price, new_price)
        self.change_amount = PriceChangeDirection.get_change_amount(old_price, new_price)
        
    def __str__(self):
        return f"PriceChangeEvent(product_id={self.product_id}, old_price={self.old_price}, new_price={self.new_price}, change_type={self.change_type.value})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el evento a diccionario"""
        return {
            'product_id': self.product_id,
            'old_price': self.old_price,
            'new_price': self.new_price,
            'store': self.store,
            'url': self.url,
            'timestamp': self.timestamp,
            'change_type': self.change_type.value,
            'change_percentage': self.change_percentage,
            'change_amount': self.change_amount
        }

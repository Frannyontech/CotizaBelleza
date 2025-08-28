"""
Producto como Subject del patrón Observer
"""
from django.db import models
from django.utils import timezone
from core.patterns.observer import Subject, PriceChangeEvent
from core.models import ProductoPersistente as BaseProductoPersistente
import logging

logger = logging.getLogger(__name__)


class ProductoSubject(BaseProductoPersistente):
    """
    ProductoPersistente extendido como Subject del patrón Observer
    Notifica a los observadores cuando cambia el precio
    """
    
    class Meta:
        proxy = True
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inicializar funcionalidad de Subject
        self._observers = []
        self._notifications_enabled = True
    
    def attach(self, observer):
        """Agrega un observador"""
        if observer not in self._observers:
            self._observers.append(observer)
            logger.debug(f"Observer {observer} agregado a {self}")
    
    def detach(self, observer):
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
    
    def notify_price_change(self, old_price: float, new_price: float, 
                          store: str, url: str = None):
        """
        Notifica a todos los observadores sobre un cambio de precio
        
        Args:
            old_price: Precio anterior
            new_price: Nuevo precio
            store: Tienda donde cambió el precio
            url: URL del producto en la tienda
        """
        event = PriceChangeEvent(
            product_id=self.internal_id,
            old_price=old_price,
            new_price=new_price,
            store=store,
            url=url,
            timestamp=timezone.now()
        )
        
        logger.info(f"Notificando cambio de precio: {event}")
        self.notify(price_event=event)
    
    def get_current_price(self, store: str = None) -> float:
        """
        Obtiene el precio actual del producto
        
        Args:
            store: Tienda específica (opcional)
            
        Returns:
            float: Precio actual o None si no hay precio
        """
        from core.models import PrecioHistorico
        
        queryset = PrecioHistorico.objects.filter(
            producto=self,
            disponible=True
        ).order_by('-fecha_scraping')
        
        if store:
            queryset = queryset.filter(tienda=store)
        
        latest_price = queryset.first()
        return float(latest_price.precio) if latest_price else None
    
    def get_price_history(self, store: str = None, limit: int = 10):
        """
        Obtiene el historial de precios
        
        Args:
            store: Tienda específica (opcional)
            limit: Número máximo de registros
            
        Returns:
            QuerySet: Historial de precios
        """
        from core.models import PrecioHistorico
        
        queryset = PrecioHistorico.objects.filter(
            producto=self
        ).order_by('-fecha_scraping')
        
        if store:
            queryset = queryset.filter(tienda=store)
        
        return queryset[:limit]
    
    def has_price_changed(self, store: str, new_price: float) -> bool:
        """
        Verifica si el precio ha cambiado
        
        Args:
            store: Tienda
            new_price: Nuevo precio
            
        Returns:
            bool: True si el precio cambió
        """
        current_price = self.get_current_price(store)
        if current_price is None:
            return True  # No hay precio previo, considerar como cambio
        
        return abs(current_price - new_price) > 0.01  # Tolerancia de 1 centavo
    
    def update_price_and_notify(self, new_price: float, store: str, 
                              url: str = None, **kwargs):
        """
        Actualiza el precio y notifica a los observadores
        
        Args:
            new_price: Nuevo precio
            store: Tienda
            url: URL del producto
            **kwargs: Otros campos del PrecioHistorico
        """
        from core.models import PrecioHistorico
        
        # Obtener precio anterior
        old_price = self.get_current_price(store)
        
        # Crear nuevo registro de precio
        precio_historico = PrecioHistorico.objects.create(
            producto=self,
            tienda=store,
            precio=new_price,
            url_producto=url,
            fecha_scraping=timezone.now(),
            **kwargs
        )
        
        # Notificar cambio si el precio cambió
        if old_price is None or self.has_price_changed(store, new_price):
            self.notify_price_change(old_price or 0, new_price, store, url)
            logger.info(f"Precio actualizado y notificado: {self.internal_id} - {store}: ${old_price} -> ${new_price}")
        else:
            logger.debug(f"Precio sin cambios: {self.internal_id} - {store}: ${new_price}")
        
        return precio_historico
    
    def __str__(self):
        return f"ProductoSubject({self.internal_id}: {self.nombre_original})"


class ProductoSubjectManager(models.Manager):
    """Manager para ProductoSubject con funcionalidades del patrón Observer"""
    
    def get_subject(self, product_id: str) -> ProductoSubject:
        """
        Obtiene un ProductoSubject por ID
        
        Args:
            product_id: ID del producto
            
        Returns:
            ProductoSubject: Producto como subject
        """
        try:
            return ProductoSubject.objects.get(internal_id=product_id)
        except ProductoSubject.DoesNotExist:
            logger.error(f"ProductoSubject no encontrado: {product_id}")
            return None
    
    def get_subjects_with_observers(self):
        """
        Obtiene productos que tienen observadores
        
        Returns:
            QuerySet: Productos con observadores
        """
        # Esta es una implementación simplificada
        # En una implementación real, podrías querer filtrar por productos que tienen alertas
        from core.models import AlertaPrecioProductoPersistente
        
        productos_con_alertas = AlertaPrecioProductoPersistente.objects.values_list(
            'producto_id', flat=True
        ).distinct()
        
        return ProductoSubject.objects.filter(id__in=productos_con_alertas)
    
    def attach_observers_to_all(self, observer_class, **observer_kwargs):
        """
        Adjunta observadores a todos los productos que tienen alertas
        
        Args:
            observer_class: Clase del observador a crear
            **observer_kwargs: Argumentos para crear el observador
        """
        subjects = self.get_subjects_with_observers()
        
        for subject in subjects:
            observer = observer_class(**observer_kwargs)
            subject.attach(observer)
            logger.info(f"Observer {observer} adjuntado a {subject}")
        
        logger.info(f"Adjuntados observadores a {subjects.count()} productos")


# Configurar el manager
ProductoSubject.objects = ProductoSubjectManager()

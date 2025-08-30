"""
Tipos de cambio de precio para el sistema de notificaciones
"""
from enum import Enum


class PriceChangeType(Enum):
    """Tipos de cambio de precio"""
    INCREASED = "increased"      # Precio subió
    DECREASED = "decreased"      # Precio bajó
    UNCHANGED = "unchanged"      # Precio se mantuvo igual
    NEW_PRICE = "new_price"      # Nuevo precio (no había precio previo)


class PriceChangeDirection:
    """Utilidades para determinar la dirección del cambio de precio"""
    
    @staticmethod
    def get_change_type(old_price: float, new_price: float, tolerance: float = 0.01) -> PriceChangeType:
        """
        Determina el tipo de cambio de precio
        
        Args:
            old_price: Precio anterior
            new_price: Nuevo precio
            tolerance: Tolerancia para considerar cambios (por defecto 1 centavo)
            
        Returns:
            PriceChangeType: Tipo de cambio
        """
        if old_price is None:
            return PriceChangeType.NEW_PRICE
        
        price_difference = abs(new_price - old_price)
        
        if price_difference <= tolerance:
            return PriceChangeType.UNCHANGED
        elif new_price > old_price:
            return PriceChangeType.INCREASED
        else:
            return PriceChangeType.DECREASED
    
    @staticmethod
    def get_change_percentage(old_price: float, new_price: float) -> float:
        """
        Calcula el porcentaje de cambio
        
        Args:
            old_price: Precio anterior
            new_price: Nuevo precio
            
        Returns:
            float: Porcentaje de cambio (positivo si subió, negativo si bajó)
        """
        if old_price is None or old_price == 0:
            return 0.0
        
        return ((new_price - old_price) / old_price) * 100
    
    @staticmethod
    def get_change_amount(old_price: float, new_price: float) -> float:
        """
        Calcula el monto del cambio
        
        Args:
            old_price: Precio anterior
            new_price: Nuevo precio
            
        Returns:
            float: Monto del cambio (positivo si subió, negativo si bajó)
        """
        if old_price is None:
            return 0.0
        
        return new_price - old_price






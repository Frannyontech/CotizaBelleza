"""
Servicios - Capa de lógica de negocio simplificada
Solo contiene los servicios esenciales para el funcionamiento con datos unificados
"""
import json
import os
from django.conf import settings


class UnifiedDataService:
    """Servicio para datos unificados del procesador ETL"""
    
    @staticmethod
    def load_unified_products():
        """Cargar productos unificados desde el archivo JSON"""
        try:
            unified_path = os.path.join(settings.BASE_DIR, 'data', 'processed', 'unified_products.json')
            
            if os.path.exists(unified_path):
                with open(unified_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Handle both array format and object format
                    if isinstance(data, list):
                        return {"productos": data, "total": len(data)}
                    elif isinstance(data, dict) and "productos" in data:
                        return {**data, "total": len(data.get("productos", []))}
                    else:
                        return {"productos": [], "total": 0}
            
            return {"productos": [], "total": 0}
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading unified products: {e}")
            return {"productos": [], "total": 0}
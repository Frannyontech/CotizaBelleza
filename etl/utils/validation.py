"""
Validadores de datos para el sistema ETL
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional


class DataValidator:
    """Validador de datos para el sistema ETL"""
    
    def __init__(self, config, logger):
        """
        Inicializa el validador
        
        Args:
            config: Instancia de ETLConfig
            logger: Instancia de Logger
        """
        self.config = config
        self.logger = logger
    
    def validate_raw_data(self, file_path: Path) -> Tuple[bool, List[str]]:
        """
        Valida un archivo de datos raw
        
        Args:
            file_path: Path al archivo a validar
            
        Returns:
            Tupla (es_válido, lista_errores)
        """
        errors = []
        
        try:
            if not file_path.exists():
                errors.append(f"Archivo no encontrado: {file_path}")
                return False, errors
            
            # Cargar archivo JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validar estructura básica
            if not isinstance(data, dict):
                errors.append("El archivo debe contener un objeto JSON")
                return False, errors
            
            # Validar campos requeridos en el nivel superior
            required_top_fields = ['tienda', 'categoria', 'productos']
            for field in required_top_fields:
                if field not in data:
                    errors.append(f"Campo requerido faltante: {field}")
            
            # Validar productos
            productos = data.get('productos', [])
            if not isinstance(productos, list):
                errors.append("'productos' debe ser una lista")
            elif len(productos) == 0:
                errors.append("La lista de productos está vacía")
            else:
                # Validar estructura de productos
                product_errors = self._validate_raw_products(productos)
                errors.extend(product_errors)
            
            # Validar metadatos
            if 'fecha_extraccion' not in data:
                errors.append("Falta campo 'fecha_extraccion'")
            
            return len(errors) == 0, errors
            
        except json.JSONDecodeError as e:
            errors.append(f"Error de formato JSON: {e}")
            return False, errors
        except Exception as e:
            errors.append(f"Error inesperado: {e}")
            return False, errors
    
    def _validate_raw_products(self, productos: List[Dict]) -> List[str]:
        """Valida estructura de productos raw"""
        errors = []
        required_fields = ['id', 'nombre', 'precio', 'marca', 'categoria', 'url']
        
        for i, producto in enumerate(productos[:10]):  # Validar solo los primeros 10
            if not isinstance(producto, dict):
                errors.append(f"Producto {i} no es un objeto válido")
                continue
            
            for field in required_fields:
                if field not in producto:
                    errors.append(f"Producto {i}: falta campo '{field}'")
            
            # Validaciones específicas
            if 'precio' in producto:
                try:
                    precio = float(str(producto['precio']).replace(',', '').replace('$', ''))
                    if precio <= 0:
                        errors.append(f"Producto {i}: precio inválido")
                except (ValueError, TypeError):
                    errors.append(f"Producto {i}: precio no numérico")
        
        return errors
    
    def validate_unified_data(self) -> Tuple[bool, List[str]]:
        """
        Valida el archivo de datos unificados
        
        Returns:
            Tupla (es_válido, lista_errores)
        """
        errors = []
        file_path = self.config.unified_products_path
        
        try:
            if not file_path.exists():
                errors.append(f"Archivo unified_products.json no encontrado")
                return False, errors
            
            # Cargar archivo
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validar que sea una lista
            if not isinstance(data, list):
                errors.append("El archivo debe contener una lista de productos")
                return False, errors
            
            if len(data) == 0:
                errors.append("La lista de productos está vacía")
                return False, errors
            
            # Validar estructura de productos unificados
            unified_errors = self._validate_unified_products(data)
            errors.extend(unified_errors)
            
            # Validaciones adicionales
            validation_stats = self._get_validation_stats(data)
            
            # Verificar que hay productos de múltiples tiendas
            if validation_stats['unique_stores'] < 2:
                errors.append("Se esperan productos de al menos 2 tiendas")
            
            # Verificar que hay algunas comparaciones de precios
            if validation_stats['multi_store_products'] == 0:
                errors.append("No se encontraron productos con comparación de precios")
            
            self.logger.info(f"[VALIDACIÓN] Productos: {validation_stats['total_products']}")
            self.logger.info(f"[VALIDACIÓN] Tiendas: {validation_stats['unique_stores']}")
            self.logger.info(f"[VALIDACIÓN] Multi-tienda: {validation_stats['multi_store_products']}")
            
            return len(errors) == 0, errors
            
        except json.JSONDecodeError as e:
            errors.append(f"Error de formato JSON: {e}")
            return False, errors
        except Exception as e:
            errors.append(f"Error inesperado validando datos unificados: {e}")
            return False, errors
    
    def _validate_unified_products(self, productos: List[Dict]) -> List[str]:
        """Valida estructura de productos unificados"""
        errors = []
        required_fields = ['product_id', 'nombre', 'marca', 'categoria', 'tiendas']
        
        product_ids = set()
        
        for i, producto in enumerate(productos[:20]):  # Validar los primeros 20
            if not isinstance(producto, dict):
                errors.append(f"Producto {i} no es un objeto válido")
                continue
            
            # Validar campos requeridos
            for field in required_fields:
                if field not in producto:
                    errors.append(f"Producto {i}: falta campo '{field}'")
            
            # Validar product_id único
            product_id = producto.get('product_id')
            if product_id:
                if product_id in product_ids:
                    errors.append(f"Producto {i}: product_id duplicado: {product_id}")
                product_ids.add(product_id)
            
            # Validar tiendas
            tiendas = producto.get('tiendas', [])
            if not isinstance(tiendas, list):
                errors.append(f"Producto {i}: 'tiendas' debe ser una lista")
            elif len(tiendas) == 0:
                errors.append(f"Producto {i}: lista de tiendas vacía")
            else:
                # Validar estructura de tiendas
                tienda_errors = self._validate_tiendas(tiendas, i)
                errors.extend(tienda_errors)
        
        return errors
    
    def _validate_tiendas(self, tiendas: List[Dict], product_index: int) -> List[str]:
        """Valida estructura de tiendas dentro de un producto"""
        errors = []
        required_fields = ['fuente', 'precio', 'stock', 'url']
        
        for j, tienda in enumerate(tiendas):
            if not isinstance(tienda, dict):
                errors.append(f"Producto {product_index}, tienda {j}: no es un objeto válido")
                continue
            
            for field in required_fields:
                if field not in tienda:
                    errors.append(f"Producto {product_index}, tienda {j}: falta campo '{field}'")
            
            # Validar precio
            if 'precio' in tienda:
                try:
                    precio = float(tienda['precio'])
                    if precio <= 0:
                        errors.append(f"Producto {product_index}, tienda {j}: precio inválido")
                except (ValueError, TypeError):
                    errors.append(f"Producto {product_index}, tienda {j}: precio no numérico")
        
        return errors
    
    def _get_validation_stats(self, data: List[Dict]) -> Dict[str, Any]:
        """Obtiene estadísticas de validación"""
        stats = {
            'total_products': len(data),
            'unique_stores': set(),
            'multi_store_products': 0,
            'categories': set(),
            'brands': set()
        }
        
        for product in data:
            # Contar categorías y marcas
            if 'categoria' in product:
                stats['categories'].add(product['categoria'])
            if 'marca' in product:
                stats['brands'].add(product['marca'])
            
            # Analizar tiendas
            tiendas = product.get('tiendas', [])
            if len(tiendas) > 1:
                stats['multi_store_products'] += 1
            
            for tienda in tiendas:
                if 'fuente' in tienda:
                    stats['unique_stores'].add(tienda['fuente'])
        
        # Convertir sets a counts
        stats['unique_stores'] = len(stats['unique_stores'])
        stats['unique_categories'] = len(stats['categories'])
        stats['unique_brands'] = len(stats['brands'])
        
        return stats
    
    def validate_all_raw_files(self) -> Dict[str, Tuple[bool, List[str]]]:
        """
        Valida todos los archivos raw
        
        Returns:
            Dict con filename: (es_válido, errores)
        """
        results = {}
        
        for filename in self.config.expected_raw_files:
            file_path = self.config.raw_dir / filename
            is_valid, errors = self.validate_raw_data(file_path)
            results[filename] = (is_valid, errors)
            
            if is_valid:
                self.logger.info(f"[VALIDACIÓN] {filename}: OK")
            else:
                self.logger.error(f"[VALIDACIÓN] {filename}: {len(errors)} errores")
                for error in errors[:3]:  # Mostrar solo los primeros 3 errores
                    self.logger.error(f"  - {error}")
        
        return results
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Obtiene resumen completo de validación
        
        Returns:
            Dict con resumen de validación
        """
        # Validar archivos raw
        raw_results = self.validate_all_raw_files()
        raw_valid = sum(1 for is_valid, _ in raw_results.values() if is_valid)
        
        # Validar datos unificados
        unified_valid, unified_errors = self.validate_unified_data()
        
        return {
            "raw_files": {
                "total": len(raw_results),
                "valid": raw_valid,
                "invalid": len(raw_results) - raw_valid,
                "details": {filename: {"valid": is_valid, "error_count": len(errors)} 
                          for filename, (is_valid, errors) in raw_results.items()}
            },
            "unified_data": {
                "valid": unified_valid,
                "error_count": len(unified_errors),
                "errors": unified_errors[:10]  # Solo los primeros 10 errores
            },
            "overall_valid": raw_valid > 0 and unified_valid
        }



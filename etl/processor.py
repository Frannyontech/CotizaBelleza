"""
Orquestador del procesador de datos ETL
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List


class ProcessorOrchestrator:
    """Orquestador para el procesamiento de datos"""
    
    def __init__(self, config, logger):
        """
        Inicializa el orquestador del procesador
        
        Args:
            config: Instancia de ETLConfig
            logger: Instancia de Logger
        """
        self.config = config
        self.logger = logger
    
    def run_processor(self) -> bool:
        """
        Ejecuta el procesador para generar unified_products.json
        
        Returns:
            True si el procesamiento fue exitoso
        """
        self.logger.info("[PROCESANDO] Iniciando processor...")
        
        try:
            # Verificar archivos raw necesarios
            missing_files = self._check_raw_files()
            
            if missing_files:
                self.logger.warning(f"[ADVERTENCIA] Archivos faltantes en raw: {missing_files}")
                self.logger.info("Continuando con archivos disponibles...")
            
            # Ejecutar processor
            success = self._execute_processor()
            
            if success:
                self.logger.info("[OK] Processor completado exitosamente")
                return True
            else:
                self.logger.error("[ERROR] Processor falló")
                return False
                
        except Exception as e:
            self.logger.error(f"[ERROR] Error en processor: {e}")
            return False
    
    def _check_raw_files(self) -> List[str]:
        """
        Verifica qué archivos raw están disponibles
        
        Returns:
            Lista de archivos faltantes
        """
        missing_files = []
        available_files = []
        
        for filename in self.config.expected_raw_files:
            file_path = self.config.raw_dir / filename
            if file_path.exists():
                available_files.append(filename)
            else:
                missing_files.append(filename)
        
        self.logger.info(f"[ARCHIVOS] Disponibles: {len(available_files)}/{len(self.config.expected_raw_files)}")
        for filename in available_files:
            self.logger.info(f"[ARCHIVOS]   ✓ {filename}")
        
        if missing_files:
            for filename in missing_files:
                self.logger.warning(f"[ARCHIVOS]   ✗ {filename}")
        
        return missing_files
    
    def _execute_processor(self) -> bool:
        """
        Ejecuta el procesador de normalización
        
        Returns:
            True si fue exitoso
        """
        try:
            # Preparar entorno para el processor
            processor_dir = self.config.project_root / "processor"
            
            if not processor_dir.exists():
                raise FileNotFoundError(f"Directorio processor no encontrado: {processor_dir}")
            
            # Agregar processor al path
            sys.path.append(str(processor_dir))
            
            # Importar módulo del processor
            processor_config = self.config.processor_config
            module_name = processor_config["module"].split('.')[-1]
            
            try:
                processor_module = __import__(module_name)
                processor_function = getattr(processor_module, processor_config["function"])
            except (ImportError, AttributeError) as e:
                raise ImportError(f"No se pudo importar {processor_config['module']}: {e}")
            
            # Cambiar directorio de trabajo temporalmente
            original_cwd = os.getcwd()
            os.chdir(str(processor_dir))
            
            try:
                # Configurar argumentos para el processor
                output_path = str(self.config.unified_products_path)
                
                # Configurar sys.argv para el processor
                old_argv = sys.argv.copy()
                sys.argv = [
                    'normalize.py',
                    '--out', output_path
                ]
                
                self.logger.info(f"[PROCESANDO] Ejecutando processor con salida: {output_path}")
                
                # Ejecutar processor
                result = processor_function()
                
                # Restaurar sys.argv
                sys.argv = old_argv
                
                # Verificar resultado
                if result == 0 or result is None:
                    # Verificar que se generó el archivo
                    if self.config.unified_products_path.exists():
                        file_size = self.config.unified_products_path.stat().st_size
                        self.logger.info(f"[PROCESANDO] Archivo generado: {file_size:,} bytes")
                        return True
                    else:
                        self.logger.error("[PROCESANDO] Archivo no generado")
                        return False
                else:
                    self.logger.error(f"[PROCESANDO] Processor retornó código de error: {result}")
                    return False
                    
            finally:
                os.chdir(original_cwd)
                
        except Exception as e:
            self.logger.error(f"[PROCESANDO] Error ejecutando processor: {e}")
            return False
    
    def validate_processor_output(self) -> Dict[str, Any]:
        """
        Valida la salida del procesador
        
        Returns:
            Dict con resultados de validación
        """
        validation = {
            "file_exists": False,
            "file_size_bytes": 0,
            "file_size_mb": 0.0,
            "is_valid_json": False,
            "product_count": 0,
            "has_required_fields": False,
            "sample_product": None,
            "errors": []
        }
        
        try:
            output_file = self.config.unified_products_path
            
            # Verificar existencia
            if not output_file.exists():
                validation["errors"].append("Archivo unified_products.json no encontrado")
                return validation
            
            validation["file_exists"] = True
            
            # Obtener tamaño
            file_stat = output_file.stat()
            validation["file_size_bytes"] = file_stat.st_size
            validation["file_size_mb"] = round(file_stat.st_size / (1024 * 1024), 2)
            
            # Validar JSON
            import json
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            validation["is_valid_json"] = True
            
            # Validar estructura
            if not isinstance(data, list):
                validation["errors"].append("Archivo debe contener una lista")
                return validation
            
            if len(data) == 0:
                validation["errors"].append("Lista de productos está vacía")
                return validation
            
            validation["product_count"] = len(data)
            
            # Validar campos requeridos en muestra
            sample = data[0]
            validation["sample_product"] = sample
            
            required_fields = ['product_id', 'nombre', 'marca', 'categoria', 'tiendas']
            missing_fields = [field for field in required_fields if field not in sample]
            
            if missing_fields:
                validation["errors"].append(f"Campos faltantes en productos: {missing_fields}")
            else:
                validation["has_required_fields"] = True
            
            # Estadísticas adicionales
            self._add_processor_stats(validation, data)
            
        except json.JSONDecodeError as e:
            validation["errors"].append(f"Error de formato JSON: {e}")
        except Exception as e:
            validation["errors"].append(f"Error validando salida: {e}")
        
        return validation
    
    def _add_processor_stats(self, validation: Dict[str, Any], data: List[Dict]):
        """Agrega estadísticas adicionales a la validación"""
        try:
            # Contar categorías y tiendas
            categorias = set()
            tiendas = set()
            multi_store_products = 0
            
            for product in data:
                if 'categoria' in product:
                    categorias.add(product['categoria'])
                
                tiendas_producto = product.get('tiendas', [])
                if len(tiendas_producto) > 1:
                    multi_store_products += 1
                
                for tienda in tiendas_producto:
                    if 'fuente' in tienda:
                        tiendas.add(tienda['fuente'])
            
            validation["categories_count"] = len(categorias)
            validation["stores_count"] = len(tiendas)
            validation["multi_store_products"] = multi_store_products
            validation["categories"] = list(categorias)
            validation["stores"] = list(tiendas)
            
        except Exception as e:
            validation["errors"].append(f"Error calculando estadísticas: {e}")
    
    def get_processor_summary(self) -> Dict[str, Any]:
        """
        Obtiene resumen completo del procesamiento
        
        Returns:
            Dict con resumen del procesamiento
        """
        summary = {
            "input_files": {},
            "output_validation": {},
            "processing_stats": {}
        }
        
        # Analizar archivos de entrada
        total_input_products = 0
        for filename in self.config.expected_raw_files:
            file_path = self.config.raw_dir / filename
            if file_path.exists():
                try:
                    import json
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    product_count = len(data.get('productos', []))
                    total_input_products += product_count
                    
                    summary["input_files"][filename] = {
                        "exists": True,
                        "product_count": product_count,
                        "size_mb": round(file_path.stat().st_size / (1024 * 1024), 2)
                    }
                except Exception as e:
                    summary["input_files"][filename] = {
                        "exists": True,
                        "error": str(e)
                    }
            else:
                summary["input_files"][filename] = {"exists": False}
        
        # Validar salida
        summary["output_validation"] = self.validate_processor_output()
        
        # Estadísticas de procesamiento
        output_products = summary["output_validation"].get("product_count", 0)
        if total_input_products > 0 and output_products > 0:
            dedup_rate = (1 - output_products / total_input_products) * 100
            summary["processing_stats"] = {
                "input_products": total_input_products,
                "output_products": output_products,
                "deduplication_rate": round(dedup_rate, 1),
                "processing_efficiency": round(output_products / total_input_products * 100, 1)
            }
        
        return summary



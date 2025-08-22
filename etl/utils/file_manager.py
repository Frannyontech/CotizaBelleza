"""
Administrador de archivos para el sistema ETL
"""

import json
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class FileManager:
    """Administrador centralizado de archivos para ETL"""
    
    def __init__(self, config):
        """
        Inicializa el administrador de archivos
        
        Args:
            config: Instancia de ETLConfig
        """
        self.config = config
        self.logger = None
    
    def set_logger(self, logger):
        """Establece el logger para usar"""
        self.logger = logger
    
    def _log(self, level: str, message: str):
        """Log helper"""
        if self.logger:
            getattr(self.logger, level.lower())(message)
    
    def move_scraped_files_to_raw(self) -> int:
        """
        Mueve archivos generados por scrapers a data/raw/
        
        Returns:
            int: Número de archivos movidos
        """
        self._log("info", "[ARCHIVOS] Moviendo archivos a data/raw/...")
        
        # Directorios donde pueden estar los archivos generados
        source_dirs = [
            self.config.project_root / "scraper" / "data",
            self.config.data_dir
        ]
        
        moved_count = 0
        
        for source_dir in source_dirs:
            if not source_dir.exists():
                continue
                
            # Buscar archivos JSON de las tiendas
            for pattern in ["*_maquillaje*.json", "*_skincare*.json"]:
                for file_path in source_dir.glob(pattern):
                    target_path = self._determine_target_path(file_path)
                    
                    if target_path:
                        try:
                            shutil.move(str(file_path), str(target_path))
                            self._log("info", f"[MOVIDO] Movido: {file_path.name} -> {target_path.name}")
                            moved_count += 1
                        except Exception as e:
                            self._log("error", f"[ERROR] Error moviendo {file_path.name}: {e}")
        
        self._log("info", f"[ARCHIVOS] {moved_count} archivos movidos a data/raw/")
        return moved_count
    
    def _determine_target_path(self, file_path: Path) -> Optional[Path]:
        """
        Determina el path de destino para un archivo basado en su nombre
        
        Args:
            file_path: Path del archivo fuente
            
        Returns:
            Path del archivo destino o None si no se puede determinar
        """
        filename = file_path.name.lower()
        
        for store in self.config.stores_config.keys():
            for category in ["maquillaje", "skincare"]:
                if store in filename and category in filename:
                    target_name = f"{store}_{category}.json"
                    return self.config.raw_dir / target_name
        
        return None
    
    def check_raw_files_exist(self) -> Dict[str, bool]:
        """
        Verifica qué archivos raw existen
        
        Returns:
            Dict con nombre_archivo: existe
        """
        file_status = {}
        
        for filename in self.config.expected_raw_files:
            file_path = self.config.raw_dir / filename
            file_status[filename] = file_path.exists()
        
        return file_status
    
    def get_missing_raw_files(self) -> List[str]:
        """
        Obtiene lista de archivos raw faltantes
        
        Returns:
            Lista de nombres de archivos faltantes
        """
        file_status = self.check_raw_files_exist()
        return [filename for filename, exists in file_status.items() if not exists]
    
    def load_json_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Carga un archivo JSON de forma segura
        
        Args:
            file_path: Path al archivo JSON
            
        Returns:
            Dict con el contenido o None si hay error
        """
        try:
            if not file_path.exists():
                self._log("warning", f"[ARCHIVO] Archivo no encontrado: {file_path}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return data
            
        except Exception as e:
            self._log("error", f"[ERROR] Error cargando {file_path}: {e}")
            return None
    
    def save_json_file(self, data: Any, file_path: Path) -> bool:
        """
        Guarda datos en un archivo JSON
        
        Args:
            data: Datos a guardar
            file_path: Path del archivo destino
            
        Returns:
            True si fue exitoso, False en caso contrario
        """
        try:
            # Crear directorio padre si no existe
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self._log("info", f"[GUARDADO] Archivo guardado: {file_path}")
            return True
            
        except Exception as e:
            self._log("error", f"[ERROR] Error guardando {file_path}: {e}")
            return False
    
    def get_file_stats(self, file_path: Path) -> Dict[str, Any]:
        """
        Obtiene estadísticas de un archivo
        
        Args:
            file_path: Path al archivo
            
        Returns:
            Dict con estadísticas del archivo
        """
        stats = {
            "exists": False,
            "size_bytes": 0,
            "size_mb": 0.0,
            "modified": None,
            "records": 0
        }
        
        try:
            if file_path.exists():
                stat = file_path.stat()
                stats["exists"] = True
                stats["size_bytes"] = stat.st_size
                stats["size_mb"] = round(stat.st_size / (1024 * 1024), 2)
                stats["modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
                
                # Si es JSON, contar registros
                if file_path.suffix.lower() == '.json':
                    data = self.load_json_file(file_path)
                    if data:
                        if isinstance(data, list):
                            stats["records"] = len(data)
                        elif isinstance(data, dict) and "productos" in data:
                            stats["records"] = len(data["productos"])
        
        except Exception as e:
            self._log("warning", f"[STATS] Error obteniendo estadísticas de {file_path}: {e}")
        
        return stats
    
    def cleanup_old_files(self, directory: Path, pattern: str, keep_count: int = 5) -> int:
        """
        Limpia archivos antiguos manteniendo solo los más recientes
        
        Args:
            directory: Directorio a limpiar
            pattern: Patrón de archivos a limpiar
            keep_count: Número de archivos a mantener
            
        Returns:
            Número de archivos eliminados
        """
        try:
            if not directory.exists():
                return 0
            
            # Obtener archivos que coinciden con el patrón
            files = list(directory.glob(pattern))
            
            if len(files) <= keep_count:
                return 0
            
            # Ordenar por fecha de modificación (más recientes primero)
            files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # Eliminar archivos antiguos
            files_to_delete = files[keep_count:]
            deleted_count = 0
            
            for file_path in files_to_delete:
                try:
                    file_path.unlink()
                    self._log("info", f"[LIMPIEZA] Eliminado archivo antiguo: {file_path.name}")
                    deleted_count += 1
                except Exception as e:
                    self._log("warning", f"[LIMPIEZA] Error eliminando {file_path.name}: {e}")
            
            return deleted_count
            
        except Exception as e:
            self._log("error", f"[ERROR] Error en limpieza de archivos: {e}")
            return 0
    
    def create_backup(self, source_path: Path, backup_dir: Optional[Path] = None) -> Optional[Path]:
        """
        Crea una copia de seguridad de un archivo
        
        Args:
            source_path: Path del archivo fuente
            backup_dir: Directorio de backup (opcional)
            
        Returns:
            Path del archivo de backup o None si hay error
        """
        try:
            if not source_path.exists():
                return None
            
            if backup_dir is None:
                backup_dir = source_path.parent / "backups"
            
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Generar nombre de backup con timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{source_path.stem}_{timestamp}{source_path.suffix}"
            backup_path = backup_dir / backup_name
            
            shutil.copy2(source_path, backup_path)
            self._log("info", f"[BACKUP] Backup creado: {backup_path}")
            
            return backup_path
            
        except Exception as e:
            self._log("error", f"[ERROR] Error creando backup de {source_path}: {e}")
            return None



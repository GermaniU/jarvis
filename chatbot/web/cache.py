"""
Componente de caché para el motor web - Maneja almacenamiento y recuperación eficiente
"""
import os
import json
import hashlib
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger("web.cache")

class CacheManager:
    """Gestor de caché para el motor web"""
    
    def __init__(self, cache_dir: str, ttl: int = 86400):
        """
        Inicializa el gestor de caché
        
        Args:
            cache_dir: Directorio para almacenar la caché
            ttl: Tiempo de vida en segundos (predeterminado: 24 horas)
        """
        self.cache_dir = cache_dir
        self.ttl = ttl
        os.makedirs(cache_dir, exist_ok=True)
        
    def get_cache_path(self, key: str, prefix: str = "") -> str:
        """
        Genera una ruta de caché para una clave
        
        Args:
            key: Clave a hashear (consulta o URL)
            prefix: Prefijo opcional para el archivo
            
        Returns:
            Ruta al archivo de caché
        """
        # Crear un hash de la clave para el nombre de archivo
        key_hash = hashlib.md5(key.encode()).hexdigest()
        filename = f"{prefix}_{key_hash}.json" if prefix else f"{key_hash}.json"
        return os.path.join(self.cache_dir, filename)
    
    def is_valid(self, cache_path: str) -> bool:
        """
        Verifica si la caché es válida basada en TTL
        
        Args:
            cache_path: Ruta al archivo de caché
            
        Returns:
            True si la caché es válida, False en caso contrario
        """
        if not os.path.exists(cache_path):
            return False
            
        file_time = os.path.getmtime(cache_path)
        now = datetime.now().timestamp()
        return (now - file_time) < self.ttl
    
    def get(self, key: str, prefix: str = "") -> Optional[Dict[str, Any]]:
        """
        Recupera datos de la caché
        
        Args:
            key: Clave a buscar
            prefix: Prefijo opcional para el archivo
        
        Returns:
            Datos guardados o None si no existe o expiró
        """
        cache_path = self.get_cache_path(key, prefix)
        
        if not self.is_valid(cache_path):
            return None
            
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                logger.debug(f"Caché recuperada: {key}")
                return json.load(f)
        except Exception as e:
            logger.error(f"Error al leer caché: {e}")
            return None
    
    def set(self, key: str, data: Dict[str, Any], prefix: str = "") -> bool:
        """
        Guarda datos en la caché
        
        Args:
            key: Clave para guardar los datos
            data: Datos a guardar
            prefix: Prefijo opcional para el archivo
            
        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        cache_path = self.get_cache_path(key, prefix)
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Caché guardada: {key}")
            return True
        except Exception as e:
            logger.error(f"Error al guardar caché: {e}")
            return False
    
    def clear_old_items(self, days_old: int = 7) -> int:
        """
        Limpia archivos de caché más antiguos que un número específico de días
        
        Args:
            days_old: Días mínimos de antigüedad para eliminar
            
        Returns:
            Número de archivos eliminados
        """
        seconds_old = days_old * 86400
        count = 0
        
        try:
            now = datetime.now().timestamp()
            
            for filename in os.listdir(self.cache_dir):
                # Solo procesar archivos JSON (caché)
                if not filename.endswith('.json') or filename == 'preferences.json':
                    continue
                    
                file_path = os.path.join(self.cache_dir, filename)
                file_time = os.path.getmtime(file_path)
                age = now - file_time
                
                if age > seconds_old:
                    os.remove(file_path)
                    count += 1
            
            logger.info(f"Limpieza de caché: {count} archivos eliminados")
            return count
        except Exception as e:
            logger.error(f"Error al limpiar caché: {e}")
            return 0
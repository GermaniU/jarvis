"""
memoria_simple.py - Versión simplificada del gestor de memoria para fallback

Este módulo proporciona una alternativa simple al sistema completo de memoria
cuando hay problemas con la inicialización del sistema principal.
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger("memoria_simple")

class MemoryManagerSimple:
    """
    Implementación simplificada del gestor de memoria
    
    Esta clase ofrece la misma interfaz que MemoryManager pero con
    funcionalidad reducida, pensada para ser un fallback cuando
    no se puede inicializar el sistema completo de memoria.
    """
    
    def __init__(self, memory_dir: str = "memory"):
        """
        Inicializa el gestor de memoria simplificado
        
        Args:
            memory_dir: Directorio para almacenar archivos de memoria
        """
        self.memory_dir = memory_dir
        self.config_path = os.path.join(memory_dir, "configuracion.json")
        
        # Asegurar que exista el directorio
        os.makedirs(memory_dir, exist_ok=True)
        
        logger.info("Gestor de memoria simplificado inicializado")
    
    def guardar_recuerdo(self, contenido: str) -> bool:
        """
        Guarda un recuerdo en un archivo de texto
        
        Args:
            contenido: Contenido del recuerdo a guardar
            
        Returns:
            bool: True si se guardó correctamente, False en caso contrario
        """
        try:
            # Generar nombre de archivo con timestamp
            nombre = datetime.now().strftime("%Y%m%d_%H%M%S") + ".txt"
            path = os.path.join(self.memory_dir, nombre)
            
            # Guardar contenido
            with open(path, "w", encoding="utf-8") as f:
                f.write(contenido)
                
            logger.info(f"Recuerdo guardado en {nombre}")
            return True
        except Exception as e:
            logger.error(f"Error al guardar recuerdo: {e}")
            return False
    
    def obtener_ultimos_recuerdos(self, limite: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene los últimos recuerdos guardados
        
        Args:
            limite: Número máximo de recuerdos a devolver
            
        Returns:
            List[Dict[str, Any]]: Lista de recuerdos con metadatos
        """
        try:
            # Obtener archivos ordenados por fecha (más recientes primero)
            archivos = self._cargar_archivos_recuerdos()
            archivos = archivos[:limite]  # Limitar cantidad
            
            # Cargar contenido de cada archivo
            recuerdos = []
            for archivo in archivos:
                try:
                    ruta = os.path.join(self.memory_dir, archivo)
                    
                    # Extraer fecha del nombre
                    fecha = None
                    if "_" in archivo:
                        fecha_str = archivo.split("_")[0]
                        if len(fecha_str) == 8:  # Formato YYYYMMDD
                            fecha = f"{fecha_str[:4]}-{fecha_str[4:6]}-{fecha_str[6:]}"
                    
                    # Si no se pudo extraer del nombre, usar la del sistema de archivos
                    if not fecha:
                        fecha = datetime.fromtimestamp(os.path.getmtime(ruta)).strftime("%Y-%m-%d")
                    
                    # Leer contenido
                    with open(ruta, "r", encoding="utf-8") as f:
                        texto = f.read()
                    
                    recuerdos.append({
                        "archivo": archivo,
                        "fecha": fecha,
                        "contenido": texto
                    })
                except Exception as e:
                    logger.error(f"Error al leer recuerdo {archivo}: {e}")
            
            return recuerdos
        except Exception as e:
            logger.error(f"Error al obtener recuerdos: {e}")
            return []
    
    def _cargar_archivos_recuerdos(self) -> List[str]:
        """
        Obtiene la lista de archivos de recuerdos ordenados por fecha
        
        Returns:
            List[str]: Lista de nombres de archivo
        """
        try:
            archivos = [
                f for f in os.listdir(self.memory_dir)
                if f.endswith(".txt") and not f.startswith("config") and not f.startswith("preferencia_")
            ]
            
            # Ordenar por fecha de modificación (más recientes primero)
            archivos.sort(key=lambda x: os.path.getmtime(os.path.join(self.memory_dir, x)), reverse=True)
            return archivos
        except Exception as e:
            logger.error(f"Error al cargar archivos de recuerdos: {e}")
            return []
    
    def leer_recuerdo(self, nombre: str) -> str:
        """
        Lee el contenido de un recuerdo específico
        
        Args:
            nombre: Nombre del archivo de recuerdo
            
        Returns:
            str: Contenido del recuerdo o mensaje de error
        """
        try:
            ruta = os.path.join(self.memory_dir, nombre)
            with open(ruta, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error al leer el recuerdo {nombre}: {e}")
            return f"Error al leer el recuerdo: {e}"
    
    def obtener_contexto_relevante(self, pregunta: str, top_k: int = 3) -> str:
        """
        Versión simplificada que devuelve los últimos recuerdos sin búsqueda semántica
        
        Args:
            pregunta: Consulta a buscar (no se usa en la versión simple)
            top_k: Número de recuerdos a incluir
            
        Returns:
            str: Texto con los últimos recuerdos
        """
        recuerdos = self.obtener_ultimos_recuerdos(top_k)
        
        if not recuerdos:
            return ""
            
        # Formatear recuerdos como texto
        texto_contexto = []
        for r in recuerdos:
            texto_contexto.append(f"[Recuerdo del {r['fecha']}]\n{r['contenido']}\n")
            
        return "\n".join(texto_contexto)
    
    def cargar_configuracion(self) -> Dict[str, Any]:
        """
        Carga la configuración del sistema
        
        Returns:
            Dict[str, Any]: Configuración cargada o diccionario vacío
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error al cargar configuración: {e}")
            return {}
    
    def guardar_configuracion(self, configuracion: Dict[str, Any]) -> bool:
        """
        Guarda la configuración del sistema
        
        Args:
            configuracion: Diccionario con la configuración
            
        Returns:
            bool: True si se guardó correctamente, False en caso contrario
        """
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(configuracion, f, indent=2)
            logger.info("Configuración guardada")
            return True
        except Exception as e:
            logger.error(f"Error al guardar configuración: {e}")
            return False
    
    def obtener_ultima_interaccion(self) -> str:
        """
        Obtiene la fecha de la última interacción
        
        Returns:
            str: Fecha y hora de la última interacción o mensaje predeterminado
        """
        try:
            archivos = self._cargar_archivos_recuerdos()
            if not archivos:
                return "Sin interacciones previas"
                
            archivo_reciente = archivos[0]
            
            # Extraer fecha del nombre
            if "_" in archivo_reciente:
                partes = archivo_reciente.split("_")
                if len(partes) >= 2:
                    fecha_str = partes[0]
                    hora_str = partes[1].split(".")[0]
                    try:
                        fecha = f"{fecha_str[:4]}-{fecha_str[4:6]}-{fecha_str[6:]}"
                        hora = f"{hora_str[:2]}:{hora_str[2:4]}:{hora_str[4:]}" if len(hora_str) >= 6 else hora_str
                        return f"{fecha} {hora}"
                    except:
                        return archivo_reciente
            
            # Si no se pudo extraer del nombre, usar la del sistema de archivos
            ruta_completa = os.path.join(self.memory_dir, archivo_reciente)
            timestamp = os.path.getmtime(ruta_completa)
            return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logger.error(f"Error al obtener última interacción: {e}")
            return "Error al determinar fecha"
    
    def obtener_estadisticas_memoria(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas básicas del sistema de memoria
        
        Returns:
            Dict[str, Any]: Diccionario con estadísticas
        """
        try:
            archivos = self._cargar_archivos_recuerdos()
            
            # Calcular tamaño total
            tamano_total = 0
            for archivo in archivos:
                try:
                    ruta = os.path.join(self.memory_dir, archivo)
                    tamano_total += os.path.getsize(ruta)
                except:
                    pass
            
            # Calcular distribución temporal
            ahora = datetime.now()
            hoy = 0
            semana = 0
            mes = 0
            
            for archivo in archivos:
                try:
                    ruta = os.path.join(self.memory_dir, archivo)
                    fecha_mod = datetime.fromtimestamp(os.path.getmtime(ruta))
                    
                    # Contar por rangos de tiempo
                    delta = ahora - fecha_mod
                    
                    if delta.days == 0:  # Hoy
                        hoy += 1
                        semana += 1
                        mes += 1
                    elif delta.days < 7:  # Esta semana
                        semana += 1
                        mes += 1
                    elif delta.days < 30:  # Este mes
                        mes += 1
                except:
                    pass
            
            return {
                "total_recuerdos": len(archivos),
                "tamano_total_kb": tamano_total / 1024,
                "ultima_interaccion": self.obtener_ultima_interaccion(),
                "distribucion_temporal": {
                    "hoy": hoy,
                    "semana": semana,
                    "mes": mes
                }
            }
        except Exception as e:
            logger.error(f"Error al obtener estadísticas: {e}")
            return {
                "total_recuerdos": 0,
                "tamano_total_kb": 0,
                "ultima_interaccion": "Desconocida",
                "distribucion_temporal": {
                    "hoy": 0,
                    "semana": 0,
                    "mes": 0
                },
                "error": str(e)
            }
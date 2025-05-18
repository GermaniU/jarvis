"""
Módulo principal del chatbot de JARVIS
Este paquete contiene los componentes fundamentales para el funcionamiento
del asistente conversacional: motor LLM, gestor de memoria y motor web.
"""
import logging
import os
import sys
from typing import Dict, Any, Optional, List

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chatbot")

# Variables para controlar el estado de inicialización
_initialized = False
_available_models = []

# Importaciones con manejo de errores
try:
    from .llm_wrapper import create_chat_engine, SimpleChatEngine
    from .memoria import MemoryManager, configurar_embedding_model
    from .web import MotorWebPrivado
except ImportError as e:
    logger.error(f"Error al importar componentes del chatbot: {e}")
    
# Función para inicializar el chatbot
def initialize(
    model_name: str = "default",
    memory_enabled: bool = True, 
    web_enabled: bool = True,
    config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Inicializa todos los componentes del chatbot
    
    Args:
        model_name: Nombre del modelo LLM a utilizar
        memory_enabled: Activar capacidad de memoria
        web_enabled: Activar capacidad de búsqueda web
        config: Configuración adicional
        
    Returns:
        Dict[str, Any]: Diccionario con componentes inicializados
    """
    global _initialized
    
    if _initialized:
        logger.info("El chatbot ya se encuentra inicializado")
        return {}
        
    components = {}
    config = config or {}
    
    # Inicializar motor LLM
    try:
        components["chat_engine"] = create_chat_engine(model_name=model_name)
        logger.info(f"Motor LLM inicializado con modelo: {model_name}")
    except Exception as e:
        logger.error(f"Error al inicializar motor LLM: {e}")
        
    # Inicializar gestor de memoria
    if memory_enabled:
        try:
            components["memory_manager"] = MemoryManager(
                max_items=config.get("max_memory_items", 100)
            )
            logger.info("Gestor de memoria inicializado")
        except Exception as e:
            logger.error(f"Error al inicializar gestor de memoria: {e}")
            
    # Inicializar motor web
    if web_enabled:
        try:
            components["web_engine"] = MotorWebPrivado(
                cache_dir=config.get("web_cache_dir", "memory/web_cache"),
                dominios_preferidos=config.get("preferred_sources", []),
                dominios_bloqueados=config.get("blocked_domains", [])
            )
            logger.info("Motor web inicializado")
        except Exception as e:
            logger.error(f"Error al inicializar motor web: {e}")
            
    _initialized = True
    return components

def get_available_models() -> List[str]:
    """
    Obtiene la lista de modelos LLM disponibles
    
    Returns:
        List[str]: Lista de nombres de modelos
    """
    global _available_models
    
    if not _available_models:
        try:
            from .llm_wrapper import listar_modelos_disponibles
            _available_models = listar_modelos_disponibles()
        except (ImportError, AttributeError):
            # Si no existe la función, proporcionar modelos por defecto
            _available_models = ["llama3", "mistral-7b", "deepseek-r1:14b"]
            
    return _available_models

def reset() -> None:
    """
    Reinicia el estado del chatbot
    """
    global _initialized
    _initialized = False
    logger.info("Estado del chatbot reiniciado")

# Asegurar que el directorio de caché exista
os.makedirs("memory", exist_ok=True)
os.makedirs("memory/web_cache", exist_ok=True)

# Exportar clases y funciones principales
__all__ = [
    'create_chat_engine',
    'SimpleChatEngine',
    'MemoryManager',
    'configurar_embedding_model',
    'MotorWebPrivado',
    'initialize',
    'get_available_models',
    'reset'
]

# Proporcionar un módulo de importaciones LLM
try:
    from .llm_imports import obtener_imports as _get_llm_imports
    llm_imports = _get_llm_imports()
except ImportError as e:
    logger.error(f"Error importando llm_imports: {e}")
    llm_imports = {}

class llm_imports:
    """Clase contenedor para importaciones LLM"""
    @staticmethod
    def obtener_imports():
        """Devuelve un diccionario con las importaciones necesarias"""
        try:
            from .asistente import obtener_llm
            from .llm_wrapper import create_chat_engine, SimpleChatEngine
            
            return {
                "obtener_llm": obtener_llm,
                "create_chat_engine": create_chat_engine,
                "SimpleChatEngine": SimpleChatEngine
            }
        except ImportError as e:
            import logging
            logging.getLogger("chatbot").error(f"Error importando módulos LLM: {e}")
            return {}
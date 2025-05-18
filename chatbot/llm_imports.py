"""
Módulo para manejar importaciones problemáticas de llama_index
y evitar errores de importación circular
"""
import logging
import sys
import os

logger = logging.getLogger("llm_imports")

def import_llama_index():
    """
    Importa e inicializa componentes de llama_index de forma segura
    para evitar importaciones circulares
    
    Returns:
        dict: Componentes importados de llama_index
    """
    components = {}
    
    # Primera verificación: asegurarse de que llama_index está instalado
    try:
        import llama_index
        logger.info(f"llama_index encontrado. Versión: {llama_index.__version__}")
    except ImportError as e:
        logger.error(f"llama_index no está instalado: {e}")
        logger.error("Por favor, instala llama-index con 'pip install llama-index==0.9.4'")
        return components
    
    # Estrategia 1: Intento directo
    try:
        logger.info("Intentando importaciones directas...")
        import llama_index
        
        # Componentes básicos
        components["StorageContext"] = llama_index.StorageContext
        components["Document"] = llama_index.Document
        components["VectorStoreIndex"] = llama_index.VectorStoreIndex
        components["load_index_from_storage"] = llama_index.load_index_from_storage
        
        # Componentes adicionales
        components["ContextChatEngine"] = llama_index.chat_engine.ContextChatEngine
        components["ChatMessage"] = llama_index.llms.base.ChatMessage
        components["MessageRole"] = llama_index.llms.base.MessageRole
        
        logger.info("Importaciones directas exitosas")
        return components
    except Exception as e:
        logger.warning(f"Estrategia 1 falló: {e}")
    
    # Estrategia 2: Importaciones individuales
    try:
        logger.info("Intentando importaciones individuales...")
        
        # Componentes básicos
        try:
            from llama_index import StorageContext, Document, VectorStoreIndex
            from llama_index import load_index_from_storage
            
            components["StorageContext"] = StorageContext
            components["Document"] = Document
            components["VectorStoreIndex"] = VectorStoreIndex
            components["load_index_from_storage"] = load_index_from_storage
            
            logger.info("Componentes básicos importados correctamente")
        except ImportError as e:
            logger.error(f"Error al importar componentes básicos: {e}")
        
        # Componentes de chat
        try:
            from llama_index.chat_engine import ContextChatEngine
            from llama_index.llms.base import ChatMessage, MessageRole
            
            components["ContextChatEngine"] = ContextChatEngine
            components["ChatMessage"] = ChatMessage
            components["MessageRole"] = MessageRole
            
            logger.info("Componentes de chat importados correctamente")
        except ImportError as e:
            logger.warning(f"No se pudieron importar componentes de chat: {e}")
        
        return components
    except Exception as e:
        logger.warning(f"Estrategia 2 falló: {e}")
    
    # Estrategia 3: Último recurso con API directa
    try:
        logger.info("Intentando importaciones directas a la API...")
        
        # Esta es una última alternativa para casos extremos
        import importlib
        
        modules_to_try = [
            ("llama_index", ["StorageContext", "Document", "VectorStoreIndex", "load_index_from_storage"]),
            ("llama_index.chat_engine", ["ContextChatEngine"]),
            ("llama_index.llms.base", ["ChatMessage", "MessageRole"])
        ]
        
        for module_name, attrs in modules_to_try:
            try:
                module = importlib.import_module(module_name)
                for attr in attrs:
                    try:
                        components[attr] = getattr(module, attr)
                        logger.info(f"Importado {attr} desde {module_name}")
                    except AttributeError:
                        logger.warning(f"No se encontró {attr} en {module_name}")
            except ImportError:
                logger.warning(f"No se pudo importar {module_name}")
        
        return components
    except Exception as e:
        logger.error(f"Todas las estrategias de importación fallaron: {e}")
        return components
"""
llm_imports.py - Módulo para centralizar las importaciones relacionadas con LLM
Este enfoque ayuda a manejar las dependencias de forma más limpia
"""
import logging
logger = logging.getLogger("chatbot.llm_imports")

def obtener_imports():
    """
    Obtiene las importaciones necesarias para el sistema LLM
    
    Returns:
        dict: Diccionario con las clases y funciones importadas
    """
    imports = {}
    
    try:
        from .asistente import obtener_llm
        imports["obtener_llm"] = obtener_llm
    except ImportError as e:
        logger.error(f"Error importando módulo asistente: {e}")
    
    try:
        from .llm_wrapper import create_chat_engine, SimpleChatEngine
        imports["create_chat_engine"] = create_chat_engine
        imports["SimpleChatEngine"] = SimpleChatEngine
    except ImportError as e:
        logger.error(f"Error importando módulo llm_wrapper: {e}")
    
    try:
        from .llm_wrapper import listar_modelos_disponibles
        imports["listar_modelos_disponibles"] = listar_modelos_disponibles
    except ImportError:
        logger.warning("Función listar_modelos_disponibles no disponible")
        
    return imports
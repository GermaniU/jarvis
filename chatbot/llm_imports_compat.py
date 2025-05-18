"""
Módulo para manejar importaciones de llama-index versión 0.8.34
compatible con diferentes versiones de langchain
"""
import logging
import importlib.util

logger = logging.getLogger("llm_imports")

# Verificar langchain y corregir importaciones
def fix_langchain_imports():
    """
    Aplica monkey patching para corregir importaciones problemáticas
    en langchain
    """
    try:
        import langchain
        logger.info(f"Versión de langchain: {langchain.__version__}")
        
        # Verificar si existe BaseCache en langchain.cache
        try:
            from langchain_core.prompts import PromptTemplate
            from langchain_core.caches import BaseCache

            return True  # Ya existe, no necesita corrección
        except ImportError:
            # Intentar importar desde langchain_core
            try:
                import langchain_core
                from langchain_core.prompts import PromptTemplate
                from langchain_core.caches import BaseCache


                
                # Monkey patch para langchain.cache
                import sys
                import langchain_core.caches
                
                # Añadir BaseCache al módulo cache de langchain
                setattr(langchain_core.caches, "BaseCache", BaseCache)
                logger.info("Aplicado monkey patch para BaseCache")
                return True
            except ImportError:
                logger.error("No se pudo importar BaseCache desde langchain_core")
                return False
    except ImportError:
        logger.error("langchain no está instalado")
        return False

def import_llama_index():
    """
    Importa e inicializa componentes de llama-index 0.8.34
    
    Returns:
        dict: Componentes importados de llama_index
    """
    components = {}
    
    # Corregir importaciones de langchain primero
    fixed = fix_langchain_imports()
    if not fixed:
        logger.warning("No se pudieron corregir las importaciones de langchain")
    
    try:
        # Importación básica
        import llama_index
        logger.info(f"llama_index encontrado. Versión: {llama_index.__version__}")
        
        # En la versión 0.8.34, los componentes son importables directamente
        try:
            from llama_index import (
                VectorStoreIndex, 
                Document, 
                SimpleDirectoryReader,
                StorageContext,
                ServiceContext,
                LLMPredictor,
                load_index_from_storage
            )
            
            # Añadir componentes básicos
            components["VectorStoreIndex"] = VectorStoreIndex
            components["Document"] = Document
            components["SimpleDirectoryReader"] = SimpleDirectoryReader
            components["StorageContext"] = StorageContext
            components["ServiceContext"] = ServiceContext
            components["LLMPredictor"] = LLMPredictor
            components["load_index_from_storage"] = load_index_from_storage
            
        except ImportError as e:
            logger.error(f"Error al importar componentes básicos: {e}")
        
        # Importar LLMs Ollama (puede requerir instalación adicional)
        try:
            try:
                # En versiones antiguas, se usaba LangChain
                from langchain.llms import Ollama
                components["Ollama"] = Ollama
                logger.info("Ollama importado desde langchain")
            except ImportError:
                try:
                    # Intento desde langchain_community (versiones más nuevas)
                    from langchain_community.llms import Ollama
                    components["Ollama"] = Ollama
                    logger.info("Ollama importado desde langchain_community")
                except ImportError:
                    # Intento alternativo desde llama-index
                    from llama_index.llms import Ollama
                    components["Ollama"] = Ollama
                    logger.info("Ollama importado desde llama_index.llms")
        except ImportError:
            logger.warning("No se pudo importar Ollama")
            
            # Implementar una clase alternativa muy básica si todo lo demás falla
            class FallbackOllama:
                def __init__(self, model="", **kwargs):
                    self.model = model
                    self.kwargs = kwargs
                
                def __call__(self, prompt, **kwargs):
                    import subprocess
                    try:
                        cmd = ["curl", "-X", "POST", "http://localhost:11434/api/generate", 
                               "-d", f'{{"model": "{self.model}", "prompt": "{prompt}"}}']
                        result = subprocess.check_output(cmd, text=True)
                        return result
                    except Exception as e:
                        return f"Error al llamar a Ollama: {e}"
            
            components["Ollama"] = FallbackOllama
            logger.warning("Usando implementación alternativa de Ollama")
        
        # Chat engine
        try:
            from llama_index.indices.query.chat_engine import SimpleChatEngine
            components["ChatEngine"] = SimpleChatEngine
            logger.info("SimpleChatEngine importado correctamente")
        except ImportError as e:
            logger.warning(f"No se pudo importar SimpleChatEngine: {e}")
        
        logger.info(f"Se importaron {len(components)} componentes de llama_index correctamente")
        
    except ImportError as e:
        logger.error(f"llama_index no está instalado: {e}")
        
    return components
# main.py - versión con implementación minimalista
import os
import sys
import logging
from chatbot.memoria import configurar_embedding_model, MemoryManager

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("jarvis_main.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("main")
logger.info("Iniciando Jarvis...")

try:
    # Configurar modelo de embeddings
    configurar_embedding_model()

    # Crear instancia de memoria
    memoria = MemoryManager()

    # Importar LLM
    from chatbot.llm_wrapper import create_chat_engine
    logger.info("Creando motor de chat...")
    chat_engine = create_chat_engine()

    # Verificar argumentos
    usar_gui = any(arg in sys.argv for arg in ["--gui", "-g"])

    # Web opcional
    try:
        from chatbot.web import MotorWebPrivado
        web_disponible = True
        web = MotorWebPrivado()
        logger.info("Módulo web privado inicializado")
    except ImportError as e:
        web_disponible = False
        web = None
        logger.warning(f"Módulo web no disponible: {e}")

    componentes = {
        "web": web,
        "web_disponible": web_disponible,
        "chat_engine": chat_engine
    }

    from chatbot.interfaz import ejecutar_chat

    if usar_gui:
        logger.info("Iniciando interfaz gráfica...")
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("gui", "gui.py")
            gui = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(gui)
            gui.interfaz.launch(share=False, inbrowser=True)
        except Exception as e:
            logger.error(f"Error al iniciar interfaz gráfica: {e}")
            logger.info("Iniciando interfaz de consola como alternativa...")
            ejecutar_chat(memoria.index, chat_engine, componentes)
    else:
        logger.info("Iniciando interfaz de consola...")
        ejecutar_chat(memoria.index, chat_engine, componentes)

except Exception as e:
    logger.critical(f"Error crítico: {e}")
    print(f"Error al iniciar Jarvis: {e}")

"""
Implementación minimalista que evita problemas de dependencias
"""
import os
import sys
import logging
import json
import requests
from typing import List, Dict, Any, Optional

logger = logging.getLogger("llm_wrapper")

class SimpleDocument:
    """Documento simple con texto y metadatos"""
    def __init__(self, text, metadata=None):
        self.text = text
        self.metadata = metadata or {}

class OllamaLLM:
    """Cliente minimalista para Ollama"""
    def __init__(self, model="deepseek-r1:14b", temperature=0.1):
        self.model = model
        self.temperature = temperature
        self.base_url = "http://localhost:11434/api"
        
    def complete(self, prompt):
        """Obtiene una respuesta de Ollama"""
        url = f"{self.base_url}/generate"
        data = {
            "model": self.model,
            "prompt": prompt,
            "temperature": self.temperature,
            "stream": False
        }
        
        try:
            response = requests.post(url, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            
            # Formato de respuesta compatible
            class Response:
                def __init__(self, text):
                    self.text = text
                    self.response = text
                    
            return Response(result.get("response", ""))
        except Exception as e:
            logger.error(f"Error al llamar a Ollama: {e}")
            return type('obj', (object,), {'text': f"Error: {e}", 'response': f"Error: {e}"})

class SimpleChatEngine:
    """Motor de chat simplificado"""
    def __init__(self, documents=None):
        self.llm = OllamaLLM()
        self.documents = documents or []
        # Añadir atributo metadata para evitar errores
        self.metadata = {"type": "simple_chat_engine", "version": "1.0"}
        
    def chat(self, message, context=None):
        """Genera respuesta para un mensaje"""
        # Formatear contexto relevante
        context_text = ""
        if context:
            context_text = f"Contexto: {context}\n\n"
            
        # Construir prompt
        prompt = f"{context_text}Usuario: {message}\n\nAsistente:"
        
        # Obtener respuesta
        response = self.llm.complete(prompt)
        return response

def load_documents(directory):
    """Carga documentos desde un directorio"""
    documents = []
    if os.path.exists(directory):
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith((".txt", ".md")):
                    try:
                        with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                            text = f.read()
                            documents.append(SimpleDocument(
                                text=text, 
                                metadata={"source": os.path.join(root, file)}
                            ))
                    except Exception as e:
                        logger.error(f"Error al cargar {file}: {e}")
    return documents

def create_chat_engine():
    """Crea un motor de chat con documentos cargados"""
    documents = []
    
    # Cargar documentos de data/ y memory/
    for directory in ["data", "memory"]:
        if os.path.exists(directory):
            docs = load_documents(directory)
            documents.extend(docs)
            logger.info(f"Cargados {len(docs)} documentos de /{directory}")
    
    # Crear y devolver motor de chat
    return SimpleChatEngine(documents)

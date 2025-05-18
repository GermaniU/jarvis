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
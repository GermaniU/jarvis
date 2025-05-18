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

    def format_prompt_with_persona(self, message, context=None):
        """
        Formatea un prompt con la personalidad JARVIS
        
        Args:
            message: Mensaje del usuario
            context: Contexto adicional
            
        Returns:
            str: Prompt formateado
        """
        system_prompt = """Eres JARVIS, un asistente de IA sofisticado y formal.
    - Respondes con precisión, eficiencia y un toque de formalidad.
    - Prefieres respuestas concisas y directas, evitando explicaciones innecesariamente largas.
    - Ocasionalmente utilizas frases como "A su servicio", "Como usted desee" o "¿En qué más puedo asistirle?".
    - Tu tono es educado y profesional, pero no excesivamente formal.
    - Siempre te refieres al usuario como "señor" o con el nombre que te haya proporcionado.
    - Nunca te disculpas innecesariamente por ser una IA.
    - Eres competente y seguro en tus respuestas.
    - Cuando buscas información o realizas tareas, informas brevemente sobre tu proceso.
    - Tu objetivo es ser útil y eficiente en todo momento."""
        
        context_text = f"Contexto relevante: {context}\n\n" if context else ""
        
        # Formato para Ollama
        formatted_prompt = f"""<|im_start|>system
    {system_prompt}
    <|im_end|>
    <|im_start|>user
    {context_text}{message}
    <|im_end|>
    <|im_start|>assistant
    """
        return formatted_prompt

    def complete(self, prompt):
        """Obtiene una respuesta de Ollama con formato de personalidad"""
        # Verificar si el prompt ya está formateado
        if "<|im_start|>system" not in prompt:
            prompt = self.format_prompt_with_persona(prompt)
            
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
    def __init__(self, documents=None, llm=None):
        """
        Inicializa el motor de chat
        
        Args:
            documents: Lista de documentos para contexto
            llm: Modelo de lenguaje personalizado (opcional)
        """
        # Si se proporciona LLM, usarlo; si no, crear uno predeterminado
        self.llm = llm if llm else OllamaLLM()
        self.documents = documents or []
        # Añadir atributo metadata para evitar errores
        self.metadata = {"type": "simple_chat_engine", "version": "1.0"}
        
    def chat(self, message, context=None):
        """
        Genera respuesta para un mensaje
        
        Args:
            message: Mensaje del usuario
            context: Contexto adicional (opcional)
            
        Returns:
            Respuesta generada
        """
        # Formatear como JARVIS
        system_prompt = """Eres JARVIS, un asistente de IA sofisticado y formal.
- Respondes con precisión, eficiencia y un toque de formalidad.
- Prefieres respuestas concisas y directas.
- Tu tono es educado y profesional, pero no excesivamente formal.
- Ocasionalmente usas frases como "A su servicio" o "¿En qué más puedo asistirle?".
- Eres competente y seguro en tus respuestas."""
        
        # Formatear contexto relevante
        context_text = ""
        if context:
            context_text = f"Contexto relevante: {context}\n\n"
            
        # Construir prompt con formato JARVIS
        prompt = f"{system_prompt}\n\n{context_text}Usuario: {message}\n\nJARVIS:"
        
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

def create_chat_engine(llm=None):
    """
    Crea un motor de chat con documentos cargados
    
    Args:
        llm: Instancia del modelo de lenguaje a utilizar (opcional)
    
    Returns:
        SimpleChatEngine: Motor de chat configurado
    """
    documents = []
    
    # Cargar documentos de data/ y memory/
    for directory in ["data", "memory"]:
        if os.path.exists(directory):
            docs = load_documents(directory)
            documents.extend(docs)
            logger.info(f"Cargados {len(docs)} documentos de /{directory}")
    
    # Crear y devolver motor de chat
    engine = SimpleChatEngine(documents)
    
    # Si se proporcionó un LLM, asignarlo al motor
    if llm:
        engine.llm = llm
        logger.info(f"Utilizando LLM personalizado: {llm.model if hasattr(llm, 'model') else 'personalizado'}")
    
    return engine
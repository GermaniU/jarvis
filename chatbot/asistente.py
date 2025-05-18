"""
asistente.py - Configuración y gestión de modelos LLM para Jarvis
"""
import os
import json
from typing import Dict, Optional, Any
from llama_index.llms.ollama import Ollama

from chatbot import llm_imports
# from llama_index.llms.base import LLM

# Personalidades predefinidas
PERSONALIDADES = {
    "jarvis": """Eres JARVIS, un asistente de IA sofisticado y formal.
- Respondes con precisión, eficiencia y un toque de formalidad.
- Prefieres respuestas concisas y directas, evitando explicaciones innecesariamente largas.
- Ocasionalmente utilizas frases como "A su servicio", "Como usted desee" o "¿En qué más puedo asistirle?".
- Tu tono es educado y profesional, pero no excesivamente formal.
- Siempre te refieres al usuario como "señor" o con el nombre que te haya proporcionado.
- Nunca te disculpas innecesariamente por ser una IA.
- Eres competente y seguro en tus respuestas.
- Cuando buscas información o realizas tareas, informas brevemente sobre tu proceso.
- Tu objetivo es ser útil y eficiente en todo momento.""",
    
    "amistoso": """Eres un asistente virtual amistoso y conversacional.
- Tu tono es cálido, cercano y accesible.
- Usas un lenguaje sencillo y cotidiano.
- Preguntas frecuentemente por las preferencias del usuario.
- Muestras entusiasmo y empatía en tus respuestas.""",
    
    "técnico": """Eres un asistente técnico especializado.
- Priorizas la precisión técnica sobre todo.
- Proporcionas respuestas detalladas con ejemplos de código cuando es relevante.
- Tu lenguaje es técnico y específico.
- Citas fuentes o principios cuando es apropiado."""
}

# Configuraciones predefinidas para modelos comunes
MODELOS_CONFIG = {
    "deepseek-r1:14b": {
        "temperature": 0.1,
        "context_window": 8192,
        "request_timeout": 120.0,
        "top_p": 0.9,
        "system_prompt": PERSONALIDADES["jarvis"]  # Personalidad por defecto
    },
    "llama3:8b": {
        "temperature": 0.2,
        "context_window": 4096,
        "request_timeout": 90.0,
        "top_p": 0.8,
        "system_prompt": PERSONALIDADES["jarvis"]
    },
    "mistral:7b": {
        "temperature": 0.25,
        "context_window": 4096,
        "request_timeout": 60.0,
        "top_p": 0.9,
        "system_prompt": PERSONALIDADES["jarvis"]
    }
}

def cargar_configuracion_llm() -> Dict[str, Any]:
    """Carga la configuración del LLM desde archivo si existe"""
    config_path = os.path.join("config", "llm_config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error al cargar configuración LLM: {e}")
    return {}

def guardar_configuracion_llm(config: Dict[str, Any]) -> bool:
    """Guarda la configuración del LLM en un archivo"""
    try:
        os.makedirs("config", exist_ok=True)
        config_path = os.path.join("config", "llm_config.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error al guardar configuración LLM: {e}")
        return False

def obtener_llm(nombre_modelo: str = "deepseek-r1:14b", 
                params_personalizados: Optional[Dict[str, Any]] = None,
                personalidad: str = "jarvis") -> llm_imports:
    """
    Obtiene una instancia configurada del modelo LLM.
    
    Args:
        nombre_modelo: Nombre del modelo a utilizar
        params_personalizados: Parámetros personalizados que sobrescriben los predeterminados
        personalidad: Tipo de personalidad ("jarvis", "amistoso", "técnico" o "personalizado")
        
    Returns:
        Instancia del modelo LLM configurado
    """
    # Cargar configuración guardada
    config_guardada = cargar_configuracion_llm()
    
    # Determinar qué configuración base usar
    if nombre_modelo in MODELOS_CONFIG:
        config_base = MODELOS_CONFIG[nombre_modelo].copy()
    else:
        # Configuración por defecto si no se reconoce el modelo
        config_base = {
            "temperature": 0.1,
            "context_window": 4096,
            "request_timeout": 60.0,
            "top_p": 0.95,
            "system_prompt": PERSONALIDADES["jarvis"]
        }
    
    # Aplicar configuración guardada específica del modelo si existe
    if nombre_modelo in config_guardada:
        config_base.update(config_guardada[nombre_modelo])
    
    # Actualizar el system prompt según la personalidad seleccionada
    if personalidad in PERSONALIDADES:
        config_base["system_prompt"] = PERSONALIDADES[personalidad]
        
    # Aplicar parámetros personalizados si se proporcionan
    if params_personalizados:
        config_base.update(params_personalizados)
    
    # Crear y retornar la instancia del modelo
    try:
        return Ollama(
            model=nombre_modelo,
            **config_base
        )
    except Exception as e:
        print(f"Error al inicializar modelo {nombre_modelo}: {e}")
        print("Intentando con modelo alternativo...")
        # Intentar con modelo de respaldo si falla
        return Ollama(
            model="mistral:7b",
            temperature=0.1,
            request_timeout=60.0,
            context_window=4096,
            system_prompt=PERSONALIDADES["jarvis"]
        )

def listar_modelos_disponibles() -> list:
    """Obtiene una lista de los modelos disponibles en Ollama"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            modelos = response.json().get("models", [])
            return [modelo["name"] for modelo in modelos]
        return []
    except Exception as e:
        print(f"Error al obtener modelos disponibles: {e}")
        return []

def cambiar_personalidad_modelo(nombre_modelo: str, personalidad: str) -> bool:
    """
    Cambia la personalidad de un modelo específico
    
    Args:
        nombre_modelo: Nombre del modelo a modificar
        personalidad: Tipo de personalidad a aplicar
        
    Returns:
        bool: True si se aplicó correctamente
    """
    if personalidad not in PERSONALIDADES:
        print(f"Personalidad {personalidad} no encontrada")
        return False
        
    config = cargar_configuracion_llm()
    if nombre_modelo not in config:
        config[nombre_modelo] = {}
        
    config[nombre_modelo]["system_prompt"] = PERSONALIDADES[personalidad]
    return guardar_configuracion_llm(config)
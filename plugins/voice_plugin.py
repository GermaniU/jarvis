"""
voice_plugin.py - Plugin para sistema de voz mejorado para Jarvis
"""
import os
import re
import logging
import queue
import threading
import time
import json
from typing import Dict, List, Any, Optional

# Importamos la clase base Plugin
from plugins import Plugin

logger = logging.getLogger("voice_plugin")

class VoicePlugin(Plugin):
    """Plugin para manejo de voz en Jarvis"""
    
    # Metadatos del plugin
    name = "voice"
    description = "Sistema de voz mejorado para Jarvis"
    version = "1.0.0"
    author = "Jarvis Team"
    priority = 80  # Alta prioridad para funcionalidad básica
    
    # Comandos que reconoce directamente este plugin
    VOICE_COMMANDS = [
        "/voz on", "/voz off", "/voz velocidad", "/voz volumen",
        "/voces", "/voz cambiar", "/silencio", "/hablar"
    ]
    
    def __init__(self, jarvis_instance=None):
        """Inicializa el plugin de voz"""
        # Inicializar atributos antes de llamar a super().__init__
        # Esta es la línea clave que faltaba - la cola de mensajes de voz
        self.speech_queue = queue.Queue()
        
        # Ahora llamar al inicializador de la clase base
        super().__init__(jarvis_instance)
        
        # Configuración predeterminada
        self.config = {
            "voice_enabled": True,
            "voice_rate": 0,  # Velocidad normal
            "voice_volume": 100,  # Volumen máximo
            "preferred_voice": None,  # Voz predeterminada del sistema
            "language": "es",  # Español por defecto
            "wake_word": "jarvis",
            "listening_timeout": 5.0
        }
        
        # Cargar configuración personalizada si existe
        self.load_config()
        
        # Atributos para TTS y STT
        self.tts_engine = None
        self.stt_engine = None
        
        # Estado de escucha
        self.is_listening = False
        self.speech_thread = None
    
    def initialize(self) -> bool:
        """Inicializa los motores de voz"""
        try:
            # Inicializar Text-to-Speech
            self._initialize_tts()
            
            # Inicializar Speech-to-Text
            self._initialize_stt()
            
            # Iniciar hilo de trabajo para síntesis de voz
            self.speech_thread = threading.Thread(target=self._speech_worker, daemon=True)
            self.speech_thread.start()
            
            logger.info("Sistema de voz inicializado correctamente")
            return True
        except Exception as e:
            logger.error(f"Error al inicializar plugin de voz: {e}")
            return False
    
    def _initialize_tts(self) -> None:
        """Inicializa el motor text-to-speech"""
        try:
            import comtypes.client
            import pythoncom
            
            # Inicializar COM para este hilo
            pythoncom.CoInitialize()
            
            # Crear motor de voz
            self.tts_engine = comtypes.client.CreateObject("SAPI.SpVoice")
            
            # Configurar velocidad y volumen - CORREGIDO AQUÍ
            self.tts_engine.Rate = self.config["voice_rate"]  # Antes era 'rate'
            self.tts_engine.Volume = self.config["voice_volume"]  # Antes era 'volume'
            
            # Seleccionar voz preferida si está configurada
            if self.config["preferred_voice"]:
                voices = self.tts_engine.GetVoices()
                for i in range(voices.Count):
                    voice = voices.Item(i)
                    if self.config["preferred_voice"] in voice.GetDescription():
                        self.tts_engine.Voice = voice
                        break
            
            # Si no hay voz preferida, buscar una para el idioma configurado
            else:
                self._set_language_voice()
            
            logger.info(f"Usando voz en {self.config['language']}: {self.tts_engine.Voice.GetDescription()}")
            
        except ImportError:
            logger.warning("No se pudo inicializar motor TTS: comtypes no disponible")
            self.tts_engine = None
        except Exception as e:
            logger.error(f"Error al inicializar TTS: {e}")
            self.tts_engine = None
    
    def _initialize_stt(self) -> None:
        """Inicializa el motor speech-to-text"""
        # Implementación pendiente - puede usar bibliotecas como SpeechRecognition o Vosk
        self.stt_engine = None
    
    def _set_language_voice(self) -> None:
        """Configura una voz según el idioma preferido"""
        if not self.tts_engine:
            return
            
        try:
            voices = self.tts_engine.GetVoices()
            
            # Mapeo de códigos de idioma a palabras clave
            language_keywords = {
                "es": ["spanish", "español", "espanol"],
                "en": ["english", "inglés", "ingles"],
                "fr": ["french", "francés", "frances"],
                "de": ["german", "alemán", "aleman"],
                "pt": ["portuguese", "portugués", "portugues"]
            }
            
            keywords = language_keywords.get(self.config["language"], ["spanish"])
            
            # Buscar voz con el idioma correcto
            for i in range(voices.Count):
                voice = voices.Item(i)
                description = voice.GetDescription().lower()
                
                for keyword in keywords:
                    if keyword.lower() in description:
                        self.tts_engine.Voice = voice
                        logger.info(f"Configuración de voz cargada")
                        return
            
            # Si no se encontró voz específica, usar la predeterminada
            logger.warning(f"No se encontró voz para idioma {self.config['language']}, usando predeterminada")
            
        except Exception as e:
            logger.error(f"Error al configurar idioma de voz: {e}")
    
    def _speech_worker(self) -> None:
        """Hilo de trabajo para procesar cola de mensajes de voz"""
        while True:
            try:
                # Verificar si hay mensajes en la cola
                if not self.speech_queue.empty():
                    text = self.speech_queue.get()
                    
                    if text and self.tts_engine and self.config["voice_enabled"]:
                        # Procesar y reproducir voz
                        self.tts_engine.Speak(text)
                    
                    self.speech_queue.task_done()
                else:
                    # Dormir para no consumir CPU
                    time.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"Error en hilo de voz: {e}")
                time.sleep(1)  # Evitar bucles rápidos en caso de error
    
    def speak(self, text: str) -> None:
        """
        Reproduce texto como voz
        
        Args:
            text: Texto a convertir en voz
        """
        if not text or not self.config["voice_enabled"]:
            return
            
        # Agregar texto a la cola para procesamiento asíncrono
        self.speech_queue.put(text)
    
    def on_response_generated(self, message: str, response: str, user_id: str = None) -> str:
        """
        Intercepta respuestas generadas para reproducirlas por voz
        
        Args:
            message: Mensaje original
            response: Respuesta generada
            user_id: ID del usuario
            
        Returns:
            str: Respuesta sin modificar
        """
        # Solo reproducir respuestas cortas para no saturar
        if len(response) < 300:
            self.speak(response)
        else:
            # Para respuestas largas, extraer un resumen o primera parte
            first_paragraph = response.split('\n\n')[0]
            if len(first_paragraph) > 150:
                first_paragraph = first_paragraph[:150] + "..."
            self.speak(first_paragraph)
            
        return response
    
    def get_commands(self) -> Dict[str, Any]:
        """Comandos proporcionados por este plugin"""
        return {
            "voz": self.cmd_toggle_voice,
            "volumen": self.cmd_set_volume,
            "velocidad": self.cmd_set_rate,
            "escuchar": self.cmd_listen
        }
    
    def cmd_toggle_voice(self, *args) -> str:
        """Activa o desactiva la voz"""
        self.config["voice_enabled"] = not self.config["voice_enabled"]
        self.save_config()
        
        status = "activada" if self.config["voice_enabled"] else "desactivada"
        return f"Voz {status}"
    
    def cmd_set_volume(self, *args) -> str:
        """
        Ajusta el volumen de la voz (0-100)
        Uso: volumen [nivel]
        """
        if not args:
            return f"Volumen actual: {self.config['voice_volume']}"
            
        try:
            volume = int(args[0])
            volume = max(0, min(100, volume))  # Limitar entre 0-100
            
            # Reinicializar el motor si es necesario
            if volume != self.config["voice_volume"]:
                self.config["voice_volume"] = volume
                
                if self.tts_engine:
                    self.tts_engine.Volume = volume
                    # Hablar para confirmar el cambio
                    self.speak(f"Volumen ajustado a {volume}")
                    
                self.save_config()
                return f"Volumen ajustado a {volume}"
        except ValueError:
            return "Error: El volumen debe ser un número entre 0 y 100"
    
    def cmd_set_rate(self, *args) -> str:
        """
        Ajusta la velocidad de la voz (-10 a 10)
        Uso: velocidad [nivel]
        """
        if not args:
            return f"Velocidad actual: {self.config['voice_rate']}"
            
        try:
            rate = int(args[0])
            rate = max(-10, min(10, rate))  # Limitar entre -10 y 10
            
            self.config["voice_rate"] = rate
            if self.tts_engine:
                self.tts_engine.Rate = rate
                
            self.save_config()
            return f"Velocidad ajustada a {rate}"
        except ValueError:
            return "Error: La velocidad debe ser un número entre -10 y 10"
    
    def cmd_listen(self, *args) -> str:
        """Activa el modo de escucha por voz"""
        if not self.stt_engine:
            return "Lo siento, el reconocimiento de voz no está disponible"
            
        # Implementación pendiente
        return "Modo de escucha no implementado aún"
    
    def shutdown(self) -> bool:
        """Limpia recursos al desactivar el plugin"""
        try:
            # Liberar recursos de voz
            self.tts_engine = None
            
            # Liberar COM si es necesario
            try:
                import pythoncom
                pythoncom.CoUninitialize()
            except:
                pass
                
            logger.info("Recursos de voz liberados")
            return True
        except Exception as e:
            logger.error(f"Error al liberar recursos de voz: {e}")
            return False
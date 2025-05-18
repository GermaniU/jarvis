"""
main.py - Punto de entrada principal para Jarvis usando el sistema de plugins

Este módulo orquesta la inicialización de todos los componentes y 
proporciona un punto de entrada único para la interfaz de usuario.

Mejoras:
- Sistema modular basado en plugins
- Manejo mejorado de errores y dependencias
- Alternativas de interfaz (CLI/GUI) de forma unificada
"""
import os
import sys
import logging
import argparse
from typing import Dict, List, Any, Optional
import re

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

class Jarvis:
    """Clase principal que coordina todos los componentes del sistema"""
    
    def __init__(self):
        """Inicializa la instancia de Jarvis"""
        self.version = "2.0.0"
        self.name = "Jarvis"
        self.plugins = None
        self.memoria = None
        self.web = None
        self.llm = None
        self.chat_engine = None
        self.interfaz = None
        self.componentes = {}
        self.memory_dir = "memory"  # Añade esta línea
        
        logger.info(f"Inicializando {self.name} v{self.version}")
    
    def inicializar(self) -> bool:
        """
        Inicializa todos los componentes del sistema en el orden correcto
        
        Returns:
            bool: True si todos los componentes esenciales se inicializaron correctamente
        """
        logger.info("Comenzando inicialización de componentes...")
        
        # Inicializar sistema de memoria (componente crítico)
        if not self._inicializar_memoria():
            logger.critical("Error al inicializar sistema de memoria. Abortando.")
            return False
        
        # Inicializar sistema de plugins
        self._inicializar_plugins()
        
        # Inicializar modelo de lenguaje
        self._inicializar_llm()
        
        # Inicializar componentes adicionales a través de plugins
        if self.plugins:
            self.plugins.initialize_plugins()
            
            # Verificar si se cargaron los plugins esenciales
            if not self._verificar_plugins_requeridos():
                logger.warning("No se pudieron cargar todos los plugins requeridos")
                # Continuar, pero con funcionalidad limitada
        
        logger.info("Sistema inicializado correctamente")
        return True
    
    def _inicializar_memoria(self) -> bool:
        """
        Inicializa el sistema de memoria y embeddings
        
        Returns:
            bool: True si se inicializó correctamente
        """
        try:
            logger.info("Inicializando sistema de memoria híbrida...")
            
            # Importar adaptador de memoria
            try:
                from chatbot.memoria_hibrida import MemoryAdapter
                # Crear instancia del adaptador que elegirá el mejor sistema disponible
                self.memoria = MemoryAdapter(memory_dir=self.memory_dir)
                logger.info("Adaptador de memoria híbrida inicializado correctamente")
            except ImportError as e:
                logger.warning(f"Adaptador de memoria híbrida no disponible: {e}")
                # Continuar con el sistema tradicional
                raise ImportError("Fallback a sistema tradicional")
                
            # Registrar en componentes
            self.componentes["memoria"] = self.memoria
            
            # Verificar y registrar capacidades disponibles
            if hasattr(self.memoria, "tiene_capacidad"):
                capacidades = {
                    "vectorial": self.memoria.tiene_capacidad("vectorial"),
                    "hibrida": self.memoria.tiene_capacidad("hibrida"),
                    "temas_importantes": self.memoria.tiene_capacidad("temas_importantes")
                }
                logger.info(f"Capacidades de memoria: {capacidades}")
            
            return True
        except Exception as e:
            logger.error(f"Error al inicializar sistema de memoria híbrida: {e}")
            
            # Intentar crear una versión tradicional de memoria como fallback
            try:
                logger.info("Inicializando sistema de memoria tradicional...")
                from chatbot.memoria import configurar_embedding_model, MemoryManager
                embedding_ok = configurar_embedding_model()
                self.memoria = MemoryManager()
                if not hasattr(self.memoria, 'index') or self.memoria.index is None:
                    logger.warning("Memoria inicializada pero sin índice de vectores disponible")
                else:
                    logger.info("Sistema de memoria tradicional inicializado con índice de vectores")
                    
                # Registrar en componentes
                self.componentes["memoria"] = self.memoria
                return True
            except Exception as e2:
                logger.error(f"Error al inicializar memoria vectorial: {e2}")
                
                # Último intento: memoria simple
                try:
                    from chatbot.memoria_simple import MemoryManagerSimple
                    self.memoria = MemoryManagerSimple()
                    logger.warning("Se ha inicializado memoria simple como alternativa final")
                    self.componentes["memoria"] = self.memoria
                    return True
                except Exception as e3:
                    logger.critical(f"Error crítico al crear cualquier sistema de memoria: {e3}")
                    return False
            
    def _inicializar_plugins(self) -> None:
        """Inicializa el sistema de plugins"""
        try:
            logger.info("Inicializando sistema de plugins...")
            
            # Importar gestor de plugins
            from plugins import PluginManager
            
            # Crear gestor de plugins
            self.plugins = PluginManager(plugins_dir="plugins", jarvis_instance=self)
            
            # Cargar plugins disponibles
            num_plugins = self.plugins.load_plugins()
            logger.info(f"Se cargaron {num_plugins} plugins")
            
            # No inicializamos aún, eso se hace después de cargar los componentes críticos
            
            # Registrar en componentes
            self.componentes["plugins"] = self.plugins
        except Exception as e:
            logger.error(f"Error al inicializar sistema de plugins: {e}")
            logger.warning("Sistema de plugins no disponible. Funcionalidad limitada.")
    
    def _inicializar_llm(self) -> None:
        """Inicializa el modelo de lenguaje y chat engine"""
        try:
            logger.info("Inicializando modelo de lenguaje...")
            
            # Importar módulos para LLM con manejo de errores
            try:
                from chatbot.asistente import obtener_llm
            except ImportError as e:
                logger.error(f"No se pudo importar obtener_llm: {e}")
                return
            
            try:
                from chatbot.llm_wrapper import create_chat_engine
            except ImportError as e:
                logger.error(f"No se pudo importar create_chat_engine: {e}")
                return
            
            # Obtener LLM con personalidad Jarvis
            self.llm = obtener_llm(personalidad="jarvis")
            
            # Crear chat engine
            self.chat_engine = create_chat_engine(self.llm)
            
            logger.info(f"Modelo de lenguaje inicializado: {self.llm.model if hasattr(self.llm, 'model') else 'desconocido'}")
            
            # Registrar en componentes
            self.componentes["llm"] = self.llm
            self.componentes["chat_engine"] = self.chat_engine
        except Exception as e:
            logger.error(f"Error al inicializar modelo de lenguaje: {e}")
            logger.warning("Sistema funcionará sin procesamiento de lenguaje natural")
    
    def _verificar_plugins_requeridos(self) -> bool:
        """
        Verifica que todos los plugins requeridos estén cargados y activados
        
        Returns:
            bool: True si todos los plugins requeridos están disponibles
        """
        # Lista de plugins que deberían estar disponibles
        plugins_requeridos = []
        
        # Verificar cada uno
        missing = []
        for plugin_name in plugins_requeridos:
            if not self.plugins or plugin_name not in self.plugins.plugins:
                missing.append(plugin_name)
        
        if missing:
            logger.warning(f"Los siguientes plugins requeridos no están disponibles: {', '.join(missing)}")
            return False
        
        return True
    
    def iniciar_interfaz(self, modo: str = "cli") -> None:
        """
        Inicia la interfaz de usuario
        
        Args:
            modo: Tipo de interfaz ('cli' para línea de comandos o 'gui' para interfaz gráfica)
        """
        logger.info(f"Iniciando interfaz en modo: {modo}")
        
        if modo == "gui":
            self._iniciar_gui()
        else:
            self._iniciar_cli()
    
    def _iniciar_cli(self) -> None:
        """Inicia la interfaz de línea de comandos"""
        try:
            from chatbot.interfaz import ejecutar_chat
            logger.info("Iniciando interfaz de línea de comandos...")
            ejecutar_chat(
                indice=self.memoria.index if hasattr(self.memoria, 'index') else None,
                llm=self.llm,
                chat_engine=self.chat_engine,
                componentes=self.componentes
            )
        except Exception as e:
            logger.error(f"Error al iniciar interfaz CLI: {e}")
            logger.critical("No se pudo iniciar ninguna interfaz. Terminando aplicación.")
            sys.exit(1)
    
    def _iniciar_gui(self) -> None:
        """Inicia la interfaz gráfica"""
        try:
            # Verificar si el módulo de GUI está disponible
            logger.info("Intentando iniciar interfaz gráfica...")
            
            import importlib.util
            spec = importlib.util.spec_from_file_location("gui", "gui.py")
            
            if spec and spec.loader:
                gui = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(gui)
                
                # Injección de dependencias
                if hasattr(gui, 'set_jarvis_instance'):
                    gui.set_jarvis_instance(self)
                
                # Iniciar GUI
                self.interfaz = gui.interfaz
                gui.interfaz.launch(share=False, inbrowser=True)
                return
            else:
                raise ImportError("No se pudo cargar el módulo de GUI")
                
        except Exception as e:
            logger.error(f"Error al iniciar interfaz gráfica: {e}")
            logger.warning("Fallback a interfaz de línea de comandos")
            self._iniciar_cli()
    
    def procesar_mensaje(self, mensaje: str, user_id: str = None) -> str:
        """
        Procesa un mensaje y devuelve una respuesta
        
        Args:
            mensaje: Mensaje a procesar
            user_id: ID del usuario (opcional)
            
        Returns:
            str: Respuesta al mensaje
        """
        # Analizar si el mensaje contiene temas importantes
        self._analizar_temas_importantes(mensaje)
        
        # Intentar procesar con plugins primero
        if self.plugins:
            try:
                respuesta_plugin = self.plugins.process_message(mensaje, user_id)
                if respuesta_plugin:
                    # Guardar interacción en memoria
                    self._guardar_en_memoria(mensaje, respuesta_plugin, 
                                            es_plugin=True, 
                                            plugin_name=getattr(self.plugins, "last_plugin_name", None))
                    
                    # Aplicar modificaciones de plugins
                    if hasattr(self.plugins, "modify_response"):
                        respuesta_plugin = self.plugins.modify_response(mensaje, respuesta_plugin, user_id)
                        
                    return respuesta_plugin
            except Exception as e:
                logger.error(f"Error al procesar mensaje con plugins: {e}")
                # Continuar con procesamiento normal si falla el plugin
    
        try:
            # Verificar disponibilidad del motor de chat
            if not self.chat_engine:
                return "Lo siento, el sistema de procesamiento de lenguaje no está disponible."
            
            # Obtener contexto relevante de la memoria
            contexto = self._obtener_contexto_memoria(mensaje)
            
            # Generar respuesta según el tipo de chat_engine disponible
            if hasattr(self.chat_engine, 'chat'):
                # Formatear el prompt con instrucciones más claras y específicas
                sistema_prompt = """
                        Eres JARVIS, un asistente personal con memoria persistente. La siguiente información proviene de tu memoria y DEBES utilizarla para personalizar tu respuesta:

                        MEMORIA:
                        {}

                        INSTRUCCIÓN: Si encuentras "mi nombre es X" o similar en la memoria, SIEMPRE dirígete al usuario como X.
                        Si hay alguna preferencia, dato personal o información importante en la memoria, DEMÚESTRALO claramente en tu respuesta utilizando esos datos.

                        Consulta del usuario: {}
                        """

                # Si hay contexto, formatearlo adecuadamente
                if contexto:
                    prompt_completo = sistema_prompt.format(contexto, mensaje)
                else:
                    prompt_completo = mensaje
    
                # Generar respuesta
                respuesta_obj = self.chat_engine.chat(prompt_completo)
                respuesta = respuesta_obj.text if hasattr(respuesta_obj, 'text') else str(respuesta_obj)
            else:
                # Fallback a LLM directo
                prompt = f"{contexto}\n\nUsuario: {mensaje}\n\nAsistente:"
                respuesta = self.llm.complete(prompt).text
            
            # Limpiar respuesta (eliminar thinking)
            respuesta = self._limpiar_respuesta(respuesta)
            
            # Guardar interacción en memoria
            es_importante = self._detectar_info_importante(mensaje, respuesta)
            self._guardar_en_memoria(mensaje, respuesta, es_importante=es_importante)
            
            # Aplicar modificaciones de plugins
            if self.plugins and hasattr(self.plugins, "modify_response"):
                respuesta = self.plugins.modify_response(mensaje, respuesta, user_id)
                
            info_personal = self._obtener_info_personal()
            if info_personal:
                info_formateada = "\n".join([f"- {k.capitalize()}: {v}" for k, v in info_personal.items()])
                contexto = f"INFORMACIÓN PERSONAL DEL USUARIO:\n{info_formateada}\n\n{contexto}"

            return respuesta
            
        except Exception as e:
            logger.error(f"Error al procesar mensaje: {e}")
            return f"Lo siento, ha ocurrido un error al procesar tu mensaje: {e}"
    
    def _obtener_contexto_memoria(self, mensaje: str) -> str:
            """
            Obtiene contexto relevante de la memoria para una consulta,
            asegurándose de incluir siempre información personal
            """
            if not self.memoria:
             return ""
            
            try:
                # Primero, intentar obtener información personal del usuario
                info_personal = self._obtener_info_personal()
                contexto_personal = ""
                
                if info_personal:
                    contexto_personal = "INFORMACIÓN PERSONAL DEL USUARIO:\n"
                    for clave, valor in info_personal.items():
                        contexto_personal += f"- {clave.capitalize()}: {valor}\n"
                    contexto_personal += "\n"
                
                # Luego obtener contexto relevante según capacidades disponibles
                contexto_general = ""
                
                # PRIMERA ESTRATEGIA: contexto combinado (híbrido)
                if hasattr(self.memoria, 'obtener_contexto_combinado'):
                    try:
                        resultados = self.memoria.obtener_contexto_combinado(mensaje, top_k=5)
                        if resultados:
                            contexto_general = self._formatear_resultados_memoria(resultados)
                    except Exception as e:
                        logger.error(f"Error al obtener contexto combinado: {e}")
                        # Continuar con otras estrategias
                
                # SEGUNDA ESTRATEGIA: contexto relevante estándar
                if not contexto_general and hasattr(self.memoria, 'obtener_contexto_relevante'):
                    try:
                        contexto_general = self.memoria.obtener_contexto_relevante(mensaje)
                    except Exception as e:
                        logger.error(f"Error al obtener contexto relevante: {e}")
                
                # TERCERA ESTRATEGIA: búsqueda simple
                if not contexto_general and hasattr(self.memoria, 'buscar_recuerdos'):
                    try:
                        recuerdos = self.memoria.buscar_recuerdos(mensaje, limite=3)
                        contexto_general = "\n\n".join(recuerdos) if recuerdos else ""
                    except Exception as e:
                        logger.error(f"Error al buscar recuerdos: {e}")
                
                # ESTRATEGIA FINAL: últimos recuerdos
                if not contexto_general:
                    try:
                        if hasattr(self.memoria, 'obtener_ultimos_recuerdos'):
                            ultimos = self.memoria.obtener_ultimos_recuerdos(3)
                            if ultimos:
                                contexto_general = self._formatear_resultados_memoria(ultimos)
                        elif hasattr(self.memoria, 'obtener_recuerdos_recientes'):
                            recientes = self.memoria.obtener_recuerdos_recientes(limite=3)
                            if recientes:
                                contexto_general = self._formatear_resultados_memoria(recientes)
                    except Exception as e:
                        logger.error(f"Error al obtener últimos recuerdos: {e}")
                
                # Combinar ambos contextos, priorizando información personal
                return contexto_personal + contexto_general
            except Exception as e:
                logger.error(f"Error al obtener contexto de memoria: {e}")
                return ""
    
    def _limpiar_respuesta(self, respuesta: str) -> str:
        """
        Limpia la respuesta eliminando marcadores internos
        
        Args:
            respuesta: Respuesta original
            
        Returns:
            str: Respuesta limpia
        """
        # Eliminar sección thinking si existe
        if "<think>" in respuesta and "</think>" in respuesta:
            partes = respuesta.split("</think>")
            respuesta = partes[-1].strip()
        
        # Eliminar otros posibles marcadores
        respuesta = re.sub(r'<internal>.*?</internal>', '', respuesta, flags=re.DOTALL)
        
        return respuesta.strip()

    def _guardar_en_memoria(self, mensaje: str, respuesta: str, 
                           es_importante: bool = False, 
                           es_plugin: bool = False,
                           plugin_name: str = None) -> None:
        """
        Guarda una interacción en la memoria con manejo avanzado
        
        Args:
            mensaje: Mensaje del usuario
            respuesta: Respuesta del sistema
            es_importante: Si debe marcarse como importante
            es_plugin: Si la respuesta proviene de un plugin
            plugin_name: Nombre del plugin que generó la respuesta
        """
        if not self.memoria:
            return
            
        try:
            # Determinar si es importante
            if es_plugin and plugin_name in ["aprendizaje", "recordar", "info", "personal"]:
                es_importante = True
                
            # Formatear interacción para guardar
            texto_interaccion = f"Usuario: {mensaje}\nAsistente: {respuesta}"
            
            # Añadir metadatos si es respuesta de plugin
            if es_plugin and plugin_name:
                texto_interaccion = f"[Plugin: {plugin_name}] {texto_interaccion}"
                
            # Usar el método adecuado según capacidades
            if hasattr(self.memoria, "guardar_recuerdo"):
                # Verificar si el método acepta el parámetro es_importante
                import inspect
                params = inspect.signature(self.memoria.guardar_recuerdo).parameters
                
                if "es_importante" in params:
                    self.memoria.guardar_recuerdo(texto_interaccion, es_importante=es_importante)
                else:
                    # Versión simple sin soporte para marcar importancia
                    self.memoria.guardar_recuerdo(texto_interaccion)
                    
            # Comprobar si hay temas importantes en el mensaje+respuesta
            if hasattr(self.memoria, "temas_importantes") and hasattr(self.memoria, "extraer_palabras_clave"):
                try:
                    # Verificar si el texto contiene algún tema importante existente
                    texto_completo = f"{mensaje} {respuesta}".lower()
                    for tema in self.memoria.temas_importantes:
                        if tema.lower() in texto_completo:
                            es_importante = True
                            # Marcar recuerdo como importante si no se hizo antes
                            if hasattr(self.memoria, "marcar_ultimo_recuerdo_importante"):
                                self.memoria.marcar_ultimo_recuerdo_importante()
                            break
                            
                    # Extraer nuevos temas importantes potenciales
                    if es_importante and hasattr(self.memoria, "agregar_tema_importante"):
                        palabras = self.memoria.extraer_palabras_clave(texto_completo, max_keywords=5)
                        for palabra in palabras:
                            if len(palabra) > 3:  # Evitar palabras muy cortas
                                self.memoria.agregar_tema_importante(palabra)
                except Exception as e:
                    logger.error(f"Error al procesar temas importantes: {e}")
                    
        except Exception as e:
            logger.error(f"Error al guardar en memoria: {e}")
    
    def cerrar(self) -> None:
        """Cierra ordenadamente todos los componentes"""
        logger.info("Cerrando sistema...")
        
        # Cerrar plugins
        if self.plugins:
            try:
                self.plugins.shutdown()
            except Exception as e:
                logger.error(f"Error al cerrar plugins: {e}")
        
        # Cerrar otros componentes si es necesario
        
        logger.info("Sistema cerrado correctamente")
    
    def recargar_sistema_memoria(self) -> bool:
        """
        Recarga el sistema de memoria
        
        Returns:
            bool: True si se recargó correctamente
        """
        logger.info("Recargando sistema de memoria...")
        
        # Guardar referencia al sistema anterior
        memoria_anterior = self.memoria
        
        # Intentar inicializar nuevo sistema
        exito = self._inicializar_memoria()
        
        if not exito:
            # Restaurar sistema anterior
            self.memoria = memoria_anterior
            logger.error("No se pudo recargar el sistema de memoria")
            return False
        
        logger.info("Sistema de memoria recargado correctamente")
        return True

    def _analizar_temas_importantes(self, mensaje: str) -> None:
        """
        Analiza si un mensaje contiene temas que deben marcarse como importantes
        
        Args:
            mensaje: Mensaje a analizar
        """
        if not self.memoria or not hasattr(self.memoria, "agregar_tema_importante"):
            return
            
        # Lista de términos que indican información importante
        indicadores_importancia = [
            "recuerda", "memoriza", "importante", "no olvides", 
            "anota", "guarda", "mi información", "mi dato",
            "mi nombre es", "mi dirección", "mi teléfono", "mi email"
        ]
        
        mensaje_lower = mensaje.lower()
        
        # Verificar si contiene indicadores
        if any(ind in mensaje_lower for ind in indicadores_importancia):
            try:
                # Intentar extraer palabras clave
                if hasattr(self.memoria, "extraer_palabras_clave"):
                    palabras = self.memoria.extraer_palabras_clave(mensaje)
                    if palabras and len(palabras) > 0:
                        for palabra in palabras[:3]:  # Tomar las 3 más relevantes
                            if len(palabra) > 3:  # Evitar palabras muy cortas
                                self.memoria.agregar_tema_importante(palabra)
                                logger.debug(f"Tema importante añadido: {palabra}")
            except Exception as e:
                logger.error(f"Error al analizar temas importantes: {e}")

    def _detectar_info_importante(self, mensaje: str, respuesta: str) -> bool:
        """
        Detecta si una interacción contiene información importante que debería reforzarse
        
        Args:
            mensaje: Mensaje del usuario
            respuesta: Respuesta del sistema
            
        Returns:
            bool: True si debe marcarse como importante
        """
        # Términos que indican que la respuesta podría ser información importante
        indicadores = [
            "he guardado", "recordaré", "anotado", "registrado",
            "tu información", "tus datos", "tu preferencia"
        ]

        
        
        # Verificar primero en la respuesta 
        respuesta_lower = respuesta.lower()
        if any(ind in respuesta_lower for ind in indicadores):
            return True
        
        # Verificar en el mensaje del usuario
        mensaje_lower = mensaje.lower()
        indicadores_mensaje = [
            "recuerda", "no olvides", "importante", "guarda",
            "memoriza", "anota", "mi información", "mi dato"
        ]
        
        if any(ind in mensaje_lower for ind in indicadores_mensaje):
            return True
            
        # Verificar si la respuesta contiene datos personalizados como nombres, fechas, etc.
        patrones_info_personal = [
            r"(?:mi nombre es|me llamo) ([A-Za-z]+)",
            r"(?:tengo) (\d+)(?: años)?",
            r"(?:mi (?:teléfono|telefono|móvil|celular|número|numero)(?: es)?) ([0-9+() -]{7,})",
            r"(?:mi (?:dirección|direccion|email|correo)(?: es)?) (\S+@\S+)",
            r"(?:my name is|i am called) ([A-Za-z]+)",
            r"(?:i am) (\d+)(?: years old)?",
        ]

        for patron in patrones_info_personal:
            if re.search(patron, mensaje, re.IGNORECASE):
                return True
                
        return False

    def _formatear_resultados_memoria(self, resultados: List[Dict]) -> str:
        """
        Formatea resultados de memoria para uso en contexto
        
        Args:
            resultados: Lista de resultados de memoria
            
        Returns:
            str: Contexto formateado
        """
        if not resultados:
            return ""
            
        contexto = []
        for rec in resultados:
            # Extraer fecha
            fecha = rec.get("fecha", "Fecha desconocida")
            
            # Añadir marca si es importante
            marca = " (⭐)" if rec.get("importante", False) else ""
            
            # Añadir fuente si está disponible
            fuente = ""
            if "fuente" in rec:
                fuente = f" [{rec['fuente']}]"
            
            # Añadir indicador de relevancia para los primeros resultados
            relevancia = ""
            if rec.get("score_final", 0) > 0.7:
                relevancia = "[MUY RELEVANTE] "
            
            # Formatear recuerdo
            texto = rec["contenido"].strip()
            contexto.append(f"{relevancia}[Recuerdo del {fecha}{marca}{fuente}]\n{texto}\n")
        
        return "\n".join(contexto)
    def load_plugins(self) -> int:
        """
        Carga todos los plugins disponibles y devuelve el número de plugins cargados
        
        Returns:
            int: Número de plugins cargados con éxito
        """
        plugins = self.load_all_plugins()
        return len(plugins)

    def shutdown(self):
        """
        Cierra ordenadamente todos los plugins activos
        
        Returns:
            bool: True si se cerraron correctamente
        """
        logger.info("Cerrando plugins...")
        
        # Lista para seguir plugins con errores
        plugins_con_error = []
        
        # Intentar cerrar cada plugin
        for name, plugin in self.plugins.items():
            if hasattr(plugin, 'shutdown'):
                try:
                    plugin.shutdown()
                    logger.debug(f"Plugin {name} cerrado correctamente")
                except Exception as e:
                    logger.error(f"Error al cerrar plugin {name}: {e}")
                    plugins_con_error.append(name)
        
        if plugins_con_error:
            logger.warning(f"No se pudieron cerrar correctamente los plugins: {', '.join(plugins_con_error)}")
        else:
            logger.info("Todos los plugins cerrados correctamente")
        
        return len(plugins_con_error) == 0

    def _guardar_info_personal(self, mensaje: str) -> None:
            """
            Detecta y guarda información personal del usuario
            
            Args:
                mensaje: Mensaje del usuario
            """
            # Patrones para extraer información personal
            patrones = {
                "nombre": r"(?:mi nombre es|me llamo) ([A-Za-z]+)",
                "edad": r"(?:tengo) (\d+)(?: años)?",
                "correo": r"(?:mi (?:email|correo)(?: es)?) (\S+@\S+)",
            }
            
            info_personal = {}
            for tipo, patron in patrones.items():
                match = re.search(patron, mensaje, re.IGNORECASE)
                if match:
                    info_personal[tipo] = match.group(1)
            
            if info_personal:
                # Guardar en memoria si se encontró información personal
                configuracion = self.memoria.cargar_configuracion()
                if "info_personal" not in configuracion:
                    configuracion["info_personal"] = {}
                
                # Actualizar con la nueva información
                configuracion["info_personal"].update(info_personal)
                self.memoria.guardar_configuracion(configuracion)
                
                # Marcar explícitamente como información importante
                texto = f"Usuario - Información Personal: {', '.join([f'{k}: {v}' for k, v in info_personal.items()])}"
                self.memoria.guardar_recuerdo(texto, es_importante=True)
                
    def _obtener_info_personal(self) -> Dict[str, str]:
        """
        Recupera información personal del usuario guardada en configuración
        
        Returns:
            Dict[str, str]: Información personal (nombre, edad, etc.)
        """
        if not self.memoria:
            return {}
            
        try:
            # Obtener información de la configuración
            config = self.memoria.cargar_configuracion()
            info_personal = config.get("info_personal", {})
            
            # También buscar en recuerdos marcados como importantes
            if hasattr(self.memoria, "_cargar_archivos_recuerdos"):
                archivos = self.memoria._cargar_archivos_recuerdos()
                importantes = [a for a in archivos if "_important" in a]
                
                for archivo in importantes[:10]:  # Revisar los 10 importantes más recientes
                    try:
                        contenido = self.memoria.leer_recuerdo(archivo)
                        
                        # Buscar patrones de datos personales en el texto
                        patrones = {
                            "nombre": r"(?:mi nombre es|me llamo) ([A-Za-zÁáÉéÍíÓóÚúÑñ]+)",
                            "edad": r"(?:tengo) (\d+)(?: años)?",
                            "correo": r"(?:mi (?:email|correo)(?: es)?) (\S+@\S+)"
                        }
                        
                        for tipo, patron in patrones.items():
                            match = re.search(patron, contenido, re.IGNORECASE)
                            if match and match.group(1):
                                info_personal[tipo] = match.group(1)
                    except Exception as e:
                        logger.error(f"Error al procesar recuerdo importante: {e}")
            
            return info_personal
        except Exception as e:
            logger.error(f"Error al obtener información personal: {e}")
            return {}

                

def parse_arguments():
    """Procesa argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(description='Jarvis - Asistente Personal con IA')
    parser.add_argument('--gui', '-g', action='store_true', help='Iniciar con interfaz gráfica')
    parser.add_argument('--debug', '-d', action='store_true', help='Activar modo debug (más logs)')
    parser.add_argument('--version', '-v', action='store_true', help='Mostrar versión y salir')
    
    return parser.parse_args()

def main():
    """Función principal"""
    # Procesar argumentos
    args = parse_arguments()
    
    # Configurar nivel de log según argumentos
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("Modo debug activado")
    
    # Mostrar versión si se solicita
    if args.version:
        jarvis = Jarvis()
        print(f"{jarvis.name} v{jarvis.version}")
        return
    
    # Crear instancia principal
    jarvis = Jarvis()
    
    # Inicializar todos los componentes
    if not jarvis.inicializar():
        logger.critical("No se pudo inicializar el sistema. Terminando aplicación.")
        return
    
    try:
        # Iniciar interfaz según modo solicitado
        modo = "gui" if args.gui else "cli"
        jarvis.iniciar_interfaz(modo)
    except KeyboardInterrupt:
        logger.info("Interrupción de usuario detectada. Cerrando sistema.")
    finally:
        # Asegurar cierre ordenado
        jarvis.cerrar()

if __name__ == "__main__":
    main()

# Añade este método a la clase PluginManager en plugins/__init__.py

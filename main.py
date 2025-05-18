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
            logger.info("Inicializando sistema de memoria...")
            
            # Primero configurar modelo de embeddings
            from chatbot.memoria import configurar_embedding_model, MemoryManager
            embedding_ok = configurar_embedding_model()
            if not embedding_ok:
                logger.warning("No se pudo configurar modelo de embeddings, continuando con funcionalidad limitada")
            
            # Crear gestor de memoria
            self.memoria = MemoryManager()
            if not hasattr(self.memoria, 'index') or self.memoria.index is None:
                logger.warning("Memoria inicializada pero sin índice de vectores disponible")
            else:
                logger.info("Sistema de memoria inicializado con índice de vectores")
                
            # Registrar en componentes
            self.componentes["memoria"] = self.memoria
            return True
        except Exception as e:
            logger.error(f"Error al inicializar sistema de memoria: {e}")
            
            # Intentar crear una versión simplificada de memoria como fallback
            try:
                from chatbot.memoria_simple import MemoryManagerSimple
                self.memoria = MemoryManagerSimple()
                logger.warning("Se ha inicializado una versión simplificada de memoria como alternativa")
                self.componentes["memoria"] = self.memoria
                return True
            except Exception as e2:
                logger.critical(f"Error crítico al crear memoria alternativa: {e2}")
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
    
    def procesar_mensaje(self, mensaje: str) -> str:
        """
        Procesa un mensaje y devuelve una respuesta
        
        Args:
            mensaje: Mensaje a procesar
            
        Returns:
            str: Respuesta al mensaje
        """
        # Intentar procesar con plugins primero
        if self.plugins:
            try:
                respuesta_plugin = self.plugins.process_message(mensaje)
                if respuesta_plugin:
                    # Registrar en memoria la interacción
                    if self.memoria:
                        self.memoria.guardar_recuerdo(f"Usuario: {mensaje}\nAsistente: {respuesta_plugin}")
                    
                    # Ejecutar hook de respuesta
                    self.plugins.trigger_hook("message_response", mensaje, respuesta_plugin)
                    
                    return respuesta_plugin
            except Exception as e:
                logger.error(f"Error al procesar mensaje con plugins: {e}")
                # Continuar con el procesamiento normal
        
        # Si no hay respuesta de plugins, usar el chat_engine
        try:
            if not self.chat_engine:
                return "Lo siento, el sistema de procesamiento de lenguaje no está disponible."
            
            # Obtener contexto relevante de memoria
            contexto = ""
            if self.memoria and hasattr(self.memoria, 'obtener_contexto_relevante'):
                contexto = self.memoria.obtener_contexto_relevante(mensaje)
            
            # Generar respuesta
            if hasattr(self.chat_engine, 'chat'):
                respuesta_obj = self.chat_engine.chat(mensaje, contexto=contexto)
                respuesta = respuesta_obj.text if hasattr(respuesta_obj, 'text') else str(respuesta_obj)
            else:
                # Fallback a LLM directo
                prompt = f"{contexto}\n\nUsuario: {mensaje}\n\nAsistente:"
                respuesta = self.llm.complete(prompt).text
            
            # Limpiar respuesta si tiene formato thinking
            if "<think>" in respuesta and "</think>" in respuesta:
                respuesta = respuesta.split("</think>")[-1].strip()
            
            # Guardar en memoria
            if self.memoria:
                self.memoria.guardar_recuerdo(f"Usuario: {mensaje}\nAsistente: {respuesta}")
            
            # Ejecutar hook de respuesta
            if self.plugins:
                self.plugins.trigger_hook("message_response", mensaje, respuesta)
                
            return respuesta
            
        except Exception as e:
            logger.error(f"Error al procesar mensaje: {e}")
            return f"Lo siento, ha ocurrido un error al procesar tu mensaje: {e}"
    
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
def load_plugins(self) -> int:
    """
    Carga todos los plugins disponibles y devuelve el número de plugins cargados
    
    Returns:
        int: Número de plugins cargados con éxito
    """
    plugins = self.load_all_plugins()
    return len(plugins)
# main.py - versión con implementación minimalista
import os
import sys
import logging

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
    # Importar implementación minimalista
    from chatbot.llm_wrapper import create_chat_engine
    
    # Crear motor de chat
    logger.info("Creando motor de chat...")
    chat_engine = create_chat_engine()
    
    
    # Verificar argumentos de línea de comandos
    usar_gui = any(arg in sys.argv for arg in ["--gui", "-g"])
    
    # Importar módulo web
    try:
        from chatbot.web import MotorWebPrivado
        web_disponible = True
        web = MotorWebPrivado()
        logger.info("Módulo web privado inicializado")
    except ImportError as e:
        web_disponible = False
        web = None
        logger.warning(f"Módulo web no disponible: {e}")
    
    # Pasar componentes a la interfaz
    componentes = {
        "web": web,
        "web_disponible": web_disponible,
        "chat_engine": chat_engine
    }
    
    # Importar interfaz
    from chatbot.interfaz import ejecutar_chat
    
    if usar_gui:
        # Iniciar interfaz gráfica
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
            ejecutar_chat(None, None, componentes)
    else:
        # Iniciar interfaz de consola
        logger.info("Iniciando interfaz de consola...")
        ejecutar_chat(None, None, componentes)
        
except Exception as e:
    logger.critical(f"Error crítico: {e}")
    print(f"Error al iniciar Jarvis: {e}")
    
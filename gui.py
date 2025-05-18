"""
gui.py - Interfaz gráfica para Jarvis usando Gradio
"""
import os
import sys
import logging
import gradio as gr
from typing import Dict, List, Any
from datetime import datetime

# Configuración de logging
logger = logging.getLogger("gui")

# Importaciones seguras
try:
    from chatbot.llm_wrapper import create_chat_engine, SimpleChatEngine
    from chatbot.memoria import MemoryManager, configurar_embedding_model
    from chatbot.web import MotorWebPrivado
except ImportError as e:
    logger.error(f"Error al importar módulos: {e}")
    print(f"Error al cargar módulos necesarios: {e}")
    sys.exit(1)

# Inicializar componentes
memory_manager = MemoryManager() if 'MemoryManager' in locals() else None
chat_engine = create_chat_engine()
web_engine = None

try:
    web_engine = MotorWebPrivado()
    logger.info("Motor web inicializado correctamente")
except Exception as e:
    logger.warning(f"No se pudo inicializar el motor web: {e}")

# Historial de chat
chat_history = []

# Historial de búsquedas web
web_search_history = []

def responder(mensaje: str, history: List[List[str]]) -> str:
    """
    Genera una respuesta al mensaje del usuario
    
    Args:
        mensaje: El mensaje del usuario
        history: Historial de conversación
        
    Returns:
        str: Respuesta generada
    """
    if not mensaje.strip():
        return "Por favor, escribe un mensaje."
    
    # Registrar mensaje en logs
    logger.info(f"Mensaje recibido: {mensaje}")
    
    # Guardar mensaje en memoria
    if memory_manager:
        try:
            # Formatear el mensaje del usuario para guardarlo
            recuerdo_usuario = f"Usuario: {mensaje}"
            memory_manager.guardar_recuerdo(recuerdo_usuario)
        except Exception as e:
            logger.error(f"Error al guardar mensaje en memoria: {e}")
    
    # Verificar si es una consulta web
    if web_engine and mensaje.lower().startswith(("busca ", "buscar ", "search ")):
        consulta = mensaje.split(" ", 1)[1]
        try:
            resultados = web_engine.buscar_informacion(consulta)
            contexto = "\n\n".join([f"**{r['titulo']}**\n{r['snippet']}\n{r['url']}" for r in resultados[:3]])
            
            # Guardar en historial de búsquedas
            web_search_history.append({
                "consulta": consulta,
                "timestamp": datetime.now().isoformat(),
                "resultados": resultados[:5]  # Limitar a 5 resultados
            })
            
            # Formatear respuesta como markdown
            respuesta = f"### Resultados de búsqueda para: {consulta}\n\n"
            respuesta += contexto
            
            # Guardar respuesta en memoria
            if memory_manager:
                recuerdo_respuesta = f"Asistente: {respuesta}"
                memory_manager.guardar_recuerdo(recuerdo_respuesta)
                
            return respuesta
        except Exception as e:
            logger.error(f"Error al realizar búsqueda web: {e}")
            return f"Error al buscar información: {str(e)}"
    
    # Buscar contexto relevante en la memoria
    contexto = ""
    if memory_manager:
        try:
            contexto = memory_manager.obtener_contexto_relevante(mensaje)
        except Exception as e:
            logger.warning(f"Error al recuperar contexto de memoria: {e}")
    
    # Generar respuesta usando el motor de chat
    try:
        # Usar chat_engine para obtener respuesta, pasando contexto si está disponible
        respuesta_obj = chat_engine.chat(mensaje, contexto)
        respuesta = respuesta_obj.text if hasattr(respuesta_obj, 'text') else str(respuesta_obj)
        
        # Limpiar respuesta si tiene formato thinking
        if "<think>" in respuesta and "</think>" in respuesta:
            respuesta = respuesta.split("</think>")[-1].strip()
        
        # Guardar respuesta en memoria
        if memory_manager:
            recuerdo_respuesta = f"Asistente: {respuesta}"
            memory_manager.guardar_recuerdo(recuerdo_respuesta)
            
        return respuesta
    except Exception as e:
        logger.error(f"Error al generar respuesta: {e}")
        return f"Lo siento, ocurrió un error: {str(e)}"

def realizar_busqueda_web(consulta: str) -> str:
    """
    Realiza una búsqueda web independiente
    
    Args:
        consulta: Consulta de búsqueda
        
    Returns:
        str: Resultados formateados
    """
    if not web_engine:
        return "El motor de búsqueda web no está disponible."
    
    if not consulta.strip():
        return "Por favor, ingresa un término de búsqueda."
    
    try:
        # Realizar búsqueda
        resultados = web_engine.buscar_informacion(consulta)
        
        # Guardar en historial
        web_search_history.append({
            "consulta": consulta,
            "timestamp": datetime.now().isoformat(),
            "resultados": resultados[:5]  # Limitar a 5 resultados
        })
        
        # Formatear resultados
        if resultados:
            texto_resultados = f"## Resultados para: {consulta}\n\n"
            for i, res in enumerate(resultados, 1):
                texto_resultados += f"### {i}. {res['titulo']}\n"
                texto_resultados += f"{res['snippet']}\n"
                texto_resultados += f"🔗 {res['url']}\n\n"
                
            return texto_resultados
        else:
            return f"No se encontraron resultados para '{consulta}'."
    except Exception as e:
        logger.error(f"Error en búsqueda web independiente: {e}")
        return f"Error al realizar la búsqueda: {str(e)}"

def analizar_pagina_web(url: str) -> str:
    """
    Analiza una página web en profundidad
    
    Args:
        url: URL de la página a analizar
        
    Returns:
        str: Análisis formateado
    """
    if not web_engine:
        return "El motor de análisis web no está disponible."
    
    if not url.strip():
        return "Por favor, ingresa una URL para analizar."
    
    try:
        # Realizar análisis
        resultado = web_engine.obtener_contenido_pagina(url)
        
        if not resultado:
            return f"No se pudo analizar la página {url}."
        
        # Formatear resultado
        analisis = f"# Análisis de {resultado['titulo']}\n\n"
        analisis += f"**URL:** {resultado['url']}\n"
        
        if resultado.get('descripcion'):
            analisis += f"**Descripción:** {resultado['descripcion']}\n\n"
            
        # Datos de contacto
        contacto = resultado.get('datos_contacto', {})
        if any(contacto.get(k) for k in ['emails', 'telefonos', 'redes_sociales']):
            analisis += "## Información de contacto\n\n"
            
            if contacto.get('emails'):
                analisis += f"**Emails:** {', '.join(contacto['emails'][:3])}"
                if len(contacto['emails']) > 3:
                    analisis += f" y {len(contacto['emails']) - 3} más"
                analisis += "\n"
                
            if contacto.get('telefonos'):
                analisis += f"**Teléfonos:** {', '.join(contacto['telefonos'][:2])}"
                if len(contacto['telefonos']) > 2:
                    analisis += f" y {len(contacto['telefonos']) - 2} más"
                analisis += "\n"
                
            if contacto.get('redes_sociales'):
                analisis += "**Redes sociales:**\n"
                for red, usuario in contacto['redes_sociales'].items():
                    analisis += f"- {red}: {usuario}\n"
                    
            analisis += "\n"
        
        # Datos comerciales
        comercial = resultado.get('datos_comerciales', {})
        if any(comercial.get(k) for k in ['precios', 'sku', 'disponibilidad']):
            analisis += "## Información comercial\n\n"
            
            if comercial.get('precios'):
                analisis += f"**Precios detectados:** {', '.join(comercial['precios'][:3])}"
                if comercial.get('moneda'):
                    analisis += f" ({comercial['moneda']})"
                analisis += "\n"
                
            if comercial.get('sku'):
                analisis += f"**SKU/ID:** {comercial['sku']}\n"
                
            if comercial.get('disponibilidad'):
                analisis += f"**Disponibilidad:** {comercial['disponibilidad']}\n"
                
            analisis += "\n"
            
        # Resumen del contenido
        analisis += "## Resumen del contenido\n\n"
        
        # Limitar el contenido para evitar respuestas muy largas
        contenido_resumido = resultado['contenido'][:1500]
        if len(resultado['contenido']) > 1500:
            contenido_resumido += "...\n\n(Contenido truncado por extensión)"
            
        analisis += contenido_resumido
        
        return analisis
    except Exception as e:
        logger.error(f"Error al analizar página web: {e}")
        return f"Error durante el análisis: {str(e)}"

def obtener_estadisticas_web() -> str:
    """
    Obtiene estadísticas del motor web
    
    Returns:
        str: Estadísticas formateadas
    """
    if not web_engine:
        return "El motor web no está disponible."
    
    try:
        stats = web_engine.obtener_estadisticas_aprendizaje()
        
        estadisticas = "# Estadísticas del Motor Web\n\n"
        estadisticas += f"**Búsquedas totales:** {stats.get('busquedas_totales', 0)}\n\n"
        
        # Dominios frecuentes
        if stats.get('dominios_frecuentes'):
            estadisticas += "## Dominios más frecuentes\n\n"
            for dominio, frecuencia in list(stats['dominios_frecuentes'].items())[:5]:
                estadisticas += f"- {dominio}: {frecuencia} apariciones\n"
            estadisticas += "\n"
            
        # Palabras clave
        if stats.get('palabras_clave_frecuentes'):
            estadisticas += "## Palabras clave frecuentes\n\n"
            for palabra, frecuencia in list(stats['palabras_clave_frecuentes'].items())[:8]:
                estadisticas += f"- {palabra}: {frecuencia} veces\n"
            estadisticas += "\n"
            
        # Dominios preferidos
        if stats.get('dominios_preferidos'):
            estadisticas += f"**Dominios preferidos:** {', '.join(stats['dominios_preferidos'])}\n\n"
            
        # Dominios bloqueados
        if stats.get('dominios_bloqueados'):
            estadisticas += f"**Dominios bloqueados:** {', '.join(stats['dominios_bloqueados'])}\n\n"
            
        # Última búsqueda
        if stats.get('ultima_busqueda'):
            estadisticas += f"**Última búsqueda realizada:** '{stats['ultima_busqueda']}'\n"
            
        return estadisticas
    except Exception as e:
        logger.error(f"Error al obtener estadísticas web: {e}")
        return f"Error al obtener estadísticas: {str(e)}"

def limpiar_historial_web():
    """Limpia el historial de búsquedas web"""
    global web_search_history
    web_search_history = []
    return "Historial de búsquedas web limpiado."

def obtener_historial_busquedas() -> str:
    """
    Obtiene el historial de búsquedas realizadas en esta sesión
    
    Returns:
        str: Historial formateado
    """
    if not web_search_history:
        return "No hay búsquedas recientes en esta sesión."
    
    historial = "# Historial de búsquedas recientes\n\n"
    
    for i, busqueda in enumerate(reversed(web_search_history[-10:])):
        consulta = busqueda['consulta']
        fecha_hora = datetime.fromisoformat(busqueda['timestamp'])
        fecha_formateada = fecha_hora.strftime("%d/%m/%Y %H:%M")
        
        historial += f"## {i+1}. '{consulta}'\n"
        historial += f"*Realizada: {fecha_formateada}*\n\n"
        
        # Mostrar primeros resultados
        for j, res in enumerate(busqueda.get('resultados', [])[:3]):
            historial += f"### Resultado {j+1}: {res['titulo']}\n"
            historial += f"{res['snippet']}\n"
            historial += f"🔗 {res['url']}\n\n"
            
        historial += "---\n\n"
    
    return historial

# Crear interfaz gráfica
with gr.Blocks(title="Jarvis - Asistente Virtual", theme=gr.themes.Soft()) as interfaz:
    gr.Markdown("# JARVIS - Asistente Virtual")
    
    with gr.Tabs() as tabs:
        with gr.TabItem("Chat Principal"):
            with gr.Row():
                with gr.Column(scale=4):
                    chatbot = gr.Chatbot(
                        label="Conversación", 
                        height=450,
                        bubble_full_width=False,
                    )
                    
                    with gr.Row():
                        mensaje = gr.Textbox(
                            label="Escribe tu mensaje",
                            placeholder="¿En qué puedo ayudarte hoy?",
                            lines=2,
                            max_lines=5,
                            show_label=False,
                        )
                        
                    with gr.Row():
                        enviar = gr.Button("Enviar", variant="primary")
                        limpiar = gr.Button("Limpiar conversación")
                
                with gr.Column(scale=1):
                    gr.Markdown("### Opciones")
                    
                    with gr.Accordion("Información del sistema", open=False):
                        memoria_info = gr.Markdown(f"""
                        - **Motor LLM**: Ollama ({chat_engine.llm.model})
                        - **Memoria**: {'Activa' if memory_manager else 'No disponible'}
                        - **Web**: {'Disponible' if web_engine else 'No disponible'}
                        - **Documentos cargados**: {len(chat_engine.documents)}
                        """)
                    
                    with gr.Accordion("Ayuda", open=False):
                        gr.Markdown("""
                        ### Comandos especiales
                        
                        - `buscar [término]`: Busca información en la web
                        - `analizar [url]`: Analiza una página web en detalle
                        - `salir`: Cierra la aplicación
                        
                        ### Tips
                        
                        - Puedes hacer preguntas específicas o conversar naturalmente
                        - Jarvis recordará el contexto de la conversación
                        - Utiliza la pestaña "Herramientas Web" para búsquedas avanzadas
                        """)
        
        # Nueva pestaña para herramientas web
        with gr.TabItem("Herramientas Web"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("## Búsqueda Web")
                    with gr.Row():
                        busqueda_input = gr.Textbox(
                            label="Término de búsqueda",
                            placeholder="Escribe lo que quieres buscar...",
                            lines=1
                        )
                        buscar_btn = gr.Button("🔍 Buscar", variant="primary")
                    
                    gr.Markdown("## Análisis de Página Web")
                    with gr.Row():
                        url_input = gr.Textbox(
                            label="URL para analizar",
                            placeholder="https://ejemplo.com",
                            lines=1
                        )
                        analizar_btn = gr.Button("🔬 Analizar", variant="primary")
                    
                    with gr.Row():
                        stats_btn = gr.Button("📊 Ver Estadísticas")
                        historial_btn = gr.Button("📜 Historial de Búsquedas")
                        limpiar_web_btn = gr.Button("🧹 Limpiar Historial")
            
            with gr.Row():
                resultados_web = gr.Markdown("### Resultados aparecerán aquí\n\nUtiliza las herramientas de la izquierda para realizar búsquedas o análisis.")
    
    # Callbacks
    def user_input(user_message, history):
        return "", history + [[user_message, None]]
    
    def bot_response(history):
        if history:
            user_message = history[-1][0]
            bot_message = responder(user_message, history[:-1])
            history[-1][1] = bot_message
        return history
    
    def clear_conversation():
        return []
    
    # Conectar eventos del chat principal
    mensaje.submit(user_input, [mensaje, chatbot], [mensaje, chatbot], queue=False).then(
        bot_response, chatbot, chatbot
    )
    
    enviar.click(user_input, [mensaje, chatbot], [mensaje, chatbot], queue=False).then(
        bot_response, chatbot, chatbot
    )
    
    limpiar.click(clear_conversation, None, chatbot)
    
    # Conectar eventos de herramientas web
    buscar_btn.click(realizar_busqueda_web, busqueda_input, resultados_web)
    analizar_btn.click(analizar_pagina_web, url_input, resultados_web)
    stats_btn.click(obtener_estadisticas_web, None, resultados_web)
    historial_btn.click(obtener_historial_busquedas, None, resultados_web)
    limpiar_web_btn.click(limpiar_historial_web, None, resultados_web)
    
    # Inicializar con mensaje de bienvenida
    interfaz.load(lambda: [[None, "¡Hola! Soy Jarvis, tu asistente virtual. ¿En qué puedo ayudarte hoy?"]])

# Mensaje al iniciar la interfaz
print("✅ Interfaz gráfica inicializada. Abriendo en el navegador...")

if __name__ == "__main__":
    # Si se ejecuta directamente, lanzar la interfaz
    interfaz.launch(share=False, inbrowser=True)

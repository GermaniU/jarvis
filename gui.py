import os
import gradio as gr
from chatbot.indexador import construir_indice
from chatbot.asistente import obtener_llm
from llama_index import StorageContext, load_index_from_storage
from chatbot.memoria import MemoryManager
import re

# Importar el módulo web privado
try:
    from chatbot.web import MotorWebPrivado
    web_disponible = True
    web = MotorWebPrivado()
    print("🌐 Módulo web privado inicializado")
except ImportError:
    web_disponible = False
    web = None
    print("🌐 Módulo web no disponible")

# Inicialización de componentes
memoria = MemoryManager()

# Cargar o construir el índice
if os.path.exists("embeddings") and os.listdir("embeddings"):
    print("🧠 Cargando índice persistente...")
    storage_context = StorageContext.from_defaults(persist_dir="embeddings")
    indice = load_index_from_storage(storage_context)
else:
    print("🧠 Construyendo índice desde /data y /memory...")
    indice = construir_indice()

# Obtener el modelo de lenguaje
llm = obtener_llm("deepseek-r1:14b")

# Configuramos el chat engine


chat_engine = indice.as_chat_engine(
    chat_mode="context",
    llm=llm,
    verbose=True
)

# Función para procesar comandos
def procesar_comando(comando):
    if comando.lower() == "/limpiar":
        return "Historial de chat limpiado."
    elif comando.lower() == "/ayuda":
        return """
## Comandos disponibles

- **/buscar** [consulta]: Realiza una búsqueda web
- **/analizar** [URL]: Analiza una página web
- **/analizar-profundo** [URL]: Análisis profundo
- **/memoria**: Muestra los recuerdos
- **/limpiar**: Limpia el historial
- **/ayuda**: Muestra esta ayuda
"""
    elif comando.lower().startswith("/buscar "):
        query = comando[8:].strip()
        if web_disponible and web:
            try:
                resultados = web.realizar_busqueda(query)
                if resultados:
                    salida = f"## Resultados para '{query}':\n\n"
                    for i, res in enumerate(resultados[:5], 1):
                        salida += f"{i}. [{res['titulo']}]({res['url']})\n"
                        if 'snippet' in res:
                            salida += f"   {res['snippet']}\n\n"
                    return salida
                else:
                    return "No se encontraron resultados."
            except Exception as e:
                return f"Error al buscar: {str(e)}"
        else:
            return "Módulo web no disponible."
    elif comando.lower().startswith("/analizar "):
        url = comando[10:].strip()
        if web_disponible and web:
            try:
                resultado = web.obtener_contenido_pagina(url)
                if resultado:
                    return f"## Análisis de {url}\n\n### {resultado['titulo']}\n\n{resultado['contenido'][:500]}...\n\n"
                else:
                    return "No se pudo obtener contenido."
            except Exception as e:
                return f"Error al analizar: {str(e)}"
        else:
            return "Módulo web no disponible."
    elif comando.lower() == "/memoria":
        try:
            recuerdos = memoria._cargar_archivos_recuerdos()
            if recuerdos:
                texto = "## Recuerdos almacenados\n\n"
                for i, rec in enumerate(recuerdos[:10], 1):
                    texto += f"{i}. {rec}\n"
                if len(recuerdos) > 10:
                    texto += f"\n... y {len(recuerdos) - 10} más"
                return texto
            else:
                return "No hay recuerdos almacenados."
        except Exception as e:
            return f"Error en memoria: {str(e)}"
    return f"Comando '{comando}' no reconocido. Usa /ayuda."

# Versión stream (respuestas en tiempo real)
def responder_stream(mensaje, historia):
    if not mensaje:
        yield historia, ""

    if mensaje.startswith("/"):
        respuesta = procesar_comando(mensaje)
        historia.append((mensaje, respuesta))
        yield historia, ""
        return

    try:
        historia.append((mensaje, "..."))  # ✅ placeholder para evitar None
        yield historia, ""

        response = chat_engine.chat(mensaje)
        memoria.guardar_recuerdo(f"Usuario: {mensaje}\nJarvis: {response.response}")
        import re
        respuesta_plana = re.sub(r"<.*?>", "", response.response).strip()
        historia[-1] = (mensaje, respuesta_plana)


        yield historia, ""
    except Exception as e:
        historia[-1] = (mensaje, f"Error: {str(e)}")
        yield historia, ""


# Interfaz Gradio
with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue"), css="footer {visibility: hidden}") as interfaz:
    gr.Markdown("# 🤖 Jarvis - Asistente Personal con IA")

    with gr.Row():
        with gr.Column(scale=4):
            chatbot = gr.Chatbot(
                [],
                elem_id="chatbot",
                bubble_full_width=False,
    avatar_images=(None, None),  # ✅ o ("static/user.png", "static/bot.png")
                height=500,
                show_label=False
            )
            with gr.Row():
                txt = gr.Textbox(
                    show_label=False,
                    placeholder="Escribe tu mensaje o comando aquí...",
                    container=False
                )
                send_btn = gr.Button("Enviar", variant="primary")

            gr.Examples(
                examples=[
                    "¿Qué puedes hacer?",
                    "/ayuda",
                    "/buscar últimas noticias sobre inteligencia artificial",
                    "/analizar https://python.org",
                    "/memoria"
                ],
                inputs=txt
            )

        with gr.Column(scale=1):
            with gr.Tabs():
                with gr.TabItem("Comandos Rápidos"):
                    gr.Markdown("""
                    ### Comandos Rápidos
                    - [/buscar](/buscar): Búsqueda web
                    - [/analizar](/analizar): Análisis web
                    - [/memoria](/memoria): Ver recuerdos
                    - [/limpiar](/limpiar): Limpiar chat
                    - [/ayuda](/ayuda): Mostrar ayuda
                    """)
                with gr.TabItem("Estado"):
                    web_status = gr.Markdown(f"🌐 Web: {'Activo' if web_disponible else 'Inactivo'}")
                    memoria_count = gr.Markdown(f"📝 Recuerdos: {len(memoria._cargar_archivos_recuerdos())}")
                    refresh_btn = gr.Button("Actualizar Estado")

    txt.submit(fn=responder_stream, inputs=[txt, chatbot], outputs=[chatbot, txt])
    send_btn.click(fn=responder_stream, inputs=[txt, chatbot], outputs=[chatbot, txt])

    def actualizar_estado():
        return (
            f"🌐 Web: {'Activo' if web_disponible else 'Inactivo'}",
            f"📝 Recuerdos: {len(memoria._cargar_archivos_recuerdos())}"
        )

    refresh_btn.click(actualizar_estado, [], [web_status, memoria_count])

    def limpiar_chat():
        return [], ""

    with gr.Row():
        clear_btn = gr.Button("Limpiar Chat", variant="secondary")
    clear_btn.click(limpiar_chat, [], [chatbot, txt])

if __name__ == "__main__":
    interfaz.launch(share=False, inbrowser=True)

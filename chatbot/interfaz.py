"""
interfaz.py - Interfaz de línea de comandos para Jarvis
"""
import os
import json
import re
import logging
import time
from datetime import datetime
from urllib.parse import urlparse
from typing import Dict, List, Optional, Any, Union, Tuple, Callable
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.progress import Progress
from rich.syntax import Syntax
# from llama_index.core.chat_engine import ContextChatEngine
# from llama_index.core.memory import ChatMemoryBuffer
# from llama_index.llms.ollama import ContextChatEngine
from llama_index.chat_engine.context import ContextChatEngine
from llama_index.memory.chat_memory_buffer import ChatMemoryBuffer

from .memoria import MemoryManager
from .asistente import obtener_llm

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("jarvis_cli.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("interfaz")

# Inicializar componentes
console = Console()
memoria = MemoryManager()

# Intentar importar módulo de voz si está disponible
try:
    from .voz import SistemaVoz
    voz_disponible = True
    logger.info("Módulo de voz disponible e importado")
except ImportError:
    logger.info("Módulo de voz no disponible, ejecutando sin sonido")
    voz_disponible = False

# Intentar importar módulo web si está disponible
try:
    from .web import MotorWebPrivado
    web_disponible = True
    web = MotorWebPrivado()
    logger.info("Módulo web disponible e inicializado")
except ImportError:
    logger.info("Módulo web no disponible")
    web_disponible = False
    web = None

# Clase dummy para voz cuando no está disponible
class VozDummy:
    def hablar(self, texto, async_mode=True):
        return False
    def cambiar_velocidad(self, nueva_velocidad):
        return False
    def cambiar_volumen(self, nuevo_volumen):
        return False
    def listar_voces(self):
        return []
    def cambiar_voz(self, indice):
        return False
    def detener(self):
        pass

# Inicializar sistema de voz
if voz_disponible:
    try:
        # Cargar configuración
        config = memoria.cargar_configuracion()
        velocidad_voz = config.get("velocidad_voz", 145)
        volumen_voz = config.get("volumen_voz", 0.85)
        indice_voz = config.get("indice_voz", None)
        
        # Inicializar con configuración personalizada
        voz = SistemaVoz(
            velocidad=velocidad_voz,
            volumen=volumen_voz,
            voz_index=indice_voz
        )
        logger.info(f"Sistema de voz inicializado: velocidad={velocidad_voz}, volumen={volumen_voz}")
    except Exception as e:
        logger.error(f"Error al inicializar sistema de voz: {e}")
        voz_disponible = False
        voz = VozDummy()
else:
    # Crear un objeto dummy para evitar errores
    voz = VozDummy()

def preparar_texto_para_voz(texto: str) -> str:
    """
    Prepara el texto para mejor pronunciación
    
    Args:
        texto: Texto a preparar
        
    Returns:
        Texto procesado para mejor pronunciación
    """
    # Mejora la pronunciación de números
    texto = re.sub(r'(\d+)\.(\d+)', r'\1 punto \2', texto)  # 3.14 -> "3 punto 14"
    
    # Mejora la pronunciación de siglas
    texto = re.sub(r'\b([A-Z]{2,})\b', lambda m: ' '.join(m.group(1)), texto)  # CPU -> "C P U"
    
    # Mejora la pronunciación de URLs
    texto = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
                  "enlace web", texto)
    
    # Mejora la pronunciación de símbolos comunes
    sustituciones = {
        '%': ' por ciento',
        '€': ' euros',
        '$': ' dólares',
        '=': ' igual a ',
        '+': ' más ',
        '-': ' menos ',
        '*': ' por ',
        '/': ' dividido por ',
        '#': ' numeral ',
        '@': ' arroba ',
        '`': '', # Eliminar backticks
        '```': '', # Eliminar bloques de código
    }
    
    for simbolo, reemplazo in sustituciones.items():
        texto = texto.replace(simbolo, reemplazo)
        
    return texto

def limpiar_url(url_raw: str) -> str:
    """
    Limpia y normaliza una URL
    
    Args:
        url_raw: URL sin procesar
        
    Returns:
        URL normalizada
    """
    url = url_raw.strip()
    url = re.sub(r'\s+', '', url)  # eliminar espacios internos
    url = re.sub(r'^https?://o?https?://', 'https://', url)  # limpiar dobles
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return url

def es_url_valida(url: str) -> bool:
    """
    Verifica si una URL es válida
    
    Args:
        url: URL a verificar
        
    Returns:
        True si la URL es válida, False en caso contrario
    """
    parsed = urlparse(url)
    return all([parsed.scheme, parsed.netloc])

def mostrar_mensaje_bienvenida() -> None:
    """Muestra mensaje de bienvenida al iniciar el sistema"""
    mensaje = "Bienvenido a Jarvis, tu asistente personal con memoria e inteligencia artificial. ¿En qué puedo ayudarte hoy?"
    console.print(Panel.fit(
        "[bold green]JARVIS - Asistente Personal con IA[/bold green]\n\n"
        "[yellow]Capacidades:[/yellow]\n"
        "- Recuerda información de conversaciones pasadas\n"
        "- Aprende tus preferencias y datos personales\n"
        "- Responde basándose en datos guardados\n"
        "- Búsqueda web con privacidad\n"
        "- Análisis de contenido web\n"
        "- Voz natural (cuando disponible)\n\n"
        "[blue]Comandos básicos:[/blue]\n"
        "- /ayuda - Muestra comandos disponibles\n"
        "- /limpiar - Borra la conversación actual\n"
        "- /buscar [consulta] - Busca en la web\n"
        "- /analizar [URL] - Analiza una página web\n"
        "- /config - Muestra la configuración\n"
        "- salir - Termina la conversación",
        title="👋 Bienvenido",
        border_style="green"
    ))
    
    # Si la voz está disponible, hablar el mensaje de bienvenida
    config = memoria.cargar_configuracion()
    usar_voz = config.get("usar_voz", True)
    if usar_voz and voz_disponible:
        texto_voz = preparar_texto_para_voz(mensaje)
        voz.hablar(texto_voz)

def mostrar_despedida() -> None:
    """Muestra mensaje de despedida al salir del sistema"""
    mensaje = "Gracias por usar Jarvis. Todas tus conversaciones han sido guardadas para futuras interacciones."
    console.print(Panel.fit(
        "[bold blue]Gracias por usar Jarvis[/bold blue]\n"
        "Todas tus conversaciones han sido guardadas para futuras interacciones.\n"
        "¡Hasta pronto!",
        title="👋 Hasta pronto",
        border_style="blue"
    ))
    
    # Si la voz está disponible, hablar el mensaje de despedida
    config = memoria.cargar_configuracion()
    usar_voz = config.get("usar_voz", True)
    if usar_voz and voz_disponible:
        texto_voz = preparar_texto_para_voz(mensaje)
        voz.hablar(texto_voz)

def mostrar_ayuda(categoria: Optional[str] = None) -> None:
    """
    Muestra ayuda contextual por categorías
    
    Args:
        categoria: Categoría específica de ayuda a mostrar
    """
    if not categoria or categoria == "general":
        console.print(Panel.fit(
            "[bold blue]COMANDOS DISPONIBLES:[/bold blue]\n\n"
            "🎛️ [bold]Comandos Generales:[/bold]\n"
            "- [yellow]/menu[/yellow] - Muestra el menú principal\n"
            "- [yellow]/ayuda[/yellow] - Muestra esta ayuda general\n"
            "- [yellow]/ayuda <categoría>[/yellow] - Ayuda específica (voz, web, memoria, config)\n"
            "- [yellow]/limpiar[/yellow] - Limpia la conversación actual\n"
            "- [yellow]/stats[/yellow] - Muestra estadísticas del sistema\n"
            "- [yellow]salir[/yellow] - Termina la sesión\n\n"
            "Para más detalles, usa: [cyan]/ayuda voz[/cyan], [cyan]/ayuda web[/cyan], [cyan]/ayuda memoria[/cyan] o [cyan]/ayuda config[/cyan]",
            title="❓ Ayuda General",
            border_style="blue"
        ))
    elif categoria == "voz":
        console.print(Panel.fit(
            "[bold blue]Comandos de voz:[/bold blue]\n"
            "- [yellow]/voz on[/yellow] - Activa la voz\n"
            "- [yellow]/voz off[/yellow] - Desactiva la voz\n"
            "- [yellow]/voz velocidad 150[/yellow] - Cambia la velocidad (100-200)\n"
            "- [yellow]/voz volumen 0.8[/yellow] - Cambia el volumen (0.0-1.0)\n"
            "- [yellow]/voces[/yellow] - Lista voces disponibles\n"
            "- [yellow]/voz cambiar 2[/yellow] - Cambia a la voz con índice 2",
            title="🔊 Ayuda de Voz",
            border_style="blue"
        ))
    elif categoria == "web":
        console.print(Panel.fit(
            "[bold blue]Comandos web:[/bold blue]\n"
            "- [yellow]/buscar <consulta>[/yellow] - Busca información en la web\n"
            "- [yellow]/buscar+ <consulta>[/yellow] - Busca y analiza automáticamente\n"
            "- [yellow]/buscar-opciones -d dominio -f reciente -n 10 <consulta>[/yellow] - Búsqueda avanzada\n"
            "- [yellow]/analizar <url>[/yellow] - Analiza en detalle una página web\n"
            "- [yellow]/analizar-profundo <url>[/yellow] - Realiza análisis estructural completo\n"
            "- [yellow]/web stats[/yellow] - Muestra estadísticas de búsqueda web\n"
            "- [yellow]/web resultados <num>[/yellow] - Cambia número de resultados (1-20)\n"
            "- [yellow]/web preferir <dominio>[/yellow] - Añade un dominio preferido\n"
            "- [yellow]/web bloquear <dominio>[/yellow] - Bloquea un dominio en resultados\n"
            "- [yellow]/exportar resultados <num>[/yellow] - Exporta búsquedas recientes",
            title="🌐 Ayuda Web",
            border_style="blue"
        ))
    elif categoria == "memoria":
        console.print(Panel.fit(
            "[bold blue]Comandos de memoria:[/bold blue]\n"
            "- [yellow]/guardar nombre=valor[/yellow] - Guarda una preferencia\n"
            "- [yellow]/memoria[/yellow] - Muestra últimos recuerdos\n"
            "- [yellow]/buscar-memoria <texto>[/yellow] - Busca en los recuerdos guardados\n"
            "- [yellow]/olvidar <id>[/yellow] - Elimina un recuerdo específico\n"
            "- [yellow]/stats memoria[/yellow] - Muestra estadísticas de memoria",
            title="🧠 Ayuda de Memoria",
            border_style="blue"
        ))
    elif categoria == "config":
        console.print(Panel.fit(
            "[bold blue]Comandos de configuración:[/bold blue]\n"
            "- [yellow]/config[/yellow] - Muestra panel de configuración\n"
            "- [yellow]/config <#>[/yellow] - Modifica una configuración específica\n"
            "- [yellow]/config reset[/yellow] - Restablece valores predeterminados\n"
            "- [yellow]/config export[/yellow] - Exporta configuración actual\n"
            "- [yellow]/config import[/yellow] - Importa configuración",
            title="⚙️ Ayuda de Configuración",
            border_style="blue"
        ))
    else:
        console.print(f"[yellow]Categoría de ayuda '{categoria}' no reconocida. Prueba con: general, voz, web, memoria, config[/yellow]")

def mostrar_opciones_configuracion() -> None:
    """Muestra las opciones de configuración actuales"""
    config = memoria.cargar_configuracion()
    
    # Obtener nombre de voz actual si está disponible
    nombre_voz = "No disponible"
    if voz_disponible:
        try:
            voces = voz.listar_voces(silent=True)
            indice_voz = config.get("indice_voz", 0)
            if voces and 0 <= indice_voz < len(voces):
                nombre_voz = voces[indice_voz]
            else:
                nombre_voz = "Predeterminada"
        except:
            nombre_voz = "Error al obtener"
    
    console.print(Panel.fit(
        "[bold yellow]CONFIGURACIÓN DE JARVIS[/bold yellow]\n\n"
        f"1. [bold]Voz[/bold]: {'Activada' if config.get('usar_voz', True) else 'Desactivada'}\n"
        f"2. [bold]Velocidad de voz[/bold]: {config.get('velocidad_voz', 145)}\n"
        f"3. [bold]Volumen[/bold]: {config.get('volumen_voz', 0.85)}\n"
        f"4. [bold]Voz actual[/bold]: {nombre_voz}\n"
        f"5. [bold]Memoria[/bold]: {config.get('max_recuerdos', 500)} recuerdos máximos\n"
        f"6. [bold]Web[/bold]: Resultados por búsqueda: {config.get('max_resultados_web', 5)}\n"
        f"7. [bold]TTL de caché[/bold]: {config.get('cache_ttl', 86400) // 3600} horas\n"
        f"8. [bold]Modelo LLM[/bold]: {config.get('modelo_llm', 'deepseek-r1:14b')}\n\n"
        "[dim]Escribe '/config #' para modificar una opción (ejemplo: /config 1)[/dim]",
        title="⚙️ Configuración",
        border_style="yellow"
    ))

def mostrar_estadisticas() -> None:
    """Muestra estadísticas generales del sistema"""
    try:
        # Estadísticas de memoria
        stats_memoria = memoria.obtener_estadisticas_memoria()
        
        # Estadísticas web si está disponible
        stats_web = {"busquedas_totales": 0}
        if web_disponible and web:
            stats_web = web.obtener_estadisticas_aprendizaje()
        
        # Construir tabla de estadísticas
        table = Table(title="📊 Estadísticas del Sistema")
        table.add_column("Categoría", style="cyan")
        table.add_column("Métrica", style="yellow")
        table.add_column("Valor", style="green")
        
        # Memoria
        table.add_row("Memoria", "Recuerdos totales", str(stats_memoria["total_recuerdos"]))
        table.add_row("Memoria", "Tamaño total", f"{stats_memoria['tamano_total_kb']:.2f} KB")
        table.add_row("Memoria", "Última interacción", stats_memoria["ultima_interaccion"])
        
        # Distribución temporal
        dist = stats_memoria["distribucion_temporal"]
        table.add_row("Memoria", "Recuerdos hoy", str(dist["hoy"]))
        table.add_row("Memoria", "Recuerdos última semana", str(dist["semana"]))
        table.add_row("Memoria", "Recuerdos último mes", str(dist["mes"]))
        
        # Web
        table.add_row("Web", "Búsquedas totales", str(stats_web["busquedas_totales"]))
        table.add_row("Web", "Dominios preferidos", str(len(stats_web.get("dominios_preferidos", []))))
        table.add_row("Web", "Dominios bloqueados", str(len(stats_web.get("dominios_bloqueados", []))))
        
        # Última búsqueda
        if stats_web.get("ultima_busqueda"):
            table.add_row("Web", "Última búsqueda", stats_web["ultima_busqueda"])
        
        # Mostrar tabla
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error al obtener estadísticas: {e}[/red]")

def mostrar_analisis_detallado(resultado: Dict[str, Any]) -> None:
    """
    Muestra un análisis detallado de una página web
    
    Args:
        resultado: Diccionario con los datos del análisis
    """
    console.print(Panel(f"""📝 [bold]ANÁLISIS DETALLADO DE PÁGINA WEB:[/bold]
    
    [bold blue]Título:[/bold blue] {resultado['titulo']}
    [bold green]URL:[/bold green] {resultado['url']}
    
    [bold yellow]RESUMEN GENERAL[/bold yellow]
    • {len(resultado['contenido'])} caracteres de contenido principal
    • {len(resultado.get('tablas', []))} tablas encontradas
    • {len(resultado.get('imagenes', []))} imágenes extraídas
    • {len(resultado.get('datos_contacto', {}).get('emails', []))} emails encontrados
    
    [bold magenta]DATOS COMERCIALES DETECTADOS[/bold magenta]
    • Precios: {', '.join(resultado.get('datos_comerciales', {}).get('precios', ['No detectados']))}
    • SKU: {resultado.get('datos_comerciales', {}).get('sku', 'No detectado')}
    • Disponibilidad: {resultado.get('datos_comerciales', {}).get('disponibilidad', 'No especificada')}
    
    [bold cyan]DATOS DE CONTACTO[/bold cyan]
    • Emails: {', '.join(resultado.get('datos_contacto', {}).get('emails', ['No detectados']))[:100]}
    • Teléfonos: {', '.join(resultado.get('datos_contacto', {}).get('telefonos', ['No detectados']))[:100]}
    • Redes sociales: {', '.join([f"{red}: {usuario}" for red, usuario in resultado.get('datos_contacto', {}).get('redes_sociales', {}).items()])[:100] or 'No detectadas'}
    """, title="🔍 Análisis Web Exhaustivo"))

def explorar_resultado_web(resultado: Dict[str, Any]) -> None:
    """
    Muestra un menú interactivo para explorar los diferentes datos extraídos
    
    Args:
        resultado: Diccionario con los datos extraídos de la página web
    """
    opciones = [
        "1. Ver contenido principal",
        "2. Explorar tablas",
        "3. Ver imágenes detectadas",
        "4. Ver datos de contacto",
        "5. Examinar datos comerciales",
        "6. Salir"
    ]
    
    while True:
        console.print("\n[bold cyan]EXPLORADOR DE DATOS WEB[/bold cyan]")
        for opcion in opciones:
            console.print(opcion)
            
        try:
            seleccion = input("\nSelecciona una opción (1-6): ")
            
            if seleccion == "1":
                console.print(Panel(Markdown(resultado['contenido'][:5000] + "..." if len(resultado['contenido']) > 5000 else resultado['contenido']), 
                             title=f"Contenido de {resultado['titulo']}"))
            
            elif seleccion == "2":
                if resultado.get('tablas'):
                    for i, tabla in enumerate(resultado['tablas']):
                        console.print(f"\n[bold]Tabla {i+1}[/bold] ({tabla.get('filas', '?')}x{tabla.get('columnas', '?')})")
                        if tabla.get('encabezados'):
                            console.print(f"Encabezados: {', '.join(tabla['encabezados'])}")
                        
                        # Mostrar primeras 3 filas
                        console.print("Primeras filas:")
                        datos = tabla.get('datos_brutos', [])
                        for j, fila in enumerate(datos[:3]):
                            console.print(f"  {j+1}: {fila}")
                        
                        # Mostrar datos estructurados
                        datos_estructurados = tabla.get('datos_estructurados', [])
                        if datos_estructurados:
                            console.print("\nDatos estructurados (ejemplo):")
                            console.print(json.dumps(datos_estructurados[0], indent=2, ensure_ascii=False))
                            
                        console.print("---")
                else:
                    console.print("[yellow]No se detectaron tablas en la página[/yellow]")
            
            elif seleccion == "3":
                if resultado.get('imagenes'):
                    console.print(f"\n[bold]Imágenes detectadas: {len(resultado['imagenes'])}[/bold]")
                    for i, img in enumerate(resultado['imagenes'][:10]):  # Mostrar máximo 10
                        console.print(f"\n[bold]{i+1}. {img.get('alt', 'Sin descripción')}[/bold]")
                        console.print(f"URL: {img.get('src', 'No disponible')}")
                        if img.get('contexto'):
                            console.print(f"Contexto: {img['contexto']}")
                        console.print("---")
                    
                    if len(resultado['imagenes']) > 10:
                        console.print(f"... y {len(resultado['imagenes']) - 10} imágenes más")
                else:
                    console.print("[yellow]No se detectaron imágenes en la página[/yellow]")
                    
            elif seleccion == "4":
                contacto = resultado.get('datos_contacto', {})
                console.print("\n[bold]DATOS DE CONTACTO[/bold]")
                
                if contacto.get('emails'):
                    console.print(f"\n[bold]Emails ({len(contacto['emails'])}):[/bold] {', '.join(contacto['emails'])}")
                    
                if contacto.get('telefonos'):
                    console.print(f"\n[bold]Teléfonos ({len(contacto['telefonos'])}):[/bold] {', '.join(contacto['telefonos'])}")
                    
                if contacto.get('direcciones'):
                    console.print(f"\n[bold]Direcciones ({len(contacto['direcciones'])}):[/bold]")
                    for i, dir in enumerate(contacto['direcciones']):
                        console.print(f"  {i+1}: {dir}")
                        
                if contacto.get('redes_sociales'):
                    console.print("\n[bold]Redes sociales:[/bold]")
                    for red, usuario in contacto['redes_sociales'].items():
                        console.print(f"  {red}: {usuario}")
                        
                if not any([contacto.get('emails'), contacto.get('telefonos'), 
                           contacto.get('direcciones'), contacto.get('redes_sociales')]):
                    console.print("[yellow]No se detectaron datos de contacto[/yellow]")
            
            elif seleccion == "5":
                datos_com = resultado.get('datos_comerciales', {})
                console.print("\n[bold]DATOS COMERCIALES[/bold]")
                
                if datos_com.get('precios'):
                    console.print(f"\n[bold]Precios detectados:[/bold] {', '.join(datos_com['precios'])}")
                    if datos_com.get('moneda'):
                        console.print(f"Moneda probable: {datos_com['moneda']}")
                        
                if datos_com.get('sku'):
                    console.print(f"\n[bold]SKU/ID de producto:[/bold] {datos_com['sku']}")
                    
                if datos_com.get('disponibilidad'):
                    console.print(f"\n[bold]Disponibilidad:[/bold] {datos_com['disponibilidad']}")
                    
                if datos_com.get('rating'):
                    console.print(f"\n[bold]Valoración:[/bold] {datos_com['rating']}/5")
                    
                if not any(datos_com.get(k) for k in ['precios', 'sku', 'disponibilidad', 'rating']):
                    console.print("[yellow]No se detectaron datos comerciales en la página[/yellow]")
            
            elif seleccion == "6":
                break
                
            else:
                console.print("[yellow]Opción no válida, intenta de nuevo[/yellow]")
                
        except Exception as e:
            console.print(f"[red]Error al procesar opción: {e}[/red]")

def ejecutar_chat(indice, llm, componentes=None) -> None:
    """
    Ejecuta una interfaz de chat en la terminal usando el índice y el modelo especificados
    
    Args:
        indice: Índice vectorial para recuperación de contexto
        llm: Modelo de lenguaje a utilizar
        componentes: Diccionario con componentes adicionales
    """
    # Extraer componentes
    web_util = componentes.get("web") if componentes else web
    web_disp = componentes.get("web_disponible", web_disponible) if componentes else web_disponible
    
    # Memoria de chat y retriever
    memory = ChatMemoryBuffer.from_defaults(token_limit=1500)
    retriever = indice.as_retriever()
    
    # Cargar configuración
    config = memoria.cargar_configuracion()
    usar_voz = config.get("usar_voz", True)  # Por defecto activada
    
    # Instrucciones para el modelo
    instrucciones = """
    Eres Jarvis, un asistente personal amigable que SIEMPRE responde en español de forma clara.
    
    REGLAS CRÍTICAS:
    1. NUNCA digas "no puedo cargar recuerdos anteriores" o frases similares.
    2. SIEMPRE usa la información de los recuerdos proporcionados como base para tu respuesta.
    3. Cuando te pregunten qué recuerdas o qué sabes, resume el contenido de los recuerdos.
    4. Si te preguntan algo específico que aparece en los recuerdos, responde con esa información.
    5. Si te preguntan sobre algo que no está en los recuerdos, di "No tengo esa información, pero puedo buscarla si deseas".
    6. Sé natural y conversacional, no demasiado formal.
    7. Cuando hables de sitios web o información de internet, ofrece análisis y opiniones útiles.
    """

    # Inicializar motor de chat
    chat_engine = ContextChatEngine.from_defaults(
        retriever=retriever,
        llm=llm,
        memory=memory,
        verbose=True,
        system_prompt=instrucciones
    )
    
    # Mostrar mensaje de bienvenida y comenzar interacción
    mostrar_mensaje_bienvenida()
    console.print("[blue]Escribe 'salir' para terminar[/blue]")
    
    # Bucle principal de chat
    while True:
        entrada = input("\nTú: ")
        
        # Procesar comandos especiales
        if entrada.lower() == "salir":
            mostrar_despedida()
            break
            
        elif entrada.lower() == "/ayuda":
            mostrar_ayuda("general")
            continue
            
        elif entrada.lower().startswith("/ayuda "):
            categoria = entrada.split(" ")[1].strip()
            mostrar_ayuda(categoria)
            continue
            
        elif entrada.lower() == "/limpiar":
            memory.reset()
            mensaje = "Conversación actual limpiada"
            console.print(f"[green]{mensaje}[/green]")
            if usar_voz and voz_disponible:
                voz.hablar(mensaje)
            continue
            
        # Comandos de voz
        elif entrada.lower() == "/voz on":
            usar_voz = True
            config["usar_voz"] = True
            memoria.guardar_configuracion(config)
            console.print("[green]Voz activada[/green]")
            if voz_disponible:
                voz.hablar("Voz activada")
            continue
            
        elif entrada.lower() == "/voz off":
            usar_voz = False
            config["usar_voz"] = False
            memoria.guardar_configuracion(config)
            console.print("[yellow]Voz desactivada[/yellow]")
            continue
            
        elif entrada.lower().startswith("/voz velocidad "):
            try:
                nueva_velocidad = int(entrada.split(" ")[-1])
                if 100 <= nueva_velocidad <= 200:
                    voz.cambiar_velocidad(nueva_velocidad)
                    config["velocidad_voz"] = nueva_velocidad
                    memoria.guardar_configuracion(config)
                    mensaje = f"Velocidad de voz cambiada a {nueva_velocidad}"
                    console.print(f"[green]{mensaje}[/green]")
                    if usar_voz and voz_disponible:
                        voz.hablar(mensaje)
                else:
                    console.print("[red]Velocidad debe estar entre 100 y 200[/red]")
            except Exception as e:
                console.print(f"[red]Error al cambiar velocidad: {e}[/red]")
            continue
            
        elif entrada.lower().startswith("/voz volumen "):
            try:
                nuevo_volumen = float(entrada.split(" ")[-1])
                if 0 <= nuevo_volumen <= 1:
                    voz.cambiar_volumen(nuevo_volumen)
                    config["volumen_voz"] = nuevo_volumen
                    memoria.guardar_configuracion(config)
                    mensaje = f"Volumen de voz cambiado a {nuevo_volumen}"
                    console.print(f"[green]{mensaje}[/green]")
                    if usar_voz and voz_disponible:
                        voz.hablar(mensaje)
                else:
                    console.print("[red]Volumen debe estar entre 0.0 y 1.0[/red]")
            except Exception as e:
                console.print(f"[red]Error al cambiar volumen: {e}[/red]")
            continue
            
        elif entrada.lower() == "/voces":
            if voz_disponible:
                voz.listar_voces()
            else:
                console.print("[yellow]El módulo de voz no está disponible[/yellow]")
            continue
            
        elif entrada.lower().startswith("/voz cambiar "):
            try:
                if voz_disponible:
                    indice_voz = int(entrada.split(" ")[-1])
                    if voz.cambiar_voz(indice_voz):
                        config["indice_voz"] = indice_voz
                        memoria.guardar_configuracion(config)
                        mensaje = f"Voz cambiada al índice {indice_voz}"
                        console.print(f"[green]{mensaje}[/green]")
                        if usar_voz:
                            voz.hablar("Ahora estoy hablando con esta voz. ¿Qué te parece?")
                    else:
                        console.print("[red]Índice de voz no válido[/red]")
                else:
                    console.print("[yellow]El módulo de voz no está disponible[/yellow]")
            except Exception as e:
                console.print(f"[red]Error al cambiar voz: {e}[/red]")
            continue
            
        # Guardar preferencias
        elif entrada.lower().startswith("/guardar "):
            try:
                param = entrada[9:].strip()
                if "=" in param:
                    clave, valor = param.split("=", 1)  # Split solo en el primer =
                    memoria.guardar_preferencia_usuario(clave.strip(), valor.strip())
                    mensaje = f"Preferencia guardada: {clave.strip()} = {valor.strip()}"
                    console.print(f"[green]{mensaje}[/green]")
                    if usar_voz and voz_disponible:
                        voz.hablar(mensaje)
                else:
                    console.print("[red]Formato incorrecto. Usa /guardar nombre=valor[/red]")
            except Exception as e:
                console.print(f"[red]Error al guardar preferencia: {e}[/red]")
            continue
            
        # Comandos de configuración
        elif entrada.lower() == "/config" or entrada.lower() == "/configuracion":
            mostrar_opciones_configuracion()
            continue
            
        elif entrada.lower().startswith("/config "):
            param = entrada[8:].strip()
            
            # Restablecer valores predeterminados
            if param == "reset":
                confirmacion = input("¿Seguro que quieres restablecer toda la configuración? (s/n): ")
                if confirmacion.lower() in ('s', 'si', 'sí'):
                    default_config = {
                        "usar_voz": True,
                        "velocidad_voz": 145,
                        "volumen_voz": 0.85,
                        "indice_voz": 0,
                        "max_recuerdos": 500,
                        "max_resultados_web": 5,
                        "cache_ttl": 86400,
                        "modelo_llm": "deepseek-r1:14b"
                    }
                    memoria.guardar_configuracion(default_config)
                    console.print("[green]Configuración restablecida a valores predeterminados[/green]")
                continue
                
            # Exportar configuración
            elif param == "export":
                try:
                    os.makedirs("config", exist_ok=True)
                    config_path = os.path.join("config", f"jarvis_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                    with open(config_path, 'w', encoding='utf-8') as f:
                        json.dump(config, f, indent=2)
                    console.print(f"[green]Configuración exportada a {config_path}[/green]")
                except Exception as e:
                    console.print(f"[red]Error al exportar configuración: {e}[/red]")
                continue
                
            # Configuración específica por número
            try:
                opcion = int(param)
                if opcion == 1:  # Cambiar estado de voz
                    usar_voz = not usar_voz
                    config["usar_voz"] = usar_voz
                    memoria.guardar_configuracion(config)
                    console.print(f"[green]Voz {'activada' if usar_voz else 'desactivada'}[/green]")
                    if voz_disponible and usar_voz:
                        voz.hablar(f"Voz {'activada' if usar_voz else 'desactivada'}")
                elif opcion == 2:  # Velocidad de voz
                    console.print("[yellow]Ingresa la nueva velocidad (100-200):[/yellow]")
                    vel = input()
                    if vel.isdigit() and 100 <= int(vel) <= 200:
                        nueva_vel = int(vel)
                        config["velocidad_voz"] = nueva_vel
                        memoria.guardar_configuracion(config)
                        if voz_disponible:
                            voz.cambiar_velocidad(nueva_vel)
                            if usar_voz:
                                voz.hablar("Probando nueva velocidad de voz")
                        console.print(f"[green]Velocidad cambiada a {nueva_vel}[/green]")
                elif opcion == 3:  # Volumen
                    console.print("[yellow]Ingresa el nuevo volumen (0.0-1.0):[/yellow]")
                    vol = input()
                    try:
                        nuevo_vol = float(vol)
                        if 0 <= nuevo_vol <= 1:
                            config["volumen_voz"] = nuevo_vol
                            memoria.guardar_configuracion(config)
                            if voz_disponible:
                                voz.cambiar_volumen(nuevo_vol)
                                if usar_voz:
                                    voz.hablar("Probando nuevo volumen de voz")
                            console.print(f"[green]Volumen cambiado a {nuevo_vol}[/green]")
                        else:
                            console.print("[red]El volumen debe estar entre 0.0 y 1.0[/red]")
                    except:
                        console.print("[red]Valor no válido para volumen[/red]")
                elif opcion == 4:  # Cambiar voz
                    if voz_disponible:
                        voces = voz.listar_voces(silent=False)
                        if voces:
                            console.print("[yellow]Ingresa el índice de la voz deseada:[/yellow]")
                            idx = input()
                            if idx.isdigit() and 0 <= int(idx) < len(voces):
                                nuevo_idx = int(idx)
                                config["indice_voz"] = nuevo_idx
                                memoria.guardar_configuracion(config)
                                voz.cambiar_voz(nuevo_idx)
                                if usar_voz:
                                    voz.hablar("Esta es la nueva voz seleccionada")
                                console.print(f"[green]Voz cambiada a {voces[nuevo_idx]}[/green]")
                            else:
                                console.print("[red]Índice no válido[/red]")
                    else:
                        console.print("[yellow]El módulo de voz no está disponible[/yellow]")
                elif opcion == 5:  # Límite de recuerdos
                    console.print("[yellow]Ingresa el número máximo de recuerdos a mantener:[/yellow]")
                    num = input()
                    if num.isdigit() and int(num) > 0:
                        max_rec = int(num)
                        config["max_recuerdos"] = max_rec
                        memoria.guardar_configuracion(config)
                        console.print(f"[green]Límite de recuerdos cambiado a {max_rec}[/green]")
                    else:
                        console.print("[red]Valor no válido para límite de recuerdos[/red]")
                elif opcion == 6:  # Resultados web
                    console.print("[yellow]Ingresa el número de resultados por búsqueda (1-20):[/yellow]")
                    num = input()
                    if num.isdigit() and 1 <= int(num) <= 20:
                        max_res = int(num)
                        config["max_resultados_web"] = max_res
                        memoria.guardar_configuracion(config)
                        if web_disp and web_util:
                            web_util.actualizar_preferencia("max_results", max_res)
                        console.print(f"[green]Número de resultados cambiado a {max_res}[/green]")
                    else:
                        console.print("[red]Valor no válido para número de resultados[/red]")
                elif opcion == 7:  # TTL de caché
                    console.print("[yellow]Ingresa el TTL de caché en horas (1-72):[/yellow]")
                    num = input()
                    if num.isdigit() and 1 <= int(num) <= 72:
                        ttl = int(num) * 3600  # Convertir a segundos
                        config["cache_ttl"] = ttl
                        memoria.guardar_configuracion(config)
                        if web_disp and web_util:
                            web_util.actualizar_preferencia("cache_ttl", ttl)
                        console.print(f"[green]TTL de caché cambiado a {num} horas[/green]")
                    else:
                        console.print("[red]Valor no válido para TTL de caché[/red]")
                elif opcion == 8:  # Modelo LLM
                    from .asistente import listar_modelos_disponibles
                    modelos = listar_modelos_disponibles()
                    if modelos:
                        console.print("[green]Modelos disponibles:[/green]")
                        for i, modelo in enumerate(modelos):
                            console.print(f"{i+1}. {modelo}")
                        console.print("[yellow]Ingresa el número del modelo a usar:[/yellow]")
                        idx = input()
                        if idx.isdigit() and 1 <= int(idx) <= len(modelos):
                            modelo_seleccionado = modelos[int(idx)-1]
                            config["modelo_llm"] = modelo_seleccionado
                            memoria.guardar_configuracion(config)
                            console.print(f"[green]Modelo LLM cambiado a {modelo_seleccionado}[/green]")
                            console.print("[yellow]Los cambios se aplicarán al reiniciar Jarvis[/yellow]")
                        else:
                            console.print("[red]Índice no válido[/red]")
                    else:
                        console.print("[yellow]No se pudieron obtener los modelos disponibles[/yellow]")
                else:
                    console.print("[red]Opción de configuración no válida[/red]")
            except Exception as e:
                console.print(f"[red]Error al modificar configuración: {e}[/red]")
            continue
            
        # Comandos de estadísticas
        elif entrada.lower() == "/stats" or entrada.lower() == "/estadisticas":
            mostrar_estadisticas()
            continue
            
        elif entrada.lower() == "/stats memoria" or entrada.lower() == "/estadisticas memoria":
            try:
                stats = memoria.obtener_estadisticas_memoria()
                
                # Crear una tabla con estadísticas
                table = Table(title="📊 Estadísticas de Memoria")
                table.add_column("Métrica", style="cyan")
                table.add_column("Valor", style="yellow")
                
                table.add_row("Total de recuerdos", str(stats["total_recuerdos"]))
                table.add_row("Espacio usado", f"{stats['tamano_total_kb']:.2f} KB")
                table.add_row("Última interacción", stats["ultima_interaccion"])
                
                # Distribución temporal
                dist = stats["distribucion_temporal"]
                table.add_row("Recuerdos de hoy", str(dist["hoy"]))
                table.add_row("Recuerdos de esta semana", str(dist["semana"]))
                table.add_row("Recuerdos de este mes", str(dist["mes"]))
                table.add_row("Recuerdos antiguos", str(dist["antiguos"]))
                
                console.print(table)
            except Exception as e:
                console.print(f"[red]Error al obtener estadísticas de memoria: {e}[/red]")
            continue
            
        # Comandos de memoria
        elif entrada.lower() == "/memoria":
            # Mostrar últimos 5 recuerdos recientes
            recuerdos = memoria._cargar_archivos_recuerdos()[:5]
            contenido_recuerdos = ""

            for r in recuerdos:
                try:
                    with open(os.path.join(memoria.memory_dir, r), "r", encoding="utf-8") as f:
                        contenido = f.read().strip()
                        contenido_recuerdos += f"[bold]{r}[/bold]:\n{contenido[:300]}...\n\n"
                except Exception as e:
                    contenido_recuerdos += f"[red]Error al leer {r}: {e}[/red]\n\n"

            if contenido_recuerdos:
                console.print(Panel(Markdown(contenido_recuerdos), title="[bold blue]Últimos Recuerdos[/bold blue]"))
            else:
                console.print("[yellow]No hay recuerdos recientes para mostrar.[/yellow]")
            continue
            
        elif entrada.lower().startswith("/buscar-memoria "):
            try:
                texto = entrada[15:].strip()
                if len(texto) < 3:
                    console.print("[yellow]Por favor proporciona al menos 3 caracteres para buscar[/yellow]")
                    continue
                    
                console.print(f"[cyan]🔍 Buscando '{texto}' en los recuerdos...[/cyan]")
                resultados = memoria.buscar_recuerdos_por_texto(texto)
                
                if resultados:
                    console.print(f"[green]✅ Se encontraron {len(resultados)} recuerdos:[/green]")
                    
                    # Crear una tabla con los resultados
                    table = Table()
                    table.add_column("ID", style="cyan")
                    table.add_column("Fecha", style="yellow")
                    table.add_column("Contexto", style="white")
                    
                    for resultado in resultados[:10]:  # Limitar a 10 resultados
                        id = resultado["id"]
                        fecha = resultado["fecha"]
                        contexto = resultado["contexto"]
                        
                        # Resaltar el texto buscado
                        contexto_resaltado = re.sub(
                            f"({texto})", 
                            lambda m: f"[bold red]{m.group(1)}[/bold red]", 
                            contexto, 
                            flags=re.IGNORECASE
                        )
                        
                        table.add_row(id, fecha, contexto_resaltado)
                    
                    console.print(table)
                    
                    if len(resultados) > 10:
                        console.print(f"[dim]... y {len(resultados) - 10} resultados más[/dim]")
                        
                    # Preguntar si se quiere ver un recuerdo completo
                    console.print("[yellow]¿Deseas ver algún recuerdo completo? (Ingresa el ID o 'n')[/yellow]")
                    seleccion = input()
                    
                    if seleccion.lower() != 'n':
                        # Buscar el recuerdo por ID
                        for r in resultados:
                            if r["id"] == seleccion:
                                console.print(Panel(Markdown(r["contenido_completo"]), title=f"Recuerdo {seleccion}"))
                                break
                        else:
                            console.print("[yellow]ID no encontrado en los resultados[/yellow]")
                else:
                    console.print("[yellow]No se encontraron recuerdos que contengan este texto[/yellow]")
            except Exception as e:
                console.print(f"[red]Error al buscar en la memoria: {e}[/red]")
            continue
            
        elif entrada.lower().startswith("/olvidar "):
            try:
                id_recuerdo = entrada[9:].strip()
                if memoria.eliminar_recuerdo(id_recuerdo):
                    console.print(f"[green]✅ Recuerdo {id_recuerdo} eliminado correctamente[/green]")
                else:
                    console.print(f"[yellow]No se pudo eliminar el recuerdo {id_recuerdo}[/yellow]")
            except Exception as e:
                console.print(f"[red]Error al eliminar recuerdo: {e}[/red]")
            continue
            
        # Comandos de web
        elif entrada.lower().startswith("/buscar ") and web_disp and web_util:
            query = entrada[8:].strip()
            if not query:
                console.print("[yellow]Por favor proporciona una consulta de búsqueda[/yellow]")
                continue
                
            console.print(f"[cyan]🔍 Buscando información privada sobre: {query}[/cyan]")
            with Progress() as progress:
                task = progress.add_task("[cyan]Realizando búsqueda...", total=1)
                # Buscar información (usar caché si existe)
                web_util.actualizar_preferencia("max_results", config.get("max_resultados_web", 5))
                resultados = web_util.buscar_informacion(query)
                progress.update(task, completed=1)
            
            if resultados:
                # Crear una tabla con los resultados
                table = Table(title=f"📄 Resultados de búsqueda para '{query}'")
                table.add_column("#", style="cyan", justify="right")
                table.add_column("Título", style="green")
                table.add_column("Descripción", style="white")
                table.add_column("URL", style="blue")
                
                for i, res in enumerate(resultados, 1):
                    table.add_row(
                        str(i),
                        res['titulo'],
                        res['snippet'][:100] + "..." if len(res['snippet']) > 100 else res['snippet'],
                        res['url']
                    )
                
                console.print(table)
                
                # Preguntar si quiere analizar algún resultado
                console.print("[yellow]¿Deseas analizar alguno de estos resultados? (Ingresa el número o 'n')[/yellow]")
                respuesta = input()
                
                if respuesta.isdigit() and 1 <= int(respuesta) <= len(resultados):
                    indice = int(respuesta) - 1
                    url_seleccionada = resultados[indice]['url'].strip()
                    # Llamar al análisis de página
                    console.print(f"[cyan]🔍 Analizando página web: {url_seleccionada}[/cyan]")
                    try:
                        # Asegurar que la URL tenga un esquema (http o https)
                        url_seleccionada = limpiar_url(url_seleccionada)
                            
                        with Progress() as progress:
                            task = progress.add_task("[cyan]Extrayendo contenido...", total=1)
                            resultado_analisis = web_util.obtener_contenido_pagina(url_seleccionada)
                            progress.update(task, completed=1)
                            
                        if resultado_analisis:
                            mostrar_analisis_detallado(resultado_analisis)
                            
                            # Guardar análisis en la memoria
                            memoria.guardar_recuerdo(f"Análisis web de {url_seleccionada}: {resultado_analisis['titulo']}")
                            
                            # Preguntar si quiere ver el contenido completo
                            console.print("[yellow]¿Deseas ver el contenido completo? (s/n)[/yellow]")
                            respuesta = input()
                            if respuesta.lower() in ('s', 'si', 'sí'):
                                console.print(Panel(Markdown(resultado_analisis['contenido'][:5000] + "..." if len(resultado_analisis['contenido']) > 5000 else resultado_analisis['contenido']), 
                                             title=f"Contenido de {resultado_analisis['titulo']}"))
                                
                            # Explorar el resultado web
                            console.print("[yellow]¿Deseas explorar los datos extraídos en detalle? (s/n)[/yellow]")
                            respuesta = input()
                            if respuesta.lower() in ('s', 'si', 'sí'):
                                explorar_resultado_web(resultado_analisis)
                                
                            # Preguntar si se desea analizar con IA
                            console.print("[yellow]¿Deseas analizar este contenido con IA? (s/n)[/yellow]")
                            respuesta = input()
                            if respuesta.lower() in ('s', 'si', 'sí'):
                                # Construir prompt para análisis
                                prompt = f"""
                                Analiza el siguiente contenido de una página web:
                                
                                Título: {resultado_analisis['titulo']}
                                
                                Contenido:
                                {resultado_analisis['contenido'][:5000]}
                                
                                Por favor proporciona:
                                1. Un resumen de 3-4 párrafos del contenido principal
                                2. Los puntos clave o ideas importantes
                                3. Tu análisis sobre la fiabilidad y calidad de la información
                                """
                                
                                console.print("[cyan]💭 Analizando contenido con IA...[/cyan]")
                                with Progress() as progress:
                                    task = progress.add_task("[cyan]Procesando análisis...", total=1)
                                    respuesta = chat_engine.chat(prompt)
                                    progress.update(task, completed=1)
                                    
                                console.print(Panel(Markdown(respuesta.response), title="[bold blue]Análisis de IA[/bold blue]"))
                                if usar_voz and voz_disponible:
                                    texto_voz = preparar_texto_para_voz(respuesta.response)
                                    voz.hablar(texto_voz)
                        else:
                            console.print("[red]No se pudo obtener contenido de la página.[/red]")
                    except Exception as e:
                        console.print(f"[red]Error al analizar la página: {e}[/red]")
            else:
                console.print("[yellow]No se encontraron resultados[/yellow]")
            continue
            
        elif entrada.lower().startswith("/analizar ") and web_disp and web_util:
            url_raw = entrada[10:]
            url = limpiar_url(url_raw)

            console.print(f"[cyan]🔍 Analizando página web: {url}[/cyan]")
            try:
                if not es_url_valida(url):
                    raise ValueError("La URL no es válida.")

                with Progress() as progress:
                    task = progress.add_task("[cyan]Analizando contenido web...", total=1)
                    resultado = web_util.obtener_contenido_pagina(url)
                    progress.update(task, completed=1)
                
                if resultado:
                    mostrar_analisis_detallado(resultado)
                    memoria.guardar_recuerdo(f"Análisis web de {url}: {resultado['titulo']}")

                    console.print("[yellow]¿Deseas ver el contenido completo? (s/n)[/yellow]")
                    if input().strip().lower() in ('s', 'si', 'sí'):
                        contenido = resultado['contenido'][:5000]
                        console.print(Panel(Markdown(contenido + "..." if len(contenido) == 5000 else contenido),
                                            title=f"Contenido de {resultado['titulo']}"))

                    console.print("[yellow]¿Deseas explorar los datos extraídos en detalle? (s/n)[/yellow]")
                    if input().strip().lower() in ('s', 'si', 'sí'):
                        explorar_resultado_web(resultado)

                    console.print("[yellow]¿Deseas analizar este contenido con IA? (s/n)[/yellow]")
                    if input().strip().lower() in ('s', 'si', 'sí'):
                        prompt = f"""
                        Analiza el siguiente contenido de una página web:
                        
                        Título: {resultado['titulo']}
                        
                        Contenido:
                        {resultado['contenido'][:5000]}
                        
                        Por favor proporciona:
                        1. Un resumen de 3-4 párrafos del contenido principal
                        2. Los puntos clave o ideas importantes
                        3. Tu análisis sobre la fiabilidad y calidad de la información
                        """
                        console.print("[cyan]💭 Analizando contenido con IA...[/cyan]")
                        
                        with Progress() as progress:
                            task = progress.add_task("[cyan]Procesando análisis...", total=1)
                            respuesta = chat_engine.chat(prompt)
                            progress.update(task, completed=1)
                            
                        console.print(Panel(Markdown(respuesta.response), title="[bold blue]Análisis de IA[/bold blue]"))
                        if usar_voz and voz_disponible:
                            texto_voz = preparar_texto_para_voz(respuesta.response)
                            voz.hablar(texto_voz)
                else:
                    console.print("[red]No se pudo obtener contenido de la página.[/red]")
            except Exception as e:
                console.print(f"[red]Error al analizar la página: {e}[/red]")
            continue
            
        elif entrada.lower() == "/menu":
            console.print(Panel.fit(
                "[bold blue]MENÚ PRINCIPAL DE JARVIS[/bold blue]\n\n"
                "1. [bold]💬 Conversación[/bold] - Habla con tu asistente personal\n"
                "2. [bold]🔍 Búsqueda Web[/bold] - Busca información en línea\n"
                "3. [bold]📝 Gestión de Recuerdos[/bold] - Administra la memoria del asistente\n"
                "4. [bold]⚙️ Configuración[/bold] - Ajusta la configuración del sistema\n"
                "5. [bold]📊 Estadísticas[/bold] - Ver estadísticas del sistema\n"
                "6. [bold]❓ Ayuda[/bold] - Consulta la documentación y comandos\n"
                "7. [bold]❌ Salir[/bold] - Terminar programa\n\n"
                "[dim]Ingresa el número de la opción o escribe un comando directo[/dim]",
                title="🤖 Jarvis - Asistente Personal",
                border_style="blue"
            ))
            
            # Obtener entrada del usuario
            try:
                seleccion = input("\nSelecciona una opción (1-7): ")
                
                if seleccion == "1":  # Conversación
                    console.print("[cyan]Iniciando conversación...[/cyan]")
                    # No hace nada porque ya estás en la conversación
                    continue
                    
                elif seleccion == "2":  # Búsqueda Web
                    console.print(Panel("Comandos de búsqueda disponibles:\n\n"
                               "- [yellow]/buscar[/yellow] consulta - Búsqueda básica\n"
                               "- [yellow]/buscar+[/yellow] consulta - Búsqueda con análisis automático\n"
                               "- [yellow]/buscar-opciones[/yellow] - Búsqueda con opciones avanzadas\n"
                               "- [yellow]/analizar[/yellow] url - Analiza una página web específica",
                               title="🔍 Opciones de búsqueda"))
                    continue
                    
                elif seleccion == "3":  # Gestión de Recuerdos
                    console.print(Panel("Gestión de memoria:\n\n"
                               "- [yellow]/memoria[/yellow] - Ver recuerdos recientes\n"
                               "- [yellow]/guardar[/yellow] nombre=valor - Guardar preferencia\n"
                               "- [yellow]/buscar-memoria[/yellow] texto - Buscar en recuerdos\n"
                               "- [yellow]/olvidar[/yellow] id - Eliminar recuerdo específico",
                               title="📝 Memoria"))
                    continue
                    
                elif seleccion == "4":  # Configuración
                    mostrar_opciones_configuracion()
                    continue
                    
                elif seleccion == "5":  # Estadísticas
                    mostrar_estadisticas()
                    continue
                    
                elif seleccion == "6":  # Ayuda
                    mostrar_ayuda("general")
                    continue
                    
                elif seleccion == "7":  # Salir
                    confirmacion = input("¿Realmente deseas salir? (s/n): ")
                    if confirmacion.lower() in ("s", "si", "sí", "y", "yes"):
                        mostrar_despedida()
                        return
                    else:
                        console.print("[green]Operación cancelada, continuando...[/green]")
                    continue
                
                else:
                    console.print("[yellow]Opción no válida. Intenta de nuevo.[/yellow]")
                    continue
                    
            except KeyboardInterrupt:
                console.print("\n[yellow]Operación interrumpida por el usuario.[/yellow]")
            except Exception as e:
                console.print(f"[red]Error al procesar selección: {e}[/red]")
            continue
                    
        # Si no es un comando especial, obtener recuerdos relevantes
        try:
            with Progress(transient=True) as progress:
                task = progress.add_task("[cyan]Recuperando recuerdos...", total=1)
                contexto_recuerdos = memoria.obtener_contexto_relevante(entrada)
                progress.update(task, completed=1)
        except Exception as e:
            console.print(f"[bold red]Error al recuperar recuerdos: {e}[/bold red]")
            contexto_recuerdos = ""

        # Crear mensaje para el modelo
        if contexto_recuerdos:
            console.print("[dim cyan]🧠 Recordando información relevante...[/dim cyan]")
            mensaje = f"""
            El usuario pregunta: "{entrada}"
            
            Recuerdos relevantes:
            {contexto_recuerdos}
            
            Por favor responde usando la información de estos recuerdos.
            """
        else:
            mensaje = entrada
            
        # Enviar mensaje y obtener respuesta
        try:
            with Progress() as progress:
                task = progress.add_task("[cyan]Generando respuesta...", total=1)
                respuesta = chat_engine.chat(mensaje)
                progress.update(task, completed=1)
                
            respuesta_final = respuesta.response
            
            # Limpiar respuesta si tiene formato thinking
            if "<think>" in respuesta_final and "</think>" in respuesta_final:
                respuesta_final = respuesta_final.split("</think>")[-1].strip()
                
            # Mostrar la respuesta con formato markdown
            respuesta_md = Markdown(respuesta_final)
            console.print(Panel(respuesta_md, title="[bold blue]Jarvis[/bold blue]"))
            
            # Si la voz está activada, hablar la respuesta
            if usar_voz and voz_disponible:
                texto_voz = preparar_texto_para_voz(respuesta_final)
                voz.hablar(texto_voz)
                
            # Guardar interacción como recuerdo
            memoria.guardar_recuerdo(f"Usuario: {entrada}\nIA: {respuesta_final}")
            
        except Exception as e:
            console.print(f"[bold red]Error al obtener respuesta: {e}[/bold red]")
            memoria.guardar_recuerdo(f"Usuario: {entrada}\nIA: Error de respuesta: {str(e)}")
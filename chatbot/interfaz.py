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
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.chat_engine.context import ContextChatEngine
# from llama_index.chat_engine.context import ContextChatEngine
# from llama_index.memory.chat_memory_buffer import ChatMemoryBuffer

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

def ejecutar_chat(indice=None, llm=None, componentes=None) -> None:
    """Inicia la interfaz de chat interactiva en la consola"""
    # Configurar logging
    logger = logging.getLogger("interfaz")
    
    # Inicializar consola
    console = Console()
    console.print(Panel("[bold blue]JARVIS - Asistente Virtual[/bold blue]", 
                        subtitle="Escribe 'salir' para terminar"))
    
    # Obtener componentes
    componentes = componentes or {}
    web = componentes.get("web")
    web_disponible = componentes.get("web_disponible", False)
    chat_engine = componentes.get("chat_engine")
    
    # Inicializar memoria si no se proporciona
    if not indice:
        try:
            from chatbot.memoria import MemoryManager
            memoria = MemoryManager()
            indice = memoria.index
            logger.info("Memoria inicializada desde el módulo")
        except Exception as e:
            logger.warning(f"No se pudo inicializar memoria: {e}")
            indice = None
    
    # Verificar inicialización de sistema de voz
    try:
        from chatbot.voz import Voz
        voz = Voz()
        voz_disponible = True
        logger.info("Módulo de voz disponible e importado")
    except ImportError:
        voz_disponible = False
        voz = None
        logger.warning("Módulo de voz no disponible")
    
    # Verificar inicialización de web
    if not web and web_disponible:
        try:
            from chatbot.web import MotorWebPrivado
            web = MotorWebPrivado()
            logger.info("Módulo web disponible e inicializado")
        except ImportError:
            web = None
            logger.warning("Módulo web no disponible")
    
    # Inicializar TTS
    if voz_disponible:
        try:
            voz.inicializar()
        except Exception as e:
            logger.error(f"Error al inicializar voz: {e}")
            voz_disponible = False
    
    # Ejecutar bucle principal
    while True:
        try:
            # Obtener entrada del usuario
            entrada = input("\n[Tú]: ")
            
            # Verificar comando de salida
            if entrada.lower() in ["salir", "exit", "quit", "q"]:
                console.print("[bold yellow]¡Hasta luego![/bold yellow]")
                break
            
            # Determinar si debemos realizar búsqueda web
            realizar_busqueda_web = False
            if web_disponible and entrada.lower().startswith(("busca ", "buscar ", "search ")):
                realizar_busqueda_web = True
                consulta = entrada.split(" ", 1)[1]
                
                # Realizar búsqueda
                with console.status("[bold green]Buscando en la web...[/bold green]"):
                    try:
                        resultados = web.realizar_busqueda(consulta)
                        contexto_web = "\n".join(resultados[:3])
                    except Exception as e:
                        logger.error(f"Error al buscar en web: {e}")
                        contexto_web = f"Error al buscar información: {e}"
                
                # Mostrar resultados
                console.print(Panel(
                    f"[italic]Resultados de búsqueda para:[/italic] [bold]{consulta}[/bold]\n\n" + 
                    contexto_web,
                    title="Resultados Web",
                    border_style="blue"
                ))
            
            # Generar respuesta 
            with console.status("[bold green]Pensando...[/bold green]"):
                # Determinar qué motor usar para la respuesta
                if chat_engine:
                    # Si tenemos chat_engine, usarlo directamente
                    if hasattr(chat_engine, 'chat'):
                        respuesta = chat_engine.chat(entrada)
                        respuesta_final = respuesta.text if hasattr(respuesta, 'text') else str(respuesta)
                    else:
                        # Fallback si chat_engine no tiene método chat
                        respuesta_final = "Error: El motor de chat no implementa el método 'chat'"
                elif indice:
                    # Usar índice si está disponible
                    try:
                        engine = indice.as_chat_engine(chat_mode="condense_question", verbose=True)
                        respuesta = engine.chat(entrada)
                        respuesta_final = respuesta.response
                    except Exception as e:
                        logger.error(f"Error al usar índice como chat engine: {e}")
                        respuesta_final = f"Error al procesar la respuesta: {e}"
                else:
                    # Fallback final si no hay motor de chat ni índice
                    try:
                        from chatbot.asistente import obtener_llm
                        llm_fallback = obtener_llm()
                        respuesta_final = llm_fallback.complete(entrada).text
                    except Exception as e:
                        respuesta_final = f"No puedo generar una respuesta: {e}"
            
            # Limpiar respuesta si tiene formato thinking
            if "<think>" in respuesta_final and "</think>" in respuesta_final:
                respuesta_final = respuesta_final.split("</think>")[-1].strip()
                
            # Mostrar la respuesta con formato markdown
            respuesta_md = Markdown(respuesta_final)
            console.print(Panel(respuesta_md, title="[bold blue]Jarvis[/bold blue]"))
            
            # Reproducir respuesta con TTS si está disponible
            if voz_disponible:
                try:
                    # Limpiar el texto para TTS
                    texto_limpio = respuesta_final
                    # Quitar marcadores markdown comunes
                    for caracter in ["*", "_", "#", "`", "[", "]", "(", ")"]:
                        texto_limpio = texto_limpio.replace(caracter, "")
                    voz.decir(texto_limpio)
                except Exception as e:
                    logger.error(f"Error al reproducir voz: {e}")
            
        except Exception as e:
            logger.error(f"Error en la ejecución: {e}")
            console.print(f"[bold red]Error:[/bold red] {e}")
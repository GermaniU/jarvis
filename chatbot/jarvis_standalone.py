#!/usr/bin/env python3
"""
jarvis_standalone.py - Versión independiente de Jarvis que no depende de LlamaIndex
"""
import os
import json
import time
import requests
import re
import datetime
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress

# Configuración básica
OLLAMA_URL = "http://localhost:11434/api/generate"
MEMORY_DIR = "memory"
WEB_CACHE_DIR = os.path.join(MEMORY_DIR, "web_cache")
DEFAULT_MODEL = "deepseek-r1:14b"
FALLBACK_MODEL = "mistral:7b"

# Crear directorios necesarios
os.makedirs(MEMORY_DIR, exist_ok=True)
os.makedirs(WEB_CACHE_DIR, exist_ok=True)

# Inicializar consola Rich
console = Console()

class MemoriaSimple:
    """Gestor de memoria simplificado"""
    
    def __init__(self, directorio: str = MEMORY_DIR):
        self.directorio = directorio
        os.makedirs(directorio, exist_ok=True)
    
    def guardar_recuerdo(self, mensaje: str, respuesta: str) -> bool:
        """Guarda una interacción en la memoria"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}.txt"
        content = f"Usuario: {mensaje}\nJarvis: {respuesta}"
        
        try:
            filepath = os.path.join(self.directorio, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            console.print(f"[red]Error al guardar recuerdo: {e}[/red]")
            return False
    
    def obtener_contexto(self, mensaje: str, max_recuerdos: int = 5) -> str:
        """
        Obtiene recuerdos relevantes para proporcionar contexto
        Esta versión simplemente devuelve los últimos recuerdos
        """
        try:
            archivos = [f for f in os.listdir(self.directorio) 
                      if f.endswith(".txt") and not f.startswith("config")]
            
            # Ordenar por fecha (más recientes primero)
            archivos.sort(reverse=True)
            
            # Tomar solo los más recientes
            recuerdos = []
            for archivo in archivos[:max_recuerdos]:
                ruta = os.path.join(self.directorio, archivo)
                with open(ruta, "r", encoding="utf-8") as f:
                    contenido = f.read()
                recuerdos.append(contenido)
            
            return "\n\n".join(recuerdos)
        except Exception as e:
            console.print(f"[yellow]Error al recuperar recuerdos: {e}[/yellow]")
            return ""

class WebSimple:
    """Buscador web simplificado"""
    
    def __init__(self, cache_dir: str = WEB_CACHE_DIR):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
    def buscar(self, consulta: str) -> List[Dict[str, str]]:
        """
        Búsqueda web simplificada usando DuckDuckGo
        """
        try:
            # Usar DuckDuckGo HTML para búsqueda
            consulta_encoded = requests.utils.quote(consulta)
            url = f"https://html.duckduckgo.com/html/?q={consulta_encoded}"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                console.print(f"[yellow]Error en búsqueda: código {response.status_code}[/yellow]")
                return []
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            resultados = []
            for result in soup.select('.result')[:5]:  # Limitar a 5 resultados
                titulo = result.select_one('.result__title')
                snippet = result.select_one('.result__snippet')
                url_elem = result.select_one('.result__url')
                
                if not all([titulo, snippet, url_elem]):
                    continue
                    
                resultados.append({
                    "titulo": titulo.get_text(strip=True),
                    "snippet": snippet.get_text(strip=True),
                    "url": url_elem.get_text(strip=True)
                })
            
            return resultados
        except Exception as e:
            console.print(f"[red]Error en búsqueda web: {e}[/red]")
            return []
            
    def obtener_contenido(self, url: str) -> Optional[Dict[str, str]]:
        """
        Extrae el contenido principal de una URL
        """
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                console.print(f"[yellow]Error al acceder a {url}: código {response.status_code}[/yellow]")
                return None
            
            # Usar BeautifulSoup para extraer contenido
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraer título
            titulo = "Sin título"
            if soup.title:
                titulo = soup.title.string.strip()
                
            # Extraer contenido principal (estrategia simple)
            contenido = ""
            
            # Buscar contenedor principal
            main_content = soup.find(['article', 'main', 'div', 'section'], 
                                    class_=re.compile(r'content|article|main'))
            
            if main_content:
                # Extraer párrafos
                for p in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4']):
                    text = p.get_text(strip=True)
                    if len(text) > 20:  # Solo párrafos significativos
                        if p.name.startswith('h'):
                            contenido += f"\n## {text}\n\n"
                        else:
                            contenido += text + "\n\n"
            else:
                # Si no encontramos un contenedor principal, extraer párrafos generales
                for p in soup.find_all('p')[:15]:  # Limitar a 15 párrafos
                    text = p.get_text(strip=True)
                    if len(text) > 50:  # Solo párrafos significativos
                        contenido += text + "\n\n"
            
            return {
                "titulo": titulo,
                "url": url,
                "contenido": contenido
            }
            
        except Exception as e:
            console.print(f"[red]Error al obtener contenido de {url}: {e}[/red]")
            return None

class LLMSimple:
    """Interfaz simplificada para el LLM"""
    
    def __init__(self, modelo: str = DEFAULT_MODEL):
        self.modelo = modelo
        # Verificar si Ollama está disponible
        self.disponible = self._verificar_disponibilidad()
        if not self.disponible:
            console.print("[yellow]Advertencia: Ollama no parece estar disponible. Jarvis funcionará en modo limitado.[/yellow]")
    
    def _verificar_disponibilidad(self) -> bool:
        """Verifica si Ollama está disponible"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def generar_respuesta(self, prompt: str) -> str:
        """
        Genera una respuesta usando Ollama
        """
        if not self.disponible:
            return "Lo siento, no puedo responder porque no se detectó Ollama. Por favor, asegúrate de que Ollama esté ejecutándose."
        
        try:
            data = {
                "model": self.modelo,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.7,
                "top_p": 0.9
            }
            
            response = requests.post(OLLAMA_URL, json=data, timeout=30)
            
            if response.status_code != 200:
                console.print(f"[yellow]Error del servidor Ollama: {response.status_code}[/yellow]")
                # Intentar con modelo de respaldo
                data["model"] = FALLBACK_MODEL
                response = requests.post(OLLAMA_URL, json=data, timeout=30)
                
            if response.status_code == 200:
                return response.json().get("response", "Lo siento, no pude generar una respuesta.")
            else:
                return f"Error al conectar con Ollama: código {response.status_code}"
                
        except Exception as e:
            console.print(f"[red]Error al generar respuesta: {e}[/red]")
            return f"Error al generar respuesta: {str(e)}"

def mostrar_bienvenida():
    """Muestra mensaje de bienvenida"""
    console.print(Panel.fit(
        "[bold green]JARVIS - Asistente Personal con IA[/bold green]\n\n"
        "[yellow]Capacidades:[/yellow]\n"
        "- Memoria de conversaciones anteriores\n"
        "- Búsqueda web básica\n"
        "- Análisis de contenido web\n\n"
        "[blue]Comandos:[/blue]\n"
        "- /ayuda - Muestra comandos disponibles\n"
        "- /buscar <consulta> - Busca información en la web\n"
        "- /analizar <url> - Analiza una página web\n"
        "- /limpiar - Limpia la conversación\n"
        "- salir - Termina la conversación",
        title="👋 Bienvenido",
        border_style="green"
    ))

def mostrar_despedida():
    """Muestra mensaje de despedida"""
    console.print(Panel.fit(
        "[bold blue]Gracias por usar Jarvis[/bold blue]\n"
        "Tus conversaciones han sido guardadas para futuras interacciones.\n"
        "¡Hasta pronto!",
        title="👋 Hasta pronto",
        border_style="blue"
    ))

def procesar_comando(comando: str, web_simple: WebSimple) -> str:
    """Procesa comandos especiales"""
    comando = comando.lower()
    
    if comando == "/ayuda":
        return """## Comandos disponibles
- /ayuda - Muestra esta ayuda
- /buscar <consulta> - Busca información en la web
- /analizar <url> - Analiza una página web
- /limpiar - Limpia la conversación
- salir - Termina la conversación"""
    
    elif comando == "/limpiar":
        console.clear()
        mostrar_bienvenida()
        return "Conversación limpiada."
        
    elif comando.startswith("/buscar "):
        consulta = comando[8:].strip()
        if not consulta:
            return "Por favor, proporciona una consulta de búsqueda."
            
        with Progress() as progress:
            task = progress.add_task("[cyan]Buscando información...", total=1)
            resultados = web_simple.buscar(consulta)
            progress.update(task, completed=1)
            
        if not resultados:
            return "No se encontraron resultados para esta consulta."
            
        texto_resultados = f"## Resultados para '{consulta}'\n\n"
        for i, res in enumerate(resultados, 1):
            texto_resultados += f"{i}. **{res['titulo']}**\n"
            texto_resultados += f"   {res['snippet']}\n"
            texto_resultados += f"   URL: {res['url']}\n\n"
            
        return texto_resultados
        
    elif comando.startswith("/analizar "):
        url = comando[10:].strip()
        if not url:
            return "Por favor, proporciona una URL para analizar."
            
        with Progress() as progress:
            task = progress.add_task("[cyan]Analizando página web...", total=1)
            resultado = web_simple.obtener_contenido(url)
            progress.update(task, completed=1)
            
        if not resultado:
            return "No se pudo analizar la página. Verifica que la URL sea correcta."
            
        texto_analisis = f"## {resultado['titulo']}\n\n"
        texto_analisis += f"URL: {resultado['url']}\n\n"
        texto_analisis += resultado['contenido'][:1500]  # Limitar longitud
        
        if len(resultado['contenido']) > 1500:
            texto_analisis += "\n\n... (contenido truncado)"
            
        return texto_analisis
        
    return f"Comando '{comando}' no reconocido. Usa /ayuda para ver los comandos disponibles."

def main():
    """Función principal"""
    console.clear()
    mostrar_bienvenida()
    
    # Inicializar componentes
    memoria = MemoriaSimple()
    web = WebSimple()
    llm = LLMSimple()
    
    # Bucle principal de chat
    while True:
        mensaje = input("\nTú: ")
        
        if mensaje.lower() == "salir":
            mostrar_despedida()
            break
            
        if mensaje.startswith("/"):
            respuesta = procesar_comando(mensaje, web)
            console.print(Panel(Markdown(respuesta), title="[bold blue]Jarvis[/bold blue]"))
            # No guardar comandos en la memoria
            continue
        
        # Obtener contexto de memoria
        contexto_memoria = memoria.obtener_contexto(mensaje, max_recuerdos=3)
        
        # Construir prompt con contexto
        prompt = f"""Eres Jarvis, un asistente personal amigable e inteligente que responde en español.
        
Historial de conversación:
{contexto_memoria}

Usuario actual: {mensaje}

Instrucciones:
1. Responde de forma clara y directa
2. Si no tienes información sobre algo, admítelo
3. Sé educado pero natural

Respuesta de Jarvis:"""
        
        # Generar respuesta
        with Progress() as progress:
            task = progress.add_task("[cyan]Pensando...", total=1)
            respuesta = llm.generar_respuesta(prompt)
            progress.update(task, completed=1)
        
        # Mostrar respuesta
        console.print(Panel(Markdown(respuesta), title="[bold blue]Jarvis[/bold blue]"))
        
        # Guardar en memoria
        memoria.guardar_recuerdo(mensaje, respuesta)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Programa interrumpido por el usuario[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Error inesperado: {e}[/bold red]")
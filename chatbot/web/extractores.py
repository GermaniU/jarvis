"""
Extractores de contenido específicos para diferentes sitios web
"""
import re
import logging
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional, List, Callable, Type

logger = logging.getLogger("web.extractores")

class SelectorExtractor:
    """Clase base para extractores de contenido basados en selectores"""
    
    @staticmethod
    def extraer_contenido_general(soup: BeautifulSoup) -> str:
        """
        Extrae contenido general de una página web cuando no hay extractores específicos
        
        Args:
            soup: Objeto BeautifulSoup con el HTML parseado
            
        Returns:
            Contenido extraído
        """
        # Estrategia de extracción principal: detectar el contenedor más relevante
        candidatos = soup.find_all(['article', 'main', 'section', 'div'])
        candidatos = [c for c in candidatos if len(c.get_text(strip=True)) > 300]

        if candidatos:
            # Ordenar candidatos por longitud de contenido
            mejor = sorted(candidatos, key=lambda c: len(c.get_text()), reverse=True)[0]
            
            # Priorizar elementos principales 
            parrafos = []
            
            # Extraer encabezados para estructura
            for h in mejor.find_all(['h1', 'h2', 'h3', 'h4']):
                text = h.get_text(strip=True)
                if len(text) > 5:
                    nivel = int(h.name[1])
                    if nivel == 1:
                        parrafos.append(f"\n\n## {text}\n")
                    elif nivel == 2:
                        parrafos.append(f"\n\n### {text}\n")
                    else:
                        parrafos.append(f"\n\n#### {text}\n")
            
            # Extraer párrafos, listas y bloques de código
            for elem in mejor.find_all(['p', 'ul', 'ol', 'pre', 'code', 'blockquote']):
                if elem.name == 'p':
                    text = elem.get_text(strip=True)
                    if len(text) > 30:
                        parrafos.append(text)
                elif elem.name in ('ul', 'ol'):
                    items = []
                    for li in elem.find_all('li'):
                        item_text = li.get_text(strip=True)
                        if len(item_text) > 10:
                            items.append(f"• {item_text}")
                    if items:
                        parrafos.append("\n".join(items))
                elif elem.name in ('pre', 'code'):
                    code_text = elem.get_text(strip=True)
                    if len(code_text) > 20:
                        parrafos.append(f"```\n{code_text}\n```")
                elif elem.name == 'blockquote':
                    quote_text = elem.get_text(strip=True)
                    if len(quote_text) > 30:
                        parrafos.append(f"> {quote_text}")
            
            return "\n\n".join(parrafos)

        # Último recurso: extraer todos los párrafos significativos
        parrafos = []
        # Extraer encabezados principales primero
        for h in soup.find_all(['h1', 'h2']):
            text = h.get_text(strip=True)
            if len(text) > 5:
                parrafos.append(f"\n## {text}\n")
        
        # Luego extraer párrafos largos
        for p in soup.find_all('p'):
            text = p.get_text(strip=True)
            if len(text) > 50:  # Solo párrafos significativos
                parrafos.append(text)
        
        return "\n\n".join(parrafos[:15])  # Limitar a 15 párrafos para evitar contenido excesivo
        
    @staticmethod
    def extraer_github(soup: BeautifulSoup) -> str:
        """Extrae contenido específico de GitHub"""
        contenido = ""
        
        # README
        readme = soup.find('article', class_='markdown-body entry-content container-lg')
        if not readme:
            readme = soup.find('div', class_='markdown-body')
        
        if readme:
            contenido = readme.get_text(separator="\n", strip=True)
            
            # Procesar encabezados para mejor formato
            contenido = re.sub(r'(^|\n)# ([^\n]+)', r'\1## \2', contenido)
            contenido = re.sub(r'(^|\n)## ([^\n]+)', r'\1### \2', contenido)
            
            # Extraer info del repositorio si está disponible
            repo_info = []
            
            # Descripción
            description = soup.find('p', class_='f4 my-3')
            if description:
                repo_info.append(description.get_text(strip=True))
            
            # Lenguajes
            langs = soup.find('div', class_='mb-2 repository-lang-stats-graph')
            if langs:
                repo_info.append(f"Lenguajes: {langs.get('aria-label', '')}")
                
            # Estrellas, forks, etc.
            for link in soup.find_all('a', class_='Link--muted'):
                text = link.get_text(strip=True)
                if text and any(x in text.lower() for x in ['star', 'fork', 'watch']):
                    repo_info.append(text)
                    
            if repo_info:
                contenido = "# Información del repositorio\n" + "\n".join(repo_info) + "\n\n# README\n" + contenido
        
        return contenido
        
    @staticmethod
    def extraer_stackoverflow(soup: BeautifulSoup) -> str:
        """Extrae contenido específico de Stack Overflow"""
        contenido = ""
        
        # Pregunta
        question = soup.find('div', id=lambda x: x and x.startswith('question'))
        if question:
            # Título
            title = question.find('a', class_='question-hyperlink')
            if not title:
                title = soup.find('h1')
                
            if title:
                contenido += f"# {title.get_text(strip=True)}\n\n"
            
            # Contenido de la pregunta
            question_body = question.find('div', class_='post-text')
            if not question_body:
                question_body = question.find('div', class_='s-prose')
                
            if question_body:
                contenido += question_body.get_text(separator="\n", strip=True) + "\n\n"
            
            # Respuestas
            answers = soup.find_all('div', id=lambda x: x and x.startswith('answer'))
            if answers:
                contenido += "# Respuestas\n\n"
                
                for i, answer in enumerate(answers[:3], 1):  # Limitar a 3 respuestas
                    contenido += f"## Respuesta {i}\n"
                    
                    # Marcar si es respuesta aceptada
                    if 'accepted-answer' in answer.get('class', []):
                        contenido += "✓ RESPUESTA ACEPTADA\n\n"
                    
                    # Contenido de la respuesta
                    answer_body = answer.find('div', class_='post-text')
                    if not answer_body:
                        answer_body = answer.find('div', class_='s-prose')
                        
                    if answer_body:
                        contenido += answer_body.get_text(separator="\n", strip=True) + "\n\n"
        
        return contenido
        
    @staticmethod
    def extraer_wikipedia(soup: BeautifulSoup) -> str:
        """Extrae contenido específico de Wikipedia"""
        contenido = ""
        
        # Título
        title = soup.find('h1', id='firstHeading')
        if title:
            contenido += f"# {title.get_text(strip=True)}\n\n"
        
        # Resumen (primer párrafo)
        content_div = soup.find('div', id='mw-content-text')
        if content_div:
            # Extraer el resumen inicial
            paragraphs = content_div.find_all('p')
            for p in paragraphs:
                if len(p.get_text(strip=True)) > 100:
                    contenido += p.get_text(strip=True) + "\n\n"
                    break
            
            # Extraer secciones principales
            for section in content_div.find_all(['h2', 'h3'], recursive=True):
                # Ignorar secciones no relevantes
                if any(x in section.get_text().lower() for x in ['referencias', 'véase también', 'enlaces externos']):
                    continue
                    
                section_title = section.get_text(strip=True).replace('[editar]', '')
                section_level = "##" if section.name == 'h2' else "###"
                
                contenido += f"{section_level} {section_title}\n\n"
                
                # Extraer contenido de la sección
                current = section.find_next()
                while current and current.name not in ['h2', 'h3', 'h4']:
                    if current.name == 'p' and len(current.get_text(strip=True)) > 30:
                        contenido += current.get_text(strip=True) + "\n\n"
                    elif current.name in ['ul', 'ol']:
                        for li in current.find_all('li', recursive=False):
                            li_text = li.get_text(strip=True)
                            if len(li_text) > 15:
                                contenido += f"• {li_text}\n"
                        contenido += "\n"
                    
                    try:
                        current = current.find_next()
                    except:
                        break
        
        return contenido
        
    @staticmethod
    def extraer_youtube(soup: BeautifulSoup) -> str:
        """Extrae información de videos de YouTube"""
        contenido = ""
        
        # Título
        title = soup.find('meta', itemprop='name')
        if title:
            contenido += f"# {title['content']}\n\n"
        else:
            title = soup.find('meta', property='og:title')
            if title:
                contenido += f"# {title['content']}\n\n"
        
        # Descripción
        description = soup.find('meta', itemprop='description')
        if description and description['content']:
            contenido += "## Descripción\n\n" + description['content'] + "\n\n"
        else:
            description = soup.find('meta', property='og:description')
            if description:
                contenido += "## Descripción\n\n" + description['content'] + "\n\n"
        
        # Datos del canal
        channel = soup.find('meta', itemprop='channelName')
        if channel:
            contenido += f"• Canal: {channel['content']}\n"
        
        # Fecha de publicación
        date = soup.find('meta', itemprop='datePublished')
        if date:
            contenido += f"• Publicado: {date['content']}\n"
        
        # Duración
        duration = soup.find('meta', itemprop='duration')
        if duration:
            contenido += f"• Duración: {duration['content']}\n"
        
        return contenido
        
    @staticmethod
    def extraer_documentacion(soup: BeautifulSoup) -> str:
        """Extrae contenido de páginas de documentación técnica"""
        contenido = ""
        
        # Título principal
        title = soup.find('h1')
        if title:
            contenido += f"# {title.get_text(strip=True)}\n\n"
        
        # Descripción o resumen inicial
        for p in soup.find_all('p')[:3]:  # Primeros párrafos como posible introducción
            if len(p.get_text(strip=True)) > 50:
                contenido += p.get_text(strip=True) + "\n\n"
                break
        
        # Extraer secciones principales con sus encabezados
        for h in soup.find_all(['h2', 'h3', 'h4']):
            text = h.get_text(strip=True)
            if len(text) < 5 or any(skip in text.lower() for skip in ['índice', 'contenido', 'table of']):
                continue
                
            level = "##" if h.name == 'h2' else "###" if h.name == 'h3' else "####"
            contenido += f"\n{level} {text}\n\n"
            
            # Extraer contenido hasta el siguiente encabezado del mismo nivel o superior
            next_h = h.find_next(['h2', 'h3', 'h4'])
            current = h.find_next()
            
            while current and (not next_h or current != next_h):
                if current.name == 'p' and len(current.get_text(strip=True)) > 30:
                    contenido += current.get_text(strip=True) + "\n\n"
                elif current.name in ['ul', 'ol']:
                    for li in current.find_all('li'):
                        li_text = li.get_text(strip=True)
                        if len(li_text) > 10:
                            contenido += f"• {li_text}\n"
                    contenido += "\n"
                elif current.name == 'pre' or current.name == 'code':
                    code_text = current.get_text(strip=True)
                    if len(code_text) > 20:
                        contenido += f"```\n{code_text}\n```\n\n"
                
                try:
                    current = current.find_next()
                except:
                    break
        
        # Si no extraímos suficiente contenido, intentar con selectores específicos comunes en docs
        if len(contenido) < 500:
            article = soup.find(['article', 'main', '.content', '.documentation', '.docs'])
            if article:
                for p in article.find_all('p'):
                    if len(p.get_text(strip=True)) > 50:
                        contenido += p.get_text(strip=True) + "\n\n"
                
                # Extraer ejemplos de código
                for code in article.find_all(['pre', 'code']):
                    code_text = code.get_text(strip=True)
                    if len(code_text) > 50:
                        contenido += f"```\n{code_text}\n```\n\n"
        
        return contenido

# Registro de extractores por dominio
EXTRACTORES = {
    "github.com": SelectorExtractor.extraer_github,
    "stackoverflow.com": SelectorExtractor.extraer_stackoverflow,
    "stackexchange.com": SelectorExtractor.extraer_stackoverflow,
    "wikipedia.org": SelectorExtractor.extraer_wikipedia,
    "youtube.com": SelectorExtractor.extraer_youtube,
    "youtu.be": SelectorExtractor.extraer_youtube,
}

def get_extractor(url: str) -> Optional[Callable[[BeautifulSoup], str]]:
    """
    Obtiene el extractor adecuado para una URL específica
    
    Args:
        url: URL de la página
        
    Returns:
        Función extractora o None si no hay un extractor específico
    """
    for dominio, extractor in EXTRACTORES.items():
        if dominio in url:
            return extractor
            
    # Extractor para documentación técnica
    if "docs." in url or ".documentation" in url or "/docs/" in url:
        return SelectorExtractor.extraer_documentacion
    
    # Extractor general como fallback
    return SelectorExtractor.extraer_contenido_general
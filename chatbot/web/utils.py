"""
Funciones auxiliares para el motor web
"""
import re
import random
import logging
from urllib.parse import urlparse, urljoin
from typing import List, Dict, Any, Optional

logger = logging.getLogger("web.utils")

def extraer_dominio(url: str) -> str:
    """
    Extrae el dominio base de una URL
    
    Args:
        url: URL completa
        
    Returns:
        Dominio extraído (ej: ejemplo.com)
    """
    match = re.search(r'(?:https?:\/\/)?(?:www\.)?([^\/]+)', url)
    return match.group(1) if match else url

def extraer_dominio_completo(url: str) -> str:
    """
    Extrae el dominio con protocolo de una URL
    
    Args:
        url: URL completa
        
    Returns:
        Dominio con protocolo (ej: https://ejemplo.com)
    """
    match = re.search(r'^(https?://[^/]+)', url)
    return match.group(1) if match else url

def normalizar_url(url: str) -> str:
    """
    Normaliza una URL asegurando que comience con http:// o https://
    
    Args:
        url: URL sin procesar
        
    Returns:
        URL normalizada
    """
    url = url.strip()
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

def get_random_user_agent(user_agents: List[str]) -> str:
    """
    Devuelve un User-Agent aleatorio de la lista proporcionada
    
    Args:
        user_agents: Lista de User-Agents disponibles
        
    Returns:
        User-Agent aleatorio
    """
    return random.choice(user_agents)

def resolver_url_relativa(base_url: str, url_relativa: str) -> str:
    """
    Resuelve una URL relativa a partir de una URL base
    
    Args:
        base_url: URL base
        url_relativa: URL relativa
        
    Returns:
        URL absoluta
    """
    return urljoin(base_url, url_relativa)

def limpiar_texto(texto: str) -> str:
    """
    Limpia y normaliza un texto eliminando espacios y caracteres extraños
    
    Args:
        texto: Texto sin procesar
        
    Returns:
        Texto limpio
    """
    # Eliminar espacios extra
    texto = re.sub(r'\s+', ' ', texto).strip()
    
    # Eliminar caracteres no imprimibles
    texto = ''.join(c for c in texto if c.isprintable() or c in ['\n', '\t'])
    
    return texto

def truncar_texto(texto: str, longitud_maxima: int = 500, sufijo: str = "...") -> str:
    """
    Trunca un texto a la longitud máxima especificada y añade un sufijo
    
    Args:
        texto: Texto a truncar
        longitud_maxima: Longitud máxima del texto
        sufijo: Sufijo a añadir si se trunca
        
    Returns:
        Texto truncado
    """
    if len(texto) <= longitud_maxima:
        return texto
        
    # Intentar truncar en un punto, espacio o salto de línea
    for i in range(longitud_maxima - 1, longitud_maxima - 50, -1):
        if i < 0:
            break
        if texto[i] in ['.', '!', '?', ' ', '\n']:
            return texto[:i+1] + sufijo
            
    return texto[:longitud_maxima] + sufijo

def es_navegador_obsoleto(user_agent: str) -> bool:
    """
    Verifica si un User-Agent pertenece a un navegador obsoleto
    
    Args:
        user_agent: String de User-Agent
        
    Returns:
        True si es un navegador obsoleto, False en caso contrario
    """
    patrones_obsoletos = [
        r'MSIE [1-9]\.', 
        r'Firefox/[1-9]\.', 
        r'Chrome/[1-9]\.', 
        r'Safari/[1-4]',
        r'Opera/[1-9]\.'
    ]
    
    return any(re.search(pattern, user_agent) for pattern in patrones_obsoletos)
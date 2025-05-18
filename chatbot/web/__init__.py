"""
Refactorización del módulo web.py dividido en componentes más pequeños
"""

# chatbot/web/__init__.py
"""
Motor de búsqueda web con enfoque en privacidad - Módulo principal
"""
import logging
from typing import Dict, List, Optional, Any

from .motor import MotorWebPrivado
from .extractores import SelectorExtractor
from .cache import CacheManager
from .utils import extraer_dominio, extraer_dominio_completo

__all__ = ['MotorWebPrivado', 'SelectorExtractor', 'CacheManager']

# Configurar logging global del módulo
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("jarvis_web.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("web")

# Alias para compatibilidad con código existente
search_engine = MotorWebPrivado
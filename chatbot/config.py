"""
config.py - Configuraciones centralizadas para Jarvis
"""
import os
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("jarvis.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Directorios y rutas
MEMORY_DIR = "memory"
EMBEDDINGS_DIR = "embeddings"
DATA_DIR = "data"

# Configuraciones de LLM
DEFAULT_MODEL = "deepseek-r1:14b"
FALLBACK_MODEL = "mistral:7b"

# Configuraciones de Embeddings
DEFAULT_EMBEDDING_MODEL = "local"

# Crear directorios necesarios
os.makedirs(MEMORY_DIR, exist_ok=True)
os.makedirs(EMBEDDINGS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# Obtener logger centralizado
def get_logger(name):
    return logging.getLogger(name)


# En config.py
# Configuración para memoria híbrida
MEMORIA_HIBRIDA = {
    "PESO_MEMORIA_RECIENTE": 0.4,
    "PESO_MEMORIA_SEMANTICA": 0.6,
    "MAX_RECUERDOS_RECIENTES": 10,
    "PRIORIDAD_TEMA_IMPORTANTE": 1.5,
    "UMBRAL_RELEVANCIA": 0.2
}